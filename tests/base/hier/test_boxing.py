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
from hio.help import helping, modify, Mine, Renam
from hio.base import Tymist
from hio.base.hier import Box, Boxer, Maker, ActBase, Act, EndAct, Bag




def test_box_basic():
    """Basic test Box class"""
    box = Box()  # defaults
    assert box.tyme == None
    assert box.tymth == None
    assert box.name == 'box'
    assert isinstance(box.mine, Mine)
    assert box.over == None
    assert box.unders == []

    assert box.preacts == []
    assert box.remacts == []
    assert box.renacts == []
    assert box.enmacts == []
    assert box.enacts == []
    assert box.reacts == []
    assert box.tacts == []
    assert box.tracts == []
    assert box.quacts == []
    assert box.requacts == []

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



def test_boxer_quen():
    """Test exen function for finding common/uncommon boxes in near far staks
    for computing exits, entries, requits, rentries on a transition
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


    # test exen staticmethod
    quen = Boxer.quen  # exen is staticmethod of Boxer

    quits, entries, requits, rentries = quen(d, e)
    assert quits == [d]
    assert entries == [e, f]
    assert requits == [c, b, a]
    assert rentries == [a, b, c]

    quits, entries, requits, rentries = quen(d, f)
    assert quits == [d]
    assert entries == [e, f]
    assert requits == [c, b, a]
    assert rentries == [a, b, c]

    quits, entries, requits, rentries = quen(a, e)
    assert quits == [d]
    assert entries == [e, f]
    assert requits == [c, b, a]
    assert rentries == [a, b, c]

    quits, entries, requits, rentries = quen(c, b)
    assert quits == [d, c, b]
    assert entries == [b, c, d]
    assert requits == [a]
    assert rentries == [a]

    quits, entries, requits, rentries = quen(c, c)
    assert quits == [d, c]
    assert entries == [c, d]
    assert requits == [b, a]
    assert rentries == [a, b]

    quits, entries, requits, rentries = quen(c, d)
    assert quits == [d]
    assert entries == [d]
    assert requits == [c, b, a]
    assert rentries == [a, b, c]

    quits, entries, requits, rentries = quen(e, d)
    assert quits == [f, e]
    assert entries == [d]
    assert requits == [c, b, a]
    assert rentries == [a, b, c]

    quits, entries, requits, rentries = quen(f, f)
    assert quits == [f]
    assert entries == [f]
    assert requits == [e, c, b, a]
    assert rentries == [a, b, c, e]

    """Done Test"""



def test_boxer_basic():
    """Basic test Boxer class"""

    tymist = Tymist()

    boxer = Boxer()  # defaults
    assert boxer.tyme == None
    assert boxer.tymth == None
    assert boxer.name == 'boxer'
    assert boxer.mine == Mine()
    assert boxer.doer == None

    assert boxer.boxes == {}
    assert boxer.first == None
    assert boxer.box == None
    assert boxer.rentries == []
    assert boxer.entries == []

    with pytest.raises(hioing.HierError):
        boxer.name = "A.B"

    with pytest.raises(hioing.HierError):
        boxer.name = ".boxer"

    boxer.wind(tymist.tymen())
    assert boxer.tymth
    assert boxer.tyme == tymist.tyme == 0.0

    boxer.mine["test"] = Bag()
    assert boxer.mine.test.value == None
    assert boxer.mine.test._tymth == None
    assert boxer.mine.test._now == None
    assert boxer.mine.test._tyme == None

    boxer.wind(tymist.tymen())
    assert boxer.mine.test.value == None
    assert boxer.mine.test._tymth
    assert boxer.mine.test._now == 0.0 == tymist.tyme
    assert boxer.mine.test._tyme == None

    boxer.mine.test.value = 1
    assert boxer.mine.test.value == 1
    assert boxer.mine.test._tymth
    assert boxer.mine.test._now == 0.0 == tymist.tyme
    assert boxer.mine.test._tyme == 0.0

    boxer.mine["best"] = Bag(_tymth=tymist.tymen())
    assert boxer.mine.best.value == None
    assert boxer.mine.best._tymth
    assert boxer.mine.best._now == 0.0
    assert boxer.mine.best._tyme == None

    boxer.mine.best.value = 1
    assert boxer.mine.best.value == 1
    assert boxer.mine.best._tyme == 0.0

    """Done Test"""


def test_boxer_make():
    """Test make method of Boxer and modify wrapper"""
    def fun(bx, go, do, on, *pa):
        bx(name='top')
        bx(over='top')
        bx()
        b = bx()
        do()
        bx(over=b)
        do(deed="end")



    assert "end" in ActBase.Registry

    boxer = Boxer()
    assert boxer.boxes == {}
    boxer.first = 'top'
    mods = boxer.make(fun)
    assert isinstance(boxer.first, Box)
    assert boxer.first == boxer.boxes['top']
    assert boxer.boxes
    assert len(boxer.boxes) == 5
    assert list(boxer.boxes) == ['top', 'box0', 'box1', 'box2', 'box3']
    assert str(boxer.boxes['top']) == 'Box(<top>box0)'
    assert str(boxer.boxes['box3']) == 'Box(top<box2<box3>)'
    assert mods["bxpre"] == 'box'
    assert mods["bxidx"] == 4
    assert mods["over"].name == 'box2'
    assert mods['box'].name == 'box3'
    assert isinstance(boxer.boxes['box2'].enacts[0], Act)
    assert isinstance(boxer.boxes['box3'].enacts[0], EndAct)

    for name, box in boxer.boxes.items():  # test resolve
        assert isinstance(box.over, Box) or box.over is None
        for tract in box.tracts:
            assert isinstance(tract.dest, Box)


    """Done Test"""

def test_boxer_make_go():
    """Test make method of Boxer and modify wrapper with bx and go verbs
    """
    def fun(bx, go, do, on, *pa):
        bx(name='top')
        bx(over='top')
        go("next")
        bx(over="")  #same as prior
        go()
        b = bx(name='mow', over=None)
        bx(name='leg0', over=b)
        go()
        bx(name='leg1', over="")
        go()
        bx(name='leg2', over="")
        go("top")



    boxer = Boxer()
    assert boxer.boxes == {}
    mods = boxer.make(fun)
    assert boxer.boxes
    assert len(boxer.boxes) == 7
    assert list(boxer.boxes) == ['top', 'box0', 'box1', 'mow', 'leg0', 'leg1', 'leg2']
    assert str(boxer.boxes['top']) == 'Box(<top>box0)'
    assert str(boxer.boxes['mow']) == 'Box(<mow>leg0)'

    for name, box in boxer.boxes.items():  # test resolve
        assert isinstance(box.over, Box) or box.over is None
        for tract in box.tracts:
            assert isinstance(tract.dest, Box)


    """Done Test"""

def test_boxer_make_run():
    """Test make method of Boxer and modify wrapper with bx and go verbs
    """
    def count(**iops):
        M = iops['M']
        if M.count.value is None:
            M.count.value = 0
        else:
            M.count.value += 1
        return M.count.value


    def fun(bx, go, do, on, *pa):
        bx(name='top')
        bx(name='mid', over='top')
        go('done', "M.count.value==2")
        bx(name='bot0', over='mid')
        do(count)
        go("next")
        bx(name='bot1')  # over defaults to same as prev box
        do(count)
        go("next")
        bx(name='bot2')  # over defaults to same as prev box
        do(count)
        go("bot0")
        bx(name='done', over=None)
        do('end')


    mine = Mine()
    mine['count'] = Bag()

    boxer = Boxer(mine=mine)
    assert boxer.boxes == {}
    mods = boxer.make(fun)
    assert len(boxer.boxes) == 6
    assert list(boxer.boxes) == ['top', 'mid', 'bot0', 'bot1', 'bot2', 'done']

    boxer.begin()
    assert boxer.box.name == "bot1"  # half trans at end of first pass
    assert mine.count.value == 0
    boxer.run()
    assert boxer.box.name == "bot2"
    assert mine.count.value == 1
    boxer.run()
    assert boxer.box.name == "done"
    assert mine.count.value == 2
    boxer.run()
    assert boxer.box is None
    assert mine.count.value == 2
    assert boxer.endial()

    """Done Test"""


def test_boxer_make_run_on_update():
    """Test make method of Boxer with on verb special need update
    """
    tymist = Tymist()

    def count(**iops):
        M = iops['M']
        if M.count.value is None:
            M.count.value = 0
        else:
            M.count.value += 1
        return M.count.value


    def fun(bx, go, do, on, *pa):
        bx(name='top')
        bx(name='mid', over='top')
        go('done', on("update", "count"))
        bx(name='bot0', over='mid')
        go("next")
        bx(name='bot1')  # over defaults to same as prev box
        go("next")
        bx(name='bot2')  # over defaults to same as prev box
        do(count)
        go("bot0")
        bx(name='done', over=None)
        do('end')


    mine = Mine()
    mine['count'] = Bag()

    boxer = Boxer(mine=mine)
    assert boxer.boxes == {}
    mods = boxer.make(fun)
    assert len(boxer.boxes) == 6
    assert list(boxer.boxes) == ['top', 'mid', 'bot0', 'bot1', 'bot2', 'done']
    boxer.wind(tymth=tymist.tymen())

    boxer.begin()
    assert boxer.box.name == "bot1"  # half trans at end of first pass
    assert mine.count.value is None
    assert mine.count._tyme is None
    assert mine._boxer_boxer_box_mid_update_count.value is None
    boxer.run()
    assert boxer.box.name == "bot2"
    boxer.run()
    assert boxer.box.name == "done"
    assert mine.count.value == 0
    assert mine.count._tyme == 0.0
    assert mine._boxer_boxer_box_mid_update_count.value is None
    boxer.run()
    assert boxer.box is None
    assert boxer.endial()

    """Done Test"""


def test_boxer_make_run_on_change():
    """Test make method of Boxer with on verb special need change
    """
    tymist = Tymist()

    def count(**iops):
        M = iops['M']
        if M.count.value is None:
            M.count.value = 0
        else:
            M.count.value += 1
        return M.count.value


    def fun(bx, go, do, on, *pa):
        bx(name='top')
        bx(name='mid', over='top')
        go('done', on("change", "count"))
        bx(name='bot0', over='mid')
        go("next")
        bx(name='bot1')  # over defaults to same as prev box
        go("next")
        bx(name='bot2')  # over defaults to same as prev box
        do(count)
        go("bot0")
        bx(name='done', over=None)
        do('end')


    mine = Mine()
    mine['count'] = Bag()

    boxer = Boxer(mine=mine)
    assert boxer.boxes == {}
    mods = boxer.make(fun)
    assert len(boxer.boxes) == 6
    assert list(boxer.boxes) == ['top', 'mid', 'bot0', 'bot1', 'bot2', 'done']
    boxer.wind(tymth=tymist.tymen())

    boxer.begin()
    assert boxer.box.name == "bot1"  # half trans at end of first pass
    assert mine.count.value is None
    assert mine.count._tyme is None
    assert mine._boxer_boxer_box_mid_change_count.value == (None, )
    assert mine.count.value == None
    boxer.run()
    assert boxer.box.name == "bot2"
    boxer.run()
    assert boxer.box.name == "done"
    assert mine.count.value == 0
    assert mine.count._tyme == 0.0
    assert mine._boxer_boxer_box_mid_change_count.value == (None, )
    boxer.run()
    assert boxer.box is None
    assert boxer.endial()

    """Done Test"""


def test_maker_basic():
    """Basic test Maker class"""
    maker = Maker()  # defaults
    assert maker.name == 'maker'
    assert maker.mine == Mine()
    assert maker.boxer == None
    assert maker.box == None

    with pytest.raises(hioing.HierError):
        maker.name = "A.B"

    with pytest.raises(hioing.HierError):
        maker.name = "|maker"



def test_concept_bx_nonlocal():
    """Test concept for bx function for adding box to box work

    """
    #global B, _bags, _boxer, _boxes, _box, _over, _proem, _index

    B = _bags = Mine()
    _boxer = None
    _boxes = {}  # default boxes dict now a global
    _box = None
    _over = None # default top box now a global
    _proem = 'box'  #  default box name prefix now a global
    _index = 0  # default box name index

    def bx(name: None|str=None, over: None|str|Box="")->Box:
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
            B, _bags: (Mine): data mine for this box work
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

        box = Box(name=name, over=over, mine=_bags, boxer=_boxer)
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

    btop = bx(name="top")
    assert _box == btop
    assert _over == None
    assert not btop._next

    b0 = bx(over="top")
    assert _box == b0
    assert _over == btop
    assert btop._next == b0

    b1 = bx()
    assert _box == b1
    assert _over == btop
    assert b0._next == b1

    b2 = bx(over=b1)
    assert _box == b2
    assert _over == b1
    assert b1._next == b2

    b3 = bx(over=None)
    assert _box == b3
    assert _over == None
    assert b2._next == b3

    b4 = bx()
    assert _box == b4
    assert _over == None
    assert b3._next == b4

    b5 = bx(over="box0")
    assert _box == b5
    assert _over == b0
    assert b4._next == b5

    b6 = bx()
    assert _box == b6
    assert _over == b0
    assert b5._next == b6
    assert not b6._next

    assert _index == 7


    assert _boxes == {'top': btop,
                    'box0': b0,
                    'box1': b1,
                    'box2': b2,
                    'box3': b3,
                    'box4': b4,
                    'box5': b5,
                    'box6': b6,}

    assert str(btop) == 'Box(<top>box0>box5)'
    assert str(b0) == 'Box(top<box0>box5)'
    assert str(b1) == 'Box(top<box1>box2)'
    assert str(b2) == 'Box(top<box1<box2>)'
    assert str(b3) == 'Box(<box3>)'
    assert str(b4) == 'Box(<box4>)'
    assert str(b5) == 'Box(top<box0<box5>)'
    assert str(b6) == 'Box(top<box0<box6>)'


    """Done Test"""

def test_concept_bx_global():
    """Test concept for bx function for adding box to box work

    """
    global B, _bags, _boxer, _boxes, _box, _over, _proem, _index

    B = _bags = Mine()
    _boxer = None
    _boxes = {}  # default boxes dict now a global
    _box = None
    _over = None # default top box now a global
    _proem = 'box'  #  default box name prefix now a global
    _index = 0  # default box name index

    def bx(name: None|str=None, over: None|str|Box="")->Box:
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
            B, _bags: (Mine): data mine for this box work
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

        box = Box(name=name, over=over, mine=_bags, boxer=_boxer)
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

    btop = bx(name="top")
    assert _box == btop
    assert _over == None
    assert not btop._next

    b0 = bx(over="top")
    assert _box == b0
    assert _over == btop
    assert btop._next == b0

    b1 = bx()
    assert _box == b1
    assert _over == btop
    assert b0._next == b1

    b2 = bx(over=b1)
    assert _box == b2
    assert _over == b1
    assert b1._next == b2

    b3 = bx(over=None)
    assert _box == b3
    assert _over == None
    assert b2._next == b3

    b4 = bx()
    assert _box == b4
    assert _over == None
    assert b3._next == b4

    b5 = bx(over="box0")
    assert _box == b5
    assert _over == b0
    assert b4._next == b5

    b6 = bx()
    assert _box == b6
    assert _over == b0
    assert b5._next == b6
    assert not b6._next

    assert _index == 7


    assert _boxes == {'top': btop,
                    'box0': b0,
                    'box1': b1,
                    'box2': b2,
                    'box3': b3,
                    'box4': b4,
                    'box5': b5,
                    'box6': b6,}

    assert str(btop) == 'Box(<top>box0>box5)'
    assert str(b0) == 'Box(top<box0>box5)'
    assert str(b1) == 'Box(top<box1>box2)'
    assert str(b2) == 'Box(top<box1<box2>)'
    assert str(b3) == 'Box(<box3>)'
    assert str(b4) == 'Box(<box4>)'
    assert str(b5) == 'Box(top<box0<box5>)'
    assert str(b6) == 'Box(top<box0<box6>)'


    """Done Test"""

if __name__ == "__main__":
    test_box_basic()
    test_boxer_quen()
    test_boxer_basic()
    test_boxer_make()
    test_boxer_make_go()
    test_boxer_make_run()
    test_boxer_make_run_on_update()
    test_boxer_make_run_on_change()
    test_maker_basic()
    test_concept_bx_nonlocal()
    test_concept_bx_global()
