# -*- encoding: utf-8 -*-
"""hio.base.hier.bagging Module

Provides dom support for items hold

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections import deque, namedtuple
from collections.abc import Iterable, Mapping, Callable
from typing import Any, Type, ClassVar
from dataclasses import dataclass, astuple, asdict, field, fields, InitVar

from ...help import registerify, namify, TymeDom, IceTymeDom
from ...hioing import HierError


@namify
@registerify
@dataclass(frozen=True)
class IceBag(IceTymeDom):
    """IceBag is frozen version of Bag which is TymeDom subclass with generic
    value field.

    Supports the cycle tyme stamping of updates to named fields using non-field attributes.

    This allows registry based creation of instances from the class name.

    Enables dataclass instances to use Mapping item syntax except for __delattr__
    because dataclasses to not allow __delattr__ to be overridden

    A non-frozen dataclass may not be a subclass of a frozen dataclass neither
    may a frozen dataclass be a subclass of a frozen dataclass.

    Frozen dataclass do not allow change or upate of either field or non-field
    attributes after __init__ this includes in the  __post_init__ method.

    Inherited Non-Field Class Attributes:
        _registry (ClassVar[dict]): dict of subclasses keyed by class.__name__
            Assigned by @registerify decorator
        _names (ClassVar[tuple[str]|None]): tuple of field names for class
            Assigned by @namify decorator

    Inherited Properties:
        _tymth (None|Callable):  Emulates interface for non-frozen TymeDom
                                 Returns None
        _tyme (None|Float): Emulates interface for non-frozen TymeDom
                            Returns None
        _now (None|float): Emulates interface for non-frozen TymeDom
                           Returns None

    Field Attributes:
       value (Any):  generic value field
    """
    value: Any = None  # generic value


@namify
@registerify
@dataclass
class Bag(TymeDom):
    """Bag is simple TymeDom subclass with generic value field.

    Supports the cycle tyme stamping of updates to named fields using non-field attributes.

    This allows registry based creation of instances from the class name.

    Enables dataclass instances to use Mapping item syntax except for __delattr__
    because dataclasses to not allow __delattr__ to be overridden

    A non-frozen dataclass may not be a subclass of a frozen dataclass neither
    may a frozen dataclass be a subclass of a frozen dataclass.


    Inherited Non-Field Class Attributes:
        _registry (ClassVar[dict]): dict of subclasses keyed by class.__name__
            Assigned by @registerify decorator
        _names (ClassVar[tuple[str]|None]): tuple of field names for class
            Assigned by @namify decorator

    Inherited Non-Field Attributes:
        _tymth (None|Callable): function wrapper closure returned by
            Tymist.tymen() method. When .tymth is called it returns associated
            Tymist.tyme. Provides injected dependency on Tymist cycle tyme base.
            None means not assigned yet.
            Use ._wind method to assign ._tymth after init of bag.
        _tyme (None|Float): cycle tyme of last update of a bag field.
            None means either ._tymth as not yet been assigned or this bag's
            fields have not yet been updated.

    Inherited Properties:
        _now (None|float): current tyme given by ._tymth if not None.

    Field Attributes:
       value (Any):  generic value field
    """
    value: Any = None  # generic value


    def __hash__(self):
        """Define hash so can work with ordered_set
        __hash__ is not inheritable in dataclasses so must be explicitly defined
        in every subclass
        """
        return hash((self.__class__.__name__,) + self._astuple())  # almost same as __eq__

