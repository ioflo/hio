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

def test_player_cycle_abort():
    """
    Test Player.cycle() with doers in deeds with abort
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

    doer0.desire = Ctl.abort
    doer1.desire = Ctl.abort
    player.cycle(deeds)
    assert player.tyme == 1.0  # on next cycle
    assert len(deeds) == 1
    assert [val[1] for val in deeds] == [1.0]
    assert doer0.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False),
                            (0.25, 'recur', 'recurring', 'recur', False),
                            (0.5, 'recur', 'recurring', 'recur', False),
                            (0.75, 'exit', 'recurring', 'abort', False)]
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
                            (0.75, 'exit', 'recurring', 'abort', False)]
    assert doer1.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False),
                            (0.5, 'recur', 'recurring', 'recur', False),
                            (1.0, 'exit', 'recurring', 'abort', False)]
    """End Test """


def test_player_run():
    """
    Test Player.cycle() with doers in deeds with abort
    """
    tock = 0.03125
    player = playing.Player(tock=tock)
    assert player.tyme == 0.0  # on next cycle
    assert player.tock == tock == 0.03125
    assert player.real == False
    assert player.limit == None
    assert player.doers == []

    doer0 = acting.WhoActor(tock=tock, ticker=player)
    doer1 = acting.WhoActor(tock=tock*2, ticker=player)
    assert doer0.tock == tock
    assert doer1.tock == tock *  2
    doers = [doer0, doer1]
    for doer in doers:
        assert doer.ticker == player
        assert doer.state == Stt.exited
        assert doer.states == []

    ticks = 8
    limit = tock * ticks
    player.run(doers=doers, limit=limit)
    assert player.tyme == limit
    assert doer0.state == Stt.aborted
    assert doer1.state == Stt.aborted
    assert len(doer0.states) == ticks +  2
    assert doer0.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False),
                            (0.03125, 'recur', 'recurring', 'recur', False),
                            (0.0625, 'recur', 'recurring', 'recur', False),
                            (0.09375, 'recur', 'recurring', 'recur', False),
                            (0.125, 'recur', 'recurring', 'recur', False),
                            (0.15625, 'recur', 'recurring', 'recur', False),
                            (0.1875, 'recur', 'recurring', 'recur', False),
                            (0.21875, 'recur', 'recurring', 'recur', False),
                            (0.25, 'exit', 'recurring', 'recur', False)]

    assert len(doer1.states) == ticks / 2 +  2
    assert doer1.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False),
                            (0.0625, 'recur', 'recurring', 'recur', False),
                            (0.125, 'recur', 'recurring', 'recur', False),
                            (0.1875, 'recur', 'recurring', 'recur', False),
                            (0.25, 'exit', 'recurring', 'recur', False)]



    player = playing.Player(tock=tock, real=True, limit=limit)
    assert player.tyme == 0.0  # on next cycle
    assert player.tock == tock == 0.03125
    assert player.real == True
    assert player.limit == limit == 0.25
    assert player.doers == []

    for doer in doers:
        doer.states = []
        doer.ticker = player

    for doer in doers:
        assert doer.ticker == player
        assert doer.state == Stt.aborted
        assert doer.states == []

    player.run(doers=doers)
    assert player.tyme == limit
    assert doer0.state == Stt.aborted
    assert doer1.state == Stt.aborted
    assert len(doer0.states) == ticks +  2
    assert doer0.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False),
                            (0.03125, 'recur', 'recurring', 'recur', False),
                            (0.0625, 'recur', 'recurring', 'recur', False),
                            (0.09375, 'recur', 'recurring', 'recur', False),
                            (0.125, 'recur', 'recurring', 'recur', False),
                            (0.15625, 'recur', 'recurring', 'recur', False),
                            (0.1875, 'recur', 'recurring', 'recur', False),
                            (0.21875, 'recur', 'recurring', 'recur', False),
                            (0.25, 'exit', 'recurring', 'recur', False)]
    assert len(doer1.states) == ticks / 2 +  2
    assert doer1.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False),
                            (0.0625, 'recur', 'recurring', 'recur', False),
                            (0.125, 'recur', 'recurring', 'recur', False),
                            (0.1875, 'recur', 'recurring', 'recur', False),
                            (0.25, 'exit', 'recurring', 'recur', False)]


    player = playing.Player(tock=tock, real=False, limit=limit)
    assert player.tyme == 0.0  # on next cycle
    assert player.tock == tock == 0.03125
    assert player.real == False
    assert player.limit == limit == 0.25
    assert player.doers == []

    for doer in doers:
        doer.states = []
        doer.ticker = player
        doer.tock = 0.0  # run asap

    for doer in doers:
        assert doer.ticker == player
        assert doer.state == Stt.aborted
        assert doer.states == []
        assert doer.tock == 0.0


    player.run(doers=doers)
    assert player.tyme == limit
    assert doer0.state == Stt.aborted
    assert doer1.state == Stt.aborted
    assert len(doer0.states) == ticks +  2
    assert doer0.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False),
                            (0.03125, 'recur', 'recurring', 'recur', False),
                            (0.0625, 'recur', 'recurring', 'recur', False),
                            (0.09375, 'recur', 'recurring', 'recur', False),
                            (0.125, 'recur', 'recurring', 'recur', False),
                            (0.15625, 'recur', 'recurring', 'recur', False),
                            (0.1875, 'recur', 'recurring', 'recur', False),
                            (0.21875, 'recur', 'recurring', 'recur', False),
                            (0.25, 'exit', 'recurring', 'recur', False)]

    assert doer1.states == doer0.states



    player = playing.Player(tock=tock, real=True, limit=limit)
    assert player.tyme == 0.0  # on next cycle
    assert player.tock == tock == 0.03125
    assert player.real == True
    assert player.limit == limit == 0.25
    assert player.doers == []

    for doer in doers:
        doer.states = []
        doer.ticker = player
        doer.tock = 0.0  # run asap

    for doer in doers:
        assert doer.ticker == player
        assert doer.state == Stt.aborted
        assert doer.states == []
        assert doer.tock == 0.0


    player.run(doers=doers)
    assert player.tyme == limit
    assert doer0.state == Stt.aborted
    assert doer1.state == Stt.aborted
    assert len(doer0.states) == ticks +  2
    assert doer0.states == [(0.0, 'enter', 'exited', 'recur', False),
                            (0.0, 'recur', 'entered', 'recur', False),
                            (0.03125, 'recur', 'recurring', 'recur', False),
                            (0.0625, 'recur', 'recurring', 'recur', False),
                            (0.09375, 'recur', 'recurring', 'recur', False),
                            (0.125, 'recur', 'recurring', 'recur', False),
                            (0.15625, 'recur', 'recurring', 'recur', False),
                            (0.1875, 'recur', 'recurring', 'recur', False),
                            (0.21875, 'recur', 'recurring', 'recur', False),
                            (0.25, 'exit', 'recurring', 'recur', False)]

    assert doer1.states == doer0.states

    """End Test """


if __name__ == "__main__":
    test_player_run()
