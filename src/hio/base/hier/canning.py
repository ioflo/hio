# -*- encoding: utf-8 -*-
"""hio.base.hier.canning Module

Provides durable dom support for items in Hold

"""
from __future__ import annotations  # so type hints of classes get resolved later


from typing import Any, Type, ClassVar
from dataclasses import dataclass, astuple, asdict, field, fields, InitVar

from ...help import NonStringIterable
from ...hioing import HierError
from .bagging import namify, registerify, TymeDom
from ..hier import holding


@namify
@registerify
@dataclass
class CanDom(TymeDom):
    """CanDom is base class that adds support for durable storage via its
    ._sdb and ._key non-field attributes

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

    Non-Field Attributes:
        _sdb (DomSuber|None): SuberBase subclass instance of durable subdb of Duror
        _key (str|None): database key used to store serialized field in ._cans


    """
    _sdb: InitVar[None|holding.DomSuber] = None  # durable storage of serialized fields
    _key: InitVar[None|str] = None  # durable storage of serialized fields

    def __post_init__(self, _tymth, _tyme, _sdb, _key):
        super(CanDom, self).__post_init__(_tymth, _tyme)
        self._sdb = _sdb
        self._key = _key



@namify
@registerify
@dataclass
class Can(CanDom):
    """CanDom is base class that adds support for durable storage via its ._cans
    non-field attribute

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
        _sdb (DomSuber|None): SuberBase subclass instance of durable subdb of Duror
        _key (str|None): database key used to store serialized field in ._cans

    Inherited Properties:
        _now (None|float): current tyme given by ._tymth if not None.

    Field Attributes:
        value (Any):  generic value field
    """
    value: Any = None  # generic value




