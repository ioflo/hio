# -*- encoding: utf-8 -*-
"""hio.base.hier.canning Module

Provides durable dom support for items in Hold

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections.abc import Mapping
from typing import Any, Type, ClassVar
from dataclasses import dataclass, astuple, asdict, field, fields, InitVar

from ...help import NonStringIterable, namify, registerify, TymeDom
from ...hioing import HierError
from ..during import DomSuber


@namify
@registerify
@dataclass
class CanDom(TymeDom):
    """CanDom is base class that adds support for durable storage via its
    ._sdb and ._key non-field attributes. Essentially acts as write through
    cache to durable copy in ._sdb at ._key when provided. Otherwise in memory
    only. Assignment to Hold instance at key, injects ._sdb and ._key. This
    makes the in-memory key in Hold and the durable key the same.

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
        _stale (bool): True means fields not yet been synced by write/read with durable
                       False means fields have been synced by write/read with durable
        _fresh (bool): True means fields being synced by read from durable
                       False means fields not being synced by read from durable
        _bulk (bool): True means do not write individual fields wait for bulk update
                      False means write individual fields as updated

    """
    _sdb: InitVar[None|DomSuber] = None  # durable storage of serialized fields
    _key: InitVar[None|str] = None  # durable storage of serialized fields
    _stale: InitVar[bool] = True  # fields synced by write to durable or not
    _fresh: InitVar[bool] = False  # fields synced by read from durable or not
    _bulk: InitVar[bool] = False  # bulk update or not


    def __post_init__(self, _tymth, _tyme, _sdb, _key, _stale, _fresh, _bulk):
        super(CanDom, self).__post_init__(_tymth, _tyme)
        self._sdb = _sdb
        self._key = _key
        self._stale = _stale
        self._fresh = _fresh
        self._bulk = _bulk


    def __setattr__(self, name, value):  # called by __setitem__
        super().__setattr__(name, value)
        if name in self._names:
            super().__setattr__("_tyme", self._now)
            if not self._bulk:
                self._write()


    def _update(self, *pa, **kwa):
        """Use item update syntax
        """
        write = False
        try:
            self._bulk = True
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
        finally:
            self._bulk = False


    def _write(self):
        """Writes own fields to ._sdb at ._key if any when not ._fresh.
        Sets ._stale to False on success
        """
        if self._sdb and self._key and not self._fresh:
            self._sdb.pin(self._key, self)  # pin sdb._ser of own fields at key
            self._stale = False
            return True
        return False


    def _sync(self, force=False):
        """Syncs by checking exists durable copy in ._sdb at ._key. If so
        and ._stale or force then reads own fields from ._sdb at ._key if any.
        If not attempts to write to ._sdb at ._key
        Toggles ._fresh during read so can update own fields from read without
        triggering a write.

        Parameters:
            force (bool): True means force read even if not ._stale
                          Flase means do not force read
        """
        if self._sdb and self._key and (self._stale or force):
            if can := self._sdb.get(self._key):  # get seb._des of own fields at key
                if can.__class__ != self.__class__:
                    raise HierError(f"Expected instance of "
                                    f"{self.__class__} on read, got "
                                    f"{can.__class__}")
                self._fresh = True  # so update does not write
                self._update(can._asdict())
                self._fresh = False
                self._stale = False  # now synced
                return True
            else:
                return self._write()
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




