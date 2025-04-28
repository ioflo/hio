# -*- encoding: utf-8 -*-
"""
tests.hold.test_holding module

"""
import pytest
import os
import lmdb

from hio import HierError
from hio.base import Duror, openDuror, Suber, IoSetSuber
from hio.base.hier import DomSuberBase, DomSuber, Subery
from hio.base.hier import TymeDom, Bag, CanDom, Can



def test_hold_basic():
    """Test Hold basic"""

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

        dom = TymeDom()

        ser = suber._ser(dom)
        assert ser == b'TymeDom\n{}'  # empty fields

        proem, serj = ser.split(suber.prosep.encode(), maxsplit=1)
        assert proem == b'TymeDom'
        assert serj == b'{}'
        proem = proem.decode()
        assert proem in TymeDom._registry

        dom = suber._des(ser)
        assert isinstance(dom, TymeDom)

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


        dom = TymeDom()
        with pytest.raises(HierError):
            ser = suber._ser(dom)

        ser = b'TymeDom\n{}'  # empty fields
        with pytest.raises(HierError):
            dom = suber._des(ser)


        bag = Bag()
        with pytest.raises(HierError):
            ser = suber._ser(bag)

        ser = b'Bag\n{"value":null}'  # value field
        with pytest.raises(HierError):
            bag = suber._des(ser)

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
        _, path = os.path.splitdrive(os.path.normpath(subery.path))
        assert path.startswith(os.path.join(os.path.sep, "tmp", "hio_lmdb_"))
        assert subery.path.endswith(os.path.join("_test", "hio", "db", "test"))
        assert subery.env.path() == subery.path
        assert os.path.exists(subery.path)

        assert isinstance(subery.cans, Suber)
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
