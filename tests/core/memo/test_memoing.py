# -*- encoding: utf-8 -*-
"""
tests.core.test_memoing module

"""
from collections import deque
from base64 import urlsafe_b64encode as encodeB64
from base64 import urlsafe_b64decode as decodeB64

import pysodium
import blake3

import pytest

from hio.hioing import MemoerError
from hio.help import helping
from hio.base import doing, tyming
from hio.core.memo import memoing
from hio.core.memo import Versionage, Sizage, GramDex, SGDex, Memoer, Keyage


def _setupKeep(salt=None):
    """Setup Keep for signed memos

    Parameters:
        salt(str|bytes): salt used to generate key pairs and oids for keep

    Returns:
        keep (dict): labels are oids, values are keyage instances


    Ed25519_Seed: str = 'A'  # Ed25519 256 bit random seed for private key
    """
    salt = salt if salt is not None else b"abcdefghijklmnop"
    if hasattr(salt, 'encode'):
        salt = salt.encode()

    if len(salt) != 16:
        raise MemoerError("Invalid provided salt")

    keep = {}

    # non transferable verkey as oid
    sigseed = pysodium.crypto_pwhash(outlen=32,
                                    passwd="0",
                                    salt=salt,
                                    opslimit=2,  # pysodium.crypto_pwhash_OPSLIMIT_INTERACTIVE,
                                    memlimit=67108864,  # pysodium.crypto_pwhash_MEMLIMIT_INTERACTIVE,
                                    alg=pysodium.crypto_pwhash_ALG_ARGON2ID13)
    # creates signing/verification key pair from seed
    verkey, sigkey = pysodium.crypto_sign_seed_keypair(sigseed)  # raw

    oid = Memoer._encodeOID(raw=verkey, code='B')  # make fully qualified
    qvk = Memoer._encodeQVK(raw=verkey)  # make fully qualified
    qss = Memoer._encodeQSS(raw=sigseed)  # make fully qualified
    keyage = Keyage(qvk=qvk, qss=qss)  # raw
    keep[oid] = keyage

    # transferable verkey as oid
    sigseed = pysodium.crypto_pwhash(outlen=32,
                                    passwd="1",
                                    salt=salt,
                                    opslimit=2,  # pysodium.crypto_pwhash_OPSLIMIT_INTERACTIVE,
                                    memlimit=67108864,  # pysodium.crypto_pwhash_MEMLIMIT_INTERACTIVE,
                                    alg=pysodium.crypto_pwhash_ALG_ARGON2ID13)
    # creates signing/verification key pair from seed
    verkey, sigkey = pysodium.crypto_sign_seed_keypair(sigseed)  # raw

    oid = Memoer._encodeOID(raw=verkey, code='D')  # make fully qualified
    qvk = Memoer._encodeQVK(raw=verkey)  # make fully qualified
    qss = Memoer._encodeQSS(raw=sigseed)  # make fully qualified
    keyage = Keyage(qvk=qvk, qss=qss)  # raw
    keep[oid] = keyage

    # digest of verkey as oid
    sigseed = pysodium.crypto_pwhash(outlen=32,
                                    passwd="2",
                                    salt=salt,
                                    opslimit=2,  # pysodium.crypto_pwhash_OPSLIMIT_INTERACTIVE,
                                    memlimit=67108864,  # pysodium.crypto_pwhash_MEMLIMIT_INTERACTIVE,
                                    alg=pysodium.crypto_pwhash_ALG_ARGON2ID13)
    # creates signing/verification key pair from seed
    verkey, sigkey = pysodium.crypto_sign_seed_keypair(sigseed)  # raw
    dig = digest = blake3.blake3(verkey).digest()

    oid = Memoer._encodeOID(raw=dig, code='E')
    qvk = Memoer._encodeQVK(raw=verkey)  # make fully qualified
    qss = Memoer._encodeQSS(raw=sigseed)  # make fully qualified
    keyage = Keyage(qvk=qvk, qss=qss)  # raw
    keep[oid] = keyage

    return keep


def test_memoer_class():
    """Test class attributes of Memoer class"""

    assert Memoer.Version == Versionage(major=0, minor=0)
    assert Memoer.Codex == memoing.GramDex

    assert Memoer.Codes == {'Basic': '__', 'Signed': '_-'}
    # Codes table with sizes of code (hard) and full primitive material
    assert Memoer.Sizes == \
    {
        '__': Sizage(cz=2, mz=22, oz=0, nz=4, sz=0, hz=28),
        '_-': Sizage(cz=2, mz=22, oz=44, nz=4, sz=88, hz=160),
    }
    #  verify Sizes and Codes
    for code, val in Memoer.Sizes.items():
        cz = val.cz
        mz = val.mz
        oz = val.oz
        nz = val.nz
        sz = val.sz
        hz = val.hz

        assert len(code) == cz == 2
        assert code[0] == '_'
        code[1] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz01234567890-_'
        assert hz > 0
        assert hz == cz + mz + oz + sz + nz
        assert mz  # ms must not be empty
        pz = (3 - ((mz) % 3)) % 3  # net pad size for mid
        assert pz == (cz % 4)  #  combined code + mid size must lie on 24 bit boundary
        assert not oz % 4   # oid size must be on 24 bit boundary
        assert not sz % 4   # sig size must be on 24 bit boundary
        assert nz and not nz % 4   # neck (num or cnt) size must be on 24 bit boundary
        assert hz and not hz % 4   # head size must be on 24 bit boundary
        if oz:
            assert sz  # sz must not be empty if oz not empty

    assert Memoer.Names == {'__': 'Basic', '_-': 'Signed'}
    assert Memoer.Sodex == SGDex

    # Base2 Binary index representation of Text Base64 Char Codes
    #assert Memoer.Bodes == {b'\xff\xf0': '__', b'\xff\xe0': '_-'}

    assert Memoer.MaxMemoSize == ((2**30-1)*4+8)  # absolute max memo payload size
    assert Memoer.MaxGramSize == (2**16-1)  # absolute max gram size
    assert Memoer.MaxGramCount == (2**24-1)  # absolute max gram count
    assert Memoer.BufSize == (2**16-1) # default buffersize

    verkey = (b"o\x91\xf4\xbe$Mu\x0b{}\xd3\xaa'g\xd1\xcf\x96\xfb\x1e\xb1S\x89H\\'ae\x06+\xb2(v")
    oid = Memoer._encodeOID(raw=verkey)
    assert oid == 'BG-R9L4kTXULe33Tqidn0c-W-x6xU4lIXCdhZQYrsih2'
    raw, code = Memoer._decodeOID(oid)
    assert raw == verkey
    assert code == 'B'
    _, _, oz, _, _, _ = Memoer.Sizes[SGDex.Signed]  # cz mz oz nz sz hz
    assert len(oid) == 44 == oz

    qvk = Memoer._encodeQVK(raw=verkey)
    assert qvk == 'BG-R9L4kTXULe33Tqidn0c-W-x6xU4lIXCdhZQYrsih2'
    raw, code = Memoer._decodeQVK(oid)
    assert raw == verkey
    assert code == 'B'
    assert len(qvk) == 44

    sigseed = (b"\x9bF\n\xf1\xc2L\xeaBC:\xf7\xe9\xd71\xbc\xd2{\x7f\x81\xae5\x9c\xca\xf9\xdb\xac@`'\x0e\xa4\x10")
    qss = Memoer._encodeQSS(raw=sigseed)
    assert qss == 'AJtGCvHCTOpCQzr36dcxvNJ7f4GuNZzK-dusQGAnDqQQ'
    raw, code = Memoer._decodeQSS(qss)
    assert raw == sigseed
    assert code == 'A'

    signature = (b'\xb0\xc0\xd5\t\xa0\xd3Q0\xfa8\x93B\x0c\x83\xb5.\xfbH\xa5\xde\xbf}6{'
                b'\xcf|\xa3\x0el"\x84f\xd3sbHC\xb9\xb9\x85\xb0\xd2v\xed\x07\xcf|c\xa4\xd6\xdcE'
                b'\xbe\x8a{w5=\xbf\x84_\x9e\xb3\x04')
    sig = Memoer._encodeSig(raw=signature)
    assert sig == '0BCwwNUJoNNRMPo4k0IMg7Uu-0il3r99NnvPfKMObCKEZtNzYkhDubmFsNJ27QfPfGOk1txFvop7dzU9v4RfnrME'
    raw, code = Memoer._decodeSig(sig)
    assert raw == signature
    assert code == '0B'
    _, _, _, _, sz, _ = Memoer.Sizes[SGDex.Signed]  # cz mz oz nz sz hz
    assert len(sig) == 88 == sz

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
        'BG-R9L4kTXULe33Tqidn0c-W-x6xU4lIXCdhZQYrsih2': Keyage(qvk='BG-R9L4kTXULe33Tqidn0c-W-x6xU4lIXCdhZQYrsih2',
                                                               qss='AJtGCvHCTOpCQzr36dcxvNJ7f4GuNZzK-dusQGAnDqQQ'),
        'DJb1Z0pHx36MCOuIHWR4yPxfIiBxVzg6UCamv8fAN8gH': Keyage(qvk='BJb1Z0pHx36MCOuIHWR4yPxfIiBxVzg6UCamv8fAN8gH',
                                                               qss='AHyX4f9OBzqNYP5m1UU4wrqtLJaeur7c5klCAWmSjNNX'),
        'EGLDQ97VnSnJS19Dz0j3NcgASGjMgMm4R-DmyrPDRZtN': Keyage(qvk='BAwWHnYdWFkbm_owY7yrfDcOSz3Cio1PuMk9DA3lrcVa',
                                                               qss='AEBMs4f_nuBKFMW_OI6DANjED__MJgmefIFZBoLVB_OM')
    }


    salt = b"ABCDEFGHIJKLMNOP"
    try:
        keep = _setupKeep(salt=salt)
    except MemoerError as ex:
        return

    assert keep == \
    {
        'BJZTHNWXscuT-SPokPzSeBkShpHj6g8bQrP0Rh7IJNUp': Keyage(qvk='BJZTHNWXscuT-SPokPzSeBkShpHj6g8bQrP0Rh7IJNUp',
                                                               qss='AMP3eeRcXFZHsJvLr4M9zxNURBKF5TDjVJR4ue00WhQC'),
        'DGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni': Keyage(qvk='BGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni',
                                                               qss='AOz1Sc-jfEjmNSEWt0-g4-cgshcdAfkvERlGSkueR8ek'),
        'EJ9RvVS6j6-stXpJEyaTi-MOJ1lZUQYkv9-Dc5GGHCVK': Keyage(qvk='BEw-enjGc-o7_Us34IZO-lDbqFG1OCGAg8e1_h1rX6cm',
                                                               qss='ANmPt8nNI9YgWAcrKl1_o5lXv1N0Le7qjqRxnduI3-8g')
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
    assert peer.Sizes[peer.code] == (2, 22, 0, 4, 0, 28)  # cz mz oz nz sz hz
    assert peer.size == peer.MaxGramSize
    assert not peer.verific
    assert not peer.echoic
    assert peer.keep == dict()
    assert peer.oid is None

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
    assert peer.Sizes[peer.code] == (2, 22, 0, 4, 0, 28)  # cz mz oz nz sz hz
    assert peer.size == 33  # can't be smaller than head + neck + 1
    assert not peer.verific
    assert not peer.echoic
    assert peer.keep == dict()
    assert peer.oid is None

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
    assert peer.oid is None

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
    assert peer.oid is None

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
    assert peer.oid is None

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

    oid = list(keep.keys())[0]
    assert oid == 'BJZTHNWXscuT-SPokPzSeBkShpHj6g8bQrP0Rh7IJNUp'

    peer = memoing.Memoer(code=GramDex.Signed, keep=keep, oid=oid)
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.GramDex.Signed == '_-'
    assert not peer.curt
    assert peer.Sizes[peer.code] == (2, 22, 44, 4, 88, 160)  # cz mz oz nz sz hz
    assert peer.size == peer.MaxGramSize
    assert not peer.verific
    assert not peer.echoic
    assert peer.keep == keep
    assert peer.oid == oid

    peer.reopen()
    assert peer.opened == True

    assert not peer.txms
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    peer.service()
    assert peer.txbs == (b'', None)

    memo = "Hello There"
    dst = "beta"

    oid = 'DGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni'   # not default .oid
    peer.memoit(memo, dst, oid)
    assert peer.txms[0] == ('Hello There', 'beta', oid)
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
    gram = (mid + oid + 'AAAA' + 'AAAB' + "Hello There" + sig).encode()
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
    assert peer.rxms[0] == ('Hello There', 'beta', oid)
    peer.serviceRxMemos()
    assert not peer.rxms

    # send and receive via echo
    memo = "See ya later!"
    dst = "beta"
    oid = 'DGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni'   # not default .oid
    peer.memoit(memo, dst, oid)
    assert peer.txms[0] == ('See ya later!', 'beta', oid)
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
    assert peer.rxms[0] == ('See ya later!', 'beta', oid)
    peer.serviceRxMemos()
    assert not peer.rxms

    # test binary q2 encoding of transmission gram header
    peer.curt = True  # set to binary base2
    memo = "Hello There"
    dst = "beta"
    oid = 'DGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni'   # not default .oid
    peer.memoit(memo, dst, oid)
    assert peer.txms[0] == ('Hello There', 'beta', oid)
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
    oid = 'DGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni'   # not default .oid
    sig = ('A' * 88)
    head = decodeB64((mid + oid + 'AAAA' + 'AAAB').encode())
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
    assert peer.rxms[0] == ('Hello There', 'beta', oid)
    peer.serviceRxMemos()
    assert not peer.rxms

    assert peer.inbox[0] == ('Hello There', 'beta', oid)
    assert peer.inbox[1] == ('See ya later!', 'beta', oid)
    assert peer.inbox[2] == ('Hello There', 'beta', oid)

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

    oid = list(keep.keys())[0]
    assert oid == 'BJZTHNWXscuT-SPokPzSeBkShpHj6g8bQrP0Rh7IJNUp'

    oidBeta = list(keep.keys())[1]
    assert oidBeta == 'DGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni'

    peer = memoing.Memoer(code=GramDex.Signed, size=170, keep=keep, oid=oid)
    assert peer.size == 170
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.GramDex.Signed == '_-'
    assert not peer.curt
    assert not peer.verific
    assert not peer.echoic
    assert peer.keep == keep
    assert peer.oid == oid

    peer.reopen()
    assert peer.opened == True

    # send and receive multiple via echo
    peer.memoit("Hello there.", "alpha")  # use default for vidAlpha
    peer.memoit("How ya doing?", "beta", oidBeta)
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
    assert peer.rxms[0] == ('Hello there.', 'alpha', oid)
    assert peer.rxms[1] == ('How ya doing?', 'beta', oidBeta)
    peer.serviceRxMemos()
    assert not peer.rxms

    # test in base2 mode
    peer.curt = True
    assert peer.curt
    peer.size = 129
    assert peer.size == 129

    # send and receive multiple via echo in base2 .curt = True mode
    peer.memoit("Hello there.", "alpha")  # use default for vidAlpha
    peer.memoit("How ya doing?", "beta", oidBeta)
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
    assert peer.rxms[0] == ('Hello there.', 'alpha', oid)
    assert peer.rxms[1] == ('How ya doing?', 'beta', oidBeta)
    peer.serviceRxMemos()
    assert not peer.rxms

    assert peer.inbox == deque(
    [
        ('Hello there.', 'alpha', oid),
        ('How ya doing?', 'beta', oidBeta),
        ('Hello there.', 'alpha', oid),
        ('How ya doing?', 'beta', oidBeta)
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
    assert peer.Sizes[peer.code] == (2, 22, 0, 4, 0, 28)  # cz mz oz nz sz hz
    assert peer.size == peer.MaxGramSize
    assert peer.verific
    assert not peer.echoic
    assert peer.keep == dict()
    assert peer.oid is None

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
    oid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    sig = ('A' * 88)
    gram = (mid + oid + 'AAAA' + 'AAAB' + "Hello There" + sig).encode()
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
    assert peer.rxms[0] == ('Hello There', 'beta', oid)
    peer.serviceRxMemos()
    assert not peer.rxms

    assert peer.inbox == deque(
    [
        ('Hello There', 'beta', oid)
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

    oid = list(keep.keys())[0]
    assert oid == 'BJZTHNWXscuT-SPokPzSeBkShpHj6g8bQrP0Rh7IJNUp'

    vidBeta = list(keep.keys())[1]
    assert vidBeta == 'DGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni'

    # verific forces rx memos to be signed or dropped
    # to force signed tx then use Signed code
    peer = memoing.Memoer(code=GramDex.Signed, size=170, verific=True,
                          echoic=True, keep=keep, oid=oid)
    assert peer.size == 170
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.GramDex.Signed == '_-'
    assert not peer.curt
    assert peer.verific
    assert peer.echoic
    assert peer.keep == keep
    assert peer.oid == oid

    peer.reopen()
    assert peer.opened == True

    # send and receive multiple via echo
    peer.memoit("Hello there.", "alpha")
    peer.memoit("How ya doing?", "beta", vidBeta)
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
        ('Hello there.', 'alpha', oid),
        ('How ya doing?', 'beta', vidBeta)
    ])

    # test in base2 mode
    peer.curt = True
    assert peer.curt
    peer.size = 129
    assert peer.size == 129

    # send and receive multiple via echo
    peer.memoit("Hello there.", "alpha")
    peer.memoit("How ya doing?", "beta", vidBeta)
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
        ('Hello there.', 'alpha', oid),
        ('How ya doing?', 'beta', vidBeta),
        ('Hello there.', 'alpha', oid),
        ('How ya doing?', 'beta', vidBeta),
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

    oid = list(keep.keys())[0]
    assert oid == 'BG-R9L4kTXULe33Tqidn0c-W-x6xU4lIXCdhZQYrsih2'

    oidBeta = list(keep.keys())[1]
    assert oidBeta == 'DJb1Z0pHx36MCOuIHWR4yPxfIiBxVzg6UCamv8fAN8gH'

    peer = memoing.SureMemoer(echoic=True, keep=keep, oid=oid)
    assert peer.size == 65535
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.GramDex.Signed == '_-'
    assert not peer.curt
    assert peer.verific
    assert peer.echoic
    assert peer.keep == keep
    assert peer.oid == oid

    assert peer.Sizes[peer.code] == Sizage(cz=2, mz=22, oz=44, nz=4, sz=88, hz=160)
    assert peer.Sizes[peer.code] == (2, 22, 44, 4, 88, 160)  # cz mz oz nz sz hz
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
    peer.memoit(memo, dst, oidBeta)
    assert peer.txms[0] == ('Hello There', 'beta', oidBeta)

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
        ('Hello There', 'beta', oidBeta),
    ])

    # send and receive some more
    memo = "See ya later!"
    dst = "beta"
    peer.memoit(memo, dst, oidBeta)
    assert peer.txms[0] == ('See ya later!', 'beta', oidBeta)

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
        ('Hello There', 'beta', oidBeta),
        ('See ya later!', 'beta', oidBeta),
    ])

    # test binary q2 encoding of transmission gram header
    peer.curt = True  # set to binary base2
    memo = "Hello There"
    dst = "beta"
    peer.memoit(memo, dst, oidBeta)
    assert peer.txms[0] == ('Hello There', 'beta', oidBeta)

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
        ('Hello There', 'beta', oidBeta),
        ('See ya later!', 'beta', oidBeta),
        ('Hello There', 'beta', oidBeta),
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

    oid = list(keep.keys())[0]
    assert oid == 'BG-R9L4kTXULe33Tqidn0c-W-x6xU4lIXCdhZQYrsih2'

    oidBeta = list(keep.keys())[1]
    assert oidBeta == 'DJb1Z0pHx36MCOuIHWR4yPxfIiBxVzg6UCamv8fAN8gH'

    # verific forces rx memos to be signed or dropped
    # to force signed tx then use Signed code

    with memoing.openSM(size=170, echoic=True, keep=keep, oid=oid) as peer:
        assert peer.size == 170
        assert peer.name == "test"
        assert peer.opened == True
        assert peer.bc is None
        assert peer.bs == memoing.Memoer.BufSize == 65535
        assert peer.code == memoing.GramDex.Signed == '_-'
        assert not peer.curt
        assert peer.verific
        assert peer.echoic
        assert peer.keep == keep
        assert peer.oid is oid

        # send and receive multiple via echo
        peer.memoit("Hello there.", "alpha")
        peer.memoit("How ya doing?", "beta", oidBeta)
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
            ('Hello there.', 'alpha', oid),
            ('How ya doing?', 'beta', oidBeta)
        ])


        # test in base2 mode
        peer.curt = True
        assert peer.curt
        peer.size = 129
        assert peer.size == 129

        # send and receive multiple via echo
        peer.memoit("Hello there.", "alpha")
        peer.memoit("How ya doing?", "beta", oidBeta)
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
            ('Hello there.', 'alpha', oid),
            ('How ya doing?', 'beta', oidBeta),
            ('Hello there.', 'alpha', oid),
            ('How ya doing?', 'beta', oidBeta),
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

