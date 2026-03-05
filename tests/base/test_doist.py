# -*- encoding: utf-8 -*-
"""
tests.base.test_doist module

"""
import platform
import inspect
import asyncio
from datetime import datetime
import traceback

import pytest

from hio.base import doing
from hio.base.doing import Doist, Doer
from hio.base.basing import State
from hio.base.doing import TryDoer, tryDo

def test_doist_basic():
    """
    Test basic doist
    """
    # test defaults
    doist = doing.Doist()
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == 0.03125
    assert doist.name == 'doist'
    assert doist.real == False
    assert doist.limit == None
    assert doist.doers == []
    assert doist.timer.duration == doist.tock

    doist.do()  # defaults make sure no exceptions

    doist = doing.Doist(name="mydoist", tyme=1.0, tock=0.01, real=True, limit=0.02, doers=[])
    assert doist.tyme == 1.0  # on next cycle
    assert doist.tock == 0.01
    assert doist.name == 'mydoist'
    assert doist.real == True
    assert doist.limit == 0.02
    assert doist.doers == []
    assert doist.timer.duration  # real time with retrograde

    doist.do()  # defaults make sure no exceptions

    doist()  # as callable


    """End Test """


def test_doist_once():
    """
    Test doist.once with deeds
    """
    doist = doing.Doist(tock=0.25)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == 0.25
    assert doist.real == False
    assert doist.limit == None
    assert doist.doers == []

    doer0 = doing.ExDoer(tock=0.25, tymth=doist.tymen())
    doer1 = doing.ExDoer(tock=0.5, tymth=doist.tymen())
    doers = [doer0, doer1]

    doist.doers = doers
    doist.enter()
    assert len(doist.deeds) == 2
    assert [val[1] for val in doist.deeds] == [0.0, 0.0]
    for doer in doers:
        assert doer.states == [State(tyme=0.0, context='enter', feed=0.0, count=0)]
        assert doer.done == False

    doist.recur()
    assert doist.tyme == 0.25  # on next cycle
    assert len(doist.deeds) == 2
    assert [val[1] for val in doist.deeds] == [0.25, 0.5]
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1)]

    doist.recur()
    assert doist.tyme == 0.5  # on next cycle
    assert len(doist.deeds) == 2
    assert [val[1] for val in doist.deeds] == [0.5, 0.5]
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.25, context='recur', feed=0.25, count=2)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1)]

    doist.recur()
    assert doist.tyme == 0.75  # on next cycle
    assert len(doist.deeds) == 2
    assert [val[1] for val in doist.deeds] == [0.75, 1.0]
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.25, context='recur', feed=0.25, count=2),
                            State(tyme=0.5, context='recur', feed=0.5, count=3)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.5, context='recur', feed=0.5, count=2)]

    doist.recur()
    assert doist.tyme == 1.0  # on next cycle
    assert len(doist.deeds) == 1
    assert [val[1] for val in doist.deeds] == [1.0]
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

    doist.recur()
    assert doist.tyme == 1.25  # on next cycle
    assert len(doist.deeds) == 1
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

    doist.recur()
    assert doist.tyme == 1.50  # on next cycle
    assert len(doist.deeds) == 1
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

    doist.recur()
    assert doist.tyme == 1.75  # on next cycle
    assert len(doist.deeds) == 0
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


def test_doist_dos():
    """
    Test doist.do with dos generator functions not generator methods
    """

    if platform.system() == 'Windows':
        pytest.skip("Windows not supported")

    tock = 0.03125
    doist = doing.Doist(tock=tock)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == False
    assert doist.limit == None
    assert doist.doers == []


    doer0 = doing.doify(doing.doifyExDo, name='gf0', tock=tock, states=None)
    assert inspect.isgeneratorfunction(doer0)
    assert doer0.opts["states"] == None
    doer0.opts['states'] = []
    assert doer0.tock == tock
    assert doer0.done == None

    doer1 = doing.doify(doing.doifyExDo, name='gf1', tock=tock*2)
    assert inspect.isgeneratorfunction(doer1)
    assert not doer1.opts
    doer1.opts['states'] = []
    assert doer1.tock == tock * 2
    assert doer1.done == None

    assert doer0 is not doer1

    doer2 = doing.doify(doing.doizeExDo, tock=0, states=None)
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
                            State(tyme=0.125, context='cease', feed=None, count=3),
                            State(tyme=0.125, context='exit', feed=None, count=4)]
    assert doer1.done == True

    assert doer2.opts["states"] == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=2),
                            State(tyme=0.125, context='cease', feed=None, count=3),
                            State(tyme=0.125, context='exit', feed=None, count=4)]
    assert doer2.done == True

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
                            State(tyme=0.125, context='cease', feed=None, count=3),
                            State(tyme=0.125, context='exit', feed=None, count=4)]

    assert doer2.opts["states"] == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.0625, context='recur', feed=0.0625, count=2),
                            State(tyme=0.125, context='cease', feed=None, count=3),
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
                            State(tyme=0.0625, context='cease', feed=None, count=3),
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
                            State(tyme=0.0625, context='cease', feed=None, count=3),
                            State(tyme=0.0625, context='exit', feed=None, count=4)]

    assert doer0.opts["states"] == doer1.opts["states"] == doer2.opts["states"]

    """End Test """


def test_doist_doers():
    """
    Test doist.do with .close of deeds
    """
    tock = 0.03125
    doist = doing.Doist(tock=tock)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == False
    assert doist.limit == None
    assert doist.doers == []

    doer0 = doing.ExDoer(tock=tock, tymth=doist.tymen())
    doer1 = doing.ExDoer(tock=tock*2, tymth=doist.tymen())
    assert doer0.tock == tock
    assert doer1.tock == tock * 2
    doers = [doer0, doer1]
    for doer in doers:
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
                            State(tyme=0.125, context='cease', feed=None, count=3),
                            State(tyme=0.125, context='exit', feed=None, count=4)]
    assert doer1.done == False

    # test as callable
    doist = doing.Doist(tock=tock)
    for doer in doers:
        doer.states = []
        assert doer.states == []
    doist(doers=doers, limit=limit)
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
                            State(tyme=0.125, context='cease', feed=None, count=3),
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
                            State(tyme=0.125, context='cease', feed=None, count=3),
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
                            State(tyme=0.125, context='cease', feed=None, count=3),
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
        doer.tock = 0.0  # run asap
        assert doer.tock == 0.0

    doist.do(doers=doers)
    assert doist.tyme == limit
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.03125, context='recur', feed=0.03125, count=2),
                            State(tyme=0.0625, context='cease', feed=None, count=3),
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
        doer.tock = 0.0  # run asap
        assert doer.tock == 0.0

    doist.do(doers=doers)
    assert doist.tyme == limit
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.03125, context='recur', feed=0.03125, count=2),
                            State(tyme=0.0625, context='cease', feed=None, count=3),
                            State(tyme=0.0625, context='exit', feed=None, count=4)]
    assert doer0.done == doer1.done == False
    assert doer1.states == doer0.states

    """End Test """

def test_extend_remove_doers():
    """
    Test Doist but dynamically extend and remove doers
    """
    tock = 1.0
    limit = 5.0
    # create some TryDoers for doers
    doer0 = TryDoer(stop=1)
    doer1 = TryDoer(stop=2)
    doer2 = TryDoer(stop=3)

    doers = [doer0, doer1, doer2]
    doist = doing.Doist(tock=tock, limit=limit, doers=list(doers))  # make copy
    assert doist.tock == tock ==  1.0
    assert doist.limit == limit == 5.0
    assert doist.done is None
    assert doist.doers == doers
    assert not doist.deeds

    doist.do(limit=2)
    assert doist.tyme == 2.0
    assert not doist.done  # still remaining deeds that did not complete
    assert doer0.done
    assert not doer1.done
    assert not doer2.done
    assert not doist.deeds
    assert doist.doers == doers

    # redo
    doist.do(tyme=0, limit=2)
    assert doist.tyme == 2.0
    assert not doist.done  # deeds that did not complete
    assert doer0.done
    assert not doer1.done
    assert not doer2.done
    assert not doist.deeds
    assert doist.doers == doers

    # redo
    doist.do(tyme=0, limit=2)
    assert doist.tyme == 2.0
    assert not doist.done  # remaining deeds that did not complete
    assert doer0.done
    assert not doer1.done
    assert not doer2.done
    assert not doist.deeds
    assert doist.doers == doers

    # Test extend and remove Doers
    # Now manually restart and run manually but do not reach limit so we can
    # and extend remove below
    doist.done = False
    assert not doist.done
    doist.tyme = 0.0
    assert doist.tyme == 0.0
    assert not doist.deeds
    assert doist.doers == doers
    doist.enter()
    assert len(doist.deeds) == 3
    doist.recur()
    doist.recur()
    assert doist.tyme == 2.0
    assert not doist.done
    assert doer0.done
    assert not doer1.done
    assert not doer2.done
    assert len(doist.deeds) == 2  # deeds still there

    # test extend Doers
    doer3 = TryDoer(stop=1)
    doer4 = TryDoer(stop=2)
    moredoers =  [doer3, doer4]
    doist.extend(doers=list(moredoers))  # make copy
    assert doist.doers == doers + moredoers
    assert len(doist.doers) == 5
    assert len(doist.deeds) == 4
    indices = [index for dog, retyme, index in doist.deeds]
    doers = [doer for dog, retyme, doer in doist.deeds]
    assert doers == [doer1, doer2, doer3, doer4]
    doist.recur()
    doist.recur()
    assert doist.tyme == 4.0
    assert not doist.done  # doist not done
    assert doer0.done
    assert doer1.done
    assert doer2.done
    assert doer3.done
    assert not doer4.done
    assert len(doist.deeds) == 1  # deeds still there
    doist.exit()
    assert doist.done == False  # forced close so not done
    assert doer0.done
    assert doer1.done
    assert doer2.done
    assert doer3.done
    assert not doer4.done  # forced close so not done
    assert not doist.deeds
    """ Done Test"""

def test_doist_remove():
    """
    Test Doist.remove of doers
    """
    tock = 1.0
    limit = 5.0
    # start over with full set to test remove
    doer0 = TryDoer(stop=1)
    doer1 = TryDoer(stop=2)
    doer2 = TryDoer(stop=3)
    doer3 = TryDoer(stop=2)
    doer4 = TryDoer(stop=3)
    doers = [doer0, doer1, doer2, doer3, doer4]
    doist = doing.Doist(tock=tock, doers=list(doers), always=True)
    assert doist.tock == tock == 1.0
    assert doist.tyme == 0.0
    assert doist.doers == doers
    for doer in doist.doers:
        assert doer.done == None
    assert doist.done == None
    assert not doist.deeds

    doist.enter()
    assert doist.done == None  # did not call .do so stays None not False
    doist.recur()
    doist.recur()
    assert doist.tyme == 2.0
    assert not doist.done  # doist not done
    assert doer0.done
    assert not doer1.done
    assert not doer2.done
    assert not doer3.done
    assert not doer4.done
    assert len(doist.deeds) == 4  # deeds still there
    doers = [doer for dog, retyme, doer in doist.deeds]
    assert doers == [doer1, doer2, doer3, doer4]  # doer0 is removed
    for dog, retyme, doer in doist.deeds:
        assert not doer.done

    doist.remove(doers=[doer0, doer1, doer3])
    assert doist.doers == [doer2, doer4]
    assert len(doist.deeds) == 2
    doers = [doer for dog, retyme, doer in doist.deeds]
    assert doers == [doer2, doer4]  # others are removed
    for dog, retyme, doer in doist.deeds:
        assert not doer.done
    assert not doer1.done  # forced exit
    assert not doer3.done  # forced exit

    doist.recur()
    doist.recur()
    assert doist.tyme == 4.0
    assert doist.done == None  # never called .do
    assert len(doist.deeds) == 0  # all done
    assert len(doist.doers) == 2  # not removed but completed
    for doer in doist.doers:
        assert doer.done
    assert doer0.done  # already clean done before remove
    assert not doer1.done  # forced exit upon remove before done
    assert doer2.done  # clean done
    assert not doer3.done  # forced exit upon remove before done
    assert doer4.done  # clean done
    doist.recur()
    doist.recur()  # does not complete because always == True
    """Done Test"""


def test_doist_remove_by_own_doer():
    """
    Test .remove method of Doist called by a doer of Doist
    """
    tock = 1.0
    limit = 5.0
    # create doist first so can inject it into removeDo
    doist = doing.Doist(tock=tock, limit=limit)
    # create doized function that removes doers
    @doing.doize(tock=0.0, doist=doist)
    def removeDo(tymth=None, tock=0.0, doist=None, **opts):
        """
         Returns generator function (doer dog) to process
            to remove all doers of doist but itself

        Parameters:
            tymth is injected function wrapper closure returned by .tymen() of
                Tymist instance (e.e. Doist/DoDoer). Calling tymth() returns
                associated Tymist .tyme.
            tock is injected initial tock value from doer.tock
            opts is dict of injected optional additional parameters from doer.opts

        Injected attributes by doize decorator as parameters to this method:
            gf.tock = tock  # default tock attribute for doer
            gf.opts = {}  # default opts for doer

        Usage:
            add to doers list
        """
        rdoers = []
        yield  # enter context also makes generator method
        # recur context
        for doer in doist.doers:
            # doize decorated function satisfies '==' but not 'is'
            if doer != removeDo:  # must be != vs. is not
                rdoers.append(doer)
        doist.remove(rdoers)
        yield  # extra yield for testing so does a couple of passes after removed
        yield  # extra yield for testing so does a couple of passes after removed
        return True  # once removed then return to remove itself as doer

    # create other doers to remove
    doer0 = TryDoer(stop=1)
    doer1 = TryDoer(stop=2)
    doer2 = TryDoer(stop=3)
    doer3 = TryDoer(stop=2)
    doer4 = TryDoer(stop=3)
    doers = [doer0, doer1, doer2, doer3, doer4, removeDo]

    doist.doers = list(doers)  # make copy
    assert doist.tock == tock == 1.0
    assert doist.tyme == 0.0
    assert doist.limit == limit == 5.0
    assert doist.doers == doers
    assert removeDo in doist.doers
    for doer in doist.doers:
        assert doer.done == None
    assert doist.done == None
    assert not doist.deeds

    doist.enter()
    assert not doist.done
    doist.recur()  # should run removeDo and remove all but itself
    assert doist.tyme == 1.0
    assert doist.deeds
    assert not doist.done  # doist not done
    assert len(doist.doers) == 1
    assert removeDo in doist.doers
    # force exited so not done
    assert not doer0.done
    assert not doer1.done
    assert not doer2.done
    assert not doer3.done
    assert not doer4.done
    doist.recur()
    assert doist.tyme == 2.0
    assert doist.deeds
    assert not doist.done  # dodoer not done
    assert doist.deeds
    assert len(doist.doers) == 1
    assert removeDo in doist.doers
    doist.recur()
    assert doist.tyme == 3.0
    assert not doist.deeds
    assert not doist.done
    assert len(doist.doers) == 1
    assert removeDo in doist.doers
    assert removeDo.done

    """Done Test"""

def test_doist_remove_own_doer():
    """
    Test .remove method of Doist called by a doer of Doist that removes all
    doers including itself.
    """
    tock = 1.0
    limit = 5.0
    # create doist first so can inject it into removeDo
    doist = doing.Doist(tock=tock, limit=limit)
    # create doized function that removes doers
    @doing.doize(tock=0.0, doist=doist)
    def removeDo(tymth=None, tock=0.0, doist=None, **opts):
        """
         Returns generator function (doer dog) to process
            to remove all doers of doist but itself

        Parameters:
            tymth is injected function wrapper closure returned by .tymen() of
                Tymist instance (e.e. Doist/DoDoer). Calling tymth() returns
                associated Tymist .tyme.
            tock is injected initial tock value from doer.tock
            opts is dict of injected optional additional parameters from doer.opts

        Injected attributes by doize decorator as parameters to this method:
            gf.tock = tock  # default tock attribute for doer
            gf.opts = {}  # default opts for doer

        Usage:
            add to doers list
        """
        yield  # enter context also makes generator method
        # recur context
        doist.remove(list(doist.doers))  # attept to remove all doers including itself
        yield  # extra yield for testing so does a couple of passes after removed
        yield  # extra yield for testing so does a couple of passes after removed
        return True  # once removed then return to remove itself as doer

    # create other doers to remove
    doer0 = TryDoer(stop=1)
    doer1 = TryDoer(stop=2)
    doer2 = TryDoer(stop=3)
    doer3 = TryDoer(stop=2)
    doer4 = TryDoer(stop=3)
    doers = [doer0, doer1, doer2, doer3, doer4, removeDo]

    doist.doers = list(doers)  # make copy
    assert doist.tock == tock == 1.0
    assert doist.tyme == 0.0
    assert doist.limit == limit == 5.0
    assert doist.doers == doers
    assert removeDo in doist.doers
    for doer in doist.doers:
        assert doer.done == None
    assert doist.done == None
    assert not doist.deeds

    doist.enter()
    assert not doist.done
    doist.recur()  # should run removeDo and remove all but itself
    assert doist.tyme == 1.0
    assert doist.deeds  # doer removed by not deed.
    assert not doist.done  # doist not done
    assert not doist.doers
    assert not removeDo in doist.doers
    # force exited so not done
    assert not doer0.done
    assert not doer1.done
    assert not doer2.done
    assert not doer3.done
    assert not doer4.done
    assert not removeDo.done

    doist.recur()
    assert doist.tyme == 2.0
    assert doist.deeds
    assert not doist.done  # dodoer not done
    assert doist.deeds
    assert not doist.doers
    doist.recur()
    assert doist.tyme == 3.0
    assert not doist.deeds
    assert not doist.done
    assert removeDo.done  # finished on it own

    """Done Test"""


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

    doer0 = doing.ExDoer(tock=0.0, tymth=doist.tymen())
    doer1 = doing.ExDoer(tock=tock*2, tymth=doist.tymen())
    assert doer0.tock == 0.0
    assert doer1.tock == tock * 2
    aDoers = [doer0, doer1]
    for doer in aDoers:
        assert doer.states == []
        assert doer.count == None
        assert doer.done == None

    aDoer = doing.DoDoer(tock=0.0, tymth=doist.tymen(), doers=aDoers)
    assert aDoer.doers == aDoers
    assert aDoer.done == None


    doer2 = doing.ExDoer(tock=0.0, tymth=doist.tymen())
    doer3 = doing.ExDoer(tock=tock*4, tymth=doist.tymen())
    assert doer2.tock == 0.0
    assert doer3.tock == tock * 4
    bDoers = [doer2, doer3]
    for doer in bDoers:
        assert doer.states == []
        assert doer.count == None
        assert doer.done == None

    bDoer = doing.DoDoer(tock=tock*2, tymth=doist.tymen(), doers=bDoers)
    assert bDoer.doers == bDoers
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
                            State(tyme=0.25, context='cease', feed=None, count=3),
                            State(tyme=0.25, context='exit', feed=None, count=4)]
    assert doer3.done == False
    """End Test """

def test_doist_asyncio():
    """Test asyncio aware support in doist via .ado and .__call__"""

    try:
        asyncio.get_running_loop()
    except RuntimeError as ex:
        pass


    async def art():  # simple coro no awaits
        return True

    async def jed():  # awaits to event loop
        await asyncio.sleep(0.05)  # returns future
        return "done jed"

    async def bob():  # awaits to event loop
        await asyncio.sleep(0.1)  # returns future
        await asyncio.sleep(0.1)  # returns future
        return "done bob"

    async def cob():  # awaits bob
        await bob()
        return "done cob"

    def genor(): # regular generator that wraps async coroutine
        count = 0
        got = (yield count)
        count += 1
        assert got == 1
        coro = bob()  # create async corouting object from function
        while True:
            try:
                #result = yield from coro
                # raises TypeError: cannot 'yield from' a coroutine object in a non-coroutine generator
                result = coro.send(None)  # returns future
                assert result  # <Future pending>
            except StopIteration as ex:
                result = ex.value
                assert result == 'done bob'
                break
            got = (yield count) #(yield result)
            count += 1
        return "done genor"

    async def bdo(): # scheduler of genor
        dog = genor()  # create dog
        done = False
        count = 0
        result = dog.send(None)
        assert result == 0

        while not done:
            count += 1
            try:
                result = dog.send(count)
                assert result >= 1
            except StopIteration as ex:
                result = ex.value
                assert result == 'done genor'
                done = True
            await asyncio.sleep(0.1)

        return done

    asyncio.run(bdo())
    assert True


    # Test with doer that is non generator recur
    class ADoer(Doer):
        """ADoer supports executes async def inside
        """

        def __init__(self, stop=5, **kwa):
            """Initialize instance.

            """
            super(ADoer, self).__init__(**kwa)
            self.count = None
            self.stop = stop
            self.results = []
            self._atask = None

        def enter(self, *, temp=None):
            """Enter Context"""

            self.count = 0
            loop = asyncio.get_event_loop()
            self._atask = loop.create_task(jed(), name="jed")
            self.results.append(dict(who="jed",
                                     result=f"started task {self._atask.get_name()}",
                                     tyme=self.tyme,
                                     count=self.count))


        def recur(self, tyme):
            """Recur Context"""
            done = False  # not self.done
            self.count += 1
            self.results.append(dict(who='adoer',
                                     result=None,
                                     tyme=self.tyme,
                                     count=self.count))

            #run coros to completion
            #arto = art()  # create coroutine object from async def function
            #while True:
                #try:
                    #result = arto.send(None)  # iterate acoro using its .send method
                    #self.results.append(dict(who="art", result="future pending", tyme=self.tyme))
                #except StopIteration as ex:
                    #result = ex.value  # get final returned value from acoro
                    #self.results.append(dict(who="art", result=result, tyme=self.tyme))
                    #break

            #dog = genor()  # create dog
            #done = False
            #count = 0
            #result = dog.send(None)
            #assert result == 0

            #while not done:
                #count += 1
                #try:
                    #result = dog.send(count)
                    #assert result >= 1
                #except StopIteration as ex:
                    #result = ex.value
                    #assert result == 'done genor'
                    #done = True
                ##await asyncio.sleep(0.1)

            #assert done

            if self._atask.done():
                result = self._atask.result()
                self.results.append(dict(who="jed result",
                                         result=result,
                                         tyme=self.tyme,
                                         count=self.count))
                done = True



            #jedo = jed()  # create coroutine object from async def function
            #while True:
                #try:
                    #result = jedo.send(None)  # iterate acoro using its .send method
                    #self.results.append(dict(who="jed", result="future pending", tyme=self.tyme))
                #except StopIteration as ex:
                    #result = ex.value  # get final returned value from acoro
                    #self.results.append(dict(who="jed", result=result, tyme=self.tyme))
                    #done = True
                    #break
                #except RuntimeError as ex:
                    ##"await wasn't used with future"
                    #result = ex.args[0]
                    #self.results.append(dict(who="jed", result=result, tyme=self.tyme))
                    #exmsg = traceback.format_exc()
                    #done = True
                    #break

            #acoro = bob()  # create coroutine object from async def function
            #while True:
                #try:
                    #result = acoro.send(None)  # iterate acoro using its .send method
                    #self.results.append(dict(who="bob", result=result, tyme=self.tyme))
                #except StopIteration as ex:
                    #result = ex.value  # get final returned value from acoro
                    #self.results.append(dict(who="bob", result=result, tyme=self.tyme))
                    #break
                #except RuntimeError as ex:
                    ##"await wasn't used with future"
                    #pass  # do not want this

            #cobo = cob()  # create coroutine object from async def function
            #while True:
                #try:
                    #result = cobo.send(None)  # iterate acoro using its .send method
                    #self.results.append(dict(who="cob", result="future pending", tyme=self.tyme))
                #except StopIteration as ex:
                    #result = ex.value  # get final returned value from acoro
                    #self.results.append(dict(who="cob", result=result, tyme=self.tyme))
                    #break
                #except RuntimeError as ex:
                    ##"await wasn't used with future"
                    #result = ex.args[0]
                    #self.results.append(dict(who="jed", result=result, tyme=self.tyme))
                    #exmsg = traceback.format_exc()
                    #break

            if self.count >= self.stop:
                done = True

            return done  # False=incomplete True=complete


    adoer = ADoer(stop=5)
    doers = [adoer]
    doist = Doist(tock=0.05, real=True, doers=doers, temp=True)

    asyncio.run(doist.ado())
    assert True
    assert adoer.results == \
    [
        {'who': 'jed', 'result': 'started task jed', 'tyme': 0.0, 'count': 0},
        {'who': 'adoer', 'result': None, 'tyme': 0.0, 'count': 1},
        {'who': 'adoer', 'result': None, 'tyme': 0.05, 'count': 2},
        {'who': 'adoer', 'result': None, 'tyme': 0.1, 'count': 3},
        {'who': 'jed result', 'result': 'done jed', 'tyme': 0.1, 'count': 3}
    ]


    #async def main():
    #atask = asyncio.create_task(doist.ado())
    #await asyncio.sleep(0.1)

    #asyncio.run(main())
    #assert True

    # Test with Doer that is geneator recur
    class RDoer(Doer):
        """Uses generator for recur method
        """

        def __init__(self, stop=1, **kwa):
            """Initialize instance.

            """
            super(RDoer, self).__init__(**kwa)
            self.states = []
            self.count = None
            self.stop = stop
            self.results = []

        def enter(self, *, temp=None):
            """Enter Context
            """
            self.count = 0

        def recur(self, tock=None):
            """Recur Context
            """

            tock = tock if tock is not None else self.tock
            tyme = None
            while (True):  # recur context
                # yield from advances to first yield as next() same as send(None)
                # first iteration receives initial tyme before first tick() default 0.0
                # so first recur is same tyme as enter
                tyme = yield(tock)  # receives tyme
                self.count += 1

                arto = art()  # create coroutine object from async def function
                while True:  # iterate until complete inline
                    try:
                        result = arto.send(None)  # iterate acoro using its .send method
                        self.results.append(dict(who="art", result="future pending", tyme=self.tyme))
                    except StopIteration as ex:
                        result = ex.value  # get final returned value from acoro
                        self.results.append(dict(who="art", result=result, tyme=self.tyme))
                        break

                jedo = jed()  # create coroutine object from async def function
                while True:  #iterate until complete inline
                    try:
                        result = jedo.send(None)  # iterate acoro using its .send method
                        self.results.append(dict(who="jed", result="future pending", tyme=self.tyme))
                    except StopIteration as ex:
                        result = ex.value  # get final returned value from acoro
                        self.results.append(dict(who="jed", result=result, tyme=self.tyme))
                        break
                    except RuntimeError as ex:
                        #"await wasn't used with future"
                        result = ex.args[0]
                        self.results.append(dict(who="jed", result=result, tyme=self.tyme))
                        exmsg = traceback.format_exc()
                        break

                cobo = cob()  # create coroutine object from async def function
                while True:
                    try:
                        result = cobo.send(None)  # iterate acoro using its .send method
                        self.results.append(dict(who="cob", result="future pending", tyme=self.tyme))
                    except StopIteration as ex:
                        result = ex.value  # get final returned value from acoro
                        self.results.append(dict(who="cob", result=result, tyme=self.tyme))
                        break
                    except RuntimeError as ex:
                        #"await wasn't used with future"
                        result = ex.args[0]
                        self.results.append(dict(who="jed", result=result, tyme=self.tyme))
                        exmsg = traceback.format_exc()
                        break


                if self.count >= self.stop:
                    break

            return True  # done

    rdoer = RDoer(stop=2)
    doers = [rdoer]
    doist = Doist(tock=0.05, real=True, doers=doers, temp=True)

    asyncio.run(doist.ado(), debug=True)
    assert True
    assert rdoer.results == \
    [
        {'who': 'art', 'result': True, 'tyme': 0.0},
        {'who': 'jed', 'result': 'future pending', 'tyme': 0.0},
        {'who': 'jed', 'result': "await wasn't used with future", 'tyme': 0.0},
        {'who': 'cob', 'result': 'future pending', 'tyme': 0.0},
        {'who': 'jed', 'result': "await wasn't used with future", 'tyme': 0.0},
        {'who': 'art', 'result': True, 'tyme': 0.05},
        {'who': 'jed', 'result': 'future pending', 'tyme': 0.05},
        {'who': 'jed', 'result': "await wasn't used with future", 'tyme': 0.05},
        {'who': 'cob', 'result': 'future pending', 'tyme': 0.05},
        {'who': 'jed', 'result': "await wasn't used with future", 'tyme': 0.05}
    ]


if __name__ == "__main__":
    test_doist_basic()
    test_doist_once()
    test_doist_dos()
    test_doist_doers()
    test_extend_remove_doers()
    test_doist_remove()
    test_doist_remove_own_doer()
    test_doist_remove_by_own_doer()
    test_nested_doers()
    test_doist_asyncio()
