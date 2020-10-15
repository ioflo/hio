# -*- encoding: utf-8 -*-
"""
tests.core.test_deeding module

"""
import pytest

from hio.base.basing import Ctl, Stt
from hio.base import cycling, doing
from hio.base import deeding
from hio.core.tcp import serving, clienting

def test_server_client():
    """
    Test ServerDoer ClientDoer classes
    """
    tick = 0.03125
    ticks = 16
    limit = ticks *  tick
    cycler = cycling.Cycler(tick=tick, real=True, limit=limit)
    assert cycler.tyme == 0.0  # on next cycle
    assert cycler.tick == tick == 0.03125
    assert cycler.real == True
    assert cycler.limit == limit == 0.5
    assert cycler.doers == []

    port = 6120
    server = serving.Server(host="", port=port)
    client = clienting.Client(host="localhost", port=port)

    serdoer = deeding.ServerDoer(cycler=cycler, server=server)
    assert serdoer.server.cycler == serdoer.cycler == cycler
    assert serdoer.server ==  server
    clidoer = deeding.ClientDoer(cycler=cycler, client=client)
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
    cycler = cycling.Cycler(tick=tick, real=True, limit=limit)
    assert cycler.tyme == 0.0  # on next cycle
    assert cycler.tick == tick == 0.03125
    assert cycler.real == True
    assert cycler.limit == limit == 0.5
    assert cycler.doers == []

    port = 6120
    server = serving.Server(host="", port=port)
    client = clienting.Client(host="localhost", port=port)

    serdoer = deeding.EchoServerDoer(cycler=cycler, server=server)
    assert serdoer.server.cycler == serdoer.cycler == cycler
    assert serdoer.server ==  server
    clidoer = deeding.ClientDoer(cycler=cycler, client=client)
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
    test_echo_server_client()
