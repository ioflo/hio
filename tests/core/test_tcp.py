# -*- encoding: utf-8 -*-
"""
tests.core.test_tcp module

"""
import pytest

from collections import deque

from hio.base import cycling
from hio.core.tcp.clienting import openClient, Client

def test_tcp_client_server():
    """
    Test the tcp connection between client and server
    """
    client = Client()
    assert client.uid == "client"
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
    with openClient(cycler=cycler) as client:
        assert client.uid == "test"
        assert client.cycler == cycler
        assert client.ha == ('127.0.0.1', 56000)
        assert client.opened == True
        assert client.accepted == False
        assert client.cutoff == False
        assert client.reconnectable == False


    assert client.opened == False
    assert client.accepted == False
    assert client.cutoff == False

    """Done Test"""




if __name__ == "__main__":
    test_tcp_client_server()
