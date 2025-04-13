# -*- encoding: utf-8 -*-
"""
tests.base.hier.test_needing module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest

from hio.base.hier import Need, Bag
from hio.help import Mine


def test_need_basic():
    """Test Need class"""

    need = Need()
    assert need.mine == Mine()
    assert need.expr == 'True'
    assert need.compiled == False

    assert need() == True  # lazy compose, compile and eval

    mine = Mine()
    need = Need(mine=mine)
    assert need.mine == mine
    assert need.expr == 'True'
    assert need.compiled == False

    assert need() == True  # lazily compile and then eval


    mine.cycle = Bag(value=5)
    mine.turn = Bag(value=2)
    need.expr = "M.cycle.value > 3 and M.turn.value <= 2"
    assert not need.compiled
    assert need()
    assert need.compiled

    mine.cycle.value = 3
    assert not need()




    """Done Test"""

if __name__ == "__main__":
    test_need_basic()

