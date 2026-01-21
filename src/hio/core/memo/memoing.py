# -*- encoding: utf-8 -*-
"""
hio.core.memoing Module

Mixin Base Classes that add support for  memograms over datagram based transports.
In this context, a memo made is a larger message that is partitioned into
smaller memograms parts that fit into transport specific datagrams.
This allows larger messages (memos) to be transported over datagram transports
which messages are larger than  a single datagram in the underlying transport.
"""

import socket
import errno
import math
import uuid
#import struct

from collections import deque, namedtuple
from contextlib import contextmanager
from base64 import urlsafe_b64encode as encodeB64
from base64 import urlsafe_b64decode as decodeB64
from dataclasses import dataclass, astuple, asdict

import pysodium

from ... import hioing, help
from ...base import tyming, doing
from ...base.tyming import Tymer, Tymee
from ...help import helping

logger = help.ogler.getLogger()

# namedtuple of ints (major: int, minor: int)
Versionage = namedtuple("Versionage", "major minor")

# signature key pair:
#    qvk = qualified base64 public verifying key
#    qss = qualified base64 private signing key seed (ed25519 sigkey = sigseed + verkey)
Keyage = namedtuple("Keyage", "qvk qss")
# example usage
#keyage = Keyage(qvk="xyy", qss="abc", )
#keep = dict("ABCXYZ"=keyage)  # qualified oid as label, Keyage instance as value

"""Design Discusssion of Memo and Gram Sizing and Encoding:

Each GramCode (tv) Typing/Version code uses a base64 two char code.
Codes always start with `_` and second char in code starts at `_`
and walks backwards through B64 code table for each gram type-version (tv) code.

tv 0 is '__'
tv 1 is '_-'
tv 3 is '_9'
...

Each of total head length including code and total neck length must be a
multiple of 4 characters (3 bytes) to align on 24 bit boundary for clean Base64
round tripping.  This ensure each converts to/from B2 without padding.
Head type-version code governs the neck as well. So whenever  field lengths or
fields change in any way we need a new gram (tv) code.

To reiterate, if ever need to change anything need a new gram (tv) code. There are
no versions per type.  This is deemed sufficient because we anticipate a very
limited set of possible fields ever needed for memogram transport types.

All gram head and neck fields are mid-pad B64 primitives. This makes for stable
coding at fron and back of head neck parts. This also means that gram parts can
can be losslessly transformed to/from equivalent CESR primitives merely by
translating the gram tv code to an equivalent entry in the  two char cesr
primitive code table. When doing so the neck is always attached and then
stripped when not needed.

The equivalent CESR codes, albeit different, map one-to-one to the gram tv codes.
This enables representing headers as CESR primitives for management but not
over the wire. One can transform Memogram Grams to CESR primitives to tunnel in
some CESR stream.

Normally CESR streams are tunneled inside Memoer memograms sent over-the-wire.
In this case, the memogram is the wrapper and each gram uses the gram TV code
defined herein not the equivalent CESR code.
Using  so far reserved and unused '_' code which is reserved as the selector
for the CESR op code table for memogram grams makes it more apparent that a gram
belongs to a memogram and not a CESR stream.
Eventually when CESR op codes eventually become defined, it's not likely to be
confusing since the context of CESR op codes is dramatically different from
transport wrappers.

Morover when a MemoGram payload is a tunneled CESR Stream, the memogram parser
will parse and strip the MemoGram gram wrappers to construct the tunneled,
stream so the wrapper is transarent to the CESR stream and the CESR stream
payload is opaque to the memogram wrapper, i.e. no ambiguity.

Gram Header Fields:
    HeadCode hc = b'__'
    HeadCodeSize hcs = 2
    MemoIDSize mis = 22
    GramNumSize gns = 4
    GramCntSize gcs = 4
    GramHeadSize ghs  = 28
    GramHeadNeckSize ghns = 28 + 4 = 32

Sizing:

We have for most datagrams, such as UDP, a max datagram size of 65535 = (2 ** 16 -1)
Thix may no longer be true on some OSes for UXD datagrams. On some OSes UXD datagrams
may be bigger. But 65535 seems like a good practical limit for maximum compatibility
across all datagram types.

Given gram count and gram num fields are 4 Base64 chars (3 bytes) or 24 bits, then:
MaxGramCount = 2**24-1

If we want a maximally size memo to be big enough to transport 1 CESR Big frame
with frame counter then the maximum memo size needs to be
(2**30-1) * 4 + 8 = 4294967292 + 8 = 4294967300

CESR groups code count in quadlets (4 chars).
The big group count codes have five digits of 6 bits each or 30 bits to count the
size of the following framed chars.
The maximum group count is (2**30-1) == 1073741823
Cesr group codes count the number
of quadlets (4 chars) in the framed group. The maximum number of bytes in a
CESR big group frame body is therefore:
(2**30-1)*4 = 1073741823 * 4 = 4294967292.
The group code itself is not included in the counted quadlets in the frame body.
The big group codes are 8 chars long. Thus with its group code the total big
frame size is:
(2**30-1)*4 + 8 = 4294967292 + 8 = 4294967300

We set
MaxMemoSize (mms) = (2**30-1)*4+8 = 4294967300

We can compare UDP and UXD given these constraints.
Notice that gramsize includes head + body and the first gram size is 4 larger
to include gram count field.

In general
MaxMemoSize = GramBodySize * MaxGramCount

Because the gram count field is 24 bits (4 chars or 3 bytes), we have:
MaxGramCount = 2**24-1 = 16777215

At a MaxGramCount of 16777215 for the MaxMemoSize  we
GramBodySize = MaxMemoSize / MaxGramCount = 4294967300/16777215 = 256 remainder 260
256 = 2**8.  So we need GramBodySize to be a little larger than 256 to reach
MaxMemoSize.  If we round up to 257 we get
maximum possible memosize = 257 * 16777215 = 4311744255 = ((2**8)+1)*(2**24-1)
Or alternatively if we set GramBodySize to 257 then the max gram count we get is
GramCount = ceil(MaxMemoSize / 257) = (ceil(4294967300/257)) = 16711936 < 16777215
or 4294967300/257 = 16711935 remainder 5

An actual Gram includes a GramHead + GramBody. So as long as the transport MTU
is at least as big as the GramHeadSize + GramBodySize then we can transport the maximum
memo size in MaxGramCount grams.

The signed header for a gram is 160 bytes for all grams but the zeroth gram.
the zeroth gram includes an extra 4 bytes for the gramcount or 164 bytes.

UDP IPV4 MTU = 576  Net safe payload = gram size = 548
MaxGramCount for UDP GramSize of 548.  Given signed header, GramBodySize is
548 - 160 = 388 which is larger than 257. So a memo of MaxMemoSize of 4294967300
can be conveyed in IPV4 datagrams with fewer than MaxGramCount grams.
This provides headroom for the extra 4 bytes in the zeroth gram.

UXD MTU is typically 65535 depending on the allocated buffer size which is much
greater than 257.


MinGramSize = MaxMemoSize // MaxGramCount = ceil(((2**30-1)*4+8 ) / (2**24-1)) = 257 = (2**8+1)
This is the min size that could result in maxMemoSize. Smaller gram sizes than 257
can not reach MaxMemoSize because MaxGramCount not big enough.
Based on datagram constraints we have
MaxGramSize = (2**16-1)


The variables ghs, and ghns are fixed for given transport service type reliable
or unreliable with head and neck fields defined appropriately
The variables gs, gbs,and mms are derived from transport MTU size
The desired gs for a given transport MTU instance may be smaller than the allowed
maximum to accomodate buffers etc.
Given the fixed gram head size for service type, ghs one can calculate the
maximum memo size mms that includes the header overhead given the contraint of
no more than 2**24-1 grams in a given memo due to 24 size of gram count gram num.

So for a given transport:
gs = min(gs, 2**16-1)  (gram size)
gbs = gs - ghs  (gram body size = gram size - gram head size)

mms = min((2**30-1)*4+8, gbs * (2**24-1))  (max memo size)
So compare memo size to mms and if greater raise error and drop memo
otherwise partition (gram) memo into grams with headers and transmit


Therefore setting the maxmemosize to be (2**30-1)*4+8 enables the a big group
frame from CESR to be conveyed by a memo.
However a maximally sized memo can not be itself conveyed by a big CESR group frame
because maximally size memo is 8 more than the biggest frame body count.
So translating memos to CESR must check that the memo  being translated iself
is limited to a size of (2**30-1)*4 not (2**30-1)*4+8

"""

"""Sizage: namedtuple for gram header part size entries in Memoer code tables
cz is the serialization code part size int number of chars in code part
mz is the mid (memo ID) part size int number of chars in the mid part
oz is the oid (origin ID) part size int number of chars in the oid part
nz is the neck part size int number of chars for the gram number in all grams
      it is also the size of the gram count that only appears in the zeroth gram
      The zeroth gram has a long neck consiting of two nz sized fields
      All other grams have ashort neck consisting of 1 nz sized field
sz is the signature part size int number of chars in the signature part
      the signature part is discontinuously attached after the body part but
      its size is included in the overhead size computation for the body size
hz is the head (header) size int number of chars
      head with short neck
        hz = cz + mz + oz + nz + sz
      zeroth head with long neck is calculated from short neck head
        zhz = hz + nz
"""
Sizage = namedtuple("Sizage", "cz mz oz nz sz hz")

@dataclass(frozen=True)
class GramCodex:
    """
    GramCodex is codex of all Gram Codes.
    Only provide defined codes.
    Undefined are left out so that inclusion(exclusion) via 'in' operator works.
    """
    Basic:     str = '__'  # Basic gram code for basic overhead parts
    Signed:    str = '_-'  # Basic gram code for signed overhead parts

    def __iter__(self):
        return iter(astuple(self))


GramDex = GramCodex()  # Make instance

@dataclass(frozen=True)
class SignGramCodex:
    """
    SignGramCodex is codex of all Signed Gram Codes.
    Only provide defined codes.
    Undefined are left out so that inclusion(exclusion) via 'in' operator works.
    """
    Signed:    str = '_-'  # Basic gram code for signed overhead parts

    def __iter__(self):
        return iter(astuple(self))


SGDex = SignGramCodex()  # Make instance


class Memoer(hioing.Mixin):
    """Memoer mixin base class to adds memogram support to a transport class.
    Memoer supports memos composed of asynchronous memograms.
    Provides common methods for subclasses.

    A memogram is a higher level construct that sits on top of a datagram transport.
    A memogram supports the segmentation and desegmentation of memos to
    respect the underlying datagram size, buffer, and fragmentation behavior.

    Layering a reliable transaction protocol for memos on top of a memogram
    transport enables reliable asynchronous messaging over unreliable datagram
    transport protocols.

    When the datagram protocol is already reliable, then a memogram transport enables
    larger memos (messages) than that natively supported by the datagram.

    Usage:
        Do not instantiate directly but use as a mixin with a transport class
        in order to create a new subclass that adds memogram support to the
        datagram transport class. For example MemoerUdp or MemoerUxd

    Each direction of dataflow uses a tiered set of buffers that respect
    the constraints of non-blocking asynchronous IO with datagram transports.

    On the transmit side memos are placed in a memo deque (double ended queue).
    Each memo is then segmented into grams (memograms) that respect the size constraints
    of the underlying datagram transport. These grams are placed in the outgoing
    gram deque. Each entry in this deque is a duple of form:
    (gram: bytes, dst: str). Each  duple is pulled off the self._serviceOneRxMemo()deque and its
    gram is put in bytearray for transport.

    memo -> .txms deque -> rend -> grams -> .txgs deque -> send -> .txbs

    On the receive side each complete memogram (gram) is put in a gram receive
    deque as a memogram (datagram sized) segment of a memo.
    These deques are indexed by the sender's source addr.
    The grams in the gram recieve deque are then desegmented into a memo
    and placed in the memo deque for consumption by the application or some other
    higher level protocol.

    receive -> (gram, src) -> grams parsed to .rxgs  .counts .oids .sources ->
    signing key pair sigkey and verifier key ->
           fuse -> memo .rxms deque

    When using non-blocking IO, asynchronous datagram transport
    protocols may have hidden buffering constraints that result in fragmentation
    of the sent datagram which means the whole datagram is not sent at once via
    a non-blocking send call. This means that the remainer of the datagram must
    be sent later and may take multiple send calls to complete. The datagram
    protocol is responsible for managing the buffering and fragmentation but
    depends on the sender repeated attempts to send the reaminder of the
    full datagram. This is ensured with the final tier with a raw transmit
    buffer that waits until it is empty before attempting to send another
    gram. Because sending to different destinations may fail for different reasons
    such as bad addresses or bad routing each destination gets its own buffer
    so that a bad destination does not block other destinations.

    Memo segmentation/desegmentation information is embedded in the grams.

    Inherited Class Attributes:
        MaxGramSize (int): absolute max gram size on tx with overhead, override
                           in subclass

    Class Attributes:
        Version (Versionage): default version consisting of namedtuple of form
            (major: int, minor: int)
        Codex (GramDex): dataclass ref to gram codex
        Codes (dict): maps codex names to codex values
        Names (dict): maps codex values to codex names
        Sodex (SGDex): dataclass ref to signed gram codex
        Sizes (dict): gram head part sizes Sizage instances keyed by gram codes
        MaxMemoSize (int): absolute max memo size
        MaxGramCount (int): absolute max gram count
        BufSize (int): used to set default buffer size for transport datagram buffers


    Stubbed Attributes:
        name (str):  unique name for Memoer transport.
                     Used to manage multiple instances.
        opened (bool):  True means transport open for use
                        False otherwise
        bc (int|None): count of transport buffers of MaxGramSize
        bs (int|None): buffer size of transport buffers. When .bc is provided
                then .bs is calculated by multiplying, .bs = .bc * .MaxGramSize.
                When .bc is not provided, then if .bs is provided use provided
                value else use default .BufSize

    Stubbed Methods:
        send(gram, dst, *, echoic=False) -> int  # send gram over transport to dst
        receive(self, *, echoic=False) -> (bytes, str|tuple|None)  # receive gram

    Attributes:
        version (Versionage): version for this memoir instance consisting of
                namedtuple of form (major: int, minor: int)
        rxgs (dict): keyed by mid (memoID) with value of dict where each
                value dict holds grams from memo keyed by gram number.
                Grams have been stripped of their headers.
                The mid appears in every gram from the same memo.
        sources (dict): keyed by mid (memoID) that holds the src for the memo.
            This enables reattaching src to fused memo in rxms deque tuple.
        counts (dict): keyed by mid (memoID) that holds the gram count from
            the first gram for the memo. This enables lookup of the gram count when
            fusing its grams.
        oids (dict[mid: (oid | None)]): keyed by mid that holds the origin ID str for
                the memo indexed by its mid (memoID). This enables reattaching
                the oid to memo when placing fused memo in rxms deque.
                oid is only present when signed header otherwise oid is None
        rxms (deque): holding rx (receive) memo tuples desegmented from rxgs grams
                each entry in deque is tuple of form:
                (memo: str, src: str, oid: str) where:
                memo is fused memo, src is source addr, oid is origin ID
        txms (deque): holding tx (transmit) memo tuples to be segmented into
                txgs grams where each entry in deque is tuple of form
                (memo: str, dst: str, oid: str | None)
                memo is memo to be partitioned into gram
                dst is dst addr for grams
                oid is origin id when gram is to be signed or None otherwise
        txgs (deque): grams to transmit, each entry is duple of form:
                (gram: bytes, dst: str).
        txbs (tuple): current transmisstion duple of form:
            (gram: bytearray, dst: str). gram bytearray may hold untransmitted
            portion when Encodesdatagram is not able to be sent all at once so can
            keep trying. Nothing to send indicated by (bytearray(), None)
            for (gram, dst)
        echos (deque): holds echo receive duples for testing. Each duple of
                       form: (gram: bytes, dst: str).
        inbox (deque): holds final received complete memos for testing when not
                       overridden in subclass to further process otherwise

    Properties:
        code (bytes | None): gram code for gram header when rending for tx
        curt (bool): True means when rending for tx encode header in base2
                     False means when rending for tx encode header in base64
        size (int): gram size when rending for tx.
            first gram size = over head size + neck size + body size.
            other gram size = over head size + body size.
            Min gram body size is one.
            Gram size also limited by MaxGramSize and MaxGramCount relative to
            MaxMemoSize.
        verific (bool): True means any rx grams must be signed.
                        False otherwise
        echoic (bool): True means use .echos in .send and .receive to mock the
                            transport layer for testing and debugging.
                       False means do not use .echos
                       Each entry in .echos is a duple of form:
                           (gram: bytes, src: str)# singing key pair sigkey and verifier key
                       Default echo is duple that
                           indicates nothing to receive of form (b'', None)
                       When False may be overridden by a method parameter
        keep (dict): labels are oids, values are Keyage instances
                         named tuple of signature key pair:
                         sigkey = private signing key
                         verkey = public verifying key
                        Keyage = namedtuple("Keyage", "sigkey verkey")
        oid (str|None): own oid defaults used to lookup keys to sign on tx

    Hidden:
        _code (bytes | None): see size property
        _curt (bool): see curt property
        _size (int): see size property
        _verific (bool): see verific property
        _echoic (bool): see echoic property
        _keep (dict): see keep property
        _oid (str|None): see oid property
    """
    Version = Versionage(major=0, minor=0)  # default version
    Codex = GramDex
    Codes = asdict(Codex)  # map code name to code
    Names = {val : key for key, val in Codes.items()} # invert map code to code name
    Sodex = SGDex  # signed gram codex
    # dict of gram header part sizes keyed by gram codes: cz mz oz nz sz hz
    Sizes = {
                '__': Sizage(cz=2, mz=22, oz=0, nz=4, sz=0, hz=28),
                '_-': Sizage(cz=2, mz=22, oz=44, nz=4, sz=88, hz=160),
             }

    # Base2 Binary index representation of Text Base64 Char Codes
    #Bodes = ({helping.codeB64ToB2(c): c for n, c in Codes.items()})
    # big enough to hold a CESR big frame with code
    MaxMemoSize = 4294967300  # (2**30-1)*4+8 absolute max net memo payload size
    MaxGramCount = 16777215  # (2**24-1) absolute max gram count
    MaxGramSize = 65535  # (2**16-1) absolute max gram size overridden in subclass
    BufSize = 65535  # (2**16-1)  default buffersize

    @classmethod
    def _encodeOID(cls, raw, code='B'):
        """Utility method for use with signed headers that encodes raw oid
        (origin ID) as CESR compatible fully qualified B64 text domain str
        using CESR compatible text code

        Parameters:
            raw (bytes): oid to be encoded with code
            code (str): code for type of raw oid CESR compatible
                Ed25519N:   str = 'B'  # Ed25519 verkey non-transferable, basic derivation.
                Ed25519:    str = 'D'  # Ed25519 verkey basic derivation
                Blake3_256: str = 'E'  # Blake3 256 bit digest derivation.

        Returns:
           qb64 (str): fully qualified base64 oid
        """
        if code not in ('B', 'D', 'E'):
            raise hioing.MemoerError(f"Invalid oid {code=}")

        rz = len(raw)  # raw size
        if rz != 32:
            raise hioing.MemoerError(f"Invalid raw size {rz=} not 32")

        pz = (3 - ((rz) % 3)) % 3  # net pad size for raw oid
        if len(code) != pz != 1:
            raise hioing.MemoerError(f"Invalid code size={len(code)} not equal"
                                     f" {pz=} not equal 1")

        b64 = encodeB64(bytes([0] * pz) + raw)[pz:] # prepad, convert, and prestrip

        qb64 = code + b64.decode()  # fully qualified base64 oid with prefix code

        _, _, oz, _, _, _ = cls.Sizes[SGDex.Signed]  # cz mz oz nz sz hz
        if len(qb64) != oz:
            hioing.MemoerError(f"Invalid oid qb64 size={len(qb64) != {oz}}")

        return qb64  # fully qualified base64 oid with prefix code


    @classmethod
    def _decodeOID(cls, qb64):
        """Utility method for use with signed headers that decodes qualified
        base64 oid to raw domain bytes from CESR compatible text code

        Parameters:
            qb64 (str): qualified base64 oid to be decoded with code
            code (str): code for type of oid CESR compatible
                Ed25519N:   str = 'B'  # Ed25519 verkey non-transferable, basic derivation.
                Ed25519:    str = 'D'  # Ed25519 verkey basic derivation
                Blake3_256: str = 'E'  # Blake3 256 bit digest derivation.

        Returns:
            tuple(raw, code) where:
                raw (bytes): oid suitable for crypto operations
                code (str): CESR compatible code from qb64
        """
        cz = 1  # only support qb64 length 44
        code = qb64[:cz]
        if code not in ('B', 'D', 'E'):
            raise hioing.MemoerError(f"Invalid oid {code=}")

        qz = len(qb64)  # text size
        if qz != 44:
            raise hioing.MemoerError(f"Invalid oid text size {qz=} not 44")

        cz = len(code)
        pz = cz % 4  # net pad size given cz
        if cz != pz != 1:  # special case here for now we only accept cz=1
            raise hioing.MemoerError(f"Invalid {cz=} not equal {pz=} not equal 1")

        base =  pz * b'A' + qb64[cz:].encode()  # strip code from b64 and prepad pz 'A's
        paw = decodeB64(base)  # now should have pz leading sextexts of zeros
        raw = paw[pz:]  # remove prepad midpad bytes to invert back to raw
        # ensure midpad bytes are zero
        pi = int.from_bytes(paw[:pz], "big")
        if pi != 0:
            raise hioing.MemoerError(f"Nonzero midpad bytes=0x{pi:0{(pz)*2}x}.")

        if len(raw) != ((qz - cz) * 3 // 4):  # exact lengths
            raise hioing.MemoerError(f"Improperly qualified material = {oid}")

        return raw, code


    @classmethod
    def _encodeQVK(cls, raw, code='B'):
        """Utility method for use with signed headers that encodes raw verkey as
        CESR compatible fully qualified B64 text domain str using CESR compatible
        text code

        Parameters:
            raw (bytes): verkey to be encoded with code
            code (str): code for type of raw verkey CESR compatible
                Ed25519N:   str = 'B'  # Ed25519 verkey non-transferable, basic derivation.

        Returns:
            qb64 (str): fully qualified base64 verkey
        """
        if code not in ('B'):
            raise hioing.MemoerError(f"Invalid qvk {code=}")

        rz = len(raw)  # raw size
        if rz != 32:
            raise hioing.MemoerError(f"Invalid raw size {rz=} not 32")

        pz = (3 - ((rz) % 3)) % 3  # net pad size for raw verkey
        if len(code) != pz != 1:
            raise hioing.MemoerError(f"Invalid code size={len(code)} "
                                     f"not equal {pz=} not equal 1")

        b64 = encodeB64(bytes([0] * pz) + raw)[pz:] # prepad, convert, and prestrip

        qb64 = code + b64.decode()  # fully qualified verkey with prefix code

        return qb64  # qualified base64 verkey


    @classmethod
    def _encodeQSS(cls, raw, code='A'):
        """Utility method for use with signed headers that encodes raw sigseed as
        CESR compatible fully qualified B64 text domain str using CESR compatible
        text code

        Parameters:
            raw (bytes): sigseed to be encoded with code
            code (str): code for type of raw sigseed CESR compatible
                Ed25519_Seed:str = 'A'  # Ed25519 256 bit random seed for private key

        Returns:
            qb64 (str): fully qualified base64 sigseed
        """
        if code not in ('A'):
            raise hioing.MemoerError(f"Invalid qss {code=}")

        rz = len(raw)  # raw size
        if rz != 32:
            raise hioing.MemoerError(f"Invalid raw size {rz=} not 32")

        pz = (3 - ((rz) % 3)) % 3  # net pad size for raw sigseed
        if len(code) != pz != 1:
            raise hioing.MemoerError(f"Invalid code size={len(code)} "
                                     f"not equal {pz=} not equal 1")

        b64 = encodeB64(bytes([0] * pz) + raw)[pz:] # prepad, convert, aqb64prestrip

        qb64 = code + b64.decode()  # fully qualified  with prefix code

        return qb64  # qualified base64 sigseed


    @classmethod
    def _decodeQSS(cls, qb64):
        """Utility method for use with signed headers that decodes qualified
        base64 sigseed to raw domain bytes from CESR compatible text code

        Parameters:
            qb64 (str): qualified base64 sigseed to be decoded with code
            code (str): code for type of raw sigseed CESR compatible
                Ed25519_Seed:str = 'A'  # Ed25519 256 bit random seed for private key

        Returns:
            tuple(raw, code) where:
                raw (bytes): sigseed suitable for crypto operations
                code (str): CESR compatible code from qb64
        """
        cz = 1  # only support qb64 length 44
        code = qb64[:cz]
        if code not in ('A'):
            raise hioing.MemoerError(f"Invalid qss {code=}")

        qz = len(qb64)  # text size
        if qz != 44:
            raise hioing.MemoerError(f"Invalid qss text size {qz=} not 44")

        cz = len(code)
        pz = cz % 4  # net pad size given cz
        if cz != pz != 1:  # special case here for now we only accept cz=1
            raise hioing.MemoerError(f"Invalid {cz=} not equal {pz=} not equal 1")

        base =  pz * b'A' + qb64[cz:].encode()  # strip code from b64 and prepad pz 'A's
        paw = decodeB64(base)  # now should have pz leading sextexts of zeros
        raw = paw[pz:]  # remove prepad midpad bytes to invert back to raw
        # ensure midpad bytes are zero
        pi = int.from_bytes(paw[:pz], "big")
        if pi != 0:
            raise hioing.MemoerError(f"Nonzero midpad bytes=0x{pi:0{(pz)*2}x}.")

        if len(raw) != ((qz - cz) * 3 // 4):  # exact lengths
            raise hioing.MemoerError(f"Improperly qualified material = {qss}")

        return raw, code


    @classmethod
    def _encodeSig(cls, raw, code='0B'):
        """Utility method for use with signed headers that encodes raw signature
        as CESR compatible fully qualified B64 text domain str using CESR
        compatible text code

        Parameters:
            raw (bytes): sig to be encoded with code
            code (str): code for type of raw sig CESR compatible
                Ed25519_Sig: str = '0B'  # Ed25519 signature. not indexed

        Returns:
           qb64 (str): fully qualified base64 sig
        """
        if code not in ('0B'):
            raise hioing.MemoerError(f"Invalid sig {code=}")

        rz = len(raw)  # raw size
        if rz != 64:
            raise hioing.MemoerError(f"Invalid raw size {rz=} not 64")

        pz = (3 - ((rz) % 3)) % 3  # net pad size for raw
        if len(code) != pz != 2:
            raise hioing.MemoerError(f"Invalid code size={len(code)} not equal"
                                     f" {pz=} not equal 2")

        b64 = encodeB64(bytes([0] * pz) + raw)[pz:] # prepad, convert, and prestrip

        qb64 = code + b64.decode()  # fully qualified base64 with prefixqb64de

        _, _, _, _, sz, _ = cls.Sizes[SGDex.Signed]  # cz mz oz nz sz hz
        if len(qb64) != sz:
            hioing.MemoerError(f"Invalid sig qb64 size={len(qb64) != {sz}}")

        return qb64  # fully qualified base64 oid with prefix code


    @classmethod
    def _decodeSig(cls, qb64):
        """Utility method for use with signed headers that decodes qualified
        base64 sig to raw domain bytes from CESR compatible text code

        Parameters:
            qb64 (str): qualified base64 sig to be decoded with code
            code (str): code for type of raw sig CESR compatible
                Ed25519_Sig: str = '0B'  # Ed25519 signature. not indexed

        Returns:
            tuple(raw, code) where:
                raw (bytes): signature suitable for crypto operations
                code (str): CESR compatible code from qb64
        """
        cz = 2  # only support qb64 length 88
        code = qb64[:cz]
        if code not in ('0B'):
            raise hioing.MemoerError(f"Invalid sig {code=}")

        qz = len(qb64)  # text size
        if qz != 88:
            raise hioing.MemoerError(f"Invalid sig text size {qz=} not 88")

        pz = cz % 4  # net pad size given cz
        if pz != cz:
            raise hioing.MemoerError(f"Invalid {pz=} not equal {cz=}")

        base =  pz * b'A' + qb64[cz:].encode()  # strip code from b64 and prepad pz 'A's
        paw = decodeB64(base)  # now should have pz leading sextexts of zeros
        raw = paw[pz:]  # remove prepad midpad bytes to invert back to raw
        # ensure midpad bytes are zero
        pi = int.from_bytes(paw[:pz], "big")
        if pi != 0:
            raise hioing.MemoerError(f"Nonzero midpad bytes=0x{pi:0{(pz)*2}x}.")

        if len(raw) != ((qz - cz) * 3 // 4):  # exact lengths
            raise hioing.MemoerError(f"Improperly qualified material = {sig}")

        return raw, code  # qualified base64 sigseed


    def __init__(self, *,
                 name=None,
                 bc=None,
                 bs=None,
                 version=None,
                 rxgs=None,
                 sources=None,
                 counts=None,
                 oids=None,
                 rxms=None,
                 txms=None,
                 txgs=None,
                 txbs=None,
                 code=GramDex.Basic,
                 curt=False,
                 size=None,
                 verific=False,
                 echoic=False,
                 keep=None,
                 oid=None,
                 **kwa
                ):
        """Setup instance

        Inherited Parameters:
            name (str): unique name for Memoer transport. Used to manage.
            opened (bool): True means opened for transport
                           False otherwise
            bc (int | None): count of transport buffers of MaxGramSize
            bs (int | None): buffer size of transport buffers. When .bc is provided
                then .bs is calculated by multiplying, .bs = .bc * .MaxGramSize.
                When .bc is not provided, then if .bs is provided use provided
                value else use default .BufSize

        Parameters:
            version (Versionage): version for this memoir instance consisting of
                namedtuple of form (major: int, minor: int)
            rxgs (dict): keyed by mid (memoID) with value of dict where each
                value dict holds grams from memo keyed by gram number.
                Grams have been stripped of their headers.
                The mid appears in every gram from the same memo.
                The value dict is keyed by the gram number gn, with value bytes.
            sources (dict): keyed by mid that holds the src for the memo indexed
                by its mid (memoID). This enables reattaching src to memo when
                placing fused memo in rxms deque.
            counts (dict): keyed by mid that holds the gram count for the
                memo indexed by its mid (memoID). This enables lookup of the
                gram count for a given memo to know when it has received all its
                constituent grams in order to fuse back into the memo.
            oids (dict[mid: (oid | None)]): keyed by mid that holds the origin ID
                str for the memo indexed by its mid (memoID).
                This enables reattaching the oid to memo when placing fused memo
                in rxms deque.
                oid is only present when signed header otherwise oid is None
            rxms (deque): holding rx (receive) memo tuples desegmented from rxgs grams
                each entry in deque is tuple of form:
                (memo: str, src: str, oid: str) where:
                memo is fused memo, src is source addr, oid is origin ID
            txms (deque): holding tx (transmit) memo tuples to be segmented into
                txgs grams where each entry in deque is tuple of form
                (memo: str, dst: str, oid: str | None)
                memo is memo to be partitioned into gram
                dst is dst addr for grams
                oid is origin id when gram is to be signed or None otherwise
            txgs (deque): grams to transmit, each entry is duple of form:
                (gram: bytes, dst: str). Grams include gram headers.
            txbs (tuple): current transmisstion duple of form:
                (gram: bytearray, dst: str). gram bytearray may hold untransmitted
                portion when datagram is not able to be sent all at once so can
                keep trying. Nothing to send indicated by (bytearray(), None)
                for (gram, dst)
            code (bytes): gram code for gram header
            curt (bool): True means when rending for tx encode header in base2
                         False means when rending for tx encode header in base64
            size (int): gram size when rending for tx.
                first gram size = head size + neck size + body size.
                other gram size = head size + body size.
                Min gram body size is one.
                Gram size also limited by MaxGramSize and MaxGramCount relative to
                MaxMemoSize.
            verific (bool): True means any rx grams must be signed.
                            False otherwise
            echoic (bool): True means use .echos in .send and .receive to mock the
                            transport layer for testing and debugging.
                       False means do not use .echos
                       Each entry in .echos is a duple of form:
                           (gram: bytes, src: str)
                       Default echo is duple that
                           indicates nothing to receive of form (b'', None)
                    When False may be overridden by a method parameter
            keep (dict|None): labels are oids and values are Keyage instances
                              that provide current signature key pair for oid
                              this is a lightweight mechanism that should be
                              overridden in subclass for real world key management.
            oid (str|None): own oid defaults used to lookup keys to sign on tx

        """

        # initialize attributes
        self.version = version if version is not None else self.Version
        self.rxgs = rxgs if rxgs is not None else dict()
        self.sources = sources if sources is not None else dict()
        self.counts = counts if counts is not None else dict()
        self.oids = oids if oids is not None else dict()
        self.rxms = rxms if rxms is not None else deque()

        self.txms = txms if txms is not None else deque()
        self.txgs = txgs if txgs is not None else deque()
        self.txbs = txbs if txbs is not None else (bytearray(), None)

        self.echos = deque()  # only used in testing as echoed tx
        self.inbox = deque()  # holds complete receive memos for testing

        self.code = code
        self.curt = curt
        self.size = size  # property sets size given .code and constraints
        self._verific = True if verific else False

        super(Memoer, self).__init__(name=name, bc=bc, bs=bs, **kwa)

        if not hasattr(self, "name"):  # stub so mixin works in isolation.
            self.name = name if name is not None else "main"  # mixed with subclass should provide this.

        if not hasattr(self, "opened"):  # stub so mixin works in isolation.
            self.opened = False  # mixed with subclass should provide this.

        if not hasattr(self, "bc"):  # stub so mixin works in isolation.
            self.bc = bc # mixin subclass should provide this.

        if not hasattr(self, "bs"):  # stub so mixin works in isolation.
            self.bs = bs # mixin subclass should provide this.

        if self.bs is None:  # default if not provided by mixin
            self.bs = self.BufSize

        self._echoic = True if echoic else False
        self._keep = keep if keep is not None else dict()
        self.oid = oid if oid else None

    @property
    def code(self):
        """Property getter for ._code

        Returns:
            code (str): two char base64 gram code
        """
        return self._code


    @code.setter
    def code(self, code):
        """Property setter for ._code

        Parameters:
            code (str): two char base64 gram code
        """
        if code not in self.Codex:
            raise hioing.MemoerError(f"Invalid {code=}.")

        self._code = code
        if hasattr(self, "_size"):
            self.size = self._size  # refresh size given new code


    @property
    def curt(self):
        """Property getter for ._curt

        Returns:
            curt (bool): True means when rending for tx encode header in base2
                         False means when rending for tx encode header in base64
        """
        return self._curt


    @curt.setter
    def curt(self, curt):
        """Property setter for ._curt

        Parameters:
            curt (bool): True means when rending for tx encode header in base2
                         False means when rending for tx encode header in base64
        """
        self._curt = curt
        if hasattr(self, "_size"):
            self.size = self._size  # refresh size given new curt


    @property
    def size(self):
        """Property getter for ._size

        Returns:
            size (int): gram size when rending for tx.
                        First gram size = head size + neck size + body size.
                        Other gram size = head size + body size.
                        Min gram body size is one.
                        Gram size also limited by MaxGramSize and MaxGramCount
                        relative to MaxMemoSize.
        """
        return self._size


    @size.setter
    def size(self, size):
        """Property setter for ._size

        Parameters:
            size (int | None): gram size for rending memo

        """
        _, _, _, nz, _, hz = self.Sizes[self.code]  # cz mz oz nz sz hz
        size = size if size is not None else self.MaxGramSize
        if self.curt:  # minimum header smaller when in base2 curt
            hz = 3 * hz // 4
            nz = 3 * nz // 4

        # mininum size must be big enough for first gram header and 1 body byte
        self._size = max(min(size, self.MaxGramSize), hz + nz + 1)


    @property
    def verific(self):
        """Property getter for ._verific

        Returns:
            verific (bool): True means any rx grams must be signed.
                            False otherwise
        """
        return self._verific

    @property
    def echoic(self):
        """Property getter for ._echoic

        Returns:
            echoic (bool): True means use .echos in .send and .receive to mock the
                            transport layer for testing and debugging.
                        False means do not use .echos
                        Each entry in .echos is a duple of form:
                            (gram: bytes, src: str)
                        Default echo is duple that
                            indicates nothing to receive of form (b'', None)
        """
        return self._echoic

    @property
    def keep(self):
        """Property getter for ._keep

        Returns:
            keep (dict): labels are oids, values are Keyage instances
                         named tuple of signature key pair:
                         sigkey = private signing key
                         verkey = public verifying key
                        Keyage = namedtuple("Keyage", "sigkey verkey")
        """
        return self._keep

    @property
    def oid(self):
        """Property getter for ._oid

        Returns:
            oid (str|None): oid used to sign on tx if any
        """
        return self._oid


    @oid.setter
    def oid(self, oid):
        """Property setter for ._oid

        Parameters:
            oid (str|None): value to assign to own oid
        """
        self._oid = oid


    def open(self):
        """Opens transport in nonblocking mode

        This is a stub. Override in transport specific subclass
        """
        self.opened = True
        return True


    def reopen(self, **kwa):
        """Idempotently open transport

        This is a stub. Override in transport specific subclass
        """
        self.close()
        return self.open()


    def close(self):
        """Closes  transport

        This is a stub. Override in transport subclass
        """
        self.opened = False


    def wiff(self, gram):
        """Determines encoding of gram bytes header when parsing grams.
        The encoding maybe either base2 or base64.

        Returns:
            curt (bool):    True means base2 encoding
                            False means base64 encoding
                            Otherwise raises hioing.MemoerError

        All gram head codes start with '_' in base64 text or in base2 binary.
        Given only allowed chars are from the set of base64 then can determine
        if header is in base64 or base2.

        First sextet:  (0b is binary, 0o is octal, 0x is hexadecimal)

        0o27 = 0b010111 means first sextet of '_' in base64
        0o77 = 0b111111 means first sextet of '_' in base2

        Assuming that only '_' is allowed as the first char of a valid gram head,
        in either Base64 or Base2 encoding, a parser can unambiguously determine
        if the gram header encoding is binary Base2 or text Base64 because
        0o27 != 0o77.

        Furthermore, it just so happens that 0o27 is a unique first sextet
        among Base64 ascii chars. So an invalid gram header when in Base64 encoding
        is detectable. However, there is one collision (see below) with invalid
        gram headers in Base2 encoding. So an erroneously constructed gram might
        not be detected merely by looking at the first sextet. Therefore
        unreliable transports must provide some additional mechanism such as a
        hash or signature on the gram.

        All Base2 codes for Base64 chars are unique since the B2 codes are just
        the count from 0 to 63. There is one collision, however, between Base2 and
        Base 64 for invalid gram headers. This is because 0o27 is the
        base2 code for ascii 'V'. This means that Base2 encodings
        that begin with 0o27 wich is the Base2 encoding of the ascii 'V, would be
        incorrectly detected as text not binary.
        """

        sextet = gram[0] >> 2
        if sextet == 0o27:
            return False  # base64 text encoding
        if sextet == 0o77:
            return True  # base2 binary encoding

        raise hioing.MemoerError(f"Unexpected {sextet=} at gram head start.")


    def verify(self, sig, ser, oid):
        """Verify signature sig on signed part of gram, ser, using current verkey
        for oid.
        Must be overriden in subclass to perform real signature verification.
        This is a stub.

        Returns:
            result (bool): True if signature verifies
                           False otherwise

        Parameters:
            sig (bytes | str): qualified base64 qb64b
            ser (bytes): signed portion of gram in delivered format
            oid (bytes | str): qualified base64 qb64b of origin ID
        """
        if hasattr(sig, 'encode'):
            sig = sig.encode()

        if hasattr(oid, 'encode'):
            oid = oid.encode()

        return True


    def pick(self, gram):
        """Strips header from gram bytearray leaving only gram body in gram and
        returns (mid, gn, gc). Raises MemoerError if unrecognized header

        Returns:
            result (tuple): tuple of form:
                (mid: str, oid: str, gn: int, gc: int | None) where:
                mid is fully qualified memoID,
                oid is origin ID used to look up signature verification key,
                gn is gram number,
                gc is gram count.
                When first gram (zeroth) returns (mid, oid, 0, gc).
                When other gram returns (mid, oid, gn, None)
                When code has empty oid then oid is None
                Otherwise raises MemoerError error.

        When valid recognized header, strips header bytes from front of gram
        leaving the gram body part bytearray.

        Parameters:
            gram (bytearray): memo gram from which to parse and strip its header.


        """
        curt = self.wiff(gram)  # rx gram encoding True=B2 or False=B64
        if curt:  # base2 binary encoding
            if len(gram) < 2:  # assumes len(code) must be 2
                raise hioing.MemoerError(f"Gram length={len(gram)} to short to "
                                         f"hold code.")
            code = helping.codeB2ToB64(gram, 2)  # assumes len(code) must be 2
            if self.verific and code not in self.Sodex:  # must be signed
                raise hioing.MemoerError(f"Unsigned gram {code =} when signed "
                                         f"required.")

            cz, mz, oz, nz, sz, hz = self.Sizes[code]  # cz mz oz nz sz hz
            pz = (3 - ((mz) % 3)) % 3  # net pad size for mid
            cms = 3 * (cz + mz) // 4  # cz + mz are aligned on 24 bit boundary
            hz = 3 * hz // 4  # encoding b2 means head part sizes smaller by 3/4
            nz = 3 * nz // 4  # encoding b2 means head part sizes smaller by 3/4
            oz = 3 * oz // 4  # encoding b2 means head part sizes smaller by 3/4
            sz = 3 * sz // 4  # encoding b2 means head part sizes smaller by 3/4

            if len(gram) < (hz + 1):  # not big enough for non-first gram
                raise hioing.MemoerError(f"Not enough rx bytes for b2 gram"
                                         f" < {hz + 1}.")

            mid = encodeB64(gram[:cms]).decode()  # fully qualified with prefix code
            oid = encodeB64(gram[cms:cms+oz]).decode()  # must be on 24 bit boundary
            gn = int.from_bytes(gram[cms+oz:cms+oz+nz])
            if gn == 0:  # first (zeroth) gram so long neck
                if len(gram) < hz + nz + 1:
                    raise hioing.MemoerError(f"Not enough rx bytes for b2 "
                                             f"gram < {hz + nz + 1}.")
                neck = gram[cms+oz+nz:cms+oz+2*nz]  # slice takes a copy
                gc = int.from_bytes(neck)  # convert to int
                sig = encodeB64(gram[-sz if sz else len(gram):])   # last ss bytes are signature
                del gram[-sz if sz else len(gram):]  # strip sig
                signed = bytes(gram[:])  # copy signed portion of gram
                del gram[:hz-sz+nz]  # strip of fore head leaving body in gram
            else:  # non-zeroth gram so short neck
                gc = None
                sig = encodeB64(gram[-sz if sz else len(gram):])
                del gram[-sz if sz else len(gram):]  # strip sig
                signed = bytes(gram[:])  # copy signed portion of gram
                del gram[:hz-sz]  # strip of fore head leaving body in gram

        else:  # base64 text encoding
            if len(gram) < 2:  # assumes len(code) must be 2
                raise hioing.MemoerError(f"Gram length={len(gram)} to short to "
                                         f"hold code.")
            code = gram[:2].decode()  # assumes len(code) must be 2
            if self.verific and code not in self.Sodex:  # must be signed
                raise hioing.MemoerError(f"Unsigned gram {code =} when signed "
                                         f"required.")
            cz, mz, oz, nz, sz, hz = self.Sizes[code]  # cz mz oz nz sz hz

            if len(gram) < (hz + 1):  # not big enough for non-first gram
                raise hioing.MemoerError(f"Not enough rx bytes for b64 gram"
                                         f" < {hz + 1}.")

            mid = bytes(gram[:cz+mz]).decode()  # fully qualified with prefix code
            oid = bytes(gram[cz+mz:cz+mz+oz]).decode() # must be on 24 bit boundary
            gn = helping.b64ToInt(gram[cz+mz+oz:cz+mz+oz+nz])
            if gn == 0:  # first (zeroth) gram so long neck
                if len(gram) < hz + nz + 1:
                    raise hioing.MemoerError(f"Not enough rx bytes for b64 "
                                             f"gram < {hz + nz + 1}.")
                neck = gram[cz+mz+oz+nz:cz+mz+oz+2*nz]  # slice takes a copy
                gc = helping.b64ToInt(neck)  # convert to int
                sig = bytes(gram[-sz if sz else len(gram):])  # last sz bytes signature
                del gram[-sz if sz else len(gram):]  # strip sig
                signed = bytes(gram[:])  # copy signed portion of gram
                del gram[:hz-sz+nz]  # strip of fore head leaving body in gram
            else:  # non-zeroth gram short neck
                gc = None
                sig = bytes(gram[-sz if sz else len(gram):])
                del gram[-sz if sz else len(gram):]  # strip sig
                signed = bytes(gram[:])  # copy signed portion of gram
                del gram[:hz-sz]  # strip of fore head leaving body in gram

        if sig:  # signature not emptyoid
            if not self.verify(sig, signed, oid):
                raise hioing.MemoerError(f"Invalid signature on gram from "
                                         f"verifier {oid=}.")

        return (mid, oid if oid else None, gn, gc)


    def receive(self, *, echoic=False) -> (bytes, str|tuple|None):
        """Attemps to receive bytes from remote source.

        May use echoic=True and .echos to mock a transport layer for testing
        Puts sent gram into .echos so that .recieve can extract it when using
        same Memoer to send and recieve to itself via its own .echos
        When using different Memoers each for send and recieve then must
        manually copy from sender Memoer .echos to Receiver Memoer .echos

        Must be overridden in subclass.
        This is a stub to define mixin interface.

        Parameters:
            echoic (bool): True means use .echos in .send and .receive to mock the
                            transport layer for testing and debugging.
                        False means do not use .echos
                        Each entry in .echos is a duple of form:
                            (gram: bytes, src: str)
                        Default echo is duple that
                            indicates nothing to receive of form (b'', None)


        Returns:
            duple (tuple): of form (data: bytes, src: str|tuple|None) where data is the
                bytes of received data and src is the source address.
                When no data the duple is (b'', None) unless echoic is True
                then pop off echo from .echos
        """
        echoic = echoic or self.echoic  # use parm when True else default .echoic
        if echoic:
            try:
                result = self.echos.popleft()
            except IndexError:
                result = (b'', None)
        else:
            result = (b'', None)

        return result


    def _serviceOneReceived(self, *, echoic=False):
        """Service one received duple (raw, src) raw packet data. Always returns
        complete datagram.

        Returns:
            result (bool):  True means data received from source over transport
                            False means no data so try again later

                        return enables greedy callers to keep calling until no
                        more data to receive from transport

        Parameters:
            echoic (bool): True means use .echos in .receive debugging purposes
                            where echo is duple of form: (gram: bytes, src: str)
                           False means do not use .echos default is duple that
                            indicates nothing to receive of form (b'', None)

        """
        try:
            gram, src = self.receive(echoic=echoic)  # if no data the duple is (b'', None)
        except socket.error as ex:  # OSError.errno always .args[0] for compat
            #if (ex.args[0] == (errno.ECONNREFUSED,
                               #errno.ECONNRESET,
                               #errno.ENETRESET,
                               #errno.ENETUNREACH,
                               #errno.EHOSTUNREACH,
                               #errno.ENETDOWN,
                               #errno.EHOSTDOWN,
                               #errno.ETIMEDOUT,
                               #errno.ETIME,
                               #errno.ENOBUFS,
                               #errno.ENOMEM)):
                #return False  # no received data
            #else:
            raise  # should not happen

        if not gram:  # no received data
            return False  # so try again later

        gram = bytearray(gram)  # make copy bytearray so can strip off header

        try:
            mid, oid, gn, gc = self.pick(gram)  # parse and strip off head leaving body
        except hioing.MemoerError as ex: # invalid gram so drop
            logger.error("Unrecognized Memoer gram from %s.\n %s.", src, ex)
            return True  # did receive data so can try again now

        if mid not in self.rxgs:
            self.rxgs[mid] = dict()

        # save stripped gram to be fused later
        if gn not in self.rxgs[mid]:  # make idempotent first only no replay
            self.rxgs[mid][gn] = gram  # index body by its gram number

        if gc is not None:
            if mid not in self.counts:  # make idempotent first only no replay
                self.counts[mid] = gc  # save gram count for mid

        if mid not in self.oids:
            self.oids[mid] = oid

        # assumes unique mid across all possible sources. No replay by different
        # source only first source for a given mid is ever recognized
        if mid not in self.sources:  # make idempotent first only no replay
            self.sources[mid] = src  # save source for later

        return True  # received valid so can try again now


    def serviceReceivesOnce(self, *, echoic=False):
        """Service receives once (non-greedy) and queue up

        Parameters:
            echoic (bool): True means use .echos in .receive debugging purposes
                            where echo is duple of form: (gram: bytes, src: str)
                           False means do not use .echos default is duple that
                            indicates nothing to receive of form (b'', None)
        """
        if self.opened:
            self._serviceOneReceived(echoic=echoic)


    def serviceReceives(self, *, echoic=False):
        """Service all receives (greedy) and queue up

        Parameters:
            echoic (bool): True means use .echos in .receive debugging purposes
                            where echo is duple of form: (gram: bytes, src: str)
                           False means do not use .echos default is duple that
                            indicates nothing to receive of form (b'', None)
        """
        while self.opened:
            if not self._serviceOneReceived(echoic=echoic):
                break


    def fuse(self, grams, cnt):
        """Fuse cnt gram body parts from grams dict into whole memo . If any
        grams are missing then returns None.

        Returns:
            memo (str | None): fused memo or None if incomplete.

        Override in subclass

        Parameters:
            grams (dict): memo gram body parts each keyed by gram number from which
                          to fuse memo. Headers have been stripped.
            cnt (int): gram count for mid
        """
        if len(grams) < cnt:  # must be missing one or more grams
            return None

        memo = bytearray()
        for i in range(cnt):  # iterate in numeric order, items are insertion ordered
            memo.extend(grams[i])  # extend memo with gram body part at gram i

        return memo.decode()  # convert bytearray to str



    def _serviceOnceRxGrams(self):
        """Service one pass over .rxgs dict for each unique mid in .rxgs

        Deleting an item from a dict at a key (since python dicts are key
        insertion ordered) means that the next time an item is created it will
        be last.
        """
        for i, mid in enumerate(list(self.rxgs.keys())):  # items may be deleted in loop
            # if mid then grams dict at mid must not be empty
            if not mid in self.counts:  # missing first gram so skip
                continue
            memo = self.fuse(self.rxgs[mid], self.counts[mid])
            if memo is not None:  # allows for empty "" memo for some src
                self.rxms.append((memo, self.sources[mid], self.oids[mid]))
                del self.rxgs[mid]
                del self.counts[mid]
                del self.sources[mid]
                del self.oids[mid]


    def serviceRxGramsOnce(self):
        """Service one pass (non-greedy) over all unique sources in .rxgs
        dict if any for received incoming grams.
        """
        if self.rxgs:
            self._serviceOnceRxGrams()


    def serviceRxGrams(self):
        """Service one pass (non-greedy) over all unique sources in .rxgs
        dict if any for received incoming grams.  No different from
        serviceRxGramsOnce because service all mids each pass.
        """
        if self.rxgs:
            self._serviceOnceRxGrams()


    def _serviceOneRxMemo(self):
        """Service one duple from .rxMsgs deque

        Returns:
            duple (tuple | None): of form (memo: str, src: str) if any
                                  otherwise None

        """
        return (self.rxms.popleft())  # raises IndexError if empty deque


    def serviceRxMemosOnce(self):
        """Service memos in .rxms deque once (non-greedy one memo) if any

        Override in subclass to handle result and put it somewhere
        """
        try:
            #memo, src, oid = self._serviceOneRxMemo()
            self.inbox.append(self._serviceOneRxMemo())
        except IndexError:
            pass


    def serviceRxMemos(self):
        """Service all memos in .rxms (greedy) if any

        Override in subclass to handle result(s) and put them somewhere
        """
        while self.rxms:
            #memo, src, oid = self._serviceOneRxMemo()
            self.inbox.append(self._serviceOneRxMemo())


    def serviceAllRxOnce(self):
        """Service receive side of stack once (non-greedy)
        """
        self.serviceReceivesOnce()
        self.serviceRxGramsOnce()
        self.serviceRxMemosOnce()


    def serviceAllRx(self):
        """Service receive side of stack (greedy) until empty or waiting for more
        """
        self.serviceReceives()
        self.serviceRxGrams()
        self.serviceRxMemos()


    def memoit(self, memo, dst, oid=None):
        """Append (memo, dst, oid) tuple to .txms deque

        Parameters:
            memo (str): to be segmented and packed into gram(s)
            dst (str): address of remote destination of memo
            oid (str | None): origin ID for verifying signature on grams
        """
        self.txms.append((memo, dst, oid))


    def sign(self, ser, oid):
        """Sign serialization ser using private sigkey for origin ID oid
        Must be overriden in subclass to fetch private key for oid and sign.
        This is a stub.

        Returns:
            sig (bytes): qb64b or qb2 when .curt
                        if not .curt then qualified base64 of signature
                        else if .curt then qualified base2 of signature
                        raises MemoerError if problem signing

        Parameters:
            ser (bytes): signed portion of gram is delivered format
            oid (bytes): qb64 or qb2 if .curt of oid of signer
                         assumes oid of correct length

        Ed25519_Seed:str = 'A'  # Ed25519 256 bit random seed for private key

        """
        if oid not in self.keep:
            raise hioing.MemoerError("Invalid {oid=} for signing")

        qvk, qss = self.keep[oid]
        sigseed, code = self._decodeQSS(qss)  # raises MemoerError if problem
        if code not in ('A'):
            raise hioing.MemoerError(f"Invalid sigseed algorithm type {code=}")




        verkey, sigkey = pysodium.crypto_sign_seed_keypair(sigseed)
        raw = pysodium.crypto_sign_detached(ser, sigkey)  # raw sig
        sig = self._encodeSig(raw)  # raise MemoerError if problem
        sig = sig.encode()  # make bytes

        if self.curt:
            sig = decodeB64(sig)  # make qb2

        return sig


    def rend(self, memo, oid=None):
        """Partition memo into packed grams with headers.

        Returns:
            grams (list[bytes]): list of grams with headers.

        Parameters:
            memo (str): to be partitioned into grams with headers
            oid (str | None): origin ID when gram is to be signed, used to
                              lookup sigkey to sign.
                              None means not signable

        Note zeroth gram has head + neck overhead, zhz = hz + nz
            so bz that fits is smaller by nz relative to non-zeroth
            non-zeroth grams just head overhead hz
            so bz that fits is bigger by nz relative to zeroth
        """
        grams = []
        memo = bytearray(memo.encode()) # convert and copy to bytearray
        # self.size is max gram size
        cz, mz, oz, nz, sz, hz = self.Sizes[self.code]  # cz mz oz nz sz hz

        oid = oid if oid is not None else self.oid

        if oz and (not oid or len(oid) != oz):
            raise hioing.MemoerError(f"Missing or invalid {oid=} for {oz=}")

        pz = (3 - ((mz) % 3)) % 3  # net pad size for mid
        # memo ID is 16 byte random UUID converted to 22 char Base64 right aligned
        mid = encodeB64(bytes([0] * pz) + uuid.uuid1().bytes)[pz:] #pzrepad, convert, and prestrip
        if cz != pz or cz != len(self.code):
            raise hioing.MemoerError(f"Invalid code size {cz=} for {pz=} or "
                                     f"code={self.code}")
        mid = self.code.encode() + mid  # fully qualified mid with prefix code
        ml = len(memo)

        if self.curt:  # rend header parts in base2 instead of base64
            hz = 3 * hz // 4  # encoding b2 means head part sizes smaller by 3/4
            nz = 3 * nz // 4  # encoding b2 means head part sizes smaller by 3/4
            oz = 3 * oz // 4  # encoding b2 means head part sizes smaller by 3/4
            sz = 3 * sz // 4  # encoding b2 means head part sizes smaller by 3/4
            mid = decodeB64(mid)

        bz = (self.size - hz)  # max standard gram body size without neck
        # compute gram count based on overhead note added neck overhead in first gram
        # first gram is special its header is longer by ns than the other grams
        # which means its payload body is shorter by ns than the other gram bodies
        # so take ml and subtract first payload size = ml - (bs-ns) to get the
        # portion of memo carried by other grams. Divide this by bs rounded up
        # (ceil) to get cnt of other grams and add 1 for the first gram to get
        # total gram cnt.
        # gc = ceil((ml-(bs-ns))/bs + 1) = ceil((ml-bs+ns)/bs + 1)
        gc = math.ceil((ml-bz+nz)/bz+1)  # includes added neck ns overhead
        mms = min(self.MaxMemoSize, (bz * self.MaxGramCount) - nz)  # max memo payload

        if ml > mms:
            raise hioing.MemoerError(f"Memo length={ml} exceeds max={mms}.")

        if self.curt:
            neck = gc.to_bytes(nz)
        else:
            neck = helping.intToB64b(gc, l=nz)

        gn = 0
        while memo:
            if self.curt:
                num = gn.to_bytes(nz)  # num size must always be neck size
            else:
                num = helping.intToB64b(gn, l=nz)  # num size must always be neck size

            if oz:  # need oid part, but can't mod here may need below to sign
                if self.curt:
                    oidp = decodeB64(oid.encode())  # oid part b2
                else:
                    oidp = oid.encode()  # oid part b64 bytes
                head = mid + oidp + num
            else:
                head = mid + num

            if gn == 0:
                gram = head + neck + memo[:bz-nz]  # copy slice past end just copies to end
                del memo[:bz-nz]  # del slice past end just deletes to end
            else:
                gram = head + memo[:bz]  # copy slice past end just copies to end
                del memo[:bz]  # del slice past end just deletes to end

            if sz:  # signed gram, .sign returns proper sig format when .curt
                sig = self.sign(gram, oid) # raises MemoerError if invalid
                gram = gram + sig

            grams.append(gram)

            gn += 1

        return grams


    def send(self, gram, dst, *, echoic=False) -> int:
        """Attemps to send bytes in txbs to remote destination dst.

        May use echoic=True and .echos to mock a transport layer for testing
        Puts sent gram into .echos so that .recieve can extract it when using
        same Memoer to send and recieve to itself via its own .echos
        When using different Memoers each for send and recieve then must
        manually copy from sender Memoer .echos to Receiver Memoer .echos

        Must be overridden in subclass.
        This is a stub to define mixin interface.

        Returns:
            count (int): bytes actually sent

        Parameters:
            gram (bytearray): of bytes to send
            dst (str): remote destination address
            echoic (bool): True means use .echos in .send and .receive to mock the
                            transport layer for testing and debugging.
                        False means do not use .echos
                        Each entry in .echos is a duple of form:
                            (gram: bytes, src: str)
                        Default echo is duple that
                            indicates nothing to receive of form (b'', None)

        """
        echoic = echoic or self.echoic  # use parm when True else default .echoic
        if echoic:
            self.echos.append((bytes(gram), dst))  # make copy

        # for example: cnt = self.ls.sendto(gram, dst)
        # cnt == int number of bytes sent
        cnt = len(gram)  # all sent
        return cnt # bytes sent


    def _serviceOneTxMemo(self):
        """Service one (memo, dst, oid) tuple from .txms deque where tuple is
        of form: (memo: str, dst: str, oid: str) where:
                memo is outgoing memo
                dst is destination address
                oid is origin ID used to lookup sigkey to sign

        Calls .rend method to process the partitioning and packing as
        appropriate to convert memo into grams with headers and sign when
        indicated.

        Appends (gram, dst) duple to .txgs deque.
        """
        memo, dst, oid = self.txms.popleft()  # raises IndexError if empty deque

        for gram in self.rend(memo, oid):  # partition memo into gram parts with head
            self.txgs.append((gram, dst))  # append duples (gram: bytes, dst: str)


    def serviceTxMemosOnce(self):
        """Service one outgoing memo from .txms deque if any (non-greedy)
        """

        try:
            self._serviceOneTxMemo()
        except IndexError:
            pass


    def serviceTxMemos(self):
        """Service all outgoing memos in .txms deque if any (greedy)
        """
        while self.txms:
            self._serviceOneTxMemo()


    def gramit(self, gram, dst):
        """Append (gram, dst) duple to .txgs deque. Utility method for testing.

        Parameters:
            gram (bytes): gram to be sent
            dst (str): address of remote destination of gram
        """
        self.txgs.append((gram, dst))


    def _serviceOnceTxGrams(self, *, echoic=False):
        """Service one pass over .txgs dict for each unique dst in .txgs and then
        services one pass over the .txbs of those outgoing grams

        Parameters:
           echoic (bool): True means echo sends into receives via. echos
                           False measn do not echo

        Each entry in .txgs is duple of form: (gram: bytes, dst: str)
        where:
            gram (bytes): is outgoing gram segment from associated memo
            dst (str): is far peer destination address

        The latest gram from .txgs is put in .txbs whose value is duple of form:
          (gram: bytearray, dst: str)  bytearray so can partial send
        where:
            gram (bytearray): holds incompletly sent gram portion if any
            dst (str | None): destination or None if last completely sent

        Returns:
            result (bool):  True means greedy callers can keep sending since
                                last gram sent completely.
                            False means either last gram send was incomplete and
                                or there are no more grams in .txgs deque. In
                                either case greedy callers need to wait and
                                try again later.

        The return value True or False enables back pressure on greedy callers
        so they know when to block waiting.

        When there is a remainder in .txbs each subsequent call of this method
        will attempt to send the remainder until the the full gram has been sent.
        This accounts for datagram protocols that expect continuing attempts to
        send remainder of a datagram when using nonblocking sends.

        When the far side peer is unavailable the gram is dropped. This means
        that unreliable transports need to have a timeout retry mechanism.

        Internally, a dst of None in the .txbs duple indicates its ok to take
        another gram from the .txgs deque if any and start sending it.

        """
        gram, dst = self.txbs  # split out saved partial send if any
        if dst == None:  # no partial send remaining so get new gram
            try:
                gram, dst = self.txgs.popleft()  # next gram
                gram = bytearray(gram)  # ensure bytearray
            except IndexError:
                return False  # nothing more to send, return False to try later

        cnt = 0
        try:
            cnt = self.send(gram, dst, echoic=echoic)  # assumes .opened == True
        except socket.error as ex:  # OSError.errno always .args[0] for compat
            if (ex.args[0] in (errno.ECONNREFUSED,
                               errno.ENOENT,
                               errno.ECONNRESET,
                               errno.ENETRESET,
                               errno.ENETUNREACH,
                               errno.EHOSTUNREACH,
                               errno.ENETDOWN,
                               errno.EHOSTDOWN,
                               errno.ETIMEDOUT,
                               errno.ETIME)):  # far peer problem
                # try again later usually won't work here so we log error
                # and drop gram so as to allow grams to other destinations
                # to get sent. When uxd, ECONNREFUSED and ENOENT means dest
                # uxd file path is not available to send to.
                logger.error("Error send from %s to %s\n %s\n",
                                                         self.name, dst, ex)
                self.txbs = (bytearray(), None) # far peer unavailable, so drop.
                dst = None  # dropped is same as all sent
            else:
                raise  # unexpected error

        if cnt:
            del gram[:cnt]  # remove from buffer those bytes sent
            if not gram:  # all sent
                dst = None  # done indicated by setting dst to None
            self.txbs = (gram, dst)  # update .txbs to indicate if completely sent

        return (False if dst else True)  # incomplete return False, else True


    def serviceTxGramsOnce(self, *, echoic=False):
        """Service one pass (non-greedy) over all unique destinations in .txgs
        dict if any for blocked destination or unblocked with pending outgoing
        grams.

        Parameters:
           echoic (bool): True means echo sends into receives via. echos
                           False measn do not echo
        """
        if self.opened and self.txgs:
            self._serviceOnceTxGrams(echoic=echoic)


    def serviceTxGrams(self, *, echoic=False):
        """Service multiple passes (greedy) over all unqique destinations in
        .txgs dict if any for blocked destinations or unblocked with pending
        outgoing grams until there is no unblocked destination with a pending gram.

        Parameters:
           echoic (bool): True means echo sends into receives via. echos
                           False measn do not echo
        """
        while self.opened and self.txgs:  # pending gram(s)
            if not self._serviceOnceTxGrams(echoic=echoic):  # send incomplete
                break  # try again later



    def serviceAllTxOnce(self):
        """Service the transmit side once (non-greedy) one transmission.
        """
        self.serviceTxMemosOnce()
        self.serviceTxGramsOnce()


    def serviceAllTx(self):
        """Service the transmit side until empty (greedy) multiple transmissions
        until blocked by pending transmission on transport.
        """
        self.serviceTxMemos()
        self.serviceTxGrams()


    def serviceLocal(self):
        """Service the local Peer's receive and transmit queues
        """
        self.serviceReceives()
        self.serviceTxGrams()


    def serviceAllOnce(self):
        """Service all Rx and Tx Once (non-greedy)
        """
        self.serviceAllRxOnce()
        self.serviceAllTxOnce()


    def serviceAll(self):
        """Service all Rx and Tx (greedy)
        """
        self.serviceAllRx()
        self.serviceAllTx()

    service = serviceAll  # alias


@contextmanager
def openMemoer(cls=None, name="test", **kwa):
    """
    Wrapper to create and open Memoer instances
    When used in with statement block, calls .close() on exit of with block

    Parameters:
        cls (Class): instance of subclass instance
        name (str): unique identifer of Memoer peer.
            Enables management of transport by name.
    Usage:
        with openMemoer() as peer:
            peer.receive()

        with openMemoer(cls=MemoerSub) as peer:
            peer.receive()

    """
    peer = None

    if cls is None:
        cls = Memoer
    try:
        peer = cls(name=name, **kwa)
        peer.reopen()

        yield peer

    finally:
        if peer:
            peer.close()


class MemoerDoer(doing.Doer):
    """Memoer Doer for reliable transports that do not require retry tymers.

    See Doer for inherited attributes, properties, and methods.

    Attributes:
       .peer (Memoer): underlying transport instance subclass of Memoer

    """

    def __init__(self, peer, **kwa):
        """Initialize instance.

        Parameters:
           peer (Peer): is Memoer Subclass instance
        """
        super(MemoerDoer, self).__init__(**kwa)
        self.peer = peer


    def enter(self, *, temp=None):
        """Do 'enter' context actions. Override in subclass. Not a generator method.
        Set up resources. Comparable to context manager enter.

        Parameters:
            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any
        """
        # inject temp into file resources here if any
        self.peer.reopen(temp=temp)


    def recur(self, tyme):
        """"""
        self.peer.service()


    def exit(self):
        """"""
        self.peer.close()



class SureMemoer(Tymee, Memoer):
    """SureMemoer mixin base class that supports reliable (sure) memo delivery
    over unreliable datagram transports. These need retry tymers and acknowledged
    delivery services.
    Subclass of Tymee and Memoer

    Inherited Class Attributes (Memoer):
        Version (Versionage): default version consisting of namedtuple of form
            (major: int, minor: int)
        Codex (GramDex): dataclass ref to gram codex
        Codes (dict): maps codex names to codex values
        Names (dict): maps codex values to codex names
        Sodex (SGDex): dataclass ref to signed gram codex
        Sizes (dict): gram head part sizes Sizage instances keyed by gram codes
        MaxMemoSize (int): absolute max memo size
        MaxGramCount (int): absolute max gram count
        BufSize (int): used to set default buffer size for transport datagram buffers

    Class Attributes:
        Tymeout (float): default timeout for retry tymer(s) if any

    Inherited Stubbed Attributes (Memoer):
        name (str):  unique name for Memoer transport.
                     Used to manage multiple instances.
        opened (bool):  True means transport open for use
                        False otherwise
        bc (int|None): count of transport buffers of MaxGramSize
        bs (int|None): buffer size of transport buffers. When .bc is provided
                then .bs is calculated by multiplying, .bs = .bc * .MaxGramSize.
                When .bc is not provided, then if .bs is provided use provided
                value else use default .BufSize

    Inherited Stubbed Methods (Memoer):
        send(gram, dst, *, echoic=False) -> int  # send gram over transport to dst
        receive(self, *, echoic=False) -> (bytes, str|tuple|None)  # receive gram

    Inherited Attributes (Memoer):
        version (Versionage): version for this memoir instance consisting of
                namedtuple of form (major: int, minor: int)
        rxgs (dict): keyed by mid (memoID) with value of dict where each
                value dict holds grams from memo keyed by gram number.
                Grams have been stripped of their headers.
                The mid appears in every gram from the same memo.
        sources (dict): keyed by mid (memoID) that holds the src for the memo.
            This enables reattaching src to fused memo in rxms deque tuple.
        counts (dict): keyed by mid (memoID) that holds the gram count from
            the first gram for the memo. This enables lookup of the gram count when
            fusing its grams.
        oids (dict[mid: (oid | None)]): keyed by mid that holds the origin ID str for
                the memo indexed by its mid (memoID). This enables reattaching
                the oid to memo when placing fused memo in rxms deque.
                Vid is only present when signed header otherwise oid is None
        rxms (deque): holding rx (receive) memo tuples desegmented from rxgs grams
                each entry in deque is tuple of form:
                (memo: str, src: str, oid: str) where:
                memo is fused memo, src is source addr, oid is origin ID
        txms (deque): holding tx (transmit) memo tuples to be segmented into
                txgs grams where each entry in deque is tuple of form
                (memo: str, dst: str, oid: str | None)
                memo is memo to be partitioned into gram
                dst is dst addr for grams
                oid is origin id when gram is to be signed or None otherwise
        txgs (deque): grams to transmit, each entry is duple of form:
                (gram: bytes, dst: str).
        txbs (tuple): current transmisstion duple of form:
            (gram: bytearray, dst: str). gram bytearray may hold untransmitted
            portion when Encodesdatagram is not able to be sent all at once so can
            keep trying. Nothing to send indicated by (bytearray(), None)
            for (gram, dst)
        echos (deque): holding echo receive duples for testing. Each duple of
                       form: (gram: bytes, dst: str).

    Attributes:
        tymeout (float): default timeout for retry tymer(s) if any
        tymers (dict): keys are tid and values are Tymers for retry tymers for
                       each inflight tx

    Inherited Properties (Tymee):
        tyme (float | None):  relative cycle time of associated Tymist which is
            provided by calling .tymth function wrapper closure which is obtained
            from Tymist.tymen().
            None means not assigned yet.
        tymth (Callable | None): function wrapper closure returned by
            Tymist.tymen() method. When .tymth is called it returns associated
            Tymist.tyme. Provides injected dependency on Tymist cycle tyme base.
            None means not assigned yet.

    Inherited Properties (Memoer):
        code (bytes | None): gram code for gram header when rending for tx
        curt (bool): True means when rending for tx encode header in base2
                     False means when rending for tx encode header in base64
        size (int): gram size when rending for tx.
            first gram size = over head size + neck size + body size.
            other gram size = over head size + body size.
            Min gram body size is one.
            Gram size also limited by MaxGramSize and MaxGramCount relative to
            MaxMemoSize.
        verific (bool): True means any rx grams must be signed.
                        False otherwise
        echoic (bool): True means use .echos in .send and .receive to mock the
                            transport layer for testing and debugging.
                       False means do not use .echos
                       Each entry in .echos is a duple of form:
                           (gram: bytes, src: str)
                       Default echo is duple that
                           indicates nothing to receive of form (b'', None)
                       When False may be overridden by a method parameter
        keep (dict): labels are oids, values are Keyage instances
                         named tuple of signature key pair:
                         sigkey = private signing key
                         verkey = public verifying key
                        Keyage = namedtuple("Keyage", "sigkey verkey")
        oid (str|None): own oid defaults used to lookup keys to sign on tx

    """
    Tymeout = 0.0  # tymeout in seconds, tymeout of 0.0 means ignore tymeout

    def __init__(self, *, tymeout=None, code=GramDex.Signed, verific=True, **kwa):
        """
        Initialization method for instance.
        Inherited Parameters:
            see superclass

        Parameters:
            tymeout (float): default for retry tymer if any

        """
        super(SureMemoer, self).__init__(code=code, verific=verific, **kwa)
        self.tymeout = tymeout if tymeout is not None else self.Tymeout
        self.tymers = {}
        #Tymer(tymth=self.tymth, duration=self.tymeout) # retry tymer


    def wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(SureMemoer, self).wind(tymth)  # wind Tymee superclass
        for tid, tymer in self.tymers.items():
            tymer.wind(tymth)

    def serviceTymers(self):
        """Service all retry tymers

        Must be overriden in subclass.
        This is a stub.
        """
        pass


    def serviceLocal(self):
        """Service the local Peer's receive and transmit queues
        """
        self.serviceReceives()
        self.serviceTxGrams()


    def serviceAllOnce(self):
        """Service all Rx and Tx Once (non-greedy)
        """
        self.serviceAllRxOnce()
        self.serviceTymers()
        self.serviceAllTxOnce()


    def serviceAll(self):
        """Service all Rx and Tx (greedy)
        """
        self.serviceAllRx()
        self.serviceTymers()
        self.serviceAllTx()


@contextmanager
def openSM(cls=None, name="test", **kwa):
    """Wrapper to create and open SureMemoer instances
    When used in with statement block, calls .close() on exit of with block

    Parameters:
        cls (Class): instance of subclass instance
        name (str): unique identifer of Memoer peer.
            Enables management of transport by name.
    Usage:
        with openSM() as peer:
            peer.receive()

        with openSM(cls=SureMemoerSub) as peer:
            peer.receive()

    """
    peer = None

    if cls is None:
        cls = SureMemoer
    try:
        peer = cls(name=name, **kwa)
        peer.reopen()

        yield peer

    finally:
        if peer:
            peer.close()


class SureMemoerDoer(doing.Doer):
    """SureMemoerDoer Doer to provide reliable delivery over unreliable
    datagram transports. This requires retry tymers and acknowldged services.

    See Doer for inherited attributes, properties, and methods.

    Attributes:
       .peer (SureMemoer) is underlying transport instance subclass of SureMemoer

    """

    def __init__(self, peer, **kwa):
        """Initialize instance.

        Parameters:
           peer (SureMemoer):  subclass instance
        """
        super(SureMemoerDoer, self).__init__(**kwa)
        self.peer = peer



    def wind(self, tymth):
        """Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(SureMemoerDoer, self).wind(tymth)  # wind this doer
        self.peer.wind(tymth)  # wind its peer



    def enter(self, *, temp=None):
        """Do 'enter' context actions. Override in subclass. Not a generator method.
        Set up resources. Comparable to context manager enter.

        Parameters:
            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any

        Doist or DoDoer winds its doers on enter
        """
        if self.tymth:
            self.peer.wind(self.tymth)  # Doist or DoDoer winds its doers on enter

        self.peer.reopen(temp=temp)  # inject temp into file resources here if any


    def recur(self, tyme):
        """"""
        self.peer.service()


    def exit(self):
        """"""
        self.peer.close()

