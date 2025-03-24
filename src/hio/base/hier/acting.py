# -*- encoding: utf-8 -*-
"""
hio.core.hier.acting Module

Provides hierarchical action support

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections.abc import Callable
from collections import namedtuple

from ...hioing import Mixin, HierError
from .hiering import Reat, Lode

"""Actage (namedtuple):
Callable object and its keyword args to be injected and called at run time.

Fields:
   act (Callable): callable object. Must have name attribute
   kwa (dict): key word args to be injected at runtime into act.
"""
Actage = namedtuple("Actage", "act kwa")


class Actor(Mixin):
    """Actor Callable Base Class. Has Actor specific Registry of classes

    Class Attributes:
        Registry (dict): keyed by subclass name of subclasses
        Index (int): default naming index for subclass instances
        Attrs (dict): default subclass attributes

    Properties:
        name

    Hidden
        ._name (str|None): unique name of Actor instance

    """
    Registry = dict()  # Actor subclass registry
    Index = 0  # naming index for default names of subclass instances
    Attrs = dict()  # subclass specific default attributes

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



def actify(name, *, base=None, attrs=None, registry=None):
    """ Parametrized decorator function that converts the decorated function
    into an Actor sub class with .act method and with class name that
    is name and registers the new subclass in the registry under name as
    a subclass of base. The default base is Actor.

    The parameters  name, attr if provided,
    are used to create the class attributes for the new subclass

    """
    base = base or Actor
    if not issubclass(base, Actor):
        raise hioing.HierError(f"Base={base} not Actor subclass.")

    # make this smarted and apply to functions with function attributes for
    # actor slots name, bags

    attrs = attrs if attrs is not None else {}
    cls = type(name, (base, ), attrs )

    def decorator(func):
        @wraps(func)
        def inner(*pa, **kwa):
            return func(*pa, **kwa)
        cls.act = inner  # method
        return inner
    return decorator
