# -*- encoding: utf-8 -*-
"""
tests.base.hier.test_boxing module

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
from hio.base.hier import Reat, Haul, Box, Boxer, Maker
from hio.base.hier import hiering
from hio.base.hier.hiering import exen, modify


def test_box_basic():
    """Basic test Box class"""
    box = Box()  # defaults
    assert box.tyme == None
    assert box.tymth == None
    assert box.name == 'box'
    assert isinstance(box.bags, Haul)
    assert box.over == None
    assert box.unders == []

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


def test_boxer_basic():
    """Basic test Boxer class"""
    boxer = Boxer()  # defaults
    assert boxer.tyme == None
    assert boxer.tymth == None
    assert boxer.name == 'boxer'
    assert boxer.bags == Haul()
    assert boxer.boxes == {}
    assert boxer.first == None
    assert boxer.doer == None

    assert boxer.pile == []
    assert boxer.box == None

    prep = boxer.prep  # make alias
    prep()


    with pytest.raises(hioing.HierError):
        boxer.name = "A.B"

    with pytest.raises(hioing.HierError):
        boxer.name = ".boxer"


def test_boxer_make():
    """Test make method of Boxer and modify wrapper"""
    def fun(be, do):
        be(name='top')
        be(over='top')
        be()
        b = be()
        be(over=b)
        do(deed="sing")
        do()

    boxer = Boxer()
    assert boxer.boxes == {}
    mods = boxer.make(fun)
    assert boxer.boxes
    assert len(boxer.boxes) == 5
    assert list(boxer.boxes) == ['top', 'box0', 'box1', 'box2', 'box3']
    assert str(boxer.boxes['top']) == 'Box(<top>box0)'
    assert str(boxer.boxes['box3']) == 'Box(top<box2<box3>)'
    assert mods["bxpre"] == 'box'
    assert mods["bxidx"] == 5
    assert mods["over"].name == 'box2'
    assert mods['box'].name == 'box3'

    """Done Test"""



def test_maker_basic():
    """Basic test Maker class"""
    maker = Maker()  # defaults
    assert maker.name == 'maker'
    assert maker.bags == Haul()
    assert maker.boxer == None
    assert maker.box == None

    with pytest.raises(hioing.HierError):
        maker.name = "A.B"

    with pytest.raises(hioing.HierError):
        maker.name = "|maker"



def test_concept_be_box_nonlocal():
    """Test concept for be function for adding box to box work

    """
    #global B, _bags, _boxer, _boxes, _box, _over, _proem, _index

    B = _bags = Haul()
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
            B, _bags: (Haul): data haul for this box work
            _boxer (Boxer | None): instance to which this box belongs
            _boxes (dict): map of boxes in this box work
            _box (Box | None): current box in box work. None if not yet a box
            _over (Box | None): current over Box in box work. None if top level


        """
        #global B, _bags, _boxer, _boxes, _box, _over, _proem, _index
        nonlocal B, _bags, _boxer, _boxes, _box, _over, _proem, _index

        if not name:  # empty or None
            if name is None:
                name = _proem + str(_index)
                _index += 1
                while name in _boxes:
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
        if _box:
            _box._next = box #update prior box lexical next to this box
        _box = box  # update current box
        return box

    assert _boxes == {}
    assert _box == None
    assert _over == None
    assert _index == 0

    btop = be(name="top")
    assert _box == btop
    assert _over == None
    assert not btop._next

    b0 = be(over="top")
    assert _box == b0
    assert _over == btop
    assert btop._next == b0

    b1 = be()
    assert _box == b1
    assert _over == btop
    assert b0._next == b1

    b2 = be(over=b1)
    assert _box == b2
    assert _over == b1
    assert b1._next == b2

    b3 = be(over=None)
    assert _box == b3
    assert _over == None
    assert b2._next == b3

    b4 = be()
    assert _box == b4
    assert _over == None
    assert b3._next == b4

    b5 = be(over="_box0")
    assert _box == b5
    assert _over == b0
    assert b4._next == b5

    b6 = be()
    assert _box == b6
    assert _over == b0
    assert b5._next == b6
    assert not b6._next

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

def test_concept_be_box_global():
    """Test concept for be function for adding box to box work

    """
    global B, _bags, _boxer, _boxes, _box, _over, _proem, _index

    B = _bags = Haul()
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
            B, _bags: (Haul): data haul for this box work
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
                while name in _boxes:
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
        if _box:
            _box._next = box #update prior box lexical next to this box
        _box = box  # update current box
        return box

    assert _boxes == {}
    assert _box == None
    assert _over == None
    assert _index == 0

    btop = be(name="top")
    assert _box == btop
    assert _over == None
    assert not btop._next

    b0 = be(over="top")
    assert _box == b0
    assert _over == btop
    assert btop._next == b0

    b1 = be()
    assert _box == b1
    assert _over == btop
    assert b0._next == b1

    b2 = be(over=b1)
    assert _box == b2
    assert _over == b1
    assert b1._next == b2

    b3 = be(over=None)
    assert _box == b3
    assert _over == None
    assert b2._next == b3

    b4 = be()
    assert _box == b4
    assert _over == None
    assert b3._next == b4

    b5 = be(over="_box0")
    assert _box == b5
    assert _over == b0
    assert b4._next == b5

    b6 = be()
    assert _box == b6
    assert _over == b0
    assert b5._next == b6
    assert not b6._next

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
    test_box_basic()
    test_boxer_basic()
    test_boxer_make()
    test_maker_basic()
    test_concept_be_box_nonlocal()
    test_concept_be_box_global()
