# -*- encoding: utf-8 -*-
"""
hio.core.hier.acting Module

Provides hierarchical action support

"""
from __future__ import annotations  # so type hints of classes get resolved later

from ...hioing import Mixin, HierError



class Act(Mixin):
    """Base class for acts """
    __slots__ = ('frame', 'context', 'act', 'actor','parms')

    def __init__(self, action=None, parms=None, **kwa):
        """
        Initialization method for instance.

        Attributes:
            .actor = ref to Actor instance or actor name to be resolved
                    call performs instances method action
            .parms = dictionary of keyword arguments for Actor instance call

        """
        super(Act,self).__init__(**kwa) # in case of MRO


        self.action = action  # callable function or instance that performs action
        self.parms = parms if parms is not None else {} # parms must always be not None


    def __call__(self): #make Act instance callable as function
        """ Define act as callable object """
        return (self.action(**self.parms))


class Actor(Mixin):
    """ Actor Base Class
        Has Actor specific Registry of classes
    """
    Registry = odict() # Actor Registry
    Parms = odict() # class defaults
    __slots__ = ('name', 'store')

    def __init__(self, name='', store=None, **kwa ):
        """
        Initialization method for instance.

        Instance attributes
            .name = name string for Actor variant in class Registry
            .store = reference to shared data Store
        """
        super(Actor,self).__init__(**kwa) # in case of MRO

        self.name = name
        if store is not None:
            if  not isinstance(store, storing.Store):
                raise ValueError("Not store {0}".format(store))
            self.store = store

    def __call__(self, **kwa):
        """ run .action  """
        return self.act(**kwa)

    def act(self, **kwa):
        """Act called by Actor. Should override in subclass."""
        pass


def actify(name, *, base=None, attrs=None, registry=None):
    """ Parametrized decorator function that converts the decorated function
    into an Actor sub class with .act method and with class name that
    is name and registers the new subclass in the registry under name as
    a subclass of base. The default base is Actor.

    The parameters  name, parms if provided,
    are used to create the class attributes for the new subclass

    """
    base = base or Actor
    if not issubclass(base, Actor):
        msg = "Base class '{0}' not subclass of Actor".format(base)
        raise excepting.RegisterError(msg)

    attrs = attrs if attrs is not None else {}
    cls = type(name, (base, ), attrs )

    def decorator(func):
        @wraps(func)
        def inner(*pa, **kwa):
            return func(*pa, **kwa)
        cls.act = inner  # method
        return inner
    return decorator
