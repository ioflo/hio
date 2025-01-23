# -*- encoding: utf-8 -*-
"""
hio.core.uxding Module
"""
import sys
import platform
import os
import errno
import socket
import shutil
from contextlib import contextmanager


from ... import help
from ...base import doing

logger = help.ogler.getLogger()


@contextmanager
def openPeer(cls=None, **kwa):
    """
    Wrapper to create and open UXD Peer instances
    When used in with statement block, calls .close() on exit of with block

    Parameters:
        cls is Class instance of subclass instance

    Usage:
        with openPeer() as peer0:
            peer0.receive()

        with openPeer(cls=PeerBig) as peer0:
            peer0.receive()

    """
    if cls is None:
        cls = Peer
    try:
        peer = cls(**kwa)
        peer.reopen()

        yield peer

    finally:
        peer.close()


class Peer(object):
    """Class to manage non blocking io on UXD (unix domain) socket.
    Use instance method .close() to close socket

    Because Unix Domain Sockets are reliable no need for retry tymer.
    """
    Umask = 0o022  # default

    def __init__(self, ha=None, umask=None, bufsize = 1024, wl=None):
        """
        Initialization method for instance.

        ha = uxd file name
        umask = umask for uxd file
        bufsize = buffer size
        wl = WireLog instance ref for debug logging or over the wire tx and rx
        """
        self.ha = ha  # uxd file path
        self.umask = umask  # only change umask if umask is not None below
        self.bs = bufsize
        self.wl = wl

        self.ss = None  # server's socket needs to be opened
        self.opened = False

    def actualBufSizes(self):
        """Returns duple of the the actual socket send and receive buffer size
        (send, receive)
        """
        if not self.ss:
            return (0, 0)

        return (self.ss.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF),
                self.ss.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF))

    def open(self):
        """Opens socket in non blocking mode.

        if socket not closed properly, binding socket gets error
            OSError: (48, 'Address already in use')
        """
        #create socket ss = server socket
        self.ss = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

        # make socket address reusable.
        # the SO_REUSEADDR flag tells the kernel to reuse a local socket in
        # TIME_WAIT state, without waiting for its natural timeout to expire.
        self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # setup buffers
        if self.ss.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF) <  self.bs:
            self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self.bs)
        if self.ss.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF) < self.bs:
            self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.bs)
        self.ss.setblocking(0) #non blocking socket

        # setup umask
        oldumask = None
        if self.umask is not None: # change umask for the uxd file
            oldumask = os.umask(self.umask) # set new and return old

        #bind to Host Address Port
        try:
            self.ss.bind(self.ha)
        except OSError as ex:
            if not ex.errno == errno.ENOENT: # No such file or directory
                logger.error("Error opening UxD %s\n %s\n", self.ha, ex)
                return False
            try:
                os.makedirs(os.path.dirname(self.ha))
            except OSError as ex:
                logger.error("Error making UXD %s\n %s\n", self.ha, ex)
                return False
            try:
                self.ss.bind(self.ha)
            except OSError as ex:
                logger.error("Error binding UXD %s\n %s\n", self.ha, ex)
                return False

        if oldumask is not None: # restore old umask
            os.umask(oldumask)

        self.ha = self.ss.getsockname()  # get resolved ha after bind
        self.opened = True
        return True

    def reopen(self):
        """Idempotently open socket by closing first if need be
        """
        self.close()
        return self.open()


    def close(self):
        """Closes  socket and unlinks UXD file.
        """
        if self.ss:
            self.ss.close() #close socket
            self.ss = None
            self.opened = False

        try:
            os.unlink(self.ha)
        except OSError:
            if os.path.exists(self.ha):
                raise


    def receive(self):
        """Perform non blocking receive on  socket.

        Returns:
            tuple of form (data, sa) where sa is source address tuple
            (sourcehost, sourceport)
            If no data then returns ('',None)
            but always returns a tuple with two elements
        """
        try:
            #sa = source address tuple (sourcehost, sourceport)
            data, sa = self.ss.recvfrom(self.bs)
        except socket.error as ex:
            # ex.args[0] is always ex.errno for better compat
            # the value of a given errno.XXXXX may be different on each os
            # EAGAIN: BSD 35, Linux 11, Windows 11
            # EWOULDBLOCK: BSD 35 Linux 11 Windows 140
            if ex.args[0]  in (errno.EAGAIN, errno.EWOULDBLOCK):
                return (b'', None) #receive has nothing empty string for data
            else:
                logger.error("Error receive on UXD %s\n %s\n", self.ha, ex)
                raise #re raise exception ex

        if self.wl:
            self.wl.writeRx(data, who=sa)

        return (data, sa)

    def send(self, data, da):
        """Perform non blocking send on  socket.

           data is string in python2 and bytes in python3
           da is destination address tuple (destHost, destPort)
        """
        try:
            result = self.ss.sendto(data, da) #result is number of bytes sent
        except OSError as ex:
            logger.error("Error send UXD from %s to %s.\n %s\n", self.ha, da, ex)
            result = 0
            raise

        if self.wl:# log over the wire send
            self.wl.writeTx(data[:result], who=da)

        return result

    def service(self):
        """
        Service sends and receives
        """



class PeerDoer(doing.Doer):
    """
    Basic UXD Peer Doer
    Because Unix Domain Sockets are reliable no need for retry tymer.

    To test in WingIde must configure Debug I/O to use external console
    See Doer for inherited attributes, properties, and methods.

    See Doer for inherited attributes, properties, and methods.

    Attributes:
       .peer is UXD Peer instance

    """

    def __init__(self, peer, **kwa):
        """
        Initialize instance.

        Parameters:
           peer is UXD Peer instance
        """
        super(PeerDoer, self).__init__(**kwa)
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
