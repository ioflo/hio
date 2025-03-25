# -*- encoding: utf-8 -*-
"""
tests.base.hier.test_hiering module

"""
from __future__ import annotations  # so type hints of classes get resolved later

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
from hio.base.hier import Reat, Haul, Maker, Boxer, Box
from hio.base.hier import hiering
from hio.base.hier.hiering import exen, modify
from hio.base.hier.hiering import Actage, Registry, Actor, actify


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


def test_act_registry_basic():
    """Test Actor registry base stuff class and subclasses"""

    assert Registry == dict(Actor=Actor)

    assert Actor.__name__ == 'Actor'

    assert Actor.Index == 0

    actor = Actor()
    assert actor.name == 'Actor0'
    assert hasattr(actor, 'name')   # hasattr works for properties and attributes

    act = Actage(act=actor, kwa={})
    act.act(**act.kwa)


def test_haul_basic():
    """Basic test Haul class"""
    keys = ('a', 'b', 'c')
    key = '.'.join(keys)
    assert key == 'a.b.c'

    # test staticmethod .tokey()
    assert Haul.tokey(keys) == key
    assert Haul.tokey('a') == 'a'  # str unchanged
    assert Haul.tokey('a.b') == 'a.b'  # str unchanged
    assert Haul.tokey(keys)

    with pytest.raises(KeyError):
        key = Haul.tokey((1, 2, 3))

    with pytest.raises(KeyError):
        key = Haul.tokey(1)


    # Test staticmethod .tokeys()
    assert Haul.tokeys(key) == keys
    assert Haul.tokeys('') == ('', )
    assert Haul.tokeys('a') == ('a', )

    assert Haul.tokey(Haul.tokeys(key)) == key
    assert Haul.tokeys(Haul.tokey(keys)) == keys

    haul = Haul()  # defaults
    assert haul == {}

    assert isinstance(haul, dict)
    assert issubclass(Haul, dict)

    haul['a'] = 5
    haul['a_b'] = 6
    assert haul['a'] == 5
    assert 'a' in haul
    assert haul.get('a') == 5

    haul[keys] = 7
    assert list(haul.items()) == [('a', 5), ('a_b', 6), ('a.b.c', 7)]

    assert haul[keys] == 7
    assert keys in haul
    assert haul.get(keys) == 7

    assert haul[key] == 7
    assert key in haul
    assert haul.get(key) == 7

    haul[key] = 8
    assert haul[keys] == 8

    del haul[keys]
    assert key not in haul

    with pytest.raises(KeyError):
        del haul[key]

    with pytest.raises(KeyError):
        del haul[keys]

    haul[keys] = 8
    del haul[key]

    with pytest.raises(KeyError):
        del haul[keys]

    with pytest.raises(KeyError):
        del haul[key]



    assert haul.get('c') == None
    assert haul.get(("b", "c")) == None

    haul[''] = 10
    assert '' in haul
    assert haul[''] == 10


    with pytest.raises(KeyError):
        haul['c']

    with pytest.raises(KeyError):
        haul[1] = 'A'

    with pytest.raises(KeyError):
        haul[("a", 2)] = 'B'

    with pytest.raises(KeyError):
        haul[("a", 2)]

    haul = Haul(a=0, a_b=1, a_b_c=2)
    assert list(haul.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2)]

    haul = Haul([('a', 0), ('a.b', 1), ('a.b.c', 2)])
    assert list(haul.items()) == [('a', 0), ('a.b', 1), ('a.b.c', 2)]

    # test init with iterable using keys as tuples
    haul = Haul([(('a', ), 0), (('a', 'b'), 1), (('a','b', 'c'), 2)], d=4)
    assert list(haul.items()) == [('a', 0), ('a.b', 1), ('a.b.c', 2), ('d', 4)]

    # test init with dict using keys as tuples
    d = {}
    d[("a", )] = 0
    d[("a", "b")] = 1
    d[("a", "b", "c")] = 2
    haul = Haul(d, d=4)
    assert list(haul.items()) == [('a', 0), ('a.b', 1), ('a.b.c', 2), ('d', 4)]

    # test update with iterable using keys as tuples
    haul = Haul()
    haul.update([(('a', ), 0), (('a', 'b'), 1), (('a','b', 'c'), 2)], d=4)
    assert list(haul.items()) == [('a', 0), ('a.b', 1), ('a.b.c', 2), ('d', 4)]

    # test update with dict using keys as tuples
    d = {}
    d[("a", )] = 0
    d[("a", "b")] = 1
    d[("a", "b", "c")] = 2
    haul = Haul()
    haul.update(d, d=4)
    assert list(haul.items()) == [('a', 0), ('a.b', 1), ('a.b.c', 2), ('d', 4)]

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
    def d(name=None, over=None):
        # '_name' is only in locals because it is referenced in the assignment
        # statement below. If _name is never referenced inside function be()
        # then it never makes it into locals(). The interpreter only populates
        # locals with varialbls in local scope it needs not all variables in
        # local scope it could access if it needed to.
        x = _name
        assert '_name' in locals()
        assert '_name' not in globals()

    d(name="test", over="up")
    assert '_name' not in globals()
    assert _name == ''

    _game = ''  # nonlocal scope since not at module level global scope is module scope
    def e(name=None, over=None):
        _game = "where"
        x = _game
        assert '_game' in locals()
        assert '_game' not in globals()

    e(name="test", over="up")
    assert '_game' not in globals()
    assert _game == ''

    _came = 'outside'  # nonlocal scope since not at module level global scope is module scope
    def c(name=None, over=None):
        nonlocal _came
        assert _came == 'outside'
        _came = "inside"

        assert '_came' in locals()
        assert '_came' not in globals()

    c(name="test", over="up")
    assert '_came' not in globals()
    assert _came == 'inside'


    global _blame  # module scope vs nonlocal scope
    assert not '_blame' in globals()  # not in globals until assigned a value
    _blame = ''
    assert '_blame' in globals()  # why is this

    def g(name=None, over=None):
        global _blame

        assert not '_blame' in locals()
        assert '_blame' in globals()  # unless assigned someplace else
        x = _blame
        _blame = "who"

    g(name="test", over="up")
    assert '_blame' in globals()
    assert _blame == "who"


    _fame = ''  # not a global at this point
    assert '_fame' not in globals()

    def h(name=None, over=None):
        global _fame

        assert not '_fame' in globals()
        _fame = 'why'  # now a global
        assert '_fame' in globals()

    h(name="test", over="up")
    assert _fame not in globals()
    assert _fame == ''  # not changed outside if not declared in global outside


    # double nested globals
    def j():
        global _tame
        assert _tame == 'here'
        _tame = "far"
        assert '_tame' in globals()

    assert '_tame' not in globals()

    global _tame
    _tame = 'here'
    assert '_tame' in globals()

    def i(name=None, over=None):
        j()
    i()
    assert '_tame' in globals()
    assert _tame == "far"


    def k():
        def l():
            global _tame
            assert _tame == 'far'
            _tame = "near"
            assert '_tame' in globals()  # closure?
        l()
    k()
    assert '_tame' in globals()
    assert _tame == "near"

    """Done Test"""



if __name__ == "__main__":
    test_reat()
    test_act_registry_basic()
    test_haul_basic()
    test_exen()
    test_inspect_stuff()
