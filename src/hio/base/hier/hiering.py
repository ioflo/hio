# -*- encoding: utf-8 -*-
"""
hio.core.hier.hiering Module

Provides hierarchical action support




Syntax notes for Mine and Dock use in boxwork:
    M mine (Mine) memory non-durable attribute syntax
    D dock (Dock) durable attribute syntax
    with locally scope variables M ref for mine and D ref for dock.


    so need syntax does not heed to "quote" paths keys into the bags
    containers Mine dict subclasses with attribute support.

    M.root_dog.value  is equivalent to self.mine["root_dog"].value or
                                       self.mine[("root", "dog")].value

    So need term  "M.root_dog.value > 5" should compile directly and eval
    as long as M is in the locals() and M is a Mine instance.

    Likewise for
    D.root_dog.value where D is a Dock and root_dog is a key in the Dock.

    So no need to do substitutions or shorthand
    The hierarchy in the .mine/.dock is indicated by '_' separated keys
    The Box Boxer Actor names are forbidden from having '_" as an element
    with Renam regex test.



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


from ..tyming import Tymee
from ... import hioing
from ...hioing import Mixin, HierError
from ...help import isNonStringIterable, MapDom, modify, Renam


"""Contextage (namedtuple):
Action contexts for Acts

Fields:
   native (str): native context
   precon (str): precon context
   renter (str): renter context
   enter (str): enter context
   recur (str): recur context
   tail (str): tail context
   transit (str): transit context
   exit (str): exit context
   rexit (str): rexit context
"""
Contextage = namedtuple("Contextage", "native precon renter enter recur tail transit exit rexit")

Context = Contextage(native="native", precon="precon", renter="renter",
                     enter="enter", recur="recur", tail="tail",
                     transit="transit", exit="exit", rexit="rexit")


# ToDo  any callable usually function that is not already a subclass of Actor.
# can be converted so a subclass of Actor and then registered in the Registry.
# normally if defining a class then inhereit from Actor. But if simply a function
# then decorate with actify so that a a new subclass is created and registered

def actify(name, *, base=None, attrs=None):
    """Parametrized decorator that converts the decorated function func into
    .act method of new subclass of class base with .__name__ name. If not
    provided then uses Act as base. When provided base must be subclass of ActBase.
    Registers new subclass in ActBase.Registry. Then instantiates cls and returns
    instance.

    Returns:
        instance (cls): instance of new subclass

    Updates the class attributes of new subclass with attrs if any.

    Usage:


    Assigning a function to a class the value of an attribute automatically
    makes that attribute a bound method with injected self as first argument.

    class A():
        def a(self):
           print(self)

    a = A()
    a.a()
    <__main__.A object at 0x1059ffc50>

    def b(self):
        print(self)

    A.b = b
    a.b()
    <__main__.A object at 0x1059ffc50>


    """
    base = base if base is not None else ActBase
    if not issubclass(base, ActBase):
        raise hioing.HierError(f"Expected ActBase subclass got {base=}.")

    attrs = attrs if attrs is not None else {}
    # assign Act attrs
    attrs.update(dict(Registry=base.Registry, Instances=base.Instances, Index=0,
                      Aliases=() ))
    cls = type(name, (base, ), attrs)  # create new subclass of base of Act.
    #registerone(cls)  # register subclass in cls.Registry
    cls.registerbyname()  # register subclass in cls.Registry by cls.__name__

    def decorator(func):
        if not isinstance(func, Callable):
            raise hioing.HierError(f"Expected Callable got {func=}.")
        cls.act = func  # assign as bound method .act with injected self.

        @functools.wraps(func)
        def inner(*pa, **kwa):
            return cls(*pa, **kwa)  # instantiate and return instance
        return inner
    return decorator


def registerone(cls):
    """Class Decorator to add cls as cls.Registry entry for itself keyed by its
    own .__name__. Need class decorator so that class object is already created
    by registration time when decorator is applied
    """
    name = cls.__name__
    if name in cls.Registry:
        raise hioing.HierError(f"Act by {name=} already registered.")
    cls.Registry[name] = cls
    return cls


def register(names=None):
    """Parametrized class Decorator to add cls as cls.Registry entry for itself
    keyed by its own .__name__ as well as being keyed by alises in names.
    A class decorator is necessary so that the class object is already created
    when decorator is applied.

    Parameters:
        names (None|str|Iterator): iterator of names as alises besides class
                name to register class in Act registry.

    """
    if not names:
        names = tuple()
    elif isinstance(names, str):
        names = (names, )  # make one tuple of str
    else:
        names = tuple(names)  # make tuple of iterable

    def decorator(cls):
        name = cls.__name__
        if name in cls.Registry:
            raise hioing.HierError(f"Act by {name=} already registered.")
        cls.Registry[name] = cls
        cls.Aliases = names
        for name in names:
            if name in cls.Registry:
                raise hioing.HierError(f"Act by {name=} already registered.")
            cls.Registry[name] = cls
        return cls
    return decorator




@register()
class ActBase(Mixin):
    """Act Base Class. Callable with Registry of itself and its subclasses.

    Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Instances (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.
        Aliases (tuple[str]): tuple of aliases (names) under which this subclas
                            appears in .Registry



    Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act
        context (str): action context for .act

    Hidden
        ._name (str|None): unique name of instance
        ._iopts (dict): input-output-paramters for .act
        ._context (str): action context for .act

    """
    Registry = {}  # subclass registry
    Instances = {}  # instance name registry
    Index = 0  # naming index for default names of this subclasses instances
    Aliases = ()  # tuple of aliases for this subclass in Registry


    @classmethod
    def registerbyname(cls, name=None):
        """Adds cls to cls.Registry entry by name. Raises HierError if already
        registered.

        Parameters:
            cls (Type[Act]): class to be registered
            name (None|str): key to register cls under.
                             When None then use cls.__name__
        """
        name = name if name is not None else cls.__name__
        if name in cls.Registry:
            raise hioing.HierError(f"Act by {name=} already registered.")
        cls.Registry[name] = cls
        return cls

    @classmethod
    def _reregister(cls):
        """Reregisters cls after clear.
        Need to override in each subclass with super to reregister the class hierarchy
        """
        ActBase.registerbyname()  # defaults to cls.__name__


    @classmethod
    def _clear(cls):
        """Clears Registry, Names and Index for testing purposes"""
        ActBase.Registry = {}
        ActBase.Instances = {}
        cls.Index = 0
        cls.Aliases = ()
        cls._reregister()



    def __init__(self, *, name=None, iops=None, context=Context.enter, **kwa):
        """Initialization method for instance.

        Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            context (str): action context for act. default is "enter"

        """
        super(ActBase, self).__init__(**kwa) # in case of MRO
        self.name = name  # set name property
        self._iops = iops if iops is not None else {}  #
        self._context = context


    def __call__(self):
        """Make ActBase instance a callable object. run its .act method"""
        return self.act(**self.iops)


    def act(self, **iops):
        """Act called by Actor. Should override in subclass."""
        return iops  # for debugging


    @property
    def name(self):
        """Property getter for ._name

        Returns:
            name (str): unique identifier of instance
        """
        return self._name


    @name.setter
    def name(self, name=None):
        """Property setter for ._name

        Parameters:
            name (str|None): unique identifier of instance. When None generate
                unique name using .Index
        """
        while name is None or name in self.Instances:
                name = self.__class__.__name__ + str(self.Index)
                self.__class__.Index += 1   # do not shadow class attribute

        if not Renam.match(name):
            raise HierError(f"Invalid {name=}.")

        self.Instances[name] = self
        self._name = name


    @property
    def iops(self):
        """Property getter for ._iopts. Makes ._iopts read only

        Returns:
            iops (dict): input-output-parameters for .act
        """
        return self._iops


    @property
    def context(self):
        """Property getter for ._context. Makes ._context read only

        Returns:
            context (str): action context for .act
        """
        return self._context






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



