# -*- encoding: utf-8 -*-
"""
tests  core.uxd.uxding module

"""
import pytest

import time
import socket
import os
import tempfile
import shutil

from hio import hioing
from hio.base import tyming, doing
from hio.core import wiring
from hio.core.uxd import uxding


def test_uxd_basic():
    """ Test the uxd connection between two peers

    """
    tymist = tyming.Tymist()
    with (wiring.openWL(samed=True, filed=True) as wl):
        bc = 4
        alpha = uxding.Peer(name="alpha", temp=True, umask=0o077, bc=bc, wl=wl)
        assert not alpha.opened
        assert alpha.reopen()
        assert alpha.opened
        assert alpha.path.endswith("alpha.uxd")
        #assert alpha.actualBufSizes() == (4194240, 4194240) == (bc * alpha.MaxGramSize, bc * alpha.MaxGramSize)

        beta = uxding.Peer(name="beta", temp=True, umask=0o077)
        assert beta.reopen()
        assert beta.path.endswith("beta.uxd")

        gamma = uxding.Peer(name="gamma", temp=True, umask=0o077)
        assert gamma.reopen()
        assert gamma.path.endswith("gamma.uxd")

        txMsg = b"Alpha sends to Beta"
        alpha.send(txMsg, beta.path)
        rxMsg, src = beta.receive()
        assert txMsg == rxMsg
        assert src == alpha.path

        txMsg = b"Alpha sends to Gamma"
        alpha.send(txMsg, gamma.path)
        rxMsg, src = gamma.receive()
        assert txMsg == rxMsg
        assert src == alpha.path

        txMsg = b"Alpha sends to Alpha"
        alpha.send(txMsg, alpha.path)
        rxMsg, src = alpha.receive()
        assert txMsg == rxMsg
        assert src == alpha.path

        txMsg = b"Beta sends to Alpha"
        beta.send(txMsg, alpha.path)
        rxMsg, src = alpha.receive()
        assert txMsg == rxMsg
        assert src == beta.path

        txMsg = b"Beta sends to Gamma"
        beta.send(txMsg, gamma.path)
        rxMsg, src = gamma.receive()
        assert txMsg == rxMsg
        assert src == beta.path

        txMsg = b"Beta sends to Beta"
        beta.send(txMsg, beta.path)
        rxMsg, src = beta.receive()
        assert txMsg == rxMsg
        assert src == beta.path

        txMsg = b"Gamma sends to Alpha"
        gamma.send(txMsg, alpha.path)
        rxMsg, src = alpha.receive()
        assert txMsg == rxMsg
        assert src == gamma.path

        txMsg = b"Gamma sends to Beta"
        gamma.send(txMsg, beta.path)
        rxMsg, src = beta.receive()
        assert txMsg == rxMsg
        assert src == gamma.path

        txMsg = b"Gamma sends to Gamma"
        gamma.send(txMsg, gamma.path)
        rxMsg, src = gamma.receive()
        assert txMsg == rxMsg
        assert src == gamma.path


        pairs = [(alpha, beta), (alpha, gamma), (alpha, alpha),
                 (beta, alpha), (beta, gamma), (beta, beta),
                 (gamma, alpha), (gamma, beta), (gamma, gamma),]
        names = [('alpha', 'beta'), ('alpha', 'gamma'), ('alpha', 'alpha'),
                 ('beta', 'alpha'), ('beta', 'gamma'), ('beta', 'beta'),
                 ('gamma', 'alpha'), ('gamma', 'beta'), ('gamma', 'gamma'),]

        for i, pair in enumerate(pairs):
            txer, rxer = pair
            txName, rxName =  names[i]
            #converts to bytes
            txMsg = f"{txName.capitalize()} sends to {rxName.capitalize()} again".encode()
            txer.send(txMsg, rxer.path)
            rxMsg, src = rxer.receive()
            assert txMsg == rxMsg
            assert src == txer.path

        rxMsg, src = alpha.receive()
        assert b'' == rxMsg
        assert None == src

        rxMsg, src = beta.receive()
        assert b'' == rxMsg
        assert None == src

        rxMsg, src = gamma.receive()
        assert b'' == rxMsg
        assert None == src

        alpha.close()
        assert not alpha.opened
        assert not os.path.exists(alpha.path)
        beta.close()
        assert not beta.opened
        assert not os.path.exists(beta.path)
        gamma.close()
        assert not gamma.opened
        assert not os.path.exists(gamma.path)


        wl.flush()  #  just to test
        assert wl.samed  # rx and tx same buffer

        assert wl.readRx()
        assert wl.readTx()
        assert wl.readTx() == wl.readRx()


    """Done Test"""

def test_open_peer():
    """Test the uxd openPeer context manager connection between two peers

    """

    tymist = tyming.Tymist()
    with (wiring.openWL(samed=True, filed=True) as wl,
          uxding.openPeer(name ="alpha", umask=0o077, wl=wl) as alpha,
          uxding.openPeer(name = "beta", umask=0o077, wl=wl) as beta,
          uxding.openPeer(name = "gamma", umask=0o077, wl=wl) as gamma):


        assert alpha.opened
        assert alpha.path.endswith("alpha.uxd")
        #assert alpha.actualBufSizes() == (65535, 65535) == (alpha.BufSize, alpha.BufSize)

        assert beta.opened
        assert beta.path.endswith("beta.uxd")

        assert gamma.opened
        assert gamma.path.endswith("gamma.uxd")

        txMsg = b"Alpha sends to Beta"
        alpha.send(txMsg, beta.path)
        rxMsg, src = beta.receive()
        assert txMsg == rxMsg
        assert src == alpha.path

        txMsg = b"Alpha sends to Gamma"
        alpha.send(txMsg, gamma.path)
        rxMsg, src = gamma.receive()
        assert txMsg == rxMsg
        assert src == alpha.path

        txMsg = b"Alpha sends to Alpha"
        alpha.send(txMsg, alpha.path)
        rxMsg, src = alpha.receive()
        assert txMsg == rxMsg
        assert src == alpha.path

        txMsg = b"Beta sends to Alpha"
        beta.send(txMsg, alpha.path)
        rxMsg, src = alpha.receive()
        assert txMsg == rxMsg
        assert src == beta.path

        txMsg = b"Beta sends to Gamma"
        beta.send(txMsg, gamma.path)
        rxMsg, src = gamma.receive()
        assert txMsg == rxMsg
        assert src == beta.path

        txMsg = b"Beta sends to Beta"
        beta.send(txMsg, beta.path)
        rxMsg, src = beta.receive()
        assert txMsg == rxMsg
        assert src == beta.path

        txMsg = b"Gamma sends to Alpha"
        gamma.send(txMsg, alpha.path)
        rxMsg, src = alpha.receive()
        assert txMsg == rxMsg
        assert src == gamma.path

        txMsg = b"Gamma sends to Beta"
        gamma.send(txMsg, beta.path)
        rxMsg, src = beta.receive()
        assert txMsg == rxMsg
        assert src == gamma.path

        txMsg = b"Gamma sends to Gamma"
        gamma.send(txMsg, gamma.path)
        rxMsg, src = gamma.receive()
        assert txMsg == rxMsg
        assert src == gamma.path


        pairs = [(alpha, beta), (alpha, gamma), (alpha, alpha),
                 (beta, alpha), (beta, gamma), (beta, beta),
                 (gamma, alpha), (gamma, beta), (gamma, gamma),]
        names = [('alpha', 'beta'), ('alpha', 'gamma'), ('alpha', 'alpha'),
                 ('beta', 'alpha'), ('beta', 'gamma'), ('beta', 'beta'),
                 ('gamma', 'alpha'), ('gamma', 'beta'), ('gamma', 'gamma'),]

        for i, pair in enumerate(pairs):
            txer, rxer = pair
            txName, rxName =  names[i]
            #converts to bytes
            txMsg = f"{txName.capitalize()} sends to {rxName.capitalize()} again".encode()
            txer.send(txMsg, rxer.path)
            rxMsg, src = rxer.receive()
            assert txMsg == rxMsg
            assert src == txer.path

        rxMsg, src = alpha.receive()
        assert b'' == rxMsg
        assert None == src

        rxMsg, src = beta.receive()
        assert b'' == rxMsg
        assert None == src

        rxMsg, src = gamma.receive()
        assert b'' == rxMsg
        assert None == src

        wl.flush()  #  just to test
        assert wl.samed  # rx and tx same buffer

        assert wl.readRx()
        assert wl.readTx()
        assert wl.readTx() == wl.readRx()

    assert not alpha.opened
    assert not os.path.exists(alpha.path)
    assert not beta.opened
    assert not os.path.exists(beta.path)
    assert not gamma.opened
    assert not os.path.exists(gamma.path)

    assert not wl.opened

    """Done Test"""

def test_uxd_path_len():
    """ Test the uxd path length

    """
    with pytest.raises(hioing.SizeError):
        name = "alpha" * 25
        assert len(name) > uxding.Peer.MaxUxdPathSize
        alpha = uxding.Peer(name=name, temp=True, reopen=True)
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


    peer = uxding.Peer(name="test", temp=True, reopen=False, umask=0o077)
    assert peer.opened == False
    assert peer.path == None
    assert peer.filed == False
    assert peer.extensioned == True

    doer = uxding.PeerDoer(peer=peer)
    assert doer.peer == peer
    assert doer.peer.opened == False

    doers = [doer]
    doist.do(doers=doers)
    assert doist.tyme == limit
    assert peer.opened == False
    assert not os.path.exists(peer.path)
    """Done Test"""



if __name__ == "__main__":
    test_uxd_basic()
    test_open_peer()
    test_uxd_path_len()
    test_peer_doer()
