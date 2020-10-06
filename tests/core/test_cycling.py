# -*- encoding: utf-8 -*-
"""
tests.core.test_cycling module

"""
import pytest

from hio.core.cycling import Cycler, Tymer

def test_cycler():
    """
    Test Cycler class
    """
    cycler = Cycler()
    assert cycler.tyme == 0.0
    assert cycler.tick == 1.0
    cycler.tock()
    assert cycler.tyme == 1.0
    cycler.tock(tick=0.75)
    assert  cycler.tyme ==  1.75
    cycler.tick = 0.5
    cycler.tock()
    assert cycler.tyme == 2.25

    cycler = Cycler(tyme=2.0, tick=0.25)
    assert cycler.tyme == 2.0
    assert cycler.tick == 0.25
    cycler.tock()
    assert cycler.tyme == 2.25
    cycler.tock(tick=0.75)
    assert  cycler.tyme ==  3.0
    cycler.tick = 0.5
    cycler.tock()
    assert cycler.tyme == 3.5


    """End Test """



if __name__ == "__main__":
    test_cycler()
