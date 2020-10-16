# -*- encoding: utf-8 -*-
"""
tests.core.test_ticking module

"""
import pytest

from hio.base import ticking


def test_ticker():
    """
    Test Ticker class
    """
    ticker = ticking.Ticker()
    assert ticker.tyme == 0.0
    assert ticker.tock == 1.0

    ticker.tick()
    assert ticker.tyme == 1.0
    ticker.tick(tock=0.75)
    assert  ticker.tyme ==  1.75
    ticker.tock = 0.5
    ticker.tick()
    assert ticker.tyme == 2.25

    ticker = ticking.Ticker(tyme=2.0, tock=0.25)
    assert ticker.tyme == 2.0
    assert ticker.tock == 0.25
    ticker.tick()
    assert ticker.tyme == 2.25
    ticker.tick(tock=0.75)
    assert  ticker.tyme ==  3.0
    ticker.tock = 0.5
    ticker.tick()
    assert ticker.tyme == 3.5
    """End Test """


def test_tymer():
    """
    Test Tymer class
    """
    tymer = ticking.Tymer()
    assert isinstance(tymer.ticker, ticking.Ticker)
    assert tymer.ticker.tyme == 0.0
    assert tymer.ticker.tock == 1.0

    assert tymer.duration == 0.0
    assert tymer.elapsed == 0.0
    assert tymer.remaining == 0.0
    assert tymer.expired == True

    tymer.ticker.tock = 0.25
    tymer.start(duration = 1.0)
    assert tymer.duration == 1.0
    assert tymer.elapsed ==  0.0
    assert tymer.remaining == 1.0
    assert tymer.expired == False

    tymer.ticker.tick()
    assert tymer.ticker.tyme == 0.25
    assert tymer.elapsed ==  0.25
    assert tymer.remaining == 0.75
    assert tymer.expired == False

    tymer.ticker.tick()
    tymer.ticker.tick()
    assert tymer.ticker.tyme == 0.75
    assert tymer.elapsed ==  0.75
    assert tymer.remaining == 0.25
    assert tymer.expired == False

    tymer.ticker.tick()
    assert tymer.ticker.tyme == 1.0
    assert tymer.elapsed ==  1.0
    assert tymer.remaining == 0.0
    assert tymer.expired == True

    tymer.ticker.tick()
    assert tymer.ticker.tyme == 1.25
    assert tymer.elapsed ==  1.25
    assert tymer.remaining == -0.25
    assert tymer.expired == True

    tymer.restart()
    assert tymer.duration == 1.0
    assert tymer.elapsed == 0.25
    assert tymer.remaining == 0.75
    assert tymer.expired == False

    tymer.ticker.tyme = 2.0
    assert tymer.elapsed ==  1.0
    assert tymer.remaining == 0.0
    assert tymer.expired == True

    tymer.restart(duration=0.25)
    assert tymer.duration == 0.25
    assert tymer.elapsed ==  0.0
    assert tymer.remaining == 0.25
    assert tymer.expired == False

    tymer.ticker.tick()
    assert tymer.elapsed ==  0.25
    assert tymer.remaining == 0.0
    assert tymer.expired == True

    tymer = ticking.Tymer(duration=1.0, start=0.25)
    assert tymer.ticker.tyme == 0.0
    assert tymer.duration == 1.0
    assert tymer.elapsed ==  -0.25
    assert tymer.remaining == 1.25
    assert tymer.expired == False
    tymer.ticker.tick()
    assert tymer.ticker.tyme == 1.0
    assert tymer.elapsed ==  0.75
    assert tymer.remaining == 0.25
    assert tymer.expired == False
    tymer.ticker.tick()
    assert tymer.ticker.tyme == 2.0
    assert tymer.elapsed == 1.75
    assert tymer.remaining == -0.75
    assert tymer.expired == True
    """End Test """



if __name__ == "__main__":
    test_tymer()
