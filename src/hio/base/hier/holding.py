# -*- encoding: utf-8 -*-
"""hio.hold.holding Module

Provides durable data storage with LMDB

"""
from __future__ import annotations  # so type hints of classes get resolved later

import os
import platform
import stat
import tempfile
from contextlib import contextmanager

import lmdb
from ordered_set import OrderedSet as oset

import hio

from ..hier import canning
from ..doing import Doer
from ..during import Duror, SuberBase, Suber, IoSetSuber
from ...help import isNonStringIterable

"""Hold is Mine subclass that on writes intercepts key and keys and then
also saves updates value in durable storage for value object CanBase and Durq
serializations
Likewise on reads intercepts key and keys and reads from durable storage
and extracts name of class so can deserialize into object subclass

Hold has attribute of Duck whose attributes are subdbs
.cans
.drqs

Hold injects reference to one of these based on the type of value and the Hold
key  into ._sdb and ._key.  When not a durable value then no injection.
This allows the value then to read/write to its ._sdb at ._key the fields
of the Can when Can or Durq when Durq


for durable deque then each value in deque is a Bag which gets stored
in its one insertion ordered key in backing durable storage

So python magic in Hold

Need class registry for TymeDom subclasses so that DomSuber and DomIoSetSuber
can look up class by name and deserialize

"""

class DomSuberBase(SuberBase):
    """Subclass of Suber with values that are serialized TymeDom subclasses.

    forces .ser to '_'
    changes ._ser and ._des methods to serialize CanBase subclasses for db

    Adds type of Dom as proem to value which is stripped off when deserializing
    type of Dom need to get it from value as class name
    need Bag class registry so can look up class by name

    """

    def __init__(self, db: Duror, *, subkey: str = 'cans.', sep='_', **kwa):
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


        """
        super(DomSuberBase, self).__init__(db=db, subkey=subkey, sep=sep, **kwa)


    def _ser(self, val: canning.CanBase):
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
        return (val.decode("utf-8") if hasattr(val, "decode") else val)


class DomSuber(Suber):
    """Subclass of Suber with values that are serialized TymeDom subclasses.

    forces .ser to '_'
    changes ._ser and ._des methods to serialize TymeDom subclasses for db

    Adds type of Dom as proem to value which is stripped off when deserializing
    type of Dom need to get it from value as class name
    need Bag class registry so can look up class by name

    """

    def __init__(self, db: Duror, *, subkey: str = 'cans.', sep='_', **kwa):
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


        """
        super(Suber, self).__init__(db=db, subkey=subkey, sep=sep, **kwa)


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
        return (val.decode("utf-8") if hasattr(val, "decode") else val)


class DomIoSetSuber(IoSetSuber):
    """Subclass of IoSetSuber with values that are serialized TymeDom subclasses.

    forces .ser to '_'
    changes ._ser and ._des methods to serialize TymeDom subclasses for db

    Adds type of Dom as proem to value which is stripped off when deserializing
    type of Dom need to get it from value as class name
    need Bag class registry so can look up Klas by name

    """

    def __init__(self, db: Duror, *, subkey: str = 'cans.', sep='_', **kwa):
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


        """
        super(DomIoSetSuber, self).__init__(db=db, subkey=subkey, sep=sep, **kwa)


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
        return (val.decode("utf-8") if hasattr(val, "decode") else val)



class Duck(Duror):
    """Duck subclass of Duror for managing durable storage action data

    ToDo:  change to use DomSuber and DomIoSetSuber

    """
    def __init__(self, **kwa):
        """
        Setup named sub databases.

        Inherited Parameters:  (see Duror)


        """
        super(Duck, self).__init__(**kwa)


    def reopen(self, **kwa):
        """Open sub databases

        Attributes:
            cans (Suber): subdb whose values are serialized Can instances
                Can is a durable Bag
            drqs (IoSetSub): subdb whose values are serialized Durq instances
                Durq is a durable Deck (deque)

        """
        super(Duck, self).reopen(**kwa)

        self.cans = Suber(db=self, subkey='cans.')
        self.drqs = IoSetSuber(db=self, subkey="drqs.")

        return self.env
