# -*- encoding: utf-8 -*-
"""
hio.core.hier.hiering Module

Provides hierarchical action support

"""
from __future__ import annotations  # so type hints of classes get resolved later

import os
import sys
import time
import logging
import json
import signal
import re
import multiprocessing as mp
import functools

from collections import deque, namedtuple
from collections.abc import Iterable, Mapping, Callable
from typing import Any, Type
from dataclasses import dataclass, astuple, asdict, field


from .. import Tymee
from ...hioing import Mixin, HierError
from ...help import isNonStringIterable, MapDom, modify


# Regular expression to detect valid attribute names for Boxes
ATREX = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
# Usage: if Reat.match(name): or if not Reat.match(name):
Reat = re.compile(ATREX)  # compile is faster

"""Actage (namedtuple):
Callable object and its keyword args to be injected and called at run time.

Fields:
   act (Callable): callable object. Must have name attribute
   kwa (dict): key word args to be injected at runtime into act.
"""
Actage = namedtuple("Actage", "act kwa")

Registry = dict()  # registry of Actor subclasses keyed by class name

def register(actor, name=None):
    """Add Registry entry for actor keyed by its name.
    Must be Callable. If name not provides then actor must have .__name__
    attribute or property
    """
    name = name if name is not None else actor.__name__
    if name in Registry:
        raise hioing.HierError(f"Actor by {name=} already registered.")
    Registry[name] = actor



# ToDo  any callable usually function that is not already a subclass of Actor.
# can be converted so a subclass of Actor and then registered in the Registry.
# normally if defining a class then inhereit from Actor. But if simply a function
# then decorate with actify so that a a new subclass is created and registered

def actify(name, *, base=None, registry=None):
    """ Parametrized decorator function that converts the decorated function
    into an Actor sub class with .act method and with class name that
    is name and registers the new subclass in the registry under name as
    a subclass of base. The default base is Actor.

    The parameters  name, attr if provided,
    are used to create the class attributes for the new subclass

    """
    if not issubclass(base, Actor):
        raise hioing.HierError(f"Expected Actor got {base=}.")

    # make this smarted and apply to functions with function attributes for
    # actor slots name, bags

    attrs = None
    cls = type(name, (base, ), attrs)

    def decorator(func):
        if not isinstance(func, Callable):
            raise hioing.HierError(f"Expected Callable got {func=}.")

        @functools.wraps(func)
        def inner(*pa, **kwa):
            return func(*pa, **kwa)
        cls.act = inner  # method
        return inner
    return decorator


class Actor(Mixin):
    """Actor Callable Base Class. Has Actor specific Registry of classes

    Class Attributes:
        Index (int): default naming index for subclass instances


    Properties:
        name (str): unique name string of instance

    Hidden
        ._name (str|None): unique name of instance

    """
    Index = 0  # naming index for default names of subclass instances
    __slots__ = ('_name')


    def __init__(self, name=None, **kwa):
        """
        Initialization method for instance.



        """
        super(Actor,self).__init__(**kwa) # in case of MRO

        if name is None:
            name = self.__class__.__name__ + str(self.Index)
            self.__class__.Index += 1   # so has not to shadow class attribute
        self.name = name


    def __call__(self, **kwa):
        """Make Actor instance a callable object. run its .act method"""
        return self.act(**kwa)


    def act(self, **kwa):
        """Act called by Actor. Should override in subclass."""
        pass

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


register(Actor)


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

@dataclass
class WorkDom(MapDom):
    """WorkDom provides state for building boxwork by a boxer to be injected
    make methods of Boxer by workify wrapper.


    Attributes:
        box (Box | None): current box in box work. None if not yet a box
        over (Box | None): current over Box in box work. None if top level
        bxpre (str):  default box name prefix used to generate unique box name
                    relative to boxer.boxes
        bxidx (int): default box name index used to generate unique box name
                    relative to boxer.boxes
    """
    box: None | Box = None  # current box in boxwork. None if not yet any box
    over: None | Box = None  # current over box in boxwork. None if not yet any over
    bxpre: str = 'box'  # default box name prefix when name not provided
    bxidx: int = 0  # default box name index when name not provided





class Haul(dict):
    """Haul subclass of dict with custom methods dunder methods and get that
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
        return super(Haul, self).__setitem__(self.tokey(k), v)


    def __getitem__(self, k):
        return super(Haul, self).__getitem__(self.tokey(k))


    def __delitem__(self, k):
        return super(Haul, self).__delitem__(self.tokey(k))


    def __contains__(self, k):
        return super(Haul, self).__contains__(self.tokey(k))


    def get(self, k, default=None):
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
            raise TypeError(f"Expected 1 positional argument got {len(pa)}.")

        if pa:
            di = pa[0]
            if isinstance(di, Mapping):
                rd = {}
                for k, v in di.items():
                    rd[self.tokey(k)] = v
                super(Haul, self).update(rd, **kwa)

            elif isinstance(di, Iterable):
                ri = []
                for k, v in di:
                    ri.append((self.tokey(k), v))
                super(Haul, self).update(ri, **kwa)

            else:
                raise TypeError(f"Expected Mapping or Iterable got {type(di)}.")

        else:
            super(Haul, self).update(**kwa)


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



