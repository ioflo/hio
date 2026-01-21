# -*- encoding: utf-8 -*-
"""
tests  core.udp.udping module

"""
import pytest

import time
import platform
import socket

from hio.base import tyming, doing
from hio.core import wiring
from hio.core.udp import udping


def test_udp_basic():
    """ Test the udp connection between two peers

    """
    tymist = tyming.Tymist()
    with (wiring.openWL(samed=True, filed=True) as wl):

        # can't use '0.0.0.0' on macos without getting local network access permissions
        #  for python, but does not trigger automatically and no way to force trigger
        # unless create application bundle etc.

        #host = socket.gethostbyname(socket.gethostname())  # get host interface
        host = '127.0.0.1'
        alphaPort = 6101
        betaPort = 6102
        alphaHa = (host, alphaPort)
        betaHa = (host, betaPort)

        alpha = udping.Peer(host=host, port = alphaPort, wl=wl)  # host on port 6101
        assert not alpha.opened
        assert alpha.name == 'main'  # default
        assert alpha.reopen()
        assert alpha.opened
        assert alpha.ha == alphaHa
        assert alpha.path == alpha.ha

        beta = udping.Peer(name='beta',host=host, port = betaPort, wl=wl)  # host on port 6102
        assert not beta.opened
        assert beta.name == 'beta'
        assert beta.reopen()
        assert beta.opened
        assert beta.ha == betaHa
        assert beta.path == beta.ha

        msgOut = b"alpha sends to beta"
        alpha.send(msgOut, beta.ha)
        time.sleep(0.05)
        msgIn, src = beta.receive()
        assert msgOut == msgIn
        assert src[1] == alpha.port  # ports equal

        msgOut = b"alpha sends to alpha"
        alpha.send(msgOut, alpha.ha)
        time.sleep(0.05)
        msgIn, src = alpha.receive()
        assert msgOut == msgIn
        assert src[1] == alpha.port  # ports equal

        msgOut = b"beta sends to alpha"
        beta.send(msgOut, alpha.ha)
        time.sleep(0.05)
        msgIn, src = alpha.receive()
        assert msgOut == msgIn
        assert src[1] == beta.port  # ports equal

        msgOut = b"beta sends to beta"
        beta.send(msgOut, beta.ha)
        time.sleep(0.05)
        msgIn, src = beta.receive()
        assert msgOut == msgIn
        assert src[1] == beta.port  # ports equal

        alpha.close()
        beta.close()

        assert not alpha.opened
        assert not beta.opened

        wl.flush()  #  just to test
        assert wl.samed  # rx and tx same buffer

        def addrBytes(ha):
            return f"('{ha[0]}', {ha[1]})".encode("ascii")

        assert wl.readRx() == (b"\nTx ('127.0.0.1', 6102):\nalpha sends to beta\n\nRx ('127.0.0.1', 6101)"
                                b":\nalpha sends to beta\n\nTx ('127.0.0.1', 6101):\nalpha sends to alpha\n"
                                b"\nRx ('127.0.0.1', 6101):\nalpha sends to alpha\n\nTx ('127.0.0.1', 6101"
                                b"):\nbeta sends to alpha\n\nRx ('127.0.0.1', 6102):\nbeta sends to alpha\n"
                                b"\nTx ('127.0.0.1', 6102):\nbeta sends to beta\n\nRx ('127.0.0.1', 6102):"
                                b'\nbeta sends to beta\n')
        assert wl.readTx() == (b"\nTx ('127.0.0.1', 6102):\nalpha sends to beta\n\nRx ('127.0.0.1', 6101)"
                                b":\nalpha sends to beta\n\nTx ('127.0.0.1', 6101):\nalpha sends to alpha\n"
                                b"\nRx ('127.0.0.1', 6101):\nalpha sends to alpha\n\nTx ('127.0.0.1', 6101"
                                b"):\nbeta sends to alpha\n\nRx ('127.0.0.1', 6102):\nbeta sends to alpha\n"
                                b"\nTx ('127.0.0.1', 6102):\nbeta sends to beta\n\nRx ('127.0.0.1', 6102):"
                                b'\nbeta sends to beta\n')


        assert wl.readTx() == wl.readRx()

    assert not wl.opened
    """Done Test"""

def test_udp():
    """ Test the udp connection between two peers with bc and bs

    """

    tymist = tyming.Tymist()
    with (wiring.openWL(samed=True, filed=True) as wl):
        host = '127.0.0.1'
        alphaPort = 6101
        betaPort = 6102
        alphaHa = (host, alphaPort)
        betaHa = (host, betaPort)
        bc = 1024

        alpha = udping.Peer(host=host, port = alphaPort, wl=wl, bc=bc)
        assert not alpha.opened
        assert alpha.name == 'main'  # default
        assert alpha.bc == bc
        assert alpha.MaxGramSize == 1240  # max safe payload
        assert alpha.bs == bc * alpha.MaxGramSize == 1269760
        assert alpha.actualBufSizes() == (0, 0)  # not opened yet
        assert alpha.reopen()
        assert alpha.opened
        assert alpha.ha == alphaHa
        assert alpha.actualBufSizes() == (alpha.bs, alpha.bs) == (1269760, 1269760)

        bs = 2 ** 15 - 1
        assert bs == 32767
        beta = udping.Peer(name='beta',host=host, port = betaPort, wl=wl, bs=bs)  # host on port 6102
        assert not beta.opened
        assert beta.name == 'beta'
        assert beta.bc is None
        assert beta.bs == bs
        assert beta.actualBufSizes() == (0, 0)  # not opened yet
        assert beta.reopen()
        assert beta.opened
        assert beta.ha == betaHa
        bses = beta.actualBufSizes()
        assert bses[0] >= beta.bs
        assert bses[1] >= beta.bs

        msgOut = b"alpha sends to beta"
        alpha.send(msgOut, beta.ha)
        time.sleep(0.05)
        msgIn, src = beta.receive()
        assert msgOut == msgIn
        assert src[1] == alpha.port  # ports equal

        msgOut = b"alpha sends to alpha"
        alpha.send(msgOut, alpha.ha)
        time.sleep(0.05)
        msgIn, src = alpha.receive()
        assert msgOut == msgIn
        assert src[1] == alpha.port  # ports equal

        msgOut = b"beta sends to alpha"
        beta.send(msgOut, alpha.ha)
        time.sleep(0.05)
        msgIn, src = alpha.receive()
        assert msgOut == msgIn
        assert src[1] == beta.port  # ports equal

        msgOut = b"beta sends to beta"
        beta.send(msgOut, beta.ha)
        time.sleep(0.05)
        msgIn, src = beta.receive()
        assert msgOut == msgIn
        assert src[1] == beta.port  # ports equal

        alpha.close()
        beta.close()

        assert not alpha.opened
        assert not beta.opened

        wl.flush()  #  just to test
        assert wl.samed  # rx and tx same buffer

        def addrBytes(ha):
            return f"('{ha[0]}', {ha[1]})".encode("ascii")

        assert wl.readRx() == (b"\nTx ('127.0.0.1', 6102):\nalpha sends to beta\n\nRx ('127.0.0.1', 6101)"
                                b":\nalpha sends to beta\n\nTx ('127.0.0.1', 6101):\nalpha sends to alpha\n"
                                b"\nRx ('127.0.0.1', 6101):\nalpha sends to alpha\n\nTx ('127.0.0.1', 6101"
                                b"):\nbeta sends to alpha\n\nRx ('127.0.0.1', 6102):\nbeta sends to alpha\n"
                                b"\nTx ('127.0.0.1', 6102):\nbeta sends to beta\n\nRx ('127.0.0.1', 6102):"
                                b'\nbeta sends to beta\n')
        assert wl.readTx() == (b"\nTx ('127.0.0.1', 6102):\nalpha sends to beta\n\nRx ('127.0.0.1', 6101)"
                                b":\nalpha sends to beta\n\nTx ('127.0.0.1', 6101):\nalpha sends to alpha\n"
                                b"\nRx ('127.0.0.1', 6101):\nalpha sends to alpha\n\nTx ('127.0.0.1', 6101"
                                b"):\nbeta sends to alpha\n\nRx ('127.0.0.1', 6102):\nbeta sends to alpha\n"
                                b"\nTx ('127.0.0.1', 6102):\nbeta sends to beta\n\nRx ('127.0.0.1', 6102):"
                                b'\nbeta sends to beta\n')


        assert wl.readTx() == wl.readRx()

    assert not wl.opened
    """Done Test"""

def test_open_peer():
    """Test the udp openPeer context manager connection between two peers

    """
    tymist = tyming.Tymist()

    # can't use '0.0.0.0' on macos without getting local network access permissions
    #  for python, but does not trigger automatically and no way to force trigger
    # unless create application bundle etc.

    #host = socket.gethostbyname(socket.gethostname())  # get host interface
    host = '127.0.0.1'
    alphaPort = 6101
    betaPort = 6102
    alphaHa = (host, alphaPort)
    betaHa = (host, betaPort)

    with (wiring.openWL(samed=True, filed=True) as wl,
            udping.openPeer(ha=alphaHa, wl=wl) as alpha, # host on port 6101
            udping.openPeer(ha=betaHa, wl=wl) as beta):  # host on port 6102

        assert alpha.opened
        assert alpha.ha == (host, alphaPort)

        assert beta.opened
        assert beta.ha == (host, betaPort)

        msgOut = b"alpha sends to beta"
        alpha.send(msgOut, beta.ha)
        time.sleep(0.1)
        msgIn, src = beta.receive()
        assert msgOut == msgIn
        assert src[1] == alpha.port  # ports equal

        msgOut = b"alpha sends to alpha"
        alpha.send(msgOut, alpha.ha)
        time.sleep(0.1)
        msgIn, src = alpha.receive()
        assert msgOut == msgIn
        assert src[1] == alpha.port  # ports equal

        msgOut = b"beta sends to alpha"
        beta.send(msgOut, alpha.ha)
        time.sleep(0.1)
        msgIn, src = alpha.receive()
        assert msgOut == msgIn
        assert src[1] == beta.port  # ports equal

        msgOut = b"beta sends to beta"
        beta.send(msgOut, beta.ha)
        time.sleep(0.1)
        msgIn, src = beta.receive()
        assert msgOut == msgIn
        assert src[1] == beta.port  # ports equal


        wl.flush()  #  just to test
        assert wl.samed  # rx and tx same buffer

        def addrBytes(ha):
            return f"('{ha[0]}', {ha[1]})".encode("ascii")

        assert wl.readRx() == (b"\nTx ('127.0.0.1', 6102):\nalpha sends to beta\n\nRx ('127.0.0.1', 6101)"
                                b":\nalpha sends to beta\n\nTx ('127.0.0.1', 6101):\nalpha sends to alpha\n"
                                b"\nRx ('127.0.0.1', 6101):\nalpha sends to alpha\n\nTx ('127.0.0.1', 6101"
                                b"):\nbeta sends to alpha\n\nRx ('127.0.0.1', 6102):\nbeta sends to alpha\n"
                                b"\nTx ('127.0.0.1', 6102):\nbeta sends to beta\n\nRx ('127.0.0.1', 6102):"
                                b'\nbeta sends to beta\n')

        assert wl.readTx() == (b"\nTx ('127.0.0.1', 6102):\nalpha sends to beta\n\nRx ('127.0.0.1', 6101)"
                                b":\nalpha sends to beta\n\nTx ('127.0.0.1', 6101):\nalpha sends to alpha\n"
                                b"\nRx ('127.0.0.1', 6101):\nalpha sends to alpha\n\nTx ('127.0.0.1', 6101"
                                b"):\nbeta sends to alpha\n\nRx ('127.0.0.1', 6102):\nbeta sends to alpha\n"
                                b"\nTx ('127.0.0.1', 6102):\nbeta sends to beta\n\nRx ('127.0.0.1', 6102):"
                                b'\nbeta sends to beta\n')

        assert wl.readTx() == wl.readRx()

    assert not alpha.opened
    assert not beta.opened
    assert not wl.opened

    """Done Test"""

def test_peer_doer():
    """
    Test PeerDoer class

    Must run in WingIDE with Debug I/O configured as external console
    """
    tock = 0.03125
    ticks = 8
    limit = tock * ticks
    doist = doing.Doist(tock=tock, real=True, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == limit
    assert doist.doers == []

    peer = udping.Peer(port = 6101)
    doer = udping.PeerDoer(tymth=doist.tymen(), peer=peer)

    doers = [doer]
    doist.do(doers=doers)
    assert doist.tyme == limit
    assert peer.opened == False

    """Done Test"""

#def test_udp_broadcast():
    #""" Test the udp connection between two peers for broadcast

    #https://stackoverflow.com/questions/64066634/sending-broadcast-in-python
    #with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        #sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        #sock.sendto(msg, ("255.255.255.255", 5005))

    #Notice no bind on sending socket. But binding on sending socket should not
    #prevent it from working. It just specifies the source address when its
    #received.

    #https://stackoverflow.com/questions/683624/udp-broadcast-on-all-interfaces
    #https://forums.raspberrypi.com/viewtopic.php?t=258448


    #System settings -> Privacy & Security -> Local Network

    #"""
    #tymist = tyming.Tymist()
    #with (wiring.openWL(samed=True, filed=True) as wl):

        #unicast = socket.gethostbyname(socket.gethostname())
        ##assert unicast == "127.0.0.1"
        #parts = unicast.split('.')
        #parts[3] = '255'
        #broadcast = ".".join(parts)  # make broadcast send address
        ##assert broadcast == "127.0.0.255"
        #bha = (broadcast, 6104)

        #alpha = udping.Peer(host=unicast,
                            #port = 6103,
                            #bcast=True)   # needed to send broadcast
        #assert not alpha.opened
        #assert alpha.reopen()
        #assert alpha.opened
        #assert alpha.bcast
        #assert alpha.ha == (unicast, 6103)

        ##beta = udping.Peer(host="", port=6104)
        #beta = udping.Peer(host=unicast,  port=6104)
        #assert not beta.opened
        #assert beta.reopen()
        #assert not beta.bcast
        ##assert beta.ha == ("0.0.0.0", 6104)
        ##assert beta.ha == ("127.0.0.1", 6104)
        #assert beta.ha[1] == bha[1]  # same port

        #msgOut = b"alpha broadcasts to beta"
        #msgIn = b""
        #src = None
        #alpha.send(msgOut, bha)
        #time.sleep(0.05)
        #msgIn, src = beta.receive()

        ##tries = 0
        ##while not msgIn and tries < 10:
            ##alpha.send(msgOut, bha)
            ##time.sleep(0.05)
            ##msgIn, src = beta.receive()
            ##tries += 1

        #assert msgIn == msgOut
        #assert src == alpha.ha

        #alpha.close()
        #beta.close()
        #time.sleep(0.1)

        #beta = udping.SocketUdpNb(host="",  # any
                                  #port=6102,
                                  #bcast=True)  # needed to send broadcast
        #assert not beta.opened
        #assert beta.reopen()
        #assert beta.bcast
        #assert beta.ha == ("0.0.0.0", 6102)
        #assert beta.ha[1] == bha[1]  # same port


        #msgOut = b"beta broadcasts to beta"
        #beta.send(msgOut, bha)
        #time.sleep(0.05)
        #msgIn, src = beta.receive()
        #assert msgIn == msgOut
        #assert src[1] == beta.ha[1]

        #alpha.close()
        #beta.close()

        #assert not alpha.opened
        #assert not beta.opened

    #"""Done Test"""

#def test_udp_basic_old():
    #""" Test the udp connection between two peers

    #"""
    #tymist = tyming.Tymist()
    #with (wiring.openWL(samed=True, filed=True) as wl):

        #alpha = udping.Peer(port = 6101, wl=wl)  # any interface on port 6101
        #if platform.system() == 'Windows':
            #alpha = udping.Peer(ha=('127.0.0.1', 6101), wl=wl)
        #assert not alpha.opened
        #assert alpha.name == 'main'  # default
        #assert alpha.reopen()
        #assert alpha.opened
        #if platform.system() == 'Windows':
            #assert alpha.ha == ('127.0.0.1', 6101)
        #else:
            #assert alpha.ha == ('0.0.0.0', 6101)

        #beta = udping.Peer(name='beta',port = 6102, wl=wl)  # any interface on port 6102
        #if platform.system() == 'Windows':
            #beta = udping.Peer(name='beta', ha=('127.0.0.1', 6102), wl=wl)

        #assert not beta.opened
        #assert beta.name == 'beta'
        #assert beta.reopen()
        #assert beta.opened
        #if platform.system() == 'Windows':
            #assert beta.ha == ('127.0.0.1', 6102)
        #else:
            #assert beta.ha == ('0.0.0.0', 6102)

        #msgOut = b"alpha sends to beta"
        #alpha.send(msgOut, beta.ha)
        #time.sleep(0.05)
        #msgIn, src = beta.receive()
        #assert msgOut == msgIn
        #assert src[1] == alpha.port  # ports equal

        #msgOut = b"alpha sends to alpha"
        #alpha.send(msgOut, alpha.ha)
        #time.sleep(0.05)
        #msgIn, src = alpha.receive()
        #assert msgOut == msgIn
        #assert src[1] == alpha.port  # ports equal

        #msgOut = b"beta sends to alpha"
        #beta.send(msgOut, alpha.ha)
        #time.sleep(0.05)
        #msgIn, src = alpha.receive()
        #assert msgOut == msgIn
        #assert src[1] == beta.port  # ports equal

        #msgOut = b"beta sends to beta"
        #beta.send(msgOut, beta.ha)
        #time.sleep(0.05)
        #msgIn, src = beta.receive()
        #assert msgOut == msgIn
        #assert src[1] == beta.port  # ports equal

        #alpha.close()
        #beta.close()

        #assert not alpha.opened
        #assert not beta.opened

        #wl.flush()  #  just to test
        #assert wl.samed  # rx and tx same buffer

        #def addrBytes(ha):
            #return f"('{ha[0]}', {ha[1]})".encode("ascii")

        #assert wl.readRx() == (b"\nTx "+addrBytes(beta.ha)+b":\nalpha sends to beta\n\nRx ('127.0.0.1', 6101):\n"
                            #b"alpha sends to beta\n\nTx "+addrBytes(alpha.ha)+b":\nalpha sends to alpha\n\nRx "
                            #b"('127.0.0.1', 6101):\nalpha sends to alpha\n\nTx "+addrBytes(alpha.ha)+b":\nbeta se"
                            #b"nds to alpha\n\nRx ('127.0.0.1', 6102):\nbeta sends to alpha\n\nTx "+addrBytes(beta.ha)+
                            #b":\nbeta sends to beta\n\nRx ('127.0.0.1', 6102):\nbeta sends to b"
                            #b'eta\n')
        #assert wl.readTx() == (b"\nTx "+addrBytes(beta.ha)+b":\nalpha sends to beta\n\nRx ('127.0.0.1', 6101):\n"
                            #b"alpha sends to beta\n\nTx "+addrBytes(alpha.ha)+b":\nalpha sends to alpha\n\nRx "
                            #b"('127.0.0.1', 6101):\nalpha sends to alpha\n\nTx "+addrBytes(alpha.ha)+b":\nbeta se"
                            #b"nds to alpha\n\nRx ('127.0.0.1', 6102):\nbeta sends to alpha\n\nTx "+addrBytes(beta.ha)+
                            #b":\nbeta sends to beta\n\nRx ('127.0.0.1', 6102):\nbeta sends to b"
                            #b'eta\n')

        #assert wl.readTx() == wl.readRx()

    #assert not wl.opened
    #"""Done Test"""


if __name__ == "__main__":
    test_udp_basic()
    test_udp()
    test_open_peer()
    test_peer_doer()
    #test_udp_broadcast()
