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
from hio.base import (Duror, openDuror, Suber, IoSetSuber,
                      DomSuberBase, DomSuber, Subery)
from hio.base.hier import Hold
from hio.base.hier import Bag, CanDom, Can
from hio.help import RawDom, RegDom



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
        assert can._stale == True
        assert can._fresh == False
        assert can._bulk == False

        can._update(value=9)
        assert can._stale == True
        assert can._fresh == False
        assert can._bulk == False
        assert can.value == 9

        hold.blue = can  # now inject by adding to hold and syncing with durable
        assert can._key == "blue"
        assert can._sdb == subery.cans
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
        assert can._write()

        can = Can(value="hello")
        assert can._key == None
        assert can._sdb == None
        assert can._stale == True
        assert can._fresh == False
        assert can._bulk == False

        hold["red"] = can  # now inject by adding to hold
        assert can._key == "red"
        assert can._sdb == subery.cans
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
            assert v._stale == False
            assert v._fresh == False
            assert v._bulk == False
            assert v._write()
            assert v._stale == False

        # test read of prestored can at key when new can assigned to key
        can = Can(value=True)
        key = "test"
        assert subery.cans.put(key, can)
        pan = subery.cans.get(key)
        assert pan == can
        assert pan.value == True

        can = Can()  # new can with defaults
        assert can.value is None
        hold[key] = can  # assign to key
        assert hold[key]._stale == False
        assert hold[key]._fresh == False
        assert hold[key].value == True  # picks up saved value

        hold[key].value = False
        assert hold[key]._stale == False
        assert hold[key]._fresh == False
        assert hold[key].value == False

        # ToDo when get another subclass of CanDom besides Can then do test that
        # raises exception when saved instance is different class than assigned.


    assert not os.path.exists(subery.path)
    assert not subery.opened

    """Done Test"""


def test_domsuberbase():
    """Test DomSuberBase, Duror sub database base class"""

    with openDuror() as duror:
        assert isinstance(duror, Duror)
        assert duror.name == "test"
        assert duror.opened

        assert DomSuberBase.Sep == '_'
        assert DomSuberBase.ProSep == '\n'

        suber = DomSuberBase(db=duror)
        assert isinstance(suber, DomSuberBase)
        assert not suber.sdb.flags()["dupsort"]
        assert suber.sep == "_"
        assert suber.prosep == '\n'

        keys = ('key', 'top')
        key = suber._tokey(keys)
        assert key == b'key_top'
        assert suber._tokeys(key) == keys

        dom = RegDom()

        ser = suber._ser(dom)
        assert ser == b'RegDom\n{}'  # empty fields

        proem, serj = ser.split(suber.prosep.encode(), maxsplit=1)
        assert proem == b'RegDom'
        assert serj == b'{}'
        proem = proem.decode()
        assert proem in RegDom._registry

        dom = suber._des(ser)
        assert isinstance(dom, RegDom)

        bag = Bag()

        ser = suber._ser(bag)
        assert ser == b'Bag\n{"value":null}'  # value field

        proem, serj = ser.split(suber.prosep.encode(), maxsplit=1)
        assert proem == b'Bag'
        assert serj == b'{"value":null}'
        proem = proem.decode()
        assert proem in Bag._registry

        bag = suber._des(ser)
        assert isinstance(bag, Bag)

        can = CanDom()

        ser = suber._ser(can)
        assert ser == b'CanDom\n{}'  # empty fields

        proem, serj = ser.split(suber.prosep.encode(), maxsplit=1)
        assert proem == b'CanDom'
        assert serj == b'{}'
        proem = proem.decode()
        assert proem in CanDom._registry

        can = suber._des(ser)
        assert isinstance(can, CanDom)

        can = Can()
        assert can.value == None

        ser = suber._ser(can)
        assert ser == b'Can\n{"value":null}'  # value field

        proem, serj = ser.split(suber.prosep.encode(), maxsplit=1)
        assert proem == b'Can'
        assert serj == b'{"value":null}'
        proem = proem.decode()
        assert proem in Can._registry

        can = suber._des(ser)
        assert isinstance(can, CanDom)
        assert can.value == None

    assert not os.path.exists(duror.path)
    assert not duror.opened

    """Done Test"""


def test_domsuber():
    """Test DomSuber, Duror sub database class"""

    with openDuror() as duror:
        assert isinstance(duror, Duror)
        assert duror.name == "test"
        assert duror.opened

        assert DomSuber.Sep == '_'
        assert DomSuber.ProSep == '\n'

        suber = DomSuber(db=duror)
        assert isinstance(suber, DomSuber)
        assert not suber.sdb.flags()["dupsort"]
        assert suber.sep == "_"
        assert suber.prosep == '\n'

        keys = ('key', 'top')
        key = suber._tokey(keys)
        assert key == b'key_top'
        assert suber._tokeys(key) == keys

        # test attempt to _ser _des with non RegDom subclass
        dom = RawDom()
        with pytest.raises(HierError):
            ser = suber._ser(dom)

        ser = b'RawDom\n{}'  # empty fields
        with pytest.raises(HierError):
            dom = suber._des(ser)

        # test with RegDom subclasses
        bag = Bag()
        ser = suber._ser(bag)
        assert ser == b'Bag\n{"value":null}'
        bag = suber._des(ser)
        assert bag.value == None

        can = CanDom()
        ser = suber._ser(can)
        assert ser == b'CanDom\n{}'  # empty fields

        proem, serj = ser.split(suber.prosep.encode(), maxsplit=1)
        assert proem == b'CanDom'
        assert serj == b'{}'
        proem = proem.decode()
        assert proem in CanDom._registry

        can = suber._des(ser)
        assert isinstance(can, CanDom)

        can = Can()
        assert can.value == None

        ser = suber._ser(can)
        assert ser == b'Can\n{"value":null}'  # value field

        proem, serj = ser.split(suber.prosep.encode(), maxsplit=1)
        assert proem == b'Can'
        assert serj == b'{"value":null}'
        proem = proem.decode()
        assert proem in Can._registry

        can = suber._des(ser)
        assert isinstance(can, CanDom)
        assert can.value == None

        # Test methods to save to lmdb
        val0 = Can(value=0)
        val1 = Can(value=1)
        val2 = Can(value=2)
        val3 = Can(value=3)

        keys = ("test_key", "0000")
        suber.put(keys=keys, val=val0)
        actual = suber.get(keys=keys)
        assert actual == val0

        suber.rem(keys)
        actual = suber.get(keys=keys)
        assert actual is None

        suber.put(keys=keys, val=val0)
        actual = suber.get(keys=keys)
        assert actual == val0

        result = suber.put(keys=keys, val=val1)
        assert not result
        actual = suber.get(keys=keys)
        assert actual == val0

        result = suber.pin(keys=keys, val=val1)
        assert result
        actual = suber.get(keys=keys)
        assert actual == val1

        suber.rem(keys)
        actual = suber.get(keys=keys)
        assert actual is None

        # test with keys as string not tuple
        keys = "keystr"

        suber.put(keys=keys, val=val2)
        actual = suber.get(keys=keys)
        assert actual == val2

        suber.rem(keys)

        actual = suber.get(keys=keys)
        assert actual is None


        keys = ("test_key", "0001")

        suber.put(keys=keys, val=val1)
        actual = suber.get(("not_found", "0001"))
        assert actual is None


        suber = DomSuber(db=duror, subkey='pugs.')
        assert isinstance(suber, DomSuber)

        suber.put(keys=("a","0"), val=val0)
        suber.put(keys=("a","1"), val=val1)
        suber.put(keys=("a","2"), val=val2)
        suber.put(keys=("a","3"), val=val3)

        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('a', '0'), val0),
                        (('a', '1'), val1),
                        (('a', '2'), val2),
                        (('a', '3'), val3)]

        suber.put(keys=("b","0"), val=val0)
        suber.put(keys=("b","1"), val=val1)
        suber.put(keys=("bc","2"), val=val2)
        suber.put(keys=("ac","3"), val=val3)

        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('a', '0'), val0),
                        (('a', '1'), val1),
                        (('a', '2'), val2),
                        (('a', '3'), val3),
                        (('ac', '3'), val3),
                        (('b', '0'), val0),
                        (('b', '1'), val1),
                        (('bc', '2'), val2)]


        # test with top keys for partial tree
        topkeys = ("b","")  # last element empty to force trailing separator
        items = [(keys, val) for keys, val in suber.getItemIter(keys=topkeys)]
        assert items == [(('b', '0'), val0),
                         (('b', '1'), val1)]

        topkeys = ("a","")  # last element empty to force trailing separator
        items = [(keys, val) for keys, val in suber.getItemIter(keys=topkeys)]
        assert items == [(('a', '0'), val0),
                        (('a', '1'), val1),
                        (('a', '2'), val2),
                        (('a', '3'), val3)]

        # test with top parameter
        keys = ("b", )  # last element empty to force trailing separator
        items = [(keys, val) for keys, val in suber.getItemIter(keys=keys, topive=True)]
        assert items == [(('b', '0'), val0),
                         (('b', '1'), val1)]

        keys = ("a", )  # last element empty to force trailing separator
        items = [(keys, val) for keys, val in suber.getItemIter(keys=keys, topive=True)]
        assert items == [(('a', '0'), val0),
                        (('a', '1'), val1),
                        (('a', '2'), val2),
                        (('a', '3'), val3)]

        # Test trim
        assert suber.trim(keys=("b", ""))
        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('a', '0'), val0),
                        (('a', '1'), val1),
                        (('a', '2'), val2),
                        (('a', '3'), val3),
                        (('ac', '3'), val3),
                        (('bc', '2'), val2)]

        assert suber.trim(keys=("a", ""))
        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('ac', '3'), val3), (('bc', '2'), val2)]

        assert suber.trim()
        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == []

        assert not suber.trim()

    assert not os.path.exists(duror.path)
    assert not duror.opened
    """Done Test"""


def test_subery_basic():
    """Test Subery class"""

    subery = Subery(reopen=True)  # default is to not reopen
    assert isinstance(subery, Subery)
    assert subery.name == "main"
    assert subery.temp == False
    assert isinstance(subery.env, lmdb.Environment)
    assert subery.path.endswith(os.path.join("hio", "db", "main"))
    assert subery.env.path() == subery.path
    assert os.path.exists(subery.path)

    assert isinstance(subery.cans, DomSuber)
    assert isinstance(subery.cans.sdb, lmdb._Database)

    assert isinstance(subery.drqs, IoSetSuber)
    assert isinstance(subery.drqs.sdb, lmdb._Database)

    subery.close(clear=True)
    assert not os.path.exists(subery.path)
    assert not subery.opened

    # test not opened on init
    subery = Subery(reopen=False)
    assert isinstance(subery, Subery)
    assert subery.name == "main"
    assert subery.temp == False
    assert subery.opened == False
    assert subery.path == None
    assert subery.env == None

    subery.reopen()
    assert subery.opened
    assert isinstance(subery.env, lmdb.Environment)
    assert subery.path.endswith(os.path.join("hio", "db", "main"))
    assert subery.env.path() == subery.path
    assert os.path.exists(subery.path)

    assert isinstance(subery.cans, DomSuber)
    assert isinstance(subery.cans.sdb, lmdb._Database)

    assert isinstance(subery.drqs, IoSetSuber)
    assert isinstance(subery.drqs.sdb, lmdb._Database)

    subery.close(clear=True)
    assert not os.path.exists(subery.path)
    assert not subery.opened

    # Test using context manager
    with openDuror(cls=Subery) as subery:  # opens with temp=True by default
        assert isinstance(subery, Subery)
        assert subery.name == "test"
        assert subery.temp == True
        assert isinstance(subery.env, lmdb.Environment)
        tempDirPath = (os.path.join(os.path.sep, "tmp")
                       if platform.system() == "Darwin" else tempfile.gettempdir())
        tempDirPath = os.path.normpath(tempDirPath)
        path = os.path.normpath(subery.path)
        #_, path = os.path.splitdrive(os.path.normpath(subery.path))
        assert path.startswith(os.path.join(tempDirPath, "hio_lmdb_"))
        assert subery.path.endswith(os.path.join("_test", "hio", "db", "test"))
        assert subery.env.path() == subery.path
        assert os.path.exists(subery.path)

        assert isinstance(subery.cans, DomSuber)
        assert isinstance(subery.cans.sdb, lmdb._Database)

        assert isinstance(subery.drqs, IoSetSuber)
        assert isinstance(subery.drqs.sdb, lmdb._Database)


    assert not os.path.exists(subery.path)
    assert not subery.opened

    """Done Test"""


if __name__ == "__main__":
    test_hold_basic()
    test_domsuberbase()
    test_domsuber()
    test_subery_basic()
