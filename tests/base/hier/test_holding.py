# -*- encoding: utf-8 -*-
"""
tests.hold.test_holding module

"""
import pytest
import os
import platform
import tempfile
import lmdb

from hio import HierError
from hio.base import Duror, openDuror, Subery
from hio.base.hier import Hold, Can, Durq, Bag


def test_hold_basic():
    """Test Hold basic"""
    hold = Hold()  # test defaults
    assert isinstance(hold, dict)
    assert isinstance(hold, Hold)
    assert hold.subery is None  # test property getter
    #assert isinstance(hold.subery, Subery)
    #assert hold.subery.name == "main"
    #hold.subery.close(clear=True)
    #assert not os.path.exists(hold.subery.path)


    with openDuror(cls=Subery) as subery:  # opens with temp=True by default
        assert isinstance(subery, Subery)
        assert subery.name == "test"
        assert subery.temp == True

        hold = Hold(_hold_subery=subery)  # test on init
        assert hold.subery == subery  # test property getter

        hold._hold_subery = subery  # must use actual key not property
        assert hold.subery == subery

        hold.subery = None  # assign to item directly does not shadow property
        assert hold["subery"] == None  # can still get item property does not shadow
        assert hold.subery == subery  # item assignment does not shadow property

        hold.update(a=1, b=2, c=3)
        assert list(hold.items()) == [('_hold_subery', subery),
                                        ('subery', None),
                                        ('a', 1),
                                        ('b', 2),
                                        ('c', 3)]

        # test durable can with subery
        can = Can(value=10)
        assert can._key == None
        assert can._sdb == None
        assert not can._durable
        assert can._stale == True
        assert can._fresh == False
        assert can._bulk == False

        can._update(value=9)
        assert not can._durable
        assert can._stale == True
        assert can._fresh == False
        assert can._bulk == False
        assert can.value == 9

        hold.blue = can  # now inject by adding to hold and syncing with durable
        assert can._key == "blue"
        assert can._sdb == subery.cans
        assert can._durable
        assert can._stale == False
        assert can._fresh == False
        assert can._bulk == False

        can.value = 15  # now update gets written to disk
        assert can._stale == False
        assert can._fresh == False
        assert can._bulk == False
        assert can._sdb.get(can._key) == can
        assert can.value == 15
        assert can._sync(force=True)
        assert can._pin()

        can = Can(value="hello")
        assert can._key == None
        assert can._sdb == None
        assert not can._durable
        assert can._stale == True
        assert can._fresh == False
        assert can._bulk == False

        hold["red"] = can  # now inject by adding to hold
        assert can._key == "red"
        assert can._sdb == subery.cans
        assert can._durable
        assert can._stale == False
        assert can._fresh == False
        assert can._bulk == False

        can["value"] = "goodbye"  # test update gets written to disk
        assert can._stale == False
        assert can._fresh == False
        assert can._sdb.get(can._key) == can
        assert can.value == "goodbye"

        can._update(value="see ya")
        assert can._stale == False
        assert can._fresh == False
        assert can._sdb.get(can._key) == can
        assert can.value == "see ya"

        can0 = Can(value=0)
        can1 = Can(value=1)
        can2 = Can(value=2)
        can3 = Can(value=3)
        can4 = Can(value=4)
        can5 = Can(value=5)

        d = dict(a=can0, b=can1, c=can2, d=can3, e=can4, f=can5)

        hold.update([("a", can0), ("b", can1)], c=can2)
        hold.update({"d": can3, "e": can4}, f=can5)

        for k, v in d.items():
            assert v._key == k
            assert v._sdb == subery.cans
            assert v._durable
            assert v._stale == False
            assert v._fresh == False
            assert v._bulk == False
            assert v._pin()
            assert v._stale == False

        # test read of prestored can at key when new can assigned to key
        can = Can(value=True)
        assert not can._durable
        key = "test"
        assert subery.cans.put(key, can)
        pan = subery.cans.get(key)
        assert pan == can
        assert pan.value == True

        can = Can()  # new can with defaults
        assert can.value is None
        assert not can._durable
        hold[key] = can  # assign to key
        assert can._durable
        assert hold[key]._stale == False
        assert hold[key]._fresh == False
        assert hold[key].value == True  # picks up saved value

        hold[key].value = False
        assert hold[key]._stale == False
        assert hold[key]._fresh == False
        assert hold[key].value == False

        # ToDo create custom test subclass of CanDom besides Can  to test that
        # raises exception when saved instance is different class than assigned.

        #Test Durq with hold subery and assign and sync by hold
        b0 = Bag(value=0)
        b1 = Bag(value=1)

        dkey = 'durqness'
        durq = Durq()
        assert durq.stale
        assert durq._sdb is None
        assert durq._key is None
        assert not durq.durable
        durq.push(b0)
        durq.push(b1)
        assert durq.stale

        hold[dkey] = durq
        assert not durq.stale
        assert durq.durable
        assert durq._sdb == subery.drqs
        assert durq._key == dkey
        assert durq._sdb.get(durq._key) == [b0, b1]


    assert not os.path.exists(subery.path)
    assert not subery.opened

    """Done Test"""




if __name__ == "__main__":
    test_hold_basic()
