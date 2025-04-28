# -*- encoding: utf-8 -*-
"""
hio.core.memoing Module

Mixin Base Classes that add support for  memograms over datagram based transports.
In this context, a memogram is a larger memogram that is partitioned into
smaller parts as transport specific datagrams. This allows larger messages to
be transported over datagram transports than the underlying transport can support.
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

from ... import hioing, help
from ...base import tyming, doing
from ...help import helping

logger = help.ogler.getLogger()

# namedtuple of ints (major: int, minor: int)
Versionage = namedtuple("Versionage", "major minor")


"""Sizage: namedtuple for gram header part size entries in Memoer code tables
cs is the code part size int number of chars in code part
ms is the mid part size int number of chars in the mid part (memoID)
vs is the vid  part size int number of chars in the vid part (verification ID)
ns is the neck part size int number of chars for the gram number in all grams
      and the additional neck that also appears in first gram for gram count
ss is the signature part size int number of chars in the signature part.
      the signature part is discontinuously attached after the body part but
      its size is included in over head computation for the body size
hs is the head size int number of chars for other grams no-neck.
      hs = cs + ms + vs + ns + ss. The size for the first gram with neck is
      hs + ns
"""
Sizage = namedtuple("Sizage", "cs ms vs ss ns hs")

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
    """
    Memoer mixin base class to adds memogram support to a transport class.
    Memoer supports asynchronous memograms. Provides common methods for subclasses.

    A memogram is a higher level construct that sits on top of a datagram.
    A memogram supports the segmentation and desegmentation of memos to
    respect the underlying datagram size, buffer, and fragmentation behavior.

    Layering a reliable transaction protocol on top of a memogram enables reliable
    asynchronous messaging over unreliable datagram transport protocols.

    When the datagram protocol is already reliable, then a memogram enables
    larger memos (messages) than that natively supported by the datagram.

    Usage:
        Do not instantiate directly but use as a mixin with a transport class
        in order to create a new subclass that adds memogram support to the
        transport class. For example MemoerUdp or MemoerUxd

    Each direction of dataflow uses a tiered set of buffers that respect
    the constraints of non-blocking asynchronous IO with datagram transports.

    On the receive side each complete datagram (gram) is put in a gram receive
    deque as a segment of a memo. These deques are indexed by the sender's
    source addr. The grams in the gram recieve deque are then desegmented into a memo
    and placed in the memo deque for consumption by the application or some other
    higher level protocol.

    On the transmit side memos are placed in a deque (double ended queue). Each
    memo is then segmented into grams (datagrams) that respect the size constraints
    of the underlying datagram transport. These grams are placed in the outgoing
    gram deque. Each entry in this deque is a duple of form:
    (gram: bytes, dst: str). Each  duple is pulled off the deque and its
    gram is put in bytearray for transport.

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
        MaxGramSize (int): absolute max gram size on tx with overhead

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


    Inherited Attributes:
        name (str):  unique name for Memoer transport. Used to manage.
        opened (bool):  True means transport open for use
                        False otherwise
        bc (int | None): count of transport buffers of MaxGramSize

    Attributes:
        version (Versionage): version for this memoir instance consisting of
                namedtuple of form (major: int, minor: int)
        rxgs (dict): holding rx (receive) (data) gram deques of grams.
            Each item in dict has key=src and val=deque of grames received
        rxgs (dict): keyed by mid (memoID) with value of dict where each deque
            holds incomplete memo grams for that mid.
            The mid appears in every gram from the same memo.
            The value dict is keyed by the gram number with value
            that is the gram bytes.
        sources (dict): keyed by mid (memoID) that holds the src for the memo.
            This enables reattaching src to fused memo in rxms deque tuple.
        counts (dict): keyed by mid (memoID) that holds the gram count from
            the first gram for the memo. This enables lookup of the gram count when
            fusing its grams.
        vids (dict[mid: (vid | None)]): keyed by mid that holds the verification ID str for
                the memo indexed by its mid (memoID). This enables reattaching
                the vid to memo when placing fused memo in rxms deque.
                Vid is only present when signed header otherwise vid is None
        rxms (deque): holding rx (receive) memo tuples desegmented from rxgs grams
                each entry in deque is tuple of form:
                (memo: str, src: str, vid: str) where:
                memo is fused memo, src is source addr, vid is verification ID
        txms (deque): holding tx (transmit) memo tuples to be segmented into
                txgs grams where each entry in deque is tuple of form
                (memo: str, dst: str, vid: str | None)
                memo is memo to be partitioned into gram
                dst is dst addr for grams
                vid is verification id when gram is to be signed or None otherwise
        txgs (deque): grams to transmit, each entry is duple of form:
                (gram: bytes, dst: str).
        txbs (tuple): current transmisstion duple of form:
            (gram: bytearray, dst: str). gram bytearray may hold untransmitted
            portion when Encodesdatagram is not able to be sent all at once so can
            keep trying. Nothing to send indicated by (bytearray(), None)
            for (gram, dst)
        echos (deque): holding echo receive duples for testing. Each duple of
                       form: (gram: bytes, dst: str).


    Hidden:
        _code (bytes | None): see size property
        _curt (bool): see curt property
        _size (int): see size property
        _verific (bool): see verific property



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


    """
    Version = Versionage(major=0, minor=0)  # default version
    Codex = GramDex
    Codes = asdict(Codex)  # map code name to code
    Names = {val : key for key, val in Codes.items()} # invert map code to code name
    Sodex = SGDex  # signed gram codex
    # dict of gram header part sizes keyed by gram codes: cs ms vs ss ns hs
    Sizes = {
                '__': Sizage(cs=2, ms=22, vs=0, ss=0, ns=4, hs=28),
                '_-': Sizage(cs=2, ms=22, vs=44, ss=88, ns=4, hs=160),
             }
    #Bodes = ({helping.codeB64ToB2(c): c for n, c in Codes.items()})
    MaxMemoSize = 4294967295 # (2**32-1) absolute max memo payload size
    MaxGramCount = 16777215 # (2**24-1) absolute max gram count
    MaxGramSize = 65535  # (2**16-1)  Overridden in subclass


    def __init__(self, *,
                 name=None,
                 bc=None,
                 version=None,
                 rxgs=None,
                 sources=None,
                 counts=None,
                 vids=None,
                 rxms=None,
                 txms=None,
                 txgs=None,
                 txbs=None,
                 code=GramDex.Basic,
                 curt=False,
                 size=None,
                 verific=False,
                 **kwa
                ):
        """Setup instance

        Inherited Parameters:
            name (str): unique name for Memoer transport. Used to manage.
            opened (bool): True means opened for transport
                           False otherwise
            bc (int | None): count of transport buffers of MaxGramSize

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
            vids (dict[mid: (vid | None)]): keyed by mid that holds the verification ID str for
                the memo indexed by its mid (memoID). This enables reattaching
                the vid to memo when placing fused memo in rxms deque.
                Vid is only present when signed header otherwise vid is None
            rxms (deque): holding rx (receive) memo tuples desegmented from rxgs grams
                each entry in deque is tuple of form:
                (memo: str, src: str, vid: str) where:
                memo is fused memo, src is source addr, vid is verification ID
            txms (deque): holding tx (transmit) memo tuples to be segmented into
                txgs grams where each entry in deque is tuple of form
                (memo: str, dst: str, vid: str | None)
                memo is memo to be partitioned into gram
                dst is dst addr for grams
                vid is verification id when gram is to be signed or None otherwise
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
        """

        # initialize attributes
        self.version = version if version is not None else self.Version
        self.rxgs = rxgs if rxgs is not None else dict()
        self.sources = sources if sources is not None else dict()
        self.counts = counts if counts is not None else dict()
        self.vids = vids if vids is not None else dict()
        self.rxms = rxms if rxms is not None else deque()

        self.txms = txms if txms is not None else deque()
        self.txgs = txgs if txgs is not None else deque()
        self.txbs = txbs if txbs is not None else (bytearray(), None)

        self.echos = deque()  # only used in testing as echoed tx

        self.code = code
        self.curt = curt
        self.size = size  # property sets size given .code and constraints
        self._verific = True if verific else False

        super(Memoer, self).__init__(name=name, bc=bc, **kwa)

        if not hasattr(self, "name"):  # stub so mixin works in isolation.
            self.name = name if name is not None else "main"  # mixed with subclass should provide this.

        if not hasattr(self, "opened"):  # stub so mixin works in isolation.
            self.opened = False  # mixed with subclass should provide this.

        if not hasattr(self, "bc"):  # stub so mixin works in isolation.
            self.bc = bc if bc is not None else 4  # mixed with subclass should provide this.


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
        _, _, _, _, ns, hs = self.Sizes[self.code]  # cs ms vs ss ns hs
        size = size if size is not None else self.MaxGramSize
        if self.curt:  # minimum header smaller when in base2 curt
            hs = 3 * hs // 4
            ns = 3 * ns // 4

        # mininum size must be big enough for first gram header and 1 body byte
        self._size = max(min(size, self.MaxGramSize), hs + ns + 1)


    @property
    def verific(self):
        """Property getter for ._verific

        Returns:
            verific (bool): True means any rx grams must be signed.
                            False otherwise
        """
        return self._verific


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
        that begin 0o27 witch is the Base2 encoding of the ascii 'V, would be
        incorrectly detected as text not binary.
        """

        sextet = gram[0] >> 2
        if sextet == 0o27:
            return False  # base64 text encoding
        if sextet == 0o77:
            return True  # base2 binary encoding

        raise hioing.MemoerError(f"Unexpected {sextet=} at gram head start.")


    def verify(self, sig, ser, vid):
        """Verify signature sig on signed part of gram, ser, using key from vid.
        Must be overriden in subclass to perform real signature verification.
        This is a stub.

        Returns:
            result (bool): True if signature verifies
                           False otherwise

        Parameters:
            sig (bytes | str): qualified base64 qb64b
            ser (bytes): signed portion of gram in delivered format
            vid (bytes | str): qualified base64 qb64b of verifier ID
        """
        if hasattr(sig, 'encode'):
            sig = sig.encode()

        if hasattr(vid, 'encode'):
            vid = vid.encode()

        return True


    def pick(self, gram):
        """Strips header from gram bytearray leaving only gram body in gram and
        returns (mid, gn, gc). Raises MemoerError if unrecognized header

        Returns:
            result (tuple): tuple of form:
                (mid: str, vid: str, gn: int, gc: int | None) where:
                mid is fully qualified memoID,
                vid is verID,
                gn is gram number,
                gc is gram count.
                When first gram (zeroth) returns (mid, vid, 0, gc).
                When other gram returns (mid, vid, gn, None)
                When code has empty vid then vid is None
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

            cs, ms, vs, ss, ns, hs = self.Sizes[code]  # cs ms vs ss ns hs
            ps = (3 - ((ms) % 3)) % 3  # net pad size for mid
            cms = 3 * (cs + ms) // 4  # cs + ms are aligned on 24 bit boundary
            hs = 3 * hs // 4  # encoding b2 means head part sizes smaller by 3/4
            ns = 3 * ns // 4  # encoding b2 means head part sizes smaller by 3/4
            vs = 3 * vs // 4  # encoding b2 means head part sizes smaller by 3/4
            ss = 3 * ss // 4  # encoding b2 means head part sizes smaller by 3/4

            if len(gram) < (hs + 1):  # not big enough for non-first gram
                raise hioing.MemoerError(f"Not enough rx bytes for b2 gram"
                                         f" < {hs + 1}.")

            #mid = encodeB64(bytes([0] * ps) + gram[cs:cms])[ps:].decode()  # prepad, convert, strip
            mid = encodeB64(gram[:cms]).decode()  # fully qualified with prefix code
            vid = encodeB64(gram[cms:cms+vs]).decode()  # must be on 24 bit boundary
            gn = int.from_bytes(gram[cms+vs:cms+vs+ns])
            if gn == 0:  # first (zeroth) gram so get neck
                if len(gram) < hs + ns + 1:
                    raise hioing.MemoerError(f"Not enough rx bytes for b2 "
                                             f"gram < {hs + ns + 1}.")
                neck = gram[cms+vs+ns:cms+vs+2*ns]  # slice takes a copy
                gc = int.from_bytes(neck)  # convert to int
                sig = encodeB64(gram[-ss if ss else len(gram):])   # last ss bytes are signature
                del gram[-ss if ss else len(gram):]  # strip sig
                signed = bytes(gram[:])  # copy signed portion of gram
                del gram[:hs-ss+ns]  # strip of fore head leaving body in gram
            else:  # non-first gram no neck
                gc = None
                sig = encodeB64(gram[-ss if ss else len(gram):])
                del gram[-ss if ss else len(gram):]  # strip sig
                signed = bytes(gram[:])  # copy signed portion of gram
                del gram[:hs-ss]  # strip of fore head leaving body in gram

        else:  # base64 text encoding
            if len(gram) < 2:  # assumes len(code) must be 2
                raise hioing.MemoerError(f"Gram length={len(gram)} to short to "
                                         f"hold code.")
            code = gram[:2].decode()  # assumes len(code) must be 2
            if self.verific and code not in self.Sodex:  # must be signed
                raise hioing.MemoerError(f"Unsigned gram {code =} when signed "
                                         f"required.")
            cs, ms, vs, ss, ns, hs = self.Sizes[code]  # cs ms vs ss ns hs

            if len(gram) < (hs + 1):  # not big enough for non-first gram
                raise hioing.MemoerError(f"Not enough rx bytes for b64 gram"
                                         f" < {hs + 1}.")

            mid = bytes(gram[:cs+ms]).decode()  # fully qualified with prefix code
            vid = bytes(gram[cs+ms:cs+ms+vs]).decode() # must be on 24 bit boundary
            gn = helping.b64ToInt(gram[cs+ms+vs:cs+ms+vs+ns])
            if gn == 0:  # first (zeroth) gram so get neck
                if len(gram) < hs + ns + 1:
                    raise hioing.MemoerError(f"Not enough rx bytes for b64 "
                                             f"gram < {hs + ns + 1}.")
                neck = gram[cs+ms+vs+ns:cs+ms+vs+2*ns]  # slice takes a copy
                gc = helping.b64ToInt(neck)  # convert to int
                sig = bytes(gram[-ss if ss else len(gram):])   # last ss bytes are signature
                del gram[-ss if ss else len(gram):]  # strip sig
                signed = bytes(gram[:])  # copy signed portion of gram
                del gram[:hs-ss+ns]  # strip of fore head leaving body in gram
            else:  # non-first gram no neck
                gc = None
                sig = bytes(gram[-ss if ss else len(gram):])
                del gram[-ss if ss else len(gram):]  # strip sig
                signed = bytes(gram[:])  # copy signed portion of gram
                del gram[:hs-ss]  # strip of fore head leaving body in gram

        if sig:  # signature not empty
            if not self.verify(sig, signed, vid):
                raise hioing.MemoerError(f"Invalid signature on gram from "
                                         f"verifier {vid=}.")

        return (mid, vid if vid else None, gn, gc)


    def receive(self, *, echoic=False):
        """Attemps to send bytes in txbs to remote destination dst.
        Must be overridden in subclass.
        This is a stub to define mixin interface.

        Parameters:
            echoic (bool): True means use .echos in .receive debugging purposes
                            where echo is duple of form: (gram: bytes, src: str)
                           False means do not use .echos default is duple that
                            indicates nothing to receive of form (b'', None)

        Returns:
            duple (tuple): of form (data: bytes, src: str) where data is the
                bytes of received data and src is the source address.
                When no data the duple is (b'', None) unless echoic is True
                then pop off echo from .echos
        """

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

        gram = bytearray(gram)# make copy bytearray so can strip off header

        try:
            mid, vid, gn, gc = self.pick(gram)  # parse and strip off head leaving body
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

        if mid not in self.vids:
            self.vids[mid] = vid

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
                self.rxms.append((memo, self.sources[mid], self.vids[mid]))
                del self.rxgs[mid]
                del self.counts[mid]
                del self.sources[mid]
                del self.vids[mid]


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
            memo, src, vid = self._serviceOneRxMemo()
        except IndexError:
            pass


    def serviceRxMemos(self):
        """Service all memos in .rxms (greedy) if any

        Override in subclass to handle result(s) and put them somewhere
        """
        while self.rxms:
            memo, src, vid = self._serviceOneRxMemo()


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


    def send(self, txbs, dst, *, echoic=False):
        """Attemps to send bytes in txbs to remote destination dst.
        Must be overridden in subclass.
        This is a stub to define mixin interface.

        Returns:
            count (int): bytes actually sent

        Parameters:
            txbs (bytes | bytearray): of bytes to send
            dst (str): remote destination address
            echoic (bool): True means echo sends into receives via. echos
                           False measn do not echo
        """
        if echoic:
            self.echos.append((bytes(txbs), dst))  # make copy
        return len(txbs)  # all sent



    def memoit(self, memo, dst, vid=None):
        """Append (memo, dst, vid) tuple to .txms deque

        Parameters:
            memo (str): to be segmented and packed into gram(s)
            dst (str): address of remote destination of memo
            vid (str | None): verifiable ID for signing grams
        """
        self.txms.append((memo, dst, vid))


    def sign(self, ser, vid):
        """Sign serialization ser using private key for verifier ID vid
        Must be overriden in subclass to fetch private key for vid and sign.
        This is a stub.

        Returns:
            sig(bytes): qb64b qualified base64 representation of signature

        Parameters:
            ser (bytes): signed portion of gram is delivered format
            vid (str | bytes): qualified base64 qb64 of verifier ID

        """
        if hasattr(vid, 'encode'):
            vid = vid.encode()
        cs, ms, vs, ss, ns, hs = self.Sizes[self.code]  # cs ms vs ss ns hs
        return b'A' * ss


    def rend(self, memo, vid=None):
        """Partition memo into packed grams with headers.

        Returns:
            grams (list[bytes]): list of grams with headers.

        Parameters:
            memo (str): to be partitioned into grams with headers
            vid (str | None): verification ID when gram is to be signed.
                              None means not signable

        Note first gram has head + neck overhead, hs + ns so bs is smaller by ns
             non-first grams have just head overhead hs so bs is bigger by ns
        """
        grams = []
        memo = bytearray(memo.encode()) # convert and copy to bytearray
        # self.size is max gram size
        cs, ms, vs, ss, ns, hs = self.Sizes[self.code]  # cs ms vs ss ns hs
        ps = (3 - ((ms) % 3)) % 3  # net pad size for mid
        if vs and (not vid or len(vid) != vs):
            raise hioing.MemoerError(f"Invalid {vid=} for size={vs}.")

        vid = b"" if vid is None else vid[:vs].encode()

        # memo ID is 16 byte random UUID converted to 22 char Base64 right aligned
        mid = encodeB64(bytes([0] * ps) + uuid.uuid4().bytes)[ps:] # prepad, convert, and strip
        mid = self.code.encode() + mid  # fully qualified mid with prefix code
        ml = len(memo)

        if self.curt:  # rend header parts in base2 instead of base64
            hs = 3 * hs // 4  # encoding b2 means head part sizes smaller by 3/4
            ns = 3 * ns // 4  # encoding b2 means head part sizes smaller by 3/4
            vs = 3 * vs // 4  # encoding b2 means head part sizes smaller by 3/4
            ss = 3 * ss // 4  # encoding b2 means head part sizes smaller by 3/4
            mid = decodeB64(mid)
            vid = decodeB64(vid)

        bs = (self.size - hs)  # max standard gram body size without neck
        # compute gram count based on overhead note added neck overhead in first gram
        # first gram is special its header is longer by ns than the other grams
        # which means its payload body is shorter by ns than the other gram bodies
        # so take ml and subtract first payload size = ml - (bs-ns) to get the
        # portion of memo carried by other grams. Divide this by bs rounded up
        # (ceil) to get cnt of other grams and add 1 for the first gram to get
        # total gram cnt.
        # gc = ceil((ml-(bs-ns))/bs + 1) = ceil((ml-bs+ns)/bs + 1)
        gc = math.ceil((ml-bs+ns)/bs+1)  # includes added neck ns overhead
        mms = min(self.MaxMemoSize, (bs * self.MaxGramCount) - ns)  # max memo payload

        if ml > mms:
            raise hioing.MemoerError(f"Memo length={ml} exceeds max={mms}.")

        if self.curt:
            neck = gc.to_bytes(ns)
        else:
            neck = helping.intToB64b(gc, l=ns)

        gn = 0
        while memo:
            if self.curt:
                num = gn.to_bytes(ns)  # num size must always be neck size
            else:
                num = helping.intToB64b(gn, l=ns)  # num size must always be neck size

            head = mid + vid + num

            if gn == 0:
                gram = head + neck + memo[:bs-ns]  # copy slice past end just copies to end
                del memo[:bs-ns]  # del slice past end just deletes to end
            else:
                gram = head + memo[:bs]  # copy slice past end just copies to end
                del memo[:bs]  # del slice past end just deletes to end

            if ss:  # sign
                sig = self.sign(gram, vid)
                if self.curt:
                    sig = decodeB64(sig)
                gram = gram + sig

            grams.append(gram)

            gn += 1

        return grams


    def _serviceOneTxMemo(self):
        """Service one (memo, dst, vid) tuple from .txms deque where tuple is
        of form: (memo: str, dst: str, vid: str) where:
                memo is outgoing memo
                dst is destination address
                vid is verification ID

        Calls .rend method to process the partitioning and packing as
        appropriate to convert memo into grams with headers and sign when
        indicated.

        Appends (gram, dst) duple to .txgs deque.
        """
        memo, dst, vid = self.txms.popleft()  # raises IndexError if empty deque

        for gram in self.rend(memo, vid):  # partition memo into gram parts with head
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
        """Append (gram, dst) duple to .txgs deque

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

        Each entry in.txgs is duple of form: (gram: bytes, dst: str)
        where:
            gram (bytes): is outgoing gram segment from associated memo
            dst (str): is far peer destination address

        .txbs is duple of form: (gram: bytearray, dst: str)
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
        that unreliable transports need to have a timeour retry mechanism.

        Internally, a dst of None in the .txbs duple indicates its ok to take
        another gram from the .txgs deque if any and start sending it.

        """
        gram, dst = self.txbs
        if dst == None:
            try:
                gram, dst = self.txgs.popleft()
                gram = bytearray(gram)
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
                dst = None  # indicate by setting dst to None
            self.txbs = (gram, dst)  # update txbs to indicate if completely sent

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



class TymeeMemoer(tyming.Tymee, Memoer):
    """TymeeMemoer mixin base class to add tymer support for unreliable transports
    that need retry tymers. Subclass of tyming.Tymee


    Inherited Class Attributes:
        see superclass

    Class Attributes:
        Tymeout (float): default timeout for retry tymer(s) if any

    Inherited Attributes:
        see superclass

    Attributes:
        tymeout (float): default timeout for retry tymer(s) if any



    """
    Tymeout = 0.0  # tymeout in seconds, tymeout of 0.0 means ignore tymeout

    def __init__(self, *, tymeout=None, **kwa):
        """
        Initialization method for instance.
        Inherited Parameters:
            see superclass

        Parameters:
            tymeout (float): default for retry tymer if any

        """
        super(TymeeMemoer, self).__init__(**kwa)
        self.tymeout = tymeout if tymeout is not None else self.Tymeout
        #self.tymer = tyming.Tymer(tymth=self.tymth, duration=self.tymeout) # retry tymer


    def wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(TymeeMemoer, self).wind(tymth)
        #self.tymer.wind(tymth)

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
def openTM(cls=None, name="test", **kwa):
    """
    Wrapper to create and open TymeeMemoer instances
    When used in with statement block, calls .close() on exit of with block

    Parameters:
        cls (Class): instance of subclass instance
        name (str): unique identifer of Memoer peer.
            Enables management of transport by name.
    Usage:
        with openTM() as peer:
            peer.receive()

        with openTM(cls=MemoerSub) as peer:
            peer.receive()

    """
    peer = None

    if cls is None:
        cls = TymeeMemoer
    try:
        peer = cls(name=name, **kwa)
        peer.reopen()

        yield peer

    finally:
        if peer:
            peer.close()


class TymeeMemoerDoer(doing.Doer):
    """TymeeMemoer Doer for unreliable transports that require retry tymers.

    See Doer for inherited attributes, properties, and methods.

    Attributes:
       .peer (TymeeMemoer) is underlying transport instance subclass of TymeeMemoer

    """

    def __init__(self, peer, **kwa):
        """Initialize instance.

        Parameters:
           peer (TymeeMemoer):  subclass instance
        """
        super(TymeeMemoerDoer, self).__init__(**kwa)
        self.peer = peer



    def wind(self, tymth):
        """Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(TymeeMemoerDoer, self).wind(tymth)
        self.peer.wind(tymth)


    def enter(self, *, temp=None):
        """Do 'enter' context actions. Override in subclass. Not a generator method.
        Set up resources. Comparable to context manager enter.

        Parameters:
            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any

        Doist or DoDoer winds its doers on enter
        """
        # inject temp into file resources here if any
        if self.tymth:
            self.peer.wind(self.tymth)
        self.peer.reopen(temp=temp)


    def recur(self, tyme):
        """"""
        self.peer.service()


    def exit(self):
        """"""
        self.peer.close()

