# -*- encoding: utf-8 -*-
"""tests.base.hier.test_bagging module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest
import dataclasses
from hio.base import Tymist
from hio.base.hier import TymeDom, Bag



def test_tymedom():
    """Test TymeDom class"""
    tymist = Tymist()

    assert TymeDom._names == ()
    # no fields just InitVar and ClassVar attributes
    fields = dataclasses.fields(TymeDom)
    assert len(fields) == 0

    b = TymeDom()  # defaults
    assert isinstance(b, TymeDom)
    assert b._names == ()
    assert b._tymth == None
    assert b._now == None
    assert b._tyme == None

    b = TymeDom(_tymth=tymist.tymen())
    assert b._names == ()
    assert b._tymth
    assert b._now == 0.0 == tymist.tyme
    assert b._tyme == None

    tymist.tick()
    assert b._now == tymist.tock
    tymist.tick()
    assert b._now == 2 * tymist.tock


    # adding attribute does not make it a dataclass field
    b.value = 1
    assert b._tyme == None
    assert b.value == 1
    assert b["value"] == 1

    # test __setitem__
    b["value"] = 2
    assert b._tyme == None
    assert b["value"] == 2

    b["stuff"] = 3
    assert b._tyme == None
    assert b["stuff"] == 3
    assert b.stuff == 3

    fields = dataclasses.fields(b)  # or equiv dataclasses.fields(TymeDom)
    assert len(fields) == 0

    b = TymeDom(_tyme=1.0)
    assert b._names == ()
    assert not b._tymth
    assert b._now == None
    assert b._tyme == 1.0


    b = TymeDom(_tyme=1.0, _tymth=tymist.tymen())
    assert b._names == ()
    assert b._tymth
    assert b._now == 2 * tymist.tock
    assert b._tyme == 1.0

    # test ._update
    tymist = Tymist()
    b = TymeDom(_tymth=tymist.tymen())
    assert b._names == ()
    assert b._tymth
    assert b._now == 0.0 == tymist.tyme
    assert b._tyme == None

    b._update(value=1)
    assert b._tyme == None
    assert b.value == 1
    assert b["value"] == 1


    # test _asdict
    d = b._asdict()
    assert d == {}  # no fields so empty

    # test _astuple
    t = b._astuple()
    assert t == ()  # no fields so empty

    """Done Test"""


def test_bag():
    """Test Bag class"""
    tymist = Tymist()

    assert Bag._names == ("value", )
    fields = dataclasses.fields(Bag)
    assert len(fields) == 1
    assert fields[0].name == 'value'

    b = Bag()
    assert b._names == ("value", )
    assert b._tymth == None
    assert b._now == None
    assert b._tyme == None
    assert b.value == None

    b = Bag(value=10)
    assert b._names == ("value", )
    assert b._tymth == None
    assert b._now == None
    assert b._tyme == None
    assert b.value == 10

    b.value = 2
    assert b._tyme == None
    assert b.value == 2

    b = Bag(_tymth=tymist.tymen())
    assert b._names == ("value", )
    assert b._tymth
    assert b._now == 0.0
    assert b._tyme == None
    assert b.value == None

    b.value = 2
    assert b._tyme == 0.0 == tymist.tyme
    assert b.value == 2

    tymist.tick()

    # test __setitem__
    b["value"] = 3
    assert b["value"] == 3
    assert b._tyme == tymist.tock

    tymist = Tymist()

    b = Bag(value=3, _tymth=tymist.tymen())
    assert b._names == ("value", )
    assert b._tymth
    assert b._now == 0.0
    assert b._tyme == None   # tymth not assigned until __post_init__
    assert b.value == 3

    b.value = 2
    assert b._tyme == 0.0 == tymist.tyme
    assert b.value == 2

    tymist.tick()
    assert b._tyme == 0.0
    assert b._now == tymist.tock

    b.value = 5
    assert b._tyme == tymist.tock
    assert b.value == 5

    # test ._update
    tymist.tick()
    b._update(value=7)
    assert b._tyme == 2 * tymist.tock
    assert b.value == 7
    assert b["value"] == 7

    # test _asdict
    d = b._asdict()
    assert d == {'value': 7}

    # test _astuple
    t = b._astuple()
    assert t == (7, )

    """Done Test"""


if __name__ == "__main__":
    test_tymedom()
    test_bag()
