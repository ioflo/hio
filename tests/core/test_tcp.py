# -*- encoding: utf-8 -*-
"""
tests.core.test_tcp module

"""
import pytest

import time
from collections import deque

from hio.base import cycling
from hio.core.tcp.clienting import openClient, Client
from hio.core.tcp.serving import openServer, Server, Incomer

def test_tcp_client_server():
    """
    Test the tcp connection between client and server
    """
    client = Client()
    assert isinstance(client.cycler, cycling.Cycler)
    assert client.timeout == 0.0
    assert isinstance(client.tymer, cycling.Tymer)
    assert client.tymer.duration == client.timeout
    assert client.tymer.cycler == client.cycler

    assert client.ha == ('127.0.0.1', 56000)
    assert (client.host, client.port) == client.ha
    assert client.hostname == client.host
    assert client.cs == None
    assert client.ca == (None, None)
    assert client.accepted == False
    assert client.cutoff == False
    assert client.reconnectable == False
    assert client.opened == False

    assert client.bs == 8096
    assert isinstance(client.txes, deque)
    assert isinstance(client.rxbs, bytearray)
    assert client.wlog == None

    cycler = cycling.Cycler()
    with openClient(cycler=cycler, timeout=0.5) as client:
        assert client.cycler == cycler
        assert client.timeout == 0.5
        assert client.ha == ('127.0.0.1', 56000)
        assert client.opened == True
        assert client.accepted == False
        assert client.cutoff == False
        assert client.reconnectable == False


    assert client.opened == False
    assert client.accepted == False
    assert client.cutoff == False

    server = Server()
    assert isinstance(server.cycler, cycling.Cycler)
    assert server.timeout == 1.0

    assert server.ha == ('', 56000)
    assert server.eha == ('127.0.0.1', 56000)
    assert server.opened == False

    assert server.bs == 8096
    assert isinstance(server.axes, deque)
    assert isinstance(server.ixes, dict)
    assert server.wlog == None

    with openServer(cycler=cycler, timeout=1.5) as server:
        assert server.ha == ('0.0.0.0', 56000)
        assert server.eha == ('127.0.0.1', 56000)
        assert server.opened == True

    assert server.opened == False

    cycler = cycling.Cycler()
    with openServer(cycler=cycler, timeout=1.0, ha=("", 6101)) as server, \
         openClient(cycler=cycler, timeout=1.0, ha=("127.0.0.1", 6101)) as beta, \
         openClient(cycler=cycler, timeout=1.0, ha=("127.0.0.1", 6101)) as gamma:

        assert server.opened == True
        assert beta.opened == True
        assert gamma.opened == True

        assert server.ha == ('0.0.0.0', 6101)
        assert server.eha == ('127.0.0.1', 6101)
        assert beta.ha == ('127.0.0.1', 6101)

        assert beta.accepted == False
        assert beta.connected == False
        assert beta.cutoff == False

        assert gamma.accepted == False
        assert gamma.connected == False
        assert gamma.cutoff == False

        #  connect beta to server
        while not beta.connected or beta.ca not in server.ixes:
            beta.serviceConnect()
            server.serviceConnects()
            time.sleep(0.05)

        assert beta.accepted == True
        assert beta.connected == True
        assert beta.cutoff == False
        assert beta.ca == beta.cs.getsockname()
        assert beta.ha == beta.cs.getpeername()
        assert server.eha == beta.ha

        ixBeta = server.ixes[beta.ca]
        assert ixBeta.cs.getsockname() == beta.cs.getpeername()
        assert ixBeta.cs.getpeername() == beta.cs.getsockname()
        assert ixBeta.cs.getpeername() == beta.ca
        assert ixBeta.ha == beta.ha

        msgOut = b"Beta sends to Server"
        count = beta.send(msgOut)
        assert count == len(msgOut)
        time.sleep(0.05)
        msgIn = ixBeta.receive()
        assert msgOut == msgIn

        # receive without sending
        msgIn = ixBeta.receive()
        assert msgIn is None

        # send multiple
        msgOut1 = b"First Message"
        count = beta.send(msgOut1)
        assert count == len(msgOut1)
        msgOut2 = b"Second Message"
        count = beta.send(msgOut2)
        assert count == len(msgOut2)
        time.sleep(0.05)
        msgIn  = ixBeta.receive()
        assert msgIn == msgOut1 + msgOut2

        # send from server to beta
        msgOut = b"Server sends to Beta"
        count = ixBeta.send(msgOut)
        assert count == len(msgOut)
        time.sleep(0.05)
        msgIn = beta.receive()
        assert msgOut == msgIn

        # receive without sending
        msgIn = beta.receive()
        assert msgIn is None

        # build message too big to fit in buffer
        size = beta.actualBufSizes()[0]
        msgOut = bytearray()
        count = 0
        while (len(msgOut) <= size * 4):
            msgOut.extend(b" %i " %  (count))
            count += 1
        assert len(msgOut) >= size * 4

        msgIn = bytearray()
        size = 0
        while len(msgIn) < len(msgOut):
            if size < len(msgOut):
                size += beta.send(msgOut[size:])
            time.sleep(0.05)
            msgIn.extend( ixBeta.receive())
        assert size == len(msgOut)
        assert msgOut == msgIn



    assert client.opened == False
    assert server.opened == False

    """Done Test"""




if __name__ == "__main__":
    test_tcp_client_server()
