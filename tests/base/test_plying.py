# -*- encoding: utf-8 -*-
"""
tests.core.test_cycling module

"""
import pytest

from hio.base import plying
from hio.base import doing
from hio.base.basing import State

def test_plier_ply():
    """
    Test plier.ply() with doers
    """
    plier = plying.Plier(tock=0.25)
    assert plier.tyme == 0.0  # on next cycle
    assert plier.tock == 0.25
    assert plier.real == False
    assert plier.limit == None
    assert plier.doers == []

    doer0 = doing.WhoDoer(tock=0.25, ticker=plier)
    doer1 = doing.WhoDoer(tock=0.5, ticker=plier)
    doers = [doer0, doer1]

    plys = plier.ready(doers=doers)
    assert len(plys) == 2
    assert [val[1] for val in plys] == [0.0, 0.0]
    for doer in doers:
        assert doer.ticker ==  plier
        assert doer.states == [State(tyme=0.0, context='enter', feed='_', count=0)]

    plier.ply(plys)
    assert plier.tyme == 0.25  # on next cycle
    assert len(plys) == 2
    assert [val[1] for val in plys] == [0.25, 0.5]
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1)]

    plier.ply(plys)
    assert plier.tyme == 0.5  # on next cycle
    assert len(plys) == 2
    assert [val[1] for val in plys] == [0.5, 0.5]
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.25, context='recur', feed=None, count=2)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1)]

    plier.ply(plys)
    assert plier.tyme == 0.75  # on next cycle
    assert len(plys) == 2
    assert [val[1] for val in plys] == [0.75, 1.0]
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.25, context='recur', feed=None, count=2),
                            State(tyme=0.5, context='recur', feed=None, count=3)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.5, context='recur', feed=None, count=2)]

    plier.ply(plys)
    assert plier.tyme == 1.0  # on next cycle
    assert len(plys) == 1
    assert [val[1] for val in plys] == [1.0]
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.25, context='recur', feed=None, count=2),
                            State(tyme=0.5, context='recur', feed=None, count=3),
                            State(tyme=0.75, context='recur', feed=None, count=4),
                            State(tyme=0.75, context='exit', feed=None, count=5)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.5, context='recur', feed=None, count=2)]

    plier.ply(plys)
    assert plier.tyme == 1.25  # on next cycle
    assert len(plys) == 1
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.25, context='recur', feed=None, count=2),
                            State(tyme=0.5, context='recur', feed=None, count=3),
                            State(tyme=0.75, context='recur', feed=None, count=4),
                            State(tyme=0.75, context='exit', feed=None, count=5)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.5, context='recur', feed=None, count=2),
                            State(tyme=1.0, context='recur', feed=None, count=3)]

    plier.ply(plys)
    assert plier.tyme == 1.50  # on next cycle
    assert len(plys) == 1
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.25, context='recur', feed=None, count=2),
                            State(tyme=0.5, context='recur', feed=None, count=3),
                            State(tyme=0.75, context='recur', feed=None, count=4),
                            State(tyme=0.75, context='exit', feed=None, count=5)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.5, context='recur', feed=None, count=2),
                            State(tyme=1.0, context='recur', feed=None, count=3)]

    plier.ply(plys)
    assert plier.tyme == 1.75  # on next cycle
    assert len(plys) == 0
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.25, context='recur', feed=None, count=2),
                            State(tyme=0.5, context='recur', feed=None, count=3),
                            State(tyme=0.75, context='recur', feed=None, count=4),
                            State(tyme=0.75, context='exit', feed=None, count=5)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.5, context='recur', feed=None, count=2),
                            State(tyme=1.0, context='recur', feed=None, count=3),
                            State(tyme=1.5, context='recur', feed=None, count=4),
                            State(tyme=1.5, context='exit', feed=None, count=5)]

    """End Test """

def test_plier_run():
    """
    Test Player.cycle() with doers in deeds with abort
    """
    tock = 0.03125
    plier = plying.Plier(tock=tock)
    assert plier.tyme == 0.0  # on next cycle
    assert plier.tock == tock == 0.03125
    assert plier.real == False
    assert plier.limit == None
    assert plier.doers == []

    doer0 = doing.WhoDoer(tock=tock, ticker=plier)
    doer1 = doing.WhoDoer(tock=tock*2, ticker=plier)
    assert doer0.tock == tock
    assert doer1.tock == tock * 2
    doers = [doer0, doer1]
    for doer in doers:
        assert doer.ticker == plier
        assert doer.states == []

    ticks = 4
    limit = tock * ticks
    plier.run(doers=doers, limit=limit)
    assert plier.tyme == limit == 0.125
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.03125, context='recur', feed=None, count=2),
                            State(tyme=0.0625, context='recur', feed=None, count=3),
                            State(tyme=0.09375, context='recur', feed=None, count=4),
                            State(tyme=0.09375, context='exit', feed=None, count=5)]

    assert doer1.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.0625, context='recur', feed=None, count=2),
                            State(tyme=0.125, context='close', feed=None, count=3),
                            State(tyme=0.125, context='exit', feed=None, count=4)]


    plier = plying.Plier(tock=tock, real=True, limit=limit)
    assert plier.tyme == 0.0  # on next cycle
    assert plier.tock == tock == 0.03125
    assert plier.real == True
    assert plier.limit == limit == 0.125
    assert plier.doers == []

    for doer in doers:
        doer.states = []
        assert doer.states == []
        doer.ticker = plier
        assert doer.ticker == plier

    plier.run(doers=doers)
    assert plier.tyme == limit == 0.125
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.03125, context='recur', feed=None, count=2),
                            State(tyme=0.0625, context='recur', feed=None, count=3),
                            State(tyme=0.09375, context='recur', feed=None, count=4),
                            State(tyme=0.09375, context='exit', feed=None, count=5)]

    assert doer1.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.0625, context='recur', feed=None, count=2),
                            State(tyme=0.125, context='close', feed=None, count=3),
                            State(tyme=0.125, context='exit', feed=None, count=4)]

    #  Run ASAP
    plier = plying.Plier(tock=tock, real=False, limit=limit)
    assert plier.tyme == 0.0  # on next cycle
    assert plier.tock == tock == 0.03125
    assert plier.real == False
    assert plier.limit == limit == 0.125
    assert plier.doers == []

    for doer in doers:
        doer.states = []
        assert doer.states == []
        doer.ticker = plier
        assert doer.ticker == plier
        doer.tock = 0.0  # run asap
        assert doer.tock == 0.0

    plier.run(doers=doers)
    assert plier.tyme == limit
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.03125, context='recur', feed=None, count=2),
                            State(tyme=0.0625, context='recur', feed=None, count=3),
                            State(tyme=0.09375, context='recur', feed=None, count=4),
                            State(tyme=0.09375, context='exit', feed=None, count=5)]

    assert doer1.states == doer0.states

    plier = plying.Plier(tock=tock, real=True, limit=limit)
    assert plier.tyme == 0.0  # on next cycle
    assert plier.tock == tock == 0.03125
    assert plier.real == True
    assert plier.limit == limit == 0.125
    assert plier.doers == []

    for doer in doers:
        doer.states = []
        assert doer.states == []
        doer.ticker = plier
        assert doer.ticker == plier
        doer.tock = 0.0  # run asap
        assert doer.tock == 0.0

    plier.run(doers=doers)
    assert plier.tyme == limit
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.03125, context='recur', feed=None, count=2),
                            State(tyme=0.0625, context='recur', feed=None, count=3),
                            State(tyme=0.09375, context='recur', feed=None, count=4),
                            State(tyme=0.09375, context='exit', feed=None, count=5)]

    assert doer1.states == doer0.states

    #  Low limit force close
    ticks = 2
    limit = tock * ticks
    plier = plying.Plier(tock=tock, real=False, limit=limit)
    assert plier.tyme == 0.0  # on next cycle
    assert plier.tock == tock == 0.03125
    assert plier.real == False
    assert plier.limit == limit == 0.0625
    assert plier.doers == []

    for doer in doers:
        doer.states = []
        assert doer.states == []
        doer.ticker = plier
        assert doer.ticker == plier
        doer.tock = 0.0  # run asap
        assert doer.tock == 0.0

    plier.run(doers=doers)
    assert plier.tyme == limit
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.03125, context='recur', feed=None, count=2),
                            State(tyme=0.0625, context='close', feed=None, count=3),
                            State(tyme=0.0625, context='exit', feed=None, count=4)]

    assert doer1.states == doer0.states

    plier = plying.Plier(tock=tock, real=True, limit=limit)
    assert plier.tyme == 0.0  # on next cycle
    assert plier.tock == tock == 0.03125
    assert plier.real == True
    assert plier.limit == limit == 0.0625
    assert plier.doers == []

    for doer in doers:
        doer.states = []
        assert doer.states == []
        doer.ticker = plier
        assert doer.ticker == plier
        doer.tock = 0.0  # run asap
        assert doer.tock == 0.0

    plier.run(doers=doers)
    assert plier.tyme == limit
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.03125, context='recur', feed=None, count=2),
                            State(tyme=0.0625, context='close', feed=None, count=3),
                            State(tyme=0.0625, context='exit', feed=None, count=4)]

    assert doer1.states == doer0.states


    """End Test """


if __name__ == "__main__":
    test_plier_run()
