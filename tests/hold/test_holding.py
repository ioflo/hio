# -*- encoding: utf-8 -*-
"""
tests.hold.test_holding module

"""
import pytest
import os
import lmdb
from ordered_set import OrderedSet as oset

from hio.hold import Holder, openHolder


def test_holder_basic():
    """Test Holder Class  """
    holder = Holder()
    assert isinstance(holder, Holder)
    assert holder.name == "main"
    assert holder.temp == False
    assert isinstance(holder.env, lmdb.Environment)
    assert holder.path.endswith(os.path.join("hio", "db", "main"))
    assert holder.env.path() == holder.path
    assert os.path.exists(holder.path)
    assert holder.opened

    holder.close(clear=True)
    assert not os.path.exists(holder.path)

    assert Holder.SuffixSize == 32
    assert Holder.MaxSuffix ==  340282366920938463463374607431768211455


    key = "ABCDEFG.FFFFFF"
    keyb = b"ABCDEFG.FFFFFF"

    ion = 0
    iokey = Holder.suffix(key, ion)
    assert iokey == b'ABCDEFG.FFFFFF.00000000000000000000000000000000'
    k, i = Holder.unsuffix(iokey)
    assert k == keyb
    assert i == ion

    ion = 64
    iokey = Holder.suffix(keyb, ion)
    assert iokey == b'ABCDEFG.FFFFFF.00000000000000000000000000000040'
    k, i = Holder.unsuffix(iokey)
    assert k == keyb
    assert i == ion

    iokey = Holder.suffix(key, Holder.MaxSuffix)
    assert iokey ==  b'ABCDEFG.FFFFFF.ffffffffffffffffffffffffffffffff'
    k, i = Holder.unsuffix(iokey)
    assert k == keyb
    assert i == Holder.MaxSuffix

    key = "ABCDEFG_FFFFFF"
    keyb = b"ABCDEFG_FFFFFF"

    ion = 0
    iokey = Holder.suffix(key, ion)
    assert iokey == b'ABCDEFG_FFFFFF.00000000000000000000000000000000'
    k, i = Holder.unsuffix(iokey)
    assert k == keyb
    assert i == ion

    ion = 64
    iokey = Holder.suffix(keyb, ion)
    assert iokey == b'ABCDEFG_FFFFFF.00000000000000000000000000000040'
    k, i = Holder.unsuffix(iokey)
    assert k == keyb
    assert i == ion

    iokey = Holder.suffix(key, Holder.MaxSuffix)
    assert iokey ==  b'ABCDEFG_FFFFFF.ffffffffffffffffffffffffffffffff'
    k, i = Holder.unsuffix(iokey)
    assert k == keyb
    assert i == Holder.MaxSuffix
    """Done Test"""


def test_openholder():
    """
    test contextmanager openHolder
    """
    with openHolder() as holder:
        assert isinstance(holder, Holder)
        assert holder.name == "test"
        assert isinstance(holder.env, lmdb.Environment)
        _, path = os.path.splitdrive(os.path.normpath(holder.path))
        assert path.startswith(os.path.join(os.path.sep, "tmp", "hio_lmdb_"))
        assert holder.path.endswith(os.path.join("_test", "hio", "db", "test"))
        assert holder.env.path() == holder.path
        assert os.path.exists(holder.path)
        assert holder.opened

    assert not os.path.exists(holder.path)
    assert not holder.opened

    with openHolder(name="blue") as holder:
        assert isinstance(holder, Holder)
        assert holder.name == "blue"
        assert isinstance(holder.env, lmdb.Environment)
        _, path = os.path.splitdrive(os.path.normpath(holder.path))
        assert path.startswith(os.path.join(os.path.sep, "tmp", "hio_lmdb_"))
        assert holder.path.endswith(os.path.join("_test", "hio", "db", "blue"))
        assert holder.env.path() == holder.path
        assert os.path.exists(holder.path)
        assert holder.opened

    assert not os.path.exists(holder.path)
    assert not holder.opened

    with openHolder(name="red") as redbaser, openHolder(name="tan") as tanbaser:
        assert isinstance(redbaser, Holder)
        assert redbaser.name == "red"
        assert redbaser.env.path() == redbaser.path
        assert os.path.exists(redbaser.path)
        assert redbaser.opened

        assert isinstance(tanbaser, Holder)
        assert tanbaser.name == "tan"
        assert tanbaser.env.path() == tanbaser.path
        assert os.path.exists(tanbaser.path)
        assert tanbaser.opened

    assert not os.path.exists(redbaser.path)
    assert not redbaser.opened
    assert not os.path.exists(tanbaser.path)
    assert not tanbaser.opened

    """Done Test"""

def test_holder():
    """Test Holder methods"""

    holder = Holder()
    assert isinstance(holder, Holder)
    assert holder.name == "main"
    assert holder.temp == False
    assert isinstance(holder.env, lmdb.Environment)
    assert holder.path.endswith(os.path.join("hio", "db", "main"))
    assert holder.env.path() == holder.path
    assert os.path.exists(holder.path)
    assert holder.opened
    holder.close(clear=True)
    assert not os.path.exists(holder.path)
    assert not holder.opened

    # test not opened on init
    holder = Holder(reopen=False)
    assert isinstance(holder, Holder)
    assert holder.name == "main"
    assert holder.temp == False
    assert holder.opened == False
    assert holder.path == None
    assert holder.env == None

    holder.reopen()
    assert holder.opened
    assert isinstance(holder.env, lmdb.Environment)
    assert holder.path.endswith(os.path.join("hio", "db", "main"))
    assert holder.env.path() == holder.path
    assert os.path.exists(holder.path)
    holder.close(clear=True)
    assert not os.path.exists(holder.path)
    assert not holder.opened

    with openHolder() as holder:
        assert holder.temp == True
        #test Val methods put set get del cnt
        key = b'A'
        val = b'whatever'
        sdb = holder.env.open_db(key=b'beep.')

        assert holder.getVal(sdb, key) == None
        assert holder.delVal(sdb, key) == False
        assert holder.putVal(sdb, key, val) == True
        assert holder.putVal(sdb, key, val) == False
        assert holder.setVal(sdb, key, val) == True
        assert holder.getVal(sdb, key) == val
        assert holder.cntVals(sdb) == 1
        assert holder.delVal(sdb, key) == True
        assert holder.getVal(sdb, key) == None
        assert holder.cntVals(sdb) == 0

        # Test getTopItemIter
        key = b"a.1"
        val = b"wow"
        assert holder.putVal(sdb, key, val) == True
        key = b"a.2"
        val = b"wee"
        assert holder.putVal(sdb, key, val) == True
        key = b"b.1"
        val = b"woo"
        assert holder.putVal(sdb, key, val) == True
        assert [(bytes(key), bytes(val)) for key, val
                     in holder.getTopItemIter(sdb=sdb)] == [(b'a.1', b'wow'),
                                                        (b'a.2', b'wee'),
                                                        (b'b.1', b'woo')]
        # Test delTopVals
        assert holder.delTopVals(sdb, top=b"a.")
        items = [ (key, bytes(val)) for key, val in holder.getTopItemIter(sdb=sdb )]
        assert items == [(b'b.1', b'woo')]

        assert holder.delTopVals(sdb)
        assert holder.cntVals(sdb) == 0


        # Test ioset methods
        """
        putIoSetVals
        addIoSetVal
        setIoSetVals

        getIoSetVals
        getIoSetValsIter
        getIoSetValLast

        cntIoSetVals

        delIoSetVals
        delIoSetVal

        getTopIoSetItemsIter
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

        sdb = holder.env.open_db(key=b'ioset.', dupsort=False)

        assert holder.getIoSetVals(sdb, key0) == oset()
        assert holder.getIoSetValLast(sdb, key0) == None
        assert holder.cntIoSetVals(sdb, key0) == 0
        assert holder.delIoSetVals(sdb, key0) == False

        assert holder.putIoSetVals(sdb, key0, vals0) == True
        assert holder.getIoSetVals(sdb, key0) == vals0  # preserved insertion order
        assert holder.cntIoSetVals(sdb, key0) == len(vals0) == 4
        assert holder.getIoSetValLast(sdb, key0) == vals0[-1] == vals0[-1]

        assert holder.putIoSetVals(sdb, key0, vals=[b'a']) == False   # duplicate
        assert holder.getIoSetVals(sdb, key0) == vals0  #  no change
        assert holder.putIoSetVals(sdb, key0, vals=[b'f']) == True
        assert holder.getIoSetVals(sdb, key0) == [b"z", b"m", b"x", b"a", b"f"]
        assert holder.addIoSetVal(sdb, key0, val=b'b') == True
        assert holder.addIoSetVal(sdb, key0, val=b'a') == False
        assert holder.getIoSetVals(sdb, key0) == [b"z", b"m", b"x", b"a", b"f", b"b"]

        assert [val for val in holder.getIoSetValsIter(sdb, key0)] == [b"z", b"m", b"x", b"a", b"f", b"b"]
        assert holder.delIoSetVals(sdb, key0) == True
        assert holder.getIoSetVals(sdb, key0) == []

        assert holder.putIoSetVals(sdb, key0, vals0) == True
        for val in vals0:
            assert holder.delIoSetVal(sdb, key0, val)
        assert holder.getIoSetVals(sdb, key0) == oset()
        assert holder.putIoSetVals(sdb, key0, vals0) == True
        for val in sorted(vals0):  # test deletion out of order
            assert holder.delIoSetVal(sdb, key0, val)
        assert holder.getIoSetVals(sdb, key0) == []

        #delete and add in odd order
        assert holder.putIoSetVals(sdb, key0, vals0) == True
        assert holder.delIoSetVal(sdb, key0, vals0[2])
        assert holder.addIoSetVal(sdb, key0, b'w')
        assert holder.delIoSetVal(sdb, key0, vals0[0])
        assert holder.addIoSetVal(sdb, key0, b'e')
        assert holder.getIoSetVals(sdb, key0) == [b'm', b'a', b'w', b'e']

        assert holder.delIoSetVals(sdb, key0) == True
        assert holder.getIoSetVals(sdb, key0) == oset()

        assert holder.putIoSetVals(sdb, key0, vals0) == True
        assert holder.putIoSetVals(sdb, key1, vals1) == True
        assert holder.putIoSetVals(sdb, key2, vals2) == True
        assert holder.getIoSetVals(sdb, key0) == vals0
        assert holder.getIoSetVals(sdb, key1) == vals1
        assert holder.getIoSetVals(sdb, key2) == vals2

        assert holder.setIoSetVals(sdb, key2, vals3)
        assert holder.getIoSetVals(sdb, key2) == vals3
        assert holder.cntVals(sdb) == 10

        assert holder.delTopVals(sdb)
        assert holder.cntVals(sdb) == 0

        # Test setTopIoSetItemIter(self, sdb, pre)
        assert holder.putIoSetVals(sdb, key0, vals0) == True
        assert holder.putIoSetVals(sdb, key1, vals1) == True
        assert holder.putIoSetVals(sdb, key2, vals2) == True
        assert holder.putIoSetVals(sdb, key3, vals3) == True
        assert holder.putIoSetVals(sdb, key4, vals4) == True
        assert holder.putIoSetVals(sdb, key5, vals5) == True
        assert holder.cntVals(sdb) == 18

        items = []
        for key, val in holder.getTopIoSetItemIter(sdb):
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
        for key, val in holder.getTopIoSetItemIter(sdb, top=b'ABC_'):
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
        for key, val in holder.getTopIoSetItemIter(sdb, top=b'AB'):
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


    assert not os.path.exists(holder.path)

    """Done Test"""




if __name__ == "__main__":
    test_holder_basic()
    test_openholder()
    test_holder()
