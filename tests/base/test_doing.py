# -*- encoding: utf-8 -*-
"""
tests.core.test_doing module

"""
import pytest

from hio.base.basing import Ctl, Stt
from hio.base.doing import Doer
from hio.base import cycling

def test_doer():
    """
    Test Doer class
    """
    doer = Doer()
    assert isinstance(doer.cycler, cycling.Cycler)
    assert doer.cycler.tyme == 0.0
    assert doer.tock == 0.0
    assert doer.desire == Ctl.exit
    assert doer.state == Stt.exited
    assert doer.done == True

    state = doer.do(Ctl.recur)
    assert state == doer.state == Stt.recurring
    assert doer.done == False
    assert doer.desire == Ctl.exit
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.exited
    assert doer.done == True
    assert doer.desire == Ctl.exit
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.exited
    assert doer.done == True
    assert doer.desire == Ctl.exit

    doer.desire = Ctl.recur
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.recurring
    assert doer.done == False
    assert doer.desire == Ctl.recur
    doer.desire = Ctl.enter
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.entered
    assert doer.done == False
    assert doer.desire == Ctl.enter
    doer.desire = Ctl.exit
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.exited
    assert doer.done == True
    assert doer.desire == Ctl.exit

    with pytest.raises(StopIteration):
        state = doer.do(Ctl.abort)

    assert doer.state == Stt.aborted
    assert doer.done == True
    assert doer.desire == Ctl.abort

    """End Test """

class WhoDoer(Doer):

    def __init__(self, **kwa):

        super(WhoDoer, self).__init__(**kwa)
        self.states = list()  # list of triples (states desire,done)

    # override .enter
    def enter(self):
        self.states.append((self.cycler.tyme, "enter", self.state.name, self.desire.name, self.done))

    # override .recur
    def recur(self):
        self.states.append((self.cycler.tyme, "recur", self.state.name, self.desire.name, self.done))

    def exit(self, **kwa):
        super(WhoDoer, self).exit(**kwa)
        self.states.append((self.cycler.tyme, "exit", self.state.name, self.desire.name, self.done))


def test_doer_sub():
    """
    Test Doer sub class
    """

    doer = WhoDoer()
    assert isinstance(doer.cycler, cycling.Cycler)
    assert doer.cycler.tyme == 0.0
    assert doer.tock == 0.0
    assert doer.desire == Ctl.exit
    assert doer.state == Stt.exited
    assert doer.done == True
    assert doer.states == []

    doer.desire = Ctl.recur
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.recurring
    assert doer.done == False
    assert doer.desire == Ctl.recur
    assert doer.states == [(0.0, 'enter', 'exited', 'recur', False),
                           (0.0, 'recur', 'entered', 'recur', False)]

    doer.cycler.turn()
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.recurring
    assert doer.done == False
    assert doer.desire == Ctl.recur
    assert doer.states == [(0.0, 'enter', 'exited', 'recur', False),
                           (0.0, 'recur', 'entered', 'recur', False),
                           (1.0, 'recur', 'recurring', 'recur', False)]

    doer.cycler.turn()
    doer.desire = Ctl.enter
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.entered
    assert doer.done == False
    assert doer.desire == Ctl.enter
    assert doer.states == [(0.0, 'enter', 'exited', 'recur', False),
                           (0.0, 'recur', 'entered', 'recur', False),
                           (1.0, 'recur', 'recurring', 'recur', False),
                           (2.0, 'exit', 'recurring', 'enter', False),
                           (2.0, 'enter', 'exited', 'enter', False)]

    doer.cycler.turn()
    doer.desire = Ctl.recur
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.recurring
    assert doer.done == False
    assert doer.desire == Ctl.recur
    assert doer.states == [(0.0, 'enter', 'exited', 'recur', False),
                           (0.0, 'recur', 'entered', 'recur', False),
                           (1.0, 'recur', 'recurring', 'recur', False),
                           (2.0, 'exit', 'recurring', 'enter', False),
                           (2.0, 'enter', 'exited', 'enter', False),
                           (3.0, 'recur', 'entered', 'recur', False)]

    doer.cycler.turn()
    doer.desire = Ctl.exit
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.exited
    assert doer.done == True
    assert doer.desire == Ctl.exit
    assert doer.states == [(0.0, 'enter', 'exited', 'recur', False),
                           (0.0, 'recur', 'entered', 'recur', False),
                           (1.0, 'recur', 'recurring', 'recur', False),
                           (2.0, 'exit', 'recurring', 'enter', False),
                           (2.0, 'enter', 'exited', 'enter', False),
                           (3.0, 'recur', 'entered', 'recur', False),
                           (4.0, 'exit', 'recurring', 'exit', True)]

    doer.cycler.turn()
    with pytest.raises(StopIteration):
        state = doer.do(Ctl.abort)

    assert doer.state == Stt.aborted
    assert doer.done == True
    assert doer.desire == Ctl.abort
    assert doer.states == [(0.0, 'enter', 'exited', 'recur', False),
                           (0.0, 'recur', 'entered', 'recur', False),
                           (1.0, 'recur', 'recurring', 'recur', False),
                           (2.0, 'exit', 'recurring', 'enter', False),
                           (2.0, 'enter', 'exited', 'enter', False),
                           (3.0, 'recur', 'entered', 'recur', False),
                           (4.0, 'exit', 'recurring', 'exit', True)]

    """End Test """


if __name__ == "__main__":
    test_doer_sub()
