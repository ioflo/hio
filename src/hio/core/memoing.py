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
However, the existence of the UDP and IP
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
protocol headers could be added in some circumstances. A more conservative
value of around 300-400 bytes may be preferred instead.

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


SO_SNDBUF
              Sets  or  gets  the  maximum socket send buffer in bytes.  The kernel doubles this value (to allow
              space for bookkeeping overhead) when it is set using setsockopt(2),  and  this  doubled  value  is
              returned  by  getsockopt(2).  The default value is set by the /proc/sys/net/core/wmem_default file
              and the maximum allowed value  is  set  by  the  /proc/sys/net/core/wmem_max  file.   The  minimum
              (doubled) value for this option is 2048.

https://stackoverflow.com/questions/21856517/whats-the-practical-limit-on-the-size-of-single-packet-transmitted-over-domain

"""
import socket
import errno

from collections import deque, namedtuple

from .. import hioing

# namedtuple of ints (major: int, minor: int)
Versionage = namedtuple("Versionage", "major minor")

class Memoir(hioing.Mixin):
    """
    Memoir mixin base class to adds memogram support to a transport class.
    Memoir supports asynchronous memograms. Provides common methods for subclasses.

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
        transport class. For example MemoirUdp or MemoGramUdp or MemoirUxd or
        MemoGramUXD

    Each direction of dataflow uses a triple-tiered set of buffers that respect
    the constraints of non-blocking asynchronous IO with datagram transports.

    On the transmit side memos are placed in a deque (double ended queue). Each
    memor is then segmented into grams (datagrams) the respect the size constraints
    of the underlying datagram transport. These grams are placed in another deque.
    Each gram in its deque is then places in a transmit buffer to be sent over the
    transport. When using non-blocking IO, asynchronous datagram transport
    protocols may have hidden buffering constraints that result in fragmentation
    of the sent datagram which means the whole datagram is not sent at once via
    a non-blocking send call. This means that the remainer of the datagram must
    be sent later and may take multiple send calls to complete. The datagram
    protocol is responsible for managing the buffering and fragmentation but
    depends on the sender repeated attempts to send the reaminder of the
    full datagram. This is ensured with the final tier with a raw transmit
    buffer that waits until it is empty before attempting to send another
    gram.

    On the receive the raw data is received into the raw data buffer. This is then
    converted into a gram and queued in the gram receive deque as a seqment of
    a memo. The grams in the gram recieve deque are then desegmented into a memo
    and placed in the memo deque for consumption by the application or some other
    higher level protocol.

    Memo segmentation information is embedded in the grams.


    Class Attributes:
        Version (Versionage): default version consisting of namedtuple of form
            (major: int, minor: int)

    Attributes:
        version (Versionage): version for this memoir instance consisting of
                namedtuple of form (major: int, minor: int)
        rxbs (bytearray): buffer holding rx (receive) data from raw transport
        txbs (bytearray): buffer holding tx (transmit) raw data to raw transport
        rxgs (deque): holding rx (receive) (data) grams (segments) recieved via rxbs raw
        txgs (deque): holding tx (transmit) (data) grams (segments) to be sent via txbs raw
        rxms (deque): holding rx (receive) memos desegmented from rxgs grams
        txms (deque): holding tx (transmit) memos to be segmented into txgs grams


    Properties:


    """

    Version = Versionage(major=0, minor=0)  # default version

    def __init__(self,
                 version=None,
                 rxbs=None,
                 txbs=None,
                 rxgs=None,
                 txgs=None,
                 rxms=None,
                 txms=None,
                 **kwa
                ):
        """Setup instance

        Inherited Parameters:


        Parameters:
            version (Versionage): version for this memoir instance consisting of
                namedtuple of form (major: int, minor: int)

            txbs (bytearray): buffer holding tx (transmit) raw data to raw transport
            rxbs (bytearray): buffer holding rx (receive) data from raw transport

            txgs (deque): holding tx (transmit) (data) grams to be sent via txbs raw
            rxgs (deque): holding rx (receive) (data) grams recieved via rxbs raw

            txms (deque): holding tx (transmit) memos to be segmented into txgs grams
            rxms (deque): holding rx (receive) memos desegmented from rxgs grams



        """
        # initialize attributes
        self.version = version if version is not None else self.Version


        self.txbs = txbs if txbs is not None else bytearray()
        self.rxbs = rxbs if rxbs is not None else bytearray()

        self.txgs = txgs if txgs is not None else deque()
        self.rxgs = rxgs if rxgs is not None else deque()


        self.txms = txms if txms is not None else deque()
        self.rxms = rxms if rxms is not None else deque()

        super(Memoir, self).__init__(**kwa)


        if not hasattr(self, "opened"):  # stub so mixin works in isolation
            self.opened = False  # mixed with subclass should provide this.

    def send(self, txbs, dst):
        """Attemps to send bytes in txbs to remote destination dst. Must be
        overridden in subclass. This is a stub to define mixin interface.

        Returns:
            count (int): bytes actually sent

        Parameters:
            txbs (bytes | bytearray): of bytes to send
            dst (str): remote destination address
        """
        return 0

    def clearTxbs(self):
        """
        Clear .txbs
        """
        self.txbs.clear()


    def clearRxbs(self):
        """
        Clear .rxbs
        """
        del self.rxbs.clear()


    def memoit(self, memo, dst):
        """Append (memo, dst) duple to .txms deque

        Parameters:
            memo (str): to be segmented and packed into gram(s)
            dst (str): address of remote destination of memo
        """
        self.txms.append((memo, dst))


    def segment(self, memo):
        """Segment and package up memo into grams.
        This is a stub method meant to be overridden in subclass

        Returns:
            grams (list): packed segments of memo

        Parameters:
            memo (str): to be segmented into grams
        """
        grams = []
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
        memo, dst = self.txms.popleft()  # duple (msg, destination addr)
        grams = self.segment(memo)
        for gram in grams:
            self.txgs.append((gram, dst))


    def serviceTxMemosOnce(self):
        """Service one outgoing memo from .txms deque if any (non-greedy)
        """
        if self.txms:
            self._serviceOneTxMemo()


    def serviceTxMemos(self):
        """Service all outgoing memos in .txms deque if any (greedy)
        """
        while self.txms:
            self._serviceOneTxMemo()


    def gramit(self, gram, dst):
        """Append (gram, dst) duple to .txgs deque

        Parameters:
            gram (str): gram to be sent
            dst (str): address of remote destination of gram
        """
        self.txgs.append((gram, dst))


    def _serviceOneTxGram(self):
        """Service one (gram, dst) duple from .txgs deque for each unique dst
        if more than one, where duple is of form
            (gram: str, dst: str) where:
                gram is outgoing gram segment from associated memo
                dst is destination address

        Returns:
            result (bool): True means full gram sent so can send another
                           False means full gram not sent so try again later

        Copies gram to .txbs buffer and sends to dst keeping track of the actual
        portion sent and then deletes the sent portion from .txbs leaving the
        remainder.

        When there is a remainder each subsequent call of this method
        will attempt to send the remainder until the the full gram has been sent.
        This accounts for datagramprotocols that expect continuing attempts to
        send remainder of a datagram when using nonblocking sends.

        When there is no remainder then takes a gram from .txgs and sends it.

        Internally, an empty .txbs indicates its ok to take another gram from
        .txgs and start sending it.

        The return value True or False enables backpressure on greedy callers
        to block waiting for current gram to be fully sent.
        """
        if not self.txbs:  # everything sent last time
            gram, dst = self.txgs.popleft()
            self.txbs.extend(gram)

        count = self.send(self.txbs, dst)  # assumes opened

        if count < len(self.txbs):  # delete sent portion
            del self.txbs[:count]
            return False  # partially blocked try send of remainder later

        self.clearTxbs()
        return True  # fully sent so can sent another gramm, not blocked

    def _serviceOneTxPkt(self, laters, blockeds):
        """
        Service one (packet, ha) duple on .txPkts deque
        Packet is assumed to be packed already in .packed
        Assumes there is a duple on the deque
        laters is deque of packed packets to try again later
        blockeds is list of ha destinations that have already blocked on this pass
        Override in subclass
        """
        pkt, ha = self.txPkts.popleft()  # duple = (packet, destination address)

        if ha in blockeds: # already blocked on this iteration
            laters.append((pkt, ha)) # keep sequential
            return False  # blocked

        try:
            count = self.handler.send(pkt.packed, ha)  # datagram always sends all
        except socket.error as ex:
            # ex.args[0] is always ex.errno for better compat
            if (ex.args[0] in (errno.ECONNREFUSED,
                               errno.ECONNRESET,
                               errno.ENETRESET,
                               errno.ENETUNREACH,
                               errno.EHOSTUNREACH,
                               errno.ENETDOWN,
                               errno.EHOSTDOWN,
                               errno.ETIMEDOUT,
                               errno.ETIME)):  # ENOBUFS  ENOMEM
                # problem sending such as busy with last message. save it for later
                laters.append((pkt, ha))
                blockeds.append(ha)
            else:
                raise

        console.profuse("{0}: sent to {1}\n    0x{2}\n".format(self.name,
                                                          ha,
                                                          hexlify(pkt.packed).decode('ascii')))
        return True  # not blocked

    def serviceTxPkts(self):
        """
        Service the .txPcks deque to send packets through server
        Override in subclass
        """
        if self.handler.opened:
            laters = deque()
            blockeds = []
            while self.txPkts:
                again = self._serviceOneTxPkt(laters, blockeds)
                if not again:
                    break
            while laters:
                self.txPkts.append(laters.popleft())

    def serviceTxPktsOnce(self):
        '''
        Service .txPkts deque once (one pkt)
        '''
        if self.handler.opened:
            laters = deque()
            blockeds = [] # will always be empty since only once
            if self.txPkts:
                self._serviceOneTxPkt(laters, blockeds)
            while laters:
                self.txPkts.append(laters.popleft())

    def serviceTxGramsOnce(self):
        """Service one outgoing gram from .txgs deque if any (non-greedy)
        """
        if self.opened and self.txgs:
            self._serviceOneTxGram()


    def serviceTxGrams(self):
        """Service all outgoing grams in .txgs deque if any (greedy) until
        blocked by pending transmissions on transport.
        """
        while self.opened and self.txgs:
            if not self._serviceOneTxGram():
                break  # blocked try again later


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


    def _serviceOneReceived(self):
        """
        Service one received raw packet data or chunk from .handler
        assumes that there is a .handler
        Override in subclass
        """
        while True:  # keep receiving until empty
            try:
                raw = self.receive()
            except Exception as ex:
                raise

            if not raw:
                return False  # no received data
            self.rxbs.extend(raw)

        packet = self.parserize(self.rxbs[:])

        if packet is not None:  # queue packet
            console.profuse("{0}: received\n    0x{1}\n".format(self.name,
                                        hexlify(self.rxbs[:packet.size]).decode('ascii')))
            del self.rxbs[:packet.size]
            self.rxPkts.append(packet)
        return True  # received data

    def _serviceOneReceived(self):
        '''
        Service one received duple (raw, ha) raw packet data or chunk from server
        assumes that there is a server
        Override in subclass
        '''
        try:
            raw, ha = self.handler.receive()  # if no data the duple is (b'', None)
        except socket.error as ex:
            # ex.args[0] always ex.errno for compat
            if (ex.args[0] == (errno.ECONNREFUSED,
                               errno.ECONNRESET,
                               errno.ENETRESET,
                               errno.ENETUNREACH,
                               errno.EHOSTUNREACH,
                               errno.ENETDOWN,
                               errno.EHOSTDOWN,
                               errno.ETIMEDOUT,
                               errno.ETIME)):
                return False  # no received data
            else:
                raise

        if not raw:  # no received data
            return False

        packet = self.parserize(raw, ha)
        if packet is not None:
            console.profuse("{0}: received\n    0x{1}\n".format(self.name,
                                        hexlify(raw).decode('ascii')))
            self.rxPkts.append((packet, ha))     # duple = ( packed, source address)
        return True  # received data

    def serviceReceives(self):
        """
        Retrieve from server all received and queue up
        """
        while self.opened:
            if not self._serviceOneReceived():
                break

    def serviceReceivesOnce(self):
        """
        Service receives once (one reception) and queue up
        """
        if self.opened:
            self._serviceOneReceived()

    def messagize(self, pkt, ha):
        """
        Returns duple of (message, remote) converted from rx packet pkt and ha
        Override in subclass
        """
        msg = pkt.packed.decode("ascii")
        try:
            remote = self.haRemotes[ha]
        except KeyError as ex:
            console.verbose(("{0}: Dropping packet received from unknown remote "
                             "ha '{1}'.\n{2}\n".format(self.name, ha, pkt.packed)))
            return (None, None)
        return (msg, remote)



    def _serviceOneRxPkt(self):
        """
        Service pkt from .rxPkts deque
        Assumes that there is a message on the .rxes deque
        """
        pkt = self.rxPkts.popleft()
        console.verbose("{0} received packet\n{1}\n".format(self.name, pkt.show()))
        self.incStat("pkt_received")
        message = self.messagize(pkt)
        if message is not None:
            self.rxMsgs.append(message)

    def serviceRxPkts(self):
        """
        Process all duples  in .rxPkts deque
        """
        while self.rxPkts:
            self._serviceOneRxPkt()

    def serviceRxPktsOnce(self):
        """
        Service .rxPkts deque once (one pkt)
        """
        if self.rxPkts:
            self._serviceOneRxPkt()

    def _serviceOneRxMsg(self):
        """
        Service one duple from .rxMsgs deque
        """
        msg = self.rxMsgs.popleft()


    def serviceRxMsgs(self):
        """
        Service .rxMsgs deque of duples
        """
        while self.rxMsgs:
            self._serviceOneRxMsg()

    def serviceRxMsgsOnce(self):
        """
        Service .rxMsgs deque once (one msg)
        """
        if self.rxMsgs:
            self._serviceOneRxMsg()


    def serviceAllRx(self):
        """
        Service receive side of stack
        """
        self.serviceReceives()
        self.serviceRxPkts()
        self.serviceRxMsgs()
        self.serviceTimers()

    def serviceAllRxOnce(self):
        """
        Service receive side of stack once (one reception)
        """
        self.serviceReceivesOnce()
        self.serviceRxPktsOnce()
        self.serviceRxMsgsOnce()
        self.serviceTimers()

    def serviceAll(self):
        """
        Service all Rx and Tx
        """
        self.serviceAllRx()
        self.serviceAllTx()

    def serviceLocal(self):
        """
        Service the local Peer's receive and transmit queues
        """
        self.serviceReceives()
        self.serviceTxPkts()









