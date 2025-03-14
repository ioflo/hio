# -*- encoding: utf-8 -*-
"""
tests.base.test_hierdoing module

"""
import pytest

import os
import sys
import time
import inspect
import types
import logging
import json

from dataclasses import dataclass, astuple, asdict, field
from hio import hioing
from hio.help import helping
from hio.base import tyming
from hio.base import hierdoing
from hio.base.hierdoing import Builder, Boxer, Box


def test_builder_basic():
    """Basic test Builder class"""
    builder = Builder()  # defaults
    assert builder.name == 'builder'
    assert builder.lode == {}
    assert builder.boxer == None
    assert builder.box == None

    with pytest.raises(hioing.HierError):
        builder.name = "A_B"

    with pytest.raises(hioing.HierError):
        builder.name = "_builder"


def test_boxer_basic():
    """Basic test Boxer class"""
    boxer = Boxer()  # defaults
    assert boxer.name == 'boxer'
    assert boxer.lode == {}
    assert boxer.first == None
    assert boxer.boxes == {}

    with pytest.raises(hioing.HierError):
        boxer.name = "A_B"

    with pytest.raises(hioing.HierError):
        boxer.name = "_boxer"


def test_box_basic():
    """Basic test Box class"""
    box = Box()  # defaults
    assert box.name == 'box'
    assert box.lode == {}
    assert box.boxer == None
    assert box.over == None
    assert box.unders == []
    assert box.nxt == None
    assert box.beacts == []
    assert box.renacts == []
    assert box.enacts == []
    assert box.reacts == []
    assert box.preacts == []
    assert box.tracts == []
    assert box.exacts == []
    assert box.rexacts == []
    assert box.auxes == []

    with pytest.raises(hioing.HierError):
        box.name = "A_B"

    with pytest.raises(hioing.HierError):
        box.name = "_box"


    """Done Test"""

if __name__ == "__main__":
    test_builder_basic()
    test_boxer_basic()
    test_box_basic()
