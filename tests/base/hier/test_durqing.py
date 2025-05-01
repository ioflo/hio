"""tests.base.hier.test_durqing module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest

import os
from collections import deque


from hio import HierError
from hio.help import RegDom
from hio.base import Duror, openDuror, Subery, DomIoSuber
from hio.base.hier import Durq, Bag


def test_durq_basic():
    """Test Durq class basic"""
    durq = Durq()  # test defaults
    assert isinstance(durq._deq, deque)
    assert durq.stale
    assert durq.sdb is None
    assert durq.key is None
    assert repr(durq) == 'Durq([])'

    b0 = Bag(value=0)
    b1 = Bag(value=1)
    b2 = Bag(value=2)
    b3 = Bag(value=3)
    b4 = Bag(value=4)
    b5 = Bag(value=5)
    b6 = Bag(value=6)
    b7 = Bag(value=7)

    with pytest.raises(IndexError):
        durq.pull(emptive=False)

    assert durq.pull() is None

    durq.push(b0)
    durq.push(b1)
    durq.push(b2)

    assert repr(durq) == 'Durq([Bag(value=0), Bag(value=1), Bag(value=2)])'

    assert durq.pull() == b0
    assert durq.pull() == b1
    assert durq.pull() == b2
    assert durq.pull() is None

    bvals = [b0, b1, b2, b3, b4, b5, b6, b7, b3]
    durq.extend(bvals)
    assert len(durq) == 9
    assert durq.count() == 9
    assert durq.count(b3) == 2

    # test iter
    vals = [val for val in durq]
    assert vals == bvals

    durq.clear()
    assert len(durq) == 0

    with openDuror(cls=Subery) as subery:  # opens with temp=True by default
        assert isinstance(subery, Subery)
        assert subery.name == "test"
        assert subery.temp == True

        assert isinstance(subery.drqs, DomIoSuber)

        key = "mydurq"

        durq = Durq(sdb=subery.drqs, key=key)
        assert isinstance(durq._deq, deque)
        assert durq.stale
        assert durq.sdb == subery.drqs
        assert durq.key == key

        durq.push(b5)
        assert not durq.stale
        assert durq.sdb.getFirst(key) == b5
        assert durq.sdb.get(key) == [b5]

        durq.push(b6)
        assert not durq.stale
        assert durq.sdb.getLast(key) == b6
        assert durq.sdb.get(key) == [b5, b6]

        assert durq.pull() == b5
        assert durq.pull() == b6
        assert durq.pull() == None
        assert durq.sdb.cnt(key) == 0

        durq.extend(bvals)
        assert durq.sdb.get(key) == bvals
        assert len(durq) == 9
        assert durq.count() == 9
        assert durq.count(b3) == 2

        # test iter
        vals = [val for val in durq]
        assert vals == bvals

        durq.clear()
        assert len(durq) == 0
        assert durq.sdb.cnt(key) == 0


        # test sync with pre-existing database
        durq.extend(bvals)  # setup sdb  with some values
        # create vacuous new durq to sync with pre-existing sdb
        durq = Durq(sdb=subery.drqs, key=key)
        assert isinstance(durq._deq, deque)
        assert durq.stale
        assert durq.sdb == subery.drqs
        assert durq.key == key
        assert not len(durq)
        assert durq.sdb.get(key) == bvals
        assert durq.sync()
        assert not durq.stale
        assert len(durq) == 9

        # test sync of pre-existing durq with empty sdb
        key = 'thatdurq'
        assert subery.drqs.get(key) == []  # nothing there
        durq = Durq()  # durq not linked to sdb
        assert durq.stale
        assert durq.sdb is None
        assert durq.key is None
        durq.extend(bvals)
        assert len(durq) == 9
        assert durq.stale
        durq.sdb = subery.drqs
        durq.key = key
        assert durq.sync()
        assert not durq.stale
        durq.sdb.get(durq.key) == bvals
        assert len(durq) == 9


    assert not os.path.exists(subery.path)
    assert not subery.opened


    """Done Test"""

if __name__ == "__main__":
    test_durq_basic()


