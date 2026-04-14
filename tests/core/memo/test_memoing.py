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

from hio.hioing import MemoerError, MemoerVerifyError
from hio.help import helping
from hio.base import doing, tyming
from hio.core.memo import memoing
from hio.core.memo import (Versionage, Sizage, Keyage,
                           MemoDex, ZeroDex, GramDex, AuthDex, AckDex,
                           Memoer, AuthMemoer, openMemoer, openAM,
                           MemoerDoer, AuthMemoerDoer)


def _setupKeep(salt=None):
    """Setup Keep for signed memos

    Parameters:
        salt(str|bytes): salt used to generate key pairs and vids for keep

    Returns:
        keep (dict): labels are vids, values are keyage instances


    Ed25519_Seed: str = 'A'  # Ed25519 256 bit random seed for private key
    """
    salt = salt if salt is not None else b"abcdefghijklmnop"
    if hasattr(salt, 'encode'):
        salt = salt.encode()

    if len(salt) != 16:
        raise MemoerError(f"Invalid provided {salt=}")

    keep = {}

    # non transferable verkey as vid
    sigseed = pysodium.crypto_pwhash(outlen=32,
                                    passwd="0",
                                    salt=salt,
                                    opslimit=2,  # pysodium.crypto_pwhash_OPSLIMIT_INTERACTIVE,
                                    memlimit=67108864,  # pysodium.crypto_pwhash_MEMLIMIT_INTERACTIVE,
                                    alg=pysodium.crypto_pwhash_ALG_ARGON2ID13)
    # creates signing/verification key pair from seed
    verkey, sigkey = pysodium.crypto_sign_seed_keypair(sigseed)  # raw

    vid = Memoer._encodeVID(raw=verkey, code='B')  # make fully qualified
    qvk = Memoer._encodeQVK(raw=verkey)  # make fully qualified
    qss = Memoer._encodeQSS(raw=sigseed)  # make fully qualified
    keyage = Keyage(qvk=qvk, qss=qss)  # raw
    keep[vid] = keyage

    # transferable verkey as vid
    sigseed = pysodium.crypto_pwhash(outlen=32,
                                    passwd="1",
                                    salt=salt,
                                    opslimit=2,  # pysodium.crypto_pwhash_OPSLIMIT_INTERACTIVE,
                                    memlimit=67108864,  # pysodium.crypto_pwhash_MEMLIMIT_INTERACTIVE,
                                    alg=pysodium.crypto_pwhash_ALG_ARGON2ID13)
    # creates signing/verification key pair from seed
    verkey, sigkey = pysodium.crypto_sign_seed_keypair(sigseed)  # raw

    vid = Memoer._encodeVID(raw=verkey, code='D')  # make fully qualified
    qvk = Memoer._encodeQVK(raw=verkey)  # make fully qualified
    qss = Memoer._encodeQSS(raw=sigseed)  # make fully qualified
    keyage = Keyage(qvk=qvk, qss=qss)  # raw
    keep[vid] = keyage

    # digest of verkey as vid
    sigseed = pysodium.crypto_pwhash(outlen=32,
                                    passwd="2",
                                    salt=salt,
                                    opslimit=2,  # pysodium.crypto_pwhash_OPSLIMIT_INTERACTIVE,
                                    memlimit=67108864,  # pysodium.crypto_pwhash_MEMLIMIT_INTERACTIVE,
                                    alg=pysodium.crypto_pwhash_ALG_ARGON2ID13)
    # creates signing/verification key pair from seed
    verkey, sigkey = pysodium.crypto_sign_seed_keypair(sigseed)  # raw
    dig = digest = blake3.blake3(verkey).digest()

    vid = Memoer._encodeVID(raw=dig, code='E')
    qvk = Memoer._encodeQVK(raw=verkey)  # make fully qualified
    qss = Memoer._encodeQSS(raw=sigseed)  # make fully qualified
    keyage = Keyage(qvk=qvk, qss=qss)  # raw
    keep[vid] = keyage

    return keep


def test_memoer_class():
    """Test class attributes of Memoer class"""

    assert Memoer.Version == Versionage(major=0, minor=0)
    assert Memoer.Codex == memoing.MemoDex

    assert Memoer.Codes == \
    {
        'GramZero': '1AAQ',
        'Gram': '1AAR',
        'GramAuthZero': '1AAS',
        'GramAuth': '1AAT' ,
        'GramSureZero': '1AAU',
        'GramSure': '1AAV',
        'GramSureAuthZero': '1AAW',
        'GramSureAuth': '1AAX',
        'Ack': '1AAY',
        'AckAuth': '1AAZ',
    }

    # Codes table with sizes of code (hard) and full primitive material
    assert Memoer.Sizes == \
    {
        '1AAQ': Sizage(hz=4, mz=24, nz=4, vz=0, az=0),
        '1AAR': Sizage(hz=4, mz=24, nz=4, vz=0, az=0),
        '1AAS': Sizage(hz=4, mz=24, nz=4, vz=44,az=88),
        '1AAT': Sizage(hz=4, mz=24, nz=4, vz=0, az=88),
        '1AAU': Sizage(hz=4, mz=24, nz=4, vz=0,az=0),
        '1AAV': Sizage(hz=4, mz=24, nz=4, vz=0, az=0),
        '1AAW': Sizage(hz=4, mz=24, nz=4, vz=44, az=88),
        '1AAX': Sizage(hz=4, mz=24, nz=4, vz=0, az=88),
        '1AAY': Sizage(hz=4, mz=24, nz=4, vz=0, az=0),
        '1AAZ': Sizage(hz=4, mz=24, nz=4, vz=44, az=88),
    }
    #  verify Sizes and Codes
    for code, val in Memoer.Sizes.items():
        hz = val.hz
        mz = val.mz
        nz = val.nz
        vz = val.vz
        az = val.az

        oz = hz + mz + nz + vz + az
        assert oz and not oz % 4   # overhead size nonzero and on 24 bit boundary

        assert len(code) == hz
        assert hz == 2 or hz == 4
        assert code[0] == '_' or code[0] == '1'
        assert code[1] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz01234567890-_'
        assert oz > 0
        assert mz  # mid must not be empty
        pz = (3 - ((mz) % 3)) % 3  # net pad size for mid
        assert pz == (hz % 4)  #  combined code + mid size must lie on 24 bit boundary
        assert not vz % 4   # vid size must be on 24 bit boundary
        assert not az % 4   # sig size must be on 24 bit boundary
        assert nz and not nz % 4   # neck (num) size must be on 24 bit boundary

        if vz:
            assert az  # az must not be empty if vz not empty

    assert Memoer.Names == \
    {
        '1AAQ': 'GramZero',
        '1AAR': 'Gram',
        '1AAS': 'GramAuthZero',
        '1AAT': 'GramAuth',
        '1AAU': 'GramSureZero',
        '1AAV': 'GramSure',
        '1AAW': 'GramSureAuthZero',
        '1AAX': 'GramSureAuth',
        '1AAY': 'Ack',
        '1AAZ': 'AckAuth',
    }

    assert Memoer.Zedex == ZeroDex
    assert Memoer.Audex == AuthDex

    for zero, nonzero in Memoer.Pairs.items():
        assert zero in ZeroDex
        assert nonzero in GramDex

    zdex = list(ZeroDex)  # astuple
    gdex = list(GramDex)  # astuple
    keys = list(Memoer.Pairs.keys())
    vals = list(Memoer.Pairs.values())
    for i, zero in enumerate(zdex):
        assert zdex[i] == keys[i] == zero
    for i, gram in enumerate(gdex):
        assert gdex[i] == vals[i] == gram

    assert Memoer.Pairs[MemoDex.GramZero] == MemoDex.Gram
    assert Memoer.Pairs[MemoDex.GramAuthZero] == MemoDex.GramAuth
    assert Memoer.Pairs[MemoDex.GramSureZero] == MemoDex.GramSure
    assert Memoer.Pairs[MemoDex.GramSureAuthZero] == MemoDex.GramSureAuth

    # Base2 Binary index representation of Text Base64 Char Codes
    #assert Memoer.Bodes == {b'\xff\xf0': '__', b'\xff\xe0': '_-'}

    assert Memoer.MaxMemoSize == ((2**30-1)*4+8)  # absolute max memo payload size
    assert Memoer.MaxGramSize == (2**16-1)  # absolute max gram size
    assert Memoer.MaxGramCount == (2**24-1)  # absolute max gram count
    assert Memoer.BufSize == (2**16-1) # default buffersize

    verkey = (b"o\x91\xf4\xbe$Mu\x0b{}\xd3\xaa'g\xd1\xcf\x96\xfb\x1e\xb1S\x89H\\'ae\x06+\xb2(v")
    vid = Memoer._encodeVID(raw=verkey)
    assert vid == 'BG-R9L4kTXULe33Tqidn0c-W-x6xU4lIXCdhZQYrsih2'
    raw, code = Memoer._decodeVID(vid)
    assert raw == verkey
    assert code == 'B'  # nontrans AID
    _, _, _, vz, _ = Memoer.Sizes[MemoDex.GramAuthZero]  # hz mz nz vz az
    assert len(vid) == 44 == vz

    qvk = Memoer._encodeQVK(raw=verkey)
    assert qvk == 'BG-R9L4kTXULe33Tqidn0c-W-x6xU4lIXCdhZQYrsih2'
    raw, code = Memoer._decodeQVK(vid)
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
    sgntr = Memoer._encodeSGN(raw=signature)
    assert sgntr == '0BCwwNUJoNNRMPo4k0IMg7Uu-0il3r99NnvPfKMObCKEZtNzYkhDubmFsNJ27QfPfGOk1txFvop7dzU9v4RfnrME'
    raw, code = Memoer._decodeSGN(sgntr)
    assert raw == signature
    assert code == '0B'
    _, _, _, _, az = Memoer.Sizes[MemoDex.GramAuthZero]  # hz mz nz vz az
    assert len(sgntr) == 88 == az

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


def test_memoer_sign_verify():
    """Test Memoer class sign and verify methods
    """
    salt = b"ABCDEFGHIJKLMNOP"
    try:
        keep = _setupKeep(salt=salt)
    except MemoerError as ex:
        return

    mid = Memoer.makeMID()  # test class method
    assert len(mid) == 24
    assert mid[:2] == '0A'

    # default vid
    vid = list(keep.keys())[0]
    assert vid == 'BJZTHNWXscuT-SPokPzSeBkShpHj6g8bQrP0Rh7IJNUp'
    code = MemoDex.GramAuthZero

    peer = Memoer(code=code, keep=keep, vid=vid)
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == Memoer.BufSize == 65535
    assert peer.code == MemoDex.GramAuthZero == '1AAS'
    assert not peer.curt
    assert peer.Sizes[peer.code] == (4, 24, 4, 44, 88)  # hz mz nz vz az
    assert peer.size == peer.MaxGramSize
    assert not peer.authic
    assert not peer.echoic
    assert peer.keep == keep
    assert peer.vid == vid

    # manually generate memogram
    mid = '0AD5s502N14R8bWw8qyvRW-S'  # hard code here for test
    gcnt = 'AAAB' # gram count 1
    # serder vid
    vid = 'DGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni'   # not default .vid
    assert vid in peer.keep
    head = code + mid + gcnt + vid
    assert head == '1AAS0AD5s502N14R8bWw8qyvRW-SAAABDGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni'

    memo = "Hello There"  # body

    sgram = (head + memo).encode()
    #sign
    sgntr = peer.sign(vid, sgram)
    #verify
    assert peer.verify(vid, sgntr, sgram)

    gram = head + memo + sgntr.decode()
    assert gram == ('1AAS0AD5s502N14R8bWw8qyvRW-SAAABDGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni'
                    'Hello There'
                    '0BBvO2SHplT7vjLMvcKU5s11d4lt_KVg0zbzZDiaRZ9jQhEZhPxqSo71DQSnk5YTpZphbooVW14sea2UL2DT_aMB')

    # test invalid  bad gram
    bgram = (head + "Hello Where").encode()
    with pytest.raises(MemoerVerifyError):
        peer.verify(vid, sgntr, bgram)

    """Done"""



def test_memoer_basic():
    """Test Memoer class basic
    """
    peer = Memoer()
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == Memoer.BufSize == 65535
    assert peer.code == MemoDex.GramZero == '1AAQ'
    assert not peer.curt
    assert peer.Sizes[peer.code] == (4, 24, 4, 0, 0)  # hz mz nz vz az
    assert peer.size == peer.MaxGramSize
    assert not peer.authic
    assert not peer.echoic
    assert peer.keep == dict()
    assert peer.vid is None

    assert peer.tymeout == 0.0
    assert peer.tymers == {}

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

    code = '1AAQ'
    mid = '0AD5s502N14R8bWw8qyvRW-S'  # hard code here for test
    gram = (code + mid + 'AAAB' + "Hello There").encode()
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

    code = '1AAQ'
    mid = '0AD5s502N14R8bWw8qyvRW-S'  # hard code here for test
    head = decodeB64((code + mid + 'AAAB').encode())  # base 2
    gram = head + b"Hello There"
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
    assert peer.code == memoing.MemoDex.GramZero == '1AAQ'
    assert not peer.curt
    assert peer.Sizes[peer.code] == (4, 24, 4, 0, 0)  # hz mz nz vz az
    assert peer.size == 33  # overhead + 1 is minimum size
    assert not peer.authic
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


    code = '1AAQ'
    mid = '0AD5s502N14R8bWw8qyvRW-S'  # hard code here for test
    gcnt = 'AAAC'  # 2
    gram = (code + mid + gcnt + "Hello ").encode()
    assert len(gram) == peer.size == 38
    echo = (gram, "beta")
    peer.echos.append(echo)

    code = '1AAR'
    gnum = 'AAAB'  # 1
    gram =  (code + mid + gnum + "There").encode()
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
    assert len(peer.txgs) == 3
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
    assert len(peer.rxgs[mid]) == 3
    assert peer.counts[mid] == 3
    assert peer.sources[mid] == 'beta'
    assert peer.rxgs[mid][0] == bytearray(b'See ya')
    assert peer.rxgs[mid][1] == bytearray(b' later')
    assert peer.rxgs[mid][2] == bytearray(b'!')
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
    assert len(peer.txgs) == 3
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

    code = '1AAQ'
    mid = '0AD5s502N14R8bWw8qyvRW-S'  # hard code here for test
    gcnt = 'AAAC'  # 2
    head = decodeB64((code + mid + gcnt).encode())  # base 2
    gram = head + b"See ya later a"
    assert len(gram) == peer.size == 38
    assert peer.wiff(gram)  # base2
    echo = (gram, "beta")
    peer.echos.append(echo)

    code = '1AAR'
    gnum = 'AAAB'  # 1
    head = decodeB64((code + mid + gnum).encode())
    gram = head + b"lligator!"
    assert len(gram) == 33
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
    peer = Memoer(size=38)
    assert peer.size == 38
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == Memoer.BufSize == 65535
    assert peer.code == MemoDex.GramZero == '1AAQ'
    assert not peer.curt
    assert not peer.authic
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
    assert len(peer.txgs) == 5
    for m, d in peer.txgs:
        assert not peer.wiff(m)  # base64
        assert d in ("alpha", "beta")
    peer.serviceTxGrams(echoic=True)
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert len(peer.echos) == 5
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
    assert peer.counts[mid] == 3
    assert len(peer.rxgs[mid]) == 3
    assert peer.rxgs[mid][0] == bytearray(b'How ya')
    assert peer.rxgs[mid][1] == bytearray(b' doing')
    assert peer.rxgs[mid][2] == bytearray(b'?')

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
    assert peer.code == memoing.MemoDex.GramZero == '1AAQ'
    assert not peer.curt
    assert not peer.authic
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
    assert len(peer.echos) == 5

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
    assert peer.code == memoing.MemoDex.GramZero == '1AAQ'
    assert not peer.curt
    assert not peer.authic
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
    assert len(peer.echos) == 5  # Rx not serviced yet after Tx serviced

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

    vid = list(keep.keys())[0]
    assert vid == 'BJZTHNWXscuT-SPokPzSeBkShpHj6g8bQrP0Rh7IJNUp'

    peer = Memoer(code=MemoDex.GramAuthZero, keep=keep, vid=vid)
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.MemoDex.GramAuthZero == '1AAS'
    assert not peer.curt
    assert peer.Sizes[peer.code] == (4, 24, 4, 44, 88)  # hz mz nz vz az
    assert peer.size == peer.MaxGramSize
    assert not peer.authic
    assert not peer.echoic
    assert peer.keep == keep
    assert peer.vid == vid

    peer.reopen()
    assert peer.opened == True

    assert not peer.txms
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    peer.service()
    assert peer.txbs == (b'', None)

    memo = "Hello There"
    dst = "beta"

    vid = 'DGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni'   # not default .vid
    peer.memoit(memo, dst, vid)
    assert peer.txms[0] == ('Hello There', 'beta', vid)
    peer.serviceTxMemos()
    assert not peer.txms
    g, d = peer.txgs[0]
    assert not peer.wiff(g)  # base64
    assert g.find(memo.encode()) != -1
    assert len(g) == 160 + 4 + len(memo)
    assert g[:4].decode() == MemoDex.GramAuthZero
    assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms

    # Test with signed header
    code = '1AAS'
    mid = '0AD5s502N14R8bWw8qyvRW-S'  # hard code here for test
    gcnt = 'AAAB'  # 1
    head = (code + mid + gcnt + vid).encode()
    sgram = head + b"Hello There"
    assert len(sgram) == 87
    assert not peer.wiff(sgram)  # base64

    # test with invalid signature
    sig = (b'A' * 88)
    gram = sgram + sig
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert not peer.echos
    assert not peer.rxgs  # drops message

    # test with valid signature
    # create signed portion of gram
    qvk, qss = peer.keep[vid]
    sig = peer.sign(vid, sgram)
    gram = sgram + sig
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
    vid = 'DGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni'   # not default .vid
    peer.memoit(memo, dst, vid)
    assert peer.txms[0] == ('See ya later!', 'beta', vid)
    peer.serviceTxMemos()
    assert not peer.txms
    g, d = peer.txgs[0]
    assert not peer.wiff(g)  # base64
    assert g.find(memo.encode()) != -1
    assert len(g) == 160 + 4 + len(memo)
    assert g[:4].decode() == MemoDex.GramAuthZero
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
    vid = 'DGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni'   # not default .vid
    peer.memoit(memo, dst, vid)
    assert peer.txms[0] == ('Hello There', 'beta', vid)
    peer.serviceTxMemos()
    assert not peer.txms
    g, d = peer.txgs[0]
    assert peer.wiff(g)  # base2
    assert g.find(memo.encode()) != -1
    assert len(g) == 3 * (160 + 4) // 4 + len(memo)
    assert helping.codeB2ToB64(g, 4) == MemoDex.GramAuthZero
    assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms

    # test with signed header
    code = '1AAS'
    mid = '0AD5s502N14R8bWw8qyvRW-S'  # hard code here for test
    gcnt = 'AAAB'  # 1
    # test with valid signature
    vid = 'DGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni'   # not default .vid
    head = (code + mid + gcnt + vid).encode()

    assert len(head) == 76
    head = decodeB64(head)  # qb2 version of head
    assert len(head) == 57
    sgram = head + memo.encode()  # sign the qb2 version
    assert len(sgram) == 68
    assert peer.curt
    qvk, qss = peer.keep[vid]
    tail = peer.sign(vid, sgram)  # returns sig in qb2 becaue .curt
    assert len(tail) == 66
    gram = head + memo.encode() + tail # qb2 version

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

    vid = list(keep.keys())[0]
    assert vid == 'BJZTHNWXscuT-SPokPzSeBkShpHj6g8bQrP0Rh7IJNUp'

    vidBeta = list(keep.keys())[1]
    assert vidBeta == 'DGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni'

    peer = Memoer(code=MemoDex.GramAuthZero, size=170, keep=keep, vid=vid)
    assert peer.size == 170
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.MemoDex.GramAuthZero == '1AAS'
    assert not peer.curt
    assert not peer.authic  # force rx must be signed
    assert not peer.echoic
    assert peer.keep == keep
    assert peer.vid == vid

    peer.reopen()
    assert peer.opened == True

    # send and receive multiple via echo signed
    peer.memoit("Hello there.", "alpha")  # use default for vidAlpha
    peer.memoit("How ya doing?", "beta", vidBeta)
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
    assert peer.rxms[1] == ('How ya doing?', 'beta', vidBeta)
    peer.serviceRxMemos()
    assert not peer.rxms

    # test in base2 mode
    peer.curt = True
    assert peer.curt
    peer.size = 129
    assert peer.size == 129

    # send and receive multiple via echo in base2 .curt = True mode
    peer.memoit("Hello there.", "alpha")  # use default for vidAlpha
    peer.memoit("How ya doing?", "beta", vidBeta)
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
    assert peer.rxms[1] == ('How ya doing?', 'beta', vidBeta)
    peer.serviceRxMemos()
    assert not peer.rxms

    assert peer.inbox == deque(
    [
        ('Hello there.', 'alpha', vid),
        ('How ya doing?', 'beta', vidBeta),
        ('Hello there.', 'alpha', vid),
        ('How ya doing?', 'beta', vidBeta)
    ])


    peer.close()
    assert peer.opened == False
    """ End Test """


def test_memoer_authic():
    """Test Memoer class with authic (signed required)
    """
    salt = b"ABCDEFGHIJKLMNOP"
    try:
        keep = _setupKeep(salt=salt)
    except MemoerError as ex:
        return

    vid = list(keep.keys())[0]
    assert vid == 'BJZTHNWXscuT-SPokPzSeBkShpHj6g8bQrP0Rh7IJNUp'

    peer = Memoer(authic=True, keep=keep, vid=vid)  # only recieves not send signed
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.MemoDex.GramZero == '1AAQ'
    assert not peer.curt
    assert peer.Sizes[peer.code] == (4, 24, 4, 0, 0)  # hz mz nz vz az
    assert peer.size == peer.MaxGramSize
    assert peer.authic
    assert not peer.echoic
    assert peer.keep == keep
    assert peer.vid is vid

    peer.reopen()
    assert peer.opened == True

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms

    # send non-signed memo to authic memoer
    code = '1AAQ'
    mid = '0AD5s502N14R8bWw8qyvRW-S'  # hard code here for test
    gcnt = 'AAAB'  # 1
    head = (code + mid + gcnt).encode()

    gram = head + "Hello There".encode()
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert not peer.rxgs  # dropped gram because not signed
    assert not peer.echos
    assert not peer.rxms

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms

    code = '1AAS'  # signed gram
    mid = '0AD5s502N14R8bWw8qyvRW-S'  # hard code here for test
    gcnt = 'AAAB'  # 1
    vid = list(keep.keys())[1]
    head = (code + mid + gcnt + vid).encode()
    sgram = head + "Hello There".encode()
    qvk, qss = peer.keep[vid]
    sig = peer.sign(vid, sgram)
    gram = sgram + sig
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

    vid = list(keep.keys())[0]
    assert vid == 'BJZTHNWXscuT-SPokPzSeBkShpHj6g8bQrP0Rh7IJNUp'

    vidBeta = list(keep.keys())[1]
    assert vidBeta == 'DGORBFFJe5Zj4T1FQHpRFSe41hQuq8HULAMWyc9C07ni'

    # authic forces rx memos to be signed or dropped
    # to force signed tx then use Signed code
    peer = Memoer(code=MemoDex.GramAuthZero, size=170, authic=True,
                          echoic=True, keep=keep, vid=vid)
    assert peer.size == 170
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.MemoDex.GramAuthZero == '1AAS'
    assert not peer.curt
    assert peer.authic
    assert peer.echoic
    assert peer.keep == keep
    assert peer.vid == vid

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
        ('Hello there.', 'alpha', vid),
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
        ('Hello there.', 'alpha', vid),
        ('How ya doing?', 'beta', vidBeta),
        ('Hello there.', 'alpha', vid),
        ('How ya doing?', 'beta', vidBeta),
    ])

    peer.inbox = deque()  # clear it

    peer.close()
    assert peer.opened == False
    """ End Test """


def test_open_memoer():
    """Test contextmanager decorator openMemoer
    """
    with (openMemoer(name='zeta') as zeta):

        assert zeta.opened
        assert zeta.name == 'zeta'
        assert zeta.tymeout == 0.0
        assert zeta.tymers == {}


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

    peer = Memoer()

    mgdoer = memoing.MemoerDoer(peer=peer)
    assert mgdoer.peer == peer
    assert not mgdoer.peer.opened
    assert mgdoer.tock == 0.0  # ASAP

    doers = [mgdoer]
    doist.do(doers=doers)
    assert doist.tyme == limit
    assert mgdoer.peer.opened == False

    """End Test """



def test_auth_memoer_basic():
    """Test AuthMemoer class basic
    """
    try:
        keep = _setupKeep()  # uses default salt
    except MemoerError as ex:
        return

    vid = list(keep.keys())[0]
    assert vid == 'BG-R9L4kTXULe33Tqidn0c-W-x6xU4lIXCdhZQYrsih2'

    oidBeta = list(keep.keys())[1]
    assert oidBeta == 'DJb1Z0pHx36MCOuIHWR4yPxfIiBxVzg6UCamv8fAN8gH'

    peer = AuthMemoer(echoic=True, keep=keep, vid=vid)
    assert peer.size == 65535
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc is None
    assert peer.bs == memoing.Memoer.BufSize == 65535
    assert peer.code == memoing.MemoDex.GramAuthZero == '1AAS'
    assert not peer.curt
    assert peer.authic
    assert peer.echoic
    assert peer.keep == keep
    assert peer.vid == vid

    assert peer.Sizes[peer.code] == Sizage(hz=4, mz=24, nz=4, vz=44, az=88)
    assert peer.Sizes[peer.code] == (4, 24, 4, 44, 88)  # hz mz nz vz az
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

    with (openAM(name='zeta') as zeta):

        assert zeta.opened
        assert zeta.name == 'zeta'
        assert zeta.tymeout == 0.0
        assert zeta.tymers == {}


    assert not zeta.opened

    """ End Test """


def test_auth_memoer_multiple_echoic_service_all():
    """Test AuthMemoer class with small gram size and multiple queued memos signed
    using echos for transport
    """
    try:
        keep = _setupKeep()  # uses default salt
    except MemoerError as ex:
        return

    vid = list(keep.keys())[0]
    assert vid == 'BG-R9L4kTXULe33Tqidn0c-W-x6xU4lIXCdhZQYrsih2'

    oidBeta = list(keep.keys())[1]
    assert oidBeta == 'DJb1Z0pHx36MCOuIHWR4yPxfIiBxVzg6UCamv8fAN8gH'

    # authic forces rx memos to be authenticated/signed or dropped
    # to force signed tx then use Auth type header code

    with memoing.openAM(size=170, echoic=True, keep=keep, vid=vid) as peer:
        assert peer.size == 170
        assert peer.name == "test"
        assert peer.opened == True
        assert peer.bc is None
        assert peer.bs == Memoer.BufSize == 65535
        assert peer.code == MemoDex.GramAuthZero == '1AAS'
        assert not peer.curt
        assert peer.authic
        assert peer.echoic
        assert peer.keep == keep
        assert peer.vid is vid

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
            ('Hello there.', 'alpha', vid),
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
            ('Hello there.', 'alpha', vid),
            ('How ya doing?', 'beta', oidBeta),
            ('Hello there.', 'alpha', vid),
            ('How ya doing?', 'beta', oidBeta),
        ])

        peer.inbox = deque()  # clear it

    assert peer.opened == False
    """ End Test """


def test_auth_memoer_doer():
    """Test AuthMemoerDoer class
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

    peer = AuthMemoer()

    tmgdoer = AuthMemoerDoer(peer=peer)
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
    test_memoer_sign_verify()
    test_memoer_basic()
    test_memoer_small_gram_size()
    test_memoer_multiple()
    test_memoer_multiple_echoic_service_tx_rx()
    test_memoer_multiple_echoic_service_all()
    test_memoer_basic_signed()
    test_memoer_multiple_signed()
    test_memoer_authic()
    test_memoer_multiple_signed_verific_echoic_service_all()
    test_open_memoer()
    test_memoer_doer()
    test_auth_memoer_basic()
    test_open_sm()
    test_auth_memoer_multiple_echoic_service_all()
    test_auth_memoer_doer()

