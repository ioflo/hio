# -*- encoding: utf-8 -*-
"""
tests  core.udp.udping module

"""
import pytest

import time
import socket

from hio.base import tyming, doing
from hio.core import wiring
from hio.core.udp import udping


def test_udp_basic():
    """ Test the udp connection between two peers

    """
    tymist = tyming.Tymist()
    with (wiring.openWL(samed=True, filed=True) as wl):

        alpha = udping.Peer(port = 6101, wl=wl)  # any interface on port 6101
        assert not alpha.opened
        assert alpha.reopen()
        assert alpha.opened
        assert alpha.ha == ('0.0.0.0', 6101)

        beta = udping.Peer(port = 6102, wl=wl)  # any interface on port 6102
        assert not beta.opened
        assert beta.reopen()
        assert beta.opened
        assert beta.ha == ('0.0.0.0', 6102)

        msgOut = b"alpha sends to beta"
        alpha.send(msgOut, beta.ha)
        time.sleep(0.05)
        msgIn, src = beta.receive()
        assert msgOut == msgIn
        assert src[1] == alpha.ha[1]  # ports equal

        msgOut = b"alpha sends to alpha"
        alpha.send(msgOut, alpha.ha)
        time.sleep(0.05)
        msgIn, src = alpha.receive()
        assert msgOut == msgIn
        assert src[1] == alpha.ha[1]  # ports equal

        msgOut = b"beta sends to alpha"
        beta.send(msgOut, alpha.ha)
        time.sleep(0.05)
        msgIn, src = alpha.receive()
        assert msgOut == msgIn
        assert src[1] == beta.ha[1]  # ports equal

        msgOut = b"beta sends to beta"
        beta.send(msgOut, beta.ha)
        time.sleep(0.05)
        msgIn, src = beta.receive()
        assert msgOut == msgIn
        assert src[1] == beta.ha[1]  # ports equal

        alpha.close()
        beta.close()

        assert not alpha.opened
        assert not beta.opened

        wl.flush()  #  just to test
        assert wl.samed  # rx and tx same buffer

        assert wl.readRx() == (b"\nTx ('0.0.0.0', 6102):\nalpha sends to beta\n\nRx ('127.0.0.1', 6101):\n"
                                b"alpha sends to beta\n\nTx ('0.0.0.0', 6101):\nalpha sends to alpha\n\nRx "
                                b"('127.0.0.1', 6101):\nalpha sends to alpha\n\nTx ('0.0.0.0', 6101):\nbeta se"
                                b"nds to alpha\n\nRx ('127.0.0.1', 6102):\nbeta sends to alpha\n\nTx ('0.0."
                                b"0.0', 6102):\nbeta sends to beta\n\nRx ('127.0.0.1', 6102):\nbeta sends to b"
                                b'eta\n')
        assert wl.readTx() == (b"\nTx ('0.0.0.0', 6102):\nalpha sends to beta\n\nRx ('127.0.0.1', 6101):\n"
                            b"alpha sends to beta\n\nTx ('0.0.0.0', 6101):\nalpha sends to alpha\n\nRx "
                            b"('127.0.0.1', 6101):\nalpha sends to alpha\n\nTx ('0.0.0.0', 6101):\nbeta se"
                            b"nds to alpha\n\nRx ('127.0.0.1', 6102):\nbeta sends to alpha\n\nTx ('0.0."
                            b"0.0', 6102):\nbeta sends to beta\n\nRx ('127.0.0.1', 6102):\nbeta sends to b"
                            b'eta\n')

        assert wl.readTx() == wl.readRx()
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
        #assert unicast == "127.0.0.1"
        #parts = unicast.split('.')
        #parts[3] = '255'
        #broadcast = ".".join(parts)  # make broadcast send address
        #assert broadcast == "127.0.0.255"
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
        #assert beta.ha == ("127.0.0.1", 6104)
        #assert beta.ha[1] == bha[1]  # same port

        #msgOut = b"alpha broadcasts to beta"
        #msgIn = b""
        #src = None
        #tries = 0
        #while not msgIn and tries < 10:
            #alpha.send(msgOut, bha)
            #time.sleep(0.05)
            #msgIn, src = beta.receive()
            #tries += 1

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


if __name__ == "__main__":
    test_udp_basic()
    #test_udp_broadcast()
