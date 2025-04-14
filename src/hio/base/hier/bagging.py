# -*- encoding: utf-8 -*-
"""hio.core.hier.bagging Module

Provides dom support for items in Mine or Dock for shared data store support

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections import deque, namedtuple
from collections.abc import Iterable, Mapping, Callable
from typing import Any, Type, ClassVar
from dataclasses import dataclass, astuple, asdict, field, fields, InitVar

from ...help import RawDom

def namify(cls):
    """Class decorator for dataclass to populate ClassVar ._names with names
    of all fields in dataclass
    """
    cls._names = tuple(field.name for field in fields(cls))
    return cls


@namify
@dataclass
class TymeDom(RawDom):
    """TymeDom is base class for Bag subclasses with common fields.

    Field Attributes:

    Non-Field Class Attributes:
        _names (ClassVar[tuple[str]|None]): tuple of field names for class
            Assigned in .__post_init__

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
            elif isinstance(di, Iterable):
                for k, v in di:
                    self[k] = v
            else:
                raise TypeError(f"Expected Mapping or Iterable got {type(di)}.")

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
@dataclass
class Bag(TymeDom):
    """Bag is simple BagDom sublclass with generic value field.

    Inherited Non-Field Class Attributes:
        _names (ClassVar[tuple[str]|None]): tuple of field names for class
            Assigned in .__post_init__

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
