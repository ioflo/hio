# -*- encoding: utf-8 -*-
"""
tests.base.hier.test_acting module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest

from hio.base.hier import Act, actify
from hio.base.hier.acting import Tract


def test_tract_basic():
    """Test Tract class and subclasses basically"""
    tract = Tract()
    assert "Tract" in Tract.Registry
    assert Tract.Registry["Tract"] == Tract

    assert tract.name == "Tract0"
    assert tract.Index == 1
    assert tract.Names[tract.name] == tract
    assert tract.dest == None
    assert tract.need == None

    assert not tract()

    """Done Test"""

if __name__ == "__main__":
    test_tract_basic()
