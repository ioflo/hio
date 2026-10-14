# -*- encoding: utf-8 -*-
"""
hio.core.tcp.serving Module

Accepter listens and accepts incoming TCP socket connections
Server is subclass of Acceptor
Server creates Remoters
Remoter is accepted incoming socket connection

ServerTls is subclass of Server
RemoterTls is subclass of Remoter

"""

import sys
import os
import errno
import socket
import ssl
from collections import deque
from contextlib import contextmanager

from ... import help
from ...base import tyming, doing
from .. import coring

logger = help.ogler.getLogger()


@contextmanager
def openServer(cls=None, **kwa):
    """
    Wrapper to create and open TCP Server instances
    When used in with statement block, calls .close() on exit of with block

    Parameters:
        cls is Class instance of subclass instance

    Usage::

        with openServer() as server0:
            server0.

        with openServer(cls=ServerTls) as server0:
            server0.

    """
    server = None
    cls = cls if cls is not None else Server

    try:
        server = cls(**kwa)
        server.reopen()  #  opens accept socket

        yield server

    finally:
        if server:
            server.close()


class Acceptor(tyming.Tymee):
    """
    Acceptor Base Class for Server.
    Nonblocking TCP Socket Acceptor Class.
    Listen socket for incoming TCP connections

    See tyming.Tymee for inherited attributes, properties, and methods

    Attributes:
        .ha is (host,port) duple (two tuple)
               host = "" or "0.0.0.0" means listen on all interfaces
        .eha is normalized (host, port) duple for incoming TLS connections
                as external facing address for TLS context
        .bs is buffer size
        .ss is server listen socket for incoming accept requests
        .axes is deque of accepte connection duples (ca, cs)
        .opened is boolean, True if listen socket .ss opened. False otherwise
    """

    def __init__(self, ha=None, bs=8096, bl=128, **kwa):
        """
        Initialization method for instance.
        ha is host address duple (host, port) listen interfaces. host = "" or
        "0.0.0.0" means listen on all interfaces. bs is buffer size. bl is
        backlog size of not yet accepted concurrent tcp connections.
        """
        super(Acceptor, self).__init__(**kwa)
        self.ha = ha or (host, port)  # ha = host address
        eha = self.ha
        host, port = eha  # expand so can normalize host
        host = coring.normalizeHost(host)
        if host in ('0.0.0.0',):
            host = '127.0.0.1'  # need specific interface for tls
        elif host in ("::", "0:0:0:0:0:0:0:0"):
            host = "::1" # need specific interface for tls
        self.eha = (host, port)
        self.bs = bs
        self.bl = bl
        self.ss = None  # listen socket for accepts
        self.axes = deque()  # deque of duple (ca, cs) accepted connections
        self.opened = False

    def actualBufSizes(self):
        """
        Returns duple of the the actual socket send and receive buffer size
        (send, receive)
        """
        if not self.ss:
            return (0, 0)

        return (self.ss.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF),
                self.ss.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF))

    def open(self):
        """
        Opens binds listen socket in non blocking mode.

        if socket not closed properly, binding socket gets error
           OSError: (48, 'Address already in use')
        """
        #create server socket ss to listen on
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # make socket address reusable.
        # the SO_REUSEADDR flag tells the kernel to reuse a local socket in
        # TIME_WAIT state, without waiting for its natural timeout to expire.
        self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Linux TCP allocates twice the requested size
        if sys.platform.startswith('linux'):
            bs = 2 * self.bs  # get size is twice the set size
        else:
            bs = self.bs

        if self.ss.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF) < bs:
            self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self.bs)
        if self.ss.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF) < bs:
            self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.bs)

        self.ss.setblocking(0)  # non blocking socket

        try:  # bind to listen socket (host, port) to receive connections
            self.ss.bind(self.ha)
            self.ss.listen(self.bl)  # this determines number of concurrent connections
        except OSError as ex:
            self.close()
            logger.error("Error binding server listen socket.\n%s\n", ex)
            return False

        self.ha = self.ss.getsockname()  # get resolved ha after bind
        self.opened = True
        return True

    def reopen(self, **kwa):
        """
        Idempotently opens listen socket
        """
        self.close()
        return self.open()

    def close(self):
        """
        Closes listen socket.
        """
        if self.ss:
            try:
                self.ss.shutdown(socket.SHUT_RDWR)  # shutdown socket
            except OSError as ex:
                pass
            self.ss.close()  #close socket
            self.ss = None
            self.opened = False

    def accept(self):
        """
        Accept new connection nonblocking
        Returns duple (cs, ca) of connected socket and connected host address
        Otherwise if no new connection returns (None, None)
        """
        # accept new virtual connected socket created from server socket
        try:
            cs, ca = self.ss.accept()  # virtual connection (socket, host address)
        except OSError as ex:
            if ex.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                return (None, None)  # nothing yet
            raise  # re-raise

        return (cs, ca)

    def serviceAccepts(self):
        """
        Service any accept requests
        Adds to .cxes dict key by ca
        """
        while True:
            cs, ca = self.accept()
            if not cs:
                break
            self.axes.append((cs, ca))


class Server(Acceptor):
    """
    Nonblocking TCP Socket Server Class.
    Listen socket for incoming TCP connections that generates Remoter sockets
    for accepted connections

    See tyming.Tymee for inherited attributes, properties, and methods

    Inherited Attributes:
        ha (tuple[str, int]): (host, port) duple; host = "" or "0.0.0.0" means listen on all interfaces
        eha (tuple[str, int]): normalized external-facing (host, port) for TLS context
        bs (int): buffer size
        ss (socket.socket | None): server listen socket for incoming accept requests
        axes (deque): accepted connection duples (ca, cs)
        opened (bool): True if listen socket ss is open; False otherwise

    Attributes:
        tymeout (float): idle tymeout in seconds passed to each accepted
            Remoter. A connection with no bytes received or sent for tymeout
            has an expired .tymer; the owner of the server decides whether to
            drop it. 0.0 means never time out.
        wl (WireLog | None): WireLog instance if any
        ixes (dict): incoming connections indexed by remote (host, port) duple
    """

    # 0.0 means accepted connections never time out. This was 1.0, but the
    # value never reached Remoter (it was passed as timeout=), so 0.0 is the
    # behavior every caller has actually had; pass tymeout to opt in.
    Tymeout = 0.0  # tymeout in seconds virtual tyme

    def __init__(self,
                 ha=None,
                 host="",
                 port=56000,
                 tymeout=None,
                 wl=None,
                 **kwa):
        """
        Initialization method for instance.
        Parameters:
            ha is TCP/IP (host, port) duple for listen socket
            host is default TCP/IP host address for listen socket
                "" or "0.0.0.0" is listen on all interfaces
            port is default TCP/IP port
            tymeout is default tymeout for to pass to remoters for incoming connections
            wl is WireLog instance if any
        """
        ha = ha or (host, port)
        super(Server, self).__init__(ha=ha, **kwa)
        self.tymeout = tymeout if tymeout is not None else self.Tymeout
        self.wl = wl
        self.ixes = dict()  # ready to rx tx incoming connections, Remoter instances


    def wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(Server, self).wind(tymth)
        for rm in self.ixes.values():  # remotoer
            rm.wind(tymth)


    def setTymeout(self, tymeout):
        """
        Set .tymeout for connections accepted from now on and apply it to the
        connections already in .ixes. See Remoter.setTymeout.
        """
        self.tymeout = tymeout
        for rm in self.ixes.values():  # remoter
            rm.setTymeout(tymeout)


    def serviceAxes(self):
        """
        Service axes

        For each newly accepted connection in .axes create Remoter
        and add to .ixes keyed by ca
        """
        self.serviceAccepts()  # populate .axes
        while self.axes:
            cs, ca = self.axes.popleft()
            if ca != cs.getpeername() or self.eha[1] != cs.getsockname()[1]: # only port on eha
                raise ValueError("Accepted socket host addresses malformed for "
                                 "peer. ca {0} != {1} or ha port {2} != {3}\n"
                                 "".format(ca, cs.getpeername(), self.eha, cs.getsockname()))
            remoter = Remoter(tymth=self.tymth,
                              ha=cs.getsockname(),
                              ca=ca,
                              cs=cs,
                              bs=self.bs,
                              wl=self.wl,
                              tymeout=self.tymeout)
            if ca in self.ixes and self.ixes[ca] is not remoter:
                self.ixes[ca].close()  # replaced so close old socket
            self.ixes[ca] = remoter


    def serviceConnects(self):
        """
        Service connects is method name to be used
        """
        self.serviceAxes()


    def shutdownIx(self, ca, how=socket.SHUT_RDWR):
        """
        Shutdown remoter given by connection address ca
        """
        if ca not in self.ixes:
            emsg = "Invalid connection address '{0}'".format(ca)
            raise ValueError(emsg)
        self.ixes[ca].shutdown(how=how)


    def shutdownSendIx(self, ca):
        """
        Shutdown send on remoter given by connection address ca
        """
        if ca not in self.ixes:
            emsg = "Invalid connection address '{0}'".format(ca)
            raise ValueError(emsg)
        self.ixes[ca].shutdownSend()


    def shutdownReceiveIx(self, ca):
        """
        Shutdown send on remoter given by connection address ca
        """
        if ca not in self.ixes:
            emsg = "Invalid connection address '{0}'".format(ca)
            raise ValueError(emsg)
        self.ixes[ca].shutdownReceive()


    def closeIx(self, ca):
        """
        Shutdown and close remoter given by connection address ca
        """
        if ca not in self.ixes:
            emsg = "Invalid connection address '{0}'".format(ca)
            raise ValueError(emsg)
        self.ixes[ca].close()


    def closeAllIx(self):
        """
        Shutdown and close all remoter connections
        """
        for rm in self.ixes.values():  # remoter
            rm.close()


    def close(self):
        """
        Close all sockets
        """
        super(Server, self).close()  #  call super close
        self.closeAllIx()


    def removeIx(self, ca, close=True):
        """
        Remove remoter given by connection address ca
        """
        if ca not in self.ixes:
            emsg = "Invalid connection address '{0}'".format(ca)
            raise ValueError(emsg)
        if close:
            self.ixes[ca].close()  # shutdown and close socket
        del self.ixes[ca]


    def serviceReceivesIx(self, ca):
        """
        Service receives for remoter by connection address ca
        """
        if ca not in self.ixes:
            emsg = "Invalid connection address '{0}'".format(ca)
            raise ValueError(emsg)

        try:
            self.ixes[ca].serviceReceives()
        except OSError as ex:
            logger.error("Closing incoming socket on %s.\n%s\n", ix.cs.getpeername(), ex)
            self.removeIx(ca=ca)  # also closes ix


    def serviceReceivesAllIx(self):
        """
        Service receives for all remoters in .ixes
        """
        for ca, ix in list(self.ixes.items()):  # list so can remove while iterating
            try:
                ix.serviceReceives()
            except OSError as ex:
                logger.error("Closing incoming socket on %s.\n%s\n", ix.cs.getpeername(), ex)
                self.removeIx(ca=ca)  # also closes ix




    def transmitIx(self, data, ca):
        '''
        Queue data onto .txbs for remoter given by connection address ca
        '''
        if ca not in self.ixes:
            emsg = "Invalid connection address '{0}'".format(ca)
            raise ValueError(emsg)
        self.ixes[ca].tx(data)


    def serviceSendsAllIx(self):
        """
        Service transmits for all remoters in .ixes
        """
        for rm in self.ixes.values():  # remoter
            rm.serviceSends()


    def service(self):
        """
        Service connects and service receives and sends for all ix.
        """
        self.serviceConnects()
        self.serviceReceivesAllIx()
        self.serviceSendsAllIx()



def initServerContext(context=None,
                      version=None,
                      certify=None,
                      keypath=None,
                      certpath=None,
                      cafilepath=None
                      ):
    """
    Initialize and return context for TLS Server
    IF context is None THEN create a context

    IF version is None THEN create context using ssl library default
    ELSE create context with version

    If certify is not None then use certify value provided Otherwise use default

    context is the tls/ssl context object; if None use default.
    version is ssl protocol version; if None use default.
    certify is cert requirement; if None use default (ssl.CERT_NONE,
    ssl.CERT_OPTIONAL, ssl.CERT_REQUIRED).
    keypath is local server PKI private key file path; if given apply to context.
    certpath is local server PKI public cert file path; if given apply to context.
    cafilepath is cert authority file path to verify client cert; if given apply.
    """
    if context is None:  # create context
        if not version:  # use default context with default protocol version
            context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
            context.verify_flags &= ~ssl.VERIFY_X509_STRICT  # XXXX new with python 3.13
            # XXXX ToDo create new test certificates that are RFC 5280 compliant
            context.verify_mode = certify if certify is not None else ssl.CERT_REQUIRED

        else:  # create context with specified protocol version
            context = ssl.SSLContext(protocol=version)
            # disable bad protocols versions
            context.options |= ssl.OP_NO_SSLv2
            context.options |= ssl.OP_NO_SSLv3
            # disable compression to prevent CRIME attacks (OpenSSL 1.0+)
            context.options |= getattr(ssl._ssl, "OP_NO_COMPRESSION", 0)
            # Prefer the server's ciphers by default fro stronger encryption
            context.options |= getattr(ssl._ssl, "OP_CIPHER_SERVER_PREFERENCE", 0)
            # Use single use keys in order to improve forward secrecy
            context.options |= getattr(ssl._ssl, "OP_SINGLE_DH_USE", 0)
            context.options |= getattr(ssl._ssl, "OP_SINGLE_ECDH_USE", 0)
            # disallow ciphers with known vulnerabilities
            context.set_ciphers(ssl._RESTRICTED_SERVER_CIPHERS)
            context.verify_mode = certify if certify is not None else ssl.CERT_REQUIRED

    if cafilepath:
        context.load_verify_locations(cafile=cafilepath,
                                      capath=None,
                                      cadata=None)
    elif context.verify_mode != ssl.CERT_NONE:
        context.load_default_certs(purpose=ssl.Purpose.CLIENT_AUTH)

    if keypath or certpath:
        context.load_cert_chain(certfile=certpath, keyfile=keypath)

    return context



class ServerTls(Server):
    """
    Server with Nonblocking TLS/SSL support
    Nonblocking TCP Socket Server Class.
    Listen socket for incoming TCP connections
    RemoterTLS sockets for accepted connections

    See tyming.Tymee for inherited attributes, properties, and methods

    Inherited Attributes:
        ha (tuple[str, int]): (host, port) duple; host = "" or "0.0.0.0" means listen on all interfaces
        eha (tuple[str, int]): normalized external-facing (host, port) for TLS context
        bs (int): buffer size
        ss (socket.socket | None): server listen socket for incoming accept requests
        axes (deque): accepted connection duples (ca, cs)
        opened (bool): True if listen socket ss is open; False otherwise
        tymeout (float): tymeout in seconds passed to each accepted
            RemoterTls. A connection that has not completed its TLS handshake
            within tymeout of being accepted is dropped. This is a total
            deadline, not an idle limit: handshake traffic does not restart
            the tymer. Once connected, tymeout is an idle limit as for
            Server. 0.0 means never time out.
        wl (WireLog | None): WireLog instance if any
        ixes (dict): incoming connections indexed by remote (host, port) duple

    Attributes:
        context (ssl.SSLContext | None): TLS context instance
        version (int | None): TLS version
        certify (bool | None): True to require client cert verification
        keypath (str | None): path to key file
        certpath (str | None): path to cert file
        cafilepath (str | None): path to CA file
    """
    def __init__(self,
                 context=None,
                 version=None,
                 certify=None,
                 keypath=None,
                 certpath=None,
                 cafilepath=None,
                 **kwa):
        """
        Initialization method for instance.
        """
        super(ServerTls, self).__init__(**kwa)

        self.cxes = dict()  # accepted incoming connections, RemoterTLS instances

        self.context = context
        self.version = version
        self.certify = certify
        self.keypath = keypath
        self.certpath = certpath
        self.cafilepath = cafilepath

        self.context = initServerContext(context=context,
                                         version=version,
                                         certify=certify,
                                         keypath=keypath,
                                         certpath=certpath,
                                         cafilepath=cafilepath
                                        )


    def wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Also winds connections still in handshake in .cxes so they can expire.
        """
        super(ServerTls, self).wind(tymth)
        for cx in self.cxes.values():  # remoterTls
            cx.wind(tymth)


    def setTymeout(self, tymeout):
        """
        Set .tymeout for connections accepted from now on and apply it to the
        connections already in .ixes and still handshaking in .cxes. A
        handshake deadline still counts from accept, see Remoter.setTymeout.
        """
        super(ServerTls, self).setTymeout(tymeout)
        for cx in self.cxes.values():  # remoterTls
            cx.setTymeout(tymeout)


    def serviceAxes(self):
        """
        Service accepteds

        For each new accepted connection create RemoterTLS and add to .cxes
        Not Handshaked
        """
        self.serviceAccepts()  # populate .axes
        while self.axes:
            cs, ca = self.axes.popleft()
            if ca != cs.getpeername() or self.eha[1] != cs.getsockname()[1]: # only port on eha
                raise ValueError("Accepted socket host addresses malformed for "
                                 "peer. ca {0} != {1} or ha port {2} != {3}\n"
                                 "".format(ca, cs.getpeername(), self.eha, cs.getsockname()))
            remoter = RemoterTls(tymth=self.tymth,
                                 ha=cs.getsockname(),
                                 ca=ca,
                                 bs=self.bs,
                                 cs=cs,
                                 wl=self.wl,
                                 tymeout=self.tymeout,
                                 context=self.context,
                                 version=self.version,
                                 certify=self.certify,
                                 keypath=self.keypath,
                                 certpath=self.certpath,
                                 cafilepath=self.cafilepath,
                                )
            if ca in self.cxes and self.cxes[ca] is not remoter:
                self.cxes[ca].close()  # replaced so close old socket
            self.cxes[ca] = remoter


    def serviceCxes(self):
        """
        Service handshakes for every remoter in .cxes
        If successful move to .ixes
        Drop any whose handshake has not completed within its tymeout
        """
        for ca, cx in list(self.cxes.items()):  # list so can remove during iteration
            cx.handshake()
            if cx.connected:  # handshake completed successfully
                del self.cxes[ca]
                cx.refresh()  # idle tyme on ixes counts from handshake completion
                if ca in self.ixes and self.ixes[ca] is not cx:
                    self.ixes[ca].close()  # replaced so close old socket
                self.ixes[ca] = cx  # add to incoming connections
                continue
            if cx.aborted:  # handshake completed unsuccessfully
                del self.cxes[ca] # remove and let client startover
                continue
            if cx.expired:  # handshake never completed so drop
                logger.debug("Dropping incoming connection from %s: tls "
                            "handshake not completed within %s s.", ca, cx.tymeout)
                cx.close()
                del self.cxes[ca]
                continue



    def serviceConnects(self):
        """
        Service accept and handshake attempts
        For each successful handshake add to .ixes.
        """
        self.serviceAxes()
        self.serviceCxes()


class Remoter(tyming.Tymee):
    """
    Class to service an incoming nonblocking TCP connection from a remote client.
    Should only be used by an Acceptor subclass such as Server
    """
    Tymeout = 0.0  # virtual tymeout in seconds

    def __init__(self,
                 ha,
                 ca,
                 cs,
                 tymeout=None,
                 refreshable=True,
                 bs=8096,
                 wl=None,
                 **kwa
                ):

        """
        Initialization method for instance.
           ha is host address duple (host, port) near side of connection.
           ca is connection address used as key in server ixes.
           cs is connection socket object. tymeout is tymeout for .tymer.
           refreshable True means tx/rx activity refreshes timer.
           bs is buffer size. wl is WireLog object if any.
        """
        super(Remoter, self).__init__(**kwa)
        self.ha = ha  # connection address of server
        self.ca = ca  # connection address of peer used to index in server.ixes
        self.cs = cs  # connection socket
        if self.cs:
            self.cs.setblocking(0)  # linux does not preserve blocking from accept
        self.tymeout = tymeout if tymeout is not None else self.Tymeout
        self.tymer = tyming.Tymer(tymth=self.tymth, duration=self.tymeout)
        # restarted only by send progress, see .sendExpired
        self.sendTymer = tyming.Tymer(tymth=self.tymth, duration=self.tymeout)
        self.cutoff = False # True when detect connection closed on far side
        self.refreshable = refreshable
        self.bs = bs
        self.txbs = bytearray()  # bytearray of data to send
        self.rxbs = bytearray()  # bytearray of data received
        self.wl = wl


    def wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(Remoter, self).wind(tymth)
        self.tymer.wind(tymth)
        self.sendTymer.wind(tymth)


    def shutdown(self, how=socket.SHUT_RDWR):
        """
        Shutdown connected socket .cs
        """
        if self.cs:
            try:
                self.cs.shutdown(how)  # shutdown socket
            except OSError as ex:
                pass


    def shutdownSend(self):
        """
        Shutdown send on connected socket .cs
        """
        if self.cs:
            try:
                self.shutdown(how=socket.SHUT_WR)  # shutdown socket
            except OSError as ex:
                pass


    def shutdownReceive(self):
        """
        Shutdown receive on connected socket .cs
        """
        if self.cs:
            try:
                self.shutdown(how=socket.SHUT_RD)  # shutdown socket
            except OSError as ex:
                pass


    def close(self):
        """
        Shutdown and close connected socket .cs
        """
        if self.cs:
            self.shutdown()
            self.cs.close()  #close socket
            self.cs = None


    @property
    def expired(self):
        """
        Returns True if this connection has been idle for longer than .tymeout.
        Never True when .tymeout is 0.0 or when no tymth has been wound, since
        without a tyme there is no idle tyme to measure.
        """
        return (self.tymeout > 0.0 and self.tymer.tyme is not None
                and self.tymer.expired)


    @property
    def sendExpired(self):
        """
        Returns True if bytes have been waiting in .txbs for longer than
        .tymeout without any send progress. Only received bytes do not count,
        so a peer that keeps sending but has stopped reading still expires.
        Never True when .tymeout is 0.0 or when no tymth has been wound.
        """
        return (self.tymeout > 0.0 and self.sendTymer.tyme is not None
                and self.sendTymer.expired)


    def setTymeout(self, tymeout):
        """
        Replace .tymeout and the duration of .tymer and .sendTymer, keeping
        the tyme each started at. So a deadline counted from accept, such as
        a TLS handshake's, still counts from accept, and setting it again
        cannot extend it.
        """
        self.tymeout = tymeout
        for tymer in (self.tymer, self.sendTymer):
            start = 0.0 if tymer.tyme is None else tymer.tyme - tymer.elapsed
            tymer.start(duration=tymeout, start=start)


    def refresh(self):
        """
        Restart tymer from now, so .tymeout measures idle tyme since the
        latest activity. Not a lossless restart: that would add a whole
        tymeout per refresh and a trickling peer would never expire.
        """
        if self.tymer.tyme is not None:  # no tymth wound means nothing to time
            self.tymer.start()


    def refreshSend(self):
        """
        Restart sendTymer from now, on send progress or when bytes are queued
        onto an empty .txbs.
        """
        if self.sendTymer.tyme is not None:  # no tymth wound means nothing to time
            self.sendTymer.start()


    def receive(self):
        """
        Perform non blocking receive on connected socket .cs

        If no data then returns None
        If connection closed then returns ''
        Otherwise returns data

        data is string in python2 and bytes in python3
        """
        try:
            data = self.cs.recv(self.bs)
        except OSError as ex:
            # ex.args[0] == ex.errno for better os compatibility.
            # the value of a given errno.XXXXX may be different on each os
            if ex.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK):
                return None  # keep trying
            elif ex.args[0] in (errno.ECONNRESET,
                                errno.ENETRESET,
                                errno.ENETUNREACH,
                                errno.EHOSTUNREACH,
                                errno.ENETDOWN,
                                errno.EHOSTDOWN,
                                errno.ETIMEDOUT,
                                errno.ECONNREFUSED):
                self.cutoff = True  # this signals need to close/reopen connection
                return bytes()  # data empty
            else:  # unexpected error
                logger.error("Unexpected error on receive on %s.\n%s\n", self.cs.getpeername(), ex)
                raise  # re-raise

        if data:  # connection open
            if self.wl:  # log over the wire rx
                self.wl.writeRx(data, self.ca)

            if self.refreshable:
                self.refresh()

        else:  # data empty so connection closed on other end
            self.cutoff = True

        return data


    def serviceReceives(self):
        """
        Service receives until no more
        """
        while not self.cutoff:
            data = self.receive()
            if not data:
                break
            self.rxbs.extend(data)


    def serviceReceiveOnce(self):
        '''
        Retrieve from server only one reception
        '''
        if not self.cutoff:
            data = self.receive()
            if data:
                self.rxbs.extend(data)


    def clearRxbs(self):
        """
        Clear .rxbs
        """
        del self.rxbs[:]


    def send(self, data):
        """
        Perform non blocking send on connected socket .cs.
        Return number of bytes sent

        data is string in python2 and bytes in python3
        """
        try:
            count = self.cs.send(data) #result is number of bytes sent
        except OSError as ex:
            # ex.args[0] == ex.errno for better compat
            # the value of a given errno.XXXXX may be different on each os
            if ex.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK):
                count = 0  # blocked try again
            elif ex.args[0] in (errno.ECONNRESET,
                                errno.ENETRESET,
                                errno.ENETUNREACH,
                                errno.EHOSTUNREACH,
                                errno.ENETDOWN,
                                errno.EHOSTDOWN,
                                errno.ETIMEDOUT,
                                errno.ECONNREFUSED):
                self.cutoff = True  # this signals need to close/reopen connection
                count = 0
            else:
                raise

        if count:
            if self.wl:
                self.wl.writeTx(data[:count], self.ca)

            if self.refreshable:
                self.refresh()
                self.refreshSend()

        return count


    def tx(self, data):
        '''
        Queue data onto .txbs
        Queuing onto an empty .txbs restarts .sendTymer, so time spent with
        nothing to send does not count against sending what is queued now.
        '''
        if data and not self.txbs and self.refreshable:
            self.refreshSend()
        self.txbs.extend(data)


    def serviceSends(self):
        """
        Service transmits
        For each tx if all bytes sent then keep sending until partial send
        or no more to send
        If partial send reattach and return
        """
        while self.txbs and not self.cutoff:
            count = self.send(self.txbs)
            del self.txbs[:count]
            break  # try again later


class RemoterTls(Remoter):
    """
    Class to service an incoming nonblocking TCP/TLS connection from a remote client.
    Should only be used from Acceptor subclass
    Provides nonblocking TLS/SSL support

    Attributes:
        connected (bool): True means TLS handshake completed False otherwise
        aborted (bool): True means client aborted TLS handshake False otherwise
    """
    def __init__(self,
                 context=None,
                 version=None,
                 certify=None,
                 keypath=None,
                 certpath=None,
                 cafilepath=None,
                 **kwa):

        """
        Initialization method for instance.
            context is tls/ssl context object; if None use default.
            version is ssl version; if None use default.
            certify is cert requirement; if None use default (ssl.CERT_NONE,
            ssl.CERT_OPTIONAL, ssl.CERT_REQUIRED).
            keypath is local server PKI private key file path; if given apply.
            certpath is local server PKI public cert file path; if given apply.
            cafilepath is cert authority file path to verify client cert; if given apply.
        """
        super(RemoterTls, self).__init__(**kwa)

        self.connected = False  # True once ssl handshake completed
        self.aborted = False # True if client aborts TLS handshake prematurely

        self.context = initServerContext(context=context,
                                    version=version,
                                    certify=certify,
                                    keypath=keypath,
                                    certpath=certpath,
                                    cafilepath=cafilepath
                                  )
        self.wrap()


    def close(self):
        """
        Shutdown and close connected socket .cs
        """
        if self.cs:
            self.shutdown()
            self.cs.close()  #close socket
            self.cs = None
            self.connected = False


    def wrap(self):
        """
        Wrap socket .cs in ssl context
        """
        self.cs = self.context.wrap_socket(self.cs,
                                           server_side=True,
                                           do_handshake_on_connect=False)


    def handshake(self):
        """
        Attempt nonblocking ssl handshake to .ha
        Sets .connected when complete successfully
        Sets .aborted when client terminates prematurely
        Keep trying while not connected and not aborted
        """
        try:
            self.cs.do_handshake()

        except ssl.SSLError as ex:
            if ex.errno in (ssl.SSL_ERROR_WANT_READ, ssl.SSL_ERROR_WANT_WRITE):
                return  # in progress try again later

            elif ex.errno in (ssl.SSL_ERROR_EOF, ):  # give up client terminated
                logger.error("SSLError aborted tls handshake of %s with %s.\n%s\n", self.ha, self.ca, ex)
                self.close()
                self.aborted = True  # indicate client aborted handshake
                return  # caller checks .aborted

            else:
                logger.error("SSLError during tls handshake of %s with %s.\n%s\n", self.ha, self.ca, ex)
                self.close()
                self.aborted = True  # indicate client aborted handshake
                return  # caller checks .aborted

        except OSError as ex:
            logger.error("OSError during tls handshake of %s with %s.\n%s\n", self.ha, self.ca, ex)
            self.close()
            self.aborted = True  # indicate client aborted handshake
            if ex.errno in (errno.ECONNABORTED, ): #  give up client aborted
                logger.error("Client aborted.\n%s\n", ex)
            return   # caller checks .aborted

        except Exception as ex:
            self.close()
            raise  # unexpected Exception so bubble up

        self.connected = True  # handshake completed successfully


    def receive(self):
        """
        Perform non blocking receive on connected socket .cs

        If no data then returns None
        If connection closed then returns ''
        Otherwise returns data

        data is string in python2 and bytes in python3
        """
        try:
            data = self.cs.recv(self.bs)
        except OSError as ex:  # ssl.SSLError is a subtype of OSError
            # ex.args[0] == ex.errno for better compat
            # the value of a given errno.XXXXX may be different on each os
            if  ex.args[0] in (ssl.SSL_ERROR_WANT_READ, ssl.SSL_ERROR_WANT_WRITE):
                return None  # blocked waiting for data
            elif ex.args[0] in (errno.ECONNRESET,
                                errno.ENETRESET,
                                errno.ENETUNREACH,
                                errno.EHOSTUNREACH,
                                errno.ENETDOWN,
                                errno.EHOSTDOWN,
                                errno.ETIMEDOUT,
                                errno.ECONNREFUSED,
                                ssl.SSLEOFError):
                self.cutoff = True  # this signals need to close/reopen connection
                return bytes()  # data empty
            else:
                logger.error("Unexpected error on receive on %s.\n%s\n", self.cs.getpeername(), ex)
                raise  # re-raise

        if data:  # connection open
            if self.wl:  # log over the wire rx
                self.wl.writeRx(data, who=self.cs.getpeername())

            if self.refreshable:
                self.refresh()

        else:  # data empty so connection closed on other end
            self.cutoff = True

        return data


    def send(self, data):
        """
        Perform non blocking send on connected socket .cs.
        Return number of bytes sent

        data is string in python2 and bytes in python3
        """
        try:
            result = self.cs.send(data) #result is number of bytes sent
        except OSError as ex:  # ssl.SSLError is a subtype of OSError
            # ex.args[0] == ex.errno for better compat
            # the value of a given errno.XXXXX may be different on each os
            if ex.args[0] in (ssl.SSL_ERROR_WANT_READ, ssl.SSL_ERROR_WANT_WRITE):
                result = 0  # blocked try again
            elif ex.args[0] in (errno.ECONNRESET,
                                errno.ENETRESET,
                                errno.ENETUNREACH,
                                errno.EHOSTUNREACH,
                                errno.ENETDOWN,
                                errno.EHOSTDOWN,
                                errno.ETIMEDOUT,
                                errno.ECONNREFUSED,
                                ssl.SSLEOFError):
                self.cutoff = True  # this signals need to close/reopen connection
                result = 0
            else:
                raise

        if result:
            if self.wl:
                self.wl.writeTx(data[:result], who=self.cs.getpeername())

            if self.refreshable:
                self.refresh()
                self.refreshSend()

        return result



class ServerDoer(doing.Doer):
    """
    Basic TCP Server Doer

    See Doer for inherited attributes, properties, and methods.

    Attributes:
       .server is TCP Server instance

    Properties:

    """

    def __init__(self, server, **kwa):
        """
        Initialize

        Parameters:
           server is TCP Server instance
        """
        super(ServerDoer, self).__init__(**kwa)
        self.server = server


    def wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(ServerDoer, self).wind(tymth)
        self.server.wind(tymth)


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
        if self.tymth:
            self.server.wind(self.tymth)
        self.server.reopen(temp=temp)


    def recur(self, tyme):
        """"""
        self.server.service()


    def exit(self):
        """"""
        self.server.close()


class EchoServerDoer(ServerDoer):
    """
    Echo TCP Server
    Just echoes back to client whatever it receives from client

    See Doer for inherited attributes, properties, and methods.

    Inherited Attributes:
        .server is TCP Server instance

    """
    def recur(self, tyme):
        """"""
        self.server.service()
        for ca, ix in self.server.ixes.items():
            if ix.rxbs:
                ix.tx(bytes(ix.rxbs))  # echo back
                ix.clearRxbs()


    def exit(self):
        """"""
        self.server.close()
