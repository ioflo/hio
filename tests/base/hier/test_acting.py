# -*- encoding: utf-8 -*-
"""tests.base.hier.test_acting module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest

import os
from collections.abc import Callable

from hio import Mixin, HierError
from hio.base import Tymist
from hio.base.hier import Nabes, Need, Box, Boxer, Bag, Hold, Hog
from hio.base.hier import (ActBase, actify, Act, Goact, EndAct, Beact,
                          Mark, LapseMark, RelapseMark,
                          BagMark, UpdateMark, ReupdateMark,
                          ChangeMark, RechangeMark,
                          Count, Discount,
                          CloseAct)
from hio.help import TymeDom


def test_actbase():
    """Test ActBase Class"""

    # clear registries for debugging
    ActBase._clearall()

    assert ActBase.__name__ == 'ActBase'
    assert ActBase.__name__ in ActBase.Registry
    assert ActBase.Registry[ActBase.__name__] == ActBase
    assert ActBase.Instances == {}
    assert ActBase.Index == 0
    assert ActBase.Names == ()

    act = ActBase()
    assert ActBase.Names == ()
    assert isinstance(act, Callable)
    assert act.name == 'ActBase0'
    assert act.iops == {}
    assert act.nabe == Nabes.endo
    assert act.hold == Hold()
    assert hasattr(act, 'name')   # hasattr works for properties and attributes
    assert act.name in ActBase.Instances
    assert ActBase.Instances[act.name] == act
    assert ActBase.Index == 1
    assert act() == {}


    act = ActBase()
    assert ActBase.Names == ()
    assert isinstance(act, Callable)
    assert act.name == 'ActBase1'
    assert act.iops == {}
    assert act.nabe == Nabes.endo
    assert act.hold == Hold()
    assert hasattr(act, 'name')   # hasattr works for properties and attributes
    assert act.name in ActBase.Instances
    assert ActBase.Instances[act.name] == act
    assert ActBase.Index == 2
    assert act() == {}


    """Done Test"""


def test_actify():
    """Test Actor registry base stuff class and subclasses"""

    @actify(name="Tact")
    def test(self, **kwa):  # signature for .act with **iops as **kwa
        assert kwa == self.iops
        return self.iops

    t = test(iops=dict(what=1), hello="hello", nabe=Nabes.redo)  # signature for Act.__init__
    assert t.name == "Tact0"
    assert t.iops == dict(what=1)
    assert t.nabe == Nabes.redo
    assert t.__class__.__name__ == "Tact"
    assert t.__class__.__name__ in t.Registry
    assert t.Registry[t.__class__.__name__] == t.__class__
    assert t.name in t.Instances
    assert t.Instances[t.name] == t
    assert isinstance(t, ActBase)
    assert t() == t.iops
    assert t.Names == ()

    x = test(bye="bye")  # signature for Act.__init__
    assert x.name == "Tact1"
    assert x.iops == {}
    assert x.nabe == Nabes.endo
    assert x.__class__.__name__ == "Tact"
    assert x.__class__.__name__ in t.Registry
    assert x.Registry[t.__class__.__name__] == t.__class__
    assert x.name in t.Instances
    assert x.Instances[t.name] == t
    assert isinstance(t, ActBase)
    assert x() == x.iops
    assert t.Names == ()

    assert x.__class__ == t.__class__
    klas = ActBase.Registry["Tact"]
    assert isinstance(t, klas)
    assert isinstance(x, klas)

    @actify(name="Pact")
    def pest(self, **kwa):  # signature for .act
        assert kwa == self.iops
        assert "why" in kwa
        assert kwa["why"] == 1
        return self.iops

    p = pest(name="spot", iops=dict(why=1))  # same signature as Act.__init__
    assert p.name == 'spot'
    assert p.iops == dict(why=1)
    assert p.nabe == Nabes.endo
    assert "Pact" in p.Registry
    klas = p.Registry["Pact"]
    assert isinstance(p, klas)
    assert p.Instances[p.name] == p
    assert p() == dict(why=1)
    assert t.Names == ()

    @actify(name="Bact")
    def best(self, *, how=None):  # signature for .act
        assert how == 5
        assert self.iops["how"] == how
        return self.iops

    b = best(iops=dict(how=5))  # signature for Act.__init__
    assert b.name == 'Bact0'
    assert b.iops == dict(how=5)
    assert b.nabe == Nabes.endo
    assert "Bact" in b.Registry
    klas = b.Registry["Bact"]
    assert isinstance(b, klas)
    assert b.Instances[b.name] == b
    assert b() == dict(how=5)
    assert t.Names == ()


    """Done Test"""



def test_act_basic():
    """Test Act class"""

    Act._clearall()  # clear instances for debugging

    assert "Act" in Act.Registry
    assert Act.Registry["Act"] == Act

    act = Act()
    assert act.name == "Act0"
    assert act.iops == {'H': {'_hold_subery': None}}
    assert act.nabe == Nabes.endo
    assert act.Index == 1
    assert act.Instances[act.name] == act
    assert act.hold == Hold()
    assert callable(act.deed)
    assert act._code is None
    assert not act.compiled

    assert act() == act.iops

    iops = dict(a=1, b=2)
    act = Act(iops=iops, nabe=Nabes.redo)
    assert act.name == "Act1"
    assert act.iops == {'a': 1, 'b': 2, 'H': {'_hold_subery': None}}
    assert act.nabe == Nabes.redo
    assert act.Index == 2
    assert act.Instances[act.name] == act
    assert act.hold == Hold()
    assert callable(act.deed)
    assert act._code is None
    assert not act.compiled

    assert act() == act.iops

    def dumb(**iops):
        H = iops['H']
        if 'count' not in H:
            H['count'] = Bag()
        if H.count.value is None:
            H.count.value = 0
        H.count.value += 1
        return (H.count.value, len(iops), iops)

    iops = dict(when="now", why="because")
    act = Act(dumb, iops=iops)
    assert act.name == "Act2"
    assert act.iops == {'when': 'now', 'why': 'because', 'H': {'_hold_subery': None}}
    assert act.nabe == Nabes.endo
    assert act.Index == 3
    assert act.Instances[act.name] == act
    assert act.hold == Hold()
    assert callable(act.deed)
    assert act.deed == dumb
    assert act._code is None
    assert not act.compiled

    assert act() == (1,
                    3,
                    {'when': 'now',
                     'why': 'because',
                     'H': {'_hold_subery': None, 'count': Bag(value=1)}})

    iops = dict(fix=3)
    hold = Hold()
    hold.stuff = Bag()
    hold.stuff.value = 0
    deed = "H.stuff.value += 1\n"
    act = Act(deed, hold=hold, iops=iops)
    assert act.name == "Act3"
    assert act.iops == {'fix': 3, 'H': {'_hold_subery': None, 'stuff': Bag(value=0)}}
    assert act.nabe == Nabes.endo
    assert act.Index == 4
    assert act.Instances[act.name] == act
    assert act.hold == hold
    assert not callable(act.deed)
    assert act.deed == deed
    assert act._code
    assert act.compiled

    assert act() == None
    assert act._code is not None
    assert act.compiled
    assert hold.stuff.value == 1

    assert act() == None
    assert act.compiled
    assert hold.stuff.value == 2

    """Done Test"""

def test_need_act():
    """Test Act using Need as its deed"""

    hold = Hold()
    need = Need(hold=hold)
    act = Act(need, hold=hold)
    assert act() == True


    hold.cycle = Bag(value=2)
    hold.turn = Bag(value=2)
    expr = "H.cycle.value > 3 and H.turn.value <= 2"
    need = Need(expr=expr, hold=hold)
    act = Act(deed=need, hold=hold)
    assert act() == False

    hold.cycle.value = 5
    assert act() == True
    """Done Test"""


def test_goact_basic():
    """Test Goact class"""

    Goact._clearall()  # clear instances for debugging

    assert "Goact" in Goact.Registry
    assert Goact.Registry["Goact"] == Goact

    goact = Goact()
    assert goact.name == "Goact0"
    assert goact.iops == {}
    assert goact.nabe == Nabes.godo
    assert goact.hold == Hold()
    assert goact.Index == 1
    assert goact.Instances[goact.name] == goact
    assert goact.dest == 'next'
    assert isinstance(goact.need, Need)
    assert goact.need()

    with pytest.raises(HierError):
        assert not goact()  # since default .dest not yet resolved

    hold = Hold()
    hold.cycle = Bag(value=3)
    box = Box(hold=hold)
    need = Need(expr='H.cycle.value >= 3', hold=hold)
    goact = Goact(dest=box, need=need)
    assert goact.need.compiled

    dest = goact()
    assert dest == box
    assert goact.need.compiled

    hold.cycle.value = 1
    assert not goact()
    """Done Test"""


def test_endact_basic():
    """Test EndAct class"""

    EndAct._clearall()  # clear instances for debugging

    assert "EndAct" in EndAct.Registry
    assert EndAct.Registry["EndAct"] == EndAct
    assert EndAct.Names == ("end", "End")
    for name in EndAct.Names:
        assert name in EndAct.Registry
        assert EndAct.Registry[name] == EndAct

    with pytest.raises(HierError):
        eact = EndAct()  # requires iops with boxer=boxer.name


    hold = Hold()
    boxer = Boxer(hold=hold)
    iops = dict(_boxer=boxer.name)

    eact = EndAct(iops=iops, hold=hold)
    assert eact.name == "EndAct1"
    assert eact.iops == iops
    assert eact.nabe == Nabes.endo
    assert eact.hold == hold
    assert eact.Index == 2
    assert eact.Instances[eact.name] == eact
    keys = ("", "boxer", boxer.name, "end")
    assert keys in eact.hold
    assert not eact.hold[keys].value
    eact()
    assert eact.hold[keys].value


    """Done Test"""

def test_beact_basic():
    """Test Beact class"""

    Beact._clearall()  # clear instances for debugging

    assert "Beact" in Beact.Registry
    assert Beact.Registry["Beact"] == Beact

    with pytest.raises(HierError):
        act = Beact(lhs="stuff.value")

    hold = Hold()
    hold.stuff = Bag()

    with pytest.raises(HierError):
        act = Beact(lhs="stuff.kind", hold=hold)

    Beact._clearall()  # clear instances for debugging

    hold = Hold()
    hold.stuff = Bag()

    act = Beact(lhs=("stuff", "value"), hold=hold)
    assert act.name == "Beact0"
    assert act.iops == {'H': {'_hold_subery': None, 'stuff': Bag(value=None)}}
    assert act.nabe == Nabes.endo
    assert act.Index == 1
    assert act.Instances[act.name] == act
    assert act.hold == hold
    assert act.lhs == ("stuff", "value")
    assert act.rhs is None
    assert act._code is None
    assert not act.compiled
    assert act() == None
    assert hold["stuff"]["value"] == None

    act.lhs = "stuff.value"
    assert act.lhs == ("stuff", "value")
    assert act() == None
    assert hold["stuff"]["value"] == None
    assert not act.compiled

    act.rhs = "5"
    assert not act.compiled
    assert act() == 5
    assert act.compiled
    assert hold["stuff"]["value"] == 5

    def dummy(**iops):
        return True

    act.rhs = dummy
    assert not act.compiled
    assert act() == True
    assert not act.compiled
    assert hold["stuff"]["value"] == True

    iops = dict(a=1, b=2)
    act = Beact(lhs="stuff.value", rhs=dummy, hold=hold, iops=iops, nabe=Nabes.redo)
    assert act.name == "Beact1"
    assert act.iops == {'a': 1, 'b': 2, 'H': {'_hold_subery': None, 'stuff': Bag(value=True)}}

    assert act.nabe == Nabes.redo
    assert act.Index == 2
    assert act.Instances[act.name] == act
    assert act.hold == hold
    assert act.lhs == ("stuff", "value")
    assert act.rhs is dummy
    assert act._code is None
    assert not act.compiled
    assert act() == True
    assert act.hold.stuff.value == True

    act = Beact(lhs="stuff.value", rhs="2**5", hold=hold, nabe=Nabes.rendo)
    assert act.name == "Beact2"
    assert act.iops == {'H': {'_hold_subery': None, 'stuff': Bag(value=True)}}
    assert act.nabe == Nabes.rendo
    assert act.Index == 3
    assert act.Instances[act.name] == act
    assert act.hold == hold
    assert act.lhs == ("stuff", "value")
    assert act.rhs is "2**5"
    assert act._code
    assert act.compiled
    assert act() == 32
    assert act.hold.stuff.value == 32

    """Done Test"""


def test_mark_basic():
    """Test Mark class"""

    Mark._clearall()  # clear instances for debugging

    assert "Mark" in Mark.Registry
    assert Mark.Registry["Mark"] == Mark
    assert Mark.Names == ()

    with pytest.raises(HierError):
        act = Mark()  # requires iops with _boxer=boxer.name and _box=box.name


    hold = Hold()
    boxer = Boxer(hold=hold)
    box = Box(hold=hold)
    iops = dict(_boxer=boxer.name, _box=box.name)

    act = Mark(iops=iops, hold=hold)
    assert act.name == 'Mark1'
    assert act.iops == iops
    assert act.nabe == Nabes.enmark
    assert act.hold == hold
    assert act.Index == 2
    assert act.Instances[act.name] == act
    assert act() is None

    """Done Test"""


def test_lapse_mark_basic():
    """Test LapseMark class"""

    LapseMark._clearall()  # clear instances for debugging

    assert "LapseMark" in LapseMark.Registry
    assert LapseMark.Registry["LapseMark"] == LapseMark
    assert LapseMark.Names == ()

    with pytest.raises(HierError):
        act = LapseMark()  # requires iops with _boxer=boxer.name and _box=box.name


    hold = Hold()
    boxer = Boxer(hold=hold)
    box = Box(hold=hold)
    iops = dict(_boxer=boxer.name, _box=box.name)

    act = LapseMark(iops=iops, hold=hold)
    assert act.name == 'LapseMark1'
    assert act.iops == iops
    assert act.nabe == Nabes.enmark
    assert act.hold == hold
    assert act.Index == 2
    assert act.Instances[act.name] == act
    keys = ("", "boxer", boxer.name, "box", box.name, "lapse")
    assert keys in act.hold
    assert not act.hold[keys].value
    assert act() is None
    assert act.hold[keys].value is None

    LapseMark._clearall()  # clear instances for debugging
    tymist = Tymist(tock=1.0)
    hold = Hold()
    boxer = Boxer(tymth=tymist.tymen(), hold=hold)
    assert boxer.tyme == tymist.tyme == 0.0
    box = Box(hold=hold)
    iops = dict(_boxer=boxer.name, _box=box.name)

    act = LapseMark(iops=iops, hold=hold)
    assert act.name == 'LapseMark0'
    assert act.iops == iops
    assert act.nabe == Nabes.enmark
    assert act.hold == hold
    assert act.Index == 1
    assert act.Instances[act.name] == act

    keys = ("", "boxer", boxer.name, "box", box.name, "lapse")
    assert keys in act.hold
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme is None
    assert act.hold[keys]._now is None
    boxer.rewind()
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme is None
    assert act.hold[keys]._now == 0.0

    assert act() == 0.0
    assert act.hold[keys].value == 0.0
    assert act.hold[keys]._tyme == 0.0
    assert act.hold[keys]._now == 0.0

    """Done Test"""

def test_relapse_mark_basic():
    """Test RelapseMark class"""

    RelapseMark._clearall()  # clear instances for debugging

    assert "RelapseMark" in RelapseMark.Registry
    assert RelapseMark.Registry["RelapseMark"] == RelapseMark
    assert RelapseMark.Names == ()

    with pytest.raises(HierError):
        act = RelapseMark()  # requires iops with _boxer=boxer.name and _box=box.name


    hold = Hold()
    boxer = Boxer(hold=hold)
    box = Box(hold=hold)
    iops = dict(_boxer=boxer.name, _box=box.name)

    act = RelapseMark(iops=iops, hold=hold)
    assert act.name == 'RelapseMark1'
    assert act.iops == iops
    assert act.nabe == Nabes.remark
    assert act.hold == hold
    assert act.Index == 2
    assert act.Instances[act.name] == act
    keys = ("", "boxer", boxer.name, "box", box.name, "relapse")
    assert keys in act.hold
    assert not act.hold[keys].value
    assert act() is None
    assert act.hold[keys].value is None

    RelapseMark._clearall()  # clear instances for debugging
    tymist = Tymist(tock=1.0)
    hold = Hold()
    boxer = Boxer(tymth=tymist.tymen(), hold=hold)
    assert boxer.tyme == tymist.tyme == 0.0
    box = Box(hold=hold)
    iops = dict(_boxer=boxer.name, _box=box.name)

    act = RelapseMark(iops=iops, hold=hold)
    assert act.name == 'RelapseMark0'
    assert act.iops == iops
    assert act.nabe == Nabes.remark
    assert act.hold == hold
    assert act.Index == 1
    assert act.Instances[act.name] == act

    keys = ("", "boxer", boxer.name, "box", box.name, "relapse")
    assert keys in act.hold
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme is None
    assert act.hold[keys]._now is None
    boxer.rewind()
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme is None
    assert act.hold[keys]._now == 0.0

    assert act() == 0.0
    assert act.hold[keys].value == 0.0
    assert act.hold[keys]._tyme == 0.0
    assert act.hold[keys]._now == 0.0

    """Done Test"""


def test_count_basic():
    """Test Count class"""
    Count._clearall()  # clear instances for debugging

    assert "Count" in Count.Registry
    assert Count.Registry["Count"] == Count
    assert Count.Names == ('count',)

    with pytest.raises(HierError):
        act = Count()  # requires iops with _boxer=boxer.name and _box=box.name


    hold = Hold()
    boxer = Boxer(hold=hold)
    box = Box(hold=hold)
    iops = dict(_boxer=boxer.name, _box=box.name)
    keys = ("", "boxer", boxer.name, "box", box.name, "count")

    act = Count(iops=iops, hold=hold)
    assert act.name == 'Count1'
    assert act.iops == iops
    assert act.nabe == Nabes.redo
    assert act.hold == hold
    assert act.Index == 2
    assert act.Instances[act.name] == act

    assert keys in act.hold
    assert not act.hold[keys].value
    assert act() == 0
    assert act.hold[keys].value == 0

    Count._clearall()  # clear instances for debugging
    tymist = Tymist(tock=1.0)
    hold = Hold()
    boxer = Boxer(tymth=tymist.tymen(), hold=hold)
    assert boxer.tyme == tymist.tyme == 0.0
    box = Box(hold=hold)
    iops = dict(_boxer=boxer.name, _box=box.name)

    act = Count(iops=iops, hold=hold)
    assert act.name == 'Count0'
    assert act.iops == iops
    assert act.nabe == Nabes.redo
    assert act.hold == hold
    assert act.Index == 1
    assert act.Instances[act.name] == act

    assert keys in act.hold
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme is None
    assert act.hold[keys]._now is None
    boxer.rewind()
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme is None
    assert act.hold[keys]._now == 0.0

    assert act() == 0
    assert act.hold[keys].value == 0
    assert act.hold[keys]._tyme == 0.0
    assert act.hold[keys]._now == 0.0

    tymist.tick()
    assert act() == 1
    assert act.hold[keys].value == 1
    assert act.hold[keys]._tyme == 1.0
    assert act.hold[keys]._now == 1.0

    """Done Test"""


def test_discount_basic():
    """Test Discount class"""
    Discount._clearall()  # clear instances for debugging

    assert "Discount" in Discount.Registry
    assert Discount.Registry["Discount"] == Discount
    assert Discount.Names == ('discount',)

    with pytest.raises(HierError):
        act = Discount()  # requires iops with _boxer=boxer.name and _box=box.name


    hold = Hold()
    boxer = Boxer(hold=hold)
    box = Box(hold=hold)
    iops = dict(_boxer=boxer.name, _box=box.name)
    keys = ("", "boxer", boxer.name, "box", box.name, "count")

    act = Discount(iops=iops, hold=hold)
    assert act.name == 'Discount1'
    assert act.iops == iops
    assert act.nabe == Nabes.exdo
    assert act.hold == hold
    assert act.Index == 2
    assert act.Instances[act.name] == act

    assert keys in act.hold
    assert not act.hold[keys].value
    assert act() == None
    assert act.hold[keys].value == None

    Discount._clearall()  # clear instances for debugging
    tymist = Tymist(tock=1.0)
    hold = Hold()
    boxer = Boxer(tymth=tymist.tymen(), hold=hold)
    assert boxer.tyme == tymist.tyme == 0.0
    box = Box(hold=hold)
    iops = dict(_boxer=boxer.name, _box=box.name)

    act = Discount(iops=iops, hold=hold)
    assert act.name == 'Discount0'
    assert act.iops == iops
    assert act.nabe == Nabes.exdo
    assert act.hold == hold
    assert act.Index == 1
    assert act.Instances[act.name] == act

    assert keys in act.hold
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme is None
    assert act.hold[keys]._now is None
    boxer.rewind()
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme is None
    assert act.hold[keys]._now == 0.0

    assert act() == None
    assert act.hold[keys].value == None
    assert act.hold[keys]._tyme == 0.0
    assert act.hold[keys]._now == 0.0

    tymist.tick()
    act.hold[keys].value = 1
    assert act.hold[keys].value == 1
    assert act.hold[keys]._tyme == 1.0
    assert act.hold[keys]._now == 1.0

    assert act() == None  # resets
    assert act.hold[keys].value == None
    assert act.hold[keys]._tyme == 1.0
    assert act.hold[keys]._now == 1.0

    """Done Test"""


def test_bag_mark_basic():
    """Test BagMark class"""

    Mark._clearall()  # clear instances for debugging

    assert "BagMark" in BagMark.Registry
    assert BagMark.Registry["BagMark"] == BagMark
    assert BagMark.Names == ()

    with pytest.raises(HierError):
        # requires iops with _boxer=boxer.name and _box=box.name _key=Bag key
        act = BagMark()  # requires iops with _boxer=boxer.name and _box=box.name


    hold = Hold()
    boxer = Boxer(hold=hold)
    box = Box(hold=hold)
    key = "test"
    hold[key] = Bag()
    iops = dict(_boxer=boxer.name, _box=box.name, _key=key)

    act = BagMark(iops=iops, hold=hold)
    assert act.name == 'BagMark1'
    assert act.iops == iops
    assert act.nabe == Nabes.enmark
    assert act.hold == hold
    assert act.Index == 2
    assert act.Instances[act.name] == act
    assert act() is None

    """Done Test"""

def test_update_mark_basic():
    """Test UpdateMark class"""
    UpdateMark._clearall()  # clear instances for debugging

    assert "UpdateMark" in UpdateMark.Registry
    assert UpdateMark.Registry["UpdateMark"] == UpdateMark
    assert UpdateMark.Names == ()

    with pytest.raises(HierError):
        # requires iops with _boxer=boxer.name and _box=box.name and _key= bag key
        act = UpdateMark()


    hold = Hold()
    boxer = Boxer(hold=hold)
    box = Box(hold=hold)
    key = "test"
    hold[key] = Bag()
    iops = dict(_boxer=boxer.name, _box=box.name, _key=key)
    keys = ("", "boxer", boxer.name, "box", box.name, "update", key)

    act = UpdateMark(iops=iops, hold=hold)
    assert act.name == 'UpdateMark1'
    assert act.iops == iops
    assert act.nabe == Nabes.enmark
    assert act.hold == hold
    assert act.Index == 2
    assert act.Instances[act.name] == act
    assert keys in act.hold
    assert not act.hold[keys].value
    assert act() is None
    assert act.hold[keys].value is None

    UpdateMark._clearall()  # clear instances for debugging
    tymist = Tymist(tock=1.0)
    hold = Hold()
    boxer = Boxer(tymth=tymist.tymen(), hold=hold)
    assert boxer.tyme == tymist.tyme == 0.0
    box = Box(hold=hold)
    key = "test"
    hold[key] = Bag()
    iops = dict(_boxer=boxer.name, _box=box.name, _key=key)

    act = UpdateMark(iops=iops, hold=hold)
    assert act.name == 'UpdateMark0'
    assert act.iops == iops
    assert act.nabe == Nabes.enmark
    assert act.hold == hold
    assert act.Index == 1
    assert act.Instances[act.name] == act

    assert keys in act.hold
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme is None
    assert act.hold[keys]._now is None
    boxer.rewind()
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme is None
    assert act.hold[keys]._now == 0.0
    assert act() is None

    tymist.tick()
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme == 0.0
    assert act.hold[keys]._now == 1.0
    assert act() is None

    hold[key].value = True
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme == 1.0
    assert act.hold[keys]._now == 1.0
    assert act() == 1.0
    assert act.hold[keys].value == 1.0

    """Done Test"""


def test_reupdate_mark_basic():
    """Test ReupdateMark class"""
    ReupdateMark._clearall()  # clear instances for debugging

    assert "ReupdateMark" in ReupdateMark.Registry
    assert ReupdateMark.Registry["ReupdateMark"] == ReupdateMark
    assert ReupdateMark.Names == ()

    with pytest.raises(HierError):
        # requires iops with _boxer=boxer.name and _box=box.name and _key= bag key
        act = ReupdateMark()


    hold = Hold()
    boxer = Boxer(hold=hold)
    box = Box(hold=hold)
    key = "test"
    hold[key] = Bag()
    iops = dict(_boxer=boxer.name, _box=box.name, _key=key)
    keys = ("", "boxer", boxer.name, "box", box.name, "reupdate", key)

    act = ReupdateMark(iops=iops, hold=hold)
    assert act.name == 'ReupdateMark1'
    assert act.iops == iops
    assert act.nabe == Nabes.remark
    assert act.hold == hold
    assert act.Index == 2
    assert act.Instances[act.name] == act
    assert keys in act.hold
    assert not act.hold[keys].value
    assert act() is None
    assert act.hold[keys].value is None

    ReupdateMark._clearall()  # clear instances for debugging
    tymist = Tymist(tock=1.0)
    hold = Hold()
    boxer = Boxer(tymth=tymist.tymen(), hold=hold)
    assert boxer.tyme == tymist.tyme == 0.0
    box = Box(hold=hold)
    key = "test"
    hold[key] = Bag()
    iops = dict(_boxer=boxer.name, _box=box.name, _key=key)

    act = ReupdateMark(iops=iops, hold=hold)
    assert act.name == 'ReupdateMark0'
    assert act.iops == iops
    assert act.nabe == Nabes.remark
    assert act.hold == hold
    assert act.Index == 1
    assert act.Instances[act.name] == act

    assert keys in act.hold
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme is None
    assert act.hold[keys]._now is None
    boxer.rewind()
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme is None
    assert act.hold[keys]._now == 0.0
    assert act() is None

    tymist.tick()
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme == 0.0
    assert act.hold[keys]._now == 1.0
    assert act() is None

    hold[key].value = True
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme == 1.0
    assert act.hold[keys]._now == 1.0
    assert act() == 1.0
    assert act.hold[keys].value == 1.0

    """Done Test"""


def test_change_mark_basic():
    """Test ChangeMark class"""
    ChangeMark._clearall()  # clear instances for debugging

    assert "ChangeMark" in ChangeMark.Registry
    assert ChangeMark.Registry["ChangeMark"] == ChangeMark
    assert ChangeMark.Names == ()

    with pytest.raises(HierError):
        # requires iops with _boxer=boxer.name and _box=box.name and _key= bag key
        act = ChangeMark()

    hold = Hold()
    boxer = Boxer(hold=hold)
    box = Box(hold=hold)
    key = "test"
    hold[key] = Bag()
    iops = dict(_boxer=boxer.name, _box=box.name, _key=key)
    keys = ("", "boxer", boxer.name, "box", box.name, "change", key)

    act = ChangeMark(iops=iops, hold=hold)
    assert act.name == 'ChangeMark1'
    assert act.iops == iops
    assert act.nabe == Nabes.enmark
    assert act.hold == hold
    assert act.Index == 2
    assert act.Instances[act.name] == act
    assert keys in act.hold
    assert not act.hold[keys].value
    assert act() == (None, )
    assert act.hold[keys].value == (None, )

    ChangeMark._clearall()  # clear instances for debugging
    tymist = Tymist(tock=1.0)
    hold = Hold()
    boxer = Boxer(tymth=tymist.tymen(), hold=hold)
    assert boxer.tyme == tymist.tyme == 0.0
    box = Box(hold=hold)
    key = "test"
    hold[key] = Bag()
    iops = dict(_boxer=boxer.name, _box=box.name, _key=key)

    act = ChangeMark(iops=iops, hold=hold)
    assert act.name == 'ChangeMark0'
    assert act.iops == iops
    assert act.nabe == Nabes.enmark
    assert act.hold == hold
    assert act.Index == 1
    assert act.Instances[act.name] == act

    assert keys in act.hold
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme is None
    assert act.hold[keys]._now is None
    boxer.rewind()
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme is None
    assert act.hold[keys]._now == 0.0
    assert act() == (None,)

    tymist.tick()
    assert act.hold[keys].value == (None,)
    assert act.hold[keys]._tyme == 0.0
    assert act.hold[keys]._now == 1.0
    assert act() == (None,)

    hold[key].value = True
    assert act.hold[keys].value == (None,)
    assert act.hold[keys]._tyme == 1.0
    assert act.hold[keys]._now == 1.0
    assert act() == (True, )
    assert act.hold[keys].value == (True, )
    """Done Test"""


def test_rechange_mark_basic():
    """Test RechangeMark class"""
    RechangeMark._clearall()  # clear instances for debugging

    assert "RechangeMark" in RechangeMark.Registry
    assert RechangeMark.Registry["RechangeMark"] == RechangeMark
    assert RechangeMark.Names == ()

    with pytest.raises(HierError):
        # requires iops with _boxer=boxer.name and _box=box.name and _key= bag key
        act = RechangeMark()

    hold = Hold()
    boxer = Boxer(hold=hold)
    box = Box(hold=hold)
    key = "test"
    hold[key] = Bag()
    iops = dict(_boxer=boxer.name, _box=box.name, _key=key)
    keys = ("", "boxer", boxer.name, "box", box.name, "rechange", key)

    act = RechangeMark(iops=iops, hold=hold)
    assert act.name == 'RechangeMark1'
    assert act.iops == iops
    assert act.nabe == Nabes.remark
    assert act.hold == hold
    assert act.Index == 2
    assert act.Instances[act.name] == act
    assert keys in act.hold
    assert not act.hold[keys].value
    assert act() == (None, )
    assert act.hold[keys].value == (None, )

    RechangeMark._clearall()  # clear instances for debugging
    tymist = Tymist(tock=1.0)
    hold = Hold()
    boxer = Boxer(tymth=tymist.tymen(), hold=hold)
    assert boxer.tyme == tymist.tyme == 0.0
    box = Box(hold=hold)
    key = "test"
    hold[key] = Bag()
    iops = dict(_boxer=boxer.name, _box=box.name, _key=key)

    act = RechangeMark(iops=iops, hold=hold)
    assert act.name == 'RechangeMark0'
    assert act.iops == iops
    assert act.nabe == Nabes.remark
    assert act.hold == hold
    assert act.Index == 1
    assert act.Instances[act.name] == act

    assert keys in act.hold
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme is None
    assert act.hold[keys]._now is None
    boxer.rewind()
    assert act.hold[keys].value is None
    assert act.hold[keys]._tyme is None
    assert act.hold[keys]._now == 0.0
    assert act() == (None,)

    tymist.tick()
    assert act.hold[keys].value == (None,)
    assert act.hold[keys]._tyme == 0.0
    assert act.hold[keys]._now == 1.0
    assert act() == (None,)

    hold[key].value = True
    assert act.hold[keys].value == (None,)
    assert act.hold[keys]._tyme == 1.0
    assert act.hold[keys]._now == 1.0
    assert act() == (True, )
    assert act.hold[keys].value == (True, )

    """Done Test"""

def test_closeact_basic():
    """Test CloseAct class"""

    CloseAct._clearall()  # clear instances for debugging

    assert "CloseAct" in CloseAct.Registry
    assert CloseAct.Registry["CloseAct"] == CloseAct
    assert CloseAct.Names == ("close", "Close")
    for name in CloseAct.Names:
        assert name in CloseAct.Registry
        assert CloseAct.Registry[name] == CloseAct

    with pytest.raises(HierError):
        cact = CloseAct()  # requires iops with me

    tymist = Tymist()

    boxerName = "BoxerTest"
    boxName = "BoxTop"
    iops = dict(_boxer=boxerName, _box=boxName)

    hold = Hold()

    tymeKey = hold.tokey(("", "boxer", boxerName, "tyme"))
    hold[tymeKey] = Bag()
    hold[tymeKey].value = tymist.tyme

    activeKey = hold.tokey(("", "boxer", boxerName, "active"))
    hold[activeKey] = Bag()
    hold[activeKey].value = boxName

    tockKey = hold.tokey(("", "boxer", boxerName, "tock"))
    hold[tockKey] = Bag()
    hold[tockKey].value = tymist.tock

    tymth = tymist.tymen()
    for dom in hold.values():  # wind hold
        if isinstance(dom, TymeDom):
            dom._wind(tymth=tymth)

    name = "elk"


    hog = Hog(name=name, iops=iops, hold=hold, temp=True)
    assert hog.opened
    assert hog.file
    assert not hog.file.closed

    ciops = dict(it=hog, clear=True, **iops)

    cact = CloseAct(iops=ciops, hold=hold)
    assert cact.name == 'CloseAct1'
    assert cact.iops == ciops
    assert cact.nabe == Nabes.exdo
    assert cact.hold == hold
    assert cact.Index == 2
    assert cact.Instances[cact.name] == cact

    cact()
    assert not hog.opened
    assert not hog.file
    assert not os.path.exists(hog.path)


    """Done Test"""


if __name__ == "__main__":
    test_actbase()
    test_actify()
    test_act_basic()
    test_need_act()
    test_goact_basic()
    test_endact_basic()
    test_beact_basic()
    test_mark_basic()
    test_lapse_mark_basic()
    test_relapse_mark_basic()
    test_count_basic()
    test_discount_basic()
    test_bag_mark_basic()
    test_update_mark_basic()
    test_reupdate_mark_basic()
    test_change_mark_basic()
    test_rechange_mark_basic()
    test_closeact_basic()

