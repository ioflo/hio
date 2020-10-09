# -*- encoding: utf-8 -*-
"""
tests.core.test_tcp module

"""
import pytest

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
    assert client.timeout == 1.0
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


    with openServer(cycler=cycler, timeout=1.0) as server, \
         openClient(cycler=cycler, timeout=1.0) as client:

        assert server.opened == True
        assert client.opened == True

        assert server.ha == ('0.0.0.0', 56000)
        assert client.ha == ('127.0.0.1', 56000)


    assert client.opened == False
    assert server.opened == False

    """Done Test"""




if __name__ == "__main__":
    test_tcp_client_server()
