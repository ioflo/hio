# -*- encoding: utf-8 -*-
"""
tests.core.test_memoing module

"""
from base64 import urlsafe_b64encode as encodeB64
from base64 import urlsafe_b64decode as decodeB64

import pytest

from hio.base import doing, tyming
from hio.core import memoing


def test_memoer_basic():
    """Test Memoer class basic
    """
    peer = memoing.Memoer()
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.code == '__' == peer.Code
    assert peer.Sizes[peer.code] == (2, 22, 4, 28)  # (code, mid, neck, head) size
    assert peer.size == peer.MaxPartSize


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
    m, d = peer.txgs[0]
    assert peer.wiff(m) == memoing.Wiffs.txt
    assert m.endswith(memo.encode())
    assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = 'ALBI68S1ZIxqwFOSWFF1L2'
    gram = ('__' + mid + 'AAAA' + 'AAAB' + "Hello There").encode()
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert peer.rxgs[mid][0] == bytearray(b'Hello There')
    assert peer.counts[mid] == 1
    assert peer.sources[mid] == 'beta'
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert peer.rxms[0] == ('Hello There', 'beta')
    peer.serviceRxMemos()
    assert not peer.rxms

    # send and receive via echo
    memo = "See ya later!"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('See ya later!', 'beta')
    peer.serviceTxMemos()
    assert not peer.txms
    m, d = peer.txgs[0]
    assert peer.wiff(m) == memoing.Wiffs.txt
    assert m.endswith(memo.encode())
    assert d == dst == 'beta'
    peer.serviceTxGrams(echoic=True)
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert peer.echos

    assert not peer.rxgs
    assert not peer.rxms
    assert not peer.counts
    assert not peer.sources
    peer.serviceReceives(echoic=True)
    mid = list(peer.rxgs.keys())[0]
    assert peer.rxgs[mid][0] == b'See ya later!'
    assert peer.counts[mid] == 1
    assert peer.sources[mid] == 'beta'
    assert not peer.echos
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    peer.rxms[0]
    assert peer.rxms[0] == ('See ya later!', 'beta')
    peer.serviceRxMemos()
    assert not peer.rxms

    # test binary q2 encoding of transmission part header
    peer.mode = memoing.Wiffs.bny
    memo = "Hello There"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('Hello There', 'beta')
    peer.serviceTxMemos()
    assert not peer.txms
    m, d = peer.txgs[0]
    assert peer.wiff(m) == memoing.Wiffs.bny
    assert m.endswith(memo.encode())
    assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = 'ALBI68S1ZIxqwFOSWFF1L2'
    headneck = decodeB64(('__' + mid + 'AAAA' + 'AAAB').encode())
    gram = headneck + b"Hello There"
    assert peer.wiff(gram) == memoing.Wiffs.bny
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert peer.rxgs[mid][0] == bytearray(b'Hello There')
    assert peer.counts[mid] == 1
    assert peer.sources[mid] == 'beta'
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert peer.rxms[0] == ('Hello There', 'beta')
    peer.serviceRxMemos()
    assert not peer.rxms

    peer.close()
    assert peer.opened == False
    """ End Test """


def test_memogram_small_part_size():
    """Test MemoGram class with small part size
    """
    peer = memoing.Memoer(size=6)
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.code == '__' == peer.Code
    assert peer.Sizes[peer.code] == (2, 22, 4, 28)  # (code, mid, neck, head) size
    assert peer.size == 33  # can't be smaller than head + neck + 1

    peer = memoing.Memoer(size=38)
    assert peer.size == 38
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
    assert len(peer.txgs) == 2
    for m, d in peer.txgs:
        assert peer.wiff(m) == memoing.Wiffs.txt
        assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    b'__DFymLrtlZG6bp0HhlUsR6uAAAAAAACHello '
    b'__DFymLrtlZG6bp0HhlUsR6uAAABThere'
    mid = 'DFymLrtlZG6bp0HhlUsR6u'
    gram = ('__' + mid + 'AAAA' + 'AAAC' + "Hello ").encode()
    echo = (gram, "beta")
    peer.echos.append(echo)
    gram = ('__' + mid + 'AAAB' + "There").encode()
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert len(peer.rxgs[mid]) == 2
    assert peer.counts[mid] == 2
    assert peer.sources[mid] == 'beta'
    assert peer.rxgs[mid][0] == bytearray(b'Hello ')
    assert peer.rxgs[mid][1] == bytearray(b'There')
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert peer.rxms[0] == ('Hello There', 'beta')
    peer.serviceRxMemos()
    assert not peer.rxms

    # send and receive via echo
    memo = "See ya later!"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('See ya later!', 'beta')
    peer.serviceTxMemos()
    assert not peer.txms
    assert len(peer.txgs) == 2
    for m, d in peer.txgs:
        assert peer.wiff(m) == memoing.Wiffs.txt
        assert d == dst == 'beta'
    peer.serviceTxGrams(echoic=True)
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert peer.echos

    assert not peer.rxgs
    assert not peer.rxms
    assert not peer.counts
    assert not peer.sources
    peer.serviceReceives(echoic=True)
    mid = list(peer.rxgs.keys())[0]
    assert len(peer.rxgs[mid]) == 2
    assert peer.counts[mid] == 2
    assert peer.sources[mid] == 'beta'
    assert peer.rxgs[mid][0] == bytearray(b'See ya')
    assert peer.rxgs[mid][1] == bytearray(b' later!')
    assert not peer.echos
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    peer.rxms[0]
    assert peer.rxms[0] == ('See ya later!', 'beta')
    peer.serviceRxMemos()
    assert not peer.rxms

    # test binary q2 encoding of transmission part header
    peer.mode = memoing.Wiffs.bny
    memo = "Hello There"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('Hello There', 'beta')
    peer.serviceTxMemos()
    assert not peer.txms
    assert len(peer.txgs) == 2
    for m, d in peer.txgs:
        assert peer.wiff(m) == memoing.Wiffs.bny
        assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms

    headneck = decodeB64(('__' + mid + 'AAAA' + 'AAAB').encode())
    gram = headneck + b"Hello There"
    assert peer.wiff(gram) == memoing.Wiffs.bny
    echo = (gram, "beta")
    peer.echos.append(echo)

    b'__DFymLrtlZG6bp0HhlUsR6uAAAAAAACHello '
    b'__DFymLrtlZG6bp0HhlUsR6uAAABThere'
    mid = 'DFymLrtlZG6bp0HhlUsR6u'
    headneck = decodeB64(('__' + mid + 'AAAA' + 'AAAC').encode())
    gram = headneck + b"Hello "
    assert peer.wiff(gram) == memoing.Wiffs.bny
    echo = (gram, "beta")
    peer.echos.append(echo)
    head = decodeB64(('__' + mid + 'AAAB').encode())
    gram = head + b"There"
    assert peer.wiff(gram) == memoing.Wiffs.bny
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert len(peer.rxgs[mid]) == 2
    assert peer.counts[mid] == 2
    assert peer.sources[mid] == 'beta'
    assert peer.rxgs[mid][0] == bytearray(b'Hello ')
    assert peer.rxgs[mid][1] == bytearray(b'There')
    peer.serviceReceives(echoic=True)
    assert len(peer.rxgs[mid]) == 2
    assert peer.counts[mid] == 2
    assert peer.sources[mid] == 'beta'
    assert peer.rxgs[mid][0] == bytearray(b'Hello ')
    assert peer.rxgs[mid][1] == bytearray(b'There')
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert peer.rxms[0] == ('Hello There', 'beta')
    peer.serviceRxMemos()
    assert not peer.rxms

    peer.close()
    assert peer.opened == False
    """ End Test """


def test_memoer_multiple():
    """Test Memoer class with small part size and multiple queued memos
    """
    peer = memoing.Memoer(size=38)
    assert peer.size == 38
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.code == '__' == peer.Code
    assert peer.Sizes[peer.code] == (2, 22, 4, 28)  # (code, mid, neck, head) size
    peer.reopen()
    assert peer.opened == True

    # send and receive multiple via echo
    peer.memoit("Hello there.", "alpha")
    peer.memoit("How ya doing?", "beta")
    assert len(peer.txms) == 2
    peer.serviceTxMemos()
    assert not peer.txms
    assert len(peer.txgs) == 4
    for m, d in peer.txgs:
        assert peer.wiff(m) == memoing.Wiffs.txt
        assert d in ("alpha", "beta")
    peer.serviceTxGrams(echoic=True)
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert len(peer.echos) == 4
    assert not peer.rxgs
    assert not peer.rxms
    assert not peer.counts
    assert not peer.sources

    peer.serviceReceives(echoic=True)
    assert not peer.echos
    assert len(peer.rxgs) == 2
    assert len(peer.counts) == 2
    assert len(peer.sources) == 2

    mid = list(peer.rxgs.keys())[0]
    assert peer.sources[mid] == 'alpha'
    assert peer.counts[mid] == 2
    assert len(peer.rxgs[mid]) == 2
    assert peer.rxgs[mid][0] == bytearray(b'Hello ')
    assert peer.rxgs[mid][1] == bytearray(b'there.')

    mid = list(peer.rxgs.keys())[1]
    assert peer.sources[mid] == 'beta'
    assert peer.counts[mid] == 2
    assert len(peer.rxgs[mid]) == 2
    assert peer.rxgs[mid][0] == bytearray(b'How ya')
    assert peer.rxgs[mid][1] == bytearray(b' doing?')

    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert len(peer.rxms) == 2
    assert peer.rxms[0] == ('Hello there.', 'alpha')
    assert peer.rxms[1] == ('How ya doing?', 'beta')
    peer.serviceRxMemos()
    assert not peer.rxms


    peer.close()
    assert peer.opened == False
    """ End Test """




def test_open_mg():
    """Test contextmanager decorator openMG
    """
    with (memoing.openMemoer(name='zeta') as zeta):

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

    peer = memoing.Memoer()

    mgdoer = memoing.MemoerDoer(peer=peer)
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
    peer = memoing.TymeeMemoer()
    assert peer.tymeout == 0.0
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.code == '__' == peer.Code
    assert peer.Sizes[peer.code] == (2, 22, 4, 28)  # (code, mid, neck, head) size
    assert peer.size == peer.MaxPartSize

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
    m, d = peer.txgs[0]
    assert peer.wiff(m) == memoing.Wiffs.txt
    assert m.endswith(memo.encode())
    assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = 'ALBI68S1ZIxqwFOSWFF1L2'
    gram = ('__' + mid + 'AAAA' + 'AAAB' + "Hello There").encode()
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert peer.rxgs[mid][0] == bytearray(b'Hello There')
    assert peer.counts[mid] == 1
    assert peer.sources[mid] == 'beta'
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert peer.rxms[0] == ('Hello There', 'beta')
    peer.serviceRxMemos()
    assert not peer.rxms

    # send and receive via echo
    memo = "See ya later!"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('See ya later!', 'beta')
    peer.serviceTxMemos()
    assert not peer.txms
    m, d = peer.txgs[0]
    assert peer.wiff(m) == memoing.Wiffs.txt
    assert m.endswith(memo.encode())
    assert d == dst == 'beta'
    peer.serviceTxGrams(echoic=True)
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert peer.echos

    assert not peer.rxgs
    assert not peer.rxms
    assert not peer.counts
    assert not peer.sources
    peer.serviceReceives(echoic=True)
    mid = list(peer.rxgs.keys())[0]
    assert peer.rxgs[mid][0] == b'See ya later!'
    assert peer.counts[mid] == 1
    assert peer.sources[mid] == 'beta'
    assert not peer.echos
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    peer.rxms[0]
    assert peer.rxms[0] == ('See ya later!', 'beta')
    peer.serviceRxMemos()
    assert not peer.rxms

    # test binary q2 encoding of transmission part header
    peer.mode = memoing.Wiffs.bny
    memo = "Hello There"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('Hello There', 'beta')
    peer.serviceTxMemos()
    assert not peer.txms
    m, d = peer.txgs[0]
    assert peer.wiff(m) == memoing.Wiffs.bny
    assert m.endswith(memo.encode())
    assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = 'ALBI68S1ZIxqwFOSWFF1L2'
    headneck = decodeB64(('__' + mid + 'AAAA' + 'AAAB').encode())
    gram = headneck + b"Hello There"
    assert peer.wiff(gram) == memoing.Wiffs.bny
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert peer.rxgs[mid][0] == bytearray(b'Hello There')
    assert peer.counts[mid] == 1
    assert peer.sources[mid] == 'beta'
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert peer.rxms[0] == ('Hello There', 'beta')
    peer.serviceRxMemos()
    assert not peer.rxms

    # Test wind
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
    with (memoing.openTM(name='zeta') as zeta):

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

    peer = memoing.TymeeMemoer()

    tmgdoer = memoing.TymeeMemoerDoer(peer=peer)
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
    test_memoer_basic()
    test_memogram_small_part_size()
    test_memoer_multiple()
    test_open_mg()
    test_memogram_doer()
    test_tymeememogram_basic()
    test_open_tmg()
    test_tymeememogram_doer()

