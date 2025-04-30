# -*- encoding: utf-8 -*-
"""tests.base.hier.test_bagging module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest
from dataclasses import dataclass, astuple, asdict, fields, field
from hio.base import Tymist
from hio.base.hier import Bag



def test_bag():
    """Test Bag class"""
    tymist = Tymist()

    assert Bag._registry
    assert Bag.__name__ in Bag._registry
    assert Bag._registry[Bag.__name__] == Bag

    assert Bag._names == ("value", )
    flds = fields(Bag)
    assert len(flds) == 1
    assert flds[0].name == 'value'

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
    test_bag()

