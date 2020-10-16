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
    doer = acting.Actor()
    assert isinstance(doer.player, playing.Player)
    assert doer.player.tyme == 0.0
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
    assert isinstance(doer.player, playing.Player)
    assert doer.player.tyme == 0.0
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

    doer.player.turn()
    state = doer.do(doer.desire)
    assert state == doer.state == Stt.recurring
    assert doer.done == False
    assert doer.desire == Ctl.recur
    assert doer.states == [(0.0, 'enter', 'exited', 'recur', False),
                           (0.0, 'recur', 'entered', 'recur', False),
                           (1.0, 'recur', 'recurring', 'recur', False)]

    doer.player.turn()
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

    doer.player.turn()
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

    doer.player.turn()
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

    doer.player.turn()
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
    player = playing.Player(tick=tick, real=True, limit=limit)
    assert player.tyme == 0.0  # on next cycle
    assert player.tick == tick == 0.03125
    assert player.real == True
    assert player.limit == limit == 0.5
    assert player.doers == []

    port = 6120
    server = serving.Server(host="", port=port)
    client = clienting.Client(host="localhost", port=port)

    serdoer = acting.ServerActor(player=player, server=server)
    assert serdoer.server.cycler == serdoer.player == player
    assert serdoer.server ==  server
    clidoer = acting.ClientActor(player=player, client=client)
    assert clidoer.client.cycler == clidoer.player == player
    assert clidoer.client == client

    assert serdoer.tock == 0.0  # ASAP
    assert clidoer.tock == 0.0  # ASAP

    doers = [serdoer, clidoer]
    for doer in doers:
        assert doer.player == player
        assert doer.state == Stt.exited


    msgTx = b"Hello me maties!"
    clidoer.client.tx(msgTx)

    player.run(doers=doers)
    assert player.tyme == limit
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
    player = playing.Player(tick=tick, real=True, limit=limit)
    assert player.tyme == 0.0  # on next cycle
    assert player.tick == tick == 0.03125
    assert player.real == True
    assert player.limit == limit == 0.5
    assert player.doers == []

    port = 6120
    server = serving.Server(host="", port=port)
    client = clienting.Client(host="localhost", port=port)

    serdoer = acting.EchoServerActor(player=player, server=server)
    assert serdoer.server.cycler == serdoer.player == player
    assert serdoer.server ==  server
    clidoer = acting.ClientActor(player=player, client=client)
    assert clidoer.client.cycler == clidoer.player == player
    assert clidoer.client == client

    assert serdoer.tock == 0.0  # ASAP
    assert clidoer.tock == 0.0  # ASAP

    doers = [serdoer, clidoer]
    for doer in doers:
        assert doer.player == player
        assert doer.state == Stt.exited


    msgTx = b"Hello me maties!"
    clidoer.client.tx(msgTx)

    player.run(doers=doers)
    assert player.tyme == limit
    assert server.opened == False
    assert client.opened == False

    assert not client.txes
    msgEx = bytes(client.rxbs)  # echoed back message
    assert msgEx == msgTx

    ca, ix = list(server.ixes.items())[0]
    assert bytes(ix.rxbs) == b""  # empty server rxbs becaue echoed

    """End Test """




if __name__ == "__main__":
    test_server_client()
