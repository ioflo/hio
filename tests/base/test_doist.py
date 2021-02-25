# -*- encoding: utf-8 -*-
"""
tests.core.test_cycling module

"""
import pytest
import inspect

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

    dogs = doist.ready(doers=doers)
    assert len(dogs) == 2
    assert [val[1] for val in dogs] == [0.0, 0.0]
    for doer in doers:
        assert doer._tymist ==  doist
        assert doer.states == [State(tyme=0.0, context='enter', feed=0.0, count=0)]
        assert doer.done == False

    doist.once(dogs)
    assert doist.tyme == 0.25  # on next cycle
    assert len(dogs) == 2
    assert [val[1] for val in dogs] == [0.25, 0.5]
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1)]

    doist.once(dogs)
    assert doist.tyme == 0.5  # on next cycle
    assert len(dogs) == 2
    assert [val[1] for val in dogs] == [0.5, 0.5]
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.25, context='recur', feed=0.25, count=2)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1)]

    doist.once(dogs)
    assert doist.tyme == 0.75  # on next cycle
    assert len(dogs) == 2
    assert [val[1] for val in dogs] == [0.75, 1.0]
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.25, context='recur', feed=0.25, count=2),
                            State(tyme=0.5, context='recur', feed=0.5, count=3)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.5, context='recur', feed=0.5, count=2)]

    doist.once(dogs)
    assert doist.tyme == 1.0  # on next cycle
    assert len(dogs) == 1
    assert [val[1] for val in dogs] == [1.0]
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.25, context='recur', feed=0.25, count=2),
                            State(tyme=0.5, context='recur', feed=0.5, count=3),
                            State(tyme=0.75, context='recur', feed=0.75, count=4),
                            State(tyme=0.75, context='exit', feed=None, count=5)]
    assert doer0.done == True
    assert doer1.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.5, context='recur', feed=0.5, count=2)]

    doist.once(dogs)
    assert doist.tyme == 1.25  # on next cycle
    assert len(dogs) == 1
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.25, context='recur', feed=0.25, count=2),
                            State(tyme=0.5, context='recur', feed=0.5, count=3),
                            State(tyme=0.75, context='recur', feed=0.75, count=4),
                            State(tyme=0.75, context='exit', feed=None, count=5)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.5, context='recur', feed=0.5, count=2),
                            State(tyme=1.0, context='recur', feed=1.0, count=3)]

    doist.once(dogs)
    assert doist.tyme == 1.50  # on next cycle
    assert len(dogs) == 1
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.25, context='recur', feed=0.25, count=2),
                            State(tyme=0.5, context='recur', feed=0.5, count=3),
                            State(tyme=0.75, context='recur', feed=0.75, count=4),
                            State(tyme=0.75, context='exit', feed=None, count=5)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.5, context='recur', feed=0.5, count=2),
                            State(tyme=1.0, context='recur', feed=1.0, count=3)]

    doist.once(dogs)
    assert doist.tyme == 1.75  # on next cycle
    assert len(dogs) == 0
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.25, context='recur', feed=0.25, count=2),
                            State(tyme=0.5, context='recur', feed=0.5, count=3),
                            State(tyme=0.75, context='recur', feed=0.75, count=4),
                            State(tyme=0.75, context='exit', feed=None, count=5)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.5, context='recur', feed=0.5, count=2),
                            State(tyme=1.0, context='recur', feed=1.0, count=3),
                            State(tyme=1.5, context='recur', feed=1.5, count=4),
                            State(tyme=1.5, context='exit', feed=None, count=5)]
    assert doer1.done == True

    """End Test """


def test_doist_doers():
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
        assert doer.count == None
        assert doer.done == None

    ticks = 4
    limit = tock * ticks
    doist.do(doers=doers, limit=limit)
    assert doist.tyme == limit == 0.125
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.03125, context='recur', feed=0.03125, count=2),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=3),
                            State(tyme=0.09375, context='recur', feed=0.09375, count=4),
                            State(tyme=0.09375, context='exit', feed=None, count=5)]
    assert doer0.done == True

    assert doer1.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=2),
                            State(tyme=0.125, context='close', feed=None, count=3),
                            State(tyme=0.125, context='exit', feed=None, count=4)]
    assert doer1.done == False

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
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.03125, context='recur', feed=0.03125, count=2),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=3),
                            State(tyme=0.09375, context='recur', feed=0.09375, count=4),
                            State(tyme=0.09375, context='exit', feed=None, count=5)]
    assert doer0.done == True

    assert doer1.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=2),
                            State(tyme=0.125, context='close', feed=None, count=3),
                            State(tyme=0.125, context='exit', feed=None, count=4)]
    assert doer1.done == False

    # doers passed to Doist init
    doist = doing.Doist(tock=tock, real=True, limit=limit, doers=doers)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == limit == 0.125
    assert doist.doers == doers

    for doer in doers:
        doer.states = []
        assert doer.states == []
        doer._tymist = doist
        assert doer._tymist == doist

    doist.do()
    assert doist.tyme == limit == 0.125
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.03125, context='recur', feed=0.03125, count=2),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=3),
                            State(tyme=0.09375, context='recur', feed=0.09375, count=4),
                            State(tyme=0.09375, context='exit', feed=None, count=5)]
    assert doer0.done == True

    assert doer1.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=2),
                            State(tyme=0.125, context='close', feed=None, count=3),
                            State(tyme=0.125, context='exit', feed=None, count=4)]
    assert doer1.done == False

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
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.03125, context='recur', feed=0.03125, count=2),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=3),
                            State(tyme=0.09375, context='recur', feed=0.09375, count=4),
                            State(tyme=0.09375, context='exit', feed=None, count=5)]
    assert doer0.done == doer1.done == True
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
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.03125, context='recur', feed=0.03125, count=2),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=3),
                            State(tyme=0.09375, context='recur', feed=0.09375, count=4),
                            State(tyme=0.09375, context='exit', feed=None, count=5)]
    assert doer0.done == doer1.done == True
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
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.03125, context='recur', feed=0.03125, count=2),
                            State(tyme=0.0625, context='close', feed=None, count=3),
                            State(tyme=0.0625, context='exit', feed=None, count=4)]
    assert doer0.done == doer1.done == False

    assert doer1.states == doer0.states

    #  low limit force close real time
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
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.03125, context='recur', feed=0.03125, count=2),
                            State(tyme=0.0625, context='close', feed=None, count=3),
                            State(tyme=0.0625, context='exit', feed=None, count=4)]
    assert doer0.done == doer1.done == False
    assert doer1.states == doer0.states

    """End Test """


def test_nested_doers():
    """
    Test Doist running nested DoDoers and Doers
    """

    tock = 0.03125
    doist = doing.Doist(tock=tock)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == False
    assert doist.limit == None
    assert doist.doers == []

    doer0 = doing.WhoDoer(tock=0.0, tymist=doist)
    doer1 = doing.WhoDoer(tock=tock*2, tymist=doist)
    assert doer0.tock == 0.0
    assert doer1.tock == tock * 2
    aDoers = [doer0, doer1]
    for doer in aDoers:
        assert doer._tymist == doist
        assert doer.states == []
        assert doer.count == None
        assert doer.done == None

    aDoer = doing.DoDoer(tock=0.0, tymist=doist, doers=aDoers)
    assert aDoer.doers == aDoers
    assert aDoer._tymist == doist
    assert aDoer.done == None


    doer2 = doing.WhoDoer(tock=0.0, tymist=doist)
    doer3 = doing.WhoDoer(tock=tock*4, tymist=doist)
    assert doer2.tock == 0.0
    assert doer3.tock == tock * 4
    bDoers = [doer2, doer3]
    for doer in bDoers:
        assert doer._tymist == doist
        assert doer.states == []
        assert doer.count == None
        assert doer.done == None

    bDoer = doing.DoDoer(tock=tock*2, tymist=doist, doers=bDoers)
    assert bDoer.doers == bDoers
    assert bDoer._tymist == doist
    assert bDoer.done == None

    doers = [aDoer, bDoer]
    ticks = 8
    limit = tock * ticks
    doist.do(doers=doers, limit=limit)  # run em all
    assert doist.tyme == limit == 0.25

    assert aDoer.done == True
    assert bDoer.done == False


    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.03125, context='recur', feed=0.03125, count=2),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=3),
                            State(tyme=0.09375, context='recur', feed=0.09375, count=4),
                            State(tyme=0.09375, context='exit', feed=None, count=5)]
    assert doer1.done == True

    assert doer1.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=2),
                            State(tyme=0.125, context='recur', feed=0.125, count=3),
                            State(tyme=0.1875, context='recur', feed=0.1875, count=4),
                            State(tyme=0.1875, context='exit', feed=None, count=5)]
    assert doer1.done == True

    assert doer2.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=2),
                            State(tyme=0.125, context='recur', feed=0.125, count=3),
                            State(tyme=0.1875, context='recur', feed=0.1875, count=4),
                            State(tyme=0.1875, context='exit', feed=None, count=5)]
    assert doer2.done == True

    assert doer3.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.125, context='recur', feed=0.125, count=2),
                            State(tyme=0.25, context='close', feed=None, count=3),
                            State(tyme=0.25, context='exit', feed=None, count=4)]
    assert doer3.done == False
    """End Test """


def test_doist_dos():
    """
    Test doist.do with dos generator functions not generator methods
    """
    tock = 0.03125
    doist = doing.Doist(tock=tock)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == False
    assert doist.limit == None
    assert doist.doers == []


    doer0 = doing.doify(doing.whoDo, name='gf0', tock=tock, states=None)
    assert inspect.isgeneratorfunction(doer0)
    assert doer0.opts["states"] == None
    doer0.opts['states'] = []
    assert doer0.tock == tock
    assert doer0.done == None

    doer1 = doing.doify(doing.whoDo, name='gf1', tock=tock*2)
    assert inspect.isgeneratorfunction(doer1)
    assert not doer1.opts
    doer1.opts['states'] = []
    assert doer1.tock == tock * 2
    assert doer1.done == None

    assert doer0 is not doer1

    doer2 = doing.exDo
    assert inspect.isgeneratorfunction(doer2)
    assert doer2.opts["states"] == None
    doer2.opts["states"] = []
    doer2.tock = tock * 2
    assert doer2.done == None

    doers = [doer0, doer1, doer2]
    for doer in doers:
        assert doer.opts['states'] == []


    ticks = 4
    limit = tock * ticks
    doist.do(doers=doers, limit=limit)
    assert doist.tyme == limit == 0.125
    assert doer0.opts["states"] == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.03125, context='recur', feed=0.03125, count=2),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=3),
                            State(tyme=0.09375, context='recur', feed=0.09375, count=4),
                            State(tyme=0.09375, context='exit', feed=None, count=5)]
    assert doer0.done == True

    assert doer1.opts["states"] == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=2),
                            State(tyme=0.125, context='close', feed=None, count=3),
                            State(tyme=0.125, context='exit', feed=None, count=4)]
    assert doer1.done == False

    assert doer2.opts["states"] == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=2),
                            State(tyme=0.125, context='close', feed=None, count=3),
                            State(tyme=0.125, context='exit', feed=None, count=4)]
    assert doer2.done == False

    #  repeat but real time
    doist = doing.Doist(tock=tock, real=True, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == limit == 0.125
    assert doist.doers == []

    for doer in doers:
        doer.opts['states'] = []
        assert doer.opts['states'] == []
        doer.done = None

    doist.do(doers=doers)
    assert doist.tyme == limit == 0.125
    assert doer0.opts["states"] == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.03125, context='recur', feed=0.03125, count=2),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=3),
                            State(tyme=0.09375, context='recur', feed=0.09375, count=4),
                            State(tyme=0.09375, context='exit', feed=None, count=5)]

    assert doer1.opts["states"] == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=2),
                            State(tyme=0.125, context='close', feed=None, count=3),
                            State(tyme=0.125, context='exit', feed=None, count=4)]

    assert doer2.opts["states"] == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=2),
                            State(tyme=0.125, context='close', feed=None, count=3),
                            State(tyme=0.125, context='exit', feed=None, count=4)]


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
        doer.opts['states'] = []
        assert doer.opts['states'] == []
        doer.tock = 0.0  # run asap

    doist.do(doers=doers)
    assert doist.tyme == limit
    assert doer0.opts["states"] == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.03125, context='recur', feed=0.03125, count=2),
                            State(tyme=0.0625, context='close', feed=None, count=3),
                            State(tyme=0.0625, context='exit', feed=None, count=4)]

    assert doer0.opts["states"] == doer1.opts["states"] == doer2.opts["states"]

    # low limit force close real time
    doist = doing.Doist(tock=tock, real=True, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == limit == 0.0625
    assert doist.doers == []

    for doer in doers:
        doer.opts['states'] = []
        assert doer.opts['states'] == []
        doer.tock = 0.0  # run asap

    doist.do(doers=doers)
    assert doist.tyme == limit
    assert doer0.opts["states"] == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.03125, context='recur', feed=0.03125, count=2),
                            State(tyme=0.0625, context='close', feed=None, count=3),
                            State(tyme=0.0625, context='exit', feed=None, count=4)]

    assert doer0.opts["states"] == doer1.opts["states"] == doer2.opts["states"]

    """End Test """



if __name__ == "__main__":
    test_doist_dos()
