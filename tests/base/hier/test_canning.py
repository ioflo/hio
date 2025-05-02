# -*- encoding: utf-8 -*-
"""tests.base.hier.test_canning module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest
from dataclasses import dataclass, astuple, asdict, fields, field

from hio.help import registerify, namify
from hio.base import Tymist
from hio.base.hier import CanDom, Can


def test_candom():
    """Test CanDom class"""
    tymist = Tymist(tock=1.0)

    assert CanDom._registry
    assert CanDom.__name__ in CanDom._registry
    assert CanDom._registry[CanDom.__name__] == CanDom

    assert CanDom._names == ()
    # no fields just InitVar and ClassVar attributes
    flds = fields(CanDom)
    assert len(flds) == 0

    cd = CanDom()  # defaults
    assert isinstance(cd, CanDom)
    assert cd._names == ()
    assert cd._tymth == None
    assert cd._now == None
    assert cd._tyme == None
    assert not cd._durable
    assert cd._sdb == None
    assert cd._key == None
    assert cd._stale == True
    assert cd._fresh == False
    assert cd._bulk == False

    cd = CanDom(_tymth=tymist.tymen())
    assert cd._names == ()
    assert cd._tymth
    assert cd._now == 0.0 == tymist.tyme
    assert cd._tyme == None
    assert not cd._durable
    assert cd._sdb == None
    assert cd._key == None
    assert cd._stale == True
    assert cd._fresh == False
    assert cd._bulk == False

    tymist.tick()
    assert cd._now == tymist.tock
    tymist.tick()
    assert cd._now == 2 * tymist.tock

    cd = CanDom(_key="hello", _stale=False, _fresh=True, _bulk=True)
    assert cd._names == ()
    assert cd._tymth == None
    assert cd._now == None
    assert cd._tyme == None
    assert not cd._durable
    assert cd._sdb == None
    assert cd._key == "hello"
    assert cd._stale == False
    assert cd._fresh == True
    assert cd._bulk == True

    @namify
    @registerify
    @dataclass
    class TestCanDom(CanDom):
        """TestCanDom dataclass

        Field Attributes:
            value (Any):  generic value field
        """
        value: Any = None  # generic value

    assert TestCanDom._names == ('value', )

    tymist = Tymist(tock=1.0)

    tcd = TestCanDom(_tymth=tymist.tymen())
    assert isinstance(tcd, CanDom)
    assert isinstance(tcd, TestCanDom)
    assert tcd._registry[tcd.__class__.__name__] == TestCanDom
    assert tcd._names == ('value', )
    assert tcd._tymth
    assert tcd._now == 0.0 == tymist.tyme
    assert tcd._tyme == None
    assert not cd._durable
    assert tcd._sdb == None
    assert tcd._key == None
    assert tcd._stale == True
    assert tcd._fresh == False
    assert tcd._bulk == False

    # test _asdict
    assert tcd._asdict() == {'value': None}

    # test _astuple
    assert tcd._astuple() == (None,)

    tcd.value = "hello"
    assert tcd._tyme == 0.0 == tcd._now == tymist._tyme
    # test _asdict
    assert tcd._asdict() == {'value': "hello"}

    # test _astuple
    assert tcd._astuple() == ("hello",)

    """Done Test"""


def test_can():
    """Test Can class"""
    tymist = Tymist()

    assert Can._registry
    assert Can.__name__ in Can._registry
    assert Can._registry[Can.__name__] == Can

    assert Can._names == ("value", )
    flds = fields(Can)
    assert len(flds) == 1
    assert flds[0].name == 'value'

    c = Can()  # defaults
    assert isinstance(c, Can)
    assert c._names == ("value", )
    assert c._tymth == None
    assert c._now == None
    assert c._tyme == None
    assert not c._durable
    assert c._sdb == None
    assert c._key == None
    assert c._stale == True
    assert c._fresh == False
    assert c._bulk == False

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
    assert not c._durable
    assert c._sdb == None
    assert c._key == None
    assert c._stale == True
    assert c._fresh == False
    assert c._bulk == False
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
    assert not c._durable
    assert c._sdb == None
    assert c._key == None
    assert c._stale == True
    assert c._fresh == False
    assert c._bulk == False
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
    test_candom()
    test_can()
