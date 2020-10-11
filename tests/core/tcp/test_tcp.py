# -*- encoding: utf-8 -*-
"""
tests.core.test_tcp module

"""
import pytest

import sys
import time
import socket
from collections import deque

from hio.base import cycling
from hio.core.tcp.clienting import openClient, Client
from hio.core.tcp.serving import openServer, Server, Incomer

def test_tcp_client_server():
    """
    Test the tcp connection between client and server

    client send from and receive to port is ephemeral
    server receive to and send from port is well known

    Server listens on ist well know  receive to and send from port

    So incoming to server.
        Source address is client host and client ephemeral port
        Destination address is server host and server well known port

    Each accept socket on server is a different duple of client source, server dest
        all the dest are the same but each source is differenct so can route
        based on the source.

    Server routes incoming packets to accept socket port. The routing uses
           the clients send from ephemeral port to do the routing to the
           correct accept socket. All the accept sockets have the same local
           port but a different remote IP host .
    The servers accept socket port is the well known port so still receives to
           and sends from its well know port.
    The server sends to and receives from the clients ephemeral port number.


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

        assert server.ha == ('0.0.0.0', 6101)  # listen interface
        assert server.eha == ('127.0.0.1', 6101)  # normalized listen/accept external interface
        assert beta.ha == ('127.0.0.1', 6101)  # server listen/accept maybe sha  (server host address)

        assert beta.accepted == False
        assert beta.connected == False
        assert beta.cutoff == False

        assert gamma.accepted == False
        assert gamma.connected == False
        assert gamma.cutoff == False

        #  connect beta to server
        while not (beta.connected and beta.ca in server.ixes):
            beta.serviceConnect()
            server.serviceConnects()
            time.sleep(0.05)

        assert beta.accepted == True
        assert beta.connected == True
        assert beta.cutoff == False
        assert beta.ca == beta.cs.getsockname()  # local connection address
        assert beta.ha == beta.cs.getpeername()  # remote connection address
        assert server.eha == beta.ha  # server external, beta external for server

        ixBeta = server.ixes[beta.ca]
        assert ixBeta.cs.getsockname() == beta.cs.getpeername()  # ixBeta local beta remote
        assert ixBeta.cs.getpeername() == beta.cs.getsockname()  # ixBeta remote beta local
        assert ixBeta.ca == beta.ca == ixBeta.cs.getpeername()
        assert ixBeta.ha == beta.ha == ixBeta.cs.getsockname()

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
            msgOut.extend(b"%032x_" %  (count))  #  need to fix this
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

        #  gamma to server
        while not (gamma.connected and gamma.ca in server.ixes):
            gamma.serviceConnect()
            server.serviceConnects()
            time.sleep(0.05)

        assert gamma.accepted == True
        assert gamma.connected == True
        assert gamma.cutoff == False
        assert gamma.ca == gamma.cs.getsockname()
        assert gamma.ha == gamma.cs.getpeername()
        assert server.eha, gamma.ha
        ixGamma = server.ixes[gamma.ca]
        assert ixGamma.cs.getsockname() == gamma.cs.getpeername()
        assert ixGamma.cs.getpeername() == gamma.cs.getsockname()
        assert ixGamma.ca == gamma.ca
        assert ixGamma.ha == gamma.ha

        msgOut = b"Gamma sends to Server"
        count = gamma.send(msgOut)
        assert count == len(msgOut)
        time.sleep(0.05)
        msgIn = ixGamma.receive()
        assert msgOut == msgIn

        # receive without sending
        msgIn = ixGamma.receive()
        assert msgIn is None

        # send from server to gamma
        msgOut = b"Server sends to Gamma"
        count = ixGamma.send(msgOut)
        assert count == len(msgOut)
        time.sleep(0.05)
        msgIn = gamma.receive()
        assert msgOut == msgIn

        # recieve without sending
        msgIn = gamma.receive()
        assert msgIn is None

        # close beta and then attempt to send
        beta.close()
        msgOut = b"Beta send on closed socket"
        with pytest.raises(AttributeError):
            count = beta.send(msgOut)

        # attempt to receive on closed socket
        with pytest.raises(AttributeError):
            msgIn = beta.receive()

        # read on server after closed beta
        msgIn = ixBeta.receive()
        assert msgIn == b''

        # send on server after closed beta
        msgOut = b"Servers sends to Beta after close"
        count = ixBeta.send(msgOut)
        assert count == len(msgOut) #apparently works

        # close ixBeta manually
        ixBeta.close()
        del server.ixes[ixBeta.ca]
        time.sleep(0.05)
        #after close no socket .cs so can't receive
        with pytest.raises(AttributeError):
             msgIn = ixBeta.receive()
        assert ixBeta.cutoff == True

        # send on gamma to servver first then shutdown gamma sends
        msgOut = b"Gamma sends to server"
        count = gamma.send(msgOut)
        assert count == len(msgOut)
        gamma.shutdownSend()
        time.sleep(0.05)
        msgIn = ixGamma.receive()
        assert msgOut ==  msgIn   # send before shutdown worked
        msgIn = ixGamma.receive()
        assert msgIn == b''  # gamma shutdown detected, not None
        assert ixGamma.cutoff == True

        # send from server to gamma first  then shutdown server send
        msgOut = b"Server sends to Gamma"
        count = ixGamma.send(msgOut)
        assert count ==  len(msgOut)
        ixGamma.shutdown()  # shutdown server connection to gamma
        time.sleep(0.05)
        msgIn = gamma.receive()
        assert msgOut == msgIn
        msgIn = gamma.receive()
        if 'linux' in sys.platform:
            assert msgIn ==  b''  # server shutdown detected not None
            assert gamma.cutoff == True
        else:
            assert msgIn == None  # server shutdown not detected
            assert gamma.cutoff == False
        time.sleep(0.05)
        msgIn = gamma.receive()
        if 'linux' in sys.platform:
            assert msgIn == b''  # server shutdown detected not None
            self.assertIs(gamma.cutoff, True)
        else:
            assert msgIn == None   # server shutdown not detected
            assert gamma.cutoff == False

        ixGamma.close()  # close server connection to gamma
        del server.ixes[ixGamma.ca]
        time.sleep(0.05)
        msgIn = gamma.receive()
        assert msgIn == b''  # server close is detected
        assert gamma.cutoff == True

        # reopen beta
        assert beta.reopen() == True
        assert beta.accepted == False
        assert beta.connected == False
        assert beta.cutoff == False

        # reconnect beta to server
        while  not (beta.connected and beta.ca in server.ixes):
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
        assert ixBeta.ca == beta.ca
        assert ixBeta.ha == beta.ha

        msgOut = b"Beta sends to server"
        count = beta.send(msgOut)
        assert count == len(msgOut)
        time.sleep(0.05)
        msgIn = ixBeta.receive()
        assert msgOut == msgIn

        # send from server to beta
        msgOut = b"Server sends to Beta"
        count = ixBeta.send(msgOut)
        assert count == len(msgOut)
        time.sleep(0.05)
        msgIn = beta.receive()
        assert msgOut == msgIn

        # send from server to beta then shutdown sever and attempt to send again
        msgOut1 = b"Server sends to Beta"
        count = ixBeta.send(msgOut)
        assert count == len(msgOut1)
        ixBeta.shutdownSend()
        msgOut2 = b"Server send again after server shutdowns socket"
        with pytest.raises(socket.error) as ex:
            count = ixBeta.send(msgOut)
        assert ex.typename == 'BrokenPipeError'
        time.sleep(0.05)
        msgIn = beta.receive()
        assert msgOut1 == msgIn
        msgIn = beta.receive()
        assert msgIn == b''  # beta detects shutdown socket
        assert beta.cutoff == True

        # send from beta to server then shutdown beta
        msgOut = b"Beta sends to server"
        count = beta.send(msgOut)
        assert count == len(msgOut)
        beta.shutdown()
        time.sleep(0.05)
        msgIn = ixBeta.receive()
        assert msgOut == msgIn
        time.sleep(0.05)
        msgIn = ixBeta.receive()
        if 'linux' in sys.platform:
            assert ixBeta.cutoff == True
            assert msgIn == b''  # server does detect shutdown
        else:
            assert ixBeta.cutoff == False
            assert  msgIn == None  # server does not detect shutdown
        beta.close()
        time.sleep(0.05)
        msgIn = ixBeta.receive()
        assert msgIn == b''  # server detects closed socket
        ixBeta.close()
        del server.ixes[ixBeta.ca]

        # reopen gamma
        assert gamma.reopen() == True
        assert gamma.accepted == False
        assert gamma.connected == False
        assert gamma.cutoff == False
        # reconnect gamma to server
        while not (gamma.connected and gamma.ca in server.ixes):
            gamma.serviceConnect()
            server.serviceConnects()
            time.sleep(0.05)

        assert gamma.accepted == True
        assert gamma.connected == True
        assert gamma.cutoff == False
        assert gamma.ca == gamma.cs.getsockname()
        assert gamma.ha == gamma.cs.getpeername()
        assert server.eha == gamma.ha

        ixGamma = server.ixes[gamma.ca]
        assert ixGamma.cs.getsockname() == gamma.cs.getpeername()
        assert ixGamma.cs.getpeername() == gamma.cs.getsockname()
        assert ixGamma.ca == gamma.ca
        assert ixGamma.ha == gamma.ha

        msgOut = b"Gamma sends to server"
        count = gamma.send(msgOut)
        assert count == len(msgOut)
        time.sleep(0.05)
        msgIn = ixGamma.receive()
        assert msgOut == msgIn

        # close both sides and reopen Gamma
        gamma.close()
        time.sleep(0.05)
        msgIn = ixGamma.receive()
        assert ixGamma.cutoff ==True  # closed on other end
        assert msgIn == b''  # server detects close
        ixGamma.close()
        del server.ixes[ixGamma.ca]

        # reopen gamma
        assert gamma.reopen() == True
        assert gamma.accepted == False
        assert gamma.connected == False
        assert gamma.cutoff == False

        # reconnect gamma to server
        while not (gamma.connected and gamma.ca in server.ixes):
            gamma.serviceConnect()
            server.serviceConnects()
            time.sleep(0.05)

        assert gamma.accepted == True
        assert gamma.connected == True
        assert gamma.cutoff == False
        assert gamma.ca == gamma.cs.getsockname()
        assert gamma.ha == gamma.cs.getpeername()
        assert server.eha == gamma.ha

        ixGamma = server.ixes[gamma.ca]
        assert ixGamma.cs.getsockname() == gamma.cs.getpeername()
        assert ixGamma.cs.getpeername() == gamma.cs.getsockname()
        assert ixGamma.ca == gamma.ca
        assert ixGamma.ha == gamma.ha

        # send from server to gamma
        msgOut = b"Server sends to Gamma"
        count = ixGamma.send(msgOut)
        assert count == len(msgOut)
        time.sleep(0.05)
        msgIn = gamma.receive()
        assert msgOut == msgIn

        ixGamma.close()
        del server.ixes[ixGamma.ca]
        time.sleep(0.05)
        msgIn = gamma.receive()
        assert msgIn == b''  # gamma detects close
        assert gamma.cutoff == True


    assert beta.opened == False
    assert gamma.opened == False
    assert server.opened == False

    """Done Test"""

def  test_tls_default_client_server:
    """
    Test open connection with tls default config
    """
    #serverKeypath = '/etc/pki/tls/certs/server_key.pem'  # local server private key
    #serverCertpath = '/etc/pki/tls/certs/server_cert.pem'  # local server public cert
    #clientCafilepath = '/etc/pki/tls/certs/client.pem' # remote client public cert

    #clientKeypath = '/etc/pki/tls/certs/client_key.pem'  # local client private key
    #clientCertpath = '/etc/pki/tls/certs/client_cert.pem'  # local client public cert
    #serverCafilepath = '/etc/pki/tls/certs/server.pem' # remote server public cert

    serverKeypath = self.certdirpath + '/server_key.pem'  # local server private key
    serverCertpath = self.certdirpath + '/server_cert.pem'  # local server public cert
    clientCafilepath = self.certdirpath + '/client.pem' # remote client public cert

    clientKeypath = self.certdirpath + '/client_key.pem'  # local client private key
    clientCertpath = self.certdirpath + '/client_cert.pem'  # local client public cert
    serverCafilepath = self.certdirpath + '/server.pem' # remote server public cert

    alpha = serving.ServerTls(host='localhost',
                                  port = 6101,
                                  bufsize=131072,
                                  wlog=wireLogAlpha,
                                  context=None,
                                  version=None,
                                  certify=None,
                                  keypath=serverKeypath,
                                  certpath=serverCertpath,
                                  cafilepath=clientCafilepath,
                                  )
    self.assertIs(alpha.reopen(), True)
    self.assertEqual(alpha.ha, ('127.0.0.1', 6101))

    serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname

    beta = clienting.ClientTls(ha=alpha.ha,
                                  bufsize=131072,
                                  wlog=wireLogBeta,
                                  context=None,
                                  version=None,
                                  certify=None,
                                  hostify=None,
                                  certedhost=serverCertCommonName,
                                  keypath=clientKeypath,
                                  certpath=clientCertpath,
                                  cafilepath=serverCafilepath,
                                  )
    self.assertIs(beta.reopen(), True)
    self.assertIs(beta.accepted, False)
    self.assertIs(beta.connected, False)
    self.assertIs(beta.cutoff, False)

    console.terse("Connecting  and Handshaking beta to alpha\n")
    while True:
        beta.serviceConnect()
        alpha.serviceConnects()
        if beta.connected and len(alpha.ixes) >= 1:
            break
        time.sleep(0.01)

    self.assertIs(beta.accepted, True)
    self.assertIs(beta.connected, True)
    self.assertIs(beta.cutoff, False)
    self.assertEqual(beta.ca, beta.cs.getsockname())
    self.assertEqual(beta.ha, beta.cs.getpeername())
    self.assertIs(beta.connected, True)

    ixBeta = alpha.ixes[beta.ca]
    self.assertIsNotNone(ixBeta.ca)
    self.assertIsNotNone(ixBeta.cs)
    self.assertEqual(ixBeta.cs.getsockname(), beta.cs.getpeername())
    self.assertEqual(ixBeta.cs.getpeername(), beta.cs.getsockname())
    self.assertEqual(ixBeta.ca, beta.ca)
    self.assertEqual(ixBeta.ha, beta.ha)

    msgOut = b"Beta sends to Alpha\n"
    beta.tx(msgOut)
    while True:
        beta.serviceTxes()
        alpha.serviceReceivesAllIx()
        time.sleep(0.01)
        if not beta.txes and ixBeta.rxbs:
            break

    time.sleep(0.05)
    alpha.serviceReceivesAllIx()

    msgIn = bytes(ixBeta.rxbs)
    self.assertEqual(msgIn, msgOut)
    #index = len(ixBeta.rxbs)
    ixBeta.clearRxbs()

    msgOut = b'Alpha sends to Beta\n'
    ixBeta.tx(msgOut)
    while True:
        alpha.serviceTxesAllIx()
        beta.serviceReceives()
        time.sleep(0.01)
        if not ixBeta.txes and beta.rxbs:
            break

    msgIn = bytes(beta.rxbs)
    self.assertEqual(msgIn, msgOut)
    #index = len(beta.rxbs)
    beta.clearRxbs()

    alpha.close()
    beta.close()

    self.assertEqual(wireLogAlpha.getRx(), wireLogAlpha.getTx())  # since wlog is same
    self.assertTrue(b"Beta sends to Alpha\n" in wireLogAlpha.getRx())
    self.assertTrue(b"Alpha sends to Beta\n" in wireLogAlpha.getRx())

    self.assertEqual(wireLogBeta.getRx(), wireLogBeta.getTx())  # since wlog is same
    self.assertTrue(b"Beta sends to Alpha\n" in wireLogBeta.getRx())
    self.assertTrue(b"Alpha sends to Beta\n" in wireLogBeta.getRx())

    wireLogAlpha.close()
    wireLogBeta.close()
    console.reinit(verbosity=console.Wordage.concise)


if __name__ == "__main__":
    test_tcp_client_server()
