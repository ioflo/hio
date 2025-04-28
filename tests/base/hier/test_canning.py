# -*- encoding: utf-8 -*-
"""tests.base.hier.test_canning module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest
import dataclasses
from hio.base import Tymist
from hio.base.hier import CanBase


def test_canbase():
    """Test CanBase class"""
    tymist = Tymist()

    assert CanBase._registry
    assert CanBase.__name__ in CanBase._registry
    assert CanBase._registry[CanBase.__name__] == CanBase

    assert CanBase._names == ()
    # no fields just InitVar and ClassVar attributes
    fields = dataclasses.fields(CanBase)
    assert len(fields) == 0

    c = CanBase()  # defaults
    assert isinstance(c, CanBase)
    assert c._names == ()
    assert c._tymth == None
    assert c._now == None
    assert c._tyme == None
    assert c._sdb == None
    assert c._key == None

    c = CanBase(_tymth=tymist.tymen())
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


if __name__ == "__main__":
    test_canbase()
