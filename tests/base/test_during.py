# -*- encoding: utf-8 -*-
"""tests.help.test_during module

"""
import pytest

import os
import platform
import tempfile
import lmdb
from ordered_set import OrderedSet as oset

from hio import HierError
from hio.base import (Duror, openDuror, SuberBase, Suber, IoSuber, IoSetSuber,
                      DomSuberBase, DomSuber, DomIoSuber, DomIoSetSuber, Subery)
from hio.base.hier import Bag, CanDom, Can
from hio.help import RawDom, RegDom



def test_duror_basic():
    """Test Duror Class  """
    duror = Duror()
    assert isinstance(duror, Duror)
    assert duror.name == "main"
    assert duror.temp == False
    assert isinstance(duror.env, lmdb.Environment)
    assert duror.path.endswith(os.path.join("hio", "db", "main"))
    assert duror.env.path() == duror.path
    assert os.path.exists(duror.path)
    assert duror.opened

    duror.close(clear=True)
    assert not os.path.exists(duror.path)

    assert Duror.SuffixSize == 32
    assert Duror.MaxSuffix ==  340282366920938463463374607431768211455


    key = "ABCDEFG.FFFFFF"
    keyb = b"ABCDEFG.FFFFFF"

    ion = 0
    iokey = Duror.suffix(key, ion)
    assert iokey == b'ABCDEFG.FFFFFF.00000000000000000000000000000000'
    k, i = Duror.unsuffix(iokey)
    assert k == keyb
    assert i == ion

    ion = 64
    iokey = Duror.suffix(keyb, ion)
    assert iokey == b'ABCDEFG.FFFFFF.00000000000000000000000000000040'
    k, i = Duror.unsuffix(iokey)
    assert k == keyb
    assert i == ion

    iokey = Duror.suffix(key, Duror.MaxSuffix)
    assert iokey ==  b'ABCDEFG.FFFFFF.ffffffffffffffffffffffffffffffff'
    k, i = Duror.unsuffix(iokey)
    assert k == keyb
    assert i == Duror.MaxSuffix

    key = "ABCDEFG_FFFFFF"
    keyb = b"ABCDEFG_FFFFFF"

    ion = 0
    iokey = Duror.suffix(key, ion)
    assert iokey == b'ABCDEFG_FFFFFF.00000000000000000000000000000000'
    k, i = Duror.unsuffix(iokey)
    assert k == keyb
    assert i == ion

    ion = 64
    iokey = Duror.suffix(keyb, ion)
    assert iokey == b'ABCDEFG_FFFFFF.00000000000000000000000000000040'
    k, i = Duror.unsuffix(iokey)
    assert k == keyb
    assert i == ion

    iokey = Duror.suffix(key, Duror.MaxSuffix)
    assert iokey ==  b'ABCDEFG_FFFFFF.ffffffffffffffffffffffffffffffff'
    k, i = Duror.unsuffix(iokey)
    assert k == keyb
    assert i == Duror.MaxSuffix
    """Done Test"""


def test_openduror():
    """
    test contextmanager openduror
    """

    with openDuror() as duror:
        assert isinstance(duror, Duror)
        assert duror.name == "test"
        assert isinstance(duror.env, lmdb.Environment)
        tempDirPath = (os.path.join(os.path.sep, "tmp")
                       if platform.system() == "Darwin" else tempfile.gettempdir())
        tempDirPath = os.path.normpath(tempDirPath)
        path = os.path.normpath(duror.path)
        #_, path = os.path.splitdrive(os.path.normpath(duror.path))
        assert path.startswith(os.path.join(tempDirPath, "hio_lmdb_"))
        assert duror.path.endswith(os.path.join("_test", "hio", "db", "test"))
        assert duror.env.path() == duror.path
        assert os.path.exists(duror.path)
        assert duror.opened

    assert not os.path.exists(duror.path)
    assert not duror.opened

    with openDuror(name="blue") as duror:
        assert isinstance(duror, Duror)
        assert duror.name == "blue"
        assert isinstance(duror.env, lmdb.Environment)
        tempDirPath = (os.path.join(os.path.sep, "tmp")
                       if platform.system() == "Darwin" else tempfile.gettempdir())
        tempDirPath = os.path.normpath(tempDirPath)
        path = os.path.normpath(duror.path)
        #_, path = os.path.splitdrive(os.path.normpath(duror.path))
        assert path.startswith(os.path.join(tempDirPath, "hio_lmdb_"))
        assert duror.path.endswith(os.path.join("_test", "hio", "db", "blue"))
        assert duror.env.path() == duror.path
        assert os.path.exists(duror.path)
        assert duror.opened

    assert not os.path.exists(duror.path)
    assert not duror.opened

    with openDuror(name="red") as redbaser, openDuror(name="tan") as tanbaser:
        assert isinstance(redbaser, Duror)
        assert redbaser.name == "red"
        assert redbaser.env.path() == redbaser.path
        assert os.path.exists(redbaser.path)
        assert redbaser.opened

        assert isinstance(tanbaser, Duror)
        assert tanbaser.name == "tan"
        assert tanbaser.env.path() == tanbaser.path
        assert os.path.exists(tanbaser.path)
        assert tanbaser.opened

    assert not os.path.exists(redbaser.path)
    assert not redbaser.opened
    assert not os.path.exists(tanbaser.path)
    assert not tanbaser.opened

    """Done Test"""

def test_duror():
    """Test Duror methods"""

    duror = Duror()
    assert isinstance(duror, Duror)
    assert duror.name == "main"
    assert duror.temp == False
    assert isinstance(duror.env, lmdb.Environment)
    assert duror.path.endswith(os.path.join("hio", "db", "main"))
    assert duror.env.path() == duror.path
    assert os.path.exists(duror.path)
    assert duror.opened
    duror.close(clear=True)
    assert not os.path.exists(duror.path)
    assert not duror.opened

    # test not opened on init
    duror = Duror(reopen=False)
    assert isinstance(duror, Duror)
    assert duror.name == "main"
    assert duror.temp == False
    assert duror.opened == False
    assert duror.path == None
    assert duror.env == None

    duror.reopen()
    assert duror.opened
    assert isinstance(duror.env, lmdb.Environment)
    assert duror.path.endswith(os.path.join("hio", "db", "main"))
    assert duror.env.path() == duror.path
    assert os.path.exists(duror.path)
    duror.close(clear=True)
    assert not os.path.exists(duror.path)
    assert not duror.opened

    with openDuror() as duror:
        assert duror.temp == True
        #test Val methods put set get del cnt
        key = b'A'
        val = b'whatever'
        sdb = duror.env.open_db(key=b'beep.')

        assert duror.getVal(sdb, key) == None
        assert duror.remVal(sdb, key) == False
        assert duror.putVal(sdb, key, val) == True
        assert duror.putVal(sdb, key, val) == False
        assert duror.pinVal(sdb, key, val) == True
        assert duror.getVal(sdb, key) == val
        assert duror.cntVals(sdb) == 1
        assert duror.remVal(sdb, key) == True
        assert duror.getVal(sdb, key) == None
        assert duror.cntVals(sdb) == 0

        # Test getTopItemIter
        key = b"a.1"
        val = b"wow"
        assert duror.putVal(sdb, key, val) == True
        key = b"a.2"
        val = b"wee"
        assert duror.putVal(sdb, key, val) == True
        key = b"b.1"
        val = b"woo"
        assert duror.putVal(sdb, key, val) == True
        assert [(bytes(key), bytes(val)) for key, val
                     in duror.getTopItemIter(sdb=sdb)] == [(b'a.1', b'wow'),
                                                        (b'a.2', b'wee'),
                                                        (b'b.1', b'woo')]
        # Test delTopVals
        assert duror.remTopVals(sdb, top=b"a.")
        items = [ (key, bytes(val)) for key, val in duror.getTopItemIter(sdb=sdb )]
        assert items == [(b'b.1', b'woo')]

        assert duror.remTopVals(sdb)
        assert duror.cntVals(sdb) == 0


        # Test io and ioset methods
        """
        getIoValFirst, getIoValLast, getIoVals, getIoValsIter
        popIoVal
        remIoVals, cntIoVals
        getTopIoItemsIter

        addIoVal, putIoVals, pinIoVals

        addIoSetVal, putIoSetVals, pinIoSetVals, remIoSetVal
        """

        key0 = b'ABC_ZYX'
        key1 = b'DEF_WVU'
        key2 = b'GHI_TSR'
        key3 = b'AB_CDE'
        key4 = b'ABC_EFG'
        key5 = b'ABC_HIJ'

        vals0 = [b"z", b"m", b"x", b"a"]
        vals1 = [b"w", b"n", b"y", b"d"]
        vals2 = [b"p", b"o", b"h", b"f"]
        vals3 = [b"q", b"e"]
        vals4 = [b'p', b'm']
        vals5 = [b't', b'a']

        # Io
        sdb = duror.env.open_db(key=b'io.', dupsort=False)

        assert duror.getIoVals(sdb, key0) == oset()
        assert duror.getIoValFirst(sdb, key0) == None
        assert duror.getIoValLast(sdb, key0) == None
        assert duror.cntIoVals(sdb, key0) == 0
        assert duror.remIoVals(sdb, key0) == False

        assert duror.putIoVals(sdb, key0, vals0) == True
        assert duror.getIoVals(sdb, key0) == vals0  # preserved insertion order
        assert duror.cntIoVals(sdb, key0) == len(vals0) == 4
        assert duror.getIoValFirst(sdb, key0) == vals0[0]
        assert duror.getIoValLast(sdb, key0) == vals0[-1] == vals0[-1]

        assert duror.putIoVals(sdb, key5, vals0)
        assert duror.popIoVal(sdb, key5) == vals0[0]
        assert duror.popIoVal(sdb, key5) == vals0[1]
        assert duror.popIoVal(sdb, key5) == vals0[2]
        assert duror.popIoVal(sdb, key5) == vals0[3]
        assert duror.popIoVal(sdb, key5) == None
        assert duror.cntIoVals(sdb, key5) == 0

        # test no dedup
        assert duror.putIoVals(sdb, key0, vals=[b'a']) == True   # allows duplicate
        assert duror.getIoVals(sdb, key0) == vals0 + [b'a']  #  doubled b'a'
        assert duror.putIoVals(sdb, key0, vals=[b'f']) == True
        assert duror.getIoVals(sdb, key0) == [b'z', b'm', b'x', b'a', b'a', b'f']
        assert duror.addIoVal(sdb, key0, val=b'b') == True
        assert duror.addIoVal(sdb, key0, val=b'a') == True  # allows duplicate
        assert duror.getIoVals(sdb, key0) == [b'z', b'm', b'x', b'a', b'a', b'f', b'b', b'a']

        assert [val for val in duror.getIoValsIter(sdb, key0)] == [b'z', b'm', b'x', b'a', b'a', b'f', b'b', b'a']
        assert duror.remIoVals(sdb, key0) == True
        assert duror.getIoVals(sdb, key0) == []

        assert duror.putIoVals(sdb, key0, vals0) == True
        assert duror.getIoVals(sdb, key0) == [b'z', b'm', b'x', b'a']
        assert duror.putIoVals(sdb, key0, vals0) == True
        assert duror.remIoVals(sdb, key0) == True
        assert duror.getIoVals(sdb, key0) == []

        #change order
        assert duror.putIoVals(sdb, key0, vals0) == True
        assert duror.addIoVal(sdb, key0, b'w')
        assert duror.addIoVal(sdb, key0, b'e')
        assert duror.getIoVals(sdb, key0) == [b'z', b'm', b'x', b'a', b'w', b'e']

        assert duror.remIoVals(sdb, key0) == True
        assert duror.getIoVals(sdb, key0) == []

        assert duror.putIoVals(sdb, key0, vals0) == True
        assert duror.putIoVals(sdb, key1, vals1) == True
        assert duror.putIoVals(sdb, key2, vals2) == True
        assert duror.getIoVals(sdb, key0) == vals0
        assert duror.getIoVals(sdb, key1) == vals1
        assert duror.getIoVals(sdb, key2) == vals2

        assert duror.pinIoVals(sdb, key2, vals3)
        assert duror.getIoVals(sdb, key2) == vals3
        assert duror.cntVals(sdb) == 10  # whole database

        assert duror.remTopVals(sdb)  # whole database
        assert duror.cntVals(sdb) == 0  # whole databse

        # Test getTopIoItemIter
        # setup database
        assert duror.putIoVals(sdb, key0, vals0) == True
        assert duror.putIoVals(sdb, key1, vals1) == True
        assert duror.putIoVals(sdb, key2, vals2) == True
        assert duror.putIoVals(sdb, key3, vals3) == True
        assert duror.putIoVals(sdb, key4, vals4) == True
        assert duror.putIoVals(sdb, key5, vals5) == True
        assert duror.cntVals(sdb) == 18

        items = []
        for key, val in duror.getTopIoItemIter(sdb):
            items.append((key, bytes(val)))

        assert items == [(b'ABC_EFG', b'p'),
                        (b'ABC_EFG', b'm'),
                        (b'ABC_HIJ', b't'),
                        (b'ABC_HIJ', b'a'),
                        (b'ABC_ZYX', b'z'),
                        (b'ABC_ZYX', b'm'),
                        (b'ABC_ZYX', b'x'),
                        (b'ABC_ZYX', b'a'),
                        (b'AB_CDE', b'q'),
                        (b'AB_CDE', b'e'),
                        (b'DEF_WVU', b'w'),
                        (b'DEF_WVU', b'n'),
                        (b'DEF_WVU', b'y'),
                        (b'DEF_WVU', b'd'),
                        (b'GHI_TSR', b'p'),
                        (b'GHI_TSR', b'o'),
                        (b'GHI_TSR', b'h'),
                        (b'GHI_TSR', b'f')]


        items = []
        for key, val in duror.getTopIoItemIter(sdb, top=b'ABC_'):
            items.append((key, bytes(val)))

        assert items == [(b'ABC_EFG', b'p'),
                        (b'ABC_EFG', b'm'),
                        (b'ABC_HIJ', b't'),
                        (b'ABC_HIJ', b'a'),
                        (b'ABC_ZYX', b'z'),
                        (b'ABC_ZYX', b'm'),
                        (b'ABC_ZYX', b'x'),
                        (b'ABC_ZYX', b'a')]

        items = []
        for key, val in duror.getTopIoItemIter(sdb, top=b'AB'):
            items.append((key, bytes(val)))

        assert items == [(b'ABC_EFG', b'p'),
                        (b'ABC_EFG', b'm'),
                        (b'ABC_HIJ', b't'),
                        (b'ABC_HIJ', b'a'),
                        (b'ABC_ZYX', b'z'),
                        (b'ABC_ZYX', b'm'),
                        (b'ABC_ZYX', b'x'),
                        (b'ABC_ZYX', b'a'),
                        (b'AB_CDE', b'q'),
                        (b'AB_CDE', b'e')]

        # IoSet
        sdb = duror.env.open_db(key=b'ioset.', dupsort=False)

        assert duror.getIoVals(sdb, key0) == oset()
        assert duror.getIoValFirst(sdb, key0) == None
        assert duror.getIoValLast(sdb, key0) == None
        assert duror.cntIoVals(sdb, key0) == 0
        assert duror.remIoVals(sdb, key0) == False

        assert duror.putIoSetVals(sdb, key0, vals0) == True
        assert duror.getIoVals(sdb, key0) == vals0  # preserved insertion order
        assert duror.cntIoVals(sdb, key0) == len(vals0) == 4
        assert duror.getIoValFirst(sdb, key0) == vals0[0]
        assert duror.getIoValLast(sdb, key0) == vals0[-1] == vals0[-1]

        assert duror.putIoSetVals(sdb, key5, vals0)
        assert duror.popIoVal(sdb, key5) == vals0[0]
        assert duror.popIoVal(sdb, key5) == vals0[1]
        assert duror.popIoVal(sdb, key5) == vals0[2]
        assert duror.popIoVal(sdb, key5) == vals0[3]
        assert duror.popIoVal(sdb, key5) == None
        assert duror.cntIoVals(sdb, key5) == 0

        # Test dedup
        assert duror.putIoSetVals(sdb, key0, vals=[b'a']) == False  # disallows duplicate
        assert duror.getIoVals(sdb, key0) == vals0  #  no change
        assert duror.putIoSetVals(sdb, key0, vals=[b'f']) == True
        assert duror.getIoVals(sdb, key0) == [b"z", b"m", b"x", b"a", b"f"]
        assert duror.addIoSetVal(sdb, key0, val=b'b') == True
        assert duror.addIoSetVal(sdb, key0, val=b'a') == False  # disallows duplicate
        assert duror.getIoVals(sdb, key0) == [b"z", b"m", b"x", b"a", b"f", b"b"]

        assert [val for val in duror.getIoValsIter(sdb, key0)] == [b"z", b"m", b"x", b"a", b"f", b"b"]
        assert duror.remIoVals(sdb, key0) == True
        assert duror.getIoVals(sdb, key0) == []

        assert duror.putIoSetVals(sdb, key0, vals0) == True
        for val in vals0:
            assert duror.remIoSetVal(sdb, key0, val)
        assert duror.getIoVals(sdb, key0) == oset()
        assert duror.putIoSetVals(sdb, key0, vals0) == True
        for val in sorted(vals0):  # test deletion out of order
            assert duror.remIoSetVal(sdb, key0, val)
        assert duror.getIoVals(sdb, key0) == []

        #delete and add in odd order
        assert duror.putIoSetVals(sdb, key0, vals0) == True
        assert duror.remIoSetVal(sdb, key0, vals0[2])
        assert duror.addIoSetVal(sdb, key0, b'w')
        assert duror.remIoSetVal(sdb, key0, vals0[0])
        assert duror.addIoSetVal(sdb, key0, b'e')
        assert duror.getIoVals(sdb, key0) == [b'm', b'a', b'w', b'e']

        assert duror.remIoVals(sdb, key0) == True
        assert duror.getIoVals(sdb, key0) == oset()

        assert duror.putIoSetVals(sdb, key0, vals0) == True
        assert duror.putIoSetVals(sdb, key1, vals1) == True
        assert duror.putIoSetVals(sdb, key2, vals2) == True
        assert duror.getIoVals(sdb, key0) == vals0
        assert duror.getIoVals(sdb, key1) == vals1
        assert duror.getIoVals(sdb, key2) == vals2

        assert duror.pinIoSetVals(sdb, key2, vals3)
        assert duror.getIoVals(sdb, key2) == vals3
        assert duror.cntVals(sdb) == 10

        assert duror.remTopVals(sdb)
        assert duror.cntVals(sdb) == 0

        # Test setTopIoSetItemIter(self, sdb, pre)
        assert duror.putIoSetVals(sdb, key0, vals0) == True
        assert duror.putIoSetVals(sdb, key1, vals1) == True
        assert duror.putIoSetVals(sdb, key2, vals2) == True
        assert duror.putIoSetVals(sdb, key3, vals3) == True
        assert duror.putIoSetVals(sdb, key4, vals4) == True
        assert duror.putIoSetVals(sdb, key5, vals5) == True
        assert duror.cntVals(sdb) == 18

        items = []
        for key, val in duror.getTopIoItemIter(sdb):
            items.append((key, bytes(val)))

        assert items == [(b'ABC_EFG', b'p'),
                        (b'ABC_EFG', b'm'),
                        (b'ABC_HIJ', b't'),
                        (b'ABC_HIJ', b'a'),
                        (b'ABC_ZYX', b'z'),
                        (b'ABC_ZYX', b'm'),
                        (b'ABC_ZYX', b'x'),
                        (b'ABC_ZYX', b'a'),
                        (b'AB_CDE', b'q'),
                        (b'AB_CDE', b'e'),
                        (b'DEF_WVU', b'w'),
                        (b'DEF_WVU', b'n'),
                        (b'DEF_WVU', b'y'),
                        (b'DEF_WVU', b'd'),
                        (b'GHI_TSR', b'p'),
                        (b'GHI_TSR', b'o'),
                        (b'GHI_TSR', b'h'),
                        (b'GHI_TSR', b'f')]


        items = []
        for key, val in duror.getTopIoItemIter(sdb, top=b'ABC_'):
            items.append((key, bytes(val)))

        assert items == [(b'ABC_EFG', b'p'),
                        (b'ABC_EFG', b'm'),
                        (b'ABC_HIJ', b't'),
                        (b'ABC_HIJ', b'a'),
                        (b'ABC_ZYX', b'z'),
                        (b'ABC_ZYX', b'm'),
                        (b'ABC_ZYX', b'x'),
                        (b'ABC_ZYX', b'a')]

        items = []
        for key, val in duror.getTopIoItemIter(sdb, top=b'AB'):
            items.append((key, bytes(val)))

        assert items == [(b'ABC_EFG', b'p'),
                        (b'ABC_EFG', b'm'),
                        (b'ABC_HIJ', b't'),
                        (b'ABC_HIJ', b'a'),
                        (b'ABC_ZYX', b'z'),
                        (b'ABC_ZYX', b'm'),
                        (b'ABC_ZYX', b'x'),
                        (b'ABC_ZYX', b'a'),
                        (b'AB_CDE', b'q'),
                        (b'AB_CDE', b'e')]


    assert not os.path.exists(duror.path)

    """Done Test"""


def test_suberbase():
    """Test SuberBase Duror sub database class"""
    with openDuror() as duror:
        assert isinstance(duror, Duror)
        assert duror.name == "test"
        assert duror.opened

        assert SuberBase.Sep == '_'

        suber = SuberBase(db=duror, subkey='bags.')
        assert isinstance(suber, SuberBase)
        assert not suber.sdb.flags()["dupsort"]
        assert suber.sep == "_"

        keys = ('key', 'top')
        key = suber._tokey(keys)
        assert key == b'key_top'
        assert suber._tokeys(key) == keys

        keys = 'bottom'
        key = suber._tokey(keys)
        assert key == b'bottom' == keys.encode()

        keys = b'bottom'
        key = suber._tokey(keys)
        assert key == b'bottom' == keys

    assert not os.path.exists(duror.path)
    assert not duror.opened
    """Done Test"""



def test_suber():
    """Test Suber Duror sub database class"""

    with openDuror() as duror:
        assert isinstance(duror, Duror)
        assert duror.name == "test"
        assert duror.opened

        assert Suber.Sep == '_'

        suber = Suber(db=duror, subkey='bags.')
        assert isinstance(suber, Suber)
        assert not suber.sdb.flags()["dupsort"]
        assert suber.sep == "_"

        keys = ('key', 'top')
        key = suber._tokey(keys)
        assert key == b'key_top'
        assert suber._tokeys(key) == keys


        sue = "Hello sailer!"

        keys = ("test_key", "0001")
        suber.put(keys=keys, val=sue)
        actual = suber.get(keys=keys)
        assert actual == sue

        suber.rem(keys)
        actual = suber.get(keys=keys)
        assert actual is None

        suber.put(keys=keys, val=sue)
        actual = suber.get(keys=keys)
        assert actual == sue

        kip = "Hey gorgeous!"
        result = suber.put(keys=keys, val=kip)
        assert not result
        actual = suber.get(keys=keys)
        assert actual == sue

        result = suber.pin(keys=keys, val=kip)
        assert result
        actual = suber.get(keys=keys)
        assert actual == kip

        suber.rem(keys)
        actual = suber.get(keys=keys)
        assert actual is None

        suber.put(keys=keys, val=sue)
        actual = suber.get(keys=keys)
        assert actual == sue

        # test with keys as tuple of bytes
        keys = (b"test_key", b"0001")
        suber.rem(keys)
        actual = suber.get(keys=keys)
        assert actual is None

        suber.put(keys=keys, val=sue)
        actual = suber.get(keys=keys)
        assert actual == sue

        # test with keys as mixed tuple of bytes
        keys = (b"test_key", "0001")
        suber.rem(keys)
        actual = suber.get(keys=keys)
        assert actual is None

        suber.put(keys=keys, val=sue)
        actual = suber.get(keys=keys)
        assert actual == sue


        # test with keys as string not tuple
        keys = "keystr"

        bob = "Shove off!"

        suber.put(keys=keys, val=bob)
        actual = suber.get(keys=keys)
        assert actual == bob

        suber.rem(keys)

        actual = suber.get(keys=keys)
        assert actual is None


        liz =  "May life is insane."
        keys = ("test_key", "0002")

        suber.put(keys=keys, val=liz)
        actual = suber.get(("not_found", "0002"))
        assert actual is None

        w = "Blue dog"
        x = "Green tree"
        y = "Red apple"
        z = "White snow"

        suber = Suber(db=duror, subkey='pugs.')
        assert isinstance(suber, Suber)

        suber.put(keys=("a","1"), val=w)
        suber.put(keys=("a","2"), val=x)
        suber.put(keys=("a","3"), val=y)
        suber.put(keys=("a","4"), val=z)

        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('a', '1'), w),
                        (('a', '2'), x),
                        (('a', '3'), y),
                        (('a', '4'), z)]

        suber.put(keys=("b","1"), val=w)
        suber.put(keys=("b","2"), val=x)
        suber.put(keys=("bc","3"), val=y)
        suber.put(keys=("ac","4"), val=z)

        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('a', '1'), 'Blue dog'),
                        (('a', '2'), 'Green tree'),
                        (('a', '3'), 'Red apple'),
                        (('a', '4'), 'White snow'),
                        (('ac', '4'), 'White snow'),
                        (('b', '1'), 'Blue dog'),
                        (('b', '2'), 'Green tree'),
                        (('bc', '3'), 'Red apple')]


        # test with top keys for partial tree
        topkeys = ("b","")  # last element empty to force trailing separator
        items = [(keys, val) for keys, val in suber.getItemIter(keys=topkeys)]
        assert items == [(('b', '1'), w),
                         (('b', '2'), x)]

        topkeys = ("a","")  # last element empty to force trailing separator
        items = [(keys, val) for keys, val in suber.getItemIter(keys=topkeys)]
        assert items == [(('a', '1'), w),
                        (('a', '2'), x),
                        (('a', '3'), y),
                        (('a', '4'), z)]

        # test with top parameter
        keys = ("b", )  # last element empty to force trailing separator
        items = [(keys, val) for keys, val in suber.getItemIter(keys=keys, topive=True)]
        assert items == [(('b', '1'), w),
                         (('b', '2'), x)]

        keys = ("a", )  # last element empty to force trailing separator
        items = [(keys, val) for keys, val in suber.getItemIter(keys=keys, topive=True)]
        assert items == [(('a', '1'), w),
                        (('a', '2'), x),
                        (('a', '3'), y),
                        (('a', '4'), z)]

        # Test trim
        assert suber.trim(keys=("b", ""))
        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('a', '1'), 'Blue dog'),
                        (('a', '2'), 'Green tree'),
                        (('a', '3'), 'Red apple'),
                        (('a', '4'), 'White snow'),
                        (('ac', '4'), 'White snow'),
                        (('bc', '3'), 'Red apple')]

        assert suber.trim(keys=("a", ""))
        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('ac', '4'), 'White snow'), (('bc', '3'), 'Red apple')]

        # Test trim with top parameters
        suber.put(keys=("a","1"), val=w)
        suber.put(keys=("a","2"), val=x)
        suber.put(keys=("a","3"), val=y)
        suber.put(keys=("a","4"), val=z)
        suber.put(keys=("b","1"), val=w)
        suber.put(keys=("b","2"), val=x)

        assert suber.trim(keys=("b",), topive=True)
        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('a', '1'), 'Blue dog'),
                        (('a', '2'), 'Green tree'),
                        (('a', '3'), 'Red apple'),
                        (('a', '4'), 'White snow'),
                        (('ac', '4'), 'White snow'),
                        (('bc', '3'), 'Red apple')]

        assert suber.trim(keys=("a",), topive=True)
        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('ac', '4'), 'White snow'),
                         (('bc', '3'), 'Red apple')]

        assert suber.trim()
        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == []

        assert not suber.trim()

    assert not os.path.exists(duror.path)
    assert not duror.opened
    """Done Test"""



def test_io_suber():
    """Test IoSuber Duror sub database class"""

    with openDuror() as duror:
        assert isinstance(duror, Duror)
        assert duror.name == "test"
        assert duror.opened

        assert IoSuber.Sep == '_'
        assert IoSuber.IonSep == '.'

        suber = IoSuber(db=duror, subkey='bags.')
        assert isinstance(suber, IoSuber)
        assert not suber.sdb.flags()["dupsort"]
        assert suber.sep == '_'
        assert suber.ionsep == '.'

        sue = "Hello sailer!"
        sal = "Not my type."

        keys0 = ("testkey", "0001")
        keys1 = ("testkey", "0002")

        assert suber.put(keys=keys0, vals=[sal, sue])
        assert suber.get(keys=keys0) == [sal, sue]  # insertion order not lexicographic
        assert suber.cnt(keys0) == 2
        assert suber.getFirst(keys=keys0) == sal
        assert suber.getLast(keys=keys0) == sue
        assert suber.pop(keys=keys0) == sal
        assert suber.pop(keys=keys0) == sue
        assert suber.pop(keys=keys0) == None
        assert suber.cnt(keys0) == 0

        assert suber.put(keys=keys0, vals=[sal, sue])
        assert suber.get(keys=keys0) == [sal, sue]  # insertion order not lexicographic
        assert suber.rem(keys0)
        assert suber.get(keys=keys0) == []
        assert suber.cnt(keys0) == 0

        assert suber.put(keys=keys0, vals=[sue, sal])
        actuals = suber.get(keys=keys0)
        assert actuals == [sue, sal]  # insertion order
        actual = suber.getLast(keys=keys0)
        assert actual == sal

        sam = "A real charmer!"
        result = suber.add(keys=keys0, val=sam)
        assert result
        actuals = suber.get(keys=keys0)
        assert actuals == [sue, sal, sam]   # insertion order

        zoe = "See ya later."
        zia = "Hey gorgeous!"

        result = suber.pin(keys=keys0, vals=[zoe, zia])
        assert result
        actuals = suber.get(keys=keys0)
        assert actuals == [zoe, zia]  # insertion order

        assert suber.put(keys=keys1, vals=[sal, sue, sam])
        actuals = suber.get(keys=keys1)
        assert actuals == [sal, sue, sam]

        for i, val in enumerate(suber.getIter(keys=keys1)):
            assert val == actuals[i]

        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('testkey', '0001'), 'See ya later.'),
                        (('testkey', '0001'), 'Hey gorgeous!'),
                        (('testkey', '0002'), 'Not my type.'),
                        (('testkey', '0002'), 'Hello sailer!'),
                        (('testkey', '0002'), 'A real charmer!')]

        items = list(suber.getFullItemIter())
        assert items ==  [(('testkey', '0001.00000000000000000000000000000000'), 'See ya later.'),
                        (('testkey', '0001.00000000000000000000000000000001'), 'Hey gorgeous!'),
                        (('testkey', '0002.00000000000000000000000000000000'), 'Not my type.'),
                        (('testkey', '0002.00000000000000000000000000000001'), 'Hello sailer!'),
                        (('testkey', '0002.00000000000000000000000000000002'), 'A real charmer!')]



        items = [(keys, val) for keys,  val in  suber.getItemIter(keys=keys0)]
        assert items == [(('testkey', '0001'), 'See ya later.'),
                         (('testkey', '0001'), 'Hey gorgeous!')]

        items = [(keys, val) for keys,  val in suber.getItemIter(keys=keys1)]
        assert items == [(('testkey', '0002'), 'Not my type.'),
                        (('testkey', '0002'), 'Hello sailer!'),
                        (('testkey', '0002'), 'A real charmer!')]


        # Test with top keys
        assert suber.put(keys=("test", "pop"), vals=[sal, sue, sam])
        topkeys = ("test", "")
        items = [(keys, val) for keys, val in suber.getItemIter(keys=topkeys)]
        assert items == [(('test', 'pop'), 'Not my type.'),
                         (('test', 'pop'), 'Hello sailer!'),
                         (('test', 'pop'), 'A real charmer!')]

        # test with top parameter
        keys = ("test", )
        items = [(keys, val) for keys, val in suber.getItemIter(keys=keys, topive=True)]
        assert items == [(('test', 'pop'), 'Not my type.'),
                         (('test', 'pop'), 'Hello sailer!'),
                         (('test', 'pop'), 'A real charmer!')]

        # IoItems
        items = list(suber.getFullItemIter(keys=topkeys))
        assert items == [(('test', 'pop.00000000000000000000000000000000'), 'Not my type.'),
                    (('test', 'pop.00000000000000000000000000000001'), 'Hello sailer!'),
                    (('test', 'pop.00000000000000000000000000000002'), 'A real charmer!')]


        assert suber.trim(keys=("test", ""))
        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('testkey', '0001'), 'See ya later.'),
                        (('testkey', '0001'), 'Hey gorgeous!'),
                        (('testkey', '0002'), 'Not my type.'),
                        (('testkey', '0002'), 'Hello sailer!'),
                        (('testkey', '0002'), 'A real charmer!')]

        # test with keys as string not tuple
        keys2 = "keystr"
        bob = "Shove off!"
        assert suber.put(keys=keys2, vals=[bob])
        actuals = suber.get(keys=keys2)
        assert actuals == [bob]
        assert suber.cnt(keys2) == 1
        assert suber.rem(keys2)
        actuals = suber.get(keys=keys2)
        assert actuals == []
        assert suber.cnt(keys2) == 0

        assert suber.put(keys=keys2, vals=[bob])
        actuals = suber.get(keys=keys2)
        assert actuals == [bob]

        bil = "Go away."
        assert suber.pin(keys=keys2, vals=[bil])
        actuals = suber.get(keys=keys2)
        assert actuals == [bil]

        assert suber.add(keys=keys2, val=bob)
        actuals = suber.get(keys=keys2)
        assert actuals == [bil, bob]

        # Test trim and append
        assert suber.trim()  # default trims whole database
        assert suber.put(keys=keys1, vals=[bob, bil])
        assert suber.get(keys=keys1) == [bob, bil]

    assert not os.path.exists(duror.path)
    assert not duror.opened
    """Done Test"""



def test_ioset_suber():
    """Test IoSetSuber Duror sub database class


    """
    with openDuror() as duror:
        assert isinstance(duror, Duror)
        assert duror.name == "test"
        assert duror.opened

        assert IoSetSuber.Sep == '_'
        assert IoSetSuber.IonSep == '.'

        suber = IoSetSuber(db=duror, subkey='bags.')
        assert isinstance(suber, IoSetSuber)
        assert not suber.sdb.flags()["dupsort"]
        assert suber.sep == '_'
        assert suber.ionsep == '.'

        sue = "Hello sailer!"
        sal = "Not my type."
        sam = "A real charmer!"
        zoe = "See ya later."
        zia = "Hey gorgeous!"

        keys0 = ("testkey", "0001")
        keys1 = ("testkey", "0002")

        assert suber.put(keys=keys0, vals=[sal, sue])
        assert suber.get(keys=keys0) == [sal, sue]  # insertion order not lexicographic
        assert suber.cnt(keys0) == 2
        assert suber.getFirst(keys=keys0) == sal
        assert suber.getLast(keys=keys0) == sue
        assert suber.pop(keys=keys0) == sal
        assert suber.pop(keys=keys0) == sue
        assert suber.pop(keys=keys0) == None
        assert suber.cnt(keys0) == 0

        assert suber.put(keys=keys0, vals=[sal, sue])
        assert suber.get(keys=keys0) == [sal, sue]  # insertion order not lexicographic
        assert suber.rem(keys0)
        assert suber.get(keys=keys0) == []
        assert suber.cnt(keys0) == 0

        # Test Dedup
        assert suber.put(keys=keys0, vals=[sal, sue, sam])
        assert suber.get(keys=keys0) == [sal, sue, sam]  # insertion order not lexicographic
        assert not suber.add(keys=keys0, val=sue)  # dup disallowed
        assert suber.get(keys=keys0) == [sal, sue, sam]
        assert not suber.put(keys=keys0, vals=[sal, sam])  # dup disallowed
        assert suber.get(keys=keys0) == [sal, sue, sam]
        assert suber.put(keys=keys0, vals=[zoe, zia, sal, sam])  # at least one not dup
        assert suber.get(keys=keys0) == [sal, sue, sam, zoe, zia]
        assert suber.rem(keys0)
        assert suber.get(keys=keys0) == []
        assert suber.cnt(keys0) == 0

        assert suber.put(keys=keys0, vals=[sue, sal])
        actuals = suber.get(keys=keys0)
        assert actuals == [sue, sal]  # insertion order
        actual = suber.getLast(keys=keys0)
        assert actual == sal

        result = suber.add(keys=keys0, val=sam)
        assert result
        actuals = suber.get(keys=keys0)
        assert actuals == [sue, sal, sam]   # insertion order

        result = suber.pin(keys=keys0, vals=[zoe, zia])
        assert result
        actuals = suber.get(keys=keys0)
        assert actuals == [zoe, zia]  # insertion order

        assert suber.put(keys=keys1, vals=[sal, sue, sam])
        actuals = suber.get(keys=keys1)
        assert actuals == [sal, sue, sam]

        for i, val in enumerate(suber.getIter(keys=keys1)):
            assert val == actuals[i]

        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('testkey', '0001'), 'See ya later.'),
                        (('testkey', '0001'), 'Hey gorgeous!'),
                        (('testkey', '0002'), 'Not my type.'),
                        (('testkey', '0002'), 'Hello sailer!'),
                        (('testkey', '0002'), 'A real charmer!')]

        items = list(suber.getFullItemIter())
        assert items ==  [(('testkey', '0001.00000000000000000000000000000000'), 'See ya later.'),
                        (('testkey', '0001.00000000000000000000000000000001'), 'Hey gorgeous!'),
                        (('testkey', '0002.00000000000000000000000000000000'), 'Not my type.'),
                        (('testkey', '0002.00000000000000000000000000000001'), 'Hello sailer!'),
                        (('testkey', '0002.00000000000000000000000000000002'), 'A real charmer!')]



        items = [(keys, val) for keys,  val in  suber.getItemIter(keys=keys0)]
        assert items == [(('testkey', '0001'), 'See ya later.'),
                         (('testkey', '0001'), 'Hey gorgeous!')]

        items = [(keys, val) for keys,  val in suber.getItemIter(keys=keys1)]
        assert items == [(('testkey', '0002'), 'Not my type.'),
                        (('testkey', '0002'), 'Hello sailer!'),
                        (('testkey', '0002'), 'A real charmer!')]


        # Test with top keys
        assert suber.put(keys=("test", "pop"), vals=[sal, sue, sam])
        topkeys = ("test", "")
        items = [(keys, val) for keys, val in suber.getItemIter(keys=topkeys)]
        assert items == [(('test', 'pop'), 'Not my type.'),
                         (('test', 'pop'), 'Hello sailer!'),
                         (('test', 'pop'), 'A real charmer!')]

        # test with top parameter
        keys = ("test", )
        items = [(keys, val) for keys, val in suber.getItemIter(keys=keys, topive=True)]
        assert items == [(('test', 'pop'), 'Not my type.'),
                         (('test', 'pop'), 'Hello sailer!'),
                         (('test', 'pop'), 'A real charmer!')]

        # IoItems
        items = list(suber.getFullItemIter(keys=topkeys))
        assert items == [(('test', 'pop.00000000000000000000000000000000'), 'Not my type.'),
                    (('test', 'pop.00000000000000000000000000000001'), 'Hello sailer!'),
                    (('test', 'pop.00000000000000000000000000000002'), 'A real charmer!')]

        # test remove with a specific val
        assert suber.rem(keys=("testkey", "0002"), val=sue)
        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('test', 'pop'), 'Not my type.'),
                        (('test', 'pop'), 'Hello sailer!'),
                        (('test', 'pop'), 'A real charmer!'),
                        (('testkey', '0001'), 'See ya later.'),
                        (('testkey', '0001'), 'Hey gorgeous!'),
                        (('testkey', '0002'), 'Not my type.'),
                        (('testkey', '0002'), 'A real charmer!')]

        assert suber.trim(keys=("test", ""))
        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('testkey', '0001'), 'See ya later.'),
                        (('testkey', '0001'), 'Hey gorgeous!'),
                        (('testkey', '0002'), 'Not my type.'),
                        (('testkey', '0002'), 'A real charmer!')]



        # test with keys as string not tuple
        keys2 = "keystr"
        bob = "Shove off!"
        assert suber.put(keys=keys2, vals=[bob])
        actuals = suber.get(keys=keys2)
        assert actuals == [bob]
        assert suber.cnt(keys2) == 1
        assert suber.rem(keys2)
        actuals = suber.get(keys=keys2)
        assert actuals == []
        assert suber.cnt(keys2) == 0

        assert suber.put(keys=keys2, vals=[bob])
        actuals = suber.get(keys=keys2)
        assert actuals == [bob]

        bil = "Go away."
        assert suber.pin(keys=keys2, vals=[bil])
        actuals = suber.get(keys=keys2)
        assert actuals == [bil]

        assert suber.add(keys=keys2, val=bob)
        actuals = suber.get(keys=keys2)
        assert actuals == [bil, bob]

        # Test trim and append
        assert suber.trim()  # default trims whole database
        assert suber.put(keys=keys1, vals=[bob, bil])
        assert suber.get(keys=keys1) == [bob, bil]

    assert not os.path.exists(duror.path)
    assert not duror.opened
    """Done Test"""



def test_dom_suber_base():
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


def test_dom_suber():
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


def test_dom_io_suber():
    """Test DomIoSuber class"""

    with openDuror() as duror:
        assert isinstance(duror, Duror)
        assert duror.name == "test"
        assert duror.opened

        assert DomIoSuber.Sep == '_'
        assert DomIoSuber.ProSep == '\n'
        assert DomIoSuber.IonSep == '.'

        suber = DomIoSuber(db=duror)
        assert isinstance(suber, DomIoSuber)
        assert not suber.sdb.flags()["dupsort"]
        assert suber.sep == "_"
        assert suber.prosep == '\n'
        assert suber.ionsep == '.'

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

        # Test Io methods

        # Test methods to save to lmdb
        val0 = Bag(value=0)
        val1 = Bag(value=1)
        val2 = Bag(value=2)
        val3 = Bag(value=3)
        val4 = Bag(value=4)
        val5 = Bag(value=5)

        keys0 = ("testkey", "00")
        keys1 = ("testkey", "01")
        keys2 = ("testkey", "02")
        keys3 = ("testkey", "03")

        assert suber.put(keys=keys0, vals=[val0, val1])
        assert suber.get(keys=keys0) == [val0, val1]  # insertion order not lexicographic
        assert suber.cnt(keys0) == 2
        assert suber.getFirst(keys=keys0) == val0  # test getFirst
        assert suber.getLast(keys=keys0) == val1  # test getFirst
        assert suber.pop(keys=keys0) == val0  # test pop
        assert suber.pop(keys=keys0) == val1  # test pop
        assert suber.pop(keys=keys0) == None  # test pop
        assert suber.cnt(keys0) == 0

        assert suber.put(keys=keys0, vals=[val0, val1])
        assert suber.get(keys=keys0) == [val0, val1]  # insertion order not lexicographic
        assert suber.rem(keys0)
        assert suber.get(keys=keys0) == []
        assert suber.cnt(keys0) == 0

        # Test Dedup
        assert suber.put(keys=keys0, vals=[val0, val1, val2])
        assert suber.get(keys=keys0) == [val0, val1, val2]  # insertion order not lexicographic
        assert suber.add(keys=keys0, val=val1)  # dup allowed
        assert suber.get(keys=keys0) == [val0, val1, val2, val1]
        assert suber.put(keys=keys0, vals=[val0, val2])  # dup allowed
        assert suber.get(keys=keys0) == [val0, val1, val2, val1, val0, val2]
        assert suber.put(keys=keys0, vals=[val3, val4, val0, val2])
        assert suber.get(keys=keys0) == [val0, val1, val2, val1, val0, val2, val3, val4, val0, val2]
        assert suber.rem(keys0)
        assert suber.get(keys=keys0) == []
        assert suber.cnt(keys0) == 0

        assert suber.put(keys=keys0, vals=[val1, val0])  # change order
        actuals = suber.get(keys=keys0)
        assert actuals == [val1, val0]  # insertion order
        actual = suber.getLast(keys=keys0)  # test getLast
        assert actual == val0

        result = suber.add(keys=keys0, val=val2)
        assert result
        actuals = suber.get(keys=keys0)
        assert actuals == [val1, val0, val2]   # insertion order

        # test pin
        result = suber.pin(keys=keys0, vals=[val3, val4])
        assert result
        actuals = suber.get(keys=keys0)
        assert actuals == [val3, val4]  # insertion order

        assert suber.put(keys=keys1, vals=[val0, val1, val2])
        actuals = suber.get(keys=keys1)
        assert actuals == [val0, val1, val2]

        for i, val in enumerate(suber.getIter(keys=keys1)):
            assert val == actuals[i]

        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('testkey', '00'), val3),
                        (('testkey', '00'), val4),
                        (('testkey', '01'), val0),
                        (('testkey', '01'), val1),
                        (('testkey', '01'), val2)]

        items = list(suber.getFullItemIter())
        assert items ==  [(('testkey', '00.00000000000000000000000000000000'), val3),
                        (('testkey', '00.00000000000000000000000000000001'), val4),
                        (('testkey', '01.00000000000000000000000000000000'), val0),
                        (('testkey', '01.00000000000000000000000000000001'), val1),
                        (('testkey', '01.00000000000000000000000000000002'), val2)]

        items = [(keys, val) for keys,  val in  suber.getItemIter(keys=keys0)]
        assert items == [(('testkey', '00'), val3),
                         (('testkey', '00'), val4)]

        items = [(keys, val) for keys,  val in suber.getItemIter(keys=keys1)]
        assert items == [(('testkey', '01'), val0),
                         (('testkey', '01'), val1),
                         (('testkey', '01'), val2)]


        # Test with top keys
        assert suber.put(keys=("test", "pop"), vals=[val0, val1, val2])
        topkeys = ("test", "")
        items = [(keys, val) for keys, val in suber.getItemIter(keys=topkeys)]
        assert items == [(('test', 'pop'), val0),
                        (('test', 'pop'), val1),
                        (('test', 'pop'), val2)]

        # test with topive parameter
        keys = ("test", )
        items = [(keys, val) for keys, val in suber.getItemIter(keys=keys, topive=True)]
        assert items == [(('test', 'pop'), val0),
                        (('test', 'pop'), val1),
                        (('test', 'pop'), val2)]

        # IoItems
        items = list(suber.getFullItemIter(keys=topkeys))
        assert items == [(('test', 'pop.00000000000000000000000000000000'), val0),
                        (('test', 'pop.00000000000000000000000000000001'), val1),
                        (('test', 'pop.00000000000000000000000000000002'), val2)]


        assert suber.trim(keys=("test", ""))
        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('testkey', '00'), val3),
                        (('testkey', '00'), val4),
                        (('testkey', '01'), val0),
                        (('testkey', '01'), val1),
                        (('testkey', '01'), val2)]

        # test with keys as string not tuple
        keys4 = "keystr"

        assert suber.put(keys=keys4, vals=[val4])
        actuals = suber.get(keys=keys4)
        assert actuals == [val4]
        assert suber.cnt(keys4) == 1
        assert suber.rem(keys4)
        actuals = suber.get(keys=keys4)
        assert actuals == []
        assert suber.cnt(keys4) == 0

        assert suber.put(keys=keys4, vals=[val4])
        actuals = suber.get(keys=keys4)
        assert actuals == [val4]

        assert suber.pin(keys=keys4, vals=[val5])
        actuals = suber.get(keys=keys4)
        assert actuals == [val5]

        assert suber.add(keys=keys4, val=val4)
        actuals = suber.get(keys=keys4)
        assert actuals == [val5, val4]

        # Test trim and append
        assert suber.trim()  # default trims whole database
        assert suber.put(keys=keys1, vals=[val4, val5])
        assert suber.get(keys=keys1) == [val4, val5]



    assert not os.path.exists(duror.path)
    assert not duror.opened

    """Done Test"""


def test_dom_ioset_suber():
    """Test DomIoSetSuber class"""
    with openDuror() as duror:
        assert isinstance(duror, Duror)
        assert duror.name == "test"
        assert duror.opened

        assert DomIoSetSuber.Sep == '_'
        assert DomIoSetSuber.ProSep == '\n'
        assert DomIoSetSuber.IonSep == '.'

        suber = DomIoSetSuber(db=duror)
        assert isinstance(suber, DomIoSetSuber)
        assert not suber.sdb.flags()["dupsort"]
        assert suber.sep == "_"
        assert suber.prosep == '\n'
        assert suber.ionsep == '.'

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

        # Test IoSet methods

        # Test methods to save to lmdb
        val0 = Bag(value=0)
        val1 = Bag(value=1)
        val2 = Bag(value=2)
        val3 = Bag(value=3)
        val4 = Bag(value=4)
        val5 = Bag(value=5)

        keys0 = ("testkey", "00")
        keys1 = ("testkey", "01")
        keys2 = ("testkey", "02")
        keys3 = ("testkey", "03")

        assert suber.put(keys=keys0, vals=[val0, val1])
        assert suber.get(keys=keys0) == [val0, val1]  # insertion order not lexicographic
        assert suber.cnt(keys0) == 2
        assert suber.getFirst(keys=keys0) == val0  # test getFirst
        assert suber.getLast(keys=keys0) == val1  # test getFirst
        assert suber.pop(keys=keys0) == val0  # test pop
        assert suber.pop(keys=keys0) == val1  # test pop
        assert suber.pop(keys=keys0) == None  # test pop
        assert suber.cnt(keys0) == 0

        assert suber.put(keys=keys0, vals=[val0, val1])
        assert suber.get(keys=keys0) == [val0, val1]  # insertion order not lexicographic
        assert suber.rem(keys0)
        assert suber.get(keys=keys0) == []
        assert suber.cnt(keys0) == 0

        # Test Dedup
        assert suber.put(keys=keys0, vals=[val0, val1, val2])
        assert suber.get(keys=keys0) == [val0, val1, val2]  # insertion order not lexicographic
        assert not suber.add(keys=keys0, val=val1)  # dup disallowed
        assert suber.get(keys=keys0) == [val0, val1, val2]
        assert not suber.put(keys=keys0, vals=[val0, val2])  # dup disallowed
        assert suber.get(keys=keys0) == [val0, val1, val2]
        assert suber.put(keys=keys0, vals=[val3, val4, val0, val2])  # at least one not dup
        assert suber.get(keys=keys0) == [val0, val1, val2, val3, val4]
        assert suber.rem(keys0)
        assert suber.get(keys=keys0) == []
        assert suber.cnt(keys0) == 0

        assert suber.put(keys=keys0, vals=[val1, val0])  # change order
        actuals = suber.get(keys=keys0)
        assert actuals == [val1, val0]  # insertion order
        actual = suber.getLast(keys=keys0)  # test getLast
        assert actual == val0

        result = suber.add(keys=keys0, val=val2)
        assert result
        actuals = suber.get(keys=keys0)
        assert actuals == [val1, val0, val2]   # insertion order

        # test pin
        result = suber.pin(keys=keys0, vals=[val3, val4])
        assert result
        actuals = suber.get(keys=keys0)
        assert actuals == [val3, val4]  # insertion order

        assert suber.put(keys=keys1, vals=[val0, val1, val2])
        actuals = suber.get(keys=keys1)
        assert actuals == [val0, val1, val2]

        for i, val in enumerate(suber.getIter(keys=keys1)):
            assert val == actuals[i]

        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('testkey', '00'), val3),
                        (('testkey', '00'), val4),
                        (('testkey', '01'), val0),
                        (('testkey', '01'), val1),
                        (('testkey', '01'), val2)]

        items = list(suber.getFullItemIter())
        assert items ==  [(('testkey', '00.00000000000000000000000000000000'), val3),
                        (('testkey', '00.00000000000000000000000000000001'), val4),
                        (('testkey', '01.00000000000000000000000000000000'), val0),
                        (('testkey', '01.00000000000000000000000000000001'), val1),
                        (('testkey', '01.00000000000000000000000000000002'), val2)]

        items = [(keys, val) for keys,  val in  suber.getItemIter(keys=keys0)]
        assert items == [(('testkey', '00'), val3),
                         (('testkey', '00'), val4)]

        items = [(keys, val) for keys,  val in suber.getItemIter(keys=keys1)]
        assert items == [(('testkey', '01'), val0),
                         (('testkey', '01'), val1),
                         (('testkey', '01'), val2)]


        # Test with top keys
        assert suber.put(keys=("test", "pop"), vals=[val0, val1, val2])
        topkeys = ("test", "")
        items = [(keys, val) for keys, val in suber.getItemIter(keys=topkeys)]
        assert items == [(('test', 'pop'), val0),
                        (('test', 'pop'), val1),
                        (('test', 'pop'), val2)]

        # test with topive parameter
        keys = ("test", )
        items = [(keys, val) for keys, val in suber.getItemIter(keys=keys, topive=True)]
        assert items == [(('test', 'pop'), val0),
                        (('test', 'pop'), val1),
                        (('test', 'pop'), val2)]

        # IoItems
        items = list(suber.getFullItemIter(keys=topkeys))
        assert items == [(('test', 'pop.00000000000000000000000000000000'), val0),
                        (('test', 'pop.00000000000000000000000000000001'), val1),
                        (('test', 'pop.00000000000000000000000000000002'), val2)]

        # test remove with a specific val
        assert suber.rem(keys=("testkey", "01"), val=val1)
        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('test', 'pop'), val0),
                        (('test', 'pop'), val1),
                        (('test', 'pop'), val2),
                        (('testkey', '00'), val3),
                        (('testkey', '00'), val4),
                        (('testkey', '01'), val0),
                        (('testkey', '01'), val2)]

        assert suber.trim(keys=("test", ""))
        items = [(keys, val) for keys, val in suber.getItemIter()]
        assert items == [(('testkey', '00'), val3),
                        (('testkey', '00'), val4),
                        (('testkey', '01'), val0),
                        (('testkey', '01'), val2)]

        # test with keys as string not tuple
        keys4 = "keystr"

        assert suber.put(keys=keys4, vals=[val4])
        actuals = suber.get(keys=keys4)
        assert actuals == [val4]
        assert suber.cnt(keys4) == 1
        assert suber.rem(keys4)
        actuals = suber.get(keys=keys4)
        assert actuals == []
        assert suber.cnt(keys4) == 0

        assert suber.put(keys=keys4, vals=[val4])
        actuals = suber.get(keys=keys4)
        assert actuals == [val4]

        assert suber.pin(keys=keys4, vals=[val5])
        actuals = suber.get(keys=keys4)
        assert actuals == [val5]

        assert suber.add(keys=keys4, val=val4)
        actuals = suber.get(keys=keys4)
        assert actuals == [val5, val4]

        # Test trim and append
        assert suber.trim()  # default trims whole database
        assert suber.put(keys=keys1, vals=[val4, val5])
        assert suber.get(keys=keys1) == [val4, val5]



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

    assert isinstance(subery.drqs, DomIoSuber)
    assert isinstance(subery.drqs.sdb, lmdb._Database)

    assert isinstance(subery.dsqs, DomIoSetSuber)
    assert isinstance(subery.dsqs.sdb, lmdb._Database)

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

    assert isinstance(subery.drqs, DomIoSuber)
    assert isinstance(subery.drqs.sdb, lmdb._Database)

    assert isinstance(subery.dsqs, DomIoSetSuber)
    assert isinstance(subery.dsqs.sdb, lmdb._Database)

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

        assert isinstance(subery.drqs, DomIoSuber)
        assert isinstance(subery.drqs.sdb, lmdb._Database)

        assert isinstance(subery.dsqs, IoSetSuber)
        assert isinstance(subery.dsqs.sdb, lmdb._Database)


    assert not os.path.exists(subery.path)
    assert not subery.opened

    """Done Test"""


if __name__ == "__main__":
    test_duror_basic()
    test_openduror()
    test_duror()
    test_suberbase()
    test_suber()
    test_io_suber()
    test_ioset_suber()
    test_dom_suber_base()
    test_dom_suber()
    test_dom_io_suber()
    test_dom_ioset_suber()
    test_subery_basic()


