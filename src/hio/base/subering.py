# -*- encoding: utf-8 -*-
"""hio.base.subering module

Support for Durable storage abstracted subclasses  (lmdb or wasm pyodide IndexedDB)
"""

from __future__ import annotations  # so type hints of classes get resolved later

import os
import sys
import platform
import stat
import tempfile
from contextlib import contextmanager

from ordered_set import OrderedSet as oset

import hio

from hio import HierError
from .doing import Doer
from ..help import isNonStringIterable, RegDom, IceRegDom

PYODIDE = 'emscripten' in sys.platform

if PYODIDE:
    from .webduring import WebDuror as Duror
else:
    from .during import Duror




class SuberBase():
    """Base class for Sub DBs of Duror
    Provides common methods for subclasses
    Do not instantiate but use a subclass

    Class Attribues:
        Sep (str): default separator to convert keys iterator to key bytes for db key

    Attributes:
        db (dbing.LMDBer): base LMDB db
        sdb (lmdb._Database): instance of lmdb named sub db for this Suber
        sep (str): separator for combining keys tuple of strs into key bytes
        verify (bool): True means reverify when ._des from db when applicable
                       False means do not reverify. Default False
    """
    Sep = '_'  # separator for combining key iterables

    def __init__(self, db: Duror, *,
                       subkey: str='docs.',
                       dupsort: bool=False,
                       sep: str=None,
                       verify: bool=False,
                       **kwa):
        """Parameters:
            db (dbing.LMDBer): base db
            subkey (str):  LMDB sub database key
            dupsort (bool): True means enable duplicates at each key
                               False (default) means do not enable duplicates at
                               each key
            sep (str): separator to convert keys iterator to key bytes for db key
                       default is self.Sep == '.'
            verify (bool): True means reverify when ._des from db when applicable
                           False means do not reverify. Default False
        """
        super(SuberBase, self).__init__()  # for multi inheritance
        self.db = db
        self.sdb = self.db.env.open_db(key=subkey.encode("utf-8"), dupsort=dupsort)
        self.sep = sep if sep is not None else self.Sep
        self.verify = True if verify else False



    def _tokey(self, keys: str|bytes|memoryview|Iterable[str|bytes|memoryview],
                topive: bool=False):
        """Converts keys to key bytes with proper separators and returns key bytes.
        If keys is already str or bytes or memoryview then returns key bytes.
        Else If keys is iterable (non-str) of strs or bytes then joins with
        separator converts to key bytes and returns. When keys is iterable and
        topive is True then enables partial key from top branch of key space given
        by partial keys by appending separator to end of partial key

        Returns:
           key (bytes): each element of keys is joined by .sep. If topive then
                        last char of key is .sep

        Parameters:
           keys (str | bytes | memoryview | Iterable[str | bytes]): db key or
                        Iterable of (str | bytes) to form key.
           topive (bool): True means treat as partial key tuple from top branch of
                       key space given by partial keys. Resultant key ends in .sep
                       character.
                       False means treat as full branch in key space. Resultant key
                       does not end in .sep character.
                       When last item in keys is empty str then will treat as
                       partial ending in sep regardless of topive value

        """
        if hasattr(keys, "encode"):  # str
            return keys.encode("utf-8")
        if isinstance(keys, memoryview):  # memoryview of bytes
            return bytes(keys)  # return bytes
        elif hasattr(keys, "decode"): # bytes
            return keys
        if topive and keys[-1]:  # topive and keys is not already partial
            keys = tuple(keys) + ('',)  # cat empty str so join adds trailing sep
        return (self.sep.join(key.decode() if hasattr(key, "decode") else key
                              for key in keys).encode())


    def _tokeys(self, key: str | bytes | memoryview):
        """Converts key bytes to keys tuple of strs by decoding and then splitting
        at separator .sep.

        Returns:
           keys (tuple[str]): makes tuple by splitting key at sep

        Parameters:
           key (str | bytes | memoryview): db key.

        """
        if isinstance(key, memoryview):  # memoryview of bytes
            key = bytes(key)
        if hasattr(key, "decode"):  # bytes
            key = key.decode()  # convert to str
        return tuple(key.split(self.sep))


    def _ser(self, val: str|bytes|memoryview):
        """
        Serialize value to bytes to store in db
        Parameters:
            val (str | bytes | memoryview): encodable as bytes
        """
        if isinstance(val, memoryview):  # memoryview is always bytes
            val = bytes(val)  # return bytes
        return (val.encode() if hasattr(val, "encode") else val)


    def _des(self, val: bytes|memoryview):
        """Deserialize val to str
        Parameters:
            val (bytes | memoryview): decodable as str
        """
        if isinstance(val, memoryview):  # memoryview is always bytes
            val = bytes(val)  # convert to bytes
        return (val.decode() if hasattr(val, "decode") else val)


    def trim(self, keys: str|bytes|memoryview|Iterable=b"", *, topive=False):
        """Removes all entries whose keys startswith keys. Enables removal of whole
        branches of db key space. To ensure that proper separation of a branch
        include empty string as last key in keys. For example ("a","") deletes
        'a.1'and 'a.2' but not 'ab'

        Parameters:
            keys (Iterable[str | bytes | memoryview]): of key parts that may be
                a truncation of a full keys tuple in  in order to address all the
                items from multiple branches of the key space.
                If keys is empty then trims all items in database.
                Either append "" to end of keys Iterable to ensure get properly
                separated top branch key or use top=True.

            topive (bool): True means treat as partial key tuple from top branch of
                       key space given by partial keys. Resultant key ends in .sep
                       character.
                       False means treat as full branch in key space. Resultant key
                       does not end in .sep character.
                       When last item in keys is empty str then will treat as
                       partial ending in sep regardless of top value


        Returns:
           result (bool): True if val at key exists so delete successful. False otherwise
        """
        return(self.db.remTopVals(sdb=self.sdb, top=self._tokey(keys, topive=topive)))


    def getFullItemIter(self, keys: str|bytes|memoryview|Iterable[str|bytes]="",
                       *, topive=False):
        """Iterator over items in .db that returns full items with subclass
        specific special hidden parts shown for debugging or testing.

        Returns:
            items (Iterator[tuple[key,val]]): (key, val) tuples of each item
            over the all the items in subdb whose key startswith key made from
            keys. Keys may be keyspace prefix to return branches of key space.
            When keys is empty then returns all items in subdb.
            This is meant to return full parts of items in both keyspace and
            valuespace which may be useful in debugging or testing.

        Parameters:
            keys (str|bytes|memoryview|Iterable[str | bytes | memoryview]):
                of key parts that may be
                a truncation of a full keys tuple in  in order to address all the
                items from multiple branches of the key space.
                If keys is empty then gets all items in database.
                Either append "" to end of keys Iterable to ensure get properly
                separated top branch key or use top=True.
                In Python str.startswith('') always returns True so if branch
                key is empty string it matches all keys in db with startswith.


            topive (bool): True means treat as partial key tuple from top branch of
                       key space given by partial keys. Resultant key ends in .sep
                       character.
                       False means treat as full branch in key space. Resultant key
                       does not end in .sep character.
                       When last item in keys is empty str then will treat as
                       partial ending in sep regardless of top value

        """
        for key, val in self.db.getTopItemIter(sdb=self.sdb,
                                               top=self._tokey(keys, topive=topive)):
            yield (self._tokeys(key), self._des(val))


    def getItemIter(self, keys: str|bytes|memoryview|Iterable="",
                       *, topive=False):
        """Iterator over items in .db subclasses that do special hidden transforms
        on either the keyspace or valuespace should override this method to hide
        hidden parts from the returned items. For example, adding either
        a hidden key space suffix or hidden val space proem to ensure insertion
        order. Use getFullItemIter instead to return full items with hidden parts
        shown for debugging or testing.

        Returns:
            items (Iterator[tuple[key,val]]): (key, val) tuples of each item
            over the all the items in subdb whose key startswith key made from
            keys. Keys may be keyspace prefix to return branches of key space.
            When keys is empty then returns all items in subdb



        Parameters:
            keys (str|bytes|memoryview|Iterable[str|bytes|memoryview]): of key
                parts that may be
                a truncation of a full keys tuple in  in order to address all the
                items from multiple branches of the key space.
                If keys is empty then gets all items in database.
                Either append "" to end of keys Iterable to ensure get properly
                separated top branch key or use top=True.
                In Python str.startswith('') always returns True so if branch
                key is empty string it matches all keys in db with startswith.


            topive (bool): True means treat as partial key tuple from top branch of
                key space given by partial keys. Resultant key ends in .sep
                character.
                False means treat as full branch in key space. Resultant key
                does not end in .sep character.
                When last item in keys is empty str then will treat as
                partial ending in sep regardless of top value

        """
        for key, val in self.db.getTopItemIter(sdb=self.sdb,
                                               top=self._tokey(keys, topive=topive)):
            yield (self._tokeys(key), self._des(val))

    def cntAll(self):
        """Counts all entries in subdb self.sdb

        Returns:
            count (int): all entries in .sdb
        """
        return self.db.cntVals(sdb=self.sdb)



class Suber(SuberBase):
    """Subclass of `SuberBase` without LMDB duplicates."""

    def __init__(self, db: Duror, *,
                       subkey: str = 'docs.',
                       dupsort: bool=False, **kwa):
        """
        Inherited Parameters:
            db (dbing.LMDBer): base db
            subkey (str):  LMDB sub database key
            dupsort (bool): True means enable duplicates at each key
                               False (default) means do not enable duplicates at
                               each key. Set to False
            sep (str): separator to convert keys iterator to key bytes for db key
                       default is self.Sep == '.'
            verify (bool): True means reverify when ._des from db when applicable
                           False means do not reverify. Default False

        Parameters:
            db (dbing.LMDBer): base db
            subkey (str):  LMDB sub database key
        """
        super(Suber, self).__init__(db=db, subkey=subkey, dupsort=False, **kwa)


    def put(self, keys: str|bytes|memoryview|Iterable[str|bytes|memoryview],
                  val: bytes|str|memoryview):
        """
        Puts val at key made from keys. Does not overwrite

        Parameters:
            keys (str|bytes|memoryview|Iterable[str|bytes|memoryview]): of key
                                      strs to be combined in order to form key
            val (bytes|str|memoryview): value from ._ser

        Returns:
            result (bool): True If successful, False otherwise, such as key
                              already in database.
        """
        return (self.db.putVal(sdb=self.sdb,
                               key=self._tokey(keys),
                               val=self._ser(val)))


    def pin(self, keys: str|bytes|memoryview|Iterable[str|bytes|memoryview],
                  val: bytes|str|memoryview):
        """
        Pins (sets) val at key made from keys. Overwrites.

        Parameters:
            keys (str|bytes|memoryview|Iterable[str|bytes|memoryview]): of key
                                      strs to be combined in order to form key
            val (bytes|str|memoryview): value from ._ser

        Returns:
            result (bool): True If successful. False otherwise.
        """
        return (self.db.pinVal(sdb=self.sdb,
                               key=self._tokey(keys),
                               val=self._ser(val)))


    def get(self, keys:  str|bytes|memoryview|Iterable[str|bytes|memoryview]):
        """
        Gets val at keys

        Parameters:
            keys ( str|bytes|memoryview|Iterable[str|bytes|memoryview]): of key
                                       strs to be combined in order to form key

        Returns:
            data (str): decoded as utf-8 or whatever ._des provides
            None if no entry at keys

        Usage::

            Use walrus operator to catch and raise missing entry
            if (data := mydb.get(keys)) is None:
                raise ExceptionHere
            use data here

        """
        val = self.db.getVal(sdb=self.sdb, key=self._tokey(keys))
        return (self._des(val) if val is not None else None)


    def rem(self, keys:  str|bytes|memoryview|Iterable[str|bytes|memoryview]):
        """
        Removes entry at keys

        Parameters:
            keys ( str|bytes|memoryview|Iterable[str|bytes|memoryview]): of key
                                       strs to be combined in order to form key

        Returns:
           result (bool): True if key exists so delete successful. False otherwise
        """
        return(self.db.remVal(sdb=self.sdb, key=self._tokey(keys)))



class IoSuber(SuberBase):
    """Insertion-ordered Suber that supports a durable queue of values per key.

    Uses a hidden ordinal suffix to preserve insertion order.
    """
    IonSep = '.'  # separator for suffixing insertion order ordinal number

    def __init__(self, db: dbing.LMDBer, *,
                       subkey: str='docs.',
                       dupsort: bool=False,
                       ionsep: str=None, **kwa):
        """Initialize instance

        Inherited Parameters:
            db (dbing.LMDBer): base db
            subkey (str):  LMDB sub database key
            dupsort (bool): True means enable duplicates at each key
                               False (default) means do not enable duplicates at
                               each key
            sep (str): separator to convert keys iterator to key bytes for db key
                       default is self.Sep == '.'
            verify (bool): True means reverify when ._des from db when applicable
                           False means do not reverify. Default False

        Parameters:
            ionsep (str|None): separator to suffix insertion order ordinal number
                       default is self.IonSep == '.'
        """
        super(IoSuber, self).__init__(db=db, subkey=subkey, dupsort=False, **kwa)
        self.ionsep = ionsep if ionsep is not None else self.IonSep


    def getFirst(self, keys: str | bytes | memoryview | Iterable):
        """Gets first val inserted at effecive key made from keys and hidden ordinal
        suffix.

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key

        Returns:
            val (str|None):  value str, None if no entry at keys

        """
        val = self.db.getIoValFirst(sdb=self.sdb, key=self._tokey(keys))
        return (self._des(val) if val is not None else val)


    def getLast(self, keys: str | bytes | memoryview | Iterable):
        """Gets last val inserted at effecive key made from keys and hidden ordinal
        suffix.

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key

        Returns:
            val (str|None):  value str, None if no entry at keys

        """
        val = self.db.getIoValLast(sdb=self.sdb, key=self._tokey(keys))
        return (self._des(val) if val is not None else val)


    def get(self, keys: str | bytes | memoryview | Iterable):
        """Gets vals set list at key made from effective keys

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key

        Returns:
            vals (Iterable):  each item in list is str
                          empty list if no entry at keys

        """
        return ([self._des(val) for val in
                    self.db.getIoValsIter(sdb=self.sdb,
                                             key=self._tokey(keys),
                                             sep=self.ionsep)])


    def getIter(self, keys: str | bytes | memoryview | Iterable):
        """Gets vals iterator at effecive key made from keys and hidden ordinal suffix.
        All vals in set of vals that share same effecive key are retrieved in
        insertion order.

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key

        Returns:
            vals (Iterator):  str values. Raises StopIteration when done

        """
        for val in self.db.getIoValsIter(sdb=self.sdb,
                                            key=self._tokey(keys),
                                            sep=self.ionsep):
            yield self._des(val)


    def pop(self, keys: str | bytes | memoryview | Iterable):
        """Pops first val if any inserted at effecive key made from keys and
        hidden ordinal suffix. Pop returns and deletes value if any.

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key

        Returns:
            val (str|None):  value str, None if no entry at keys

        """
        val = self.db.popIoVal(sdb=self.sdb, key=self._tokey(keys))
        return (self._des(val) if val is not None else val)


    def add(self, keys: str | bytes | memoryview | Iterable,
            val: str | bytes | memoryview):
        """Add val idempotently to vals at effective key made from keys and hidden
        ordinal suffix. Idempotent means that added value is not already in set
        of vals at key. Does not overwrite or add same value at same key more
        than once.

        Parameters:
            keys (str | bytes | memoryview | Iterable): of key parts to be
                    combined in order to form key
            val (str | bytes | memoryview): serialization

        Returns:
            result (bool): True means value added ,
                            False otherwise.

        """
        return (self.db.addIoVal(sdb=self.sdb,
                                    key=self._tokey(keys),
                                    val=self._ser(val),
                                    sep=self.ionsep))


    def put(self, keys: str | bytes | memoryview | Iterable,
                  vals: str | bytes | memoryview | Iterable):
        """Puts all vals each with an effective key made from keys and hidden
        ordinal suffix that are not already in set of vals at key.
        Does not overwrite existing vals. Does not add val if already same val
        in set.

        Parameters:
            keys (str | bytes | memoryview | Iterable): of key parts to be
                    combined in order to form key
            vals (str | bytes | memoryview | Iterable): of str serializations

        Returns:
            result (bool): True If successful, False otherwise.

        """
        if not isNonStringIterable(vals):  # not iterable
            vals = (vals, )  # make iterable
        return (self.db.putIoVals(sdb=self.sdb,
                                     key=self._tokey(keys),
                                     vals=[self._ser(val) for val in vals],
                                     sep=self.ionsep))


    def pin(self, keys: str | bytes | memoryview | Iterable,
                  vals: str | bytes | memoryview | Iterable):
        """Pins (sets) vals at effective key made from keys and hidden ordinal suffix.
        Overwrites. Removes all pre-existing vals that share same effective keys
        and replaces them with vals

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key
            vals (Iterable): str serializations

        Returns:
            result (bool): True If successful, False otherwise.

        """
        if not isNonStringIterable(vals):  # not iterable
            vals = (vals, )  # make iterable
        return (self.db.pinIoVals(sdb=self.sdb,
                                     key=self._tokey(keys),
                                     vals=[self._ser(val) for val in vals],
                                     sep=self.ionsep))


    def rem(self, keys: str | bytes | memoryview | Iterable):
        """Removes entry at effective key made from keys and hidden ordinal suffix
        that matches val if any. Otherwise deletes all values at effective key.

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key
            val (str):  value at key to delete. Subclass ._ser method may
                        accept different value types
                        if val is empty then remove all values at key

        Returns:
           result (bool): True if effective key with val exists so rem successful.
                           False otherwise

        """
        return self.db.remIoVals(sdb=self.sdb,
                                 key=self._tokey(keys),
                                 sep=self.ionsep)


    def cnt(self, keys: str | bytes | memoryview | Iterable):
        """Return count of  values at effective key made from keys and hidden ordinal
        suffix. Zero otherwise

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key
        """
        return (self.db.cntIoVals(sdb=self.sdb,
                                     key=self._tokey(keys),
                                     sep=self.ionsep))


    def getItemIter(self, keys: str | bytes | memoryview | Iterable = "",
                    *, topive=False):
        """Return iterator over all the items in top branch defined by keys where
        keys may be truncation of full branch.

        Returns:
            items (Iterator): of (key, val) tuples over the all the items in
            subdb whose effective key startswith key made from keys.
            Keys may be keyspace prefix in order to return branches of key space.
            When keys is empty then returns all items in subdb.
            Returned key in each item has ordinal suffix removed.

        Parameters:
            keys (Iterable): tuple of bytes or strs that may be a truncation of
                a full keys tuple in  in order to address all the items from
                multiple branches of the key space. If keys is empty then gets
                all items in database.
                Either append "" to end of keys Iterable to ensure get properly
                separated top branch key or use top=True.
                In Python str.startswith('') always returns True so if branch
                key is empty string it matches all keys in db with startswith.

            topive (bool): True means treat as partial key tuple from top branch of
                key space given by partial keys. Resultant key ends in .sep
                character.
                False means treat as full branch in key space. Resultant key
                does not end in .sep character.
                When last item in keys is empty str then will treat as
                partial ending in sep regardless of top value

        """
        for key, val in self.db.getTopIoItemIter(sdb=self.sdb,
                top=self._tokey(keys, topive=topive), sep=self.ionsep):
            yield (self._tokeys(key), self._des(val))



class IoSetSuber(SuberBase):
    """Insertion-ordered Suber that supports a set of distinct values per key.

    Uses a hidden ordinal suffix to preserve insertion order.
    """
    IonSep = '.'  # separator for suffixing insertion order ordinal number

    def __init__(self, db: dbing.LMDBer, *,
                       subkey: str='docs.',
                       dupsort: bool=False,
                       ionsep: str=None, **kwa):
        """Initialize instance

        Inherited Parameters:
            db (dbing.LMDBer): base db
            subkey (str):  LMDB sub database key
            dupsort (bool): True means enable duplicates at each key
                               False (default) means do not enable duplicates at
                               each key
            sep (str): separator to convert keys iterator to key bytes for db key
                       default is self.Sep == '.'
            verify (bool): True means reverify when ._des from db when applicable
                           False means do not reverify. Default False

        Parameters:
            ionsep (str|None): separator to suffix insertion order ordinal number
                       default is self.IonSep == '.'
        """
        super(IoSetSuber, self).__init__(db=db, subkey=subkey, dupsort=False, **kwa)
        self.ionsep = ionsep if ionsep is not None else self.IonSep


    def getFirst(self, keys: str | bytes | memoryview | Iterable):
        """Gets first val inserted at effecive key made from keys and hidden ordinal
        suffix.

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key

        Returns:
            val (str|None):  value str, None if no entry at keys

        """
        val = self.db.getIoValFirst(sdb=self.sdb, key=self._tokey(keys))
        return (self._des(val) if val is not None else val)


    def getLast(self, keys: str | bytes | memoryview | Iterable):
        """Gets last val inserted at effecive key made from keys and hidden ordinal
        suffix.

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key

        Returns:
            val (str|None):  value str, None if no entry at keys

        """
        val = self.db.getIoValLast(sdb=self.sdb, key=self._tokey(keys))
        return (self._des(val) if val is not None else val)


    def get(self, keys: str | bytes | memoryview | Iterable):
        """Gets vals set list at key made from effective keys

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key

        Returns:
            vals (Iterable):  each item in list is str
                          empty list if no entry at keys

        """
        return ([self._des(val) for val in
                    self.db.getIoValsIter(sdb=self.sdb,
                                             key=self._tokey(keys),
                                             sep=self.ionsep)])


    def getIter(self, keys: str | bytes | memoryview | Iterable):
        """Gets vals iterator at effecive key made from keys and hidden ordinal suffix.
        All vals in set of vals that share same effecive key are retrieved in
        insertion order.

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key

        Returns:
            vals (Iterator):  str values. Raises StopIteration when done

        """
        for val in self.db.getIoValsIter(sdb=self.sdb,
                                            key=self._tokey(keys),
                                            sep=self.ionsep):
            yield self._des(val)


    def pop(self, keys: str | bytes | memoryview | Iterable):
        """Pops first val if any inserted at effecive key made from keys and
        hidden ordinal suffix. Pop returns and deletes value if any.

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key

        Returns:
            val (str|None):  value str, None if no entry at keys

        """
        val = self.db.popIoVal(sdb=self.sdb, key=self._tokey(keys))
        return (self._des(val) if val is not None else val)


    def add(self, keys: str | bytes | memoryview | Iterable,
            val: str | bytes | memoryview):
        """Add val idempotently to vals at effective key made from keys and hidden
        ordinal suffix. Idempotent means that added value is not already in set
        of vals at key. Does not overwrite or add same value at same key more
        than once.

        Parameters:
            keys (str | bytes | memoryview | Iterable): of key parts to be
                    combined in order to form key
            val (str | bytes | memoryview): serialization

        Returns:
            result (bool): True means unique value added among duplications,
                            False means duplicate of same value already exists.

        """
        return (self.db.addIoSetVal(sdb=self.sdb,
                                    key=self._tokey(keys),
                                    val=self._ser(val),
                                    sep=self.ionsep))


    def put(self, keys: str | bytes | memoryview | Iterable,
                  vals: str | bytes | memoryview | Iterable):
        """Puts all vals each with an effective key made from keys and hidden
        ordinal suffix that are not already in set of vals at key.
        Does not overwrite existing vals. Does not add val if already same val
        in set.

        Parameters:
            keys (str | bytes | memoryview | Iterable): of key parts to be
                    combined in order to form key
            vals (str | bytes | memoryview | Iterable): of str serializations

        Returns:
            result (bool): True If successful, False otherwise.

        """
        if not isNonStringIterable(vals):  # not iterable
            vals = (vals, )  # make iterable
        return (self.db.putIoSetVals(sdb=self.sdb,
                                     key=self._tokey(keys),
                                     vals=[self._ser(val) for val in vals],
                                     sep=self.ionsep))


    def pin(self, keys: str | bytes | memoryview | Iterable,
                  vals: str | bytes | memoryview | Iterable):
        """Pins (sets) vals at effective key made from keys and hidden ordinal suffix.
        Overwrites. Removes all pre-existing vals that share same effective keys
        and replaces them with vals

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key
            vals (Iterable): str serializations

        Returns:
            result (bool): True If successful, False otherwise.

        """
        if not isNonStringIterable(vals):  # not iterable
            vals = (vals, )  # make iterable
        return (self.db.pinIoSetVals(sdb=self.sdb,
                                     key=self._tokey(keys),
                                     vals=[self._ser(val) for val in vals],
                                     sep=self.ionsep))


    def rem(self, keys: str | bytes | memoryview | Iterable,
                   val: str | bytes | memoryview = b''):
        """Removes entry at effective key made from keys and hidden ordinal suffix
        that matches val if any. Otherwise deletes all values at effective key.

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key
            val (str):  value at key to delete. Subclass ._ser method may
                        accept different value types
                        if val is empty then remove all values at key

        Returns:
            result (bool): True if deletion succeeds; False otherwise.
                If val is provided, remove matching value at effective key.
                If val is empty, remove all values at effective key.

        """
        if val:
            return self.db.remIoSetVal(sdb=self.sdb,
                                       key=self._tokey(keys),
                                       val=self._ser(val),
                                       sep=self.ionsep)
        else:
            return self.db.remIoVals(sdb=self.sdb,
                                       key=self._tokey(keys),
                                       sep=self.ionsep)


    def cnt(self, keys: str | bytes | memoryview | Iterable):
        """Return count of  values at effective key made from keys and hidden ordinal
        suffix. Zero otherwise

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key
        """
        return (self.db.cntIoVals(sdb=self.sdb,
                                     key=self._tokey(keys),
                                     sep=self.ionsep))


    def getItemIter(self, keys: str | bytes | memoryview | Iterable = "",
                    *, topive=False):
        """Return iterator over all the items in top branch defined by keys where
        keys may be truncation of full branch.

        Returns:
            items (Iterator): of (key, val) tuples over the all the items in
            subdb whose effective key startswith key made from keys.
            Keys may be keyspace prefix in order to return branches of key space.
            When keys is empty then returns all items in subdb.
            Returned key in each item has ordinal suffix removed.

        Parameters:
            keys (Iterable): tuple of bytes or strs that may be a truncation of
                a full keys tuple in  in order to address all the items from
                multiple branches of the key space. If keys is empty then gets
                all items in database.
                Either append "" to end of keys Iterable to ensure get properly
                separated top branch key or use top=True.
                In Python str.startswith('') always returns True so if branch
                key is empty string it matches all keys in db with startswith.

            topive (bool): True means treat as partial key tuple from top branch of
                key space given by partial keys. Resultant key ends in .sep
                character.
                False means treat as full branch in key space. Resultant key
                does not end in .sep character.
                When last item in keys is empty str then will treat as
                partial ending in sep regardless of top value

        """
        for key, val in self.db.getTopIoItemIter(sdb=self.sdb,
                top=self._tokey(keys, topive=topive), sep=self.ionsep):
            yield (self._tokeys(key), self._des(val))


class DomSuberBase(SuberBase):
    """Suber that serializes `RegDom` subclasses.

    Forces `.sep` to `_` and uses a class-name proem (LF) when serializing.
    """
    ProSep = '\n'  # separator class name proem to serialized RegDom instance

    def __init__(self, db: Duror, *, subkey: str = 'bags.', sep='_', prosep=None,
                 **kwa):
        """
        Inherited Parameters:
            db (Duror): base db
            subkey (str):  LMDB sub database key
            dupsort (bool): True means enable duplicates at each key
                               False (default) means do not enable duplicates at
                               each key. Set to False
            sep (str): separator to convert keys iterator to key bytes for db key
                       default is self.Sep == '.'
            verify (bool): True means reverify when ._des from db when applicable
                           False means do not reverify. Default False

        Parameters:
            prosep (str|None): separator class name proem to serialized RegDom instance
                               default is self.ProSep (LF)
        """
        super(DomSuberBase, self).__init__(db=db, subkey=subkey, sep=sep, **kwa)
        self.prosep = prosep if prosep is not None else self.ProSep


    def _ser(self, val: RegDom):
        """Serialize value to json bytes to store in db with proem that is
        class name. Must be in registry. Uses LF (byte 0x0A) as separator between
        proem class name and json serialization of val

        Parameters:
            val (RegDom): encodable as bytes json
        """
        try:
            klas = val._registry[val.__class__.__name__]
        except (KeyError, AttributeError) as ex:
            raise HierError(f"Unregistered subclass instance={val}") from ex

        return (klas.__name__.encode() + self.prosep.encode() + val._asjson())


    def _des(self, val: bytes|memoryview):
        """Deserialize val to RegDom subclass instance as given by proem
        prepended to json serialization of RegDom subclass instance
        Uses LF (byte 0x0A) as separator between proem class name and json serialization
        of val

        Parameters:
            val (bytes|memoryview): proem + LF + json

        Returns:
            dom (RegDom): instance of RegDom subclass as registered under proem

        """
        if isinstance(val, memoryview):  # memoryview is always bytes
            val = bytes(val)  # convert to bytes

        proem, ser = val.split(sep=self.prosep.encode(), maxsplit=1)
        proem = proem.decode()
        if proem in RegDom._registry:
            klas = RegDom._registry[proem]
        elif proem in IceRegDom._registry:
            klas = IceRegDom._registry[proem]
        else:
            raise HierError(f"Unregistered serialized subclass={proem}")

        return (klas._fromjson(ser))


class DomSuber(DomSuberBase, Suber):
    """Suber that serializes `CanDom` subclasses with LF proem."""

    def __init__(self, db: Duror, *, subkey: str = 'cans.', sep='_', prosep='\n',
                 **kwa):
        """
        Inherited Parameters:
            db (Duror): base db
            subkey (str):  LMDB sub database key
            dupsort (bool): True means enable duplicates at each key
                               False (default) means do not enable duplicates at
                               each key. Set to False
            sep (str): separator to convert keys iterator to key bytes for db key
                       default is self.Sep == '.'
            verify (bool): True means reverify when ._des from db when applicable
                           False means do not reverify. Default False
            prosep (str|None): separator class name proem to serialized CanDom instance
                               default is self.ProSep (LF)

        """
        super(DomSuber, self).__init__(db=db, subkey=subkey,
                                       sep=sep, prosep=prosep, **kwa)


class DomIoSuber(DomSuberBase, IoSuber):
    """Insertion-ordered Suber that serializes `RegDom` subclasses with LF proem."""

    def __init__(self, db: Duror, *, subkey: str = 'dsqs.', sep='_',
                 prosep='\n', ionsep='.', **kwa):
        """
        Inherited Parameters:
            db (Duror): base db
            subkey (str):  LMDB sub database key
            dupsort (bool): True means enable duplicates at each key
                               False (default) means do not enable duplicates at
                               each key. Set to False
            sep (str): separator to convert keys iterator to key bytes for db key
                       default is self.Sep == '.'
            verify (bool): True means reverify when ._des from db when applicable
                           False means do not reverify. Default False
            prosep (str|None): separator class name proem to serialized CanDom instance
                               default is self.ProSep (LF)
            ionsep (str|None): separator to suffix insertion order ordinal number
                       default is self.IonSep == '.'


        """
        super(DomIoSuber, self).__init__(db=db, subkey=subkey, sep=sep,
                                            prosep=prosep, ionsep=ionsep, **kwa)



class DomIoSetSuber(DomSuberBase, IoSetSuber):
    """Insertion-ordered set Suber that serializes `RegDom` subclasses with LF proem."""

    def __init__(self, db: Duror, *, subkey: str = 'dsqs.', sep='_',
                 prosep='\n', ionsep='.', **kwa):
        """
        Inherited Parameters:
            db (Duror): base db
            subkey (str):  LMDB sub database key
            dupsort (bool): True means enable duplicates at each key
                               False (default) means do not enable duplicates at
                               each key. Set to False
            sep (str): separator to convert keys iterator to key bytes for db key
                       default is self.Sep == '.'
            verify (bool): True means reverify when ._des from db when applicable
                           False means do not reverify. Default False
            prosep (str|None): separator class name proem to serialized CanDom instance
                               default is self.ProSep (LF)
            ionsep (str|None): separator to suffix insertion order ordinal number
                       default is self.IonSep == '.'


        """
        super(DomIoSetSuber, self).__init__(db=db, subkey=subkey, sep=sep,
                                            prosep=prosep, ionsep=ionsep, **kwa)



class Subery(Duror):
    """Subery subclass of Duror for managing subdbs of Duror for durable storage
    of action data
    """
    def __init__(self, **kwa):
        """
        Setup named sub databases.

        Inherited Parameters:  (see Duror)
        """
        super(Subery, self).__init__(**kwa)


    def reopen(self, **kwa):
        """Open sub databases

        Attributes:
            cans (Suber): subdb whose values are serialized Can instances
                Can is a durable Bag
            drqs (IoSetSub): subdb whose values are serialized RegDom instances
                Interfaced via a Durq which is a durable queue (FIFO)
            dsqs (IoSetSub): subdb whose values are serialized RegDom instances
                Interfaced via a Dusq which is  durable set queue (FIFO deduped)

        """
        super(Subery, self).reopen(**kwa)

        self.cans = DomSuber(db=self, subkey='cans.')
        self.drqs = DomIoSuber(db=self, subkey="drqs.")  # durable queue
        self.dsqs = DomIoSetSuber(db=self, subkey="dsqs.")  # durable set queue

        return self.env

