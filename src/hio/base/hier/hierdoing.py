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
from dataclasses import dataclass, astuple, asdict, field
import typing


from .. import tyming
from ..doing import Doist, Doer
from ... import hioing
from ...hioing import Mixin, HierError
from ... import help
from ...help.helping import isNonStringIterable



def exen(nears,far):
    """Computes the relative differences (uncommon  and common parts) between
    the box stak lists nears passed in and fars from box far.stak

    Parameters:
        nears (list[Box]): near box.stak in top down order
        far (Box): far box giving fars = far.stak in top down order.

    Assumes staks nears and fars are in top down order

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

    Since a given box's stak is always traced up via its .over if any and down via
    its primary under i.e. .unders[0] if any, when far is in nears the anything
    below far is same in both fars and nears.

    Otherwise when far not in nears then i where fars[i] is not nears[i]
    indicates first box where fars down and nears down is uncommon i.e. the stak
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
    fars = far.stak  # top down order
    l = min(len(nears), len(fars))  # l >= 1 since far in fars & near in nears
    for i in range(l):  # start at the top of both nears and fars
        if (far is nears[i]) or (fars[i] is not nears[i]): #first effective uncommon member
            # (exits, enters, rexits, renters)
            return (nears[i:].reverse(), fars[i:], nears[:i].reverse(), fars[:i])


class Lode(dict):
    """Lode subclass of dict with custom methods dunder methods and get that
    will only allow actual keys as str. Iterables passed in as key are converted
    to a "_' joined str. Uses "_" so can use dict constuctor if need be with str
    path. Assumes items in Iterable do not contain '_'.

    Special staticmethods:
        tokeys(k) returns split of k at separator '_' as tuple.

    """
    @staticmethod
    def tokeys(k):
        """Converts '_' joined key string to tuple of keys by splitting on '_'

        Parameters:
            k (str): '_' joined string to be split
        Returns:
            keys (tuple[str]): split of k on '_' into path key components
        """
        return tuple(k.split("_"))


    def __setitem__(self, k, v):
        if isNonStringIterable(k):
            try:
                k = '_'.join(k)
            except Exception as ex:
                raise KeyError(ex.args) from ex
        if not isinstance(k, str):
            raise KeyError(f"Expected str got {k}.")
        return super(Lode, self).__setitem__(k, v)

    def __getitem__(self, k):
        if isNonStringIterable(k):
            try:
                k = '_'.join(k)
            except Exception as ex:
                raise KeyError(ex.args) from ex
        if not isinstance(k, str):
            raise KeyError(f"Expected str got {k}.")
        return super(Lode, self).__getitem__(k)


    def __contains__(self, k):
        if isNonStringIterable(k):
            try:
                k = '_'.join(k)
            except Exception as ex:
                raise KeyError(ex.args) from ex
        if not isinstance(k, str):
            raise KeyError(f"Expected str got {k}.")
        return super(Lode, self).__contains__(k)


    def get(self, k, default=None):
        if isNonStringIterable(k):
            try:
                k = '_'.join(k)
            except Exception as ex:
                raise KeyError(ex.args) from ex
        if not isinstance(k, str):
            raise KeyError(f"Expected str got {k}.")
        if not super(Lode, self).__contains__(k):
            return default
        else:
            return super(Lode, self).__getitem__(k)


class Builder(Mixin):
    """Builder Class boxworks of Boxer and Box instances.
    Holds reference to in-memory lode shared by all boxes in boxwork
    Holds reference to current Boxer and Boxe being built

    Attributes:
        lode (Lode): in memory data lode shared by all boxes in boxwork
        boxer (Boxer | None): current boxer
        box (Box | None): cureent box

    Properties:
        name (str): unique identifier of instance

    Hidden:
        _name (str): unique identifier of instance

    """
    def __init__(self, *, name='builder', lode=None, **kwa):
        """Initialize instance.

        Parameters:
            name (str): unique identifier of box
            lode (Lode | None): in memory data lode shared by all boxes in box work


        """
        super(Builder, self).__init__(**kwa)
        self.name = name
        self.lode = lode if lode is not None else Lode()
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
        if '_' in name:
            raise HierError(f"Invalid {name=} contains '_'.")
        self._name = name


class Boxer(Mixin):
    """Boxer Class that executes hierarchical action framework (boxwork) instances.
    Boxer instance holds reference to in-memory data lode shared by all its boxes
    and other Boxers in a given boxwork.
    Box instance holds a reference to its first (beginning) box.
    Box instance holds references to all its boxes in dict keyed by box name.

    Attributes:
        lode (Lode): in memory data lode shared by all boxes in box work
        doer (Doer | None): doer running this boxer
        first (Box | None):  beginning box
        stak (list[Box]): active stak of boxes
        box (Box | None):  active box in stak
        boxes (dict): all boxes mapping of (box name, box) pairs

    Properties:
        name (str): unique identifier of instance

    Hidden:
        _name (str): unique identifier of instance


    Order of Execution of Contexts:
        time[k=0]  First Time
            precur preacts (marks)
            benter beacts
            renter renacts
            enter enacts
            recur reacts
            while not done:
                time[k=k+1]  Next Time
                    precur preacts (marks)
                    transit
                        if tract in tracts is True and benter beacts new stak is True:
                            segue to new stak
                                old stak:
                                    exit exacts
                                    rexit rexacts
                                new stak:
                                    renter renacts
                                    enter enacts
                    else:
                        recur reacts (current stak)
            exit exacts
            rexit rexacts

    """
    def __init__(self, *, name='boxer', lode=None, doer=None, first=None, **kwa):
        """Initialize instance.

        Parameters:
            name (str): unique identifier of box
            lode (Lode | None): in memory data lode shared by all boxes in box work
            doer (Doer | None): Doer running this Boxer
            first (Box | None):  beginning box


        """
        super(Boxer, self).__init__(**kwa)
        self.name = name
        self.lode = lode if lode is not None else Lode()
        self.doer = None
        self.first = first
        self.stak = []  # current active stak
        self.box = None  # current active box in active stak
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
        if '_' in name:
            raise HierError(f"Invalid {name=} contains '_'.")
        self._name = name


class Box(Mixin):
    """Box Class for hierarchical action framework (boxwork) instances.
    Box instance holds reference to in-memory data lode shared by all the boxes in a
    given boxwork as well as its executing Boxer.
    Box instance holds references (links) to its over box and its under boxes.
    Box instance holds the acts to be executed in their context.



    Attributes:
        lode (dict): in memory data lode shared by all boxes in box work
        boxer (Boxer | None):  this box's Boxer instance
        over (Box | None): this box's over box instance or None
        unders (list[Box]): this box's under box instances or empty
        nxt (Box | None): this box's next box if any
        stak (list[Box]): this box's stak of boxes
        preacts (list[act]): precur (pre-occurence pre-transit) context acts
        beacts (list[act]): benter (before enter) context acts
        renacts (list[act]): renter (re-enter) context acts
        reacts (list[act]): recur context acts
        tracts (list[act]): transit context acts
        exacts (list[act]): exit context acts
        rexacts (list[act]): rexit (re-exit) context acts

    Properties:
        name (str): unique identifier of instance

    Hidden:
        _name (str): unique identifier of instance




    """
    def __init__(self, *, name='box', lode=None, boxer=None, **kwa):
        """Initialize instance.

        Parameters:
            name (str): unique identifier of box
            lode (dict | None): in memory data lode shared by all boxes in box work
            boxer (Boxer | None):  this box's Boxer instance


        """
        super(Box, self).__init__(**kwa)
        if '_' in name:
            raise HierError(f"Invalid {name=} contains '_'.")
        self.name = name
        self.lode = lode if lode is not None else Lode()
        self.boxer = boxer
        self.over = None  # over box
        self.unders = []  # list of under boxes, zeroth entry is primary
        self.nxt = None  # next box
        self.stak = []  # stak of boxes to which this box belongs
        # acts by contexts
        self.preacts = []  # precur context list of pre-occurence pre-transit acts
        self.beacts = []  # benter context list of before enter acts
        self.renacts = []  # renter context list of re-enter acts
        self.enacts = []  # enter context list of enter acts
        self.reacts = []  # recur context list of recurring acts
        self.tracts = []  # transit context list of transition acts
        self.exacts = []  # exit context list of exit acts
        self.rexacts = []  # rexit context list of re-exit acts

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
        if '_' in name:
            raise HierError(f"Invalid {name=} contains '_'.")
        self._name = name
