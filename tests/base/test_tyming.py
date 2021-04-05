# -*- encoding: utf-8 -*-
"""
tests.core.test_ticking module

"""
import inspect
import pytest

from hio.base import tyming


def test_tymist():
    """
    Test Tymist class
    """
    tymist = tyming.Tymist()
    assert tymist.tyme == 0.0
    assert tymist.tock == 0.03125
    tymist.tock = 1.0
    tymist.tick()
    assert tymist.tyme == 1.0
    tymist.tick(tock=0.75)
    assert  tymist.tyme ==  1.75
    tymist.tock = 0.5
    tymist.tick()
    assert tymist.tyme == 2.25

    tymist = tyming.Tymist(tyme=2.0, tock=0.25)
    assert tymist.tyme == 2.0
    assert tymist.tock == 0.25
    tymist.tick()
    assert tymist.tyme == 2.25
    tymist.tick(tock=0.75)
    assert  tymist.tyme ==  3.0
    tymist.tock = 0.5
    tymist.tick()
    assert tymist.tyme == 3.5

    tymth = tymist.tymen()
    assert inspect.isfunction(tymth)
    tymth.__name__ == 'tymth'
    assert tymth() == tymist.tyme
    tymist.tick()
    assert tymth() == tymist.tyme

    g = tymth
    assert inspect.isfunction(tymth)
    g.__name__ == "g"
    assert g() == tymist.tyme
    tymist.tick()
    assert g() == tymist.tyme

    """End Test """


def test_tymee():
    """
    Test Tymee class
    """
    tymee = tyming.Tymee()
    assert tymee.tymth == None
    with pytest.raises(TypeError):
        tymee.tyme  # NoneType object not callable

    tymist = tyming.Tymist(tock=1.0)
    tymee = tyming.Tymee(tymth=tymist.tymen())
    assert tymee.tyme == tymist.tyme == 0.0
    tymist.tick()
    assert tymee.tyme == tymist.tyme == 1.0

    tymist = tyming.Tymist(tock=0.5)
    tymee.tymth = tymist.tymen()
    assert tymee.tyme == tymist.tyme == 0.0
    tymist.tick()
    assert tymee.tyme == tymist.tyme == 0.5

    tymist = tyming.Tymist(tock=0.25)
    tymee.wind(tymth=tymist.tymen())
    assert tymee.tyme == tymist.tyme == 0.0
    tymist.tick()
    assert tymee.tyme == tymist.tyme == 0.25
    tymist.tick()
    assert tymee.tyme == tymist.tyme == 0.5

    tymist.tock = 1.0
    tymist.tick()
    assert tymee.tyme == tymist.tyme == 1.5
    """End Test"""


def test_tymer():
    """
    Test Tymer class
    """
    with pytest.raises(TypeError):
        tymer = tyming.Tymer()  # calls .tyme which calls .tymth which is None

    tymist = tyming.Tymist()
    assert tymist.tock == 0.03125
    tymer = tyming.Tymer(tymth=tymist.tymen())
    assert tymer.tyme == 0.0
    assert tymer.duration == 0.0
    assert tymer.elapsed == 0.0
    assert tymer.remaining == 0.0
    assert tymer.expired == True
    tymist.tock = 0.25
    assert tymist.tock == 0.25

    tymer.start(duration = 1.0)
    assert tymer.duration == 1.0
    assert tymer.elapsed ==  0.0
    assert tymer.remaining == 1.0
    assert tymer.expired == False

    tymist.tick()
    assert tymer.tyme == tymist.tyme == 0.25
    assert tymer.elapsed ==  0.25
    assert tymer.remaining == 0.75
    assert tymer.expired == False

    tymist.tick()
    tymist.tick()
    assert tymer.tyme == 0.75
    assert tymer.elapsed ==  0.75
    assert tymer.remaining == 0.25
    assert tymer.expired == False

    tymist.tick()
    assert tymer.tyme == 1.0
    assert tymer.elapsed ==  1.0
    assert tymer.remaining == 0.0
    assert tymer.expired == True

    tymist.tick()
    assert tymer.tyme == 1.25
    assert tymer.elapsed ==  1.25
    assert tymer.remaining == -0.25
    assert tymer.expired == True

    tymer.restart()
    assert tymer.duration == 1.0
    assert tymer.elapsed == 0.25
    assert tymer.remaining == 0.75
    assert tymer.expired == False

    tymist.tyme = 2.0
    assert tymer.elapsed ==  1.0
    assert tymer.remaining == 0.0
    assert tymer.expired == True

    tymer.restart(duration=0.25)
    assert tymer.duration == 0.25
    assert tymer.elapsed ==  0.0
    assert tymer.remaining == 0.25
    assert tymer.expired == False

    tymist.tick()
    assert tymer.elapsed ==  0.25
    assert tymer.remaining == 0.0
    assert tymer.expired == True

    tymist = tyming.Tymist(tock=1.0)
    tymer = tyming.Tymer(tymth=tymist.tymen(), duration=1.0, start=0.25)
    assert tymer.tyme == 0.0
    assert tymer.duration == 1.0
    assert tymer.elapsed ==  -0.25
    assert tymer.remaining == 1.25
    assert tymer.expired == False

    tymist.tick()
    assert tymer.tyme == 1.0
    assert tymer.elapsed ==  0.75
    assert tymer.remaining == 0.25
    assert tymer.expired == False
    tymist.tick()
    assert tymer.tyme == 2.0
    assert tymer.elapsed == 1.75
    assert tymer.remaining == -0.75
    assert tymer.expired == True

    tymist = tyming.Tymist(tyme=5.0, tock=0.125)
    tymer.wind(tymist.tymen())
    assert tymer.tyme == tymist.tyme == 5.0
    assert tymer.expired == False
    assert tymer._start == tymer.tyme == 5.0
    assert tymer._stop == tymer.tyme + tymer.duration == 6.0
    tymist.tick()
    assert tymer.tyme == tymer._start + tymist.tock == 5.125
    """End Test """



if __name__ == "__main__":
    test_tymer()
