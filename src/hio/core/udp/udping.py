# -*- encoding: utf-8 -*-
"""
hio.core.udping Module
"""
import sys
import platform
import os
import errno
import socket
from contextlib import contextmanager

from ... import help
from ...base import tyming, doing
from .. import coring

logger = help.ogler.getLogger()


UDP_MAX_DATAGRAM_SIZE = (2 ** 16) - 1  # 65535
UDP_MAX_SAFE_PAYLOAD = 548  # IPV4 MTU 576 - udp headers 28
# IPV6 MTU is 1280 but headers are bigger
UDP_MAX_PACKET_SIZE = min(1024, UDP_MAX_DATAGRAM_SIZE)  # assumes IPV6 capable equipment



@contextmanager
def openPeer(cls=None, **kwa):
    """
    Wrapper to create and open UDP Peer instances
    When used in with statement block, calls .close() on exit of with block

    Parameters:
        cls (Class): instance of subclass instance

    Usage:
        with openPeer() as peer0:
            peer0.receive()

        with openPeer(cls=PeerBig) as peer0:
            peer0.receive()

    """
    peer = None

    if cls is None:
        cls = Peer
    try:
        peer = cls(**kwa)
        peer.reopen()

        yield peer

    finally:
        if peer:
            peer.close()



class Peer(tyming.Tymee):
    """Class to manage non blocking I/O on UDP socket.
    SubClass of Tymee to enable support for retry tymers as UDP is unreliable.

    Class Attributes:
        Tymeout (float): default timeout for retry tymer(s) if any

    Inherited Properties:
         .tyme is float relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        .tymth is function wrapper closure returned by Tymist .tymeth() method.
            When .tymth is called it returns associated Tymist .tyme.
            .tymth provides injected dependency on Tymist tyme base.

    Attributes:
        tymeout (float): timeout for retry tymer(s) if any

        ha (tuple): host address of form (host,port) of type (str, int) of this
                peer's socket address.
        bs (int): buffer size
        wl (WireLog): instance ref for debug logging of over the wire tx and rx
        bcast (bool): True enables sending to broadcast addresses from local socket
                      False otherwise
        ls (socket.socket): local socket of this Peer
        opened (bool): True local socket is created and opened. False otherwise

    Properties:
        host (str): element of .ha duple
        port (int): element of .ha duple


    """
    Tymeout = 0.0  # tymeout in seconds, tymeout of 0.0 means ignore tymeout

    def __init__(self, *,
                 tymeout=None,
                 ha=None,
                 host='',
                 port=55000,
                 bufsize=1024,
                 wl=None,
                 bcast=False,
                 **kwa):
        """
        Initialization method for instance.
        tymeout (float): default for retry tymer if any
        ha (tuple): local socket (host, port) address duple of type (str, int)
        host (str): address where '' means any interface on host
        port (int): socket port
        bs (int):  buffer size
        wl (WireLog): instance to log over the wire tx and rx
        bcast (bool): True enables sending to broadcast addresses from local socket
                      False otherwise
        """
        super(Peer, self).__init__(**kwa)
        self.tymeout = tymeout if tymeout is not None else self.Tymeout
        #self.tymer = tyming.Tymer(tymth=self.tymth, duration=self.tymeout) # retry tymer

        self.ha = ha or (host, port)  # ha = host address duple (host, port)
        host, port = self.ha
        host = coring.normalizeHost(host)  # ip host address
        self.ha = (host, port)

        self.bs = bufsize
        self.wl = wl
        self.bcast = bcast

        self.ls = None  # local socket for this Peer
        self.opened = False

    @property
    def host(self):
        """
        Property that returns host in .ha duple
        """
        return self.ha[0]


    @host.setter
    def host(self, value):
        """
        setter for host property
        """
        self.ha = (value, self.port)


    @property
    def port(self):
        """
        Property that returns port in .ha duple
        """
        return self.ha[1]


    @port.setter
    def port(self, value):
        """
        setter for port property
        """
        self.ha = (self.host, value)



    def wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(Peer, self).wind(tymth)
        #self.tymer.wind(tymth)


    def actualBufSizes(self):
        """Returns duple of the the actual socket send and receive buffer size
        (send, receive)
        """
        if not self.ls:
            return (0, 0)

        return (self.ls.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF),
                self.ls.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF))

    def open(self):
        """Opens socket in non blocking mode.

        if socket not closed properly, binding socket gets error
           OSError: (48, 'Address already in use')
        """
        #create socket ss = server socket
        self.ls = socket.socket(socket.AF_INET,
                                socket.SOCK_DGRAM,
                                socket.IPPROTO_UDP)

        if self.bcast:  # needed to send broadcast, not needed to receive
            self.ls.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # make socket address and port reusable. doesn't seem to have an effect.
        # the SO_REUSEADDR flag tells the kernel to reuse a local socket in
        # TIME_WAIT state, without waiting for its natural timeout to expire.
        # Also use SO_REUSEPORT on linux and darwin
        # https://stackoverflow.com/questions/14388706/how-do-so-reuseaddr-and-so-reuseport-differ

        self.ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if platform.system() != 'Windows':
            self.ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        # setup buffers
        if self.ls.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF) <  self.bs:
            self.ls.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self.bs)
        if self.ls.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF) < self.bs:
            self.ls.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.bs)
        self.ls.setblocking(0)  # non blocking socket

        #bind to Host Address Port
        try:
            self.ls.bind(self.ha)
        except OSError as ex:
            logger.error("Error opening UDP %s\n %s\n", self.ha, ex)
            return False

        self.ha = self.ls.getsockname()  # get resolved ha after bind
        self.opened = True
        return True

    def reopen(self):
        """Idempotently open socket
        """
        self.close()
        return self.open()

    def close(self):
        """Closes  socket.
        """
        if self.ls:
            self.ls.close() #close socket
            self.ls = None
            self.opened = False

    def receive(self):
        """Perform non blocking read on  socket.

        Returns:
            tuple of form (data, sa)
            if no data then returns (b'',None)
            but always returns a tuple with two elements
        """
        try:
            data, sa = self.ls.recvfrom(self.bs)  # sa is source (host, port)
        except OSError as ex:
            # ex.args[0] == ex.errno for better compat
            # the value of a given errno.XXXXX may be different on each os
            # EAGAIN: BSD 35, Linux 11, Windows 11
            # EWOULDBLOCK: BSD 35 Linux 11 Windows 140
            if ex.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK):
                return (b'', None) #receive has nothing empty string for data
            else:
                logger.error("Error receive on UDP %s\n %s\n", self.ha, ex)
                raise #re raise exception ex

        if self.wl:  # log over the wire receive
            self.wl.writeRx(data, who=sa)

        return (data, sa)

    def send(self, data, da):
        """Perform non blocking send on  socket.

        data is string in python2 and bytes in python3
        da is destination address tuple (destHost, destPort)
        """
        try:
            result = self.ls.sendto(data, da) #result is number of bytes sent
        except OSError as ex:
            logger.error("Error send UDP from %s to %s.\n %s\n", self.ha, da, ex)
            result = 0
            raise

        if self.wl:  # log over the wire send
            self.wl.writeTx(data[:result], who=da)

        return result


    def service(self):
        """
        Service sends and receives
        """


class PeerDoer(doing.Doer):
    """
    Basic UDP Peer Doer

    See Doer for inherited attributes, properties, and methods.

    Attributes:
       .peer is UDP Peer instance

    """

    def __init__(self, peer, **kwa):
        """
        Initialize instance.

        Parameters:
           peer (Peer):  UDP instance
        """
        super(PeerDoer, self).__init__(**kwa)
        self.peer = peer
        if self.tymth:
            self.peer.wind(self.tymth)


    def wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(PeerDoer, self).wind(tymth)
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
