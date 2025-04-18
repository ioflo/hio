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
from hio.base.hier import (Nabes, Rexcnt, Rexlps, Rexrlp, Bag,
                           Box, Boxer, Boxery,
                           ActBase, Act, EndAct, )


def test_rexlps():
    """Test regular expression Rexlps special need condition 'lapse' """
    cond = "lapse"
    assert Rexlps.match(cond).group("lps", "cmp") == ("lapse", "")

    cond = "lapse>=2.0"
    assert Rexlps.match(cond).group("lps", "cmp") == ("lapse", ">=2.0")

    cond = "lapse>=2.0\nwhat"  # ignores newline and stuff after
    assert Rexlps.match(cond).group("lps", "cmp") == ("lapse", ">=2.0")

    cond = " lapse >= 2.0 "  # ignores whitespace before lapse
    assert Rexlps.match(cond).group("lps", "cmp") == ("lapse", " >= 2.0 ")

    cond = " lapse\t >= 2.0 "  # any whitespace after lapse
    assert Rexlps.match(cond).group("lps", "cmp") == ('lapse', '\t >= 2.0 ')

    cond = "lapse != 2"  # any whitespace after lapse
    assert Rexlps.match(cond).group("lps", "cmp") == ("lapse", " != 2")

    cond = "lapse > 2"  # any whitespace after lapse
    assert Rexlps.match(cond).group("lps", "cmp") == ("lapse", " > 2")

    cond = "lapse == 2"  # any whitespace after lapse
    assert Rexlps.match(cond).group("lps", "cmp") == ("lapse", " == 2")

    cond = "lapsed >= 2"  # does not match other word with 'lapse' prefix
    assert not Rexlps.match(cond)

    cond = "lapse1 >= 2"  # does not match other word with 'lapse' prefix
    assert not Rexlps.match(cond)

    cond = "lapse_ >= 2"  # does not match other word with 'lapse' prefix
    assert not Rexlps.match(cond)

    cond = "_lapse >= 2"  # does not match other word with 'lapse' suffix
    assert not Rexlps.match(cond)

    cond = "0lapse >= 2"  # does not match other word with 'lapse' suffix
    assert not Rexlps.match(cond)

    cond = "my lapse >= 2"  # does not match other word with 'lapse' suffix
    assert not Rexlps.match(cond)

    """Done Test"""


def test_rexrlp():
    """Test regular expression Rexrlp special need condition 'relapse' """
    cond = "relapse"
    assert Rexrlp.match(cond).group("rlp", "cmp") == ("relapse", "")

    cond = "relapse>=2.0"
    assert Rexrlp.match(cond).group("rlp", "cmp") == ("relapse", ">=2.0")

    cond = "relapse>=2.0\nwhat"  # ignores newline and stuff after
    assert Rexrlp.match(cond).group("rlp", "cmp") == ("relapse", ">=2.0")

    cond = " relapse >= 2.0 "  # ignores whitespace before relapse
    assert Rexrlp.match(cond).group("rlp", "cmp") == ("relapse", " >= 2.0 ")

    cond = " relapse\t >= 2.0 "  # any whitespace after relapse
    assert Rexrlp.match(cond).group("rlp", "cmp") == ('relapse', '\t >= 2.0 ')

    cond = "relapse != 2"  # any whitespace after relapse
    assert Rexrlp.match(cond).group("rlp", "cmp") == ("relapse", " != 2")

    cond = "relapse > 2"  # any whitespace after relapse
    assert Rexrlp.match(cond).group("rlp", "cmp") == ("relapse", " > 2")

    cond = "relapse == 2"  # any whitespace after relapse
    assert Rexrlp.match(cond).group("rlp", "cmp") == ("relapse", " == 2")

    cond = "relapsed >= 2"  # does not match other word with 'relapse' prefix
    assert not Rexrlp.match(cond)

    cond = "relapse1 >= 2"  # does not match other word with 'relapse' prefix
    assert not Rexrlp.match(cond)

    cond = "relapse_ >= 2"  # does not match other word with 'relapse' prefix
    assert not Rexrlp.match(cond)

    cond = "_relapse >= 2"  # does not match other word with 'relapse' suffix
    assert not Rexrlp.match(cond)

    cond = "0relapse >= 2"  # does not match other word with 'relapse' suffix
    assert not Rexrlp.match(cond)

    cond = "my relapse >= 2"  # does not match other word with 'relapse' suffix
    assert not Rexrlp.match(cond)

    """Done Test"""


def test_rexcnt():
    """Test regular expression Rexcnt special need condition 'count' """
    cond = "count"
    assert Rexcnt.match(cond).group("cnt", "cmp") == ("count", "")

    cond = "count>=2"
    assert Rexcnt.match(cond).group("cnt", "cmp") == ("count", ">=2")

    cond = "count>=2\nwhat"  # ignores newline and stuff after
    assert Rexcnt.match(cond).group("cnt", "cmp") == ("count", ">=2")

    cond = " count >= 2 "  # ignores whitespace before count
    assert Rexcnt.match(cond).group("cnt", "cmp") == ("count", " >= 2 ")

    cond = " count\t >= 2 "  # any whitespace after count
    assert Rexcnt.match(cond).group("cnt", "cmp") == ('count', '\t >= 2 ')

    cond = "count != 2"  # any whitespace after count
    assert Rexcnt.match(cond).group("cnt", "cmp") == ("count", " != 2")

    cond = "count > 2"  # any whitespace after count
    assert Rexcnt.match(cond).group("cnt", "cmp") == ("count", " > 2")

    cond = "count == 2"  # any whitespace after count
    assert Rexcnt.match(cond).group("cnt", "cmp") == ("count", " == 2")

    cond = "counter >= 2"  # does not match other word with 'count' prefix
    assert not Rexcnt.match(cond)

    cond = "count1 >= 2"  # does not match other word with 'count' prefix
    assert not Rexcnt.match(cond)

    cond = "count_ >= 2"  # does not match other word with 'count' prefix
    assert not Rexcnt.match(cond)

    cond = "_count >= 2"  # does not match other word with 'count' suffix
    assert not Rexcnt.match(cond)

    cond = "0count >= 2"  # does not match other word with 'count' suffix
    assert not Rexcnt.match(cond)

    cond = "my count >= 2"  # does not match other word with 'count' suffix
    assert not Rexcnt.match(cond)

    """Done Test"""




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
    assert box.remarks == []
    assert box.renacts == []
    assert box.enmarks == []
    assert box.enacts == []
    assert box.reacts == []
    assert box.anacts == []
    assert box.goacts == []
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



def test_boxer_exen():
    """Test exen function for finding common/uncommon boxes in near far staks
    for computing exits, endos, rexdos, rendos on a transition
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
    exen = Boxer.exen  # exen is staticmethod of Boxer

    exdos, endos, rexdos, rendos = exen(d, e)
    assert exdos == [d]
    assert endos == [e, f]
    assert rexdos == [c, b, a]
    assert rendos == [a, b, c]

    exdos, endos, rexdos, rendos = exen(d, f)
    assert exdos == [d]
    assert endos == [e, f]
    assert rexdos == [c, b, a]
    assert rendos == [a, b, c]

    exdos, endos, rexdos, rendos = exen(a, e)
    assert exdos == [d]
    assert endos == [e, f]
    assert rexdos == [c, b, a]
    assert rendos == [a, b, c]

    exdos, endos, rexdos, rendos = exen(c, b)
    assert exdos == [d, c, b]
    assert endos == [b, c, d]
    assert rexdos == [a]
    assert rendos == [a]

    exdos, endos, rexdos, rendos = exen(c, c)
    assert exdos == [d, c]
    assert endos == [c, d]
    assert rexdos == [b, a]
    assert rendos == [a, b]

    exdos, endos, rexdos, rendos = exen(c, d)
    assert exdos == [d]
    assert endos == [d]
    assert rexdos == [c, b, a]
    assert rendos == [a, b, c]

    exdos, endos, rexdos, rendos = exen(e, d)
    assert exdos == [f, e]
    assert endos == [d]
    assert rexdos == [c, b, a]
    assert rendos == [a, b, c]

    exdos, endos, rexdos, rendos = exen(f, f)
    assert exdos == [f]
    assert endos == [f]
    assert rexdos == [e, c, b, a]
    assert rendos == [a, b, c, e]

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
    boxer.rewind()
    assert boxer.mine.test._tymth
    assert boxer.mine.test._now == boxer.tyme
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
    def fun(bx, go, do, on, at, be, *pa):
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
        for goact in box.goacts:
            assert isinstance(goact.dest, Box)


    """Done Test"""

def test_boxer_make_go():
    """Test make method of Boxer and modify wrapper with bx and go verbs
    """
    def fun(bx, go, do, on, at, be, *pa):
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
        for goact in box.goacts:
            assert isinstance(goact.dest, Box)


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


    def fun(bx, go, do, on, at, be, *pa):
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

    assert mine.count.value is None

    boxer.begin()
    assert boxer.box.name == "top"
    assert mine.count.value == 0
    boxer.run()
    assert boxer.box.name == "bot1"  # half trans at end of first pass
    assert mine.count.value == 1
    boxer.run()
    assert boxer.box.name == "bot2"
    assert mine.count.value == 2
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


    def fun(bx, go, do, on, at, be, *pa):
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

    assert mine.count.value is None
    assert mine.count._tyme is None
    assert mine._boxer_boxer_box_mid_update_count.value is None

    boxer.begin()
    assert boxer.box.name == "top"  # default first
    assert mine.count.value == None
    assert mine.count._tyme == None
    assert mine._boxer_boxer_box_mid_update_count.value == None
    boxer.run()
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


    def fun(bx, go, do, on, at, be, *pa):
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

    assert mine.count.value is None
    assert mine.count._tyme is None
    assert mine._boxer_boxer_box_mid_change_count.value is None

    boxer.begin()
    assert boxer.box.name == "top"  # default first
    assert mine.count.value is None
    assert mine.count._tyme is None
    assert mine._boxer_boxer_box_mid_change_count.value == (None, )
    boxer.run()
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

def test_boxer_make_run_on_count():
    """Test make method of Boxer with on verb special need count
    """
    tymist = Tymist()

    def fun(bx, go, do, on, at, be, *pa):
        bx(name='top')
        bx('mid', 'top')
        do("count", "redo")
        do("discount", "exdo")
        go('done', on("count >= 2"))
        bx('bot0', 'mid', first=True)
        go("next")
        bx('bot1')  # over defaults to same as prev box
        go("next")
        bx('bot2')  # over defaults to same as prev box
        go("bot0")
        bx(name='done', over=None)
        do('end')


    mine = Mine()

    boxer = Boxer(mine=mine)
    assert boxer.boxes == {}
    mods = boxer.make(fun)
    assert len(boxer.boxes) == 6
    assert list(boxer.boxes) == ['top', 'mid', 'bot0', 'bot1', 'bot2', 'done']
    boxer.wind(tymth=tymist.tymen())
    assert boxer.boxes["mid"].reacts
    assert boxer.boxes["mid"].exacts

    assert mine._boxer_boxer_box_mid_count.value is None

    boxer.begin()
    assert boxer.box.name == "bot0"   # since set as first
    assert mine._boxer_boxer_box_mid_count.value == 0
    boxer.run()
    assert boxer.box.name == "bot1"  # half trans at end of first pass
    assert mine._boxer_boxer_box_mid_count.value == 1
    boxer.run()
    assert boxer.box.name == "bot2"
    assert mine._boxer_boxer_box_mid_count.value == 2
    boxer.run()
    assert boxer.box.name == "done"
    assert mine._boxer_boxer_box_mid_count.value is None
    boxer.run()
    assert boxer.box is None
    assert boxer.endial()

    """Done Test"""


def test_boxer_make_run_verbs():
    """Test make method of Boxer with all verbs

    """
    tymist = Tymist()

    def dumb(**iops):
        return True

    def fun(bx, go, do, on, at, be, *pa):
        bx(name='top')
        bx('mid', 'top')
        at('redo')
        do("count")
        at("exdo")
        do("discount")
        go('done', on("count >= 2"))
        bx('bot0', 'mid', first=True)
        do('M.stuff.value += 1')
        go("next")
        bx('bot1')  # over defaults to same as prev box
        do('M.stuff.value += 1')
        be("crud.value", "2**4")
        go("next")
        bx('bot2')  # over defaults to same as prev box
        be("crud.value", dumb)
        go("bot0")
        bx(name='done', over=None)
        do('end')


    mine = Mine()
    # init mine Bags
    mine.stuff = Bag()
    mine.stuff.value = 0
    mine.crud = Bag()

    boxer = Boxer(mine=mine)
    assert boxer.boxes == {}
    mods = boxer.make(fun)
    assert len(boxer.boxes) == 6
    assert list(boxer.boxes) == ['top', 'mid', 'bot0', 'bot1', 'bot2', 'done']
    boxer.wind(tymth=tymist.tymen())
    assert boxer.boxes["mid"].reacts
    assert boxer.boxes["mid"].exacts

    assert mine._boxer_boxer_box_mid_count.value is None
    assert mine.stuff.value == 0
    assert mine.crud.value == None

    boxer.begin()
    assert boxer.box.name == "bot0"   # since set as first
    assert mine._boxer_boxer_box_mid_count.value == 0
    assert mine.stuff.value == 1
    assert mine.crud.value == None
    boxer.run()
    assert boxer.box.name == "bot1"  # half trans at end of first pass
    assert mine._boxer_boxer_box_mid_count.value == 1
    assert mine.stuff.value == 2
    assert mine.crud.value == 16
    boxer.run()
    assert boxer.box.name == "bot2"
    assert mine._boxer_boxer_box_mid_count.value == 2
    assert mine.stuff.value == 2
    assert mine.crud.value == True
    boxer.run()
    assert boxer.box.name == "done"
    assert mine._boxer_boxer_box_mid_count.value is None
    assert mine.stuff.value == 2
    assert mine.crud.value == True
    boxer.run()
    assert boxer.box is None
    assert boxer.endial()

    """Done Test"""

def test_boxer_make_run_lapse():
    """Test make method of Boxer with lapse condition

    """
    def fun(bx, go, do, on, at, be, *pa):
        bx(name='top')
        bx('mid', 'top')
        at('redo')
        do("count")
        at("exdo")
        do("discount")
        go('done', on("count >= 5"))
        bx('bot0', 'mid', first=True)
        go("next", on("lapse >= 2.0"))
        bx('bot1')  # over defaults to same as prev box
        go("next", on("lapse >= 2.0"))
        bx('bot2')  # over defaults to same as prev box
        go("bot0")
        bx(name='done', over=None)
        do('end')


    tymist = Tymist(tock=1.0)
    mine = Mine()
    # init mine Bags
    mine.stuff = Bag()
    mine.stuff.value = 0
    mine.crud = Bag()

    boxer = Boxer(tymth=tymist.tymen(), mine=mine)
    assert boxer.boxes == {}
    mods = boxer.make(fun)
    assert len(boxer.boxes) == 6
    assert list(boxer.boxes) == ['top', 'mid', 'bot0', 'bot1', 'bot2', 'done']
    boxer.rewind()
    assert boxer.boxes["mid"].reacts
    assert boxer.boxes["mid"].exacts

    assert mine._boxer_boxer_box_mid_count.value is None
    assert mine._boxer_boxer_box_bot0_lapse.value is None
    assert mine._boxer_boxer_box_bot0_lapse._now == 0.0
    assert mine._boxer_boxer_box_bot1_lapse.value == None
    assert mine._boxer_boxer_box_bot1_lapse._now == 0.0

    boxer.begin()
    assert boxer.box.name == "bot0"   # since set as first
    assert mine._boxer_boxer_box_mid_count.value == 0
    assert mine._boxer_boxer_box_bot0_lapse.value == 0.0
    assert mine._boxer_boxer_box_bot0_lapse._now == 0.0
    tymist.tick()
    boxer.run()
    assert boxer.box.name == "bot0"
    assert mine._boxer_boxer_box_mid_count.value == 1
    assert mine._boxer_boxer_box_bot0_lapse.value == 0.0
    assert mine._boxer_boxer_box_bot0_lapse._now == 1.0
    tymist.tick()
    boxer.run()
    assert boxer.box.name == "bot1"
    assert mine._boxer_boxer_box_mid_count.value == 2
    assert mine._boxer_boxer_box_bot0_lapse.value == 0.0
    assert mine._boxer_boxer_box_bot0_lapse._now == 2.0
    assert mine._boxer_boxer_box_bot1_lapse.value == 2.0
    assert mine._boxer_boxer_box_bot1_lapse._now == 2.0
    tymist.tick()
    boxer.run()
    assert boxer.box.name == "bot1"
    assert mine._boxer_boxer_box_mid_count.value == 3
    assert mine._boxer_boxer_box_bot0_lapse.value == 0.0
    assert mine._boxer_boxer_box_bot0_lapse._now == 3.0
    assert mine._boxer_boxer_box_bot1_lapse.value == 2.0
    assert mine._boxer_boxer_box_bot1_lapse._now == 3.0
    tymist.tick()
    boxer.run()
    assert boxer.box.name == "bot2"
    assert mine._boxer_boxer_box_mid_count.value == 4
    assert mine._boxer_boxer_box_bot0_lapse.value == 0.0
    assert mine._boxer_boxer_box_bot0_lapse._now == 4.0
    assert mine._boxer_boxer_box_bot1_lapse.value == 2.0
    assert mine._boxer_boxer_box_bot1_lapse._now == 4.0
    tymist.tick()
    boxer.run()
    assert boxer.box.name == "bot0"
    assert mine._boxer_boxer_box_mid_count.value == 5
    assert mine._boxer_boxer_box_bot0_lapse.value == 5.0
    assert mine._boxer_boxer_box_bot0_lapse._now == 5.0
    assert mine._boxer_boxer_box_bot1_lapse.value == 2.0
    assert mine._boxer_boxer_box_bot1_lapse._now == 5.0
    tymist.tick()
    boxer.run()
    assert boxer.box.name == "done"
    assert mine._boxer_boxer_box_mid_count.value is None
    tymist.tick()
    boxer.run()
    assert boxer.box is None
    assert boxer.endial()

    """Done Test"""

def test_boxer_make_run_relapse():
    """Test make method of Boxer with relapse condition

    """
    def fun(bx, go, do, on, at, be, *pa):
        bx(name='top')
        bx('mid', 'top')
        at('redo')
        do("count")
        at("exdo")
        do("discount")
        go('done', on("count >= 5"))
        go('done', on("relapse >= 2.0"))
        bx('bot0', 'mid', first=True)
        go("next")
        bx('bot1')  # over defaults to same as prev box
        go("next", on("lapse >= 2.0"))
        bx('bot2')  # over defaults to same as prev box
        go("bot0")
        bx(name='done', over=None)
        do('end')


    tymist = Tymist(tock=1.0)
    mine = Mine()
    # init mine Bags
    mine.stuff = Bag()
    mine.stuff.value = 0
    mine.crud = Bag()

    boxer = Boxer(tymth=tymist.tymen(), mine=mine)
    assert boxer.boxes == {}
    mods = boxer.make(fun)
    assert len(boxer.boxes) == 6
    assert list(boxer.boxes) == ['top', 'mid', 'bot0', 'bot1', 'bot2', 'done']
    boxer.rewind()
    assert boxer.boxes["mid"].reacts
    assert boxer.boxes["mid"].exacts

    assert mine._boxer_boxer_box_mid_count.value is None
    assert mine._boxer_boxer_box_mid_relapse.value is None
    assert mine._boxer_boxer_box_mid_relapse._now == 0.0
    assert mine._boxer_boxer_box_bot1_lapse.value is None
    assert mine._boxer_boxer_box_bot1_lapse._now == 0.0

    assert boxer.tyme == 0.0
    boxer.begin()
    assert boxer.box.name == "bot0"   # since set as first
    assert mine._boxer_boxer_box_mid_count.value == 0
    assert mine._boxer_boxer_box_mid_relapse.value == None
    assert mine._boxer_boxer_box_mid_relapse._now == 0.0
    tymist.tick()
    assert boxer.tyme == 1.0
    boxer.run()
    assert boxer.box.name == "bot1"
    assert mine._boxer_boxer_box_mid_count.value == 1
    assert mine._boxer_boxer_box_mid_relapse.value == 1.0
    assert mine._boxer_boxer_box_mid_relapse._now == 1.0
    assert mine._boxer_boxer_box_bot1_lapse.value == 1.0
    assert mine._boxer_boxer_box_bot1_lapse._now == 1.0
    tymist.tick()
    assert boxer.tyme == 2.0
    boxer.run()
    assert boxer.box.name == "bot1"
    assert mine._boxer_boxer_box_mid_count.value == 2
    assert mine._boxer_boxer_box_mid_relapse.value == 1.0
    assert mine._boxer_boxer_box_mid_relapse._now == 2.0
    assert mine._boxer_boxer_box_bot1_lapse.value == 1.0
    assert mine._boxer_boxer_box_bot1_lapse._now == 2.0
    tymist.tick()
    assert boxer.tyme == 3.0
    boxer.run()
    assert boxer.box.name == "done"
    assert mine._boxer_boxer_box_mid_count.value is None
    assert mine._boxer_boxer_box_mid_relapse.value == 1.0
    assert mine._boxer_boxer_box_mid_relapse._now == 3.0
    tymist.tick()
    assert boxer.tyme == 4.0
    boxer.run()
    assert boxer.box is None
    assert boxer.endial()

    """Done Test"""



def test_boxery_basic():
    """Basic test Boxery class"""
    maker = Boxery()  # defaults
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
    test_rexlps()
    test_rexrlp()
    test_rexcnt()
    test_box_basic()
    test_boxer_exen()
    test_boxer_basic()
    test_boxer_make()
    test_boxer_make_go()
    test_boxer_make_run()
    test_boxer_make_run_on_update()
    test_boxer_make_run_on_change()
    test_boxer_make_run_on_count()
    test_boxer_make_run_verbs()
    test_boxer_make_run_lapse()
    test_boxer_make_run_relapse()
    test_boxery_basic()
    test_concept_bx_nonlocal()
    test_concept_bx_global()
