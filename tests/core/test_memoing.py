# -*- encoding: utf-8 -*-
"""
tests.core.test_memoing module

"""


import pytest

from hio.base import doing
from hio.core import memoing


def test_memogram_basic():
    """Test MemoGram class basic
    """
    peer = memoing.MemoGram()
    assert peer.name == "main"
    assert peer.opened == False
    peer.reopen()
    assert peer.opened == True

    assert not peer.txms
    assert not peer.txgs
    gram, dst = peer.txbs
    assert not dst
    peer.service()
    gram, dst = peer.txbs
    assert not dst

    memo = "Hello There"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms
    peer.serviceTxMemos()
    assert not peer.txms
    assert peer.txgs
    peer.serviceTxGrams()
    assert not peer.txgs

    assert not peer.rxgs
    assert not peer.rxms
    echo = (b"Bye yall", "beta")
    peer.serviceReceives(echo=echo)
    assert peer.rxgs
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert peer.rxms
    peer.serviceRxMemos()
    assert not peer.rxms


    peer.close()
    assert peer.opened == False



    """ End Test """


def test_open_mg():
    """Test contextmanager decorator openMG
    """
    with (memoing.openMG(name='zeta') as zeta):

        assert zeta.opened
        assert zeta.name == 'zeta'


    assert not zeta.opened

    """ End Test """


def test_memogram_doer():
    """Test MemoGramDoer class
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

    peer = memoing.MemoGram()

    mgdoer = memoing.MemoGramDoer(peer=peer)
    assert mgdoer.peer == peer
    assert not mgdoer.peer.opened
    assert mgdoer.tock == 0.0  # ASAP

    doers = [mgdoer]
    doist.do(doers=doers)
    assert doist.tyme == limit
    assert mgdoer.peer.opened == False

    """End Test """


if __name__ == "__main__":
    test_memogram_basic()
    test_open_mg()
    test_memogram_doer()

