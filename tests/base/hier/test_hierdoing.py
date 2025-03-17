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
import inspect



from dataclasses import dataclass, astuple, asdict, field
from hio import hioing
from hio.help import helping
from hio.base import tyming

from hio.base.hier import Reat, Lode, Builder, Boxer, Box
from hio.base.hier import hierdoing
from hio.base.hier.hierdoing import exen

def test_reat():
    """Test regular expression Reat for attribute name """
    name = "hello"
    assert Reat.match(name)

    name = "_hello"
    assert Reat.match(name)

    name = "hell1"
    assert Reat.match(name)

    name = "1hello"
    assert not Reat.match(name)

    name = "hello.hello"
    assert not Reat.match(name)
    """Done Test"""


def test_lode_basic():
    """Basic test Lode class"""
    keys = ('a', 'b', 'c')
    key = '.'.join(keys)
    assert key == 'a.b.c'

    # test staticmethod .tokey()
    assert Lode.tokey(keys) == key
    assert Lode.tokey('a') == 'a'  # str unchanged
    assert Lode.tokey('a.b') == 'a.b'  # str unchanged
    assert Lode.tokey(keys)

    with pytest.raises(KeyError):
        key = Lode.tokey((1, 2, 3))

    with pytest.raises(KeyError):
        key = Lode.tokey(1)


    # Test staticmethod .tokeys()
    assert Lode.tokeys(key) == keys
    assert Lode.tokeys('') == ('', )
    assert Lode.tokeys('a') == ('a', )

    assert Lode.tokey(Lode.tokeys(key)) == key
    assert Lode.tokeys(Lode.tokey(keys)) == keys

    lode = Lode()  # defaults
    assert lode == {}

    assert isinstance(lode, dict)
    assert issubclass(Lode, dict)

    lode['a'] = 5
    lode['a_b'] = 6
    assert lode['a'] == 5
    assert 'a' in lode
    assert lode.get('a') == 5

    lode[keys] = 7
    assert list(lode.items()) == [('a', 5), ('a_b', 6), ('a.b.c', 7)]

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

    lode[''] = 10
    assert '' in lode
    assert lode[''] == 10


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

    lode = Lode([('a', 0), ('a.b', 1), ('a.b.c', 2)])
    assert list(lode.items()) == [('a', 0), ('a.b', 1), ('a.b.c', 2)]

    # test init with iterable using keys as tuples
    lode = Lode([(('a', ), 0), (('a', 'b'), 1), (('a','b', 'c'), 2)], d=4)
    assert list(lode.items()) == [('a', 0), ('a.b', 1), ('a.b.c', 2), ('d', 4)]

    # test init with dict using keys as tuples
    d = {}
    d[("a", )] = 0
    d[("a", "b")] = 1
    d[("a", "b", "c")] = 2
    lode = Lode(d, d=4)
    assert list(lode.items()) == [('a', 0), ('a.b', 1), ('a.b.c', 2), ('d', 4)]

    # test update with iterable using keys as tuples
    lode = Lode()
    lode.update([(('a', ), 0), (('a', 'b'), 1), (('a','b', 'c'), 2)], d=4)
    assert list(lode.items()) == [('a', 0), ('a.b', 1), ('a.b.c', 2), ('d', 4)]

    # test update with dict using keys as tuples
    d = {}
    d[("a", )] = 0
    d[("a", "b")] = 1
    d[("a", "b", "c")] = 2
    lode = Lode()
    lode.update(d, d=4)
    assert list(lode.items()) == [('a', 0), ('a.b', 1), ('a.b.c', 2), ('d', 4)]

    """Done Test"""


def test_builder_basic():
    """Basic test Builder class"""
    builder = Builder()  # defaults
    assert builder.name == 'builder'
    assert builder.lode == Lode()
    assert builder.boxer == None
    assert builder.box == None

    with pytest.raises(hioing.HierError):
        builder.name = "A.B"

    with pytest.raises(hioing.HierError):
        builder.name = "|builder"


def test_boxer_basic():
    """Basic test Boxer class"""
    boxer = Boxer()  # defaults
    assert boxer.tyme == None
    assert boxer.tymth == None
    assert boxer.name == 'boxer'
    assert boxer.lode == Lode()
    assert boxer.doer == None
    assert boxer.first == None
    assert boxer.pile == []
    assert boxer.box == None
    assert boxer.boxes == {}



    with pytest.raises(hioing.HierError):
        boxer.name = "A.B"

    with pytest.raises(hioing.HierError):
        boxer.name = ".boxer"


def test_box_basic():
    """Basic test Box class"""
    box = Box()  # defaults
    assert box.tyme == None
    assert box.tymth == None
    assert box.name == 'box'
    assert box.lode == Lode()
    assert box.boxer == None
    assert box.over == None
    assert box.unders == []

    assert box.nxt == None
    assert box.preacts == []
    assert box.beacts == []
    assert box.renacts == []
    assert box.enacts == []
    assert box.reacts == []
    assert box.tracts == []
    assert box.exacts == []
    assert box.rexacts == []

    assert box.pile == [box]
    assert box.spot == 0
    assert box.trail == '<box>'
    assert str(box) == "Box(<box>)"
    assert repr(box) == "Box(name='box')"

    assert isinstance(eval(repr(box)), Box)

    with pytest.raises(hioing.HierError):
        box.name = "A.B"

    with pytest.raises(hioing.HierError):
        box.name = ".box"

    """Done Test"""

def test_exen():
    """Test exen function for finding common/uncommon boxes in near far staks
    for computing exits, enters, rexits, renters on a transition
    """
    a = Box(name='a')
    b = Box(name='b')
    b.over = a
    a.unders.append(b)
    c = Box(name='c')
    c.over = b
    b.unders.append(c)
    d = Box(name='d')
    d.over = c
    c.unders.append(d)

    e = Box(name='e')
    e.over = c
    c.unders.append(e)
    f = Box(name='f')
    f.over = e
    e.unders.append(f)


    assert repr(a) == "Box(name='a')"

    assert str(a) == "Box(<a>b>c>d)"
    assert a.pile == [a, b, c, d]

    assert str(b) == "Box(a<b>c>d)"
    assert b.pile == [a, b, c, d]

    assert str(c) == "Box(a<b<c>d)"
    assert c.pile == [a, b, c, d]

    assert str(d) == "Box(a<b<c<d>)"
    assert d.pile == [a, b, c, d]

    assert str(e) == "Box(a<b<c<e>f)"
    assert e.pile == [a, b, c, e, f]

    assert str(f) == "Box(a<b<c<e<f>)"
    assert f.pile == [a, b, c, e, f]

    assert a.pile == b.pile == c.pile == d.pile
    assert e.pile == f.pile


    # test exen
    exits, enters, rexits, renters = exen(d, e)
    assert exits == [d]
    assert enters == [e, f]
    assert rexits == [c, b, a]
    assert renters == [a, b, c]

    exits, enters, rexits, renters = exen(d, f)
    assert exits == [d]
    assert enters == [e, f]
    assert rexits == [c, b, a]
    assert renters == [a, b, c]

    exits, enters, rexits, renters = exen(a, e)
    assert exits == [d]
    assert enters == [e, f]
    assert rexits == [c, b, a]
    assert renters == [a, b, c]

    exits, enters, rexits, renters = exen(c, b)
    assert exits == [d, c, b]
    assert enters == [b, c, d]
    assert rexits == [a]
    assert renters == [a]

    exits, enters, rexits, renters = exen(c, c)
    assert exits == [d, c]
    assert enters == [c, d]
    assert rexits == [b, a]
    assert renters == [a, b]

    exits, enters, rexits, renters = exen(c, d)
    assert exits == [d]
    assert enters == [d]
    assert rexits == [c, b, a]
    assert renters == [a, b, c]

    exits, enters, rexits, renters = exen(e, d)
    assert exits == [f, e]
    assert enters == [d]
    assert rexits == [c, b, a]
    assert renters == [a, b, c]

    exits, enters, rexits, renters = exen(f, f)
    assert exits == [f]
    assert enters == [f]
    assert rexits == [e, c, b, a]
    assert renters == [a, b, c, e]

    """Done Test"""



def test_inspect_stuff():
    """Test inpect stuff to see how works"""

    def f(name, over):
        av = inspect.getargvalues(inspect.currentframe())
        """ArgInfo(args=['name', 'over'],
                   varargs=None,
                   keywords=None,
                   locals={'name': 'test', 'over': 'up',
                   'av': ...)   """
        pass

    sig = inspect.signature(f)

    f(name="test", over="up")

    _name = ''
    _boxes = {}  # default boxes dict
    _over = None # default top box

    def be(name=None, over=None):
        # '_name' is only in locals because it is referenced in the assignment
        # statement below. If _name is never referenced inside function be()
        # then it never makes it into locals(). The interpreter only populates
        # locals with varialbls in local scope it needs not all variables in
        # local scope it could access if it needed to.
        x = _name
        assert '_name' in locals()

        #l = locals() # makes copy of locals
        # l['name'] = 'big'
        #g = globals()  # makes copy of globals
        assert '_name' not in globals()

    be(name="test", over="up")

    global _blame
    assert not '_blame' in globals()  # not in globals until assigned a value
    _blame = ''
    assert '_blame' in globals()  # why is this

    def g(name=None, over=None):
        global _blame

        assert not '_blame' in locals()
        assert '_blame' in globals()  # unless assigned someplace else
        x = _blame

    g(name="test", over="up")

    _fame = ''  # not a global at this point
    assert not '_fame' in globals()

    def h(name=None, over=None):
        global _fame

        assert not '_fame' in globals()
        _fame = 'why'  # now a global
        assert '_fame' in globals()

    h(name="test", over="up")

    """Done Test"""

def test_be_box():
    """Test be function for adding box to box work

    Note: name mangling only happens inside a class definition.
    """
    global _boxes, _over, _prefix
    _boxes = {}  # default boxes dict now a global
    _over = None # default top box now a global
    _prefix = '_box'  #  default box name prefix now a global

    def be(name=None, over=None):
        global _boxes, _over, _prefix

        assert '_prefix' in globals()
        x = _prefix

    be(name="test", over="up")


    """Done Test"""



if __name__ == "__main__":
    test_reat()
    test_lode_basic()
    test_builder_basic()
    test_boxer_basic()
    test_box_basic()
    test_exen()
    test_inspect_stuff()
    test_be_box()
