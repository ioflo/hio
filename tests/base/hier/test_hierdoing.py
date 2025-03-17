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
from hio.base.hier import Reat, Lode, Maker, Boxer, Box
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


def test_maker_basic():
    """Basic test Maker class"""
    maker = Maker()  # defaults
    assert maker.name == 'maker'
    assert maker.bags == Lode()
    assert maker.boxer == None
    assert maker.box == None

    with pytest.raises(hioing.HierError):
        maker.name = "A.B"

    with pytest.raises(hioing.HierError):
        maker.name = "|maker"


def test_boxer_basic():
    """Basic test Boxer class"""
    boxer = Boxer()  # defaults
    assert boxer.tyme == None
    assert boxer.tymth == None
    assert boxer.name == 'boxer'
    assert boxer.bags == Lode()
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
    assert box.bags == Lode()
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

    """Done Test"""

def test_be_box():
    """Test concept for be function for adding box to box work

    """
    global B, _bags, _boxer, _boxes, _box, _over, _proem, _index

    B = _bags = Lode()
    _boxer = None
    _boxes = {}  # default boxes dict now a global
    _box = None
    _over = None # default top box now a global
    _proem = '_box'  #  default box name prefix now a global
    _index = 0  # default box name index

    def be(name: None|str=None, over: None|str|Box="")->Box:
        """Make a box and add to box work

        Parameters:
            name (None | str): when None then create name from _proem and _index
                               if non-empty string then use provided
                               otherwise raise exception

            over (None | str | Box): over box for new box.
                                    when str then name of new over box
                                    when box then actual over box
                                    when None then no over box (top level)
                                    when empty then same level use _over

        Globals:
            B, _bags: (Lode): data lode for this box work
            _boxer (Boxer | None): instance to which this box belongs
            _boxes (dict): map of boxes in this box work
            _box (Box | None): current box in box work. None if not yet a box
            _over (Box | None): current over Box in box work. None if top level


        """
        global B, _bags, _boxer, _boxes, _box, _over, _proem, _index

        if not name:  # empty or None
            if name is None:
                name = _proem + str(_index)
                _index += 1
            else:
                raise hioing.HierError(f"Missing name.")

        if name in _boxes:  # duplicate name
            raise hioing.HierError(f"Non-unique box {name=}.")

        if over is not None:  # not at top level
            if isinstance(over, str):
                if not over:  # empty string
                    over = _over  # same level
                else:  # resolvable string
                    try:
                        over = _boxes[over]  # resolve
                    except KeyError as ex:
                        raise hioing.HierError(f"Under box={name} defined before"
                                               f"its {over=}.") from ex

            elif over.name not in _boxes:  # stray over box
                _boxes[over.name] = over  # add to boxes

        box = Box(name=name, over=over, bags=_bags, boxer=_boxer)
        if box.over is not None:  # not at top level
            box.over.unders.append(box)  # add to over.unders list

        _over = over  # update current level
        _boxes[box.name] = box  # update box work
        _box = box  # update current box
        return box

    assert _boxes == {}
    assert _box == None
    assert _over == None
    assert _index == 0

    btop = be(name="top")
    assert _box == btop
    assert _over == None

    b0 = be(over="top")
    assert _box == b0
    assert _over == btop

    b1 = be()
    assert _box == b1
    assert _over == btop

    b2 = be(over=b1)
    assert _box == b2
    assert _over == b1

    b3 = be(over=None)
    assert _box == b3
    assert _over == None

    b4 = be()
    assert _box == b4
    assert _over == None

    b5 = be(over="_box0")
    assert _box == b5
    assert _over == b0

    b6 = be()
    assert _box == b6
    assert _over == b0

    assert _index == 7


    assert _boxes == {'top': btop,
                    '_box0': b0,
                    '_box1': b1,
                    '_box2': b2,
                    '_box3': b3,
                    '_box4': b4,
                    '_box5': b5,
                    '_box6': b6,}

    assert str(btop) == 'Box(<top>_box0>_box5)'
    assert str(b0) == 'Box(top<_box0>_box5)'
    assert str(b1) == 'Box(top<_box1>_box2)'
    assert str(b2) == 'Box(top<_box1<_box2>)'
    assert str(b3) == 'Box(<_box3>)'
    assert str(b4) == 'Box(<_box4>)'
    assert str(b5) == 'Box(top<_box0<_box5>)'
    assert str(b6) == 'Box(top<_box0<_box6>)'


    """Done Test"""



if __name__ == "__main__":
    test_reat()
    test_lode_basic()
    test_maker_basic()
    test_boxer_basic()
    test_box_basic()
    test_exen()
    test_inspect_stuff()
    test_be_box()
