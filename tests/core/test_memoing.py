# -*- encoding: utf-8 -*-
"""
tests.core.test_memoing module

"""


import pytest

from hio.base import doing, tyming
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
    assert peer.txbs == (b'', None)
    peer.service()
    assert peer.txbs == (b'', None)

    memo = "Hello There"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('Hello There', 'beta')
    peer.serviceTxMemos()
    assert not peer.txms
    assert peer.txgs[0] == (b'Hello There', 'beta')
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.rxms
    echo = (b"Bye yall", "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert peer.rxgs["beta"][0] == b"Bye yall"
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert peer.rxms[0] == ('Bye yall', 'beta')
    peer.serviceRxMemos()
    assert not peer.rxms

    memo = "See ya later!"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('See ya later!', 'beta')
    peer.serviceTxMemos()
    assert not peer.txms
    assert peer.txgs[0] == (b'See ya later!', 'beta')
    peer.serviceTxGrams(echoic=True)
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert peer.echos

    assert not peer.rxgs
    assert not peer.rxms
    peer.serviceReceives(echoic=True)
    assert peer.rxgs["beta"][0] == b"See ya later!"
    assert not peer.echos
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert peer.rxms[0] == ('See ya later!', 'beta')
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

def test_tymeememogram_basic():
    """Test TymeeMemoGram class basic
    """
    peer = memoing.TymeeMemoGram()
    assert peer.tymeout == 0.0
    assert peer.name == "main"
    assert peer.opened == False
    peer.reopen()
    assert peer.opened == True

    assert not peer.txms
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    peer.service()
    assert peer.txbs == (b'', None)

    memo = "Hello There"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('Hello There', 'beta')
    peer.serviceTxMemos()
    assert not peer.txms
    assert peer.txgs[0] == (b'Hello There', 'beta')
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.rxms
    echo = (b"Bye yall", "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert peer.rxgs["beta"][0] == b"Bye yall"
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert peer.rxms[0] == ('Bye yall', 'beta')
    peer.serviceRxMemos()
    assert not peer.rxms

    memo = "See ya later!"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('See ya later!', 'beta')
    peer.serviceTxMemos()
    assert not peer.txms
    assert peer.txgs[0] == (b'See ya later!', 'beta')
    peer.serviceTxGrams(echoic=True)
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert peer.echos

    assert not peer.rxgs
    assert not peer.rxms
    peer.serviceReceives(echoic=True)
    assert peer.rxgs["beta"][0] == b"See ya later!"
    assert not peer.echos
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert peer.rxms[0] == ('See ya later!', 'beta')
    peer.serviceRxMemos()
    assert not peer.rxms

    tymist = tyming.Tymist(tock=1.0)
    peer.wind(tymth=tymist.tymen())
    assert peer.tyme == tymist.tyme == 0.0
    tymist.tick()
    assert peer.tyme == tymist.tyme == 1.0



    peer.close()
    assert peer.opened == False
    """ End Test """


def test_open_tmg():
    """Test contextmanager decorator openTMG
    """
    with (memoing.openTMG(name='zeta') as zeta):

        assert zeta.opened
        assert zeta.name == 'zeta'
        assert zeta.tymeout == 0.0


    assert not zeta.opened

    """ End Test """


def test_tymeememogram_doer():
    """Test TymeeMemoGramDoer class
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

    peer = memoing.TymeeMemoGram()

    tmgdoer = memoing.TymeeMemoGramDoer(peer=peer)
    assert tmgdoer.peer == peer
    assert not tmgdoer.peer.opened
    assert tmgdoer.tock == 0.0  # ASAP

    doers = [tmgdoer]
    doist.do(doers=doers)
    assert doist.tyme == limit
    assert tmgdoer.peer.opened == False

    tymist = tyming.Tymist(tock=1.0)
    tmgdoer.wind(tymth=tymist.tymen())
    assert tmgdoer.tyme == tymist.tyme == 0.0
    assert peer.tyme == tymist.tyme == 0.0
    tymist.tick()
    assert tmgdoer.tyme == tymist.tyme == 1.0
    assert peer.tyme == tymist.tyme == 1.0

    """End Test """



if __name__ == "__main__":
    test_memogram_basic()
    test_open_mg()
    test_memogram_doer()
    test_tymeememogram_basic()
    test_open_tmg()
    test_tymeememogram_doer()

