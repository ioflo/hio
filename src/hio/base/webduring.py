# -*- encoding: utf-8 -*-
"""Browser-safe durable storage for HIO wrappers."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import json

from ordered_set import OrderedSet as oset
from sortedcontainers import SortedDict

import hio

from hio import HierError
from .filing import Filer

try:
    from pyscript import storage
except ImportError:  # pragma: no cover
    storage = None


_RECORDS_KEY = "__records__"


async def _clear_handles(handles):
    """Clear persisted records for captured browser storage handles."""
    for handle in handles.values():
        handle[_RECORDS_KEY] = "{}"
        await handle.sync()


async def _persist_stores(handles, stores, dirty):
    """Persist captured dirty stores through captured browser storage handles."""
    persisted = []
    for store in tuple(stores):
        if store not in dirty:
            continue
        handles[store][_RECORDS_KEY] = json.dumps(
            {key.hex(): val.hex() for key, val in stores[store].items()},
            sort_keys=True,
        )
        await handles[store].sync()
        persisted.append(store)
    return persisted


def _to_bytes(value):
    if isinstance(value, memoryview):
        return bytes(value)
    if hasattr(value, "encode"):
        return value.encode("utf-8")
    return bytes(value)


class WebSubDb:
    """LMDB-like sub-database handle for existing wrapper classes."""

    def __init__(self, *, key, dupsort, items):
        self.key = _to_bytes(key)
        self.dupsort = True if dupsort else False
        self.items = items

    def flags(self):
        return {"dupsort": self.dupsort}


class WebDuror(Filer):
    """Browser durable storage with Duror-compatible method semantics.

    Uses an async PyScript style storage opener instead of LMDB and exposes the
    same low-level db methods used by Duror wrappers.
    """

    SuffixSize = 32
    MaxSuffix = int("f" * SuffixSize, 16)
    MetaStore = b"__meta__"
    VersionKey = b"__version__"

    def __init__(
        self,
        *,
        name="main",
        base="",
        temp=False,
        reopen=False,
        clear=False,
        stores=None,
        storageOpener=None,
        **kwa,
    ):
        """Setup browser durable storage state.

        Parameters:
            stores (Iterable[bytes|str]): sub-database names to open.
            storageOpener (Callable): async opener for a named browser storage namespace.
        """
        if kwa:
            raise HierError(f"Unsupported WebDuror parameters: {', '.join(kwa)}")
        super(WebDuror, self).__init__(
            name=name,
            base=base,
            temp=temp,
            reopen=False,
            clear=clear,
        )
        self.env = None
        self._version = None
        self._stores = {}
        self._handles = {}
        self._dirty = set()
        self._store_names = () if stores is None else tuple(_to_bytes(store) for store in stores)
        self._storageOpener = storageOpener

        if reopen:
            raise HierError("WebDuror uses async open; use await reopen() or openWebDuror().")

    def open_db(self, key=None, dupsort=False):
        if not self.opened or self.env is None:
            raise HierError("WebDuror is not open.")
        store = self.MetaStore if key is None else _to_bytes(key)
        if store not in self._stores:
            raise HierError(f"WebDuror store {store!r} was not declared before open.")

        return WebSubDb(
            key=store,
            dupsort=dupsort,
            items=self._stores[store],
        )

    async def reopen(
        self,
        *,
        clear=False,
        stores=None,
        storageOpener=None,
        temp=None,
        **kwa,
    ):
        """Open declared browser storage namespaces and load persisted records."""
        if kwa:
            raise HierError(f"Unsupported WebDuror reopen parameters: {', '.join(kwa)}")
        if stores is not None:
            self._store_names = tuple(_to_bytes(store) for store in stores)
        if storageOpener is not None:
            self._storageOpener = storageOpener
        if temp is not None:
            self.temp = True if temp else False

        if self.opened:
            await self.aclose(clear=clear)

        opener = self._storageOpener if self._storageOpener is not None else storage
        if opener is None:
            raise HierError("WebDuror requires pyscript.storage or storageOpener.")

        declared = (self.MetaStore,) + tuple(store for store in self._store_names if store != self.MetaStore)
        handles = {}
        loaded = {}
        for store in declared:
            name = store.decode("utf-8")
            namespace = f"{self.base}:{self.name}:{name}" if self.base else f"{self.name}:{name}"
            handle = await opener(namespace)
            if clear:
                handle[_RECORDS_KEY] = "{}"
                await handle.sync()
            raw = handle.get(_RECORDS_KEY)
            if raw in (None, ""):
                records = {}
            else:
                if isinstance(raw, (bytes, memoryview)):
                    raw = bytes(raw).decode("utf-8")
                if isinstance(raw, str):
                    payload = json.loads(raw)
                elif isinstance(raw, dict):
                    payload = raw
                else:
                    raise TypeError(f"Unsupported persisted record payload type: {type(raw)}")
                records = {
                    bytes.fromhex(str(key)): bytes.fromhex(str(val))
                    for key, val in payload.items()
                }
            handles[store] = handle
            loaded[store] = SortedDict(records)

        self._stores = loaded
        self._handles = handles
        self._dirty = set()
        self.env = self
        self.opened = True
        self._version = None

        if self.getVer() is None:
            self.version = hio.__version__
            await self.flush()

        return self.opened

    def close(self, clear=False):
        """Close local handles after persisting or clearing pending state.

        When called inside a running loop, persistence is scheduled on that loop.
        Use await aclose() when the caller must wait for completion.
        """
        if self.opened and (clear or self._dirty):
            handles = dict(self._handles)
            stores = {store: SortedDict(items) for store, items in self._stores.items()}
            dirty = set(self._dirty)
            task = _clear_handles(handles) if clear else _persist_stores(handles, stores, dirty)
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                asyncio.run(task)
            else:
                loop.create_task(task)

        self.env = None
        self.opened = False
        self._stores = {}
        self._handles = {}
        self._dirty = set()
        self._version = None
        return not self.opened

    async def aclose(self, clear=False):
        """Flush pending writes, optionally clear persisted browser records, and close."""
        if self.opened:
            if clear:
                await _clear_handles(dict(self._handles))
                self._dirty.clear()
            elif self._dirty:
                await self.flush()
        self.close()
        return self.opened

    async def flush(self):
        """Persist dirty stores through their browser storage handles."""
        if not self._dirty:
            return 0
        if not self.opened:
            raise HierError("WebDuror is not open.")
        persisted = await _persist_stores(self._handles, self._stores, self._dirty)
        self._dirty.difference_update(persisted)
        return len(persisted)

    @property
    def version(self):
        """ Return the version of database stored in __version__ key.

        This value is read through cached in memory

        Returns:
            version (str): semver string
                the version of the database or None if not set in the database

        """
        if self._version is None:
            self._version = self.getVer()
        return self._version

    @version.setter
    def version(self, version):
        """Set the version of the database in memory and in the __version__ key

        Parameters:
            version (str): The new semver formatted version of the database

        """
        if hasattr(version, "decode"):
            version = version.decode("utf-8")
        self._version = version
        self.setVer(version)

    def getVer(self):
        """Returns the value of the the semver formatted version in the
        __version__ key in this database

        Returns:
            str: semver formatted version of the database

        """
        val = self._stores[self.MetaStore].get(self.VersionKey)
        return val.decode("utf-8") if val is not None else None

    def setVer(self, version):
        """ Set the version of the database in the __version__ key

        Parameters:
            version (str): The new semver formatted version str of the database

        """
        self._stores[self.MetaStore][self.VersionKey] = _to_bytes(version)
        self._dirty.add(self.MetaStore)

    def putVal(self, sdb, key, val):
        """Write serialized bytes val to location key in db (subdb)
        Does not overwrite.
        Returns:
            result (bool): True if val successfully written; False if val at key already exists

        Parameters:
            sdb (WebSubDb): opened named subdb with dupsort=False
            key (bytes): within subdb's keyspace
            val (bytes):  to be written at key
        """
        key = _to_bytes(key)
        if key in sdb.items:
            return False
        sdb.items[key] = _to_bytes(val)
        self._dirty.add(sdb.key)
        return True

    def pinVal(self, sdb, key, val):
        """Write serialized bytes val to location key in db
        Overwrites existing val if any
        Returns:
            result (bool): True if val successfully written; False otherwise

        Parameters:
            sdb (WebSubDb): opened named subdb with dupsort=False
            key (bytes): within subdb's keyspace
            val (bytes):  to be written at key
        """
        sdb.items[_to_bytes(key)] = _to_bytes(val)
        self._dirty.add(sdb.key)
        return True

    def getVal(self, sdb, key):
        """Get val at key in db

        Returns:
            val (bytes):  None if no entry at key

        Parameters:
            sdb (WebSubDb): opened named subdb with dupsort=False
            key (bytes): within subdb's keyspace

        """
        val = sdb.items.get(_to_bytes(key))
        return bytes(val) if val is not None else None

    def remVal(self, sdb, key):
        """Removes value at key in db.

        Returns:
            result (bool): True If key exists in database
                           False otherwise

        Parameters:
            sdb (WebSubDb): opened named subdb with dupsort=False
            key (bytes): within subdb's keyspace
        """
        key = _to_bytes(key)
        if key not in sdb.items:
            return False
        del sdb.items[key]
        self._dirty.add(sdb.key)
        return True

    def cntVals(self, sdb):
        """Counts entries in subdb db

        Returns:
            count (int): number of entries in subdb db, or zero otherwise

        Parameters:
            sdb (WebSubDb): opened named subdb with dupsort=False
        """
        return len(sdb.items)

    def getTopItemIter(self, sdb, top=b""):
        """Iterates over branch of subdb db rooted at top key

        Returns:
            items (Iterator): of (full key, val) tuples over a branch of the db
                given by top key where: full key is full database key for val
                not truncated top key

        Raises StopIteration Error when empty.

        Parameters:
            sdb (WebSubDb): instance of named sub db with dupsort==False
            top (bytes): truncated top key, a key space prefix to get all the items
                        from multiple branches of the key space. If top key is
                        empty then gets all items in database.
                        In Python str.startswith('') always returns True so if branch
                        key is empty string it matches all keys in db with startswith.
        """
        top = _to_bytes(top)
        for key in sdb.items.irange(minimum=top):
            if not key.startswith(top):
                break
            yield (bytes(key), bytes(sdb.items[key]))

    def remTopVals(self, sdb, top=b""):
        """Removes all values in branch of db given top key.

        Returns:
            result (bool): True if values were deleted at key.
                           False otherwise if no values at key

        Parameters:
            sdb (WebSubDb): instance of named sub db with dupsort==False
            top (bytes): truncated top key, a key space prefix to get all the items
                        from multiple branches of the key space. If top key is
                        empty then deletes all items in database

        Raises StopIteration Error when empty.

        """
        top = _to_bytes(top)
        keys = []
        for key in sdb.items.irange(minimum=top):
            if not key.startswith(top):
                break
            keys.append(key)
        for key in keys:
            del sdb.items[key]
        if keys:
            self._dirty.add(sdb.key)
        return True if keys else False

    @staticmethod
    def suffix(key: bytes | str | memoryview, ion: int, *, sep: bytes | str = b"."):
        """
        Return iokey after concatenating the hex ordinal suffix to `key` using
        `sep`.

        Parameters:
            key (bytes|str|memoryview): apparent effective database key (unsuffixed)
            ion (int)): insertion ordered ordinal numberfor set of vals
            sep (bytes): separator character(s) for concatenating suffix
        """
        if isinstance(key, memoryview):
            key = bytes(key)
        elif hasattr(key, "encode"):
            key = key.encode()
        if hasattr(sep, "encode"):
            sep = sep.encode()
        ion = b"%032x" % ion
        return sep.join((key, ion))

    @staticmethod
    def unsuffix(iokey: bytes | str | memoryview, *, sep: bytes | str = b"."):
        """
        Return `(key, ion)` from splitting `iokey` at the rightmost `sep`.

        Parameters:
            iokey (bytes|str|memoryview): actual database key suffixed
            sep (bytes): separator character(s) for splitting suffix
        """
        if isinstance(iokey, memoryview):
            iokey = bytes(iokey)
        elif hasattr(iokey, "encode"):
            iokey = iokey.encode()
        if hasattr(sep, "encode"):
            sep = sep.encode()
        key, ion = iokey.rsplit(sep=sep, maxsplit=1)
        ion = int(ion, 16)
        return (key, ion)

    def _io_items(self, store, key, *, ion=0, sep=b"."):
        key = _to_bytes(key)
        iokey = self.suffix(key, ion, sep=sep)
        for iokey in store.irange(minimum=iokey):
            ckey, cion = self.unsuffix(iokey, sep=sep)
            if ckey != key:
                break
            yield iokey, bytes(store[iokey])

    def _next_ion(self, store, key, *, sep=b"."):
        ion = 0
        for iokey, val in self._io_items(store, key, sep=sep):
            ckey, cion = self.unsuffix(iokey, sep=sep)
            ion = cion + 1
        return ion

    def getIoValFirst(self, sdb, key, *, ion=0, sep=b"."):
        """Gets first of the insertion ordered set of values at key,
        None if no entry.
        Returns the first value at the apparent effective key whose iokey is
        greater than or equal to the iokey from `ion`, or None if no entry.

        Parameters:
            sdb (WebSubDb): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
            ion (int): starting ordinal value, default 0

        """
        for iokey, val in self._io_items(sdb.items, key, ion=ion, sep=sep):
            return val
        return None

    def getIoValLast(self, sdb, key, *, sep=b"."):
        """Gets last value (last in) of insertion ordered set values at key
        Returns the last value at the apparent effective key, or None if no entry.

        Uses hidden ordinal key suffix for insertion ordering. The suffix is
        appended and stripped transparently.

        Parameters:
            sdb (WebSubDb): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
        """
        val = None
        for iokey, cval in self._io_items(sdb.items, key, sep=sep):
            val = cval
        return val

    def getIoVals(self, sdb, key, *, ion=0, sep=b"."):
        """Gets list of all the insertion ordered set of values at key

        Returns:
            vals (list[bytes]): insertion-ordered values at same apparent effective key;
                hidden ordinal key suffix is used for insertion ordering and stripped transparently.

        Parameters:
            sdb (WebSubDb): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
            ion (int): starting ordinal value, default 0

        """
        return [val for iokey, val in self._io_items(sdb.items, key, ion=ion, sep=sep)]

    def getIoValsIter(self, sdb, key, *, ion=0, sep=b"."):
        """Gets Iterator of all the insertion ordered set of values at key

        Returns:
            ioset (Iterator): iterator over insertion ordered set of values
                              at same apparent effective key.
                              Uses hidden ordinal key suffix for insertion ordering.
                              The suffix is appended and stripped transparently.

        Raises StopIteration Error when empty.

        Parameters:
            sdb (WebSubDb): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
            ion (int): starting ordinal value, default 0
        """
        for iokey, val in self._io_items(sdb.items, key, ion=ion, sep=sep):
            yield val

    def popIoVal(self, sdb, key, *, ion=0, sep=b"."):
        """Pops first of the insertion ordered set of values at key.
        None if no entry. Pop deletes the returned entry.

        Returns:
            val (bytes|None): first val at same apparent effective key
                        whose iokey >= iokey from ion
                        Uses hidden ordinal key suffix for insertion ordering.
                        The suffix is appended and stripped transparently.
                        None if no entry.

        Parameters:
            sdb (WebSubDb): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
            ion (int): starting ordinal value, default 0

        """
        for iokey, val in self._io_items(sdb.items, key, ion=ion, sep=sep):
            del sdb.items[iokey]
            self._dirty.add(sdb.key)
            return val
        return None

    def remIoVals(self, sdb, key, *, sep=b"."):
        """Deletes all values at apparent effective key.
        Uses hidden ordinal key suffix for insertion ordering.
        The suffix is appended and stripped transparently.

        Returns:
            result (bool): True if at least one value was deleted at key.
                           False otherwise, if no values at key

        Parameters:
            sdb (WebSubDb): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
        """
        keys = [iokey for iokey, val in self._io_items(sdb.items, key, sep=sep)]
        for iokey in keys:
            del sdb.items[iokey]
        if keys:
            self._dirty.add(sdb.key)
        return True if keys else False

    def cntIoVals(self, sdb, key, *, sep=b"."):
        """Count all values with the same apparent effective key.
        Uses hidden ordinal key suffix for insertion ordering.
        The suffix is appended and stripped transparently.

        Returns:
            count (int): count values in set at apparent effective key

        Parameters:
            sdb (WebSubDb): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
        """
        return len(self.getIoVals(sdb=sdb, key=key, sep=sep))

    def getTopIoItemIter(self, sdb, top=b"", *, sep=b"."):
        """Gets Iterator of all values in branch rooted at top key
        The suffix is appended and stripped transparently.

        Returns:
            items (Iterator[(key,val)]): iterator of tuples (key, val) where
                key is apparent key with hidden insertion ordering suffixe removed
                from effective key. Iterates over top branch of insertion
                ordered set values where each effective key has trailing hidden
                suffix of serialization of insertion ordering ordinal.

            Uses hidden ordinal key suffix for insertion ordering.

        Raises StopIteration Error when empty.

        Parameters:
            sdb (WebSubDb): instance of named sub db with dupsort==False
            top (bytes): top key in db. When top is empty then every item in db.
            sep (bytes): sep character for attached io suffix
        """
        for iokey, val in self.getTopItemIter(sdb=sdb, top=top):
            key, ion = self.unsuffix(iokey, sep=sep)
            yield (key, val)

    def addIoVal(self, sdb, key, val, *, sep=b"."):
        """Add val at end (append) of insertion ordered set of values all with the
        same apparent effective key. Does not dedup val.
        Uses hidden ordinal key suffix for insertion ordering.
        The suffix is appended and stripped transparently.

        Returns:
           result (bool): True is added to set. False if already in set.

        Parameters:
            sdb (WebSubDb): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
            val (bytes): serialized value to add

        """
        ion = self._next_ion(sdb.items, key, sep=sep)
        sdb.items[self.suffix(key, ion, sep=sep)] = _to_bytes(val)
        self._dirty.add(sdb.key)
        return True

    def putIoVals(self, sdb, key, vals, *, sep=b"."):
        """Adds at end (append) each val in vals to insertion ordered list of
        values all with the same apparent effective key for each val.
        Does not dedup added vals.
        Uses hidden ordinal key suffix for insertion ordering.
        The suffix is appended and stripped transparently.

        Returns:
           result (bool): True if added to set. False if already in set.

        Parameters:
            sdb (WebSubDb): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
            vals (Iterable): serialized values to add to set of vals at key

        """
        ion = self._next_ion(sdb.items, key, sep=sep)
        result = False
        for offset, val in enumerate(vals):
            sdb.items[self.suffix(key, ion + offset, sep=sep)] = _to_bytes(val)
            result = True
        if result:
            self._dirty.add(sdb.key)
        return result

    def pinIoVals(self, sdb, key, vals, *, sep=b"."):
        """Erase all vals at key and then add vals as insertion ordered set of
        values all with the same apparent effective key. Does not dedup vals.
        Uses hidden ordinal key suffix for insertion ordering.
        The suffix is appended and stripped transparently.

        Returns:
           result (bool): True is added to set.

        Parameters:
            sdb (WebSubDb): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
            vals (abc.Iterable): serialized values to add to set of vals at key
        """
        old = [iokey for iokey, val in self._io_items(sdb.items, key, sep=sep)]
        for iokey in old:
            del sdb.items[iokey]
        result = False
        for ion, val in enumerate(vals):
            sdb.items[self.suffix(key, ion, sep=sep)] = _to_bytes(val)
            result = True
        if old or result:
            self._dirty.add(sdb.key)
        return result

    def addIoSetVal(self, sdb, key, val, *, sep=b"."):
        """Add val idempotently to insertion ordered set of values all with the
        same apparent effective key if val not already in set of vals at key.
        Dedups the added val.
        Uses hidden ordinal key suffix for insertion ordering.
        The suffix is appended and stripped transparently.

        Returns:
           result (bool): True is added to set. False if already in set.

        Parameters:
            sdb (WebSubDb): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
            val (bytes): serialized value to add

        """
        val = _to_bytes(val)
        vals = oset()
        ion = 0
        for iokey, cval in self._io_items(sdb.items, key, sep=sep):
            vals.add(cval)
            ckey, cion = self.unsuffix(iokey, sep=sep)
            ion = cion + 1
        if val in vals:
            return False
        sdb.items[self.suffix(key, ion, sep=sep)] = val
        self._dirty.add(sdb.key)
        return True

    def putIoSetVals(self, sdb, key, vals, *, sep=b"."):
        """Adds idempotently each val in vals to insertion ordered set of values
        all with the same apparent effective key for each val that is not already
        in set of vals at key. Dedups the put vals.
        Uses hidden ordinal key suffix for insertion ordering.
        The suffix is appended and stripped transparently.

        Returns:
           result (bool): True if added to set. False if already in set.

        Parameters:
            sdb (WebSubDb): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
            vals (Iterable): serialized values to add to set of vals at key

        """
        vals = oset(_to_bytes(val) for val in vals)
        pvals = oset()
        ion = 0
        for iokey, cval in self._io_items(sdb.items, key, sep=sep):
            pvals.add(cval)
            ckey, cion = self.unsuffix(iokey, sep=sep)
            ion = cion + 1
        vals -= pvals
        result = False
        for offset, val in enumerate(vals):
            sdb.items[self.suffix(key, ion + offset, sep=sep)] = val
            result = True
        if result:
            self._dirty.add(sdb.key)
        return result

    def pinIoSetVals(self, sdb, key, vals, *, sep=b"."):
        """Erase all vals at key and then add unique vals as insertion ordered set of
        values all with the same apparent effective key. Dedups the set vals.
        Uses hidden ordinal key suffix for insertion ordering.
        The suffix is appended and stripped transparently.

        Returns:
           result (bool): True is added to set.

        Parameters:
            sdb (WebSubDb): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
            vals (abc.Iterable): serialized values to add to set of vals at key
        """
        old = [iokey for iokey, val in self._io_items(sdb.items, key, sep=sep)]
        for iokey in old:
            del sdb.items[iokey]
        result = False
        vals = oset(_to_bytes(val) for val in vals)
        for ion, val in enumerate(vals):
            sdb.items[self.suffix(key, ion, sep=sep)] = val
            result = True
        if old or result:
            self._dirty.add(sdb.key)
        return result

    def remIoSetVal(self, sdb, key, val, *, sep=b"."):
        """Removes (delete) matching val at apparent effective key if exists.
        Uses hidden ordinal key suffix for insertion ordering.
        The suffix is appended and stripped transparently.

        Because the insertion order of val is not provided must perform a linear
        search over set of values.

        Another problem is that vals may get added and deleted in any order so
        the max suffix ion may creep up over time. The suffix ordinal max > 2**16
        is an impossibly large number, however, so the suffix will not max out
        practically.But its not the most elegant solution.

        In some cases a better approach would be to use getIoSetItemsIter which
        returns the actual iokey not the apparent effetive key so can delete
        using the iokey without searching for the value. This is most applicable
        when processing escrows where all the escrowed items are processed linearly
        and one needs to delete some of them in stride with their processing.

        Returns:
            result (bool): True if val was deleted at key. False otherwise
                if val not found at key

        Parameters:
            sdb (WebSubDb): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
            val (bytes): value to delete
        """
        val = _to_bytes(val)
        for iokey, cval in self._io_items(sdb.items, key, sep=sep):
            if val == cval:
                del sdb.items[iokey]
                self._dirty.add(sdb.key)
                return True
        return False


@asynccontextmanager
async def openWebDuror(*, cls=None, name="test", temp=True, clear=False, **kwa):
    """Async context manager wrapper for WebDuror instances."""
    duror = None
    if cls is None:
        cls = WebDuror
    try:
        duror = cls(name=name, temp=temp, reopen=False, clear=clear, **kwa)
        await duror.reopen(clear=clear)
        yield duror
    finally:
        if duror:
            await duror.aclose(clear=clear or duror.temp)
