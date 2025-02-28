# -*- encoding: utf-8 -*-
"""
tests.core.test_peer_memoer module

"""
import os
import platform

import pytest

from hio.help import helping
from hio.base import doing, tyming
from hio.core.memo import GramDex
from hio.core.uxd import uxding, peermemoing




def test_memoer_peer_basic():
    """Test MemoerPeer class"""
    if platform.system() == "Windows":
        return
    alpha = peermemoing.PeerMemoer(name="alpha", temp=True, size=38)
    assert alpha.name == "alpha"
    assert alpha.code == GramDex.Basic
    assert not alpha.curt
    # (code, mid, vid, sig, neck, head) part sizes
    assert alpha.Sizes[alpha.code] == (2, 22, 0, 0, 4, 28)  # cs ms vs ss ns hs
    assert alpha.size == 38

    assert alpha.bc == 4
    assert not alpha.opened
    assert alpha.reopen()
    assert alpha.opened
    assert alpha.path.endswith("alpha.uxd")
    #assert alpha.actualBufSizes() == (4194240, 4194240) == (alpha.bc * alpha.MaxGramSize,
    #                                                        alpha.bc * alpha.MaxGramSize)

    beta = peermemoing.PeerMemoer(name="beta", temp=True, size=38)
    assert beta.reopen()
    assert beta.path.endswith("beta.uxd")

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
    assert not os.path.exists(beta.path)

    assert alpha.close()
    assert not alpha.opened
    assert not os.path.exists(alpha.path)


    """Done Test"""


def test_memoer_peer_open():
    """Test MemoerPeer class with context manager openPM"""
    if platform.system() == "Windows":
        return
    with (peermemoing.openPM(name='alpha', size=38) as alpha,
          peermemoing.openPM(name='beta', size=38) as beta):


        assert alpha.name == "alpha"
        assert alpha.code == GramDex.Basic
        assert not alpha.curt
        # (code, mid, vid, sig, neck, head) part sizes
        assert alpha.Sizes[alpha.code] == (2, 22, 0, 0, 4, 28)  # cs ms vs ss ns hs
        assert alpha.size == 38
        assert alpha.bc == 4

        assert alpha.opened
        assert alpha.path.endswith("alpha.uxd")

        assert beta.bc == 4
        assert beta.opened
        assert beta.path.endswith("beta.uxd")

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
    assert not os.path.exists(beta.path)

    assert alpha.close()
    assert not alpha.opened
    assert not os.path.exists(alpha.path)


    """Done Test"""



def test_peermemoer_doer():
    """Test PeerMemoerDoer class
    """
    if platform.system() == "Windows":
        return
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
    assert peer.path == None
    assert peer.filed == False
    assert peer.extensioned == True

    doer = peermemoing.PeerMemoerDoer(peer=peer)
    assert doer.peer == peer
    assert not doer.peer.opened
    assert doer.tock == 0.0  # ASAP

    doers = [doer]
    doist.do(doers=doers)
    assert doist.tyme == limit
    assert peer.opened == False
    assert not os.path.exists(peer.path)
    """Done Test"""


if __name__ == "__main__":
    test_memoer_peer_basic()
    test_memoer_peer_open()
    test_peermemoer_doer()

