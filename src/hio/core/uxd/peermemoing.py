# -*- encoding: utf-8 -*-
"""
hio.core.uxd.peermemoing Module
"""
from contextlib import contextmanager

from ... import help
from ... import hioing
from ...base import doing
from ..uxd import Peer
from ..memo import Memoer, GramDex

logger = help.ogler.getLogger()


class PeerMemoer(Peer, Memoer):
    """Class for sending memograms over UXD transport
    Mixin base classes Peer and Memoer to attain memogram over uxd transport.


    Inherited Class Attributes:
        MaxGramSize (int): absolute max gram size on tx with overhead
        See memoing.Memoer Class
        See Peer Class

    Inherited Attributes:
        See memoing.Memoer Class
        See Peer Class

    Class Attributes:


    Attributes:


    """


    def __init__(self, *, bc=4, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            bc (int | None): count of transport buffers of MaxGramSize

            See memoing.Memoer for other inherited paramters
            See Peer for other inherited paramters


        Parameters:

        """
        super(PeerMemoer, self).__init__(bc=bc, **kwa)



@contextmanager
def openPM(cls=None, name="test", temp=True, reopen=True, clear=True,
             filed=False, extensioned=True, **kwa):
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
        reopen (bool): True (re)open with this init
                       False not (re)open with this init but later (default)
        clear (bool): True means remove directory upon close when reopening
                      False means do not remove directory upon close when reopening
        filed (bool): True means .path is file path not directory path
                      False means .path is directiory path not file path
        extensioned (bool): When not filed:
                            True means ensure .path ends with fext
                            False means do not ensure .path ends with fext

    See filing.Filer and uxding.Peer for other keyword parameter passthroughs

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
        peer = cls(name=name, temp=temp, reopen=reopen, clear=clear,
                   filed=filed, extensioned=extensioned, **kwa)

        yield peer

    finally:
        if peer:
            peer.close(clear=peer.temp or clear)



class PeerMemoerDoer(doing.Doer):
    """PeerMemoerDoer Doer for reliable UXD transport.
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
        self.peer.close(clear=True)

