# -*- encoding: utf-8 -*-
"""
tests.core.test_cycling module

"""
import pytest

from hio.base.basing import Ctl, Stt
from hio.base import playing
from hio.base import acting


def test_player_cycle():
    """
    Test Player.cycle() with doers in deeds
    """
    player = playing.Player(tock=0.25)
    assert player.tyme == 0.0  # on next cycle
    assert player.tock == 0.25
    assert player.real == False
    assert player.limit == None
    assert player.doers == []

    doer0 = acting.WhoActor(tock=0.25, ticker=player)
    doer1 = acting.WhoActor(tock=0.5, ticker=player)
    doers = [doer0, doer1]
    for doer in doers:
        assert doer.ticker == player

    deeds = player.ready(doers=doers)
    assert len(deeds) == 2
    assert [val[1] for val in deeds] == [0.0, 0.0]
    for doer in doers:
        assert doer.states == []


    player.cycle(deeds)
    assert player.tyme == 0.25  # on next cycle
    assert len(deeds) == 2
    assert [val[1] for val in deeds] == [0.25, 0.5]
    assert doer0.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False)]
    assert doer1.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False)]

    player.cycle(deeds)
    assert player.tyme == 0.5  # on next cycle
    assert len(deeds) == 2
    assert [val[1] for val in deeds] == [0.5, 0.5]
    assert doer0.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False),
                            (0.25, 'recur', 'recurring', 'recur', False)]
    assert doer1.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False)]


    player.cycle(deeds)
    assert player.tyme == 0.75  # on next cycle
    assert len(deeds) == 2
    assert [val[1] for val in deeds] == [0.75, 1.0]
    assert doer0.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False),
                            (0.25, 'recur', 'recurring', 'recur', False),
                            (0.5, 'recur', 'recurring', 'recur', False)]
    assert doer1.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False),
                            (0.5, 'recur', 'recurring', 'recur', False)]


    doer0.desire = Ctl.exit
    doer1.desire = Ctl.exit
    player.cycle(deeds)
    assert player.tyme == 1.0  # on next cycle
    assert len(deeds) == 1
    assert [val[1] for val in deeds] == [1.0]
    assert doer0.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False),
                            (0.25, 'recur', 'recurring', 'recur', False),
                            (0.5, 'recur', 'recurring', 'recur', False),
                            (0.75, 'exit', 'recurring', 'exit', True)]
    assert doer1.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False),
                            (0.5, 'recur', 'recurring', 'recur', False)]

    player.cycle(deeds)
    assert player.tyme == 1.25  # on next cycle
    assert len(deeds) == 0
    assert doer0.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False),
                            (0.25, 'recur', 'recurring', 'recur', False),
                            (0.5, 'recur', 'recurring', 'recur', False),
                            (0.75, 'exit', 'recurring', 'exit', True)]
    assert doer1.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False),
                            (0.5, 'recur', 'recurring', 'recur', False),
                            (1.0, 'exit', 'recurring', 'exit', True)]

    """End Test """


if __name__ == "__main__":
    test_test()
