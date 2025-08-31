# -*- encoding: utf-8 -*-
"""
tests.help.test_timing module

"""
import time
import datetime

import pytest

from hio.help.timing import TimerError, RetroTimerError
from hio.help.timing import Timer, MonoTimer
from hio.help.timing import nowIso8601, fromIso8601, toIso8601



def test_timer():
    """
    Test Timer class
    """
    timer = Timer()
    time.sleep(0.0001)
    assert timer.duration == 0.0
    assert timer.elapsed > 0.0
    assert timer.remaining < 0.0
    assert timer.expired == True

    timer.restart(duration=0.125)
    time.sleep(0.001)
    assert timer.duration == 0.125
    assert timer.elapsed > 0.0
    assert timer.remaining > 0.0
    assert timer.expired == False
    time.sleep(0.125)
    assert timer.expired == True

    timer.start(duration = 0.125)
    time.sleep(0.001)
    assert timer.duration == 0.125
    assert timer.elapsed < 0.125
    assert timer.remaining > 0.0
    assert timer.expired == False
    time.sleep(0.125)
    assert timer.expired == True

    timer = Timer(duration=0.125)
    time.sleep(0.001)
    assert timer.duration == 0.125
    assert timer.elapsed > 0.0
    assert timer.remaining > 0.0
    assert timer.expired == False
    time.sleep(0.125)
    assert timer.expired == True

    timer = Timer(duration=0.125, start=time.time() + 0.05)
    time.sleep(0.001)
    assert timer.duration == 0.125
    assert timer.elapsed < 0.0
    assert timer.remaining > 0.125
    assert timer.expired == False
    time.sleep(0.175)
    assert timer.expired == True

    timer = Timer(duration=0.125, start=time.time() - 0.05)
    time.sleep(0.001)
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
    time.sleep(0.001)
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
    time.sleep(0.001)
    assert timer.elapsed > 0.0
    assert timer.remaining > 0.0
    assert timer.expired == False
    time.sleep(0.125)
    assert timer.expired == True

    timer = MonoTimer(duration=0.125, start=time.time() + 0.05)  #
    assert timer.duration == 0.125
    assert timer.elapsed <= 0.0
    time.sleep(0.001)
    assert timer.remaining < 0.125
    assert timer.expired == False
    time.sleep(0.175)
    assert timer.expired == True

    timer = MonoTimer(duration=0.125, start=time.time() - 0.05)
    assert timer.duration == 0.125
    time.sleep(0.001)
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


def test_iso8601():  # mocked in pytest
    """
    Test datetime ISO 8601 helpers
    """
    # dts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    dts = '2020-08-22T20:34:41.687702+00:00'
    dt = fromIso8601(dts)
    assert dt.year == 2020
    assert dt.month == 8
    assert dt.day == 22

    dtb = b'2020-08-22T20:34:41.687702+00:00'
    dt = fromIso8601(dts)
    assert dt.year == 2020
    assert dt.month == 8
    assert dt.day == 22


    dts1 = nowIso8601()
    dt1 = fromIso8601(dts1)

    # Add a small delay to ensure timestamps are different
    time.sleep(0.001)

    dts2 = nowIso8601()
    dt2 = fromIso8601(dts2)

    assert dt2 > dt1

    assert dts1 == toIso8601(dt1)
    assert dts2 == toIso8601(dt2)

    time.sleep(0.001)

    dts3 = toIso8601()
    dt3 = fromIso8601(dts3)

    assert dt3 > dt2

    td = dt3 - dt2  # timedelta
    assert td.microseconds > 0.0

    dt4 = dt + datetime.timedelta(seconds=25.0)
    dts4 = toIso8601(dt4)
    assert dts4 == '2020-08-22T20:35:06.687702+00:00'
    dt4 = fromIso8601(dts4)
    assert (dt4 - dt).seconds == 25.0

    # test for microseconds zero
    dts = "2021-01-01T00:00:00.000000+00:00"
    dt = fromIso8601(dts)
    dts1 = toIso8601(dt)
    assert dts1 == dts

    """ End Test """

if __name__ == "__main__":
    test_timer()
    test_monotimer()
    test_iso8601()
