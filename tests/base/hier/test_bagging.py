# -*- encoding: utf-8 -*-
"""tests.base.hier.test_bagging module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest

from hio.base.hier import BagDom, Bag



def test_bagdom():
    """Test BagDom class"""
    b = BagDom()
    assert isinstance(b, BagDom)
    assert b._tyme == None

    b = BagDom(_tyme=0.0)
    assert b._tyme == 0.0

    b._tyme = 1.0
    assert b._tyme == 1.0


    """Done Test"""

def test_bag():
    """Test Bag class"""
    b = Bag()
    assert b._tyme == None
    assert b.value == None

    b = Bag(_tyme=1.0, value=10)
    assert b._tyme == 1.0
    assert b.value == 10

    b.value = 2
    assert b.value == 2


    """Done Test"""


if __name__ == "__main__":
    test_bagdom()
    test_bag()
