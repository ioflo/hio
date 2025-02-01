# -*- encoding: utf-8 -*-
"""
hio.core.uxding Module
"""
import sys
import platform
import os
import stat
import errno
import socket
import shutil
from contextlib import contextmanager


from ... import help
from ... import hioing
from ...base import doing, filing

logger = help.ogler.getLogger()


@contextmanager
def openPeer(cls=None, name="test", temp=True, reopen=True, clear=True,
             filed=False, extensioned=True, **kwa):
    """
    Wrapper to create and open UXD Peer instances
    When used in with statement block, calls .close() on exit of with block

    Parameters:
        cls is Class instance of subclass instance
        name is str name of Peer instance path part so can have multiple Peers
             at different paths that each use different dirs or files
        temp is Boolean, True means open in temporary directory, clear on close
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
        with openPeer() as peer0:
            peer0.receive()

        with openPeer(cls=PeerBig) as peer0:
            peer0.receive()

    """
    peer = None
    if cls is None:
        cls = Peer
    try:
        peer = cls(name=name, temp=temp, reopen=reopen, clear=clear,
                   filed=filed, extensioned=extensioned, **kwa)

        yield peer

    finally:
        if peer:
            peer.close(clear=peer.temp or clear)





class Peer(filing.Filer):
    """Class to manage non-blocking io on UXD (unix domain) socket.
    Use instance method .close() to close socket

    Because Unix Domain Sockets are reliable no need for retry tymer.


    Inherited Class Attributes:
        HeadDirPath (str): default abs dir path head such as "/usr/local/var"
        TailDirPath (str): default rel dir path tail when using head
        CleanTailDirPath (str): default rel dir path tail when creating clean
        AltHeadDirPath (str): default alt dir path head such as  "~"
                              as fallback when desired head not permitted.
        AltTailDirPath (str): default alt rel dir path tail as fallback
                              when using alt head.
        AltCleanTailDirPath (str): default alt rel path tail when creating clean
        TempHeadDir (str): default temp abs dir path head such as "/tmp"
        TempPrefix (str): default rel dir path prefix when using temp head
        TempSuffix (str): default rel dir path suffix when using temp head and tail
        Perm (int): explicit default octal perms such as 0o1700
        Mode (str): open mode such as "r+"
        Fext (str): default file extension such as "text" for "fname.text"

    Inherited Attributes:
        name (str): unique path component used in directory or file path name
        base (str): another unique path component inserted before name
        temp (bool): True means use TempHeadDir in /tmp directory
        headDirPath (str): head directory path
        path (str | None):  full directory or file path once created else None
        perm (int):  numeric os permissions for directory and/or file(s)
        filed (bool): True means .path ends in file.
                       False means .path ends in directory
        mode (str): file open mode if filed
        fext (str): file extension if filed
        file (File | None): File instance when filed and created.
        opened (bool): True means directory path, uxd file, and socket are
                created and opened. False otherwise

    Class Attributes:
        Umask (int): octal default umask permissions such as 0o022

    Attributes:
        umask (int): unpermission mask for uxd file, usually octal 0o022
                     .umask is applied after .perm is set if any
        bs (int): buffer size
        wl (WireLog): instance ref for debug logging of over the wire tx and rx
        ls (socket.socket): local socket of this Peer

    """
    HeadDirPath = "/usr/local/var"  # default in /usr/local/var
    TailDirPath = "hio/uxd"
    CleanTailDirPath = "hio/clean/uxd"
    AltHeadDirPath = "~"  # put in ~ as fallback when desired not permitted
    AltTailDirPath = ".hio/uxd"
    AltCleanTailDirPath = ".hio/clean/uxd"
    TempHeadDir = "/tmp"
    TempPrefix = "hio_uxd_"
    TempSuffix = "_test"
    Perm = stat.S_ISVTX | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR  # 0o1700==960
    Mode = "r+"
    Fext = "uxd"
    Umask = 0o022  # default

    def __init__(self, *, umask=None, bs = 1024, wl=None,
                 reopen=False, clear=True,
                 filed=False, extensioned=True, **kwa):
        """Initialization method for instance.
        Inherited Parameters:
            reopen (bool): True (re)open with this init
                           False not (re)open with this init but later (default)
            clear (bool): True means remove directory upon close when reopening
                          False means do not remove directory upon close when reopening
            filed (bool): True means .path is file path not directory path
                          False means .path is directiory path not file path
            extensioned (bool): When not filed:
                                True means ensure .path ends with fext
                                False means do not ensure .path ends with fext
            See Filing.Filer for other inherited paramters


        Parameters:
            umask (int): unpermission mask for uxd file, usually octal 0o022
            bs (int): buffer size
            wl (WireLog): instance ref for debug logging of over the wire tx and rx
        """
        self.umask = umask  # only change umask if umask is not None below
        self.bs = bs
        self.wl = wl
        self.ls = None  # local socket of this Peer, needs to be opened/bound

        super(Peer, self).__init__(reopen=reopen,
                                   clear=clear,
                                   filed=filed,
                                   extensioned=extensioned,
                                   **kwa)


    def actualBufSizes(self):
        """Returns:
            sizes (tuple); duple of the form (int, int) of the (tx, rx)
                actual socket send and receive buffer size

        """
        if not self.ls:
            return (0, 0)

        return (self.ls.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF),
                self.ls.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF))


    def open(self):
        """Opens socket in non blocking mode.

        Returns:
            result (bool): True of opened successfully. False otherwise

        if socket not closed properly, binding socket gets error
            OSError: (48, 'Address already in use')
        """
        #create socket ss = server socket
        self.ls = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

        # make socket address reusable.
        # the SO_REUSEADDR flag tells the kernel to reuse a local socket in
        # TIME_WAIT state, without waiting for its natural timeout to expire.
        self.ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # setup buffers
        if self.ls.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF) <  self.bs:
            self.ls.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self.bs)
        if self.ls.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF) < self.bs:
            self.ls.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.bs)
        self.ls.setblocking(0) #non blocking socket

        # setup umask
        oldumask = None
        if self.umask is not None: # change umask for the uxd file
            oldumask = os.umask(self.umask) # set new and return old

        #bind to file path
        try:
            self.ls.bind(self.path)
        except OSError as ex:
            if not ex.errno == errno.ENOENT: # No such file or directory
                logger.error("Error opening UxD %s\n %s\n", self.path, ex)
                return False
            try:
                os.makedirs(os.path.dirname(self.path))
            except OSError as ex:
                logger.error("Error making UXD %s\n %s\n", self.path, ex)
                return False
            try:
                self.ls.bind(self.path)
            except OSError as ex:
                logger.error("Error binding UXD %s\n %s\n", self.path, ex)
                return False

        if oldumask is not None: # restore old umask
            os.umask(oldumask)

        self.path = self.ls.getsockname()  # get resolved path after bind
        self.opened = True
        return self.opened


    def reopen(self, clear=True, **kwa):
        """Idempotently open socket by closing first if need be

        Returns:
            result (bool): True of opened successfully. False otherwise

        Inherited Parameters:
            clear (bool): True means remove directory and uxd file upon close
                          False means do not remove directory and uxd file upon close
            See filing.Filer for other inherited parameters
        """
        #self.close(clear=clear)

        opened = super(Peer, self).reopen(clear=clear, **kwa)
        if not opened:
            raise hioing.FilerError(f"Failure opening uxd path {self.path}.")

        return self.open()


    def close(self, clear=True):
        """Closes  socket and unlinks UXD file.

        Inherited Parameters:
            clear (bool): True means remove directory/uxd file upon close
                          False means do not remove directory/uxd file upon close
            See filing.Filer for other inherited parameters
        """
        if self.ls:
            self.ls.close() #close socket
            self.ls = None
            self.opened = False

        try:
            super(Peer, self).close(clear=clear)  # removes uxd file at end of path only
        except OSError:
            if os.path.exists(self.path):
                raise

        return self.opened


    def receive(self):
        """Perform non blocking receive on  socket.

        Returns:
            result (tuple): of form (bytes, str | None) labeled (data, src) where
                data is bytes of data received
                src is str uxd source path or None
                If data empty then returns (b'', None) but always returns duple
        """
        try:
            data, src = self.ls.recvfrom(self.bs)  # data, uxd source path
        except socket.error as ex:
            # ex.args[0] is always ex.errno for better compat
            # the value of a given errno.XXXXX may be different on each os
            # EAGAIN: BSD 35, Linux 11, Windows 11
            # EWOULDBLOCK: BSD 35 Linux 11 Windows 140
            if ex.args[0]  in (errno.EAGAIN, errno.EWOULDBLOCK):
                return (b'', None) #receive has nothing empty string for data
            else:
                logger.error("Error receive on UXD %s\n %s\n", self.path, ex)
                raise #re raise exception ex

        if self.wl:
            self.wl.writeRx(data, who=src)

        return (data, src)


    def send(self, data, dst):
        """Perform non blocking send on socket.

        Returns:
            cnt (int): number of bytes actually sent

        Parameters:
           data (bytes): payload to send
           dst (str):  uxd destination path
        """
        try:
            cnt = self.ls.sendto(data, dst)  # count is int number of bytes sent
        except OSError as ex:
            logger.error("Error send UXD from %s to %s.\n %s\n", self.path, dst, ex)
            cnt = 0
            raise

        if self.wl:# log over the wire send
            self.wl.writeTx(data[:cnt], who=dst)

        return cnt

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
        self.peer.close(clear=True)
