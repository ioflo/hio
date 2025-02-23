# -*- encoding: utf-8 -*-
"""
hio.core.memoing Module

Mixin Base Classes that add support for  memograms over datagram based transports.
In this context, a memogram is a larger memogram that is partitioned into
smaller parts as transport specific datagrams. This allows larger messages to
be transported over datagram transports than the underlying transport can support.

Provide mixin classes.
Takes of advantage of multiple inheritance to enable mixtures of behaviors
with minimal code duplication (more DRY).

New style python classes use the C3 linearization algorithm. Multiple inheritance
forms a directed acyclic graph called a diamond graph. This graph is linarized
into the method resolution order.
Use class.mro() or class.__mro__

(see https://www.geeksforgeeks.org/method-resolution-order-in-python-inheritance/)
Basically:
* children always precede their parents
* immediate parent classes of a child are visited in the order listed in the
child class statement.
* a super class is visited only after all sub classes have been visited
* linearized graph is monotonic (a class is only visted once)

Datagram IP Fragmentation
https://packetpushers.net/blog/ip-fragmentation-in-detail/
Only the first fragment contains the header that is needed to defragment at
the other end.

https://stackoverflow.com/questions/24045424/when-acting-on-a-udp-socket-what-can-cause-sendto-to-send-fewer-bytes-than-re
Answer is that UDP sendto always sends all the bytes but does not make a distinction
between nonblocking and blocking calls to sendto.
Other documentation seems to indicate that sendto when non-blocking may not
send all the bytes.
https://learn.microsoft.com/en-us/dotnet/api/system.net.sockets.socket.sendto?view=net-9.0

http://esp32.io/viewtopic.php?t=2378
For UDP, sendto() will try to allocate a packet buffer to hold the full
UDP packet of the size requested (up to 64KB) and will return with errno=ENOMEM
if this fails. Otherwise, provided FD_ISSET(sock, &write_set) is set then the
sendto() will succeed. But you should check for this failure.
Generally if the ESP32 is not low on free memory then you won't see ENOMEM here.

Every call to send must send less that sf::UdpSocket::MaxDatagramSize bytes --
which is a little less than 2^16 (65536) bytes.

https://people.computing.clemson.edu/~westall/853/notes/udpsend.pdf
However, the existence of the UDP and IPmid = uuid.uuid4().bytes  # 16 byte random uuid

headers should also limit.

Maximum IPV4 header size is 60 bytes and UDP header is 8 bytes so maximum UDP
datagram payload size is  65535 - 60 - 8 = 65467

With ipv6 the IP headers are done differently so maximum payload size is
65,535 - 8 = 65527

https://en.wikipedia.org/wiki/Maximum_transmission_unit
https://stackoverflow.com/questions/1098897/what-is-the-largest-safe-udp-packet-size-on-the-internet
The maximum safe UDP payload is 508 bytes. This is a packet size of 576
(the "minimum maximum reassembly buffer size"), minus the maximum 60-byte
IP header and the 8-byte UDP header. As others have mentioned, additional
protocol headers could be added in some circumstances. A more conservamid = uuid.uuid4().bytes  # 16 byte random uuid
tive
value of around 300-400 bytes may be preferred instead.

Usually ip headers are only 20 bytes so with UDP header (src, dst) of 8 bytes
the maximum allowed payload is 576 - 28 = 548

Any UDP payload this size or smaller is guaranteed to be deliverable over IP
(though not guaranteed to be delivered). Anything larger is allowed to be
outright dropped by any router for any reason.

Except on an IPv6-only route,
where the maximum payload is 1,212 bytes.

Unix Domain Socket:
https://unix.stackexchange.com/questions/424380/what-values-may-linux-use-for-the-default-unix-socket-buffer-size

Path cannot exceed 108 bytes
The  SO_SNDBUF  socket  option does have an effect for UNIX domain sockets,
but the SO_RCVBUF option does not.
For datagram sockets, the SO_SNDBUF value imposes an upper limit on the size
of outgoing datagrams.
This limit is calculated as the doubled (see socket(7)) option value less 32 bytes used for overhead.

Doubling accounts for the overhead.
SO_SNDBUF
              Sets or gets the maximum socket send buffer in bytes.  The
              kernel doubles this value (to allow space for bookkeeping
              overhead) when it is set using setsockopt(2), and this
              doubled value is returned by getsockopt(2).  The default
              value is set by the /proc/sys/net/core/wmem_default file
              and the maximum allowed value is set by the
              /proc/sys/net/core/wmem_max file.  The minimum (doubled)
              value for this option is 2048.

In python the getsockopt apparently does not return the doubled value but
the undoubled value.

https://unix.stackexchange.com/questions/38043/size-of-data-that-can-be-written-to-read-from-sockets
https://stackoverflow.com/questions/21856517/whats-the-practical-limitmid = uuid.uuid4().bytes  # 16 byte random uuid
-on-the-size-of-single-packet-transmitted-over-domain

Memo
Memo partitioning into parts.

Default part is of form  part = head + sep + body.
Some subclasses might have part of form part = head + sep + body + tail.
In that case encoding of body + tail must provide a way to separate body from tail.
Typically tail would be a signature on the fore part = head + sep + body


Separator sep is b'|' must not be a base64 character.

The head consists of three fields in base64
mid = memo IDmid = uuid.uuid4().bytes  # 16 byte random uuid

pn = part number of part in memo zero based
pc = part count of total parts in memo may be zero when body is empty

Sep = b'|'
assert not helping.Reb64.match(Sep)

body = b"demogram"
pn = 0
pc = 12

pn = helping.intToB64b(pn, l=4)
pc = helping.intToB64b(pc, l=4)

PartLeader = struct.Struct('!16s4s4s')
PartLeader.size  == 24
head = PartLeader.pack(mid, pn, pc)
part = Sep.join(head, body)


head, sep, body = part.partition(Sep)
assert helping.Reb64.match(head)
mid, pn, pc = PartLeader.unpack(head)
pn = helping.b64ToInt(pn)
pc = helping.b64ToInt(pc)

# test PartHead
code = MtrDex.PartHead
assert code == '0P'
codeb = code.encode()mid = uuid.uuid4().bytes  # 16 byte random uuid



mid = uuid.uuid4().bytes  # 16 byte random uuid


mid = 1
midb = mid.to_bytes(16)
assert midb == b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01'
pn = 1
pnb = pn.to_bytes(3)
assert pnb == b'\x00\x00\x01'
pc = 2
pcb = pc.to_bytes(3)
assert pcb == b'\x00\x00\x02'
raw = midb + pnb + pcb
assert raw == (b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01'
               b'\x00\x00\x01\x00\x00\x02')mid = uuid.uuid4().bytes  # 16 byte random uuid


assert mid == int.from_bytes(raw[:16])
assert pn == int.from_bytes(raw[16:19])
assert pc == int.from_bytes(raw[19:22])

midb64b = encodeB64(bytes([0] * 2) + midb)[2:] # prepad ans strip
pnb64b = encodeB64(pnb)
pcb64b = encodeB64(pcb)

qb64b = codeb + midb64b + pnb64b + pcb64b
assert qb64b == b'0PAAAAAAAAAAAAAAAAAAAAABAAABAAAC'
qb64 = qb64b.decode()
qb2 = decodeB64(qb64b)

assert mid == int.from_bytes(decodeB64(b'AA' + qb64b[2:24]))
assert pn == int.from_bytes(decodeB64(qb64b[24:28]))
assert pc == int.from_bytes(decodeB64(qb64b[28:32]))


codeb64b = b'__"

# 16 byte random uuid
midb64b = encodeB64(bytes([0] * 2) + uuid.uuid4().bytes)[2:] # prepad then strip
pn = 1
pnb64b = helping.intToB64b(pn, l=3)
pc = 2
pcb64b = helping.intToB64b(pc, l=3)

headb64b = codeb64b + midb64b + pnb64b + pcb64b

fmt = '!2s22s4s4s'
PartLeader = struct.Struct(fmt)
PartLeader.size  == 32
head = PartLeader.pack(codeb64b, midb64b, pnb64b, pcb64b)

assert helping.Reb64.match(head)
codeb64b, midb64b, pnb64b, pcb64b = PartLeader.unpack(head)
codeb64b, midb64b, pnb64b, pcb64b = PartLeader unpack_from(fmt, part)


mid = helping.b64ToInt(b'AA' + midb64b))
pn = helping.b64ToInt(pnb64b))
pc = helping.b64ToInt(pcb64b))

Standard header in all parts consists of
code + mid + pn

The first part with pn == 0 also has an additional field called the neck
that is the total part count pc

Standard
HeadSize = 28  # base64 chars or 21 base2 bytes
NeckSize = 4 # base  64 chars or 21 base2 bytes

codeb64b = b'__"
midb64b = encodeB64(bytes([0] * 2) + uuid.uuid4().bytes)[2:] # prepad, convert,  and strip
pn = 1
pnb64b = helping.intToB64b(pn, l=4)
pc = 2
pcb64b = helping.intToB64b(pc, l=4)

headb64b = codeb64b + midb64b + pnb64b
neckb64b = pcb64b
assert helping.Reb64.match(headb64b)
assert helping.Reb64.match(neckb64b)

codeb64b = headb64b[:2]
mid = helping.b64ToInt(b'AA' + headb64b[2:24]))  # prepad and convert
pn = helping.b64ToInt(headb64b[24:28]))
pc = helping.b64ToInt(neckb64b[28:32]))


PartCode Typing/Versions uses a different base64 two char code.
Codes always start with `_` and second char in code starts at `_`
and walks backwards through B64 code table for each part type-version (tv) code.
Each of total head length including code and total neck length must be a
multiple of 4 characters.  so eacch converts to/from B2 without padding.
Head type-version code governs the neck as well. So to change length in order to change
field lengths or add or remove fields need a new part (tv) code.

To reiterate, if ever need to change anything ned a new part tv code. There are
no versions per type.  This is deemed sufficient because anticipate a very
limited set of possible fields ever needed for memogram transport types.

tv 0 is '__'
tv 1 is '_-'
tv 3 is '_9'

Because the part head and neck are valid mid-pad B64 primitives then can be losslessly
transformed to/from CESR primitives merely by translated the part tv code to
an  equivalent entry in the  two char cesr primitive code table. When doing so
The neck is always attached and then stripped when not needed.

The CESR codes albeit different are one-to-one. This enables representing headers
as CESR primitives for management but not over the wire. I.e. can transform
Memogram Parts to CESR primitives to tunnel in some CESR stream.

Normally CESR streams are tunneled inside Memoer memograms sent over-the-wire.
In this case, the memogram is the wrapper and each part uses the part tv code
defined herein not the equivalent CESR code.
Using  so far reserved and unused '_' code which is reserved as the selector
for theCESR op code table for memogram parts makes it more apparent that a part
belongs to a memogram and not a CESR stream.
Eventually when CESR op codes eventually become defined, it's not likely to be
confusing since the context of CESR op codes is different that transport
wrappers.

Morover when a MemoGram payload is a tunneled CESR Stream, the memogram parser
will parse and strip the MemoGram part wrappers to construct the tunneled,
stream so the wrapper is transarent to the CESR stream and the CESR stream
payload is opaque to the memogram wrapper, i.e. no ambiguity.



HeadCode hc = b'__'
HeadCodeSize hcs = 2
MemoIDSize mis = 22
PartNumSize pns = 4
PartCntSize pcs = 4
PartHeadSize phs  = 28
PartHeadNeckSize phns = 28 + 4 = 32


MaxPartBodySize = ()2** 16 -1) - HeadSize
PartBodySize pbs = something <= MaxBodySize
PartSize = PartHeadSize + PartBodySize
PartSize <= 2**16 -1

MaxMemoSize = (2**16-1)**2
MaxPartCount for UDP PartSize of 508 is ceil(MaxMemoSize/508) = 8454403  which is < 2**24-1
not partsize includes head
MaxPartCount for UXD PartSize of 2**16 -1  is ceil(MaxMemoSize/(2**16-1))= 2**16-1
MinPartSize = MaxMemoSize // (2**24-1) = 255  = 2**8-1
MaxPartSize = (2**16-1)
For any given PartSize  there is a MaxPartCount of 2**24-1 so if fix the PartSize
this limits the effective
mms = min((2**16-1)**2), (PartSize - PartHeadSize) * (2**24-1))
mms = min((2**16-1)**2), (PartBodySize) * (2**24-1))
Note there is an extra 4 characters in first part for the neck

so ps, pbs, and mms are variables specific to transport
PHS is fixed for the transport type reliable unreliable with header fields as defined
The desired ps for a given transport instance may be smaller than the allowed
maximum to accomodate buffers etc.
Given the fixed part head size PHS once can calculate the maximum memo size
that includes the header overhead given the contraint of no more than 2**24-1
parts in a given memo.

So for a given transport:
ps == min(ps, 2**16-1)
pbs = ps - PHS

mms = min((2**16-1)**2), pbs * (2**24-1))
So compare memo size to mms and if greater raise error and drop memo
otherwise partition (part) memo into parts with headers and transmit


Note max memo size is (2**16-1)**2 = 4294836225.
But accounting for the part header overhead the largest payload max memo size is
max part size = (2**16-1) == 65535
max part count = (2**24-1) == 16777215
standard header size hs = 28
neck size ns = 4
bs = maxpartsize - hs = (65535 - hs) = 65507  # max standard part body size
max theoretical memogram payload size mms is
mms = (bs * maxpartcount) - ns  = 65507 * 16777215 - 4 = 1099025023001
but this is too big so we limit it to 4294836225 but we can have a payload
of 4294836225 when using the maxpartsize for each part.

The maximum number of bytes in a CESR big group frame body is
(2**30-1)*4 = 4294967292.
The maximum group count is (2**30-1) == 1073741823
Groups code count in quadlets (4) and the max count value is (2**30-1) for 5
6 bit b64 digits.
The group code is not part of the counted quadlets so the largest group
with its group code of length 8 is 4294967292 + 8 = 4294967300
which is (2**30-1)*4 + 8.

This is bigger than the max effective MemoGram payload size by
4294967300 - 4294836225 = 131075


So when sending via segmented MemoGram parts the maximum big group count frame
with code as payload is

(4294836225 - 8) // 4 = 1073709054

This is less than the absolute max group count by
1073741823 - 1073709054 = 32769

So biggest memogram payload is relatively slightly smaller than the max group
frame size with group code.

To fix this we would have to allow for a bigger part gram size than 2**16-1
For UXD datagrams this is not a hard limit
but it is a hard limit for UDP datagrams

It is unlikely we would ever reach those limits in a practical application.

ToDo:
change maxmemosize to accomodate big group + code
Change mode to boolean b2mode True False no more Wiffs
Add code '_-' for signed parts   vs verification id size ss signatures size
expanes Sizes for vs and ss
Signed first part  code + mid + vid + pn + pc + body + sig
Signed other parts  code + mid + vid + pn + body + sig
Add sign and verify methods
Change name of MemoGram to Memoer to match convention


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
from dataclasses import dataclass, astuple

from .. import hioing, help
from ..base import tyming, doing
from ..help import helping

logger = help.ogler.getLogger()

# namedtuple of ints (major: int, minor: int)
Versionage = namedtuple("Versionage", "major minor")

Wiffage = namedtuple("Wiffage", 'txt bny')  # part head encoding
Wiffs = Wiffage(txt='txt', bny='bny')


# namedtuple for size entries in Memoer code tables
# cs is the code size int number of chars in code portion
# ms is the mid size int number of chars in the mid portion (memoID)
# ns is the neck size int number of chars for the part number in all parts and
#       the additional neck that also appears in first part
# hs is the head size int number of chars hs = cs + ms + ns and for the first
#       part the head of size hs is followed by a neck of size ns. So the total
#       overhead on first part is os = hs + ns

Sizage = namedtuple("Sizage", "cs ms ns hs")

@dataclass(frozen=True)
class PartCodex:
    """
    PartCodex is codex of all Part Head Codes.
    Only provide defined codes.
    Undefined are left out so that inclusion(exclusion) via 'in' operator works.
    """
    Basic:     str = '__'  # Basic Part Head Code

    def __iter__(self):
        return iter(astuple(self))


PartDex = PartCodex()  # Make instance


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


    Class Attributes:
        Version (Versionage): default version consisting of namedtuple of form
            (major: int, minor: int)
        BufCount (int):  default bufcount bc for transport 64
        Code (str):  default part type-version head code '__'
        MaxMemoSize (int): absolute max memo size  4294836225
        MaxPartSize (int): absolute max part size  65535
        MaxPartCount (int): absolute max part count  16777215
        Sizes (dict): part sizes Sizage instances keyed by part codes
        Mode (str): default encoding mode for tx part header b64 'txt' Wiffs.txt

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
            holds incomplete memo part grams for that mid.
            The mid appears in every gram part from the same memo.
            The value dict is keyed by the part number pn, with value
            that is the part bytes.
        sources (dict): keyed by mid (memoID) that holds the src for the memo.
            This enables reattaching src to fused memo in rxms deque tuple.
        counts (dict): keyed by mid (memoID) that holds the part count (pc) from
            the first part for the memo. This enables lookup of the pc when
            fusing its parts.
        rxms (deque): holding rx (receive) memo duples desegmented from rxgs grams
                each entry in deque is duple of form (memo: str, dst: str)
        txms (deque): holding tx (transmit) memo tuples to be segmented into
                txgs grams where each entry in deque is duple of form
                (memo: str, dst: str)
        txgs (deque): grams to transmit, each entry is duple of form:
                (gram: bytes, dst: str).
        txbs (tuple): current transmisstion duple of form:
            (gram: bytearray, dst: str). gram bytearray may hold untransmitted
            portion when Encodesdatagram is not able to be sent all at once so can
            keep trying. Nothing to send indicated by (bytearray(), None)
            for (gram, dst)
        echos (deque): holding echo receive duples for testing. Each duple of
                       form: (gram: bytes, dst: str).
        code (bytes | None): part head code for part header
        size (int): part size for this instance for transport. Part size
                   = head size  + body size. Part size limited by
                   MaxPartSize and head size + 1
        mode (str): encoding mode for part header when transmitting,
                b64 'txt' or b2 'bny'



    Properties:

    """
    Version = Versionage(major=0, minor=0)  # default version
    BufCount = 64  # default bufcount bc for transport
    Code = PartDex.Basic  # default part type-version head code '__'
    MaxMemoSize = 4294836225 # (2**16-1)**2 absolute max memo size
    MaxPartSize = 65535 # (2**16-1) absolute max part size
    MaxPartCount = 16777215 # (2**24-1) absolute max part count
    Sizes = {'__': Sizage(cs=2, ms=22, ns=4, hs=28)}  # dict of part sizes keyed by part codes
    Mode = Wiffs.txt  # encoding mode for tx part header b64 'txt' or b2 'bny'


    def __init__(self,
                 name='main',
                 bc=None,
                 version=None,
                 rxgs=None,
                 sources=None,
                 counts=None,
                 rxms=None,
                 txms=None,
                 txgs=None,
                 txbs=None,
                 code=None,
                 size=None,
                 mode=None,
                 **kwa
                ):
        """Setup instance

        Inherited Parameters:
            name (str): unique name for Memoer transport. Used to manage.
            bc (int | None): count of transport buffers of MaxGramSize

        Parameters:
            version (Versionage): version for this memoir instance consisting of
                namedtuple of form (major: int, minor: int)
            rxgs (dict): keyed by mid (memoID) with value of dict where each deque
                holds incomplete memo part grams for that mid.
                The mid appears in every gram part from the same memo.
                The value dict is keyed by the part number pn, with value
                that is the part bytes.
            sources (dict): keyed by mid that holds the src for the memo indexed by its
                mid (memoID). This enables reattaching src to memo when
                placing fused memo in rxms deque.
            counts (dict): keyed by mid that holds the part count (pc) for the
                memo indexed by its mid (memoID). This enables lookup of the pc
                to memo when fusing its parts.
            rxms (deque): holding rx (receive) memo duples fused from rxgs grams
                each entry in deque is duple of form (memo: str, dst: str)
            txms (deque): holding tx (transmit) memo tuples to be partitioned into
                txgs grams where each entry in deque is duple of form
                (memo: str, dst: str)
            txgs (deque): grams to transmit, each entry is duple of form:
                (gram: bytes, dst: str).
            txbs (tuple): current transmisstion duple of form:
                (gram: bytearray, dst: str). gram bytearray may hold untransmitted
                portion when datagram is not able to be sent all at once so can
                keep trying. Nothing to send indicated by (bytearray(), None)
                for (gram, dst)
            code (bytes | None): part code for part header
            size (int): part size for this instance for transport. Part size
                = head size + body size. Part size limited by
                MaxPartSize and MaxPartCount relative to MaxMemoSize as well
                as minimum part body size of 1
            mode (str): encoding mode for part header when transmitting,
                b64 'txt' or b2 'bny'




        """
        # initialize attributes
        self.version = version if version is not None else self.Version
        self.rxgs = rxgs if rxgs is not None else dict()
        self.sources = sources if sources is not None else dict()
        self.counts = counts if counts is not None else dict()
        self.rxms = rxms if rxms is not None else deque()

        self.txms = txms if txms is not None else deque()
        self.txgs = txgs if txgs is not None else deque()
        self.txbs = txbs if txbs is not None else (bytearray(), None)

        bc = bc if bc is not None else self.BufCount  # use bufcount to calc .bs

        self.echos = deque()  # only used in testing as echoed tx

        self.code = code if code is not None else self.Code
        _, _, ns, hs = self.Sizes[self.code]
        size = size if size is not None else self.MaxPartSize
        self.size = max(min(size, self.MaxPartSize), hs + ns + 1)
        self.mode = mode if mode is not None else self.Mode

        super(Memoer, self).__init__(name=name, bc=bc, **kwa)

        if not hasattr(self, "name"):  # stub so mixin works in isolation.
            self.name = name  # mixed with subclass should provide this.

        if not hasattr(self, "opened"):  # stub so mixin works in isolation.
            self.opened = False  # mixed with subclass should provide this.


    def open(self):
        """Opens transport in nonblocking mode

        This is a stub. Override in transport specific subclass
        """
        self.opened = True
        return True


    def reopen(self):
        """Idempotently open transport
        """
        self.close()
        return self.open()


    def close(self):
        """Closes  transport

        This is a stub. Override in transport subclass
        """
        self.opened = False


    def wiff(self, part):
        """Determines encoding format of part bytes header as either base64 text
        'txt' or base2 binary 'bny' from first 6 bits (sextet) in part.

        Returns:
            wiff (Wiffs): Wiffs.txt if B64 text, Wiffs.bny if B2 binary
                                Otherwise raises hioing.MemoerError

        All part head codes start with '_' in base64 text or in base2 binary.
        Given only allowed chars are from the set of base64 then can determine
        if header is in base64 or base2.

        First sextet:  (0b is binary, 0o is octal, 0x is hexadecimal)

        0o27 = 0b010111 means first sextet of '_' in base64  => 'txt'
        0o77 = 0b111111 means first sextet of '_' in base2  => 'bny'

        Assuming that only '_' is allowed as the first char of a valid part head,
        in either Base64 or Base2 encoding, a parser can unambiguously determine
        if the part header encoding is binary Base2 or text Base64 because
        0o27 != 0o77.

        Furthermore, it just so happens that 0o27 is a unique first sextet
        among Base64 ascii chars. So an invalid part header when in Base64 encoding
        is detectable. However, there is one collision (see below) with invalid
        part headers in Base2 encoding. So an erroneously constructed part might
        not be detected merely by looking at the first sextet. Therefore
        unreliable transports must provide some additional mechanism such as a
        hash or signature on the part.

        All Base2 codes for Base64 chars are unique since the B2 codes are just
        the count from 0 to 63. There is one collision, however, between Base2 and
        Base 64 for invalid part headers. This is because 0o27 is the
        base2 code for ascii 'V'. This means that Base2 encodings
        that begin 0o27 witch is the Base2 encoding of the ascii 'V, would be
        incorrectly detected as text not binary.
        """

        sextet = part[0] >> 2
        if sextet == 0o27:
            return Wiffs.txt  # 'txt'
        if sextet == 0o77:
            return Wiffs.bny  # 'bny'

        raise hioing.Memoer(f"Unexpected {sextet=} at part head start.")


    def parse(self, part):
        """Parse and strips header from gram part bytearray and returns
        (mid, pn, pc) when first part, (mid, pn, None) when other part
        Otherwise raises MemoerError is unrecognized header

        Returns:
            result (tuple): tuple of form:
                (mid: str, pn: int, pc: int | None) where:
                mid is memoID, pn is part number, pc is part count.
                When first first part (zeroth) returns (mid, 0, pc).
                When other part returns (mid, pn, None)
                Otherwise raises memogram error.

        When valid recognized header, strips header bytes from front of part
        leaving the part body part bytearray.

        Parameters:
            part (bytearray): memo part gram from which to parse and strip its header.

        """
        cs, ms, ns, hs = self.Sizes[self.code]

        wiff = self.wiff(part)
        if wiff == Wiffs.bny:
            bhs = 3 * (hs) // 4  # binary head size
            head = part[:bhs]  # slice takes a copy
            if len(head) < bhs:  # not enough bytes for head
                raise hioing.Memoer(f"Part size b2 too small < {bhs}"
                                           f" for head.")
            head = encodeB64(head)  # convert to Base64
            del part[:bhs]  # strip head off part
        else:  # wiff == Wiffs.txt:
            head = part[:hs]  # slice takes a copy
            if len(head) < hs:  # not enough bytes for head
                raise hioing.Memoer(f"Part size b64 too small < {hs} for"
                                           f"head.")
            del part[:hs]  # strip off head off

        code = head[:cs].decode()
        if code != self.code:
            raise hioing.Memoer(f"Unrecognized part {code=}.")

        mid = head[cs:cs+ms].decode()
        pn = helping.b64ToInt(head[cs+ms:cs+ms+ns])

        pc = None
        if pn == 0:  # first (zeroth) part so get neck
            if wiff == Wiffs.bny:
                bns = 3 * (ns) // 4  # binary neck size
                neck = part[:bns]  # slice takes a copy
                if len(neck) < bns:  # not enough bytes for neck
                    raise hioing.Memoer(f"Part size b2 too small < {bns}"
                                               f" for neck.")
                neck = encodeB64(neck)  # convert to Base64
                del part[:bns]  # strip off neck
            else:  # wiff == Wiffs.txt:
                neck = part[:ns]  # slice takes a copy
                if len(neck) < ns:  # not enough bytes for neck
                    raise hioing.Memoer(f"Part size b64 too small < {ns}"
                                               f" for neck.")
                del part[:ns]  # strip off neck

            pc = helping.b64ToInt(neck)

        return (mid, pn, pc)


    def receive(self, *, echoic=False):
        """Attemps to send bytes in txbs to remote destination dst. Must be
        overridden in subclass. This is a stub to define mixin interface.

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
            raise

        if not gram:  # no received data
            return False

        part = bytearray(gram)# make copy bytearray so can strip off header

        try:
            mid, pn, pc = self.parse(part)  # parse and strip off head leaving body
        except hioing.Memoer as ex: # invalid part so drop
            logger.error("Unrecognized Memoer part from %s.\n %s.", src, ex)
            return True  # did receive data to can keep receiving

        if mid not in self.rxgs:
            self.rxgs[mid] = dict()

        # save stripped part gram to be fused later
        if pn not in self.rxgs[mid]:  # make idempotent first only no replay
            self.rxgs[mid][pn] = part  # index body by its part number

        if pc is not None:
            if mid not in self.counts:  # make idempotent first only no replay
                self.counts[mid] = pc  # save part count for mid

        # assumes unique mid across all possible sources. No replay by different
        # source only first source for a given mid is ever recognized
        if mid not in self.sources:  # make idempotent first only no replay
            self.sources[mid] = src  # save source for later


        return True  # received valid


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


    def fuse(self, parts, cnt):
        """Fuse cnt gram part bodies from parts dict into whole memo . If any
        parts are missing then returns None.

        Returns:
            memo (str | None): fused memo or None if incomplete.

        Override in subclass

        Parameters:
            parts (dict): memo part bodies each keyed by part number from which
                          to fuse memo.
            cnt (int): part count for mid
        """
        if len(parts) < cnt:  # must be missing one or more parts
            return None

        memo = bytearray()
        for i in range(cnt):  # iterate in numeric order, items are insertion ordered
            memo.extend(parts[i])  # extend memo with part body at part i

        return memo.decode()  # convert bytearray to str



    def _serviceOnceRxGrams(self):
        """Service one pass over .rxgs dict for each unique mid in .rxgs

        Deleting an item from a dict at a key (since python dicts are key
        insertion ordered) means that the next time an item is created it will
        be last.
        """
        for i, mid in enumerate(list(self.rxgs.keys())):  # items may be deleted in loop
            # if mid then parts dict at mid must not be empty
            if not mid in self.counts:  # missing first part so skip
                continue
            memo = self.fuse(self.rxgs[mid], self.counts[mid])
            if memo is not None:  # allows for empty "" memo for some src
                self.rxms.append((memo, self.sources[mid]))
                del self.rxgs[mid]
                del self.counts[mid]
                del self.sources[mid]


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
            memo, src = self._serviceOneRxMemo()
        except IndexError:
            pass


    def serviceRxMemos(self):
        """Service all memos in .rxms (greedy) if any

        Override in subclass to handle result(s) and put them somewhere
        """
        while self.rxms:
            memo, src = self._serviceOneRxMemo()


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
        """Attemps to send bytes in txbs to remote destination dst. Must be
        overridden in subclass. This is a stub to define mixin interface.

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



    def memoit(self, memo, dst):
        """Append (memo, dst) duple to .txms deque

        Parameters:
            memo (str): to be segmented and packed into gram(s)
            dst (str): address of remote destination of memo
        """
        self.txms.append((memo, dst))


    def rend(self, memo):
        """Partition memo into packed part grams with headers.

        Returns:
            parts (list[bytes]): list of part grams with headers.

        Parameters:
            memo (str): to be partitioned into gram parts with headers

        Note first part has head + neck overhead, hs + ns so bs is smaller by ns
             non-first parts have just head overhead hs so bs is bigger by ns
        """
        parts = []
        memo = bytearray(memo.encode()) # convert and copy to bytearray

        cs, ms, ns, hs = self.Sizes[self.code]
        # self.size is max part size
        bs = (self.size - hs)  # max standard part body size,
        mms = min(self.MaxMemoSize, (bs * self.MaxPartCount) - ns)  # max memo payload
        ml = len(memo)
        if ml > mms:
            raise hioing.Memoer(f"Memo length={ml} exceeds max={mms}.")

        # memo ID is 16 byte random UUID converted to 22 char Base64 right aligned
        midb = encodeB64(bytes([0] * 2) + uuid.uuid4().bytes)[2:] # prepad, convert, and strip
        #mid = midb.decode()
        # compute part count account for added neck overhead in first part
        pc = math.ceil((ml + ns - bs)/bs + 1)  # includes added neck ns overhead
        neck = helping.intToB64b(pc, l=ns)
        if self.mode == Wiffs.bny:
            neck = decodeB64(neck)
        pn = 0
        while memo:
            pnb = helping.intToB64b(pn, l=ns)  # pn size always == neck size
            head = self.code.encode() + midb + pnb
            if self.mode == Wiffs.bny:
                head = decodeB64(head)
            if pn == 0:
                part = head + neck + memo[:bs-ns]  # copy slice past end just copies to end
                del memo[:bs-ns]  # del slice past end just deletes to end
            else:
                part = head + memo[:bs]  # copy slice past end just copies to end
                del memo[:bs]  # del slice past end just deletes to end
            parts.append(part)

            pn += 1

        return parts


    def _serviceOneTxMemo(self):
        """Service one (memo, dst) duple from .txms deque where duple is of form
            (memo: str, dst: str) where:
                memo is outgoing memo
                dst is destination address
        Calls .segment method to process the segmentation and packing as
        appropriate to convert memo into gram(s).
        Appends duples of (gram, dst) from grams to .txgs deque.
        """
        memo, dst = self.txms.popleft()  # raises IndexError if empty deque

        for part in self.rend(memo):  # partition memo into gram parts with head
            self.txgs.append((part, dst))  # append duples (gram: bytes, dst: str)


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
            else:
                raise  # unexpected error

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

    service = serviceAll  # alias override peer service method


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


    def enter(self):
        """"""
        self.peer.reopen()


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

        Stub override in subclass
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
        if self.tymth:
            self.peer.wind(self.tymth)


    def wind(self, tymth):
        """Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(TymeeMemoerDoer, self).wind(tymth)
        self.peer.wind(tymth)


    def enter(self):
        """"""
        self.peer.reopen()


    def recur(self, tyme):
        """"""
        self.peer.service()


    def exit(self):
        """"""
        self.peer.close()
