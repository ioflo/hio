# -*- encoding: utf-8 -*-
"""
hio.core.hierdoing Module

Provides hierarchical action support

"""
import os
import sys
import time
import logging
import json
import signal
import re
import multiprocessing as mp

from collections import deque, namedtuple
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, astuple, asdict, field
import typing


from .. import Tymee
from ...hioing import Mixin, HierError
from ...help.helping import isNonStringIterable


# Regular expression to detect valid attribute names for Boxes
ATREX = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
# Usage: if Reat.match(name): or if not Reat.match(name):
Reat = re.compile(ATREX)  # compile is faster

def exen(near,far):
    """Computes the relative differences (uncommon  and common parts) between
    the box pile lists nears passed in and fars from box far.pile

    Parameters:
        near (Box): near box giving nears =near.pile in top down order
        far (Box): far box giving fars = far.pile in top down order.

    Assumes piles nears and fars are in top down order

    Returns:
        quadruple (tuple[list]): quadruple of lists of form:
            (exits, enters, renters, rexits) where:
            exits is list of uncommon boxes in nears but not in fars to be exited.
                Reversed to bottom up order.
            enters is list of uncommon boxes in fars but not in nears to be entered
            rexits is list of common boxes in both nears and fars to be re-exited
                Reversed to bottom up order.
            renters is list of common boxes in both nears and fars to be re-entered

            The sets of boxes in rexits and renters are the same set but rexits
            is reversed to bottum up order.


    Supports forced reentry transitions when far is in nears. This means fars
        == nears. In this case:
        The common part of nears/fars from far down is force exited
        The common part of nears/fars from far down is force entered

    When far in nears then forced entry at far so far is nears[i]
    catches that case for forced entry at some far in nears. Since
    far is in fars, then when far == nears[i] then fars == nears.

    Since a given box's pile is always traced up via its .over if any and down via
    its primary under i.e. .unders[0] if any, when far is in nears the anything
    below far is same in both fars and nears.

    Otherwise when far not in nears then i where fars[i] is not nears[i]
    indicates first box where fars down and nears down is uncommon i.e. the pile
    tree branches at i. This is the normal non-forced entry case for transition.

    Two different topologies are accounted for with this code.
    Recall that python slice of list is zero based where:
       fars[i] not in fars[:i] and fars[i] in fars[i:]
       nears[i] not in nears[:i] and nears[i] in nears[i:]
       this means fars[:0] == nears[:0] == [] empty list

    1.0 near and far in same tree either on same branch or different branches
        1.1 on same branch forced entry where nears == fars so far in nears.
           Walk down from shared root to find where far is nears[i]. Boxes above
           far given by fars[:i] == nears[:i] are re-exit re-enter set of boxes.
           Boxes at far and below are forced exit entry.
        1.2 on different branch to walk down from root until find fork where
           fars[i] is not nears[i]. So fars[:i] == nears[:i] above fork at i,
           and are re-exit and re-enter set of boxes. Boxes at i and below in
           nears are exit and boxes at i and below in fars are enter
    2.0 near and far not in same tree. In this case top of nears at nears[0] is
        not top of fars ar fars[0] i.e. different tree roots, far[0] != near[0]
        and fars[:0] == nears[:0] = [] means empty re-exits and re-enters and
        all nears are exit and all fars are entry.

    """
    nears = near.pile  # top down order
    fars = far.pile  # top down order
    l = min(len(nears), len(fars))  # l >= 1 since far in fars & near in nears
    for i in range(l):  # start at the top of both nears and fars
        if (far is nears[i]) or (fars[i] is not nears[i]): #first effective uncommon member
            # (exits, enters, rexits, renters)
            return (list(reversed(nears[i:])), fars[i:],
                    list(reversed(nears[:i])), fars[:i])



class Lode(dict):
    """Lode subclass of dict with custom methods dunder methods and get that
    will only allow actual keys as str. Iterables passed in as key are converted
    to a "_' joined str. Uses "_" so can use dict constuctor if need be with str
    path. Assumes items in Iterable do not contain '_'.

    Special staticmethods:
        tokeys(k) returns split of k at separator '_' as tuple.

    """
    def __init__(self, *pa, **kwa):
        """Convert keys that are tuples when positional argument is Iterable or
        Mapping to '.' joined strings

        dict __init__ signature options are:
            dict(**kwa)
            dict(mapping, **kwa)
            dict(iterable, **kwa)
        dict.update has same call signature
            d.update({"a": 5, "b": 2,}, c=3 , d=4)

        """
        self.update(*pa, **kwa)


    def __setitem__(self, k, v):
        #if isNonStringIterable(k):
            #try:
                #k = '.'.join(k)
            #except Exception as ex:
                #raise KeyError(ex.args) from ex
        #if not isinstance(k, str):
            #raise KeyError(f"Expected str got {k}.")
        return super(Lode, self).__setitem__(self.tokey(k), v)


    def __getitem__(self, k):
        #if isNonStringIterable(k):
            #try:
                #k = '.'.join(k)
            #except Exception as ex:
                #raise KeyError(ex.args) from ex
        #if not isinstance(k, str):
            #raise KeyError(f"Expected str got {k}.")
        return super(Lode, self).__getitem__(self.tokey(k))


    def __contains__(self, k):
        #if isNonStringIterable(k):
            #try:
                #k = '.'.join(k)
            #except Exception as ex:
                #raise KeyError(ex.args) from ex
        #if not isinstance(k, str):
            #raise KeyError(f"Expected str got {k}.")
        return super(Lode, self).__contains__(self.tokey(k))


    def get(self, k, default=None):
        #if isNonStringIterable(k):
            #try:
                #k = '.'.join(k)
            #except Exception as ex:
                #raise KeyError(ex.args) from ex
        #if not isinstance(k, str):
            #raise KeyError(f"Expected str got {k}.")
        #if not super(Lode, self).__contains__(k):
            #return default
        #else:
            #return super(Lode, self).__getitem__(k)
        if not self.__contains__(k):
            return default
        else:
            return self.__getitem__(k)



    def update(self, *pa, **kwa):
        """Convert keys that are tuples when positional argument is Iterable or
        Mapping to '.' joined strings

        dict __init__ signature options are:
            dict(**kwa)
            dict(mapping, **kwa)
            dict(iterable, **kwa)
        dict.update has same call signature
            d.update({"a": 5, "b": 2,}, c=3 , d=4)

        """
        if len(pa) > 1:
            raise TypeError(f"expected 1 positional argument got {len(pa)}")

        if pa:
            di = pa[0]
            if isinstance(di, Mapping):
                rd = {}
                for k, v in di.items():
                    #if isNonStringIterable(k):
                        #try:
                            #k = '.'.join(k)
                        #except Exception as ex:
                            #raise KeyError(ex.args) from ex
                    #if not isinstance(k, str):
                        #raise KeyError(f"Expected str got {k}.")
                    rd[self.tokey(k)] = v
                super(Lode, self).update(rd, **kwa)

            elif isinstance(di, Iterable):
                ri = []
                for k, v in di:
                    #if isNonStringIterable(k):
                        #try:
                            #k = '.'.join(k)
                        #except Exception as ex:
                            #raise KeyError(ex.args) from ex
                    #if not isinstance(k, str):
                        #raise KeyError(f"Expected str got {k}.")
                    ri.append((self.tokey(k), v))
                super(Lode, self).update(ri, **kwa)

        else:
            super(Lode, self).update(**kwa)


    @staticmethod
    def tokey(keys):
        """Joins tuple of strings keys to '.' joined string key. If already
        str then returns unchanged.

        Parameters:
            keys (Iterable[str] | str ): non-string Iteralble of path key
                    components to be '.' joined into key.
                    If keys is already str then returns unchanged

        Returns:
            key (str): '.' joined string
        """
        if isNonStringIterable(keys):
            try:
                key = '.'.join(keys)
            except Exception as ex:
                raise KeyError(ex.args) from ex
        else:
            key = keys
        if not isinstance(key, str):
            raise KeyError(f"Expected str got {key}.")
        return key


    @staticmethod
    def tokeys(key):
        """Converts '.' joined string key to tuple of keys by splitting on '.'

        Parameters:
            key (str): '.' joined string to be split
        Returns:
            keys (tuple[str]): split of key on '.' into path key components
        """
        return tuple(key.split("."))


class Maker(Mixin):
    """Maker Class makes boxworks of Boxer and Box instances.
    Holds reference to in-memory lode shared by all boxes in boxwork
    Holds reference to current Boxer and Boxe being built

    Attributes:
        bags (Lode): in memory data lode shared by all boxes in boxwork
        boxer (Boxer | None): current boxer
        box (Box | None): cureent box

    Properties:
        name (str): unique identifier of instance

    Hidden:
        _name (str): unique identifier of instance

    """
    def __init__(self, *, name='maker', bags=None, **kwa):
        """Initialize instance.

        Parameters:
            name (str): unique identifier of instance
            bags (Lode | None): in memory data lode shared by all boxes in box work


        """
        super(Maker, self).__init__(**kwa)
        self.name = name
        self.bags = bags if bags is not None else Lode()
        self.boxer = None
        self.box = None

    @property
    def name(self):
        """Property getter for ._name

        Returns:
            name (str): unique identifier of instance
        """
        return self._name


    @name.setter
    def name(self, name):
        """Property setter for ._name

        Paramaters:
            name (str): unique identifier of instance
        """
        if not Reat.match(name):
            raise HierError(f"Invalid {name=}.")

        self._name = name

    def make(self):
        """"""


class Boxer(Tymee):
    """Boxer Class that executes hierarchical action framework (boxwork) instances.
    Boxer instance holds reference to in-memory data lode shared by all its boxes
    and other Boxers in a given boxwork.
    Box instance holds a reference to its first (beginning) box.
    Box instance holds references to all its boxes in dict keyed by box name.

    Inherited Attributes, Properties
        see Tymee

    Attributes:
        bags (Lode): in memory Lode (map) of data bags shared by all boxes in box work
        doer (Doer | None): doer running this boxer
        first (Box | None):  beginning box
        pile (list[Box]): active pile of boxes
        box (Box | None):  active box in pile
        boxes (dict): all boxes mapping of (box name, box) pairs

    Properties:
        name (str): unique identifier of instance

    Hidden:
        _name (str): unique identifier of instance


    Order of Execution of Contexts:
        time[k=0]  First Time
            precur preacts (marks)
            benter beacts
            enter enacts
            recur reacts
            while not done:
                time[k=k+1]  Next Time
                    precur preacts (marks)
                    transit
                        if tract in tracts is True and benter beacts new pile is True:
                            segue to new pile
                                old pile:
                                    exit exacts
                                    rexit rexacts
                                new pile:
                                    renter renacts
                                    enter enacts
                    else:
                        recur reacts (current pile)
            exit exacts


    """
    def __init__(self, *, name='boxer', bags=None, doer=None, first=None, **kwa):
        """Initialize instance.

        Parameters:
            name (str): unique identifier of box
            bags (Lode | None): in memory Lode (map) of data bags shared by all
                                 boxes in box work
            doer (Doer | None): Doer running this Boxer
            first (Box | None):  beginning box


        """
        super(Boxer, self).__init__(**kwa)
        self.name = name
        self.bags = bags if bags is not None else Lode()
        self.doer = None
        self.first = first
        self.pile = []  # current active pile
        self.box = None  # current active box in active pile
        self.boxes = {}

    @property
    def name(self):
        """Property getter for ._name

        Returns:
            name (str): unique identifier of instance
        """
        return self._name


    @name.setter
    def name(self, name):
        """Property setter for ._name

        Paramaters:
            name (str): unique identifier of instance
        """
        if not Reat.match(name):
            raise HierError(f"Invalid {name=}.")
        self._name = name

    def prep(self):
        """"""

    def run(self):
        """"""

    def quit(self):
        """"""

    def make(self):
        """"""


class Box(Tymee):
    """Box Class for hierarchical action framework (boxwork) instances.
    Box instance holds reference to in-memory data lode shared by all the boxes in a
    given boxwork as well as its executing Boxer.
    Box instance holds references (links) to its over box and its under boxes.
    Box instance holds the acts to be executed in their context.

    Inherited Attributes, Properties
        see Tymee

    Attributes:
        bags (Lode): in memory Lode (map) of data bags shared by all boxes
                     in box work
        boxer (Boxer | None):  this box's Boxer instance
        over (Box | None): this box's over box instance or None
        unders (list[Box]): this box's under box instances or empty
                            zeroth entry is primary under

        nxt (Box | None): this box's next box if any
        preacts (list[act]): precur (pre-occurence pre-transit) context acts
        beacts (list[act]): benter (before enter) context acts
        renacts (list[act]): renter (re-enter) context acts
        reacts (list[act]): recur context acts
        tracts (list[act]): transit context acts
        exacts (list[act]): exit context acts
        rexacts (list[act]): rexit (re-exit) context acts

    Properties:
        name (str): unique identifier of instance
        pile (list[Box]): this box's pile of boxes generated by tracing .over up
                          and .unders[0] down if any. This is generated lazily.
                          To refresh call ._trace()
        trail (str): human friendly represetion of pile as delimited string of
                        box names from .pile. This is generated lazily.
                        To refresh call ._trace()

    Hidden:
        _name (str): unique identifier of instance
        _pile (list[Box] | None): pile of Boxes to which this box belongs.
                                  None means not yet traced.
        _spot (int | None): zero based offset into .pile of this box. This is
                            computed by ._trace
        _trail (int | None): human friendly represetion of pile as delimited
                             string of box names from .pile.
                            This is computed by ._trace
        _trace(): function to trace and update ._pile from .over and .unders[0]
                  and update ._spot and ._trail




    """
    def __init__(self, *, name='box', bags=None, boxer=None, over=None,
                 unders=None, **kwa):
        """Initialize instance.

        Parameters:
            name (str): unique identifier of box
            bags (Lode): in memory Lode (map) of data bags shared by all boxes
                         in box work
            boxer (Boxer | None):  this box's Boxer instance
            over (Box | None): this box's over box instance or None
            unders (list[Box]): this box's under box instances or empty.
                                zeroth entry is primary under
        """
        super(Box, self).__init__(**kwa)
        self.name = name
        self._pile = None  # force .trace on first access of .pile property
        self._spot = None  # zero based offset into .pile of this box
        self._trail = None  # delimited string representation of box names in .pile

        self.bags = bags if bags is not None else Lode()
        self.boxer = boxer
        self.over = over  # over box
        self.unders = unders if unders is not None else []  # list of under boxes,

        self.nxt = None  # next box to execute on default transition

        # acts by contexts
        self.preacts = []  # precur context list of pre-occurence pre-transit acts
        self.beacts = []  # benter context list of before enter acts
        self.renacts = []  # renter context list of re-enter acts
        self.enacts = []  # enter context list of enter acts
        self.reacts = []  # recur context list of recurring acts
        self.tracts = []  # transit context list of transition acts
        self.exacts = []  # exit context list of exit acts
        self.rexacts = []  # rexit context list of re-exit acts


    def __repr__(self):
        """Representation usable by eval()."""
        return (f"{self.__class__.__name__}(name='{self.name}')")

    def __str__(self):
        """Representation human friendly."""
        return (f"{self.__class__.__name__}({self.trail})")


    def _trace(self):
        """Trace pile and update .pile by tracing over up if any and unders[0]
        down if any.
        """
        pile = []
        over = self.over
        while over:
            pile.insert(0, over)
            over = over.over
        pile.append(self)
        self._spot = len(pile) - 1
        under = self.unders[0] if self.unders else None
        while under:
            pile.append(under)
            under = under.unders[0] if under.unders else None
        self._pile = pile

        up = "<".join(over.name for over in self._pile[:self._spot])
        dn = ">".join(under.name for under in self._pile[self._spot+1:])
        self._trail = up + "<" + self._name + ">" + dn


    @property
    def name(self):
        """Property getter for ._name

        Returns:
            name (str): unique identifier of instance
        """
        return self._name


    @name.setter
    def name(self, name):
        """Property setter for ._name

        Paramaters:
            name (str): unique identifier of instance
        """
        if not Reat.match(name):
            raise HierError(f"Invalid {name=}.")
        self._name = name


    @property
    def pile(self):
        """Property getter for ._pile

        Returns:
            pile (list[Box]): this box's pile of boxes generated by tracing
                              .over up and .unders[0] down if any. This is
                              generated lazily to refresh call ._trace().
                              pile always includes self once traced.
        """
        if self._pile is None:
            self._trace()
        return self._pile

    @property
    def spot(self):
        """Property getter for ._spot

        Returns:
            spot (int): zero based offset of this box into its pile of boxes
                        generated by tracing .over up and .unders[0] down if any.
                        This is generated lazily. To refresh call ._trace().
                        Since pile always includes self, spot is always defined
                        once traced.
        """
        if self._spot is None:
            self._trace()
        return self._spot

    @property
    def trail(self):
        """Property getter for ._trail

        Returns:
            trail (str): human frieldly delimited string of box names from .pile.
                        This is generated lazily. To refresh call ._trace().
                        Since pile always includes self, trail is always defined
                        once traced.
        """
        if self._trail is None:
            self._trace()
        return self._trail




