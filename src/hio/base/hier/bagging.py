# -*- encoding: utf-8 -*-
"""hio.base.hier.bagging Module

Provides dom support for items hold

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections import deque, namedtuple
from collections.abc import Iterable, Mapping, Callable
from typing import Any, Type, ClassVar
from dataclasses import dataclass, astuple, asdict, field, fields, InitVar

from ...help import RawDom, NonStringIterable
from ...hioing import HierError
from ..during import SuberBase, Suber


def registerify(cls):
    """Class Decorator to add cls as cls._registry entry for itself keyed by its
    own .__name__. Need class decorator so that class object is already created
    by registration time when decorator is applied
    """
    name = cls.__name__
    if name in cls._registry:
        raise HierError(f"TymeDom subclass {name=} already registered.")
    cls._registry[name] = cls
    return cls


def namify(cls):
    """Class decorator for dataclass to populate ClassVar ._names with names
    of all fields in dataclass
    """
    cls._names = tuple(field.name for field in fields(cls))
    return cls



@namify
@registerify
@dataclass
class TymeDom(RawDom):
    """TymeDom is base class for Bagish subclasses with common fields.

    Field Attributes:

    Non-Field Class Attributes:
        _registry (ClassVar[dict]): dict of subclasses keyed by class.__name__
            Assigned by @registerify decorator
        _names (ClassVar[tuple[str]|None]): tuple of field names for class
            Assigned by @namify decorator

    Non-Field Attributes:
        _tymth (None|Callable): function wrapper closure returned by
            Tymist.tymen() method. When .tymth is called it returns associated
            Tymist.tyme. Provides injected dependency on Tymist cycle tyme base.
            None means not assigned yet.
            Use ._wind method to assign ._tymth after init of bag.
        _tyme (None|Float): cycle tyme of last update of a bag field.
            None means either ._tymth as not yet been assigned or this bag's
            fields have not yet been updated.

    Properties:
        _now (None|float): current tyme given by ._tymth if not None.

    """
    _registry:  ClassVar[dict] = {}  # subclass registry
    _names: ClassVar[tuple[str]|None] = None  # Assigned in  __post_init__
    _tymth: InitVar[None|Callable] = None  # tymth closure not a field
    _tyme: InitVar[None|float] = None  # tyme of last update

    def __post_init__(self, _tymth, _tyme):
        self._tymth = _tymth
        self._tyme = _tyme


    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name in self._names:
            super().__setattr__("_tyme", self._now)


    def __setitem__(self, k, v):
        try:
            return setattr(self, k, v)
        except AttributeError as ex:
            raise IndexError(ex.args) from ex


    def _update(self, *pa, **kwa):
        """Use item update syntax
        """
        if len(pa) > 1:
            raise TypeError(f"Expected 1 positional argument got {len(pa)}.")

        if pa:
            di = pa[0]
            if isinstance(di, Mapping):
                for k, v in di.items():
                    self[k] = v
            elif isinstance(di, NonStringIterable):
                for k, v in di:
                    self[k] = v
            else:
                raise TypeError(f"Expected Mapping or NonStringIterable got"
                                f" {type(di)}.")

        for k, v in kwa.items():
            self[k] = v


    @property
    def _now(self):
        """Gets current tyme from injected ._tymth closure from Tymist.
        tyme is float cycle time in seconds
        Returns:
            _now (float | None): tyme from self.tymth() when wound else None
        """
        return self._tymth() if self._tymth else None


    def _wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Override in subclasses to update any dependencies on a change in
        tymist.tymth base
        """
        self._tymth = tymth


@namify
@registerify
@dataclass
class Bag(TymeDom):
    """Bag is simple TymeDom sublclass with generic value field.

    Inherited Non-Field Class Attributes:
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


