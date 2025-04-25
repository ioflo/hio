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

from ..doing import Doer
from ..filing import Filer
from ..during import Duror, Suber, IoSetSuber
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
