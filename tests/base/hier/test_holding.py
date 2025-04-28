# -*- encoding: utf-8 -*-
"""
tests.hold.test_holding module

"""
import pytest
import os
import lmdb


from hio.base import Duror, openDuror, Suber, IoSetSuber
from hio.base.hier import DomSuber, Duck

def test_hold_basic():
    """Test Hold basic"""

    """Done Test"""



def test_domsuber():
    """Test DomSuber, Duror sub database class"""

    with openDuror() as duror:
        assert isinstance(duror, Duror)
        assert duror.name == "test"
        assert duror.opened

        assert Suber.Sep == '_'

        suber = DomSuber(db=duror, subkey='bags.')
        assert isinstance(suber, DomSuber)
        assert not suber.sdb.flags()["dupsort"]
        assert suber.sep == "_"

        keys = ('key', 'top')
        key = suber._tokey(keys)
        assert key == b'key_top'
        assert suber._tokeys(key) == keys

        """Done Test"""



def test_duck_basic():
    """Test Duck class"""

    duck = Duck(reopen=True)  # default is to not reopen
    assert isinstance(duck, Duck)
    assert duck.name == "main"
    assert duck.temp == False
    assert isinstance(duck.env, lmdb.Environment)
    assert duck.path.endswith(os.path.join("hio", "db", "main"))
    assert duck.env.path() == duck.path
    assert os.path.exists(duck.path)

    assert isinstance(duck.cans, Suber)
    assert isinstance(duck.cans.sdb, lmdb._Database)

    assert isinstance(duck.drqs, IoSetSuber)
    assert isinstance(duck.drqs.sdb, lmdb._Database)

    duck.close(clear=True)
    assert not os.path.exists(duck.path)
    assert not duck.opened

    # test not opened on init
    duck = Duck(reopen=False)
    assert isinstance(duck, Duck)
    assert duck.name == "main"
    assert duck.temp == False
    assert duck.opened == False
    assert duck.path == None
    assert duck.env == None

    duck.reopen()
    assert duck.opened
    assert isinstance(duck.env, lmdb.Environment)
    assert duck.path.endswith(os.path.join("hio", "db", "main"))
    assert duck.env.path() == duck.path
    assert os.path.exists(duck.path)

    assert isinstance(duck.cans, Suber)
    assert isinstance(duck.cans.sdb, lmdb._Database)

    assert isinstance(duck.drqs, IoSetSuber)
    assert isinstance(duck.drqs.sdb, lmdb._Database)

    duck.close(clear=True)
    assert not os.path.exists(duck.path)
    assert not duck.opened



    # Test using context manager
    with openDuror(cls=Duck) as duck:  # opens with temp=True by default
        assert isinstance(duck, Duck)
        assert duck.name == "test"
        assert duck.temp == True
        assert isinstance(duck.env, lmdb.Environment)
        _, path = os.path.splitdrive(os.path.normpath(duck.path))
        assert path.startswith(os.path.join(os.path.sep, "tmp", "hio_lmdb_"))
        assert duck.path.endswith(os.path.join("_test", "hio", "db", "test"))
        assert duck.env.path() == duck.path
        assert os.path.exists(duck.path)

        assert isinstance(duck.cans, Suber)
        assert isinstance(duck.cans.sdb, lmdb._Database)

        assert isinstance(duck.drqs, IoSetSuber)
        assert isinstance(duck.drqs.sdb, lmdb._Database)


    assert not os.path.exists(duck.path)
    assert not duck.opened

    """Done Test"""





if __name__ == "__main__":
    test_hold_basic()
    test_domsuber()
    test_duck_basic()
