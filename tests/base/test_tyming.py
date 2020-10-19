# -*- encoding: utf-8 -*-
"""
tests.core.test_ticking module

"""
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
    """End Test """


def test_tymee():
    """
    Test Tymee class
    """
    tymee = tyming.Tymee()
    assert isinstance(tymee._tymist, tyming.Tymist)
    assert tymee.tyme == tymee._tymist.tyme

    tymist = tyming.Tymist(tock=0.5)
    tymee = tyming.Tymee(tymist=tymist)
    assert tymee._tymist == tymist
    assert tymee.tyme == tymist.tyme

    tymist.tick()
    assert tymee.tyme == tymist.tyme == 0.5

    tymist.tock = 0.25
    tymist.tick()
    assert tymee.tyme == tymist.tyme == 0.75


    tymist = tyming.Tymist(tyme=5.0, tock=2.0)
    tymee.wind(tymist)
    assert tymee.tyme == tymist.tyme == 5.0
    tymist.tick()
    assert tymee.tyme == 7.0

    """End Test"""


def test_tymer():
    """
    Test Tymer class
    """
    tymer = tyming.Tymer()
    assert isinstance(tymer._tymist, tyming.Tymist)
    assert tymer.tyme == 0.0
    assert tymer._tymist.tock == 0.03125

    assert tymer.duration == 0.0
    assert tymer.elapsed == 0.0
    assert tymer.remaining == 0.0
    assert tymer.expired == True

    tymer._tymist.tock = 0.25
    tymer.start(duration = 1.0)
    assert tymer.duration == 1.0
    assert tymer.elapsed ==  0.0
    assert tymer.remaining == 1.0
    assert tymer.expired == False

    tymer._tymist.tick()
    assert tymer.tyme == 0.25
    assert tymer.elapsed ==  0.25
    assert tymer.remaining == 0.75
    assert tymer.expired == False

    tymer._tymist.tick()
    tymer._tymist.tick()
    assert tymer.tyme == 0.75
    assert tymer.elapsed ==  0.75
    assert tymer.remaining == 0.25
    assert tymer.expired == False

    tymer._tymist.tick()
    assert tymer.tyme == 1.0
    assert tymer.elapsed ==  1.0
    assert tymer.remaining == 0.0
    assert tymer.expired == True

    tymer._tymist.tick()
    assert tymer.tyme == 1.25
    assert tymer.elapsed ==  1.25
    assert tymer.remaining == -0.25
    assert tymer.expired == True

    tymer.restart()
    assert tymer.duration == 1.0
    assert tymer.elapsed == 0.25
    assert tymer.remaining == 0.75
    assert tymer.expired == False

    tymer._tymist.tyme = 2.0
    assert tymer.elapsed ==  1.0
    assert tymer.remaining == 0.0
    assert tymer.expired == True

    tymer.restart(duration=0.25)
    assert tymer.duration == 0.25
    assert tymer.elapsed ==  0.0
    assert tymer.remaining == 0.25
    assert tymer.expired == False

    tymer._tymist.tick()
    assert tymer.elapsed ==  0.25
    assert tymer.remaining == 0.0
    assert tymer.expired == True

    tymer = tyming.Tymer(duration=1.0, start=0.25)
    assert tymer.tyme == 0.0
    assert tymer.duration == 1.0
    assert tymer.elapsed ==  -0.25
    assert tymer.remaining == 1.25
    assert tymer.expired == False
    tymer._tymist.tock = 1.0
    tymer._tymist.tick()
    assert tymer.tyme == 1.0
    assert tymer.elapsed ==  0.75
    assert tymer.remaining == 0.25
    assert tymer.expired == False
    tymer._tymist.tick()
    assert tymer.tyme == 2.0
    assert tymer.elapsed == 1.75
    assert tymer.remaining == -0.75
    assert tymer.expired == True

    tymist = tyming.Tymist(tyme=5.0, tock=0.125)
    tymer.wind(tymist)
    assert tymer.tyme == tymist.tyme == 5.0
    assert tymer.expired == False
    assert tymer._start == tymer.tyme == 5.0
    assert tymer._stop == tymer.tyme + tymer.duration == 6.0
    tymist.tick()
    assert tymer.tyme == tymer._start + tymist.tock == 5.125
    """End Test """



if __name__ == "__main__":
    test_tymer()
