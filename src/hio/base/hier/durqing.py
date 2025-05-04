# -*- encoding: utf-8 -*-
"""hio.base.hier.durqing Module

Provides durable  queue for hold hierarchical actions

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections import deque
from typing import Any

from hio import HierError
from ...help import RegDom, IceRegDom, NonStringIterable

class Durq():
    """Durq (durable queue) class when injected with
    .sdb and .key will store its ordered list durably and allow access as a FIFO
    queue

    Properties
        stale (bool): True means in-memory and durable on disk not synced
                     False means in-memory and durable on disk synced
        durable (bool): True means ._sdb and ._key and ._sdb.db and
                                .sdb.db.opened are not None
                        False otherwise


    Hidden:
       _deq (deque):  in-memory cache as deque
       _sdb (DomIoSuber): instance of durable store
       _key (str): into .sdb
       _stale (bool): for .stale property:
                       True means in-memory and durable on disk not synced
                       False means in-memory and durable on disk synced

    """
    def __init__(self, *pa):
        """Initialize instance

        Parameters:
           pa[0] (NonStringeIteralble[RegDom]): instances to preload self._deq

        """
        self._deq = deque()
        self._stale = True

        self._sdb = None
        self._key = None

        if len(pa) > 1:
            raise TypeError(f"Expected 1 positional argument got {len(pa)}.")

        if pa:
            di = pa[0]
            if isinstance(di, NonStringIterable):
                self.extend(di)

            else:
                raise TypeError(f"Expected NonStringIterable got "
                                f"{type(di)}.")


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

    @property
    def durable(self):
        """Property durable True when durable subdb injected and opened.

        Returns:
            durable (bool): True means ._sdb and ._key and ._sdb.db and
                                .sdb.db.opened are not None
                            False otherwise
        """
        return (self._sdb is not None and self._key is not None and self._sdb.db
                and self._sdb.db.opened)


    def extend(self, vals: NonStringIterable[RegDom|IceRegDom]):
        """Extend ._deq with vals
        Peforms equivalent operation on durable .sdb at .key if any

        """
        if not vals:
            return False

        for val in vals:
            if not isinstance(val, (RegDom, IceRegDom)):
                raise HierError(f"Expected RegDom instance got {val}")

        self._deq.extend(vals)
        if self.put(vals) is False:  # durable but put failed
            raise HierError(f"Mismatch between cache and durable at "
                            f"key={self._key}")
        return True


    def push(self, val: RegDom|IceRegDom):
        """If not None, add val to last in. Otherwise ignore
        Peforms equivalent operation on durable .sdb at .key if any

        Parameters:
            val (RegDom): element to be appended to deck (deque)
        """
        if val is not None:
            if not isinstance(val, (RegDom, IceRegDom)):
                raise HierError(f"Expected RegDom instance got {val}")
            self._deq.append(val)
            result = self.add(val)
            if result == False:  # durable but not added
                raise HierError(f"Mismatch between cache and durable at "
                                f"key={self._key}")
            return True
        return False


    def pull(self, emptive=True):
        """Remove and return first in value
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
            if self.durable and self.pop() is not None:
                raise HierError(f"Mismatch between cache and durable at "
                                f"key={self._key}")
            if not emptive:
                raise
            return None
        else:  # successfully popped so pop from ._sdb
            if self.durable and self.pop() is None:  # not popped from ._sdb
                raise HierError(f"Mismatch between cache and durable at "
                                f"key={self._key}")

        return val  # value to return


    def clear(self):
        """Clear all values from deque
        Peforms equivalent operation on durable .sdb at .key if any

        """
        prior = len(self._deq)
        self._deq.clear()
        unique = prior > 0
        if not unique:
            return False

        if self.rem() == False:
            raise HierError(f"Mismatch between cache and durable at "
                            f"key={self._key}")
        return True


    def count(self, value):
        """Returns count of entries in ._deq equal to value
        """
        return(self._deq.count(value))  # counts matching values



    def put(self, vals: NonStringIterable[RegDom|IceRegDom]):
        """Put (append) vals to .sdb at .key if any"""
        if self.durable:
            self._stale = False
            return self._sdb.put(keys=self._key, vals=vals)
        return None


    def add(self, val):
        """Add value to .sdb at .key if any"""
        if self.durable:
            self._stale = False
            return self._sdb.add(keys=self._key, val=val)
        return None


    def pop(self):
        """Pop value from .sdb at .key if any"""
        if self.durable:
            return self._sdb.pop(keys=self._key)
        return None


    def rem(self):
        """Remove all values from .sdb at .key if any"""
        if self.durable:
            return self._sdb.rem(keys=self._key)
        return None


    def cnt(self):
        """Count all values in .sdb at .key if any"""
        if self.durable:
            return self._sdb.cnt(keys=self._key)
        return None


    def pin(self):
        """Pins all of ._deq to ._sdb at ._key if any.
        Sets ._stale to False on success
        """
        if self.durable:
            vals = [val for val in self._deq]
            self._sdb.pin(self._key, vals)  # pin sdb._ser to ._deq vals
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
        if self.durable and (self.stale or force):
            if self._sdb.cnt(self._key):  # not empty
                self._deq.clear()
                self._deq.extend(self._sdb.getIter(self._key))
                self._stale = False
                return True

            else: # empty
                return self.pin()

        return None

