# -*- encoding: utf-8 -*-
"""
tests.core.test_cycling module

"""
import pytest

from hio.base.basing import Ctl, Stt
from hio.base.cycling import Cycler, Tymer
from hio.base import doing

def test_cycler():
    """
    Test Cycler class
    """
    cycler = Cycler()
    assert cycler.tyme == 0.0
    assert cycler.tick == 1.0
    assert cycler.real == False
    assert cycler.limit == None
    assert cycler.doers == list()

    cycler.turn()
    assert cycler.tyme == 1.0
    cycler.turn(tick=0.75)
    assert  cycler.tyme ==  1.75
    cycler.tick = 0.5
    cycler.turn()
    assert cycler.tyme == 2.25

    cycler = Cycler(tyme=2.0, tick=0.25)
    assert cycler.tyme == 2.0
    assert cycler.tick == 0.25
    cycler.turn()
    assert cycler.tyme == 2.25
    cycler.turn(tick=0.75)
    assert  cycler.tyme ==  3.0
    cycler.tick = 0.5
    cycler.turn()
    assert cycler.tyme == 3.5

    cycler = Cycler(tick=0.01, limit=0.05)
    cycler.run()
    assert cycler.tyme == 0.01

    cycler = Cycler(tick=0.01, real=True, limit=0.05)
    cycler.run()
    assert cycler.tyme == 0.01

    """End Test """

def test_tymer():
    """
    Test Tymer class
    """
    tymer = Tymer()
    assert isinstance(tymer.cycler, Cycler)
    assert tymer.cycler.tyme == 0.0
    assert tymer.cycler.tick == 1.0

    assert tymer.duration == 0.0
    assert tymer.elapsed == 0.0
    assert tymer.remaining == 0.0
    assert tymer.expired == True

    tymer.cycler.tick = 0.25
    tymer.start(duration = 1.0)
    assert tymer.duration == 1.0
    assert tymer.elapsed ==  0.0
    assert tymer.remaining == 1.0
    assert tymer.expired == False

    tymer.cycler.turn()
    assert tymer.cycler.tyme == 0.25
    assert tymer.elapsed ==  0.25
    assert tymer.remaining == 0.75
    assert tymer.expired == False

    tymer.cycler.turn()
    tymer.cycler.turn()
    assert tymer.cycler.tyme == 0.75
    assert tymer.elapsed ==  0.75
    assert tymer.remaining == 0.25
    assert tymer.expired == False

    tymer.cycler.turn()
    assert tymer.cycler.tyme == 1.0
    assert tymer.elapsed ==  1.0
    assert tymer.remaining == 0.0
    assert tymer.expired == True

    tymer.cycler.turn()
    assert tymer.cycler.tyme == 1.25
    assert tymer.elapsed ==  1.25
    assert tymer.remaining == -0.25
    assert tymer.expired == True

    tymer.restart()
    assert tymer.duration == 1.0
    assert tymer.elapsed == 0.25
    assert tymer.remaining == 0.75
    assert tymer.expired == False

    tymer.cycler.tyme = 2.0
    assert tymer.elapsed ==  1.0
    assert tymer.remaining == 0.0
    assert tymer.expired == True

    tymer.restart(duration=0.25)
    assert tymer.duration == 0.25
    assert tymer.elapsed ==  0.0
    assert tymer.remaining == 0.25
    assert tymer.expired == False

    tymer.cycler.turn()
    assert tymer.elapsed ==  0.25
    assert tymer.remaining == 0.0
    assert tymer.expired == True

    tymer = Tymer(duration=1.0, start=0.25)
    assert tymer.cycler.tyme == 0.0
    assert tymer.duration == 1.0
    assert tymer.elapsed ==  -0.25
    assert tymer.remaining == 1.25
    assert tymer.expired == False
    tymer.cycler.turn()
    assert tymer.cycler.tyme == 1.0
    assert tymer.elapsed ==  0.75
    assert tymer.remaining == 0.25
    assert tymer.expired == False
    tymer.cycler.turn()
    assert tymer.cycler.tyme == 2.0
    assert tymer.elapsed == 1.75
    assert tymer.remaining == -0.75
    assert tymer.expired == True
    """End Test """

class WhoDoer(doing.Doer):

    def __init__(self, **kwa):

        super(WhoDoer, self).__init__(**kwa)
        self.states = list()  # list of triples (states desire,done)

    # override .enter
    def enter(self):
        self.states.append(("enter", self.state.name, self.desire.name, self.done))

    # override .recur
    def recur(self):
        self.states.append(("recur", self.state.name, self.desire.name, self.done))

    def exit(self, **kwa):
        super(WhoDoer, self).exit(**kwa)
        self.states.append(("exit", self.state.name, self.desire.name, self.done))

def test_cycler_cycle():
    """
    Test Cycler.cycle() with doers in deeds
    """
    doer0 = WhoDoer(tock=0.25)
    doer1 = WhoDoer(tock=0.5)
    doers = [doer0, doer1]

    cycler = Cycler(tick=0.25, doers=doers)
    assert cycler.tyme == 0.0  # on next cycle
    assert cycler.tick == 0.25
    assert cycler.real == False
    assert cycler.limit == None
    assert cycler.doers == doers

    deeds = cycler.ready()
    assert len(deeds) == 2
    assert [val[1] for val in deeds] == [0.0, 0.0]
    assert doer0.states == []
    assert doer1.states == []

    cycler.cycle(deeds)
    assert cycler.tyme == 0.25  # on next cycle
    assert len(deeds) == 2
    assert [val[1] for val in deeds] == [0.25, 0.5]
    assert doer0.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False)]
    assert doer1.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False)]

    cycler.cycle(deeds)
    assert cycler.tyme == 0.5  # on next cycle
    assert len(deeds) == 2
    assert [val[1] for val in deeds] == [0.5, 0.5]
    assert doer0.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False)]
    assert doer1.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False)]

    cycler.cycle(deeds)
    assert cycler.tyme == 0.75  # on next cycle
    assert len(deeds) == 2
    assert [val[1] for val in deeds] == [0.75, 1.0]
    assert doer0.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False)]
    assert doer1.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False)]

    doer0.desire = Ctl.exit
    doer1.desire = Ctl.exit
    cycler.cycle(deeds)
    assert cycler.tyme == 1.0  # on next cycle
    assert len(deeds) == 1
    assert [val[1] for val in deeds] == [1.0]
    assert doer0.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('exit', 'recurring', 'exit', True)]
    assert doer1.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False)]

    cycler.cycle(deeds)
    assert cycler.tyme == 1.25  # on next cycle
    assert len(deeds) == 0
    assert doer0.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('exit', 'recurring', 'exit', True)]
    assert doer1.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('exit', 'recurring', 'exit', True)]
    """End Test """

def test_cycler_cycle_abort():
    """
    Test Cycler.cycle() with doers in deeds with abort
    """
    doer0 = WhoDoer(tock=0.25)
    doer1 = WhoDoer(tock=0.5)
    doers = [doer0, doer1]

    cycler = Cycler(tick=0.25, doers=doers)
    assert cycler.tyme == 0.0  # on next cycle
    assert cycler.tick == 0.25
    assert cycler.real == False
    assert cycler.limit == None
    assert cycler.doers == doers

    deeds = cycler.ready()
    assert len(deeds) == 2
    assert [val[1] for val in deeds] == [0.0, 0.0]
    assert doer0.states == []
    assert doer1.states == []

    cycler.cycle(deeds)
    assert cycler.tyme == 0.25  # on next cycle
    assert len(deeds) == 2
    assert [val[1] for val in deeds] == [0.25, 0.5]
    assert doer0.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False)]
    assert doer1.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False)]

    cycler.cycle(deeds)
    assert cycler.tyme == 0.5  # on next cycle
    assert len(deeds) == 2
    assert [val[1] for val in deeds] == [0.5, 0.5]
    assert doer0.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False)]
    assert doer1.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False)]

    cycler.cycle(deeds)
    assert cycler.tyme == 0.75  # on next cycle
    assert len(deeds) == 2
    assert [val[1] for val in deeds] == [0.75, 1.0]
    assert doer0.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False)]
    assert doer1.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False)]

    doer0.desire = Ctl.abort
    doer1.desire = Ctl.abort
    cycler.cycle(deeds)
    assert cycler.tyme == 1.0  # on next cycle
    assert len(deeds) == 1
    assert [val[1] for val in deeds] == [1.0]
    assert doer0.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('exit', 'recurring', 'abort', False)]
    assert doer1.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False)]

    cycler.cycle(deeds)
    assert cycler.tyme == 1.25  # on next cycle
    assert len(deeds) == 0
    assert doer0.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('exit', 'recurring', 'abort', False)]
    assert doer1.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('exit', 'recurring', 'abort', False)]


    """End Test """


def test_cycler_run():
    """
    Test Cycler.cycle() with doers in deeds with abort
    """
    tick = 0.03125
    doer0 = WhoDoer(tock=tick)
    doer1 = WhoDoer(tock=tick*2)
    doers = [doer0, doer1]
    assert doer0.state == Stt.exited
    assert doer1.state == Stt.exited
    for doer in doers:
        assert doer.states == []

    cycler = Cycler(tick=tick, doers=doers)
    assert cycler.tyme == 0.0  # on next cycle
    assert cycler.tick == tick == 0.03125
    assert cycler.real == False
    assert cycler.limit == None
    assert cycler.doers == doers

    ticks = 8
    limit = tick * ticks
    cycler.run(limit=limit)
    assert cycler.tyme == limit
    assert doer0.state == Stt.aborted
    assert doer1.state == Stt.aborted
    assert len(doer0.states) == ticks +  2
    assert doer0.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('exit', 'recurring', 'recur', False)]
    assert len(doer1.states) == ticks / 2 +  2
    assert doer1.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('exit', 'recurring', 'recur', False)]



    for doer in doers:
        doer.states = []
    for doer in doers:
        assert doer.states == []

    cycler = Cycler(tick=tick, doers=doers, real=True, limit=limit)
    assert cycler.tyme == 0.0  # on next cycle
    assert cycler.tick == tick == 0.03125
    assert cycler.real == True
    assert cycler.limit == limit == 0.25
    assert cycler.doers == doers

    cycler.run()
    assert cycler.tyme == limit
    assert doer0.state == Stt.aborted
    assert doer1.state == Stt.aborted
    assert len(doer0.states) == ticks +  2
    assert doer0.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('exit', 'recurring', 'recur', False)]
    assert len(doer1.states) == ticks / 2 +  2
    assert doer1.states == [('enter', 'exited', 'recur', False),
                            ('recur', 'entered', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('recur', 'recurring', 'recur', False),
                            ('exit', 'recurring', 'recur', False)]


    """End Test """


if __name__ == "__main__":
    test_cycler_run()
