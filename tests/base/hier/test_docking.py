# -*- encoding: utf-8 -*-
"""tests.base.hier.test_docking module

"""
import pytest

import os
import lmdb

from hio.base.hier import Dock
from hio.hold import Holder, openHolder, Suber, IoSetSuber


def test_dock_basic():
    """Test Dock class"""

    dock = Dock(reopen=True)  # default is to not reopen
    assert isinstance(dock, Dock)
    assert dock.name == "main"
    assert dock.temp == False
    assert isinstance(dock.env, lmdb.Environment)
    assert dock.path.endswith(os.path.join("hio", "db", "main"))
    assert dock.env.path() == dock.path
    assert os.path.exists(dock.path)

    assert isinstance(dock.cans, Suber)
    assert isinstance(dock.cans.sdb, lmdb._Database)

    assert isinstance(dock.drqs, IoSetSuber)
    assert isinstance(dock.drqs.sdb, lmdb._Database)

    dock.close(clear=True)
    assert not os.path.exists(dock.path)
    assert not dock.opened

    # test not opened on init
    dock = Dock(reopen=False)
    assert isinstance(dock, Dock)
    assert dock.name == "main"
    assert dock.temp == False
    assert dock.opened == False
    assert dock.path == None
    assert dock.env == None

    dock.reopen()
    assert dock.opened
    assert isinstance(dock.env, lmdb.Environment)
    assert dock.path.endswith(os.path.join("hio", "db", "main"))
    assert dock.env.path() == dock.path
    assert os.path.exists(dock.path)

    assert isinstance(dock.cans, Suber)
    assert isinstance(dock.cans.sdb, lmdb._Database)

    assert isinstance(dock.drqs, IoSetSuber)
    assert isinstance(dock.drqs.sdb, lmdb._Database)

    dock.close(clear=True)
    assert not os.path.exists(dock.path)
    assert not dock.opened



    # Test using context manager
    with openHolder(cls=Dock) as dock:  # opens with temp=True by default
        assert isinstance(dock, Dock)
        assert dock.name == "test"
        assert dock.temp == True
        assert isinstance(dock.env, lmdb.Environment)
        _, path = os.path.splitdrive(os.path.normpath(dock.path))
        assert path.startswith(os.path.join(os.path.sep, "tmp", "hio_lmdb_"))
        assert dock.path.endswith(os.path.join("_test", "hio", "db", "test"))
        assert dock.env.path() == dock.path
        assert os.path.exists(dock.path)

        assert isinstance(dock.cans, Suber)
        assert isinstance(dock.cans.sdb, lmdb._Database)

        assert isinstance(dock.drqs, IoSetSuber)
        assert isinstance(dock.drqs.sdb, lmdb._Database)


    assert not os.path.exists(dock.path)
    assert not dock.opened

    """Done Test"""


if __name__ == "__main__":
    test_dock_basic()
