# -*- encoding: utf-8 -*-
"""
tests.core.test_cycling module

"""
import pytest

from hio.base import doing
from hio.base import doing
from hio.base.basing import State

def test_doist_once():
    """
    Test doist.once with dogs
    """
    doist = doing.Doist(tock=0.25)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == 0.25
    assert doist.real == False
    assert doist.limit == None
    assert doist.doers == []

    doer0 = doing.WhoDoer(tock=0.25, tymist=doist)
    doer1 = doing.WhoDoer(tock=0.5, tymist=doist)
    doers = [doer0, doer1]

    plys = doist.ready(doers=doers)
    assert len(plys) == 2
    assert [val[1] for val in plys] == [0.0, 0.0]
    for doer in doers:
        assert doer._tymist ==  doist
        assert doer.states == [State(tyme=0.0, context='enter', feed='_', count=0)]

    doist.once(plys)
    assert doist.tyme == 0.25  # on next cycle
    assert len(plys) == 2
    assert [val[1] for val in plys] == [0.25, 0.5]
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1)]

    doist.once(plys)
    assert doist.tyme == 0.5  # on next cycle
    assert len(plys) == 2
    assert [val[1] for val in plys] == [0.5, 0.5]
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.25, context='recur', feed=None, count=2)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1)]

    doist.once(plys)
    assert doist.tyme == 0.75  # on next cycle
    assert len(plys) == 2
    assert [val[1] for val in plys] == [0.75, 1.0]
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.25, context='recur', feed=None, count=2),
                            State(tyme=0.5, context='recur', feed=None, count=3)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.5, context='recur', feed=None, count=2)]

    doist.once(plys)
    assert doist.tyme == 1.0  # on next cycle
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

    doist.once(plys)
    assert doist.tyme == 1.25  # on next cycle
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

    doist.once(plys)
    assert doist.tyme == 1.50  # on next cycle
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

    doist.once(plys)
    assert doist.tyme == 1.75  # on next cycle
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

def test_doist_do():
    """
    Test doist.do with .close of .dogs
    """
    tock = 0.03125
    doist = doing.Doist(tock=tock)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == False
    assert doist.limit == None
    assert doist.doers == []

    doer0 = doing.WhoDoer(tock=tock, tymist=doist)
    doer1 = doing.WhoDoer(tock=tock*2, tymist=doist)
    assert doer0.tock == tock
    assert doer1.tock == tock * 2
    doers = [doer0, doer1]
    for doer in doers:
        assert doer._tymist == doist
        assert doer.states == []

    ticks = 4
    limit = tock * ticks
    doist.do(doers=doers, limit=limit)
    assert doist.tyme == limit == 0.125
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


    doist = doing.Doist(tock=tock, real=True, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == limit == 0.125
    assert doist.doers == []

    for doer in doers:
        doer.states = []
        assert doer.states == []
        doer._tymist = doist
        assert doer._tymist == doist

    doist.do(doers=doers)
    assert doist.tyme == limit == 0.125
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
    doist = doing.Doist(tock=tock, real=False, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == False
    assert doist.limit == limit == 0.125
    assert doist.doers == []

    for doer in doers:
        doer.states = []
        assert doer.states == []
        doer._tymist = doist
        assert doer._tymist == doist
        doer.tock = 0.0  # run asap
        assert doer.tock == 0.0

    doist.do(doers=doers)
    assert doist.tyme == limit
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.03125, context='recur', feed=None, count=2),
                            State(tyme=0.0625, context='recur', feed=None, count=3),
                            State(tyme=0.09375, context='recur', feed=None, count=4),
                            State(tyme=0.09375, context='exit', feed=None, count=5)]

    assert doer1.states == doer0.states

    doist = doing.Doist(tock=tock, real=True, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == limit == 0.125
    assert doist.doers == []

    for doer in doers:
        doer.states = []
        assert doer.states == []
        doer._tymist = doist
        assert doer._tymist == doist
        doer.tock = 0.0  # run asap
        assert doer.tock == 0.0

    doist.do(doers=doers)
    assert doist.tyme == limit
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
    doist = doing.Doist(tock=tock, real=False, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == False
    assert doist.limit == limit == 0.0625
    assert doist.doers == []

    for doer in doers:
        doer.states = []
        assert doer.states == []
        doer._tymist = doist
        assert doer._tymist == doist
        doer.tock = 0.0  # run asap
        assert doer.tock == 0.0

    doist.do(doers=doers)
    assert doist.tyme == limit
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.03125, context='recur', feed=None, count=2),
                            State(tyme=0.0625, context='close', feed=None, count=3),
                            State(tyme=0.0625, context='exit', feed=None, count=4)]

    assert doer1.states == doer0.states

    doist = doing.Doist(tock=tock, real=True, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == limit == 0.0625
    assert doist.doers == []

    for doer in doers:
        doer.states = []
        assert doer.states == []
        doer._tymist = doist
        assert doer._tymist == doist
        doer.tock = 0.0  # run asap
        assert doer.tock == 0.0

    doist.do(doers=doers)
    assert doist.tyme == limit
    assert doer0.states == [State(tyme=0.0, context='enter', feed='_', count=0),
                            State(tyme=0.0, context='recur', feed=None, count=1),
                            State(tyme=0.03125, context='recur', feed=None, count=2),
                            State(tyme=0.0625, context='close', feed=None, count=3),
                            State(tyme=0.0625, context='exit', feed=None, count=4)]

    assert doer1.states == doer0.states


    """End Test """


if __name__ == "__main__":
    test_doist_do()
