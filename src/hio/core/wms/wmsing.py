# -*- encoding: utf-8 -*-
"""
hio.core.wms.wmsing Module

WinMailSlots as datagram transport

"""
import sys
import platform
import os
import stat
import errno
import tempfile
import shutil
from contextlib import contextmanager

try:
    import win32file
except ImportError:
    pass


from ... import help
from ... import hioing
from ...base import doing, filing

logger = help.ogler.getLogger()

class Peer(filing.Filer):
    """Class to manage reliable datagram transport on Windows using Mailslots
    instead of unix domain sockets. WinMailSlot (wms)

    Because win-mail-slots (wms) are reliable no need for retry tymer.
    Because win-mail-slots do not attach the source address we have to
    embed the source address in the memogram header. So we need a new memogram
    header code for wms as reliable transport replacement for uxd on Windows.



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
        MaxGramSize (int): max bytes in in datagram for this transport
        BufSize (int): used to set buffer size for transport datagram buffers


    Attributes:
        umask (int): unpermission mask for uxd file, usually octal 0o022
                     .umask is applied after .perm is set if any
        bc (int | None): count of transport buffers of MaxGramSize
        bs (int): buffer size of transport buffers. When .bc then .bs is calculated
            by multiplying, .bs = .bc * .MaxGramSize. When .bc is None then .bs
            is provided value or default .BufSize
        wl (WireLog): instance ref for debug logging of over the wire tx and rx
        ls (socket.socket): local slot of this Peer

    """
    HeadDirPath = os.path.join(os.path.sep, 'usr', 'local', 'var')  # default in /usr/local/var
    TailDirPath = os.path.join("hio", "wms")
    CleanTailDirPath = os.path.join("hio", "clean", "wms")
    AltHeadDirPath = os.path.expanduser("~")  # put in ~ as fallback when desired not permitted
    AltTailDirPath = os.path.join(".hio", "wms")
    AltCleanTailDirPath = os.path.join(".hio","clean", "wms")
    TempHeadDir = (os.path.join(os.path.sep, "tmp")
                   if platform.system() == "Darwin" else tempfile.gettempdir())
    TempPrefix = "hio_wms_"
    TempSuffix = "_test"
    Perm = stat.S_ISVTX | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR  # 0o1700==960
    Mode = "r+"
    Fext = "wms"
    Umask = 0o022  # default
    MaxGramSize = 65535  # 2 ** 16 - 1  default gram size override in subclass
    BufSize = 65535  # 2 ** 16 - 1  default buffersize


    def __init__(self, *, umask=None, bc=None, bs=None, wl=None,
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
            bc (int | None): count of transport buffers of MaxGramSize
            bs (int | None): buffer size of transport buffers. When .bc is provided
                then .bs is calculated by multiplying, .bs = .bc * .MaxGramSize.
                When .bc is not provided, then if .bs is provided use provided
                value else use default .BufSize
            wl (WireLog): instance ref for debug logging of over the wire tx and rx
        """
        self.umask = umask  # only change umask if umask is not None below
        self.bc = bc
        if self.bc:
            self.bs = self.MaxGramSize * self.bc
        else:
            self.bs = bs if bs is not None else self.BufSize


        self.wl = wl
        self.ls = None  # local slot of this Peer, needs to be opened/bound

        super(Peer, self).__init__(reopen=reopen,
                                   clear=clear,
                                   filed=filed,
                                   extensioned=extensioned,
                                   **kwa)


    def open(self):
        """Opens mailslot in nonblocking mode
        """
        try:
            self.ls = win32file.CreateMailslot(self.path, 0, 0, None)
            # ha = path to mailslot
            # 0 = MaxMessageSize, 0 for unlimited
            # 0 = ReadTimeout, 0 to not block
            # None = SecurityAttributes, none for nothing special
        except win32file.error as ex:
            #console.terse('mailslot.error = {0}'.format(ex))
            return False

        self.opened = True
        return True


    def reopen(self):
        """
        Clear the ms and reopen
        """
        self.close()
        return self.open()

    def close(self):
        '''
        Close the mailslot
        '''
        if self.ls:
            win32file.CloseHandle(self.ls)
            self.ls = None
            self.opened = False

    def receive(self):
        """
        Perform a non-blocking read on the mailslot

        Returns tuple of form (data, sa)
        if no data, returns ('', None)
          but always returns a tuple with 2 elements

        Note win32file.ReadFile returns a tuple: (errcode, data)

        """
        try:
            errcode, data = win32file.ReadFile(self.ls, self.bs)

            # Mailslots don't send their source address
            # We can assign this in a higher level of the stack if needed
            sa = None

            #if console._verbosity >= console.Wordage.profuse:  # faster to check
                #cmsg = ("Server at {0} received from {1}\n"
                           #"{2}\n".format(self.path, sa, data.decode("UTF-8")))
                #console.profuse(cmsg)

            if self.wl:
                self.wl.writeRx(sa, data)

            return (data, sa)

        except win32file.error:
            return (b'', None)

    def send(self, data, dest):
        """
        Perform a non-blocking write on the mailslot
        data is string in python2 and bytes in python3
        da is destination mailslot path

        Parameters:
            data (bytes): to send
            dest (Mailslot):  destination mailslot
        """

        try:
            f = win32file.CreateFile(dest,
                                     win32file.GENERIC_WRITE | win32file.GENERIC_READ,
                                     win32file.FILE_SHARE_READ,
                                     None, win32file.OPEN_ALWAYS, 0, None)
        except win32file.error as ex:
            emsg = 'mailslot.error = {0}: opening mailslot from {1} to {2}\n'.format(
                ex, self.path, dest)
            #console.terse(emsg)
            result = 0
            raise

        try:  # WriteFile returns a tuple, we only care about the number of bytes
            errcode, result = win32file.WriteFile(f, data)
        except win32file.error as ex:
            emsg = 'mailslot.error = {0}: sending from {1} to {2}\n'.format(ex, self.path, dest)
            #console.terse(emsg)
            result = 0
            raise

        finally:
            win32file.CloseHandle(f)

        #if console._verbosity >=  console.Wordage.profuse:
            #cmsg = ("Server at {0} sent to {1}, {2} bytes\n"
                    #"{3}\n".format(self.path, dest, result, data[:result].decode('UTF-8')))
            #console.profuse(cmsg)

        if self.wl:
            self.wl.writeTx(da, data)

        return result
