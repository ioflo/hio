# -*- encoding: utf-8 -*-
"""
tests.core.test_memoing module

"""
from collections import deque
from base64 import urlsafe_b64encode as encodeB64
from base64 import urlsafe_b64decode as decodeB64

import pytest

from hio.hioing import MemoerError
from hio.help import helping
from hio.base import doing, tyming
from hio.core.memo import memoing
from hio.core.memo import Versionage, Sizage, GramDex, SGDex, Memoer, Keyage


def _setupKeep(salt=None):
    """Setup Keep for signed memos

    Parameters:
        salt(str|bytes): salt used to generate key pairs and vids for keep

    Returns:
        keep (dict): labels are vids, values are keyage instances


    Ed25519_Seed: str = 'A'  # Ed25519 256 bit random seed for private key
    """
    try:
        import pysodium
        import blake3
    except ImportError:
        raise MemoerError("Missing cryptographic module support")


    salt = salt if salt is not None else b"abcdefghijklmnop"
    if hasattr(salt, 'encode'):
        salt = salt.encode()

    if len(salt) != 16:
        raise MemoerError("Invalid provided salt")

    keep = {}

    sigseed = pysodium.crypto_pwhash(outlen=32,
                                    passwd="0",
                                    salt=salt,
                                    opslimit=2,  # pysodium.crypto_pwhash_OPSLIMIT_INTERACTIVE,
                                    memlimit=67108864,  # pysodium.crypto_pwhash_MEMLIMIT_INTERACTIVE,
                                    alg=pysodium.crypto_pwhash_ALG_ARGON2ID13)
    # creates signing/verification key pair from seed
    verkey, sigkey = pysodium.crypto_sign_seed_keypair(sigseed)  # raw

    vid = Memoer._encodeVid(vid=verkey, code='B')
    assert len(vid) == 44

    keyage = Keyage(verkey=verkey, sigseed=sigseed)  # raw
    keep[vid] = keyage

    sigseed = pysodium.crypto_pwhash(outlen=32,
                                    passwd="1",
                                    salt=salt,
                                    opslimit=2,  # pysodium.crypto_pwhash_OPSLIMIT_INTERACTIVE,
                                    memlimit=67108864,  # pysodium.crypto_pwhash_MEMLIMIT_INTERACTIVE,
                                    alg=pysodium.crypto_pwhash_ALG_ARGON2ID13)
    # creates signing/verification key pair from seed
    verkey, sigkey = pysodium.crypto_sign_seed_keypair(sigseed)  # raw

    vid = Memoer._encodeVid(vid=verkey, code='D')
    assert len(vid) == 44

    keyage = Keyage(verkey=verkey, sigseed=sigseed)  # raw
    keep[vid] = keyage

    sigseed = pysodium.crypto_pwhash(outlen=32,
                                    passwd="2",
                                    salt=salt,
                                    opslimit=2,  # pysodium.crypto_pwhash_OPSLIMIT_INTERACTIVE,
                                    memlimit=67108864,  # pysodium.crypto_pwhash_MEMLIMIT_INTERACTIVE,
                                    alg=pysodium.crypto_pwhash_ALG_ARGON2ID13)
    # creates signing/verification key pair from seed
    verkey, sigkey = pysodium.crypto_sign_seed_keypair(sigseed)  # raw

    dig = digest = blake3.blake3(verkey).digest()

    vid = Memoer._encodeVid(vid=dig, code='E')
    assert len(vid) == 44

    keyage = Keyage(verkey=verkey, sigseed=sigseed)  # raw
    keep[vid] = keyage

    return keep


def test_memoer_class():
    """Test class attributes of Memoer class"""

    assert Memoer.Version == Versionage(major=0, minor=0)
    assert Memoer.Codex == memoing.GramDex

    assert Memoer.Codes == {'Basic': '__', 'Signed': '_-'}
    # Codes table with sizes of code (hard) and full primitive material
    assert Memoer.Sizes == \
    {
        '__': Sizage(cs=2, ms=22, vs=0, ss=0, ns=4, hs=28),
        '_-': Sizage(cs=2, ms=22, vs=44, ss=88, ns=4, hs=160),
    }
    #  verify Sizes and Codes
    for code, val in Memoer.Sizes.items():
        cs = val.cs
        ms = val.ms
        vs = val.vs
        ss = val.ss
        ns = val.ns
        hs = val.hs

        assert len(code) == cs == 2
        assert code[0] == '_'
        code[1] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz01234567890-_'
        assert hs > 0
        assert hs == cs + ms + vs + ss + ns
        assert ms  # ms must not be empty
        ps = (3 - ((ms) % 3)) % 3  # net pad size for mid
        assert ps == (cs % 4)  #  combined code + mid size must lie on 24 bit boundary
        assert not vs % 4   # vid size must be on 24 bit boundary
        assert not ss % 4   # sig size must be on 24 bit boundary
        assert ns and not ns % 4   # neck (num or cnt) size must be on 24 bit boundary
        assert hs and not hs % 4   # head size must be on 24 bit boundary
        if vs:
            assert ss  # ss must not be empty if vs not empty

    assert Memoer.Names == {'__': 'Basic', '_-': 'Signed'}
    assert Memoer.Sodex == SGDex

    # Base2 Binary index representation of Text Base64 Char Codes
    #assert Memoer.Bodes == {b'\xff\xf0': '__', b'\xff\xe0': '_-'}

    assert Memoer.MaxMemoSize == ((2**30-1)*4+8)  # absolute max memo payload size
    assert Memoer.MaxGramSize == (2**16-1)  # absolute max gram size
    assert Memoer.MaxGramCount == (2**24-1)  # absolute max gram count
    assert Memoer.BufSize == (2**16-1) # default buffersize

    verkey = (b"o\x91\xf4\xbe$Mu\x0b{}\xd3\xaa'g\xd1\xcf\x96\xfb\x1e\xb1S\x89H\\'ae\x06+\xb2(v")
    vidqb64 = Memoer._encodeVid(vid=verkey)
    assert vidqb64 == 'BG-R9L4kTXULe33Tqidn0c-W-x6xU4lIXCdhZQYrsih2'
    cs, ms, vs, ss, ns, hs = Memoer.Sizes[SGDex.Signed]  # cs ms vs ss ns hs
    assert len(vidqb64) == 44 == vs
    """Done Test"""


def test_setup_keep():
    """Test _setupkeep utility function
    """
    try:
        keep = _setupKeep()  # default salt
    except MemoerError as ex:
        return

    assert keep == \
    {
        'BG-R9L4kTXULe33Tqidn0c-W-x6xU4lIXCdhZQYrsih2': Keyage(verkey=b"o\x91\xf4\xbe$Mu\x0b{}\xd3\xaa'g\xd1\xcf\x96\xfb\x1e\xb1S\x89H\\'ae\x06+\xb2(v",
                                                               sigseed=b"\x9bF\n\xf1\xc2L\xeaBC:\xf7\xe9\xd71\xbc\xd2{\x7f\x81\xae5\x9c\xca\xf9\xdb\xac@`'\x0e\xa4\x10"),
        'DJb1Z0pHx36MCOuIHWR4yPxfIiBxVzg6UCamv8fAN8gH': Keyage(verkey=b'\x96\xf5gJG\xc7~\x8c\x08\xeb\x88\x1ddx\xc8\xfc_" qW8:P&\xa6\xbf\xc7\xc07\xc8\x07',
                                                               sigseed=b'|\x97\xe1\xffN\x07:\x8d`\xfef\xd5E8\xc2\xba\xad,\x96\x9e\xba\xbe\xdc\xe6IB\x01i\x92\x8c\xd3W'),
        'EGLDQ97VnSnJS19Dz0j3NcgASGjMgMm4R-DmyrPDRZtN': Keyage(verkey=b'\x0c\x16\x1ev\x1dXY\x1b\x9b\xfa0c\xbc\xab|7\x0eK=\xc2\x8a\x8dO\xb8\xc9=\x0c\r\xe5\xad\xc5Z',
                                                               sigseed=b'@L\xb3\x87\xff\x9e\xe0J\x14\xc5\xbf8\x8e\x83\x00\xd8\xc4\x0f\xff\xcc&\t\x9e|\x81Y\x06\x82\xd5\x07\xf3\x8c')
    }

    salt = b"ABCDEFGHIJKLMNOP"
    try:
        keep = _setupKeep(salt=salt)
    except MemoerError as ex:
        return

    assert keep == \
    {
        'BJZTHNWXscuT-SPokPzSeBkShpHj6g8bQrP0Rh7IJNUp': Keyage(verkey=b'\x96S\x1c\xd5\x97\xb1\xcb\x93\xf9#\xe8\x90\xfc\xd2x\x19\x12\x86\x91\xe3\xea\x0f\x1bB\xb3\xf4F\x1e\xc8$\xd5)',
                                                               sigseed=b'\xc3\xf7y\xe4\\\\VG\xb0\x9b\xcb\xaf\x83=\xcf\x13TD\x12\x85\xe50\xe3T\x94x\xb9\xed4Z\x14\x02'),
        'DGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni': Keyage(verkey=b"c\x91\x04QI{\x96c\xe1=E@zQ\x15'\xb8\xd6\x14.\xab\xc1\xd4,\x03\x16\xc9\xcfB\xd3\xb9\xe2",
                                                               sigseed=b'\xec\xf5I\xcf\xa3|H\xe65!\x16\xb7O\xa0\xe3\xe7 \xb2\x17\x1d\x01\xf9/\x11\x19FJK\x9eG\xc7\xa4'),
        'EJ9RvVS6j6-stXpJEyaTi-MOJ1lZUQYkv9-Dc5GGHCVK': Keyage(verkey=b'L>zx\xc6s\xea;\xfdK7\xe0\x86N\xfaP\xdb\xa8Q\xb58!\x80\x83\xc7\xb5\xfe\x1dk_\xa7&',
                                                               sigseed=b'\xd9\x8f\xb7\xc9\xcd#\xd6 X\x07+*]\x7f\xa3\x99W\xbfSt-\xee\xea\x8e\xa4q\x9d\xdb\x88\xdf\xef ')
    }

    """Done"""




def test_memoer_basic():
    """Test Memoer class basic
    """
    peer = memoing.Memoer()
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.GramDex.Basic == '__'
    assert not peer.curt
    # (code, mid, vid, sig, neck, head) part sizes
    assert peer.Sizes[peer.code] == (2, 22, 0, 0, 4, 28)  # cs ms vs ss ns hs
    assert peer.size == peer.MaxGramSize
    assert not peer.verific
    assert not peer.echoic
    assert peer.keep == dict()
    assert peer.vid is None

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
    assert peer.txms[0] == ('Hello There', 'beta', None)
    peer.serviceTxMemos()
    assert not peer.txms
    m, d = peer.txgs[0]
    assert not peer.wiff(m)  # base64
    assert m.endswith(memo.encode())
    assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    # inject sent gram into .echos so it can recieve from its own as mock transport
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = '__ALBI68S1ZIxqwFOSWFF1L2'
    gram = (mid + 'AAAA' + 'AAAB' + "Hello There").encode()
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
    assert peer.rxms[0] == ('Hello There', 'beta', None)
    peer.serviceRxMemos()
    assert not peer.rxms

    assert peer.inbox[0] == ('Hello There', 'beta', None)

    # send and receive via .echos to itself as both sender and receiver
    memo = "See ya later!"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('See ya later!', 'beta', None)
    peer.serviceTxMemos()
    assert not peer.txms
    m, d = peer.txgs[0]
    assert not peer.wiff(m)  # base64
    assert m.endswith(memo.encode())
    assert d == dst == 'beta'
    peer.serviceTxGrams(echoic=True)  # send to .echos
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert peer.echos

    assert not peer.rxgs
    assert not peer.rxms
    assert not peer.counts
    assert not peer.sources
    peer.serviceReceives(echoic=True)  # receive own echo
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
    assert peer.rxms[0] == ('See ya later!', 'beta', None)
    peer.serviceRxMemos()
    assert not peer.rxms

    assert peer.inbox[0] == ('Hello There', 'beta', None)
    assert peer.inbox[1] == ('See ya later!', 'beta', None)

    # test binary q2 encoding of transmission gram header
    peer.curt = True  # set to binary base2
    assert peer.curt
    memo = "Hello There"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('Hello There', 'beta', None)
    peer.serviceTxMemos()
    assert not peer.txms
    m, d = peer.txgs[0]
    assert peer.wiff(m)  # base2
    assert m.endswith(memo.encode())
    assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = '__ALBI68S1ZIxqwFOSWFF1L2'
    headneck = decodeB64((mid + 'AAAA' + 'AAAB').encode())
    gram = headneck + b"Hello There"
    assert peer.wiff(gram)  # base2
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
    assert peer.rxms[0] == ('Hello There', 'beta', None)
    peer.serviceRxMemos()
    assert not peer.rxms

    assert peer.inbox[0] == ('Hello There', 'beta', None)
    assert peer.inbox[1] == ('See ya later!', 'beta', None)
    assert peer.inbox[2] == ('Hello There', 'beta', None)
    peer.inbox = deque()  # clear it

    peer.close()
    assert peer.opened == False
    """ End Test """


def test_memoer_small_gram_size():
    """Test Memoer class with small gram size
    """
    peer = memoing.Memoer(size=6)
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.GramDex.Basic == '__'
    assert not peer.curt
    # (code, mid, vid, sig, neck, head) part sizes
    assert peer.Sizes[peer.code] == (2, 22, 0, 0, 4, 28)  # cs ms vs ss ns hs
    assert peer.size == 33  # can't be smaller than head + neck + 1
    assert not peer.verific
    assert not peer.echoic
    assert peer.keep == dict()
    assert peer.vid is None

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
    assert peer.txms[0] == ('Hello There', 'beta', None)
    peer.serviceTxMemos()
    assert not peer.txms
    assert len(peer.txgs) == 2
    for m, d in peer.txgs:
        assert not peer.wiff(m)  # base64
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
    mid = '__DFymLrtlZG6bp0HhlUsR6u'
    gram = (mid + 'AAAA' + 'AAAC' + "Hello ").encode()
    echo = (gram, "beta")
    peer.echos.append(echo)
    gram = (mid + 'AAAB' + "There").encode()
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
    assert peer.rxms[0] == ('Hello There', 'beta', None)
    peer.serviceRxMemos()
    assert not peer.rxms
    assert not peer.echos

    assert peer.inbox[0] == ('Hello There', 'beta', None)

    # send and receive via echo
    memo = "See ya later!"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('See ya later!', 'beta', None)
    peer.serviceTxMemos()
    assert not peer.txms
    assert len(peer.txgs) == 2
    for m, d in peer.txgs:
        assert not peer.wiff(m)  # base64
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
    assert not peer.echos
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
    assert peer.rxms[0] == ('See ya later!', 'beta', None)
    peer.serviceRxMemos()
    assert not peer.rxms

    assert peer.inbox[0] == ('Hello There', 'beta', None)
    assert peer.inbox[1] == ('See ya later!', 'beta', None)

    # test binary q2 encoding of transmission gram header
    peer.curt =  True  # set to binary base2
    assert peer.curt
    assert peer.size == 38
    memo = 'See ya later alligator!'
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('See ya later alligator!', 'beta', None)
    peer.serviceTxMemos()
    assert not peer.txms
    assert len(peer.txgs) == 2
    for m, d in peer.txgs:
        assert peer.wiff(m)   # base2
        assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    assert not peer.echos

    b'__DFymLrtlZG6bp0HhlUsR6uAAAAAAACHello '
    b'__DFymLrtlZG6bp0HhlUsR6uAAABThere'
    mid = '__DFymLrtlZG6bp0HhlUsR6u'
    headneck = decodeB64((mid + 'AAAA' + 'AAAC').encode())
    gram = headneck + b"See ya later a"
    assert peer.wiff(gram)   # base2
    echo = (gram, "beta")
    peer.echos.append(echo)
    head = decodeB64((mid + 'AAAB').encode())
    gram = head + b"lligator!"
    assert peer.wiff(gram)  # base2
    echo = (gram, "beta")
    peer.echos.append(echo)

    peer.serviceReceives(echoic=True)
    assert not peer.echos
    assert len(peer.rxgs[mid]) == 2
    assert peer.counts[mid] == 2
    assert peer.sources[mid] == 'beta'
    assert peer.rxgs[mid][0] == bytearray(b'See ya later a')
    assert peer.rxgs[mid][1] == bytearray(b'lligator!')
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert peer.rxms[0] == ('See ya later alligator!', 'beta', None)
    peer.serviceRxMemos()
    assert not peer.rxms

    assert peer.inbox[0] == ('Hello There', 'beta', None)
    assert peer.inbox[1] == ('See ya later!', 'beta', None)
    assert peer.inbox[2] == ('See ya later alligator!', 'beta', None)
    peer.inbox = deque()  # clear it

    peer.close()
    assert peer.opened == False
    """ End Test """


def test_memoer_multiple():
    """Test Memoer class with small gram size and multiple queued memos
    """
    peer = memoing.Memoer(size=38)
    assert peer.size == 38
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.GramDex.Basic == '__'
    assert not peer.curt
    assert not peer.verific
    assert not peer.echoic
    assert peer.keep == dict()
    assert peer.vid is None

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
        assert not peer.wiff(m)  # base64
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
    assert peer.rxms[0] == ('Hello there.', 'alpha', None)
    assert peer.rxms[1] == ('How ya doing?', 'beta', None)
    peer.serviceRxMemos()
    assert not peer.rxms

    assert peer.inbox[0] == ('Hello there.', 'alpha', None)
    assert peer.inbox[1] == ('How ya doing?', 'beta', None)

    peer.inbox = deque()  # clear it

    peer.close()
    assert peer.opened == False
    """ End Test """


def test_memoer_multiple_echoic_service_tx_rx():
    """Test Memoer class with small gram size and multiple queued memos
    Use .echoic property true so can service all
    """
    peer = memoing.Memoer(size=38, echoic=True)
    assert peer.size == 38
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.GramDex.Basic == '__'
    assert not peer.curt
    assert not peer.verific
    assert peer.echoic
    assert peer.keep == dict()
    assert peer.vid is None

    peer.reopen()
    assert peer.opened == True

    # send and receive multiple via echo
    peer.memoit("Hello there.", "alpha")
    peer.memoit("How ya doing?", "beta")
    assert len(peer.txms) == 2

    peer.serviceAllTx()
    assert not peer.txms
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert len(peer.echos) == 4

    assert not peer.rxgs
    assert not peer.rxms
    assert not peer.counts
    assert not peer.sources

    peer.serviceAllRx()

    assert not peer.echos
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms

    assert peer.inbox[0] == ('Hello there.', 'alpha', None)
    assert peer.inbox[1] == ('How ya doing?', 'beta', None)

    peer.inbox = deque()  # clear it

    peer.close()
    assert peer.opened == False
    """ End Test """


def test_memoer_multiple_echoic_service_all():
    """Test Memoer class with small gram size and multiple queued memos
    Use .echoic property true so can service all
    """
    peer = memoing.Memoer(size=38, echoic=True)
    assert peer.size == 38
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.GramDex.Basic == '__'
    assert not peer.curt
    assert not peer.verific
    assert peer.echoic
    assert peer.keep == dict()
    assert peer.vid is None

    peer.reopen()
    assert peer.opened == True

    # send and receive multiple via echo
    peer.memoit("Hello there.", "alpha")
    peer.memoit("How ya doing?", "beta")
    assert len(peer.txms) == 2

    peer.serviceAll()  # services Rx first then Tx so have to serviceAll twice

    assert not peer.txms
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert len(peer.echos) == 4  # Rx not serviced yet after Tx serviced

    peer.serviceAll()  # services Rx first then Tx so have to serviceAll twice
    assert not peer.echos
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms

    assert peer.inbox[0] == ('Hello there.', 'alpha', None)
    assert peer.inbox[1] == ('How ya doing?', 'beta', None)

    peer.inbox = deque()  # clear it

    peer.close()
    assert peer.opened == False
    """ End Test """


def test_memoer_basic_signed():
    """Test Memoer class basic signed code
    """
    salt = b"ABCDEFGHIJKLMNOP"
    try:
        keep = _setupKeep(salt=salt)
    except MemoerError as ex:
        return

    peer = memoing.Memoer(code=GramDex.Signed)
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.GramDex.Signed == '_-'
    assert not peer.curt
    # (code, mid, vid, sig, neck, head) part sizes
    assert peer.Sizes[peer.code] == (2, 22, 44, 88, 4, 160)  # cs ms vs ss ns hs
    assert peer.size == peer.MaxGramSize
    assert not peer.verific
    assert not peer.echoic
    assert peer.keep == dict()
    assert peer.vid is None

    peer.reopen()
    assert peer.opened == True

    assert not peer.txms
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    peer.service()
    assert peer.txbs == (b'', None)

    memo = "Hello There"
    dst = "beta"
    vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    peer.memoit(memo, dst, vid)
    assert peer.txms[0] == ('Hello There', 'beta', vid)
    peer.serviceTxMemos()
    assert not peer.txms
    g, d = peer.txgs[0]
    assert not peer.wiff(g)  # base64
    assert g.find(memo.encode()) != -1
    assert len(g) == 160 + 4 + len(memo)
    assert g[:2].decode() == GramDex.Signed
    assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = '_-ALBI68S1ZIxqwFOSWFF1L2'

    sig = ('A' * 88)
    gram = (mid + vid + 'AAAA' + 'AAAB' + "Hello There" + sig).encode()
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
    assert peer.rxms[0] == ('Hello There', 'beta', vid)
    peer.serviceRxMemos()
    assert not peer.rxms

    # send and receive via echo
    memo = "See ya later!"
    dst = "beta"
    vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    peer.memoit(memo, dst, vid)
    assert peer.txms[0] == ('See ya later!', 'beta', vid)
    peer.serviceTxMemos()
    assert not peer.txms
    g, d = peer.txgs[0]
    assert not peer.wiff(g)  # base64
    assert g.find(memo.encode()) != -1
    assert len(g) == 160 + 4 + len(memo)
    assert g[:2].decode() == GramDex.Signed
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
    assert peer.rxms[0] == ('See ya later!', 'beta', vid)
    peer.serviceRxMemos()
    assert not peer.rxms

    # test binary q2 encoding of transmission gram header
    peer.curt = True  # set to binary base2
    memo = "Hello There"
    dst = "beta"
    vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    peer.memoit(memo, dst, vid)
    assert peer.txms[0] == ('Hello There', 'beta', vid)
    peer.serviceTxMemos()
    assert not peer.txms
    g, d = peer.txgs[0]
    assert peer.wiff(g)  # base64
    assert g.find(memo.encode()) != -1
    assert len(g) == 3 * (160 + 4) // 4 + len(memo)
    assert helping.codeB2ToB64(g, 2) == GramDex.Signed
    assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = '_-ALBI68S1ZIxqwFOSWFF1L2'
    vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    sig = ('A' * 88)
    head = decodeB64((mid + vid + 'AAAA' + 'AAAB').encode())
    tail = decodeB64(sig.encode())
    gram = head + memo.encode() + tail
    assert peer.wiff(gram)  # base2
    assert len(gram) == 3 * (160 + 4) // 4 + len(memo)
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
    assert peer.rxms[0] == ('Hello There', 'beta', vid)
    peer.serviceRxMemos()
    assert not peer.rxms

    assert peer.inbox[0] == ('Hello There', 'beta', vid)
    assert peer.inbox[1] == ('See ya later!', 'beta', vid)
    assert peer.inbox[2] == ('Hello There', 'beta', vid)

    peer.inbox = deque()  # clear it

    peer.close()
    assert peer.opened == False
    """ End Test """

def test_memoer_multiple_signed():
    """Test Memoer class with small gram size and multiple queued memos signed
    """
    salt = b"ABCDEFGHIJKLMNOP"
    try:
        keep = _setupKeep(salt=salt)
    except MemoerError as ex:
        return

    peer = memoing.Memoer(code=GramDex.Signed, size=170)
    assert peer.size == 170
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.GramDex.Signed == '_-'
    assert not peer.curt
    assert not peer.verific
    assert not peer.echoic
    assert peer.keep == dict()
    assert peer.vid is None

    peer.reopen()
    assert peer.opened == True

    # send and receive multiple via echo
    vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    peer.memoit("Hello there.", "alpha", vid)
    peer.memoit("How ya doing?", "beta", vid)
    assert len(peer.txms) == 2
    peer.serviceTxMemos()
    assert not peer.txms
    assert len(peer.txgs) == 4
    for g, d in peer.txgs:
        assert not peer.wiff(g)  # base64
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
    assert peer.rxms[0] == ('Hello there.', 'alpha', vid)
    assert peer.rxms[1] == ('How ya doing?', 'beta', vid)
    peer.serviceRxMemos()
    assert not peer.rxms

    # test in base2 mode
    peer.curt = True
    assert peer.curt
    peer.size = 129
    assert peer.size == 129

    # send and receive multiple via echo
    vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    peer.memoit("Hello there.", "alpha", vid)
    peer.memoit("How ya doing?", "beta", vid)
    assert len(peer.txms) == 2
    peer.serviceTxMemos()
    assert not peer.txms
    assert len(peer.txgs) == 4
    for g, d in peer.txgs:
        assert peer.wiff(g)  # base64
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
    assert peer.rxms[0] == ('Hello there.', 'alpha', vid)
    assert peer.rxms[1] == ('How ya doing?', 'beta', vid)
    peer.serviceRxMemos()
    assert not peer.rxms

    assert peer.inbox == deque(
    [
        ('Hello there.', 'alpha', vid),
        ('How ya doing?', 'beta', vid),
        ('Hello there.', 'alpha', vid),
        ('How ya doing?', 'beta', vid)
    ])


    peer.close()
    assert peer.opened == False
    """ End Test """


def test_memoer_verific():
    """Test Memoer class with verific (signed required)
    """

    peer = memoing.Memoer(verific=True)
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.GramDex.Basic == '__'
    assert not peer.curt
    # (code, mid, vid, sig, neck, head) part sizes
    assert peer.Sizes[peer.code] == (2, 22, 0, 0, 4, 28)  # cs ms vs ss ns hs
    assert peer.size == peer.MaxGramSize
    assert peer.verific
    assert not peer.echoic
    assert peer.keep == dict()
    assert peer.vid is None

    peer.reopen()
    assert peer.opened == True

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = '__ALBI68S1ZIxqwFOSWFF1L2'  # not signed code
    gram = (mid + 'AAAA' + 'AAAB' + "Hello There").encode()
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert not peer.rxgs  # dropped gram
    assert not peer.echos
    assert not peer.rxms

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = '_-ALBI68S1ZIxqwFOSWFF1L2'
    vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    sig = ('A' * 88)
    gram = (mid + vid + 'AAAA' + 'AAAB' + "Hello There" + sig).encode()
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert peer.rxgs[mid][0] == bytearray(b'Hello There')
    assert peer.counts[mid] == 1
    assert peer.sources[mid] == 'beta'
    assert not peer.echos
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert peer.rxms[0] == ('Hello There', 'beta', vid)
    peer.serviceRxMemos()
    assert not peer.rxms

    assert peer.inbox == deque(
    [
        ('Hello There', 'beta', vid)
    ])

    peer.close()
    assert peer.opened == False
    """ End Test """


def test_memoer_multiple_signed_verific_echoic_service_all():
    """Test Memoer class with small gram size and multiple queued memos signed
    using echos for transport
    """
    salt = b"ABCDEFGHIJKLMNOP"
    try:
        keep = _setupKeep(salt=salt)
    except MemoerError as ex:
        return

    # verific forces rx memos to be signed or dropped
    # to force signed tx then use Signed code
    peer = memoing.Memoer(code=GramDex.Signed, size=170, verific=True, echoic=True)
    assert peer.size == 170
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.GramDex.Signed == '_-'
    assert not peer.curt
    assert peer.verific
    assert peer.echoic
    assert peer.keep == dict()
    assert peer.vid is None

    peer.reopen()
    assert peer.opened == True

    # send and receive multiple via echo
    vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    peer.memoit("Hello there.", "alpha", vid)
    peer.memoit("How ya doing?", "beta", vid)
    assert len(peer.txms) == 2

    peer.serviceAll()  # servicAll services Rx first then Tx so have to repeat

    assert not peer.txms
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert len(peer.echos) == 4  # rx not serviced yet
    assert not peer.rxgs
    assert not peer.rxms
    assert not peer.counts
    assert not peer.sources

    peer.serviceAll()  # servicAll services Rx first then Tx so have to repeat
    assert not peer.echos
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms

    assert peer.inbox == deque(
    [
        ('Hello there.', 'alpha', vid),
        ('How ya doing?', 'beta', vid)
    ])


    # test in base2 mode
    peer.curt = True
    assert peer.curt
    peer.size = 129
    assert peer.size == 129

    # send and receive multiple via echo
    vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    peer.memoit("Hello there.", "alpha", vid)
    peer.memoit("How ya doing?", "beta", vid)
    assert len(peer.txms) == 2

    peer.serviceAll()  # servicAll services Rx first then Tx so have to repeat

    assert not peer.txms
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert len(peer.echos) == 4  # rx not serviced yet
    assert not peer.rxgs
    assert not peer.rxms
    assert not peer.counts
    assert not peer.sources

    peer.serviceAll()  # servicAll services Rx first then Tx so have to repeat
    assert not peer.echos
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms

    assert peer.inbox == deque(
    [
        ('Hello there.', 'alpha', vid),
        ('How ya doing?', 'beta', vid),
        ('Hello there.', 'alpha', vid),
        ('How ya doing?', 'beta', vid),
    ])

    peer.inbox = deque()  # clear it

    peer.close()
    assert peer.opened == False
    """ End Test """


def test_open_memoer():
    """Test contextmanager decorator openMemoer
    """
    with (memoing.openMemoer(name='zeta') as zeta):

        assert zeta.opened
        assert zeta.name == 'zeta'


    assert not zeta.opened

    """ End Test """


def test_memoer_doer():
    """Test MemoerDoer class
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



def test_sure_memoer_basic():
    """Test SureMemoer class basic
    """
    try:
        keep = _setupKeep()  # uses default salt
    except MemoerError as ex:
        return


    peer = memoing.SureMemoer(echoic=True)
    assert peer.size == 65535
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.GramDex.Signed == '_-'
    assert not peer.curt
    assert peer.verific
    assert peer.echoic
    assert peer.keep == dict()
    assert peer.vid is None

    # (code, mid, vid, neck, head, sig) part sizes
    assert peer.Sizes[peer.code] == Sizage(cs=2, ms=22, vs=44, ss=88, ns=4, hs=160) # cs ms vs ss ns hs
    assert peer.size == peer.MaxGramSize
    assert peer.tymeout == 0.0
    assert peer.tymers == {}

    peer.reopen()
    assert peer.opened == True

    assert not peer.txms
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    peer.service()  # alias for .serviceAll
    assert peer.txbs == (b'', None)

    memo = "Hello There"
    dst = "beta"
    vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    peer.memoit(memo, dst, vid)
    assert peer.txms[0] == ('Hello There', 'beta', vid)

    peer.service()  # services Rx then Tx so rx of tx not serviced until 2nd pass

    assert not peer.txms
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert len(peer.echos) == 1
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms

    peer.service()

    assert not peer.echos
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms

    assert peer.inbox == deque(
    [
        ('Hello There', 'beta', vid),
    ])

    # send and receive some more
    memo = "See ya later!"
    dst = "beta"
    peer.memoit(memo, dst, vid)
    assert peer.txms[0] == ('See ya later!', 'beta', vid)

    peer.service()

    assert not peer.txms
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert len(peer.echos) == 1

    assert not peer.rxgs
    assert not peer.rxms
    assert not peer.counts
    assert not peer.sources

    peer.service()

    assert not peer.echos
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms

    assert peer.inbox == deque(
    [
        ('Hello There', 'beta', vid),
        ('See ya later!', 'beta', vid),
    ])

    # test binary q2 encoding of transmission gram header
    peer.curt = True  # set to binary base2
    memo = "Hello There"
    dst = "beta"
    peer.memoit(memo, dst, vid)
    assert peer.txms[0] == ('Hello There', 'beta', vid)

    peer.service()

    assert not peer.txms
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert len(peer.echos) == 1

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms

    peer.service()
    assert not peer.echos
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms

    assert peer.inbox == deque(
    [
        ('Hello There', 'beta', vid),
        ('See ya later!', 'beta', vid),
        ('Hello There', 'beta', vid),
    ])

    # Test wind
    tymist = tyming.Tymist(tock=1.0)
    peer.wind(tymth=tymist.tymen())
    assert peer.tyme == tymist.tyme == 0.0
    tymist.tick()
    assert peer.tyme == tymist.tyme == 1.0

    peer.close()
    assert peer.opened == False
    """ End Test """

def test_open_sm():
    """Test contextmanager decorator openTM for openTymeeMemoer
    """
    try:
        keep = _setupKeep()  # uses default salt
    except MemoerError as ex:
        return

    with (memoing.openSM(name='zeta') as zeta):

        assert zeta.opened
        assert zeta.name == 'zeta'
        assert zeta.tymeout == 0.0
        assert zeta.tymers == {}


    assert not zeta.opened

    """ End Test """


def test_sure_memoer_multiple_echoic_service_all():
    """Test SureMemoer class with small gram size and multiple queued memos signed
    using echos for transport
    """
    try:
        keep = _setupKeep()  # uses default salt
    except MemoerError as ex:
        return

    # verific forces rx memos to be signed or dropped
    # to force signed tx then use Signed code

    with memoing.openSM(size=170, echoic=True) as peer:
        assert peer.size == 170
        assert peer.name == "test"
        assert peer.opened == True
        assert peer.bc is None
        assert peer.bs == memoing.Memoer.BufSize == 65535
        assert peer.code == memoing.GramDex.Signed == '_-'
        assert not peer.curt
        assert peer.verific
        assert peer.echoic
        assert peer.keep == dict()
        assert peer.vid is None

        # send and receive multiple via echo
        vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
        peer.memoit("Hello there.", "alpha", vid)
        peer.memoit("How ya doing?", "beta", vid)
        assert len(peer.txms) == 2

        peer.service()  # services Rx first then Tx so have to repeat

        assert not peer.txms
        assert not peer.txgs
        assert peer.txbs == (b'', None)
        assert len(peer.echos) == 4  # rx not serviced yet

        assert not peer.rxgs
        assert not peer.rxms
        assert not peer.counts
        assert not peer.sources

        peer.serviceAll()  # servicAll services Rx first then Tx so have to repeat
        assert not peer.echos
        assert not peer.rxgs
        assert not peer.counts
        assert not peer.sources
        assert not peer.rxms

        assert peer.inbox == deque(
        [
            ('Hello there.', 'alpha', vid),
            ('How ya doing?', 'beta', vid)
        ])


        # test in base2 mode
        peer.curt = True
        assert peer.curt
        peer.size = 129
        assert peer.size == 129

        # send and receive multiple via echo
        vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
        peer.memoit("Hello there.", "alpha", vid)
        peer.memoit("How ya doing?", "beta", vid)
        assert len(peer.txms) == 2

        peer.serviceAll()  # servicAll services Rx first then Tx so have to repeat

        assert not peer.txms
        assert not peer.txgs
        assert peer.txbs == (b'', None)
        assert len(peer.echos) == 4  # rx not serviced yet
        assert not peer.rxgs
        assert not peer.rxms
        assert not peer.counts
        assert not peer.sources

        peer.serviceAll()  # servicAll services Rx first then Tx so have to repeat
        assert not peer.echos
        assert not peer.rxgs
        assert not peer.counts
        assert not peer.sources
        assert not peer.rxms

        assert peer.inbox == deque(
        [
            ('Hello there.', 'alpha', vid),
            ('How ya doing?', 'beta', vid),
            ('Hello there.', 'alpha', vid),
            ('How ya doing?', 'beta', vid),
        ])

        peer.inbox = deque()  # clear it

    assert peer.opened == False
    """ End Test """


def test_sure_memoer_doer():
    """Test SureMemoerDoer class
    """
    try:
        keep = _setupKeep()  # uses default salt
    except MemoerError as ex:
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

    peer = memoing.SureMemoer()

    tmgdoer = memoing.SureMemoerDoer(peer=peer)
    assert tmgdoer.peer == peer
    assert not tmgdoer.peer.opened
    assert tmgdoer.tock == 0.0  # ASAP

    doers = [tmgdoer]
    doist.do(doers=doers)
    assert doist.tyme == limit
    assert tmgdoer.peer.opened == False

    tymist = tyming.Tymist(tock=1.0)
    tmgdoer.wind(tymth=tymist.tymen())
    assert tmgdoer.tymth == tmgdoer.peer.tymth
    assert tmgdoer.tyme == peer.tyme == tymist.tyme == 0.0

    tymist.tick()
    assert tmgdoer.tyme == peer.tyme == tymist.tyme == 1.0

    """End Test """



if __name__ == "__main__":
    test_memoer_class()
    test_setup_keep()
    test_memoer_basic()
    test_memoer_small_gram_size()
    test_memoer_multiple()
    test_memoer_multiple_echoic_service_tx_rx()
    test_memoer_multiple_echoic_service_all()
    test_memoer_basic_signed()
    test_memoer_multiple_signed()
    test_memoer_verific()
    test_memoer_multiple_signed_verific_echoic_service_all()
    test_open_memoer()
    test_memoer_doer()
    test_sure_memoer_basic()
    test_open_sm()
    test_sure_memoer_multiple_echoic_service_all()
    test_sure_memoer_doer()

