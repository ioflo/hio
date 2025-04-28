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

from hio import HierError

from ..hier import bagging
from ..hier import canning
from ..doing import Doer
from ..during import Duror, SuberBase, Suber, IoSetSuber
from ...help import isNonStringIterable

"""Hold is Mine subclass that on writes intercepts key and keys and then
also saves updates value in durable storage for value object CanDom and Durq
serializations
Likewise on reads intercepts key and keys and reads from durable storage
and extracts name of class so can deserialize into object subclass

Hold has attribute of Durk whose attributes are subdbs
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

    forces .sep to '_'
    changes ._ser and ._des methods to serialize TymeDom subclasses for db
    with default prosep for class name proem from json body is `\n`

    Adds type of Dom as proem to value which is stripped off when deserializing
    type of Dom need to get it from value as class name
    need Can class registry so can look up class by name

    Inherited Class Attribues:
        Sep (str): default separator to convert keys iterator to key bytes for db key

    Inherited Attributes:
        db (dbing.LMDBer): base LMDB db
        sdb (lmdb._Database): instance of lmdb named sub db for this Suber
        sep (str): separator for combining keys tuple of strs into key bytes
        verify (bool): True means reverify when ._des from db when applicable
                       False means do not reverify. Default False

    ClassAttributes:
        ProSep (str): separator class name proem to serialized TymeDom instance

    Attributes
        prosep (str): separator class name proem to serialized TymeDom instance
                      default is self.ProSep == '\n'

    """
    ProSep = '\n'  # separator class name proem to serialized TymeDom instance

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
            prosep (str|None): separator class name proem to serialized TymeDom instance
                               default is self.ProSep == '\n'
        """
        super(DomSuberBase, self).__init__(db=db, subkey=subkey, sep=sep, **kwa)
        self.prosep = prosep if prosep is not None else self.ProSep


    def _ser(self, val: bagging.TymeDom):
        """Serialize value to json bytes to store in db with proem that is
        class name. Must be in registry. Uses b'\n' as separator between
        proem class name and json serialization of val

        Parameters:
            val (TymeDom): encodable as bytes json
        """
        try:
            klas = val._registry[val.__class__.__name__]
        except KeyError as ex:
            raise HierError(f"Unregistered subclass instance={val}") from ex

        return (klas.__name__.encode() + self.prosep.encode() + val._asjson())


    def _des(self, val: bytes|memoryview):
        """Deserialize val to TymeDom subclass instance as given by proem
        prepended to json serialization of TymeDom subclass instance
        Uses b'\n' as separator between proem class name and json serialization
        of val

        Parameters:
            val (bytes|memoryview): proem\njson

        Returns:
            dom (TymeDom): instance of TymeDom subclass as registered under proem

        """
        if isinstance(val, memoryview):  # memoryview is always bytes
            val = bytes(val)  # convert to bytes

        proem, ser = val.split(sep=self.prosep.encode(), maxsplit=1)
        proem = proem.decode()
        try:
            klas = bagging.TymeDom._registry[proem]
        except KeyError as ex:
            raise HierError(f"Unregistered serialized subclass={proem}") from ex

        return (klas._fromjson(ser))


class DomSuber(DomSuberBase, Suber):
    """Subclass of (DomSuberBase, Suber) with values that are serialized CanDom
    subclasses.

    forces .sep to '_'
    forces .prosep to '\n'

    Adds type of Dom as proem to value which is stripped off when deserializing
    type of Dom need to get it from value as class name
    need Can class registry so can look up class by name

    """

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
                               default is self.ProSep == '\n'


        """
        super(DomSuber, self).__init__(db=db, subkey=subkey,
                                       sep=sep, prosep=prosep, **kwa)


    def _ser(self, val: canning.CanDom):
        """Serialize value to json bytes to store in db with proem that is
        class name. Must be in registry. Uses b'\n' as separator between
        proem class name and json serialization of val

        Parameters:
            val (CanDom): encodable as bytes json
        """
        if not isinstance(val, canning.CanDom):
            raise HierError(f"Expected instance of CanDom got {val}")

        return super(DomSuber, self)._ser(val=val)



    def _des(self, val: bytes|memoryview):
        """Deserialize val to CanDom subclass instance as given by proem
        prepended to json serialization of CanDom subclass instance
        Uses b'\n' as separator between proem class name and json serialization
        of val

        Parameters:
            val (bytes|memoryview): proem\njson

        Returns:
            dom (CanDom): instance as registered under proem

        """
        can = super(DomSuber, self)._des(val=val)
        if not isinstance(can, canning.CanDom):
            raise HierError(f"Expected instance of CanDom got {can}")

        return (can)


class DomIoSetSuber(DomSuberBase, IoSetSuber):
    """Subclass of (DomSuberBase, IoSetSuber) with values that are serialized
    TymeDom subclasses.

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



class Durk(Duror):
    """Durk subclass of Duror for managing durable storage action data

    ToDo:  change to use DomSuber and DomIoSetSuber

    """
    def __init__(self, **kwa):
        """
        Setup named sub databases.

        Inherited Parameters:  (see Duror)


        """
        super(Durk, self).__init__(**kwa)


    def reopen(self, **kwa):
        """Open sub databases

        Attributes:
            cans (Suber): subdb whose values are serialized Can instances
                Can is a durable Bag
            drqs (IoSetSub): subdb whose values are serialized Durq instances
                Durq is a durable Deck (deque)

        """
        super(Durk, self).reopen(**kwa)

        self.cans = Suber(db=self, subkey='cans.')
        self.drqs = IoSetSuber(db=self, subkey="drqs.")

        return self.env
