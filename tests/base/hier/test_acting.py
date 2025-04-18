# -*- encoding: utf-8 -*-
"""tests.base.hier.test_acting module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest

from hio import Mixin, HierError
from hio.base import Tymist
from hio.base.hier import Nabes, ActBase, actify, Need, Box, Boxer, Bag
from hio.base.hier import (Act, Goact, EndAct, Beact,
                          Mark, LapseMark, RelapseMark)

from hio.help import Mine

def test_act_basic():
    """Test Act class"""

    Act._clearall()  # clear instances for debugging

    assert "Act" in Act.Registry
    assert Act.Registry["Act"] == Act

    act = Act()
    assert act.name == "Act0"
    assert act.iops == {'M': {}, 'D': None}
    assert act.nabe == Nabes.endo
    assert act.Index == 1
    assert act.Instances[act.name] == act
    assert act.mine == Mine()
    assert act.dock == None
    assert callable(act.deed)
    assert act._code is None
    assert not act.compiled

    assert act() == act.iops

    iops = dict(a=1, b=2)
    act = Act(iops=iops, nabe=Nabes.redo)
    assert act.name == "Act1"
    assert act.iops == {'a': 1, 'b': 2, 'M': {}, 'D': None}
    assert act.nabe == Nabes.redo
    assert act.Index == 2
    assert act.Instances[act.name] == act
    assert act.mine == Mine()
    assert act.dock == None
    assert callable(act.deed)
    assert act._code is None
    assert not act.compiled

    assert act() == act.iops

    def dumb(**iops):
        M = iops['M']
        if 'count' not in M:
            M['count'] = Bag()
        if M.count.value is None:
            M.count.value = 0
        M.count.value += 1
        return (M.count.value, len(iops), iops)

    iops = dict(when="now", why="because")
    act = Act(dumb, iops=iops)
    assert act.name == "Act2"
    assert act.iops == {'when': 'now', 'why': 'because', 'M': {}, 'D': None}
    assert act.nabe == Nabes.endo
    assert act.Index == 3
    assert act.Instances[act.name] == act
    assert act.mine == Mine()
    assert act.dock == None
    assert callable(act.deed)
    assert act.deed == dumb
    assert act._code is None
    assert not act.compiled

    assert act() == (1, 4, {'when': 'now',
                            'why': 'because',
                            'M': {'count': Bag(value=1)},
                            'D': None})

    iops = dict(fix=3)
    mine = Mine()
    mine.stuff = Bag()
    mine.stuff.value = 0
    deed = "M.stuff.value += 1\n"
    act = Act(deed, mine=mine, iops=iops)
    assert act.name == "Act3"
    assert act.iops == {'fix': 3, 'M': {'stuff': Bag(value=0)}, 'D': None}
    assert act.nabe == Nabes.endo
    assert act.Index == 4
    assert act.Instances[act.name] == act
    assert act.mine == mine
    assert act.dock == None
    assert not callable(act.deed)
    assert act.deed == deed
    assert act._code
    assert act.compiled

    assert act() == None
    assert act._code is not None
    assert act.compiled
    assert mine.stuff.value == 1

    assert act() == None
    assert act.compiled
    assert mine.stuff.value == 2

    """Done Test"""

def test_need_act():
    """Test Act using Need as its deed"""

    mine = Mine()
    need = Need(mine=mine)
    act = Act(need, mine=mine)
    assert act() == True


    mine.cycle = Bag(value=2)
    mine.turn = Bag(value=2)
    expr = "M.cycle.value > 3 and M.turn.value <= 2"
    need = Need(expr=expr, mine=mine)
    act = Act(deed=need, mine=mine)
    assert act() == False

    mine.cycle.value = 5
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
    assert goact.mine == Mine()
    assert goact.dock == None
    assert goact.Index == 1
    assert goact.Instances[goact.name] == goact
    assert goact.dest == 'next'
    assert isinstance(goact.need, Need)
    assert goact.need()

    with pytest.raises(HierError):
        assert not goact()  # since default .dest not yet resolved

    mine = Mine()
    mine.cycle = Bag(value=3)
    box = Box(mine=Mine)
    need = Need(expr='M.cycle.value >= 3', mine=mine)
    goact = Goact(dest=box, need=need)
    assert goact.need.compiled

    dest = goact()
    assert dest == box
    assert goact.need.compiled

    mine.cycle.value = 1
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


    mine = Mine()
    boxer = Boxer(mine=mine)
    iops = dict(_boxer=boxer.name)

    eact = EndAct(iops=iops, mine=mine)
    assert eact.name == "EndAct1"
    assert eact.iops == iops
    assert eact.nabe == Nabes.endo
    assert eact.mine == mine
    assert eact.dock == None
    assert eact.Index == 2
    assert eact.Instances[eact.name] == eact
    keys = ("", "boxer", boxer.name, "end")
    assert keys in eact.mine
    assert not eact.mine[keys].value
    eact()
    assert eact.mine[keys].value


    """Done Test"""

def test_beact_basic():
    """Test Beact class"""

    Beact._clearall()  # clear instances for debugging

    assert "Beact" in Beact.Registry
    assert Beact.Registry["Beact"] == Beact

    with pytest.raises(HierError):
        act = Beact(lhs="stuff.value")

    mine = Mine()
    mine.stuff = Bag()

    with pytest.raises(HierError):
        act = Beact(lhs="stuff.kind", mine=mine)

    Beact._clearall()  # clear instances for debugging

    mine = Mine()
    mine.stuff = Bag()

    act = Beact(lhs=("stuff", "value"), mine=mine)
    assert act.name == "Beact0"
    assert act.iops == {'M': {'stuff': Bag(value=None)}, 'D': None}
    assert act.nabe == Nabes.endo
    assert act.Index == 1
    assert act.Instances[act.name] == act
    assert act.mine == mine
    assert act.dock is None
    assert act.lhs == ("stuff", "value")
    assert act.rhs is None
    assert act._code is None
    assert not act.compiled
    assert act() == None
    assert mine["stuff"]["value"] == None

    act.lhs = "stuff.value"
    assert act.lhs == ("stuff", "value")
    assert act() == None
    assert mine["stuff"]["value"] == None
    assert not act.compiled

    act.rhs = "5"
    assert not act.compiled
    assert act() == 5
    assert act.compiled
    assert mine["stuff"]["value"] == 5

    def dummy(**iops):
        return True

    act.rhs = dummy
    assert not act.compiled
    assert act() == True
    assert not act.compiled
    assert mine["stuff"]["value"] == True

    iops = dict(a=1, b=2)
    act = Beact(lhs="stuff.value", rhs=dummy, mine=mine, iops=iops, nabe=Nabes.redo)
    assert act.name == "Beact1"
    assert act.iops == {'a': 1, 'b': 2, 'M': {'stuff': Bag(value=True)}, 'D': None}
    assert act.nabe == Nabes.redo
    assert act.Index == 2
    assert act.Instances[act.name] == act
    assert act.mine == mine
    assert act.dock is None
    assert act.lhs == ("stuff", "value")
    assert act.rhs is dummy
    assert act._code is None
    assert not act.compiled
    assert act() == True
    assert act.mine.stuff.value == True

    act = Beact(lhs="stuff.value", rhs="2**5", mine=mine, nabe=Nabes.rendo)
    assert act.name == "Beact2"
    assert act.iops =={'M': {'stuff': Bag(value=True)}, 'D': None}
    assert act.nabe == Nabes.rendo
    assert act.Index == 3
    assert act.Instances[act.name] == act
    assert act.mine == mine
    assert act.dock is None
    assert act.lhs == ("stuff", "value")
    assert act.rhs is "2**5"
    assert act._code
    assert act.compiled
    assert act() == 32
    assert act.mine.stuff.value == 32

    """Done Test"""


def test_mark_basic():
    """Test Mark class"""

    Mark._clearall()  # clear instances for debugging

    assert "Mark" in Mark.Registry
    assert Mark.Registry["Mark"] == Mark
    assert Mark.Names == ()

    with pytest.raises(HierError):
        act = Mark()  # requires iops with _boxer=boxer.name and _box=box.name


    mine = Mine()
    boxer = Boxer(mine=mine)
    box = Box(mine=Mine)
    iops = dict(_boxer=boxer.name, _box=box.name)

    act = Mark(iops=iops, mine=mine)
    assert act.name == 'Mark1'
    assert act.iops == iops
    assert act.nabe == Nabes.enmark
    assert act.mine == mine
    assert act.dock == None
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


    mine = Mine()
    boxer = Boxer(mine=mine)
    box = Box(mine=Mine)
    iops = dict(_boxer=boxer.name, _box=box.name)

    act = LapseMark(iops=iops, mine=mine)
    assert act.name == 'LapseMark1'
    assert act.iops == iops
    assert act.nabe == Nabes.enmark
    assert act.mine == mine
    assert act.dock == None
    assert act.Index == 2
    assert act.Instances[act.name] == act
    keys = ("", "boxer", boxer.name, "box", box.name, "lapse")
    assert keys in act.mine
    assert not act.mine[keys].value
    assert act() is None
    assert act.mine[keys].value is None

    LapseMark._clearall()  # clear instances for debugging
    tymist = Tymist(tock=1.0)
    mine = Mine()
    boxer = Boxer(tymth=tymist.tymen(), mine=mine)
    assert boxer.tyme == tymist.tyme == 0.0
    box = Box(mine=Mine)
    iops = dict(_boxer=boxer.name, _box=box.name)

    act = LapseMark(iops=iops, mine=mine)
    assert act.name == 'LapseMark0'
    assert act.iops == iops
    assert act.nabe == Nabes.enmark
    assert act.mine == mine
    assert act.dock == None
    assert act.Index == 1
    assert act.Instances[act.name] == act

    keys = ("", "boxer", boxer.name, "box", box.name, "lapse")
    assert keys in act.mine
    assert act.mine[keys].value is None
    assert act.mine[keys]._tyme is None
    assert act.mine[keys]._now is None
    boxer.rewind()
    assert act.mine[keys].value is None
    assert act.mine[keys]._tyme is None
    assert act.mine[keys]._now == 0.0

    assert act() == 0.0
    assert act.mine[keys].value == 0.0
    assert act.mine[keys]._tyme == 0.0
    assert act.mine[keys]._now == 0.0

    """Done Test"""

def test_relapse_mark_basic():
    """Test RelapseMark class"""

    RelapseMark._clearall()  # clear instances for debugging

    assert "RelapseMark" in RelapseMark.Registry
    assert RelapseMark.Registry["RelapseMark"] == RelapseMark
    assert RelapseMark.Names == ()

    with pytest.raises(HierError):
        act = RelapseMark()  # requires iops with _boxer=boxer.name and _box=box.name


    mine = Mine()
    boxer = Boxer(mine=mine)
    box = Box(mine=Mine)
    iops = dict(_boxer=boxer.name, _box=box.name)

    act = RelapseMark(iops=iops, mine=mine)
    assert act.name == 'RelapseMark1'
    assert act.iops == iops
    assert act.nabe == Nabes.enmark
    assert act.mine == mine
    assert act.dock == None
    assert act.Index == 2
    assert act.Instances[act.name] == act
    keys = ("", "boxer", boxer.name, "box", box.name, "relapse")
    assert keys in act.mine
    assert not act.mine[keys].value
    assert act() is None
    assert act.mine[keys].value is None

    RelapseMark._clearall()  # clear instances for debugging
    tymist = Tymist(tock=1.0)
    mine = Mine()
    boxer = Boxer(tymth=tymist.tymen(), mine=mine)
    assert boxer.tyme == tymist.tyme == 0.0
    box = Box(mine=Mine)
    iops = dict(_boxer=boxer.name, _box=box.name)

    act = RelapseMark(iops=iops, mine=mine)
    assert act.name == 'RelapseMark0'
    assert act.iops == iops
    assert act.nabe == Nabes.enmark
    assert act.mine == mine
    assert act.dock == None
    assert act.Index == 1
    assert act.Instances[act.name] == act

    keys = ("", "boxer", boxer.name, "box", box.name, "relapse")
    assert keys in act.mine
    assert act.mine[keys].value is None
    assert act.mine[keys]._tyme is None
    assert act.mine[keys]._now is None
    boxer.rewind()
    assert act.mine[keys].value is None
    assert act.mine[keys]._tyme is None
    assert act.mine[keys]._now == 0.0

    assert act() == 0.0
    assert act.mine[keys].value == 0.0
    assert act.mine[keys]._tyme == 0.0
    assert act.mine[keys]._now == 0.0

    """Done Test"""


if __name__ == "__main__":
    test_act_basic()
    test_need_act()
    test_goact_basic()
    test_endact_basic()
    test_beact_basic()
    test_mark_basic()
    test_lapse_mark_basic()
    test_relapse_mark_basic()
