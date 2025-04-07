# -*- encoding: utf-8 -*-
"""tests.base.hier.test_acting module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest

from hio import Mixin, HierError
from hio.base.hier import Context, ActBase, actify, Need, Box, Boxer, Bag
from hio.base.hier import Act, Tract, EndAct

from hio.help import Mine

def test_act_basic():
    """Test Act class"""
    # clear registries for debugging
    Act._clear()

    assert "Act" in Act.Registry
    assert Act.Registry["Act"] == Act

    act = Act()
    assert act.name == "Act0"
    assert act.iops == {}
    assert act.context == Context.enter
    assert act.Index == 1
    assert act.Instances[act.name] == act
    assert act.mine == Mine()
    assert act.dock == None

    assert not act()

    """Done Test"""


def test_tract_basic():
    """Test Tract class"""
    # clear registries for debugging
    Tract._clear()

    assert "Tract" in Tract.Registry
    assert Tract.Registry["Tract"] == Tract

    tract = Tract()
    assert tract.name == "Tract0"
    assert tract.iops == {}
    assert tract.context == Context.transit
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
    # clear registries for debugging
    EndAct._clear()

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
    assert eact.context == Context.enter
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
    test_tract_basic()
    test_endact_basic()
