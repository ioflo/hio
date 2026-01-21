# -*- encoding: utf-8 -*-
"""
hio.core.udp.peermemoing Module
"""
from contextlib import contextmanager

from ... import help

from ...base import doing
from ...base.tyming import Tymer
from ..udp import Peer
from ..memo import Memoer

logger = help.ogler.getLogger()


class PeerMemoer(Peer, Memoer):
    """Class for sending memograms over UXD transport
    Mixin base classes Peer and Memoer to attain memogram over uxd transport.


    Inherited Class Attributes:
        (Peer)
        BufSize (int): used to set default buffer size for transport datagram buffers
        MaxGramSize (int): max gram bytes for this transport

        (Memoer)
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
        (Peer)
        name (str): unique identifier of peer for managment purposes
        ha (tuple): host address of form (host,port) of type (str, int) of this
                peer's socket address.

        bc (int | None): count of transport buffers of MaxGramSize
        bs (int): buffer size
        wl (WireLog): instance ref for debug logging of over the wire tx and rx

        ls (socket.socket): local socket of this Peer
        opened (bool): True local socket is created and opened. False otherwise

        bcast (bool): True enables sending to broadcast addresses from local socket
                      False otherwise

        (Memoer)
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
                oid is verification id when gram is to be signed or None otherwise
        txgs (deque): grams to transmit, each entry is duple of form:
                (gram: bytes, dst: str).
        txbs (tuple): current transmisstion duple of form:
            (gram: bytearray, dst: str). gram bytearray may hold untransmitted
            portion when Encodesdatagram is not able to be sent all at once so can
            keep trying. Nothing to send indicated by (bytearray(), None)
            for (gram, dst)
        echos (deque): holding echo receive duples for testing. Each duple of
                       form: (gram: bytes, dst: str).


    Inherited Properties:
        (Peer)
        host (str): element of .ha duple
        port (int): element of .ha duple
        path (tuple): .ha (host, port)  alias to match .uxd

        (Memoer)
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

    def __init__(self, *, bc=1024, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            bc (int | None): count of transport buffers of MaxGramSize

            See memoing.Memoer for other inherited paramters
            See Peer for other inherited paramters


        Parameters:

        """
        super(PeerMemoer, self).__init__(bc=bc, **kwa)



@contextmanager
def openPM(cls=None, name="test", temp=True, reopen=True, **kwa):
    """
    Wrapper to create and open UXD PeerMemoer instances
    When used in with statement block, calls .close() on exit of with block

    Parameters:
        cls (Class): instance of subclass instance
        name (str): unique identifer of PeerMemoer peer.
                    Enables management of transport by name.
                    Provides unique path part so can have many peers each at
                    different paths but in same directory.
        temp (bool): True means open in temporary directory, clear on close
                     Otherwise open in persistent directory, do not clear on close
        reopen (bool): True (re)open with this init (default)
                       False not (re)open with this init but later

    See udping.Peer for other keyword parameter passthroughs

    Usage:
        with openPM() as peer:
            peer.receive()

        with openPM(cls=PeerMemoerSubclass) as peer:
            peer.receive()

    """
    peer = None
    if cls is None:
        cls = PeerMemoer
    try:
        peer = cls(name=name, temp=temp, reopen=reopen, **kwa)

        yield peer

    finally:
        if peer:
            peer.close()


class PeerMemoerDoer(doing.Doer):
    """PeerMemoerDoer Doer for unreliable UDP transport.
    Does not require retry tymers.

    See Doer for inherited attributes, properties, and methods.
    To test in WingIde must configure Debug I/O to use external console

    Attributes:
       .peer (PeerMemoerDoer): underlying transport instance subclass of Memoer

    """

    def __init__(self, peer, **kwa):
        """Initialize instance.

        Parameters:
           peer (Peer): is Memoer Subclass instance
        """
        super(PeerMemoerDoer, self).__init__(**kwa)
        self.peer = peer


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
        self.peer.reopen(temp=temp)


    def recur(self, tyme):
        """"""
        self.peer.service()


    def exit(self):
        """"""
        self.peer.close()


class SafePeerMemoerDoer(doing.Doer):
    """PeerMemoerDoer Doer for unreliable UDP transport.
    Does not require retry tymers.

    See Doer for inherited attributes, properties, and methods.
    To test in WingIde must configure Debug I/O to use external console

    Attributes:
       .peer (PeerMemoerDoer): underlying transport instance subclass of Memoer

    """

    def __init__(self, peer, **kwa):
        """Initialize instance.

        Parameters:
           peer (Peer): is Memoer Subclass instance
        """
        super(SafePeerMemoerDoer, self).__init__(**kwa)
        self.peer = peer


    def wind(self, tymth):
        """Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(SafePeerMemoerDoer, self).wind(tymth)
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
        if self.tymth:  # Doist or DoDoer already winds its doers on enter
            self.peer.wind(self.tymth)
        # inject temp into file resources here if any
        self.peer.reopen(temp=temp)


    def recur(self, tyme):
        """"""
        self.peer.service()


    def exit(self):
        """"""
        self.peer.close()
