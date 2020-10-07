# -*- encoding: utf-8 -*-
"""
tests.help.test_timing module

"""
import pytest

from hio.help.timing import TimerError, RetroTimerError
from hio.help.timing import Timer, MonoTimer


def test_timer():
    """
    Test Timer class
    """
    timer = Timer()
    assert timer.duration == 0.0
    assert timer.elapsed == 0.0
    assert timer.remaining == 0.0
    assert timer.expired == True

    timer.start(duration = 1.0)
    assert timer.duration == 1.0
    assert timer.elapsed ==  0.0
    assert timer.remaining == 1.0
    assert timer.expired == False

    timer.cycler.tock()
    assert timer.cycler.tyme == 0.25
    assert timer.elapsed ==  0.25
    assert timer.remaining == 0.75
    assert timer.expired == False

    timer.cycler.tock()
    timer.cycler.tock()
    assert timer.cycler.tyme == 0.75
    assert timer.elapsed ==  0.75
    assert timer.remaining == 0.25
    assert timer.expired == False

    timer.cycler.tock()
    assert timer.cycler.tyme == 1.0
    assert timer.elapsed ==  1.0
    assert timer.remaining == 0.0
    assert timer.expired == True

    timer.cycler.tock()
    assert timer.cycler.tyme == 1.25
    assert timer.elapsed ==  1.25
    assert timer.remaining == -0.25
    assert timer.expired == True

    timer.restart()
    assert timer.duration == 1.0
    assert timer.elapsed == 0.25
    assert timer.remaining == 0.75
    assert timer.expired == False

    timer.cycler.tyme = 2.0
    assert timer.elapsed ==  1.0
    assert timer.remaining == 0.0
    assert timer.expired == True

    timer.restart(duration=0.25)
    assert timer.duration == 0.25
    assert timer.elapsed ==  0.0
    assert timer.remaining == 0.25
    assert timer.expired == False

    timer.cycler.tock()
    assert timer.elapsed ==  0.25
    assert timer.remaining == 0.0
    assert timer.expired == True

    timer = Tymer(duration=1.0, start=0.25)
    assert timer.cycler.tyme == 0.0
    assert timer.duration == 1.0
    assert timer.elapsed ==  -0.25
    assert timer.remaining == 1.25
    assert timer.expired == False
    timer.cycler.tock()
    assert timer.cycler.tyme == 1.0
    assert timer.elapsed ==  0.75
    assert timer.remaining == 0.25
    assert timer.expired == False
    timer.cycler.tock()
    assert timer.cycler.tyme == 2.0
    assert timer.elapsed == 1.75
    assert timer.remaining == -0.75
    assert timer.expired == True
    """End Test """

if __name__ == "__main__":
    test_timer()
