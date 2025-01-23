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

from hio.base import tyming, doing
from hio.core import wiring
from hio.core.uxd import uxding


def test_uxd_basic():
    """ Test the uxd connection between two peers

    """
    tymist = tyming.Tymist()
    with (wiring.openWL(samed=True, filed=True) as wl):
        testDirpath = os.path.join('~', '.hio', 'test')
        testDirpath = os.path.abspath(os.path.expanduser(testDirpath))
        if not os.path.exists(testDirpath):
            os.makedirs(testDirpath)

        tempDirpath = tempfile.mkdtemp(prefix="test", suffix="uxd", dir=testDirpath)

        sockDirpath = os.path.join(tempDirpath, 'uxd')
        if not os.path.exists(sockDirpath):
            os.makedirs(sockDirpath)

        ha = os.path.join(sockDirpath, 'alpha.uxd')
        assert ha.endswith("/uxd/alpha.uxd")

        alpha = uxding.Peer(ha=ha, umask=0o077, wl=wl)
        assert not alpha.opened
        assert alpha.reopen()
        assert alpha.opened
        assert alpha.ha == ha

        ha = os.path.join(sockDirpath, 'beta.uxd')
        beta = uxding.Peer(ha=ha, umask=0o077)
        assert beta.reopen()
        assert beta.ha == ha

        ha = os.path.join(sockDirpath, 'gamma.uxd')
        gamma = uxding.Peer(ha=ha, umask=0o077)
        assert gamma.reopen()
        assert gamma.ha == ha

        txMsg = b"Alpha sends to Beta"
        alpha.send(txMsg, beta.ha)
        rxMsg, sa = beta.receive()
        assert txMsg == rxMsg
        assert sa == alpha.ha

        txMsg = b"Alpha sends to Gamma"
        alpha.send(txMsg, gamma.ha)
        rxMsg, sa = gamma.receive()
        assert txMsg == rxMsg
        assert sa == alpha.ha

        txMsg = b"Alpha sends to Alpha"
        alpha.send(txMsg, alpha.ha)
        rxMsg, sa = alpha.receive()
        assert txMsg == rxMsg
        assert sa == alpha.ha

        txMsg = b"Beta sends to Alpha"
        beta.send(txMsg, alpha.ha)
        rxMsg, sa = alpha.receive()
        assert txMsg == rxMsg
        assert sa == beta.ha

        txMsg = b"Beta sends to Gamma"
        beta.send(txMsg, gamma.ha)
        rxMsg, sa = gamma.receive()
        assert txMsg == rxMsg
        assert sa == beta.ha

        txMsg = b"Beta sends to Beta"
        beta.send(txMsg, beta.ha)
        rxMsg, sa = beta.receive()
        assert txMsg == rxMsg
        assert sa == beta.ha

        txMsg = b"Gamma sends to Alpha"
        gamma.send(txMsg, alpha.ha)
        rxMsg, sa = alpha.receive()
        assert txMsg == rxMsg
        assert sa == gamma.ha

        txMsg = b"Gamma sends to Beta"
        gamma.send(txMsg, beta.ha)
        rxMsg, sa = beta.receive()
        assert txMsg == rxMsg
        assert sa == gamma.ha

        txMsg = b"Gamma sends to Gamma"
        gamma.send(txMsg, gamma.ha)
        rxMsg, sa = gamma.receive()
        assert txMsg == rxMsg
        assert sa == gamma.ha


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
            txer.send(txMsg, rxer.ha)
            rxMsg, sa = rxer.receive()
            assert txMsg == rxMsg
            assert sa == txer.ha

        rxMsg, sa = alpha.receive()
        assert b'' == rxMsg
        assert None == sa

        rxMsg, sa = beta.receive()
        assert b'' == rxMsg
        assert None == sa

        rxMsg, sa = gamma.receive()
        assert b'' == rxMsg
        assert None == sa

        alpha.close()
        assert not alpha.opened
        beta.close()
        assert not beta.opened
        gamma.close()
        assert not gamma.opened


        wl.flush()  #  just to test
        assert wl.samed  # rx and tx same buffer

        assert wl.readRx()
        assert wl.readTx()
        assert wl.readTx() == wl.readRx()

        shutil.rmtree(testDirpath)  # and all dependent paths

    assert not os.path.exists(testDirpath)
    assert not os.path.exists(tempDirpath)
    assert not os.path.exists(sockDirpath)

    """Done Test"""

def test_open_peer():
    """Test the uxd openPeer context manager connection between two peers

    """
    testDirpath = os.path.join('~', '.hio', 'test')
    testDirpath = os.path.abspath(os.path.expanduser(testDirpath))
    if not os.path.exists(testDirpath):
        os.makedirs(testDirpath)
    tempDirpath = tempfile.mkdtemp(prefix="test", suffix="uxd", dir=testDirpath)
    sockDirpath = os.path.join(tempDirpath, 'uxd')
    if not os.path.exists(sockDirpath):
        os.makedirs(sockDirpath)

    aha = os.path.join(sockDirpath, 'alpha.uxd')
    assert aha.endswith("/uxd/alpha.uxd")
    bha = os.path.join(sockDirpath, 'beta.uxd')
    assert bha.endswith("/uxd/beta.uxd")
    gha = os.path.join(sockDirpath, 'gamma.uxd')
    assert gha.endswith("/uxd/gamma.uxd")


    tymist = tyming.Tymist()
    with (wiring.openWL(samed=True, filed=True) as wl,
          uxding.openPeer(ha = aha, umask=0o077, wl=wl) as alpha,
          uxding.openPeer(ha = bha, umask=0o077, wl=wl) as beta,
          uxding.openPeer(ha = gha, umask=0o077, wl=wl) as gamma):


        #alpha = uxding.Peer(ha=ha, umask=0x077, wl=wl)
        assert alpha.opened
        assert alpha.ha == aha

        #beta = uxding.Peer(ha=bha, umask=0x077)
        assert beta.opened
        assert beta.ha == bha

        #gamma = uxding.Peer(ha=gha, umask=0x077)
        assert gamma.opened
        assert gamma.ha == gha

        txMsg = b"Alpha sends to Beta"
        alpha.send(txMsg, beta.ha)
        rxMsg, sa = beta.receive()
        assert txMsg == rxMsg
        assert sa == alpha.ha

        txMsg = b"Alpha sends to Gamma"
        alpha.send(txMsg, gamma.ha)
        rxMsg, sa = gamma.receive()
        assert txMsg == rxMsg
        assert sa == alpha.ha

        txMsg = b"Alpha sends to Alpha"
        alpha.send(txMsg, alpha.ha)
        rxMsg, sa = alpha.receive()
        assert txMsg == rxMsg
        assert sa == alpha.ha

        txMsg = b"Beta sends to Alpha"
        beta.send(txMsg, alpha.ha)
        rxMsg, sa = alpha.receive()
        assert txMsg == rxMsg
        assert sa == beta.ha

        txMsg = b"Beta sends to Gamma"
        beta.send(txMsg, gamma.ha)
        rxMsg, sa = gamma.receive()
        assert txMsg == rxMsg
        assert sa == beta.ha

        txMsg = b"Beta sends to Beta"
        beta.send(txMsg, beta.ha)
        rxMsg, sa = beta.receive()
        assert txMsg == rxMsg
        assert sa == beta.ha

        txMsg = b"Gamma sends to Alpha"
        gamma.send(txMsg, alpha.ha)
        rxMsg, sa = alpha.receive()
        assert txMsg == rxMsg
        assert sa == gamma.ha

        txMsg = b"Gamma sends to Beta"
        gamma.send(txMsg, beta.ha)
        rxMsg, sa = beta.receive()
        assert txMsg == rxMsg
        assert sa == gamma.ha

        txMsg = b"Gamma sends to Gamma"
        gamma.send(txMsg, gamma.ha)
        rxMsg, sa = gamma.receive()
        assert txMsg == rxMsg
        assert sa == gamma.ha


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
            txer.send(txMsg, rxer.ha)
            rxMsg, sa = rxer.receive()
            assert txMsg == rxMsg
            assert sa == txer.ha

        rxMsg, sa = alpha.receive()
        assert b'' == rxMsg
        assert None == sa

        rxMsg, sa = beta.receive()
        assert b'' == rxMsg
        assert None == sa

        rxMsg, sa = gamma.receive()
        assert b'' == rxMsg
        assert None == sa

        wl.flush()  #  just to test
        assert wl.samed  # rx and tx same buffer

        assert wl.readRx()
        assert wl.readTx()
        assert wl.readTx() == wl.readRx()

    assert not alpha.opened
    assert not beta.opened
    assert not gamma.opened

    assert not wl.opened

    shutil.rmtree(testDirpath)  # and all dependent paths

    assert not os.path.exists(testDirpath)
    assert not os.path.exists(tempDirpath)
    assert not os.path.exists(sockDirpath)

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

    testDirpath = os.path.join('~', '.hio', 'test')
    testDirpath = os.path.abspath(os.path.expanduser(testDirpath))
    if not os.path.exists(testDirpath):
        os.makedirs(testDirpath)
    tempDirpath = tempfile.mkdtemp(prefix="test", suffix="uxd", dir=testDirpath)
    sockDirpath = os.path.join(tempDirpath, 'uxd')
    if not os.path.exists(sockDirpath):
        os.makedirs(sockDirpath)
    aha = os.path.join(sockDirpath, 'alpha.uxd')

    peer = uxding.Peer(ha=aha, umask=0o077)
    doer = uxding.PeerDoer(peer=peer)

    doers = [doer]
    doist.do(doers=doers)
    assert doist.tyme == limit
    assert peer.opened == False

    shutil.rmtree(testDirpath)  # and all dependent paths
    assert not os.path.exists(testDirpath)
    assert not os.path.exists(tempDirpath)
    assert not os.path.exists(sockDirpath)




if __name__ == "__main__":
    test_uxd_basic()
    test_open_peer()
    test_peer_doer()
