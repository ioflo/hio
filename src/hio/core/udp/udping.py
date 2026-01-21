# -*- encoding: utf-8 -*-
"""
hio.core.udp.udping Module
"""
import sys
import platform
import os
import errno
import socket
from contextlib import contextmanager

from ... import hioing
from .. import coring
from ...base import tyming, doing
from ... import help

logger = help.ogler.getLogger()



UDP_IPV4_MAX_SAFE_PAYLOAD = 548  # IPV4 MTU 576 - 28 headers
UDP_IPv6_MAX_SAFE_PAYLOAD =  1240  # IPV6 MTU 1280 - 40 headers
UDP_MAX_DATAGRAM_SIZE = (2 ** 16) - 1  # 65535
UDP_MAX_PACKET_SIZE = min(1024, UDP_MAX_DATAGRAM_SIZE)  # assumes IPV6 capable equipment

# the only way to fragment ipv6 packet is for source to do it. Never done by
# routers en-route.  IPV6 has many extension headers that are only used if set
# up at the source. The fragment header is an 8 byte extension header.
# https://www.geeksforgeeks.org/computer-networks/ipv6-fragmentation-header/

class Peer(hioing.Mixin):
    """Class to manage non blocking I/O on UDP socket.

    Class Attributes:
        BufSize (int): used to set default buffer size for transport datagram buffers
        MaxGramSize (int): max bytes in in datagram for this transport


    Attributes:
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

    Properties:
        host (str): element of .ha duple
        port (int): element of .ha duple
        path (tuple): .ha (host, port)  alias to match .uxd


    """
    BufSize = 65535  # 2 ** 16 - 1  default buffersize
    MaxGramSize = UDP_IPv6_MAX_SAFE_PAYLOAD  # 1240

    def __init__(self, *,
                 name='main',
                 ha=None,
                 host='127.0.0.1',
                 port=55000,
                 bc=None,
                 bs=None,
                 wl=None,
                 bcast=False,
                 reopen=False,
                 **kwa):
        """
        Initialization method for instance.
        Parameters:
            name (str): unique identifier of peer for managment purposes
            ha (tuple): local socket (host, port) address duple of type (str, int)
            host (str): address where '' means any interface on host
            port (int): socket port
            bc (int | None): count of transport buffers of MaxGramSize
            bs (int | None): buffer size of transport buffers. When .bc is provided
                then .bs is calculated by multiplying, .bs = .bc * .MaxGramSize.
                When .bc is not provided, then if .bs is provided use provided
                value else use default .BufSize
            wl (WireLog): instance ref for debug logging of over the wire tx and rx
            bcast (bool): True enables sending to broadcast addresses from local socket
                          False otherwise
            reopen (bool): True (re)open with this init
                           False not (re)open with this init but later (default)
        """

        self.name = name
        self.ha = ha or (host, port)  # ha = host address duple (host, port)
        host, port = self.ha
        host = coring.normalizeHost(host)  # ip host address
        self.ha = (host, port)

        self.bc = int(bc) if bc is not None and bc > 0 else None
        if self.bc:
            self.bs = self.MaxGramSize * self.bc
        else:
            self.bs = bs if bs is not None else self.BufSize

        self.wl = wl
        self.bcast = bcast

        self.ls = None  # local socket for this Peer needs to be opened/bound
        self.opened = False

        super(Peer, self).__init__(**kwa)
        if reopen:
            self.reopen()

    @property
    def path(self):
        """
        Property that returns .ha duple
        stub to match uxd interface
        """
        return self.ha

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

    def reopen(self, **kwa):
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

        return not self.opened  # True means closed successfully

    def receive(self, **kwa):
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
            if (ex.args[0] in (errno.EAGAIN,
                              errno.EWOULDBLOCK)):
                return (b'', None) #receive has nothing empty string for data
            else:
                logger.error("Error receive on UDP %s\n %s\n", self.ha, ex)
                raise #re raise exception ex

        if self.wl:  # log over the wire receive
            self.wl.writeRx(data, who=sa)

        return (data, sa)


    def send(self, data, dst, **kwa):
        """Perform non blocking send on  socket.

        Returns:
            cnt (int): count of bytes actually sent, may be less than len(data).

        Parameters:
            data (bytes | bytearray):  payload to send (txbs)
            dst (str): udp destination addr duple of form (host: str, port: int)
        """
        try:
            cnt = self.ls.sendto(data, dst)  # count == int number of bytes sent
        except OSError as ex:
            # ex.args[0] == ex.errno for better compat
            # the value of a given errno.XXXXX may be different on each os
            # EAGAIN: BSD 35, Linux 11, Windows 11
            # EWOULDBLOCK: BSD 35 Linux 11 Windows 140
            if (ex.args[0] in (errno.EAGAIN,
                               errno.EWOULDBLOCK,
                               errno.ENOBUFS,
                               errno.ENOMEM)):
                # not enough buffer space to send, do not consume data
                return 0  # try again later with same data

            else:
                logger.error("Error send UDP from %s to %s.\n %s\n", self.ha, dst, ex)
                cnt = 0
            raise

        if self.wl:  # log over the wire actually sent data portion
            self.wl.writeTx(data[:cnt], who=dst)

        return cnt




@contextmanager
def openPeer(cls=None, name="test", **kwa):
    """
    Wrapper to create and open UDP Peer instances
    When used in with statement block, calls .close() on exit of with block

    Parameters:
        cls (Class): instance of subclass instance
        name (str): unique identifer of peer. Enables management of Peer sockets
                    by name.
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
        peer = cls(name=name, **kwa)
        peer.reopen()

        yield peer

    finally:
        if peer:
            peer.close()



class PeerDoer(doing.Doer):
    """Basic UDP Peer Doer
    Stub Override in Subclass
    To test in WingIde must configure Debug I/O to use external console
    See Doer for inherited attributes, properties, and methods.

    See Doer for inherited attributes, properties, and methods.

    Attributes:
       .peer is UDP Peer instance

    """

    def __init__(self, peer, **kwa):
        """
        Initialize instance.

        Parameters:
           peer is UXD Peer instance
        """
        super(PeerDoer, self).__init__(**kwa)
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
        pass  # Override in subclass to service receives and sends




    def exit(self):
        """"""
        self.peer.close()

