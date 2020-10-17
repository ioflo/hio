# -*- encoding: utf-8 -*-
"""
tests.core.test_doing module

"""
import pytest

import inspect

from hio.base import ticking
from hio.base import doing
from hio.base import plying
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

def test_dog_function():
    """
    Test dog example generator function non-class based
    """
    tock = 1.0
    ticker = ticking.Ticker()
    do = doing.dog(ticker=ticker)
    assert inspect.isgenerator(do)
    result = do.send(None)
    assert result == 0.0
    result = do.send("Hello")
    assert result == 0.0
    result = do.send("Hi")
    assert result == 0.0
    result = do.close()
    assert result == None
    with pytest.raises(StopIteration):
        result = do.send("what?")

    do = doing.dog(ticker=ticker, tock=tock)
    assert inspect.isgenerator(do)
    result = do.send(None)
    assert result == tock == 1.0
    result = do.send("Hello")
    assert result == tock == 1.0
    result = do.send("Hi")
    assert result == tock == 1.0
    result = do.close()
    assert result == None
    with pytest.raises(StopIteration):
        result = do.send("what?")

    do = doing.dog(ticker=ticker, tock=tock)
    assert inspect.isgenerator(do)
    result = next(do)
    assert result == tock == 1.0
    result = next(do)
    assert result == tock == 1.0
    result = next(do)
    assert result == tock == 1.0
    result = do.close()
    assert result == None
    with pytest.raises(StopIteration):
        result = do.send("what?")

    do = doing.dog(ticker=ticker, tock=tock)
    assert inspect.isgenerator(do)
    result = next(do)
    assert result == tock == 1.0
    result = next(do)
    assert result == tock == 1.0
    result = next(do)
    assert result == tock == 1.0
    result = do.close()
    assert result == None
    with pytest.raises(StopIteration):
        result = do.send("what?")

    do = doing.dog(ticker=ticker, tock=tock)
    assert inspect.isgenerator(do)
    result = next(do)
    assert result == tock == 1.0
    result = next(do)
    assert result == tock == 1.0
    result = next(do)
    assert result == tock == 1.0
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
    doer = doing.TestDoer(ticker=ticker, tock=0.25)
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
    doer = doing.TestDoer(ticker=ticker, tock=0.25)
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
    doer = doing.TestDoer(ticker=ticker, tock=0.25)
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


def test_whodog_break():
    """
    Test whodog testing function example with break to normal exit
    """
    ticker = ticking.Ticker(tock=0.125)
    assert ticker.tyme == 0.0
    states = []

    do = doing.testdog(states=states, ticker=ticker, tock=0.25)
    assert inspect.isgenerator(do)
    result = do.send(None)
    assert result == 0
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0)]
    result = do.send("Hello")
    assert result == 1
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1)]
    ticker.tick()
    result = do.send("Hi")
    assert result ==  2
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2)]
    ticker.tick()
    result = do.send("Blue")
    assert result == 3
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2),
                           State(tyme=0.25, context='recur', feed='Blue', count=3)]

    ticker.tick()
    try:
        result = do.send("Red")
    except StopIteration as ex:
        assert ex.value == True  #  clean return
        assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                               State(tyme=0.0, context='recur', feed='Hello', count=1),
                               State(tyme=0.125, context='recur', feed='Hi', count=2),
                               State(tyme=0.25, context='recur', feed='Blue', count=3),
                               State(tyme=0.375, context='recur', feed='Red', count=4),
                               State(tyme=0.375, context='exit', feed='Red', count=5)]
    """End Test """


def test_whodog_close():
    """
    Test whodog testing function example with close to force exit
    """
    ticker = ticking.Ticker(tock=0.125)
    assert ticker.tyme == 0.0
    states = []

    do = doing.testdog(states=states, ticker=ticker, tock=0.25)
    assert inspect.isgenerator(do)
    result = do.send(None)
    assert result == 0
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0)]
    result = do.send("Hello")
    assert result  == 1
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1)]


    ticker.tick()
    result = do.send("Hi")
    assert result ==  2
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2)]
    ticker.tick()
    result = do.close()
    assert result == None
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2),
                           State(tyme=0.25, context='close', feed='Hi', count=3),
                           State(tyme=0.25, context='exit', feed='Hi', count=4)]

    ticker.tick()
    try:
        result = do.send("what?")
    except StopIteration as ex:
        assert ex.value == None  # not clean return
        assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                               State(tyme=0.0, context='recur', feed='Hello', count=1),
                               State(tyme=0.125, context='recur', feed='Hi', count=2),
                               State(tyme=0.25, context='close', feed='Hi', count=3),
                               State(tyme=0.25, context='exit', feed='Hi', count=4)]

    """End Test """


def test_whodog_throw():
    """
    Test whodog testing function example with throw to force exit
    """
    ticker = ticking.Ticker(tock=0.125)
    assert ticker.tyme == 0.0
    states = []

    do = doing.testdog(states=states, ticker=ticker, tock=0.25)
    assert inspect.isgenerator(do)
    result = do.send(None)
    assert result == 0
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0)]
    result = do.send("Hello")
    assert result  == 1
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1)]


    ticker.tick()
    result = do.send("Hi")
    assert result ==  2
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2)]
    ticker.tick()
    try:
        result = do.throw(ValueError, "Bad")
    except ValueError as ex:
        assert ex.args[0] == "Bad"
        assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                                State(tyme=0.0, context='recur', feed='Hello', count=1),
                                State(tyme=0.125, context='recur', feed='Hi', count=2),
                                State(tyme=0.25, context='abort', feed='Hi', count=3),
                                State(tyme=0.25, context='exit', feed='Hi', count=4)]

    ticker.tick()
    try:
        result = do.send("what?")
    except StopIteration as ex:
        assert ex.value == None  # not clean return
        assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                                State(tyme=0.0, context='recur', feed='Hello', count=1),
                                State(tyme=0.125, context='recur', feed='Hi', count=2),
                                State(tyme=0.25, context='abort', feed='Hi', count=3),
                                State(tyme=0.25, context='exit', feed='Hi', count=4)]



def test_server_client():
    """
    Test ServerDoer ClientDoer classes
    """
    tock = 0.03125
    ticks = 16
    limit = ticks *  tock
    plier = plying.Plier(tock=tock, real=True, limit=limit)
    assert plier.tyme == 0.0  # on next cycle
    assert plier.tock == tock == 0.03125
    assert plier.real == True
    assert plier.limit == limit == 0.5
    assert plier.doers == []

    port = 6120
    server = serving.Server(host="", port=port)
    client = clienting.Client(host="localhost", port=port)

    serdoer = doing.ServerDoer(ticker=plier, server=server)
    assert serdoer.server.ticker == serdoer.ticker == plier
    assert serdoer.server ==  server
    clidoer = doing.ClientDoer(ticker=plier, client=client)
    assert clidoer.client.ticker == clidoer.ticker == plier
    assert clidoer.client == client

    assert serdoer.tock == 0.0  # ASAP
    assert clidoer.tock == 0.0  # ASAP

    doers = [serdoer, clidoer]
    for doer in doers:
        assert doer.ticker == plier

    msgTx = b"Hello me maties!"
    clidoer.client.tx(msgTx)

    plier.run(doers=doers)
    assert plier.tyme == limit
    assert server.opened == False
    assert client.opened == False

    assert not client.txes
    ca, ix = list(server.ixes.items())[0]
    msgRx = bytes(ix.rxbs)
    assert msgRx == msgTx

    """End Test """

def test_echo_server_client():
    """
    Test EchoServerDoer ClientDoer classes
    """
    tock = 0.03125
    ticks = 16
    limit = ticks *  tock
    plier = plying.Plier(tock=tock, real=True, limit=limit)
    assert plier.tyme == 0.0  # on next cycle
    assert plier.tock == tock == 0.03125
    assert plier.real == True
    assert plier.limit == limit == 0.5
    assert plier.doers == []

    port = 6120
    server = serving.Server(host="", port=port)
    client = clienting.Client(host="localhost", port=port)

    serdoer = doing.EchoServerDoer(ticker=plier, server=server)
    assert serdoer.server.ticker == serdoer.ticker == plier
    assert serdoer.server ==  server
    clidoer = doing.ClientDoer(ticker=plier, client=client)
    assert clidoer.client.ticker == clidoer.ticker == plier
    assert clidoer.client == client

    assert serdoer.tock == 0.0  # ASAP
    assert clidoer.tock == 0.0  # ASAP

    doers = [serdoer, clidoer]
    for doer in doers:
        assert doer.ticker == plier

    msgTx = b"Hello me maties!"
    clidoer.client.tx(msgTx)

    plier.run(doers=doers)
    assert plier.tyme == limit
    assert server.opened == False
    assert client.opened == False

    assert not client.txes
    msgEx = bytes(client.rxbs)  # echoed back message
    assert msgEx == msgTx

    ca, ix = list(server.ixes.items())[0]
    assert bytes(ix.rxbs) == b""  # empty server rxbs becaue echoed

    """End Test """




if __name__ == "__main__":
    test_echo_server_client()
