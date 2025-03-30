# -*- encoding: utf-8 -*-
"""
tests.base.hier.test_needing module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest

from hio.base.hier import Need
from hio.help import Mine


def test_need_basic():
    """Test Need class"""

    need = Need()
    assert need.mine == Mine()
    assert need.terms == tuple()
    assert need.strict == False
    assert need.composed == False
    assert need.compiled == False

    assert need() == True  # lazy compose, compile and eval

    mine = Mine()
    need = Need(mine=mine)
    assert need.mine == mine
    assert need.terms == tuple()
    assert need.strict == False
    assert need.composed == False
    assert need.compiled == False

    assert need() == True  # lazy compose, compile and eval


    """Done Test"""

if __name__ == "__main__":
    test_need_basic()

