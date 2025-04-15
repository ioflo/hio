# -*- encoding: utf-8 -*-
"""tests.base.hier.test_acting module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest

from hio import Mixin, HierError
from hio.base.hier import Nabe, ActBase, actify, Need, Box, Boxer, Bag
from hio.base.hier import Act, Tract, EndAct

from hio.help import Mine

def test_act_basic():
    """Test Act class"""

    Act._clearall()  # clear instances for debugging

    assert "Act" in Act.Registry
    assert Act.Registry["Act"] == Act

    act = Act()
    assert act.name == "Act0"
    assert act.iops == {'M': {}, 'D': None}
    assert act.nabe == Nabe.entry
    assert act.Index == 1
    assert act.Instances[act.name] == act
    assert act.mine == Mine()
    assert act.dock == None
    assert callable(act.deed)
    assert act._code is None
    assert not act.compiled

    assert act() == act.iops

    iops = dict(a=1, b=2)
    act = Act(iops=iops, nabe=Nabe.redo)
    assert act.name == "Act1"
    assert act.iops == {'a': 1, 'b': 2, 'M': {}, 'D': None}
    assert act.nabe == Nabe.redo
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
    assert act.nabe == Nabe.entry
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
    assert act.nabe == Nabe.entry
    assert act.Index == 4
    assert act.Instances[act.name] == act
    assert act.mine == mine
    assert act.dock == None
    assert not callable(act.deed)
    assert act.deed == deed
    assert act._code is None
    assert not act.compiled

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


def test_tract_basic():
    """Test Tract class"""

    Tract._clearall()  # clear instances for debugging

    assert "Tract" in Tract.Registry
    assert Tract.Registry["Tract"] == Tract

    tract = Tract()
    assert tract.name == "Tract0"
    assert tract.iops == {}
    assert tract.nabe == Nabe.transit
    assert tract.mine == Mine()
    assert tract.dock == None
    assert tract.Index == 1
    assert tract.Instances[tract.name] == tract
    assert tract.dest == 'next'
    assert isinstance(tract.need, Need)
    assert tract.need()

    with pytest.raises(HierError):
        assert not tract()  # since default .dest not yet resolved

    mine = Mine()
    mine.cycle = Bag(value=3)
    box = Box(mine=Mine)
    need = Need(expr='M.cycle.value >= 3', mine=mine)
    tract = Tract(dest=box, need=need)
    assert not tract.need.compiled

    dest = tract()
    assert dest == box
    assert tract.need.compiled

    mine.cycle.value = 1
    assert not tract()
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
    assert eact.nabe == Nabe.entry
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

if __name__ == "__main__":
    test_act_basic()
    test_need_act()
    test_tract_basic()
    test_endact_basic()
