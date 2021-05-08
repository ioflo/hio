# -*- encoding: utf-8 -*-
"""
tests.core.test_cycling module

"""
import pytest
import inspect

from hio.base import doing
from hio.base.basing import State
from hio.base.doing import TryDoer, tryDo

def test_doist():
    """
    Test basic doist
    """
    doist = doing.Doist()
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == 0.03125
    assert doist.real == False
    assert doist.limit == None
    assert doist.doers == []
    assert doist.timer.duration == doist.tock

    doist.do()  # defaults make sure no exceptions

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
    deeds = doist.ready()
    assert len(deeds) == 2
    assert [val[1] for val in deeds] == [0.0, 0.0]
    for doer in doers:
        assert doer.states == [State(tyme=0.0, context='enter', feed=0.0, count=0)]
        assert doer.done == False

    doist.once(deeds=deeds)
    assert doist.tyme == 0.25  # on next cycle
    assert len(deeds) == 2
    assert [val[1] for val in deeds] == [0.25, 0.5]
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1)]

    doist.once(deeds=deeds)
    assert doist.tyme == 0.5  # on next cycle
    assert len(deeds) == 2
    assert [val[1] for val in deeds] == [0.5, 0.5]
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.25, context='recur', feed=0.25, count=2)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1)]

    doist.once(deeds=deeds)
    assert doist.tyme == 0.75  # on next cycle
    assert len(deeds) == 2
    assert [val[1] for val in deeds] == [0.75, 1.0]
    assert doer0.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.25, context='recur', feed=0.25, count=2),
                            State(tyme=0.5, context='recur', feed=0.5, count=3)]
    assert doer1.states == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                            State(tyme=0.0, context='recur', feed=0.0, count=1),
                            State(tyme=0.5, context='recur', feed=0.5, count=2)]

    doist.once(deeds=deeds)
    assert doist.tyme == 1.0  # on next cycle
    assert len(deeds) == 1
    assert [val[1] for val in deeds] == [1.0]
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

    doist.once(deeds=deeds)
    assert doist.tyme == 1.25  # on next cycle
    assert len(deeds) == 1
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

    doist.once(deeds=deeds)
    assert doist.tyme == 1.50  # on next cycle
    assert len(deeds) == 1
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

    doist.once(deeds=deeds)
    assert doist.tyme == 1.75  # on next cycle
    assert len(deeds) == 0
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

def test_extend_remove_doers():
    """
    Test Doist but dynamically extend and remove doers
    """
    # create some TryDoers for doers
    doer0 = TryDoer(stop=1)
    doer1 = TryDoer(stop=2)
    doer2 = TryDoer(stop=3)

    doers = [doer0, doer1, doer2]
    tock = 1.0
    limit = 5.0
    doist = doing.Doist(tock=tock, limit=limit, doers=list(doers))  # make copy
    assert doist.tock == tock ==  1.0
    assert doist.limit == limit == 5.0
    assert doist.done is None
    assert doist.doers == doers
    assert not doist.always
    assert not doist.deeds

    doist.do(limit=2)
    assert doist.tyme == 2.0
    assert not doist.done  # still remaining deeds that did not complete
    assert doer0.done
    assert not doer1.done
    assert not doer2.done
    assert not doist.deeds
    assert doist.doers == doers

    # redo but with doist.always == True
    doist.always = True
    assert doist.always
    doist.do(tyme=0, limit=2)
    assert doist.tyme == 2.0
    assert not doist.done  # deeds that did not complete
    assert doist.always
    assert doer0.done
    assert not doer1.done
    assert not doer2.done
    assert not doist.deeds
    assert doist.doers == doers

    # redo but using parameter always = ==True
    doist.always = False
    assert not doist.always
    doist.do(tyme=0, limit=2, always=True)  #  use parameter for always
    assert doist.tyme == 2.0
    assert not doist.done  # remaining deeds that did not complete
    assert not doist.always
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
    doist.always = True
    assert doist.always
    doist.tyme = 0.0
    assert doist.tyme == 0.0
    assert not doist.deeds
    assert doist.doers == doers
    doist.ready()
    assert len(doist.deeds) == 3
    doist.once()
    doist.once()
    assert doist.tyme == 2.0
    assert not doist.done
    assert doist.always
    assert doer0.done
    assert not doer1.done
    assert not doer2.done
    assert len(doist.deeds) == 2  # deeds still there

    # now extend Doers
    doer3 = TryDoer(stop=1)
    doer4 = TryDoer(stop=2)
    moredoers =  [doer3, doer4]
    doist.extend(doers=list(moredoers))  # make copy
    assert doist.doers == doers + moredoers
    assert len(doist.doers) == 5
    assert len(doist.deeds) == 4
    indices = [index for dog, retyme, index in doist.deeds]
    assert indices == [1, 2, 3, 4]  # doer0 is done
    for deed in doist.deeds:
        assert not doist.doers[deed[2]].done
    for i, doer in enumerate(doist.doers):
        assert doer.done == (i not  in indices)
    doist.once()
    doist.once()
    assert doist.tyme == 4.0
    assert not doist.done  # doist not done
    assert doist.always == True
    assert doer0.done
    assert doer1.done
    assert doer2.done
    assert doer3.done
    assert not doer4.done
    assert len(doist.deeds) == 1  # deeds still there
    indices = [index for dog, retyme, index in doist.deeds]
    assert indices == [4]  # doer4 not done
    for deed in doist.deeds:
        assert not doist.doers[deed[2]].done
    for i, doer in enumerate(doist.doers):
        assert doer.done == (i not  in indices)
    doist.close()
    assert doist.done == False  # forced close so not done
    assert doer0.done
    assert doer1.done
    assert doer2.done
    assert doer3.done
    assert not doer4.done  # forced close so not done
    assert not doist.deeds

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
    assert doist.always == True
    assert doist.done == None
    assert not doist.deeds

    doist.ready()
    assert doist.done == None  # did not call .do so stays None not False
    doist.once()
    doist.once()
    assert doist.tyme == 2.0
    assert not doist.done  # doist not done
    assert doist.always == True
    assert doer0.done
    assert not doer1.done
    assert not doer2.done
    assert not doer3.done
    assert not doer4.done
    assert len(doist.deeds) == 4  # deeds still there
    indices = [index for dog, retyme, index in doist.deeds]
    assert indices == [1, 2, 3, 4]  # only doer0 done
    for deed in doist.deeds:
        assert not doist.doers[deed[2]].done
    for i, doer in enumerate(doist.doers):
        assert doer.done == (i not  in indices)
    doist.remove(doers=[doer0, doer1, doer3])
    assert doist.doers == [doer2, doer4]
    assert len(doist.deeds) == 2
    indices = [index for dog, retyme, index in doist.deeds]
    assert indices == [0, 1]  # indices shifted to match new doers
    for deed in doist.deeds:
        assert not doist.doers[deed[2]].done
    for i, doer in enumerate(doist.doers):
        assert doer.done == (i not  in indices)
    doist.once()
    doist.once()
    assert doist.tyme == 4.0
    assert doist.done == None  # never called .do
    assert len(doist.deeds) == 0  # all done
    indices = [index for dog, retyme, index in doist.deeds]
    assert indices == []  # all done
    for deed in doist.deeds:
        assert not doist.doers[deed[2]].done
    for i, doer in enumerate(doist.doers):
        assert doer.done == (i not in indices)
    doist.once()
    doist.once()  # does not complete because always == True
    """ Done Test"""

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

    doer2 = doing.doizeExDo
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
    test_extend_remove_doers()
