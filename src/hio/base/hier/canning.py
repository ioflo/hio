# -*- encoding: utf-8 -*-
"""hio.base.hier.canning Module

Provides durable dom support for items in Hold

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections.abc import Mapping
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
        _stale (bool): True means fields not yet been synced by write to durable
                       False means fields have been synced by write to durable
        _fresh (bool): True means fields have been synced by read from durable
                       False means fields have not yet been synced by read from durable


    """
    _sdb: InitVar[None|holding.DomSuber] = None  # durable storage of serialized fields
    _key: InitVar[None|str] = None  # durable storage of serialized fields
    _stale: InitVar[bool] = True  # fields synced by write to durable or not
    _fresh: InitVar[bool] = False  # fields synced by read from durable or not


    def __post_init__(self, _tymth, _tyme, _sdb, _key, _stale, _fresh):
        super(CanDom, self).__post_init__(_tymth, _tyme)
        self._sdb = _sdb
        self._key = _key
        self._stale = _stale
        self._fresh = _fresh


    def __setattr__(self, name, value):  # called by __setitem__
        super().__setattr__(name, value)
        if name in self._names:
            super().__setattr__("_tyme", self._now)
            self._write()


    def _update(self, *pa, **kwa):
        """Use item update syntax
        """
        write = False

        if pa:
            if len(pa) > 1:
                raise TypeError(f"Expected 1 positional argument got {len(pa)}.")

            di = pa[0]
            if isinstance(di, Mapping):
                for k, v in di.items():
                    self[k] = v
                    if k in self._names:
                        write = True

            elif isinstance(di, NonStringIterable):
                for k, v in di:
                    self[k] = v
                    if k in self._names:
                        write = True
            else:
                raise TypeError(f"Expected Mapping or NonStringIterable got"
                                f" {type(di)}.")

        for k, v in kwa.items():
            self[k] = v
            if k in self._names:
                write = True

        if write:
            self._write()


    def _write(self):
        """Writes own fields to ._sdb at ._key if any when not ._fresh.
        Sets ._stale to False on success
        """
        if self._sdb and self._key and not self._fresh:
            self._sdb.pin(self._key, self)  # pin sdb._ser of own fields at key
            self._stale = False
            return True
        return False


    def _read(self, force=False):
        """Reads own fields from ._sdb at ._key if any when ._stale.
        Toggles ._fresh so can update own fields from read without triggering
        a write.

        Parameters:
            force (bool): True means force read even if not ._stale
                          Flase means do not force read
        """
        if self._sdb and self._key and (self._stale or force):
            if can := self._sdb.get(self._key):  # get seb._des of own fields at key
                self._fresh = True  # so update does not write
                self._update(can._asdict())
                self._fresh = False
                return True
        return False




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




