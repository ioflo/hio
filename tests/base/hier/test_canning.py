# -*- encoding: utf-8 -*-
"""tests.base.hier.test_canning module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest
import dataclasses
from hio.base import Tymist
from hio.base.hier import CanDom, Can


def test_canbase():
    """Test CanDom class"""
    tymist = Tymist()

    assert CanDom._registry
    assert CanDom.__name__ in CanDom._registry
    assert CanDom._registry[CanDom.__name__] == CanDom

    assert CanDom._names == ()
    # no fields just InitVar and ClassVar attributes
    fields = dataclasses.fields(CanDom)
    assert len(fields) == 0

    c = CanDom()  # defaults
    assert isinstance(c, CanDom)
    assert c._names == ()
    assert c._tymth == None
    assert c._now == None
    assert c._tyme == None
    assert c._sdb == None
    assert c._key == None

    c = CanDom(_tymth=tymist.tymen())
    assert c._names == ()
    assert c._tymth
    assert c._now == 0.0 == tymist.tyme
    assert c._tyme == None
    assert c._sdb == None
    assert c._key == None

    tymist.tick()
    assert c._now == tymist.tock
    tymist.tick()
    assert c._now == 2 * tymist.tock

    """Done Test"""

def test_can():
    """Test Can class"""
    tymist = Tymist()

    assert Can._registry
    assert Can.__name__ in Can._registry
    assert Can._registry[Can.__name__] == Can

    assert Can._names == ("value", )
    fields = dataclasses.fields(Can)
    assert len(fields) == 1
    assert fields[0].name == 'value'

    c = Can()  # defaults
    assert isinstance(c, Can)
    assert c._names == ("value", )
    assert c._tymth == None
    assert c._now == None
    assert c._tyme == None
    assert c._sdb == None
    assert c._key == None

    c = Can(value=10)
    assert c._names == ("value", )
    assert c._tymth == None
    assert c._now == None
    assert c._tyme == None
    assert c.value == 10

    c.value = 2
    assert c._tyme == None
    assert c.value == 2

    c = Can(_tymth=tymist.tymen())
    assert c._names == ("value", )
    assert c._tymth
    assert c._now == 0.0 == tymist.tyme
    assert c._tyme == None
    assert c._sdb == None
    assert c._key == None
    assert c.value == None

    c.value = 2
    assert c._tyme == 0.0 == tymist.tyme
    assert c.value == 2

    tymist.tick()
    assert c._now == tymist.tock

    # test __setitem__
    c["value"] = 3
    assert c["value"] == 3
    assert c._tyme == tymist.tock

    tymist.tick()
    assert c._now == 2 * tymist.tock

    tymist = Tymist()

    c = Can(value=3, _tymth=tymist.tymen())
    assert c._names == ("value", )
    assert c._tymth
    assert c._now == 0.0
    assert c._tyme == None   # tymth not assigned until __post_init__
    assert c._sdb == None
    assert c._key == None
    assert c.value == 3

    c.value = 2
    assert c._tyme == 0.0 == tymist.tyme
    assert c.value == 2

    tymist.tick()
    assert c._tyme == 0.0
    assert c._now == tymist.tock

    c.value = 5
    assert c._tyme == tymist.tock
    assert c.value == 5

    # test ._update
    tymist.tick()
    c._update(value=7)
    assert c._tyme == 2 * tymist.tock
    assert c.value == 7
    assert c["value"] == 7

    # test _asdict
    d = c._asdict()
    assert d == {'value': 7}

    # test _astuple
    t = c._astuple()
    assert t == (7, )


    """Done Test"""



if __name__ == "__main__":
    test_canbase()
    test_can()
