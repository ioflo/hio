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
        MaxGramSize (int): max gram bytes for this transport
        Version (Versionage): default version namedtuple of form (major: int, minor: int)
        Codex (GramDex): dataclass ref to gram codex
        Codes (dict): maps codex names to codex values
        Names (dict): maps codex values to codex names
        Sodex (SGDex): dataclass ref to signed gram codex
        Sizes (dict): gram head part sizes Sizage instances keyed by gram codes
        MaxMemoSize (int): absolute max memo size
        MaxGramCount (int): absolute max gram count
        BufSize (int): used to set default buffer size for transport datagram buffers
        Tymeout (float): default timeout for retry tymer(s) if any

    Inherited Attributes:
        name (str): unique identifier of peer for management purposes
        ha (tuple): host address of form (host,port) of type (str, int) of this peer's socket address.

        bc (int or None): count of transport buffers of MaxGramSize
        bs (int): buffer size
        wl (WireLog): instance ref for debug logging of over the wire tx and rx

        ls (socket.socket): local socket of this Peer
        opened (bool): True local socket is created and opened. False otherwise

        bcast (bool): True enables sending to broadcast addresses from local socket; False otherwise

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
        vids (dict[mid: (vid | None)]): keyed by mid that holds the verifier ID str for
            the memo indexed by its mid (memoID). This enables reattaching
            the vid to memo when placing fused memo in rxms deque.
            Vid is only present when signed header otherwise vid is None
        rxms (deque): holding rx (receive) memo tuples desegmented from rxgs grams
            each entry in deque is tuple of form:
            (memo: str, src: str, vid: str) where:
            memo is fused memo, src is source addr, vid is verifier ID
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
        inbox (deque): holds final received complete memos for testing when not
                       overridden in subclass to further process otherwise
        tymeout (float): default timeout for retry tymer(s) if any
        tymers (dict): keys are tid and values are Tymers for retry tymers for
                       each inflight tx


    Inherited Properties:
        tyme (float or None):  relative cycle time of associated Tymist which is
            provided by calling .tymth function wrapper closure which is obtained
            from Tymist.tymen().
            None means not assigned yet.
        tymth (Callable or None): function wrapper closure returned by
            Tymist.tymen() method. When .tymth is called it returns associated
            Tymist.tyme. Provides injected dependency on Tymist cycle tyme base.
            None means not assigned yet.

        host (str): element of .ha duple
        port (int): element of .ha duple
        path (tuple): .ha (host, port)  alias to match .uxd

        code (bytes | None): gram code for gram header when rending for tx
        curt (bool): True means when rending for tx encode header in base2; False means when rending for tx encode header in base64
        size (int): gram size when rending for tx.
        authic (bool): True means any rx grams must be signed; False otherwise
        echoic (bool): True means use .echos in .send and .receive to mock transport.
        keep (dict): labels are vids and values are Keyage instances.
        vid (str|None): own vid defaults used to lookup keys to sign on tx

        Notes::
        - size: first gram size = over head size + neck size + body size;
            subsequent grams use over head size + body size; gram body size is at
            least one and is limited by MaxGramSize and MaxGramCount relative to
            MaxMemoSize.
        - echoic: each entry in .echos is (gram: bytes, src: str); default echo
            is (b'', None); when False it may be overridden by method parameter.
        - keep: Keyage is namedtuple("Keyage", "sigkey verkey") with private
            signing key sigkey and public verifying key verkey.

    """

    def __init__(self, *, bc=1024, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            bc (int | None): count of transport buffers of MaxGramSize

        See Also:
            memoing.Memoer: other inherited parameters.
            Peer: other inherited parameters.


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
        name (str): unique identifier of PeerMemoer peer.
                    Enables management of transport by name.
                    Provides unique path part so can have many peers each at
                    different paths but in same directory.
        temp (bool): True means open in temporary directory, clear on close
                     Otherwise open in persistent directory, do not clear on close
        reopen (bool): True (re)open with this init (default)
                       False not (re)open with this init but later

    See udping.Peer for other keyword parameter passthroughs

    See Also:
        udping.Peer: other keyword parameter passthroughs.

    Usage::

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
