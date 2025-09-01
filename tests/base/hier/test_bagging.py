# -*- encoding: utf-8 -*-
"""tests.base.hier.test_bagging module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest
from dataclasses import (dataclass, astuple, asdict, fields, field,
                         FrozenInstanceError)
from hio.base import Tymist
from hio.base.hier import Bag, IceBag


def test_ice_bag():
    """Test IceBag class"""
    tymist = Tymist()

    assert IceBag._registry
    assert IceBag.__name__ in IceBag._registry
    assert IceBag._registry[IceBag.__name__] == IceBag

    assert IceBag._names == ("value", )
    flds = fields(IceBag)
    assert len(flds) == 1
    assert flds[0].name == 'value'

    b = IceBag()
    assert b._names == ("value", )
    assert b._tymth == None
    assert b._now == None
    assert b._tyme == None
    assert b.value == None

    assert b.__dataclass_params__.frozen == True
    assert hash(b) == hash(b)

    with pytest.raises(FrozenInstanceError):
        b.value = True

    with pytest.raises(FrozenInstanceError): # no non-field attrributes
        b.val = True

    with pytest.raises(TypeError):  # no item assignment
        b["val"] = True

    b = IceBag(value=10)
    assert b._names == ("value", )
    assert b._tymth == None
    assert b._now == None
    assert b._tyme == None
    assert b.value == 10

    b = IceBag(value=3, _tymth=tymist.tymen(), _tyme=1.0)
    assert b._names == ("value", )
    assert b._tymth == None
    assert b._now == None
    assert b._tyme == None
    assert b.value == 3

    with pytest.raises(AttributeError):
        b._update(value=7)

    # test _asdict
    d = b._asdict()
    assert d == {'value': 3}

    # test _astuple
    t = b._astuple()
    assert t == (3, )

    with pytest.raises(TypeError):
        b = IceBag(value=1, val=2)

    """Done Test"""


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

    assert b.__dataclass_params__.frozen == False
    assert hash(b) == hash(b)

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

    # Adding fields?
    with pytest.raises(TypeError):
        bag = Bag(value=5, test=6)

    bag = Bag(value=5)
    assert bag._names == ('value', )
    flds = fields(bag)
    assert len(flds) == 1
    bag.test = 6  # added attribute on the fly
    assert "test" not in bag._names
    flds = fields(bag)
    assert len(flds) == 1


    """Done Test"""


if __name__ == "__main__":
    test_ice_bag()
    test_bag()


