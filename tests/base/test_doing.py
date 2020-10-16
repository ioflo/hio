# -*- encoding: utf-8 -*-
"""
tests.core.test_doing module

"""
import pytest

import inspect

from hio.base import ticking
from hio.base import doing
from hio.base.doing import State
from hio.core.tcp import serving, clienting

def test_doer():
    """
    Test Doer base class
    """
    tock = 1.0
    doer = doing.Doer()
    assert isinstance(doer.ticker, ticking.Ticker)
    assert doer.tock == 0.0

    ticker = ticking.Ticker()
    doer = doing.Doer(ticker=ticker, tock=tock)
    assert doer.ticker == ticker
    assert doer.tock == tock == 1.0
    doer.tock = 0.0
    assert doer.tock ==  0.0

    do = doer.do()
    assert inspect.isgenerator(do)
    result = do.send(None)
    assert result == doer.tock == 0.0
    result = do.send("Hello")
    assert result == doer.tock == 0.0
    result = do.send("Hi")
    assert result == doer.tock == 0.0
    result = do.close()
    assert result == None

    with pytest.raises(StopIteration):
        result = do.send("what?")

    do = doer()
    assert inspect.isgenerator(do)
    result = do.send(None)
    assert result == doer.tock == 0.0
    result = do.send("Hello")
    assert result == doer.tock == 0.0
    result = do.send("Hi")
    assert result == doer.tock == 0.0
    result = do.close()
    assert result == None

    with pytest.raises(StopIteration):
        result = do.send("what?")

    do = doer()
    assert inspect.isgenerator(do)
    result = next(do)
    assert result == doer.tock == 0.0
    result = next(do)
    assert result == doer.tock == 0.0
    result = next(do)
    assert result == doer.tock == 0.0
    result = do.close()
    assert result == None

    with pytest.raises(StopIteration):
        result = do.send("what?")

    do = doer(tock=tock)
    assert inspect.isgenerator(do)
    result = next(do)
    assert result == doer.tock == tock == 1.0
    result = next(do)
    assert result == doer.tock == 1.0
    result = next(do)
    assert result == doer.tock == 1.0
    result = do.close()
    assert result == None

    with pytest.raises(StopIteration):
        result = do.send("what?")

    doer.tock = 0.0

    do = doer.do(tock=tock)
    assert inspect.isgenerator(do)
    result = next(do)
    assert result == doer.tock == tock == 1.0
    result = next(do)
    assert result == doer.tock == 1.0
    result = next(do)
    assert result == doer.tock == 1.0
    result = do.close()
    assert result == None

    with pytest.raises(StopIteration):
        result = do.send("what?")



    """End Test """

def test_whodoer_break():
    """
    Test WhoDoer testing class with break to normal exit
    """
    ticker = ticking.Ticker(tock=0.125)
    doer = doing.WhoDoer(ticker=ticker, tock=0.25)
    assert doer.ticker == ticker
    assert doer.ticker.tock == 0.125
    assert doer.tock == 0.25
    assert doer.states ==  []
    assert ticker.tyme == 0.0

    do = doer.do()
    assert inspect.isgenerator(do)
    result = do.send(None)
    assert result == 0
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0)]
    result = do.send("Hello")
    assert result  == 1
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1)]


    ticker.tick()
    result = do.send("Hi")
    assert result ==  2
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2)]
    ticker.tick()
    result = do.send("Blue")
    assert result == 3
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2),
                           State(tyme=0.25, context='recur', feed='Blue', count=3)]

    ticker.tick()
    try:
        result = do.send("Red")
    except StopIteration as ex:
        assert ex.value == True  #  clean return
        assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                               State(tyme=0.0, context='recur', feed='Hello', count=1),
                               State(tyme=0.125, context='recur', feed='Hi', count=2),
                               State(tyme=0.25, context='recur', feed='Blue', count=3),
                               State(tyme=0.375, context='recur', feed='Red', count=4),
                               State(tyme=0.375, context='exit', feed='Red', count=5)]
    """End Test """


def test_whodoer_close():
    """
    Test WhoDoer testing class with close to force exit
    """
    ticker = ticking.Ticker(tock=0.125)
    doer = doing.WhoDoer(ticker=ticker, tock=0.25)
    assert doer.ticker == ticker
    assert doer.ticker.tock == 0.125
    assert doer.tock == 0.25
    assert doer.states ==  []
    assert ticker.tyme == 0.0

    do = doer.do()
    assert inspect.isgenerator(do)
    result = do.send(None)
    assert result == 0
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0)]
    result = do.send("Hello")
    assert result  == 1
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1)]


    ticker.tick()
    result = do.send("Hi")
    assert result ==  2
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2)]
    ticker.tick()
    result = do.close()
    assert result == None
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2),
                           State(tyme=0.25, context='close', feed='Hi', count=3),
                           State(tyme=0.25, context='exit', feed='Hi', count=4)]

    ticker.tick()
    try:
        result = do.send("what?")
    except StopIteration as ex:
        assert ex.value == None  # not clean return
        assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                               State(tyme=0.0, context='recur', feed='Hello', count=1),
                               State(tyme=0.125, context='recur', feed='Hi', count=2),
                               State(tyme=0.25, context='close', feed='Hi', count=3),
                               State(tyme=0.25, context='exit', feed='Hi', count=4)]

    """End Test """


def test_whodoer_throw():
    """
    Test WhoDoer testing class with throw to force exit
    """
    ticker = ticking.Ticker(tock=0.125)
    doer = doing.WhoDoer(ticker=ticker, tock=0.25)
    assert doer.ticker == ticker
    assert doer.ticker.tock == 0.125
    assert doer.tock == 0.25
    assert doer.states ==  []
    assert ticker.tyme == 0.0

    do = doer.do()
    assert inspect.isgenerator(do)
    result = do.send(None)
    assert result == 0
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0)]
    result = do.send("Hello")
    assert result  == 1
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1)]


    ticker.tick()
    result = do.send("Hi")
    assert result ==  2
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2)]
    ticker.tick()
    try:
        result = do.throw(ValueError, "Bad")
    except ValueError as ex:
        assert ex.args[0] == "Bad"
        assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                                State(tyme=0.0, context='recur', feed='Hello', count=1),
                                State(tyme=0.125, context='recur', feed='Hi', count=2),
                                State(tyme=0.25, context='abort', feed='Hi', count=3),
                                State(tyme=0.25, context='exit', feed='Hi', count=4)]

    ticker.tick()
    try:
        result = do.send("what?")
    except StopIteration as ex:
        assert ex.value == None  # not clean return
        assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                                State(tyme=0.0, context='recur', feed='Hello', count=1),
                                State(tyme=0.125, context='recur', feed='Hi', count=2),
                                State(tyme=0.25, context='abort', feed='Hi', count=3),
                                State(tyme=0.25, context='exit', feed='Hi', count=4)]


if __name__ == "__main__":
    test_whodoer_throw()
