# -*- encoding: utf-8 -*-
"""
hio.core.memoing Module

Mixin Base Classes that add support for MemoGrams to datagram based transports.

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

HeadSize = 32  # base64 chars
codeb64b = b'__"
midb64b = encodeB64(bytes([0] * 2) + uuid.uuid4().bytes)[2:] # prepad, convert,  and strip
pn = 1
pnb64b = helping.intToB64b(pn, l=3)
pc = 2
pcb64b = helping.intToB64b(pc, l=3)

headb64b = codeb64b + midb64b + pnb64b + pcb64b
assert helping.Reb64.match(headb64b)

codeb64b = headb64b[:2]
mid = helping.b64ToInt(b'AA' + headb64b[2:24]))  # prepad and convert
pn = helping.b64ToInt(headb64b[24:28]))
pc = helping.b64ToInt(headb64b[28:32]))


PartCode Typing/Versions uses a different base64 two char code.
Codes always start with `_` and second char in code starts at `_`
and walks backwards through B64 code table for each part type-version (tv) code.
Total head length including code must be a multiple of 4 characters so
converts to/from B2 without padding. So to change length in order to change
field lengths or add or remove fields need a new part (tv) code.

To reiterate, if ever need to change anything ned a new part tv code. There are
no versions per type.  This is deemed sufficient because anticipate a very
limited set of possible fields ever needed for memogram transport types.

tv 0 is '__'
tv 1 is '_-'
tv 3 is '_9'

Because the part headers are valid mid-pad B64 primitives then can be losslessly
transformed to/from CESR primitives merely by translated the part tv code to
an  equivalent entry in the  two char cesr primitive code table.
The CESR codes albeit different are one-to-one. This enables representing headers
as CESR primitives for management but not over the wire. I.e. can transform
Memogram Parts to CESR primitives to tunnel in some CESR stream.

Normally CESR streams are tunneled inside Memograms sent over-the-wire. When
the MemoGram is the wrapper then use the part tv code not the equivalent CESR code.
By using so the far reserved and unused '_' CESR op code table selector char
from CESR it makes it obvious that its a Memogram
tv Part Code not a CESR code when debugging. Even when the op codes are defined
its not likely to be confusing since the context of CESR op codes is different.
Morover when the MemoGram is a CESR Stream, a memogram parser will parse and
strip the MemoGram wrappers to construct the MemoGram, so no collisions.



HeadCode hc = b'__'
HeadCodeSize hcs = 2
MemoIDSize mis = 22
PartNumSize pns = 4
PartCntSize pcs = 4
PartHeadSize phs  = 32


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


"""
import socket
import errno
import struct

from collections import deque, namedtuple
from contextlib import contextmanager
from base64 import urlsafe_b64encode as encodeB64
from base64 import urlsafe_b64decode as decodeB64

from hio import hioing, help
from hio.base import tyming, doing

logger = help.ogler.getLogger()

# namedtuple of ints (major: int, minor: int)
Versionage = namedtuple("Versionage", "major minor")

# namedtuple for size entries in MemoGram Pizes (part sizes) table
# cs is the part head size int number of chars in part code
# phs is the soft size int number of chars in soft (unstable) part of code
# xs is the xtra size into number of xtra (pre-pad) chars as part of soft
# fs is the full size int number of chars in code plus appended material if any
# ls is the lead size int number of bytes to pre-pad pre-converted raw binary
Sizage = namedtuple("Sizage", "hs ss xs fs ls")



@contextmanager
def openMG(cls=None, name="test", **kwa):
    """
    Wrapper to create and open MemoGram instances
    When used in with statement block, calls .close() on exit of with block

    Parameters:
        cls (Class): instance of subclass instance
        name (str): unique identifer of MemoGram peer.
            Enables management of transport by name.
    Usage:
        with openMemoGram() as peer:
            peer.receive()

        with openMemoGram(cls=MemoGramSub) as peer:
            peer.receive()

    """
    peer = None

    if cls is None:
        cls = MemoGram
    try:
        peer = cls(name=name, **kwa)
        peer.reopen()

        yield peer

    finally:
        if peer:
            peer.close()


class MemoGram(hioing.Mixin):
    """
    MemoGram mixin base class to adds memogram support to a transport class.
    MemoGram supports asynchronous memograms. Provides common methods for subclasses.

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
        transport class. For example MemoGramUdp or MemoGramUxd

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

    Inherited Attributes:
        name (str):  unique name for MemoGram transport. Used to manage.
        opened (bool):  True means transport open for use
                        False otherwise
        bc (int | None): count of transport buffers of MaxGramSize

    Attributes:
        version (Versionage): version for this memoir instance consisting of
                namedtuple of form (major: int, minor: int)
        rxgs (dict): holding rx (receive) (data) gram deques of grams.
            Each item in dict has key=src and val=deque of grames received
            from transport. Each item of form (src: str, gram: deque)
        rxms (deque): holding rx (receive) memo duples desegmented from rxgs grams
                each entry in deque is duple of form (memo: str, dst: str)
        txms (deque): holding tx (transmit) memo tuples to be segmented into
                txgs grams where each entry in deque is duple of form
                (memo: str, dst: str)
        txgs (deque): grams to transmit, each entry is duple of form:
                (gram: bytes, dst: str).
        txbs (tuple): current transmisstion duple of form:
            (gram: bytearray, dst: str). gram bytearray may hold untransmitted
            portion when datagram is not able to be sent all at once so can# namedtuple for size entries in Matter  and Counter derivation code tables
# hs is the hard size int number of chars in hard (stable) part of code
# ss is the soft size int number of chars in soft (unstable) part of code
# xs is the xtra size into number of xtra (pre-pad) chars as part of soft
# fs is the full size int number of chars in code plus appended material if any
# ls is the lead size int number of bytes to pre-pad pre-converted raw binary
Sizage = namedtuple("Sizage", "hs ss xs fs ls")

            keep trying. Nothing to send indicated by (bytearray(), None)
            for (gram, dst)


        rxgs dict keyed by mid (memo id) that holds incomplete memo parts.
            The mid appears in every gram part from the same memo.
            each val is dict of received gram parts keyed by part number.

        srcs is dict keyed by mid that holds the src for that mid. This allows
            reattaching src to memo when placing in rxms deque


        mids (dict): of dicts keyed by src and each value dict keyed by

        echos (deque): holding echo receive duples for testing. Each duple of

        pc (bytes | None): part code for part header
                        form: (gram: bytes, dst: str).
        ps (int): part size for this instance for transport. Part size
                   = part head size  + part body size. Part size limited by
                   MaxPartSize and PartHeadSize + 1
        mms (int): max memo size relative to part size. Limited by MaxMemoSize
                    and MaxPartCount for the part size.


    Properties:




    """
    Version = Versionage(major=0, minor=0)  # default version
    BufCount = 64  # default bufcount bc for transport
    PartCode = b'__'  # default part type-version code for head
    MaxMemoSize = 4294836225 # (2**16-1)**2 absolute max memo size
    MaxPartSize = 65535 # (2**16-1) absolute max part size
    MaxPartCount = 16777215 # (2**24-1) absolute max part count
    PartHeadSizes = {b'__': 32}  # dict of part head sizes keyed by part codes


    def __init__(self,
                 name='main',
                 bc=None,
                 version=None,
                 rxgs=None,
                 rxms=None,
                 txms=None,
                 txgs=None,
                 txbs=None,
                 pc=None,
                 ps=None,
                 **kwa
                ):
        """Setup instance

        Inherited Parameters:
            name (str): unique name for MemoGram transport. Used to manage.
            bc (int | None): count of transport buffers of MaxGramSize

        Parameters:
            version (Versionage): version for this memoir instance consisting of
                namedtuple of form (major: int, minor: int)
            rxgs (dict): holding rx (receive) (data) gram deques of grams.
                Each item in dict has key=src and val=deque of grams received
                from transport. Each item of form (src: str, gram: deque)
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
            pc (bytes | None): part code for part header
            ps (int): part size for this instance for transport. Part size
                   = part head size  + part body size. Part size limited by
                   MaxPartSize and MaxPartCount relative to MaxMemoSize as well
                   as minimum part body size of 1
            pbs (int): part body size = part size - part head size for given
                       part code. Part body size must be at least 1.
            mms (int): max memo size relative to part size and limited by
                        MaxMemoSize and MaxPartCount for given part size.



        """
        # initialize attributes
        self.version = version if version is not None else self.Version
        self.rxgs = rxgs if rxgs is not None else dict()
        self.rxms = rxms if rxms is not None else deque()

        self.txms = txms if txms is not None else deque()
        self.txgs = txgs if txgs is not None else deque()
        self.txbs = txbs if txbs is not None else (bytearray(), None)

        bc = bc if bc is not None else self.BufCount  # use bufcount to calc .bs

        self.echos = deque()  # only used in testing as echoed tx

        self.pc = pc if pc is not None else self.PartCode
        phs = self.PartHeadSizes[self.pc] # part head size
        ps = ps if ps is not None else self.MaxPartSize
        self.ps = max(min(ps, self.MaxPartSize), phs + 1)
        self.pbs = (self.ps - phs)  # part body size
        self.mms = min(self.MaxMemoSize, self.pbs * self.MaxPartCount)

        super(MemoGram, self).__init__(name=name, bc=bc, **kwa)

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

        if src not in self.rxgs:
            self.rxgs[src] = deque()

        self.rxgs[src].append(gram)

        return True  # received data


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
            echo = None  # only echo once


    def fuse(self, grams):
        """Fuse gram parts from frams deque into whole memo. If grams is
        missing any the parts for a whole memo then returns None.

        Returns:
            memo (str | None): fused memo or None if incomplete.

        Override in subclass

        Parameters:
            grams (deque): gram segments from which to fuse memo parts.
        """
        try:
            gram = grams.popleft()
            memo = gram.decode()
        except IndexError:
            return None

        return memo


    def _serviceOnceRxGrams(self):
        """Service one pass over .rxgs dict for each unique src in .rxgs

        Returns:
            result (bool):  True means at least one src has received a memo and
                                has writing grams so can keep desegmenting.
                            False means all sources waiting for more grams
                                so try again later.

        The return value True or False enables back pressure on greedy callers
        so they know when to block waiting for at least one source with received
        memo and additional grams to desegment.

        Deleting an item from a dict at a key (since python dicts are key creation
        ordered) means that the next time an item is created at that key, that
        item will be last in order. In order to dynamically change the ordering
        of iteration over sources,  when there are no received grams from a
        given source we remove its dict item. This reorders the source
        as last when a new gram is received and avoids iterating over sources
        with no received grams.

        """
        goods = [False] * len(self.rxgs)  # list by src, True memo False no-memo
        # service grams to desegment
        for i, src in enumerate(list(self.rxgs.keys())):  # list since items may be deleted in loop
            # if src then grams deque at src must not be empty
            memo = self.fuse(self.rxgs[src])
            if memo is not None:  # allows for empty "" memo for some src
                self.rxms.append((memo, src))

            if not self.rxgs[src]:  # deque at src empty so remove deque
                del self.rxgs[src]  # makes src unordered until next memo at src

            if memo is not None:  # received and desegmented memo
                if src in self.rxgs:  # more received gram(s) at src
                    goods[i] = True  # indicate memo recieved with more received gram(s)

        return any(goods)  # at least one memo from a source with more received grams


    def serviceRxGramsOnce(self):
        """Service one pass (non-greedy) over all unique sources in .rxgs
        dict if any for received incoming grams.
        """
        if self.rxgs:
            self._serviceOnceRxGrams()


    def serviceRxGrams(self):
        """Service multiple passes (greedy) over all unqique sources in
        .rxgs dict if any for sources with complete desegmented memos and more
        incoming grams.
        """
        while self.rxgs:
            if not self._serviceOnceRxGrams():
                break


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


    def part(self, memo):
        """Partition memo into parts as grams.
        This is a stub method meant to be overridden in subclass

        Returns:
            grams (list[bytes]): packed segments of memo, each seqment is bytes

        Parameters:
            memo (str): to be segmented into grams
        """
        grams = [memo.encode()]
        return grams


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
        grams = self.part(memo)
        for gram in grams:
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



class MemoGramDoer(doing.Doer):
    """MemoGram Doer for reliable transports that do not require retry tymers.

    See Doer for inherited attributes, properties, and methods.

    Attributes:
       .peer (MemoGram): underlying transport instance subclass of MemoGram

    """

    def __init__(self, peer, **kwa):
        """Initialize instance.

        Parameters:
           peer (Peer): is MemoGram Subclass instance
        """
        super(MemoGramDoer, self).__init__(**kwa)
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

@contextmanager
def openTMG(cls=None, name="test", **kwa):
    """
    Wrapper to create and open TymeeMemoGram instances
    When used in with statement block, calls .close() on exit of with block

    Parameters:
        cls (Class): instance of subclass instance
        name (str): unique identifer of MemoGram peer.
            Enables management of transport by name.
    Usage:
        with openMemoGram() as peer:
            peer.receive()

        with openMemoGram(cls=MemoGramSub) as peer:
            peer.receive()

    """
    peer = None

    if cls is None:
        cls = TymeeMemoGram
    try:
        peer = cls(name=name, **kwa)
        peer.reopen()

        yield peer

    finally:
        if peer:
            peer.close()


class TymeeMemoGram(tyming.Tymee, MemoGram):
    """TymeeMemoGram mixin base class to add tymer support for unreliable transports
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
        super(TymeeMemoGram, self).__init__(**kwa)
        self.tymeout = tymeout if tymeout is not None else self.Tymeout
        #self.tymer = tyming.Tymer(tymth=self.tymth, duration=self.tymeout) # retry tymer


    def wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(TymeeMemoGram, self).wind(tymth)
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


class TymeeMemoGramDoer(doing.Doer):
    """TymeeMemoGram Doer for unreliable transports that require retry tymers.

    See Doer for inherited attributes, properties, and methods.

    Attributes:
       .peer (TymeeMemoGram) is underlying transport instance subclass of TymeeMemoGram

    """

    def __init__(self, peer, **kwa):
        """Initialize instance.

        Parameters:
           peer (TymeeMemoGram):  subclass instance
        """
        super(TymeeMemoGramDoer, self).__init__(**kwa)
        self.peer = peer
        if self.tymth:
            self.peer.wind(self.tymth)


    def wind(self, tymth):
        """Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(TymeeMemoGramDoer, self).wind(tymth)
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
