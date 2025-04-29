# -*- encoding: utf-8 -*-
"""tests.help.test_during module

"""
import pytest

import os
import platform
import tempfile
import lmdb
from ordered_set import OrderedSet as oset

from hio.base import (Duror, openDuror, SuberBase, Suber, IoSetSuber)


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
        assert duror.delVal(sdb, key) == False
        assert duror.putVal(sdb, key, val) == True
        assert duror.putVal(sdb, key, val) == False
        assert duror.setVal(sdb, key, val) == True
        assert duror.getVal(sdb, key) == val
        assert duror.cntVals(sdb) == 1
        assert duror.delVal(sdb, key) == True
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
        assert duror.delTopVals(sdb, top=b"a.")
        items = [ (key, bytes(val)) for key, val in duror.getTopItemIter(sdb=sdb )]
        assert items == [(b'b.1', b'woo')]

        assert duror.delTopVals(sdb)
        assert duror.cntVals(sdb) == 0


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

        sdb = duror.env.open_db(key=b'ioset.', dupsort=False)

        assert duror.getIoSetVals(sdb, key0) == oset()
        assert duror.getIoSetValLast(sdb, key0) == None
        assert duror.cntIoSetVals(sdb, key0) == 0
        assert duror.delIoSetVals(sdb, key0) == False

        assert duror.putIoSetVals(sdb, key0, vals0) == True
        assert duror.getIoSetVals(sdb, key0) == vals0  # preserved insertion order
        assert duror.cntIoSetVals(sdb, key0) == len(vals0) == 4
        assert duror.getIoSetValLast(sdb, key0) == vals0[-1] == vals0[-1]

        assert duror.putIoSetVals(sdb, key0, vals=[b'a']) == False   # duplicate
        assert duror.getIoSetVals(sdb, key0) == vals0  #  no change
        assert duror.putIoSetVals(sdb, key0, vals=[b'f']) == True
        assert duror.getIoSetVals(sdb, key0) == [b"z", b"m", b"x", b"a", b"f"]
        assert duror.addIoSetVal(sdb, key0, val=b'b') == True
        assert duror.addIoSetVal(sdb, key0, val=b'a') == False
        assert duror.getIoSetVals(sdb, key0) == [b"z", b"m", b"x", b"a", b"f", b"b"]

        assert [val for val in duror.getIoSetValsIter(sdb, key0)] == [b"z", b"m", b"x", b"a", b"f", b"b"]
        assert duror.delIoSetVals(sdb, key0) == True
        assert duror.getIoSetVals(sdb, key0) == []

        assert duror.putIoSetVals(sdb, key0, vals0) == True
        for val in vals0:
            assert duror.delIoSetVal(sdb, key0, val)
        assert duror.getIoSetVals(sdb, key0) == oset()
        assert duror.putIoSetVals(sdb, key0, vals0) == True
        for val in sorted(vals0):  # test deletion out of order
            assert duror.delIoSetVal(sdb, key0, val)
        assert duror.getIoSetVals(sdb, key0) == []

        #delete and add in odd order
        assert duror.putIoSetVals(sdb, key0, vals0) == True
        assert duror.delIoSetVal(sdb, key0, vals0[2])
        assert duror.addIoSetVal(sdb, key0, b'w')
        assert duror.delIoSetVal(sdb, key0, vals0[0])
        assert duror.addIoSetVal(sdb, key0, b'e')
        assert duror.getIoSetVals(sdb, key0) == [b'm', b'a', b'w', b'e']

        assert duror.delIoSetVals(sdb, key0) == True
        assert duror.getIoSetVals(sdb, key0) == oset()

        assert duror.putIoSetVals(sdb, key0, vals0) == True
        assert duror.putIoSetVals(sdb, key1, vals1) == True
        assert duror.putIoSetVals(sdb, key2, vals2) == True
        assert duror.getIoSetVals(sdb, key0) == vals0
        assert duror.getIoSetVals(sdb, key1) == vals1
        assert duror.getIoSetVals(sdb, key2) == vals2

        assert duror.setIoSetVals(sdb, key2, vals3)
        assert duror.getIoSetVals(sdb, key2) == vals3
        assert duror.cntVals(sdb) == 10

        assert duror.delTopVals(sdb)
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
        for key, val in duror.getTopIoSetItemIter(sdb):
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
        for key, val in duror.getTopIoSetItemIter(sdb, top=b'ABC_'):
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
        for key, val in duror.getTopIoSetItemIter(sdb, top=b'AB'):
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



def test_ioset_suber():
    """Test IoSetSuber LMDBer sub database class"""

    with openDuror() as duror:
        assert isinstance(duror, Duror)
        assert duror.name == "test"
        assert duror.opened

        assert IoSetSuber.Sep == '_'
        assert IoSetSuber.IonSep == '.'

        iosuber = IoSetSuber(db=duror, subkey='bags.')
        assert isinstance(iosuber, IoSetSuber)
        assert not iosuber.sdb.flags()["dupsort"]
        assert iosuber.sep == '_'
        assert iosuber.ionsep == '.'

        sue = "Hello sailer!"
        sal = "Not my type."

        keys0 = ("testkey", "0001")
        keys1 = ("testkey", "0002")

        assert iosuber.put(keys=keys0, vals=[sal, sue])
        actuals = iosuber.get(keys=keys0)
        assert actuals == [sal, sue]  # insertion order not lexicographic
        assert iosuber.cnt(keys0) == 2
        actual = iosuber.getLast(keys=keys0)
        assert actual == sue

        assert iosuber.rem(keys0)
        actuals = iosuber.get(keys=keys0)
        assert not actuals
        assert actuals == []
        assert iosuber.cnt(keys0) == 0

        assert iosuber.put(keys=keys0, vals=[sue, sal])
        actuals = iosuber.get(keys=keys0)
        assert actuals == [sue, sal]  # insertion order
        actual = iosuber.getLast(keys=keys0)
        assert actual == sal

        sam = "A real charmer!"
        result = iosuber.add(keys=keys0, val=sam)
        assert result
        actuals = iosuber.get(keys=keys0)
        assert actuals == [sue, sal, sam]   # insertion order

        zoe = "See ya later."
        zia = "Hey gorgeous!"

        result = iosuber.pin(keys=keys0, vals=[zoe, zia])
        assert result
        actuals = iosuber.get(keys=keys0)
        assert actuals == [zoe, zia]  # insertion order

        assert iosuber.put(keys=keys1, vals=[sal, sue, sam])
        actuals = iosuber.get(keys=keys1)
        assert actuals == [sal, sue, sam]

        for i, val in enumerate(iosuber.getIter(keys=keys1)):
            assert val == actuals[i]

        items = [(keys, val) for keys, val in iosuber.getItemIter()]
        assert items == [(('testkey', '0001'), 'See ya later.'),
                        (('testkey', '0001'), 'Hey gorgeous!'),
                        (('testkey', '0002'), 'Not my type.'),
                        (('testkey', '0002'), 'Hello sailer!'),
                        (('testkey', '0002'), 'A real charmer!')]

        items = list(iosuber.getFullItemIter())
        assert items ==  [(('testkey', '0001.00000000000000000000000000000000'), 'See ya later.'),
                        (('testkey', '0001.00000000000000000000000000000001'), 'Hey gorgeous!'),
                        (('testkey', '0002.00000000000000000000000000000000'), 'Not my type.'),
                        (('testkey', '0002.00000000000000000000000000000001'), 'Hello sailer!'),
                        (('testkey', '0002.00000000000000000000000000000002'), 'A real charmer!')]



        items = [(keys, val) for keys,  val in  iosuber.getItemIter(keys=keys0)]
        assert items == [(('testkey', '0001'), 'See ya later.'),
                         (('testkey', '0001'), 'Hey gorgeous!')]

        items = [(keys, val) for keys,  val in iosuber.getItemIter(keys=keys1)]
        assert items == [(('testkey', '0002'), 'Not my type.'),
                        (('testkey', '0002'), 'Hello sailer!'),
                        (('testkey', '0002'), 'A real charmer!')]


        # Test with top keys
        assert iosuber.put(keys=("test", "pop"), vals=[sal, sue, sam])
        topkeys = ("test", "")
        items = [(keys, val) for keys, val in iosuber.getItemIter(keys=topkeys)]
        assert items == [(('test', 'pop'), 'Not my type.'),
                         (('test', 'pop'), 'Hello sailer!'),
                         (('test', 'pop'), 'A real charmer!')]

        # test with top parameter
        keys = ("test", )
        items = [(keys, val) for keys, val in iosuber.getItemIter(keys=keys, topive=True)]
        assert items == [(('test', 'pop'), 'Not my type.'),
                         (('test', 'pop'), 'Hello sailer!'),
                         (('test', 'pop'), 'A real charmer!')]

        # IoItems
        items = list(iosuber.getFullItemIter(keys=topkeys))
        assert items == [(('test', 'pop.00000000000000000000000000000000'), 'Not my type.'),
                    (('test', 'pop.00000000000000000000000000000001'), 'Hello sailer!'),
                    (('test', 'pop.00000000000000000000000000000002'), 'A real charmer!')]

        # test remove with a specific val
        assert iosuber.rem(keys=("testkey", "0002"), val=sue)
        items = [(keys, val) for keys, val in iosuber.getItemIter()]
        assert items == [(('test', 'pop'), 'Not my type.'),
                        (('test', 'pop'), 'Hello sailer!'),
                        (('test', 'pop'), 'A real charmer!'),
                        (('testkey', '0001'), 'See ya later.'),
                        (('testkey', '0001'), 'Hey gorgeous!'),
                        (('testkey', '0002'), 'Not my type.'),
                        (('testkey', '0002'), 'A real charmer!')]

        assert iosuber.trim(keys=("test", ""))
        items = [(keys, val) for keys, val in iosuber.getItemIter()]
        assert items == [(('testkey', '0001'), 'See ya later.'),
                        (('testkey', '0001'), 'Hey gorgeous!'),
                        (('testkey', '0002'), 'Not my type.'),
                        (('testkey', '0002'), 'A real charmer!')]



        # test with keys as string not tuple
        keys2 = "keystr"
        bob = "Shove off!"
        assert iosuber.put(keys=keys2, vals=[bob])
        actuals = iosuber.get(keys=keys2)
        assert actuals == [bob]
        assert iosuber.cnt(keys2) == 1
        assert iosuber.rem(keys2)
        actuals = iosuber.get(keys=keys2)
        assert actuals == []
        assert iosuber.cnt(keys2) == 0

        assert iosuber.put(keys=keys2, vals=[bob])
        actuals = iosuber.get(keys=keys2)
        assert actuals == [bob]

        bil = "Go away."
        assert iosuber.pin(keys=keys2, vals=[bil])
        actuals = iosuber.get(keys=keys2)
        assert actuals == [bil]

        assert iosuber.add(keys=keys2, val=bob)
        actuals = iosuber.get(keys=keys2)
        assert actuals == [bil, bob]

        # Test trim and append
        assert iosuber.trim()  # default trims whole database
        assert iosuber.put(keys=keys1, vals=[bob, bil])
        assert iosuber.get(keys=keys1) == [bob, bil]

    assert not os.path.exists(duror.path)
    assert not duror.opened
    """Done Test"""


if __name__ == "__main__":
    test_duror_basic()
    test_openduror()
    test_duror()
    test_suberbase()
    test_suber()
    test_ioset_suber()

