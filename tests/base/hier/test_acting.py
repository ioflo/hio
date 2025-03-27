# -*- encoding: utf-8 -*-
"""
tests.base.hier.test_acting module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest

from hio.base.hier import ActBase, actify, Act, Tract, Need



def test_act_basic():
    """Test Act class"""
    # clear registries for debugging
    Act._clear()


    act = Act()
    assert "Act" in Act.Registry
    assert Act.Registry["Act"] == Act

    assert act.name == "Act0"
    assert act.Index == 1
    assert act.Names[act.name] == act
    assert act.dest == None
    assert act.need == None

    assert not act()

    """Done Test"""


def test_tract_basic():
    """Test Tract class"""
    # clear registries for debugging
    Tract._clear()


    tract = Tract()
    assert "Tract" in Tract.Registry
    assert Tract.Registry["Tract"] == Tract

    assert tract.name == "Tract0"
    assert tract.Index == 1
    assert tract.Names[tract.name] == tract
    assert tract.dest == None
    assert isinstance(tract.need, Need)
    assert tract.need()

    assert not tract()  # since not created default .dest

    """Done Test"""

if __name__ == "__main__":
    test_act_basic()
    test_tract_basic()
