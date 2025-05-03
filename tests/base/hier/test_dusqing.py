# -*- encoding: utf-8 -*-
"""tests.base.hier.test_dusqing module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest

import os
from ordered_set import OrderedSet as oset

from hio import HierError
from hio.help import RegDom
from hio.base import Duror, openDuror, Subery, DomIoSuber, DomIoSetSuber
from hio.base.hier import Dusq, Bag


def test_dusq_basic():
    """Test Dusq class basic"""
    dusq = Dusq()  # test defaults

    assert not dusq  # empty
    assert isinstance(dusq._oset, oset)
    assert dusq.stale
    assert not dusq.durable
    assert dusq._sdb is None
    assert dusq._key is None
    assert repr(dusq) == 'Dusq([])'

    b0 = Bag(value=0)
    b1 = Bag(value=1)
    b2 = Bag(value=2)
    b3 = Bag(value=3)
    b4 = Bag(value=4)
    b5 = Bag(value=5)
    b6 = Bag(value=6)
    b7 = Bag(value=7)
    b8 = Bag(value=8)

    with pytest.raises(IndexError):
        dusq.pull(emptive=False)

    assert dusq.pull() is None

    assert dusq.push(b0)
    dusq.push(b1)
    dusq.push(b2)

    assert dusq  # not empty
    assert dusq.push(None) is False  # can't push None

    assert repr(dusq) == 'Dusq([Bag(value=0), Bag(value=1), Bag(value=2)])'

    assert dusq.pull() == b0
    assert dusq.pull() == b1
    assert dusq.pull() == b2
    assert dusq.pull() is None

    bvals = [b0, b1, b2, b3, b4, b5, b6, b7, b3]
    uvals = [b0, b1, b2, b3, b4, b5, b6, b7]  # all unique for set
    dusq.update(bvals)
    assert len(dusq) == 8  # b3 duplicated so deduped on update to set
    assert list(dusq) == uvals

    # test iter
    vals = [val for val in dusq]
    assert vals == uvals

    assert dusq.clear()
    assert len(dusq) == 0

    dusq = Dusq(bvals)
    assert len(dusq) == 8
    assert dusq.stale
    assert dusq  # not empty

    while dusq:
        assert dusq.pull() is not None

    assert not dusq  # empty

    with openDuror(cls=Subery) as subery:  # opens with temp=True by default
        assert isinstance(subery, Subery)
        assert subery.name == "test"
        assert subery.temp == True

        assert isinstance(subery.dsqs, DomIoSetSuber)

        key = "mydusq"

        dusq = Dusq()
        assert isinstance(dusq._oset, oset)
        assert dusq.stale
        assert not dusq.durable
        dusq._sdb = subery.dsqs
        dusq._key = key
        assert dusq._sdb == subery.dsqs
        assert dusq._key == key
        assert dusq.durable

        assert not dusq  # empty
        assert dusq.push(None) is False  # can't push None
        assert not dusq

        assert dusq.push(b5)
        assert not dusq.stale
        assert dusq._sdb.getFirst(key) == b5
        assert dusq._sdb.get(key) == [b5]

        assert dusq.push(b6)
        assert not dusq.stale
        assert dusq._sdb.getLast(key) == b6
        assert dusq._sdb.get(key) == [b5, b6]

        assert dusq.pull() == b5
        assert dusq.pull() == b6
        assert dusq.pull() == None
        assert dusq._sdb.cnt(key) == 0

        assert dusq.update(bvals)
        assert dusq._sdb.get(key) == uvals  # only unique
        assert len(dusq) == 8

        # test iter
        vals = [val for val in dusq]
        assert vals == uvals

        assert dusq.clear()
        assert len(dusq) == 0
        assert dusq._sdb.cnt(key) == 0

        # test sync with pre-existing database
        dusq.update(bvals)  # setup sdb  with some values
        # create vacuous new durq to sync with pre-existing sdb
        dusq = Dusq()
        assert isinstance(dusq._oset, oset)
        assert dusq.stale
        assert not dusq.durable
        dusq._sdb = subery.dsqs
        dusq._key = key
        assert dusq._sdb == subery.dsqs
        assert dusq._key == key
        assert dusq.durable
        assert not len(dusq)
        assert not dusq  # empty
        assert dusq._sdb.get(key) == uvals
        assert dusq.sync()
        assert not dusq.stale
        assert len(dusq) == 8

        # test sync of pre-existing durq with empty sdb
        key = 'thatdusq'
        assert subery.dsqs.get(key) == []  # nothing there
        dusq = Dusq(bvals)  # dusq not linked to sdb
        assert len(dusq) == 8  # only unique values in bvals
        assert dusq.stale
        assert dusq._sdb is None
        assert dusq._key is None
        assert not dusq.durable
        dusq._sdb = subery.dsqs
        dusq._key = key
        assert dusq.durable
        assert dusq.sync()
        assert not dusq.stale
        assert len(dusq) == 8
        dusq._sdb.get(dusq._key) == uvals

    assert not os.path.exists(subery.path)
    assert not subery.opened
    """Done Test"""


if __name__ == "__main__":
    test_dusq_basic()

