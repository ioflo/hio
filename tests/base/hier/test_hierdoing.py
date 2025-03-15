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
from hio.base.hier import hierdoing
from hio.base.hier.hierdoing import Lode, Builder, Boxer, Box

def test_lode_basic():
    """Basic test Lode class"""
    lode = Lode()  # defaults
    assert lode == {}

    assert isinstance(lode, dict)
    assert issubclass(Lode, dict)

    lode['a'] = 5
    lode['a_b'] = 6
    assert lode['a'] == 5
    assert 'a' in lode
    assert lode.get('a') == 5

    keys = ('a', 'b', 'c')
    key = '_'.join(keys)
    assert key == 'a_b_c'

    lode[keys] = 7
    assert list(lode.items()) == [('a', 5), ('a_b', 6), ('a_b_c', 7)]

    assert lode[keys] == 7
    assert keys in lode
    assert lode.get(keys) == 7

    assert lode[key] == 7
    assert key in lode
    assert lode.get(key) == 7

    lode[key] = 8
    assert lode[keys] == 8

    assert lode.get('c') == None
    assert lode.get(("b", "c")) == None

    with pytest.raises(KeyError):
        lode['c']

    with pytest.raises(KeyError):
        lode[1] = 'A'

    with pytest.raises(KeyError):
        lode[("a", 2)] = 'B'

    with pytest.raises(KeyError):
        lode[("a", 2)]

    lode = Lode(a=0, a_b=1, a_b_c=2)
    assert list(lode.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2)]

    assert Lode.tokeys(key) == keys
    assert Lode.tokeys('') == ('', )
    assert Lode.tokeys('a') == ('a', )

    lode[''] = 10
    assert '' in lode
    assert lode[''] == 10

    """Done Test"""


def test_builder_basic():
    """Basic test Builder class"""
    builder = Builder()  # defaults
    assert builder.name == 'builder'
    assert builder.lode == Lode()
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
    assert boxer.lode == Lode()
    assert boxer.doer == None
    assert boxer.first == None
    assert boxer.stak == []
    assert boxer.box == None
    assert boxer.boxes == {}

    with pytest.raises(hioing.HierError):
        boxer.name = "A_B"

    with pytest.raises(hioing.HierError):
        boxer.name = "_boxer"


def test_box_basic():
    """Basic test Box class"""
    box = Box()  # defaults
    assert box.name == 'box'
    assert box.lode == Lode()
    assert box.boxer == None
    assert box.over == None
    assert box.unders == []
    assert box.nxt == None
    assert box.stak == []
    assert box.preacts == []
    assert box.beacts == []
    assert box.renacts == []
    assert box.enacts == []
    assert box.reacts == []
    assert box.tracts == []
    assert box.exacts == []
    assert box.rexacts == []

    with pytest.raises(hioing.HierError):
        box.name = "A_B"

    with pytest.raises(hioing.HierError):
        box.name = "_box"


    """Done Test"""

if __name__ == "__main__":
    test_lode_basic()
    test_builder_basic()
    test_boxer_basic()
    test_box_basic()
