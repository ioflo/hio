# -*- encoding: utf-8 -*-
"""
tests.core.test_cycling module

"""
import pytest

from hio.base.cycling import Cycler, Tymer

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

    tymer.cycler.tock()
    assert tymer.cycler.tyme == 0.25
    assert tymer.elapsed ==  0.25
    assert tymer.remaining == 0.75
    assert tymer.expired == False

    tymer.cycler.tock()
    tymer.cycler.tock()
    assert tymer.cycler.tyme == 0.75
    assert tymer.elapsed ==  0.75
    assert tymer.remaining == 0.25
    assert tymer.expired == False

    tymer.cycler.tock()
    assert tymer.cycler.tyme == 1.0
    assert tymer.elapsed ==  1.0
    assert tymer.remaining == 0.0
    assert tymer.expired == True

    tymer.cycler.tock()
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

    tymer.cycler.tock()
    assert tymer.elapsed ==  0.25
    assert tymer.remaining == 0.0
    assert tymer.expired == True

    tymer = Tymer(duration=1.0, start=0.25)
    assert tymer.cycler.tyme == 0.0
    assert tymer.duration == 1.0
    assert tymer.elapsed ==  -0.25
    assert tymer.remaining == 1.25
    assert tymer.expired == False
    tymer.cycler.tock()
    assert tymer.cycler.tyme == 1.0
    assert tymer.elapsed ==  0.75
    assert tymer.remaining == 0.25
    assert tymer.expired == False
    tymer.cycler.tock()
    assert tymer.cycler.tyme == 2.0
    assert tymer.elapsed == 1.75
    assert tymer.remaining == -0.75
    assert tymer.expired == True


    """End Test """

if __name__ == "__main__":
    test_tymer()
