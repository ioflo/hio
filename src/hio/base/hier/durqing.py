# -*- encoding: utf-8 -*-
"""hio.base.hier.durqing Module

Provides durable  queue for hold hierarchical actions

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections.abc import Iterable
from collections import deque
from typing import Any

from hio import HierError
from ...help import RegDom

class Durq():
    """Durq (durable queue) class when injected with
    .sdb and .key will store its ordered list durably and allow access as a FIFO
    queue

    Attributes:
        sdb (DomIoSuber): instance of durable store
        key (str): into .sdb

    Properties
        stale (bool): True means in-memory and durable on disk not synced
                     False means in-memory and durable on disk synced


    Hidden:
       _deq (deque):  in-memory cache
       _stale (bool): for .stale property:
                       True means in-memory and durable on disk not synced
                       False means in-memory and durable on disk synced

    """
    def __init__(self, sdb=None, key=None, **kwa):
        """Initialize instance

        """
        self._deq = deque()
        self._stale = True

        self.sdb = sdb
        self.key = key


    def __repr__(self):
        """Custom repr for Durq"""
        return (f"Durq({repr(list(self._deq))})")


    def __iter__(self):
        """Makes iterator out of self by returning iterable ._deq"""
        return iter(self._deq)

    def __len__(self):
        """Supports len()"""
        return len(self._deq)


    @property
    def stale(self):
        """Getter for ._stale

        Returns:
            stale (bool): True means in-memory and durable on disk not synced
                         False means in-memory and durable on disk synced
        """
        return self._stale


    def push(self, val: RegDom):
        """If not None, add val to right side of ._deq, Otherwise ignore
        Peforms equivalent operation on durable .sdb at .key if any

        Parameters:
            val (RegDom): element to be appended to deck (deque)
        """
        if val is not None:
            if not isinstance(val, RegDom):
                raise HierError(f"Expected RegDom instance got {val}")
            self._deq.append(val)
            if self.add(val) == False:  # durable
                raise HierError(f"Mismatch between cache and durable at "
                                f"key={self.key}")

    def pull(self, emptive=True):
        """Remove and return val from left side of ._deq,
        If empty and emptive return None else raise IndexError

        Peforms equivalent operation on durable .sdb at .key if any

        Parameters:
            emptive (bool): True means return None instead of raise IndexError
               when attempt to pull
               False means normal behavior of deque
        """
        try:
            val = self._deq.popleft()
        except IndexError:  # empty
            if self.sdb and self.key and self.pop() is not None:
                raise HierError(f"Mismatch between cache and durable at "
                                f"key={self.key}")
            if not emptive:
                raise
            return None

        # value to return
        if self.sdb and self.key and self.pop() is None:
            raise HierError(f"Mismatch between cache and durable at "
                            f"key={self.key}")
        return val


    def clear(self):
        """Clear all values from deque
        Peforms equivalent operation on durable .sdb at .key if any

        """
        self._deq.clear()
        self.rem()


    def count(self, value=None):
        """Returns count of entries in ._deq equal to value unless value
        is None then count all the values.

        Peforms equivalent operation on durable .sdb at .key if any
        """
        if value is None:
            cnt = len(self)
            dcnt = self.cnt()
            if dcnt is not None and cnt != dcnt:
                raise HierError(f"Mismatch between cache and durable at "
                                f"key={self.key}")
            return cnt

        # need to create a IoSuber.cntVal() so can compare
        return(self._deq.count(value))  # counts matching values


    def extend(self, vals: Iterable[RegDom]):
        """Extend ._deq with vals
        Peforms equivalent operation on durable .sdb at .key if any

        """
        for val in vals:
            if not isinstance(val, RegDom):
                raise HierError(f"Expected RegDom instance got {val}")
        self._deq.extend(vals)
        self.put(vals)


    def add(self, val):
        """Add value to .sdb at .key if any"""
        if self.sdb and self.key:
            self._stale = False
            return self.sdb.add(keys=self.key, val=val)
        return None


    def pop(self):
        """Pop value from .sdb at .key if any"""
        if self.sdb and self.key:
            return self.sdb.pop(keys=self.key)
        return None


    def rem(self):
        """Remove all values from .sdb at .key if any"""
        if self.sdb and self.key:
            return self.sdb.rem(keys=self.key)
        return None


    def cnt(self):
        """Count all values in .sdb at .key if any"""
        if self.sdb and self.key:
            return self.sdb.cnt(keys=self.key)
        return None


    def put(self, vals: Iterable[RegDom]):
        """Put (append) vals to .sdb at .key if any"""
        if self.sdb and self.key:
            self._stale = False
            return self.sdb.put(keys=self.key, vals=vals)
        return None


    def pin(self):
        """Pins all of ._deq to ._sdb at ._key if any.
        Sets ._stale to False on success
        """
        if self.sdb and self.key:
            vals = [val for val in self._deq]
            self.sdb.pin(self.key, vals)  # pin sdb._ser to ._deq vals
            self._stale = False
            return True
        return None


    def sync(self, force=False):
        """Syncs by checking exists durable copy in ._sdb at ._key. If so
        and ._stale or force then reads own data from ._sdb at ._key if any.
        If not attempts to write to ._sdb at ._key

        Parameters:
            force (bool): True means force read even if not ._stale
                          Flase means do not force read
        """
        if self.sdb and self.key and (self.stale or force):
            if self.sdb.cnt(self.key):  # not empty
                self._deq.clear()
                self._deq.extend(self.sdb.getIter(self.key))
                self._stale = False
                return True

            else: # empty
                return self.pin()

        return None

