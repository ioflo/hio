# -*- encoding: utf-8 -*-
"""hio.hold.holding Module

Provides durable data storage with LMDB

"""
from __future__ import annotations  # so type hints of classes get resolved later

import os
import platform
import stat
import tempfile
from collections.abc import Mapping
from contextlib import contextmanager
from typing import Any

import lmdb
from ordered_set import OrderedSet as oset

from hio import HierError

from ...help import NonStringIterable, Mine
from ..doing import Doer
from .canning import CanDom




class Hold(Mine):
    """Hold is Mine subclass that on writes intercepts key and keys and then
    also saves updates value in durable storage for value object CanDom and Durq
    serializations

    Hold has special item '_hold_subery' whose value is Subery instance or None.
    Read access is provided via the property .subery

    Subery attributes are the subdbs:
    .cans
    .drqs

    Hold injects reference to one of these based on the type of value and the Hold
    key  into ._sdb and ._key.  When not a durable value then no injection.
    This allows the value then to read/write to its ._sdb at ._key the fields
    of the Can when Can or Durq when Durq


    Properties:
        subery (None|Subery): gets instance from item at '_hold_subery' or None

    Methods:
        inject(self, key, val): injects .cans into val._sdb and key into val._key


    """
    def __init__(self, *pa, **kwa):
        """Convert keys that are tuples when positional argument is Iterable or
        Mapping to '.' joined strings

        dict __init__ signature options are:
            dict(**kwa)
            dict(mapping, **kwa)
            dict(iterable, **kwa)
        dict.update has same call signature
            d.update({"a": 5, "b": 2,}, c=3 , d=4)
        """
        self._hold_subery = None
        super(Hold, self).__init__(*pa, **kwa)


    def __setitem__(self, k, v):  # __setattr__ calls __setitem__
        k = self.tokey(k)  # get key to inject
        result = super(Hold, self).__setitem__(k, v)
        self.inject(k, v)
        return result


    def update(self, *pa, **kwa):
        """Convert keys that are tuples when positional argument is Iterable or
        Mapping to '.' joined strings

        dict __init__ signature options are:
            dict(**kwa)
            dict(mapping, **kwa)
            dict(iterable, **kwa)
        dict.update has same call signature
            d.update({"a": 5, "b": 2,}, c=3 , d=4)

        """
        if len(pa) > 1:
            raise TypeError(f"Expected 1 positional argument got {len(pa)}.")

        if pa:
            di = pa[0]
            if isinstance(di, Mapping):
                rd = {}
                for k, v in di.items():
                    rd[self.tokey(k)] = v
                super(Hold, self).update(rd, **kwa)
                for k, v in rd.items():
                    self.inject(k, v)

            elif isinstance(di, NonStringIterable):
                ri = []
                for k, v in di:
                    ri.append((self.tokey(k), v))
                super(Hold, self).update(ri, **kwa)
                for k, v in ri:
                    self.inject(k, v)

            else:
                raise TypeError(f"Expected Mapping or NonStringIterable got "
                                f"{type(di)}.")

        else:
            super(Hold, self).update(**kwa)

        for k, v in kwa.items():
            self.inject(k, v)



    def inject(self, key, val):
        """When val is instance of CanDom, injects .tokey(key) into val._key and
        .subery.cans into val._sdb

        Parameters:
            key (str): for item
            val (Any|CanDom): for item. When instance subclass of CanDom then
                inject to ._key and ._sdb
        """
        if isinstance(val, CanDom):
            val._key = key
            val._sdb = self.subery.cans if self.subery else None
            val._sync()  # attempt to sync with sdb at key if any

    @property
    def subery(self):
        """Gets value of special item '_hold_subery'

        Returns:
            subery (None|Subery): instance or None
        """
        return self["_hold_subery"]



