# -*- encoding: utf-8 -*-
"""
tests.core.test_doing module

"""
import pytest

from hio.base.basing import Ctl, Stt
from hio.base import playing
from hio.base import acting
from hio.core.tcp import serving, clienting


def test_doer():
    """
    Test Doer class
    """
    doer = acting.Doer()
    assert isinstance(doer.cycler, playing.Player)
    assert doer.cycler.tyme == 0.0
    assert doer.tock == 0.0
    assert doer.desire == Ctl.exit
    assert doer.state == Stt.exited
    assert doer.done == True

    state = doer.do(Ctl.recur)
    assert state == doer.state == Stt.recurring
    assert doer.done == False
    assert doer.desire == Ctl.exit
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.exited
    assert doer.done == True
    assert doer.desire == Ctl.exit
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.exited
    assert doer.done == True
    assert doer.desire == Ctl.exit

    doer.desire = Ctl.recur
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.recurring
    assert doer.done == False
    assert doer.desire == Ctl.recur
    doer.desire = Ctl.enter
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.entered
    assert doer.done == False
    assert doer.desire == Ctl.enter
    doer.desire = Ctl.exit
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.exited
    assert doer.done == True
    assert doer.desire == Ctl.exit

    with pytest.raises(StopIteration):
        state = doer.do(Ctl.abort)

    assert doer.state == Stt.aborted
    assert doer.done == True
    assert doer.desire == Ctl.abort

    """End Test """



def test_doer_sub():
    """
    Test Doer sub class
    """

    doer = acting.WhoDoer()
    assert isinstance(doer.cycler, playing.Player)
    assert doer.cycler.tyme == 0.0
    assert doer.tock == 0.0
    assert doer.desire == Ctl.exit
    assert doer.state == Stt.exited
    assert doer.done == True
    assert doer.states == []

    doer.desire = Ctl.recur
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.recurring
    assert doer.done == False
    assert doer.desire == Ctl.recur
    assert doer.states == [(0.0, 'enter', 'exited', 'recur', False),
                           (0.0, 'recur', 'entered', 'recur', False)]

    doer.cycler.turn()
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.recurring
    assert doer.done == False
    assert doer.desire == Ctl.recur
    assert doer.states == [(0.0, 'enter', 'exited', 'recur', False),
                           (0.0, 'recur', 'entered', 'recur', False),
                           (1.0, 'recur', 'recurring', 'recur', False)]

    doer.cycler.turn()
    doer.desire = Ctl.enter
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.entered
    assert doer.done == False
    assert doer.desire == Ctl.enter
    assert doer.states == [(0.0, 'enter', 'exited', 'recur', False),
                           (0.0, 'recur', 'entered', 'recur', False),
                           (1.0, 'recur', 'recurring', 'recur', False),
                           (2.0, 'exit', 'recurring', 'enter', False),
                           (2.0, 'enter', 'exited', 'enter', False)]

    doer.cycler.turn()
    doer.desire = Ctl.recur
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.recurring
    assert doer.done == False
    assert doer.desire == Ctl.recur
    assert doer.states == [(0.0, 'enter', 'exited', 'recur', False),
                           (0.0, 'recur', 'entered', 'recur', False),
                           (1.0, 'recur', 'recurring', 'recur', False),
                           (2.0, 'exit', 'recurring', 'enter', False),
                           (2.0, 'enter', 'exited', 'enter', False),
                           (3.0, 'recur', 'entered', 'recur', False)]

    doer.cycler.turn()
    doer.desire = Ctl.exit
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.exited
    assert doer.done == True
    assert doer.desire == Ctl.exit
    assert doer.states == [(0.0, 'enter', 'exited', 'recur', False),
                           (0.0, 'recur', 'entered', 'recur', False),
                           (1.0, 'recur', 'recurring', 'recur', False),
                           (2.0, 'exit', 'recurring', 'enter', False),
                           (2.0, 'enter', 'exited', 'enter', False),
                           (3.0, 'recur', 'entered', 'recur', False),
                           (4.0, 'exit', 'recurring', 'exit', True)]

    doer.cycler.turn()
    with pytest.raises(StopIteration):
        state = doer.do(Ctl.abort)

    assert doer.state == Stt.aborted
    assert doer.done == True
    assert doer.desire == Ctl.abort
    assert doer.states == [(0.0, 'enter', 'exited', 'recur', False),
                           (0.0, 'recur', 'entered', 'recur', False),
                           (1.0, 'recur', 'recurring', 'recur', False),
                           (2.0, 'exit', 'recurring', 'enter', False),
                           (2.0, 'enter', 'exited', 'enter', False),
                           (3.0, 'recur', 'entered', 'recur', False),
                           (4.0, 'exit', 'recurring', 'exit', True)]

    """End Test """


def test_server_client():
    """
    Test ServerDoer ClientDoer classes
    """
    tick = 0.03125
    ticks = 16
    limit = ticks *  tick
    cycler = playing.Player(tick=tick, real=True, limit=limit)
    assert cycler.tyme == 0.0  # on next cycle
    assert cycler.tick == tick == 0.03125
    assert cycler.real == True
    assert cycler.limit == limit == 0.5
    assert cycler.doers == []

    port = 6120
    server = serving.Server(host="", port=port)
    client = clienting.Client(host="localhost", port=port)

    serdoer = acting.ServerDoer(cycler=cycler, server=server)
    assert serdoer.server.cycler == serdoer.cycler == cycler
    assert serdoer.server ==  server
    clidoer = acting.ClientDoer(cycler=cycler, client=client)
    assert clidoer.client.cycler == clidoer.cycler == cycler
    assert clidoer.client == client

    assert serdoer.tock == 0.0  # ASAP
    assert clidoer.tock == 0.0  # ASAP

    doers = [serdoer, clidoer]
    for doer in doers:
        assert doer.cycler == cycler
        assert doer.state == Stt.exited


    msgTx = b"Hello me maties!"
    clidoer.client.tx(msgTx)

    cycler.run(doers=doers)
    assert cycler.tyme == limit
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
    tick = 0.03125
    ticks = 16
    limit = ticks *  tick
    cycler = playing.Player(tick=tick, real=True, limit=limit)
    assert cycler.tyme == 0.0  # on next cycle
    assert cycler.tick == tick == 0.03125
    assert cycler.real == True
    assert cycler.limit == limit == 0.5
    assert cycler.doers == []

    port = 6120
    server = serving.Server(host="", port=port)
    client = clienting.Client(host="localhost", port=port)

    serdoer = acting.EchoServerDoer(cycler=cycler, server=server)
    assert serdoer.server.cycler == serdoer.cycler == cycler
    assert serdoer.server ==  server
    clidoer = acting.ClientDoer(cycler=cycler, client=client)
    assert clidoer.client.cycler == clidoer.cycler == cycler
    assert clidoer.client == client

    assert serdoer.tock == 0.0  # ASAP
    assert clidoer.tock == 0.0  # ASAP

    doers = [serdoer, clidoer]
    for doer in doers:
        assert doer.cycler == cycler
        assert doer.state == Stt.exited


    msgTx = b"Hello me maties!"
    clidoer.client.tx(msgTx)

    cycler.run(doers=doers)
    assert cycler.tyme == limit
    assert server.opened == False
    assert client.opened == False

    assert not client.txes
    msgEx = bytes(client.rxbs)  # echoed back message
    assert msgEx == msgTx

    ca, ix = list(server.ixes.items())[0]
    assert bytes(ix.rxbs) == b""  # empty server rxbs becaue echoed

    """End Test """




if __name__ == "__main__":
    test_doer_sub()
