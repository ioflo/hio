# -*- encoding: utf-8 -*-
"""
tests.help.test_timing module

"""
import time
import pytest

from hio.help.timing import TimerError, RetroTimerError
from hio.help.timing import Timer, MonoTimer


def test_timer():
    """
    Test Timer class
    """
    timer = Timer()
    assert timer.duration == 0.0
    assert timer.elapsed > 0.0
    assert timer.remaining < 0.0
    assert timer.expired == True

    timer.restart(duration=0.125)
    assert timer.duration == 0.125
    assert timer.elapsed > 0.0
    assert timer.remaining > 0.0
    assert timer.expired == False
    time.sleep(0.125)
    assert timer.expired == True

    timer.start(duration = 0.125)
    assert timer.duration == 0.125
    assert timer.elapsed < 0.125
    assert timer.remaining > 0.0
    assert timer.expired == False
    time.sleep(0.125)
    assert timer.expired == True

    timer = Timer(duration=0.125)
    assert timer.duration == 0.125
    assert timer.elapsed > 0.0
    assert timer.remaining > 0.0
    assert timer.expired == False
    time.sleep(0.125)
    assert timer.expired == True

    timer = Timer(duration=0.125, start=time.time() + 0.05)
    assert timer.duration == 0.125
    assert timer.elapsed < 0.0
    assert timer.remaining > 0.125
    assert timer.expired == False
    time.sleep(0.175)
    assert timer.expired == True

    timer = Timer(duration=0.125, start=time.time() - 0.05)
    assert timer.duration == 0.125
    assert timer.elapsed > 0.0
    assert timer.remaining < 0.075
    assert timer.expired == False
    time.sleep(0.075)
    assert timer.expired == True

    """End Test """

def test_monotimer():
    """
    Test MonoTimer class
    """
    timer = MonoTimer()
    assert timer.duration == 0.0
    assert timer.elapsed > 0.0
    assert timer.remaining < 0.0
    assert timer.expired == True

    timer.restart(duration=0.125)
    assert timer.duration == 0.125
    assert timer.elapsed > 0.0
    assert timer.remaining > 0.0
    assert timer.expired == False
    time.sleep(0.125)
    assert timer.expired == True

    timer.start(duration = 0.125)
    assert timer.duration == 0.125
    assert timer.elapsed < 0.125
    assert timer.remaining > 0.0
    assert timer.expired == False
    time.sleep(0.125)
    assert timer.expired == True

    timer = MonoTimer(duration=0.125)
    assert timer.duration == 0.125
    assert timer.elapsed > 0.0
    assert timer.remaining > 0.0
    assert timer.expired == False
    time.sleep(0.125)
    assert timer.expired == True

    timer = MonoTimer(duration=0.125, start=time.time() + 0.05)  #
    assert timer.duration == 0.125
    assert timer.elapsed <= 0.0
    assert timer.remaining < 0.125
    assert timer.expired == False
    time.sleep(0.175)
    assert timer.expired == True

    timer = MonoTimer(duration=0.125, start=time.time() - 0.05)
    assert timer.duration == 0.125
    assert timer.elapsed > 0.0
    assert timer.remaining < 0.075
    assert timer.expired == False
    time.sleep(0.075)
    assert timer.expired == True

    timer = MonoTimer(duration=0.125, retro=False)
    timer._last = timer._start + 0.05  # simulate retrograded
    with pytest.raises(RetroTimerError):
        assert timer.elapsed > 0.0


    timer = MonoTimer(duration=0.125)
    timer._last = timer._start + 0.05  # simulate retrograded
    assert timer.elapsed > 0.0
    assert timer.remaining > 0.0
    assert timer.expired == False
    time.sleep(0.125)
    assert timer.expired == True

    """End Test """

if __name__ == "__main__":
    test_monotimer()
