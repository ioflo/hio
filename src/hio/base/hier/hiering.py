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
    attrs.update(dict(Registry=base.Registry, Names=base.Names, Index=0))
    cls = type(name, (base, ), attrs)  # create new subclass of base of Act.
    register(cls)  # register subclass in cls.Registry

    def decorator(func):
        if not isinstance(func, Callable):
            raise hioing.HierError(f"Expected Callable got {func=}.")
        cls.act = func  # assign as bound method .act with injected self.

        @functools.wraps(func)
        def inner(*pa, **kwa):
            return cls(*pa, **kwa)  # instantiate and return instance
        return inner
    return decorator


def register(cls):
    """Class Decorator to add cls as cls.Registry entry for itself keyed by its
    own .__name__. Need class decorator so that class object is already created
    by registration time when decorator is applied
    """
    name = cls.__name__
    if name in cls.Registry:
        raise hioing.HierError(f"Act by {name=} already registered.")
    cls.Registry[name] = cls
    return cls


@register
class ActBase(Mixin):
    """Act Base Class. Callable with Registry of itself and its subclasses.

    Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Names (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.



    Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act

    Hidden
        ._name (str|None): unique name of instance
        ._iopts (dict): input-output-paramters for .act

    """
    Registry = {}  # subclass registry
    Names = {}  # instance name registry
    Index = 0  # naming index for default names of this subclasses instances

    @classmethod
    def _reregister(cls):
        """Reregisters cls after clear.
        Need to override in each subclass with super to reregister the class hierarchy
        """
        register(ActBase)


    @classmethod
    def _clear(cls):
        """Clears Registry, Names and Index for testing purposes"""
        ActBase.Registry = {}
        ActBase.Names = {}
        cls.Index = 0
        cls._reregister()



    def __init__(self, *, name=None, iops=None, **kwa):
        """Initialization method for instance.

        Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.

        """
        super(ActBase, self).__init__(**kwa) # in case of MRO
        self.name = name  # set name property
        self._iops = iops if iops is not None else {}  #


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
        while name is None or name in self.Names:
                name = self.__class__.__name__ + str(self.Index)
                self.__class__.Index += 1   # do not shadow class attribute

        if not Renam.match(name):
            raise HierError(f"Invalid {name=}.")

        self.Names[name] = self
        self._name = name


    @property
    def iops(self):
        """Property getter for ._iopts. Makes ._iopts read only

        Returns:
            iops (dict): input-output-parameters for .act
        """
        return self._iops






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



