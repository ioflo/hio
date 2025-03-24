# -*- encoding: utf-8 -*-
"""
hio.core.hier.acting Module

Provides hierarchical action support

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections.abc import Callable
from collections import namedtuple

from ... import hioing
from ...hioing import Mixin, HierError
from .hiering import Reat, Lode

"""Actage (namedtuple):
Callable object and its keyword args to be injected and called at run time.

Fields:
   act (Callable): callable object. Must have name attribute
   kwa (dict): key word args to be injected at runtime into act.
"""
Actage = namedtuple("Actage", "act kwa")



# ToDO change this so that its looking for a callable with a .name attribute
# or property hasattr works for both. If not then add .name as attribute
# then either callable subclasses or functions will work the same with regards
# name. The name is used for introspection logging debugging etc. Can set a
# conditional breakpoint based on Actor.name for a given act (actage) entry
# in a box.  Look as doify for coping the function not just decorating it in place
#

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
        Registry (dict): keyed by subclass name of subclasses
        Index (int): default naming index for subclass instances


    Properties:
        name (str): unique name string of instance

    Hidden
        ._name (str|None): unique name of instance

    """
    Registry = dict()  # Actor subclass registry
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


