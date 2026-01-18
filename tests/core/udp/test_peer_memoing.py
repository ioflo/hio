# -*- encoding: utf-8 -*-
"""
tests.core.test_peer_memoer module

"""
import os
import platform
import time

import pytest

from hio.help import helping
from hio.base import doing, tyming
from hio.core.memo import GramDex
from hio.core.udp import udping, peermemoing


def test_memoer_peer_basic():
    """Test MemoerPeer class"""

    alphaPort = 6103
    betaPort = 6104

    alpha = peermemoing.PeerMemoer(name="alpha", temp=True)
    assert alpha.name == "alpha"
    assert alpha.code == GramDex.Basic
    assert not alpha.curt
    assert alpha.Sizes[alpha.code] == (2, 22, 0, 4, 0, 28)  # cz mz oz nz sz hz
    assert alpha.size == 1240  # default MaxGramSize for udp
    assert alpha.bc == 1024
    assert not alpha.opened
    assert alpha.ha == ('127.0.0.1', 55000)
    assert alpha.path == alpha.ha


    size = 38  # force gram size to be smaller than default so forces segmentation
    alpha = peermemoing.PeerMemoer(name="alpha", temp=True, size=size, port=alphaPort)
    assert alpha.name == "alpha"
    assert alpha.code == GramDex.Basic
    assert not alpha.curt
    assert alpha.Sizes[alpha.code] == (2, 22, 0, 4, 0, 28)  # cz mz oz nz sz hz
    assert alpha.size == size
    assert alpha.bc == 1024
    assert not alpha.opened
    assert alpha.reopen()
    assert alpha.opened
    assert alpha.ha == ('127.0.0.1', alphaPort)
    assert alpha.path == alpha.ha
    #assert alpha.actualBufSizes() == (1269760, 1269760) == (alpha.bc * alpha.MaxGramSize, alpha.bc * alpha.MaxGramSize)

    beta = peermemoing.PeerMemoer(name="beta", temp=True, size=size, port=betaPort)
    assert beta.reopen()
    assert beta.opened
    assert beta.ha == ('127.0.0.1', betaPort)
    assert beta.path == beta.ha
    #assert beta.actualBufSizes() == (1269760, 1269760) == (beta.bc * beta.MaxGramSize, beta.bc * beta.MaxGramSize)

    # alpha sends
    alpha.memoit("Hello there.", beta.ha)
    alpha.memoit("How ya doing?", beta.path)
    assert len(alpha.txms) == 2
    alpha.serviceTxMemos()
    assert not alpha.txms
    assert len(alpha.txgs) == 4
    for m, d in alpha.txgs:
        assert not alpha.wiff(m)  # base64
        assert d == beta.path
    alpha.serviceTxGrams()
    assert not alpha.txgs
    assert alpha.txbs == (b'', None)
    assert not alpha.rxgs
    assert not alpha.rxms
    assert not alpha.counts
    assert not alpha.sources

    # beta receives
    beta.serviceReceives()
    time.sleep(0.05)
    assert not beta.echos
    assert len(beta.rxgs) == 2
    assert len(beta.counts) == 2
    assert len(beta.sources) == 2

    mid = list(beta.rxgs.keys())[0]
    assert beta.sources[mid] == alpha.path
    assert beta.counts[mid] == 2
    assert len(beta.rxgs[mid]) == 2
    assert beta.rxgs[mid][0] == bytearray(b'Hello ')
    assert beta.rxgs[mid][1] == bytearray(b'there.')

    mid = list(beta.rxgs.keys())[1]
    assert beta.sources[mid] == alpha.path
    assert beta.counts[mid] == 2
    assert len(beta.rxgs[mid]) == 2
    assert beta.rxgs[mid][0] == bytearray(b'How ya')
    assert beta.rxgs[mid][1] == bytearray(b' doing?')

    beta.serviceRxGrams()
    assert not beta.rxgs
    assert not beta.counts
    assert not beta.sources
    assert len(beta.rxms) == 2
    assert beta.rxms[0] == ('Hello there.', alpha.path, None)
    assert beta.rxms[1] == ('How ya doing?', alpha.path, None)
    beta.serviceRxMemos()
    assert not beta.rxms

    # beta sends
    beta.memoit("Well is not this a fine day?", alpha.path)
    beta.memoit("Do you want to do lunch?", alpha.path)
    assert len(beta.txms) == 2
    beta.serviceTxMemos()
    assert not beta.txms
    beta.serviceTxGrams()
    assert not beta.txgs
    assert beta.txbs == (b'', None)
    assert not beta.rxgs
    assert not beta.rxms
    assert not beta.counts
    assert not beta.sources

    # alpha receives
    alpha.serviceReceives()
    time.sleep(0.05)
    assert not alpha.echos
    assert len(alpha.rxgs) == 2
    assert len(alpha.counts) == 2
    assert len(alpha.sources) == 2

    mid = list(alpha.rxgs.keys())[0]
    assert alpha.sources[mid] == beta.path
    assert alpha.counts[mid] == 4
    assert len(alpha.rxgs[mid]) == 4

    mid = list(alpha.rxgs.keys())[1]
    assert alpha.sources[mid] == beta.path
    assert alpha.counts[mid] == 3
    assert len(alpha.rxgs[mid]) == 3

    alpha.serviceRxGrams()
    assert not alpha.rxgs
    assert not alpha.counts
    assert not alpha.sources
    assert len(alpha.rxms) == 2
    assert alpha.rxms[0] == ('Well is not this a fine day?', beta.path, None)
    assert alpha.rxms[1] == ('Do you want to do lunch?', beta.path, None)
    alpha.serviceRxMemos()
    assert not alpha.rxms

    assert beta.close()
    assert not beta.opened

    assert alpha.close()
    assert not alpha.opened

    """Done Test"""


def test_memoer_peer_open():
    """Test MemoerPeer class with context manager openPM"""

    host = '127.0.0.1'  # default
    alphaPort = 6103
    betaPort = 6104
    size = 38

    with (peermemoing.openPM(name='alpha', size=size, port=alphaPort) as alpha,
          peermemoing.openPM(name='beta', size=size, port=betaPort) as beta):


        assert alpha.name == "alpha"
        assert alpha.code == GramDex.Basic
        assert not alpha.curt
        # (code, mid, vid, sig, neck, head) part sizes
        assert alpha.Sizes[alpha.code] == (2, 22, 0, 4, 0, 28)  # cz mz oz nz sz hz
        assert alpha.size == size
        assert alpha.bc == 1024

        assert alpha.opened
        assert alpha.ha == alpha.path == (host, alphaPort)

        assert beta.bc == 1024
        assert beta.opened
        assert beta.ha == beta.path == (host, betaPort)

        # alpha sends
        alpha.memoit("Hello there.", beta.path)
        alpha.memoit("How ya doing?", beta.path)
        assert len(alpha.txms) == 2
        alpha.serviceTxMemos()
        assert not alpha.txms
        assert len(alpha.txgs) == 4
        for m, d in alpha.txgs:
            assert not alpha.wiff(m)  # base64
            assert d == beta.path
        alpha.serviceTxGrams()
        assert not alpha.txgs
        assert alpha.txbs == (b'', None)
        assert not alpha.rxgs
        assert not alpha.rxms
        assert not alpha.counts
        assert not alpha.sources

        # beta receives
        beta.serviceReceives()
        while not beta.rxgs:
            time.sleep(0.05)
        assert not beta.echos
        assert len(beta.rxgs) == 2
        assert len(beta.counts) == 2
        assert len(beta.sources) == 2

        mid = list(beta.rxgs.keys())[0]
        assert beta.sources[mid] == alpha.path
        assert beta.counts[mid] == 2
        assert len(beta.rxgs[mid]) == 2
        assert beta.rxgs[mid][0] == bytearray(b'Hello ')
        assert beta.rxgs[mid][1] == bytearray(b'there.')

        mid = list(beta.rxgs.keys())[1]
        assert beta.sources[mid] == alpha.path
        assert beta.counts[mid] == 2
        assert len(beta.rxgs[mid]) == 2
        assert beta.rxgs[mid][0] == bytearray(b'How ya')
        assert beta.rxgs[mid][1] == bytearray(b' doing?')

        beta.serviceRxGrams()
        assert not beta.rxgs
        assert not beta.counts
        assert not beta.sources
        assert len(beta.rxms) == 2
        assert beta.rxms[0] == ('Hello there.', alpha.path, None)
        assert beta.rxms[1] == ('How ya doing?', alpha.path, None)
        beta.serviceRxMemos()
        assert not beta.rxms

        # beta sends
        beta.memoit("Well is not this a fine day?", alpha.path)
        beta.memoit("Do you want to do lunch?", alpha.path)
        assert len(beta.txms) == 2
        beta.serviceTxMemos()
        assert not beta.txms
        beta.serviceTxGrams()
        assert not beta.txgs
        assert beta.txbs == (b'', None)
        assert not beta.rxgs
        assert not beta.rxms
        assert not beta.counts
        assert not beta.sources

        # alpha receives
        alpha.serviceReceives()
        time.sleep(0.05)
        assert not alpha.echos
        assert len(alpha.rxgs) == 2
        assert len(alpha.counts) == 2
        assert len(alpha.sources) == 2

        mid = list(alpha.rxgs.keys())[0]
        assert alpha.sources[mid] == beta.path
        assert alpha.counts[mid] == 4
        assert len(alpha.rxgs[mid]) == 4

        mid = list(alpha.rxgs.keys())[1]
        assert alpha.sources[mid] == beta.path
        assert alpha.counts[mid] == 3
        assert len(alpha.rxgs[mid]) == 3

        alpha.serviceRxGrams()
        assert not alpha.rxgs
        assert not alpha.counts
        assert not alpha.sources
        assert len(alpha.rxms) == 2
        assert alpha.rxms[0] == ('Well is not this a fine day?', beta.path, None)
        assert alpha.rxms[1] == ('Do you want to do lunch?', beta.path, None)
        alpha.serviceRxMemos()
        assert not alpha.rxms

    assert not beta.opened
    assert not alpha.opened

    """Done Test"""



def test_peermemoer_doer():
    """Test PeerMemoerDoer class
    """

    tock = 0.03125
    ticks = 4
    limit = ticks *  tock
    doist = doing.Doist(tock=tock, real=True, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == limit == 0.125
    assert doist.doers == []

    peer = peermemoing.PeerMemoer(name="test", temp=True, reopen=False)
    assert peer.opened == False
    assert peer.ha == peer.path == ('127.0.0.1', 55000)

    doer = peermemoing.PeerMemoerDoer(peer=peer)
    assert doer.peer == peer
    assert not doer.peer.opened
    assert doer.tock == 0.0  # ASAP

    doers = [doer]
    doist.do(doers=doers)
    assert doist.tyme == limit
    assert peer.opened == False
    """Done Test"""


if __name__ == "__main__":
    test_memoer_peer_basic()
    test_memoer_peer_open()
    test_peermemoer_doer()


