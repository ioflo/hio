# -*- encoding: utf-8 -*-
"""
tests.base.hier.test_needing module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest

from hio.base.hier import Need, Bag, Hold



def test_need_basic():
    """Test Need class"""

    need = Need()
    assert need.hold == Hold()
    assert need.expr == 'True'
    assert need.compiled == True

    assert need() == True  # lazy eval

    mine = Hold()
    need = Need(hold=mine)
    assert need.hold == mine
    assert need.expr == 'True'
    assert need.compiled == True

    assert need() == True  # lazily eval


    mine.cycle = Bag(value=5)
    mine.turn = Bag(value=2)
    need.expr = "H.cycle.value > 3 and H.turn.value <= 2"
    assert not need.compiled  # lazy compile
    assert need()
    assert need.compiled

    mine.cycle.value = 3
    assert not need()

    """Done Test"""

if __name__ == "__main__":
    test_need_basic()

