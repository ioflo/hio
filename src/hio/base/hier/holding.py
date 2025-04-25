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
also saves updates value in durable storage for value object RawDom serializations
Likewise on reads intercepts key and keys and reads from durable storage
and extracts name of class so can deserialize into object subclass

for durable deque then each value in deque is a RawDom which gets stored
in its one insertion ordered key in backing durable storage

So python magic in Hold
Each Can object has fields that ref appropriate Suber subclass so can store
at key in the Suber.



"""




# in holding
# todo DomSuber subclass that forces .ser to '_' and .ionser to '.'
# changes ._ser and ._des methods to serialize RawDom subclasses for db

# todo DomIoSetSuber subclass that forces .ser to '_' and .ionser to '.'
# changes ._ser and ._des methods to serialize RawDom subclasses for db

# here
# change Dock to use DomSuber and DomIoSetSuber





class Duck(Duror):
    """Duck subclass of Duror for managing durable storage action data

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
