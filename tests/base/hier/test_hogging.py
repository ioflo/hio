# -*- encoding: utf-8 -*-
"""tests.base.hier.test_acting module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import os
import platform
import tempfile


import pytest

from hio.base import Doist
from hio.base.hier import Nabes, Hog, openHog, HogDoer



def test_hog_basic():
    """Test Hog class"""
    Hog._clearall()  # clear Hog.Instances for debugging

    hog = Hog(temp=True)  # test defaults
    assert hog.temp
    assert hog.name == "Hog0"
    assert hog.opened
    assert hog.filed
    assert hog.extensioned
    assert hog.fext == 'hog'
    assert hog.file
    assert not hog.file.closed
    assert os.path.exists(hog.path)

    tempDirPath = (os.path.join(os.path.sep, "tmp")
                       if platform.system() == "Darwin"
                       else tempfile.gettempdir())
    tempDirPath = os.path.normpath(tempDirPath)
    path = os.path.normpath(hog.path)  # '/tmp/hio_u36wdtp5_test/hio/Hog1.hog'
    assert path.startswith(os.path.join(tempDirPath, "hio_"))
    assert hog.path.endswith(os.path.join('_test', 'hio', 'Hog0.hog'))

    assert Hog.Registry[Hog.__name__] is Hog
    assert Hog.Registry['log'] is Hog
    assert Hog.Registry['Log'] is Hog

    assert hog() == {}  # default returns iops
    assert hog.nabe == Nabes.afdo
    assert hog.hold
    assert not hog.hold.subery
    assert hog.logs == {}

    hog.close(clear=True)
    assert not hog.opened
    assert not hog.file
    assert not os.path.exists(hog.path)


    """Done Test"""


def test_open_hog():
    """Test openHog context manager"""
    Hog._clearall()  # clear Hog.Instances for debugging

    with openHog() as hog:  # test defaults
        assert hog.temp
        assert hog.name == "Hog0"
        assert hog.opened
        assert hog.filed
        assert hog.extensioned
        assert hog.fext == 'hog'
        assert hog.file
        assert not hog.file.closed
        assert os.path.exists(hog.path)

        tempDirPath = (os.path.join(os.path.sep, "tmp")
                           if platform.system() == "Darwin"
                           else tempfile.gettempdir())
        tempDirPath = os.path.normpath(tempDirPath)
        path = os.path.normpath(hog.path)  # '/tmp/hio_u36wdtp5_test/hio/Hog1.hog'
        assert path.startswith(os.path.join(tempDirPath, "hio_"))
        assert hog.path.endswith(os.path.join('_test', 'hio', 'Hog0.hog'))

        assert Hog.Registry[Hog.__name__] is Hog
        assert Hog.Registry['log'] is Hog
        assert Hog.Registry['Log'] is Hog

        assert hog() == {}  # default returns iops
        assert hog.nabe == Nabes.afdo
        assert hog.hold
        assert not hog.hold.subery
        assert hog.logs == {}

    assert not hog.opened
    assert not hog.file
    assert not os.path.exists(hog.path)

    """Done Test"""

def test_hog_doer():
    """Test HogDoer"""
    Hog._clearall()  # clear Hog.Instances for debugging

    # create two HogDoer instances and run them

    hog0 = Hog(name='test0', temp=True, reopen=False)
    assert hog0.temp
    assert hog0.name == "test0"
    assert not hog0.opened
    assert hog0.filed
    assert hog0.extensioned
    assert hog0.fext == 'hog'
    assert not hog0.file
    assert not hog0.path

    hogDoer0 = HogDoer(hog=hog0)
    assert hogDoer0.hog == hog0
    assert not hogDoer0.hog.opened

    hog1 = Hog(name='test1', temp=True, reopen=False)
    assert not hog1.opened
    assert not hog1.file
    assert not hog1.path

    hogDoer1 = HogDoer(hog=hog1)
    assert hogDoer1.hog == hog1
    assert not hogDoer1.hog.opened

    limit = 0.25
    tock = 0.03125
    doist = Doist(limit=limit, tock=tock)

    doers = [hogDoer0, hogDoer1]

    doist.doers = doers
    doist.enter()
    assert len(doist.deeds) == 2
    assert [val[1] for val in doist.deeds] == [0.0, 0.0]  #  retymes
    for doer in doers:
        assert doer.hog.opened
        assert doer.hog.file
        assert os.path.join('_test', 'hio', 'test') in doer.hog.path

    doist.recur()
    assert doist.tyme == 0.03125  # on next cycle
    assert len(doist.deeds) == 2
    for doer in doers:
        assert doer.hog.opened
        assert doer.hog.file

    for dog, retyme, index in doist.deeds:
        dog.close()

    for doer in doers:
        assert not doer.hog.opened
        assert not doer.hog.file
        assert not os.path.exists(doer.hog.path)


    # start over but not opened
    doist.tyme = 0.0
    doist.do(doers=doers)
    assert doist.tyme == limit
    for doer in doers:
        assert not doer.hog.opened
        assert not doer.hog.file
        assert not os.path.exists(doer.hog.path)

    """End Test"""


if __name__ == "__main__":
    test_hog_basic()
    test_open_hog()
    test_hog_doer()
