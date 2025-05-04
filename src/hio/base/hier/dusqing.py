# -*- encoding: utf-8 -*-
"""hio.base.hier.dusqing Module

Provides durable set queue for hold hierarchical actions

"""
from __future__ import annotations  # so type hints of classes get resolved later

from ordered_set import OrderedSet as oset
from copy import deepcopy

from hio import HierError
from ...help import RegDom, IceRegDom, NonStringIterable

class Dusq():
    """Dusq (durable set queue) class when injected with
    .sdb and .key will store its ordered set durably and allow access as a
    deduped FIFO queue. A set is deduped.

    Properties
        stale (bool): True means in-memory and durable on disk not synced
                     False means in-memory and durable on disk synced
        durable (bool): True means ._sdb and ._key and ._sdb.db and
                                .sdb.db.opened are not None
                        False otherwise


    Hidden:
       _oset (oset):  in-memory cache as ordered set
       _sdb (DomIoSuber): instance of durable store
       _key (str): into .sdb
       _stale (bool): for .stale property:
                       True means in-memory and durable on disk not synced
                       False means in-memory and durable on disk synced

    """

    def __init__(self, *pa):
        """Initialize instance

        Parameters:
           pa[0] (NonStringeIteralble[RegDom]): instances to preload self._oset

        """
        self._oset = oset()
        self._stale = True

        self._sdb = None
        self._key = None

        if len(pa) > 1:
            raise TypeError(f"Expected 1 positional argument got {len(pa)}.")

        if pa:
            di = pa[0]
            if isinstance(di, NonStringIterable):
                self.update(di)

            else:
                raise TypeError(f"Expected NonStringIterable got "
                                f"{type(di)}.")


    def __repr__(self):
        """Custom repr for Dusq"""
        return (f"Dusq({repr(list(self._oset))})")


    def __iter__(self):
        """Makes iterator out of self by returning iterable ._deq"""
        return iter(tuple(val if val.__dataclass_params__.frozen else deepcopy(val)
                          for val in self._oset))  # ensure not mutable outside
        #return iter(self._oset)

    def __len__(self):
        """Supports len()"""
        return len(self._oset)


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


    def update(self, vals: NonStringIterable[RegDom|IceRegDom], *, deep=True):
        """Update ._deq with vals
        Peforms equivalent operation on durable .sdb at .key if any

        Parameters:
            vals (NonStringIterable[RegDom]): to add to dusq
            deep (bool): True means deepcopy to ensure can't mutate outside
                         False means do not deepcopy

        """
        for val in vals:
            if not isinstance(val, (RegDom, IceRegDom)):
                raise HierError(f"Expected RegDom instance got {val}")
        vals = tuple(val if val.__dataclass_params__.frozen else deepcopy(val)
                     for val in vals)  # so can't mutate
        prior = len(self)
        self._oset.update(vals)
        unique = len(self._oset) > prior  # uniquely added some val from vals to set
        if unique:
            if self.put(vals) is False:  # durable unique update but put failed
                raise HierError(f"Mismatch between cache and durable at "
                                f"key={self._key}")
            return True
        return False


    def push(self, val: RegDom|IceRegDom):
        """If not None, add val add val to last in if unique. Otherwise ignore
        Peforms equivalent operation on durable .sdb at .key if any

        Parameters:
            val (RegDom): element to be appended to deck (deque)
        """
        if val is not None:
            if not isinstance(val, (RegDom, IceRegDom)):
                raise HierError(f"Expected RegDom instance got {val}")
            # so can't mutate
            val = val if val.__dataclass_params__.frozen else deepcopy(val)
            prior = len(self._oset)
            self._oset.add(val)
            unique = len(self._oset) > prior  # uniquely added val to set
            result = self.add(val)
            if unique and result == False:  # durable unique but not added
                raise HierError(f"Mismatch between cache and durable at "
                                f"key={self._key}")
            return True
        return False


    def pull(self, emptive=True):
        """Remove and return first in val
        If empty and emptive return None else raise IndexError

        Peforms equivalent operation on durable .sdb at .key if any

        Parameters:
            emptive (bool): True means return None instead of raise IndexError
               when attempt to pull
               False means normal behavior of deque
        """
        try:
            val = self._oset[0]
            self._oset.remove(val)
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
        # value to return ensure not mutable outside
        return val if val.__dataclass_params__.frozen else deepcopy(val)


    def clear(self):
        """Clear all values
        Peforms equivalent operation on durable .sdb at .key if any
        """
        prior = len(self._oset)
        self._oset.clear()
        unique = prior > 0
        if not unique:
            return False

        if self.rem() == False:
            raise HierError(f"Mismatch between cache and durable at "
                            f"key={self._key}")
        return True


    def remove(self, value: RegDom|IceRegDom):
        """Remove value if contained

        Returns:
            result (bool): True value was removed
                           Raises KeyError if value not found

        Peforms equivalent operation on durable .sdb at .key if any
        """
        if not isinstance(val, (RegDom, IceRegDom)):
            raise HierError(f"Expected RegDom instance got {val}")
         # so can't mutate
        val = val if val.__dataclass_params__.frozen else deepcopy(val)
        try:
            self._oset.remove(value)
        except KeyError as ex:
            return False
        else:
            if self.rem(value) == False:
                raise HierError(f"Mismatch between cache and durable at "
                                f"key={self._key}")
        return True


    def put(self, vals: NonStringIterable[RegDom|IceRegDom]):
        """Put (append) vals to .sdb at .key if any and unique to set"""
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


    def rem(self, val=None):
        """Remove all values from .sdb at .key if any"""
        if self.durable:
            return self._sdb.rem(keys=self._key, val=val)
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
            vals = [val for val in self._oset]
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
                self._oset.clear()
                self._oset.update(self._sdb.getIter(self._key))
                self._stale = False
                return True

            else: # empty
                return self.pin()

        return None
