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
from ...help import isNonStringIterable, MapDom, modify, Renam, Mine


"""Nabage (namedtuple):
Action nabes (contexts mileu neighborhood) for Acts

Fields:
   native (str): native nabe
   predo (str): predo nabe
   remark (str): remark sub-nabe of rendo
   rendo (str): rendo nabe
   enmark (str): enmark sub-nabe of endo
   endo (str): endo nabe
   redo (str): redo nabe
   ando (str): ando nabe
   godo (str): godo nabe
   exdo (str): exdo nabe
   rexdo (str): rexdo nabe
"""
Nabage = namedtuple("Nabage", "native predo remark rendo enmark endo"
                                      " redo ando godo exdo rexdo")

Nabes = Nabage(native="native", predo="predo", remark="remark",
                     rendo="rendo", enmark="enmark", endo="endo",
                     redo="redo", ando="ando", godo="godo",
                     exdo="exdo", rexdo="rexdo")


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
        acts (dict):  registry of ActBase subclasses by name (including aliases)
        context (str): action context for act
    """
    box: None | Box = None  # current box in boxwork. None if not yet any box
    over: None | Box = None  # current over box in boxwork. None if not yet any over
    bxpre: str = 'box'  # default box name prefix when name not provided
    bxidx: int = 0  # default box name index when name not provided
    acts: dict = field(default_factory=dict)  # registry of Acts by name & aliases
    nabe: str = Nabes.native  # current action nabe (context)



def actify(name, *, base=None, attrs=None):
    """Parametrized decorator that converts the decorated function func into
    .act method of new subclass of class base with .__name__ name. If not
    provided then uses Act as base. When provided base must be subclass of ActBase.
    Registers new subclass in ActBase.Registry. Then instantiates cls and returns
    instance.

    Returns:
        instance (cls): instance of new subclass

    Updates the class attributes of new subclass with attrs if any.

    Any callable usually function that is not already a subclass of ActBase can be
    converted to a subclass of ActBase and then registered in the Registry by its
    given name. Usually when defining a class simply make is a subclass of ActBase.
    But when given a function on can decorate it with actify so that a new
    subclass of ActBase is created and registered.

    Usage:
        @actify(name="Tact")
        def test(self, **kwa):  # signature for .act with **iops as **kwa
            assert kwa == self.iops
            return self.iops

        t = test(iops=dict(what=1), hello="hello", nabe=Nabe.redo)

    Notes:
    In Python, when a function is assigned as the value of a class attribute,
    the value of that attribute is automagically converted to a bound method of
    that class with injected self as first argument.

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
                      Names=() ))
    cls = type(name, (base, ), attrs)  # create new subclass of base of Act.
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
        names (None|str|Iterator): iterator of names as aliases besides class
            name to register class in Act registry and assigned to cls.Names

    """
    if not names:
        names = tuple()
    elif isinstance(names, str):
        names = (names, )  # make one tuple of str
    else:
        names = tuple(names)  # make tuple of iterable

    def decorator(cls):
        name = cls.__name__
        if name in cls.Registry:  # already registration for name
            if cls.Registry[name] is not cls:  # different cls at name
                raise hioing.HierError(f"Different Act by same {name=} already "
                                       f"registered.")
        else:  # not yet regisered under name
            cls.Registry[name] = cls
        cls.Names = names  # creates class specific attribute .Names
        for name in names:
            if name in cls.Registry:   # already registration for name
                if cls.Registry[name] is not cls:  # different cls at name
                    raise hioing.HierError(f"Different Act by same {name=} already "
                                           f"registered.")
            else:  # not yet registered under name
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
        Names (tuple[str]): tuple of aliases (names) under which this subclas
                            appears in .Registry. Created by @register

    Attributes:
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork

    Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act
        nabe (str): action nabe (context) for .act

    Hidden
        ._name (str|None): unique name of instance
        ._iopts (dict): input-output-paramters for .act
        ._nabe (str): action nabe (context) for .act

    """
    Registry = {}  # subclass registry
    Instances = {}  # instance name registry
    Index = 0  # naming index for default names of this subclasses instances
    #Names = ()  # tuple of aliases for this subclass created by @register


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
        if name in cls.Registry:  # already registration for name
            if cls.Registry[name] is not cls:  # different cls at name
                raise hioing.HierError(f"Different Act by same {name=} already "
                                           f"registered.")
        else:  # not yet registered under name
            cls.Registry[name] = cls
        return cls

    @classmethod
    def _clear(cls):
        """Clears Instances and and Index for testing purposes"""
        cls.Instances = {}
        cls.Index = 0


    @classmethod
    def _clearall(cls):
        """Clears Instances and and Index for testing purposes"""
        registry = ActBase.Registry.values()
        registry = set(registry)  # so only one copy, accounts for aliases
        for klas in registry:
            klas._clear()



    def __init__(self, *, name=None, iops=None, nabe=Nabes.endo,
                 mine=None, dock=None, **kwa):
        """Initialization method for instance.

        Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for act. default is "endo"
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        """
        super(ActBase, self).__init__(**kwa) # in case of MRO
        self.name = name  # set name property
        self._iops = dict(iops) if iops is not None else {}  # make copy
        self._nabe = nabe if nabe is not Nabes.native else Nabes.endo
        self.mine = mine if mine is not None else Mine()
        self.dock = dock   # stub fix later when have Dock class


    def __call__(self):
        """Make ActBase instance a callable object.
        Call its .act method with self.iops as parameters
        """
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
    def nabe(self):
        """Property getter for ._nabe. Makes ._nabe read only

        Returns:
            nabe (str): action nabe (context) for .act
        """
        return self._nabe


