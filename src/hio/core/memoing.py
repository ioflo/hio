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

"""
from collections import deque

from .. import hioing



class MemoirBase(hioing.Mixin):
    """
    Base Memoir object.
    Base class for memogram support
    Provides common methods for subclasses
    Do not instantiate but use a subclass
    """

    def __init__(self,
                 version=None,
                 rxbs=None,
                 rxPkts=None,
                 rxMsgs=None,
                 txbs=None,
                 txPkts=None,
                 txMsgs=None,
                 **kwa
                ):
        """
        Setup instance

        Inherited Parameters:


        Parameters:
            version is version tuple or string for this memoir instance
            rxbs is bytearray buffer to hold rx data stream if any
            rxPkts is deque to hold received packet if any
            rxMsgs is deque to hold received msgs if any
            txbs is bytearray buffer to hold rx data stream if any
            txPkts is deque to hold packet to be transmitted if any
            txMsgs is deque to hold messages to be transmitted if any

        Inherited Attributes:

        Attributes:
            .version is version tuple or string for this stack
            .rxbs is bytearray buffer to hold input data stream
            .rxPkts is deque to hold received packets
            .rxMsgs is to hold received msgs
            .txbs is bytearray buffer to hold rx data stream if any
            .txPkts is deque to hold packets to be transmitted
            .txMsgs is deque to hold messages to be transmitted

        Inherited Properties:

        Properties:


        """
        super(MemoirBase, self).__init__(**kwa)

        self.version = version

        self.rxbs = rxbs if rxbs is not None else bytearray()
        self.rxPkts = rxPkts if rxPkts is not None else deque()
        self.rxMsgs = rxMsgs if rxMsgs is not None else deque()
        self.txbs = txbs if txbs is not None else bytearray()
        self.txPkts = txPkts if txPkts is not None else deque()
        self.txMsgs = txMsgs if txMsgs is not None else deque()


    def clearTxbs(self):
        """
        Clear .txbs
        """
        del self.txbs[:]  # self.txbs.clear() not supported before python 3.3

    def _serviceOneTxPkt(self):
        """
        Service one (packet, ha) duple on .txPkts deque
        Packet is assumed to be packed already in .packed
        Override in subclass
        """
        pkt = None
        if not self.txbs:  # everything sent last time
            pkt, ha = self.txPkts.popleft()
            self.txbs.extend(pkt.packed)

        try:
            count = self.send(self.txbs, ha)
        except Exception as ex:
            raise



        if count < len(self.txbs):  # delete sent portion
            del self.txbs[:count]
            return False  # partially blocked try again later

        self.clearTxbs()
        return True  # not blocked


    def serviceTxPkts(self):
        """
        Service the .txPkts deque to send packets through server
        Override in subclass
        """
        while self.opened and self.txPkts:
            if not self._serviceOneTxPkt():
                break  # blocked try again later

    def serviceTxPktsOnce(self):
        '''
        Service .txPkts deque once (one pkt)
        '''
        if self.opened and self.txPkts:
            self._serviceOneTxPkt()


    def transmit(self, pkt, ha=None):
        """
        Pack and Append (pkt, ha) duple to .txPkts deque
        Override in subclass
        """
        try:
            pkt.pack()
        except ValueError as ex:
            emsg = "{}: Error packing pkt.\n{}\n{}\n".format(self.name, pkt, ex)
            console.terse(emsg)

        else:
            self.txPkts.append((pkt, ha))


    def packetize(self, msg, remote=None):
        """
        Returns packed packet created from msg destined for remote
        Remote provided if attributes needed to fill in packet
        Override in subclass
        """
        packet = packeting.Packet(stack=self, packed=msg.encode('ascii'))
        try:
            packet.pack()
        except ValueError as ex:
            emsg = "{}: Error packing msg.\n{}\n{}\n".format(self.name, msg, ex)
            console.terse(emsg)

            return None
        return packet


    def _serviceOneTxMsg(self):
        """
        Handle one (message, remote) duple from .txMsgs deque
        Assumes there is a duple on the deque
        Appends (packet, ha) duple to txPkts deque
        """
        msg, remote = self.txMsgs.popleft()  # duple (msg, destination uid
        console.verbose("{0} sending to {1}\n{2}\n".format(self.name,
                                                           remote.name,
                                                           msg))
        packet = self.packetize(msg, remote)
        if packet is not None:
            self.txPkts.append((packet, remote.ha))


    def serviceTxMsgs(self):
        """
        Service .txMsgs deque of outgoing  messages
        """
        while self.txMsgs:
            self._serviceOneTxMsg()

    def serviceTxMsgOnce(self):
        """
        Service .txMsgs deque once (one msg)
        """
        if self.txMsgs:
            self._serviceOneTxMsg()

    def message(self, msg, remote=None):
        """
        Append (msg, remote) duple to .txMsgs deque
        If destination remote not given
        Then use zeroth remote If any otherwise Raise exception
        Override in subclass
        """
        if remote is None:
            if not self.remotes:
                emsg = "No remote to send to.\n"
                console.terse(emsg)

                return
            remote = self.remotes.values()[0]
        self.txMsgs.append((msg, remote))

    def serviceAllTx(self):
        '''
        Service:
           txMsgs queue
           txes queue to server send
        '''
        self.serviceTxMsgs()
        self.serviceTxPkts()

    def serviceAllTxOnce(self):
        """
        Service the transmit side of the stack once (one transmission)
        """
        self.serviceTxMsgOnce()
        self.serviceTxPktsOnce()

    def clearRxbs(self):
        """
        Clear .rxbs
        """
        del self.rxbs[:]  # self.rxbs.clear() not supported before python 3.3

    def parserize(self, raw):
        """
        Returns packet parsed from raw data
        Override in subclass
        """
        packet = packeting.Packet(stack=self)
        try:
            packet.parse(raw=raw)
        except ValueError as ex:
            emsg = "{}: Error parsing raw.\n{}\n{}\n".format(self.name, raw, ex)
            console.terse(emsg)
            self.incStat("pkt_parse_error")
            return None
        return packet

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









