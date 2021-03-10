# -*- encoding: utf-8 -*-
"""
hio.help.wiring module

"""

import os
import datetime
import io
import tempfile
import shutil
from contextlib import contextmanager

from ..base import doing

@contextmanager
def openWL(cls=None, name="test", temp=True, **kwa):
    """
    Context manager wrapper WireLog instances.
    Defaults to temporary wire logs.
    Context 'with' statements call .close on exit of 'with' block

    Parameters:
        cls is Class instance of subclass instance
        name is str name of wirelog instance for filename so can have multiple wirelogs
             at different paths thar each use different file name
        temp is Boolean, True means open in temporary directory, clear on close
                Otherwise open in persistent directory, do not clear on close

    Usage:

    with openWL(name="bob") as wl:
        wl.writeRx  ....

    with openWL(name="eve", cls=SubclassedWireLog)

    """
    if cls is None:
        cls = WireLog
    try:
        wl = cls(name=name, temp=temp, reopen=True, **kwa)
        yield wl

    finally:
        wl.close()  # if .temp also clears


class WireLog():
    """
    For debugging of non-blocking transports, provides log files or in memory
    buffers for logging 'over the wire' network tx and rx packets as bytes

    Attributes:
        .rxed is Boolean True means log rx
        .txed is Boolean True means log tx
        .samed is Boolean True means log both rx and tx to same file or buffer
        .filed is Boolean True means log to file False means log to memory buffer
        .fmt is io write bytes printf style format string
            Default is b'\n%(dx)b %(who)b:\n%(data)b\n' where:
                who is src or dst for rx tx respectively
                dx is the io direction and will be set to either b'tx' or b'rx' and
                data is the actual io data as bytes
            to write io data without direction who or line feeds use fmt= b'%(data)b'
        .name is str used in file name
        .temp is Boolean True means use /tmp directory
        .prefix is str used as part of path prefix and formating
        .headDirPath is str used as head of path
        .tailDirpath is str used as tail of path
        .altTailDirPath is str used a alternate tail of path
        .dirPath is full directory path
        .rxl is rx log io file or io buffer
        .txl is tx log io file or io buffer
        .opened is Boolean, True means file is opened Otherwise False

    """
    Prefix = "hio"
    HeadDirPath = "/usr/local/var"  # default in /usr/local/var
    TailDirPath = "wirelogs"
    AltHeadDirPath = "~"  #  put in ~ as fallback when desired dir not permitted
    TempHeadDir = "/tmp"
    TempPrefix = "test_"
    TempSuffix = "_temp"
    Format = b'\n%(dx)b %(who)b:\n%(data)b\n'  # default format string as bytes


    def __init__(self, rxed=True, txed=True, samed=False, filed=False,
                 fmt=None, name='main', temp=False, prefix=None,
                 headDirPath=None, reopen=False, clear=False):
        """
        Init Loggery factory instance

        Parameters:
            rxed is Boolean True means log rx received bytes
            txed is Boolean True means log tx transmitted bytes
            samed is Boolean True means log both rx and tx to same file or buffer
            filed is Boolean True means log file False means log to memory buffer
            fmt is printf style format str or bytes converted based on .byted
            name is application specific log file name
            temp is Boolean True means use /tmp directory If .filed and clear on close
                    False means use  headDirpath If .filed
            prefix is str to include in path and logging template
            headDirPath is str for custom headDirPath for log file
            reopen is Booblean True means reopen path if anything changed
            clear is Boolean True means clear .dirPath when closing in reopen
        """
        self.rxed = True if rxed else False
        self.txed = True if txed else False
        self.samed = True if samed else False
        self.filed = True if filed else False
        self.fmt = fmt if fmt is not None else self.Format
        if hasattr(self.fmt, "encode"):   # ensure bytes
            self.fmt = self.fmt.encode("utf-8")
        self.name = name if name else 'main'  # for file name
        self.temp = True if temp else False
        self.prefix = prefix if prefix is not None else self.Prefix
        self.headDirPath = headDirPath if headDirPath is not None else self.HeadDirPath
        self.dirPath = None
        self.rxl = None  # receive log iofile or iobuffer
        self.txl = None  # transmit log iofile or iobuffer
        self.opened = False

        if reopen:
            self.reopen(headDirPath=self.headDirPath, clear=clear)


    def reopen(self, rxed=None, txed=None, samed=None, filed=None, fmt=None,
               name=None, temp=None, headDirPath=None, clear=False):
        """
        Use or Create if not preexistent, directory path for file .path
        First closes .path if already opened. If clear is True then also clears
        .path before reopening

        Parameters:
            rxed is optional Boolean If None or unchanged then ignore.
                Otherwise when creating io use .rxed if not provided
            txed is optional Boolean If None or unchanged then ignore.
                Otherwise when creating io use .txed if not provided
            samed is optional Boolean If None or unchanged then ignore.
                Otherwise when creating io use .same if not provided
            filed is optional Boolean If None or unchanged then ignore.
                Otherwise when creating io use .filed if not provided
            fmt is optional bytes printf format If None or unchanged then ignore.
                Otherwise when creating io use .fmt if not provided
            name is optional name
                if None or unchanged then ignore otherwise recreate path
                    When recreating path, If not provided use .name
            temp is optional boolean:
                If None ignore Otherwise
                    Assign to .temp
                    If True then open in temporary directory and clear on close,
                    If False then open persistent directory
            headDirPath is optional str head directory pathname of main database
                if None or unchanged then ignore otherwise recreate path
                   When recreating path, If not provided use default .HeadDirpath
            clear is Boolean True means clear .path when closing
        """
        if self.opened:
            self.close(clear=clear)

        # check for changes in creation parameters if need to recreate
        if rxed is not None and rxed == self.rxed:
            rxed = None  # don't need to recreate  because of rxed change
        if txed is not None and txed == self.txed:
            txed = None  # don't need to recreate  because of txed change
        if samed is not None and samed == self.samed:
            samed = None  # don't need to recreate  because of samed change
        if filed is not None and filed == self.filed:
            filed = None  # don't need to recreate  because of filed change
        if fmt is not None and fmt == self.fmt:
            fmt = None
        if name is not None and name == self.name:
            name = None  # don't need to recreate path because of name change
        if temp is not None and temp == self.temp:
            temp = None  # don't need to recreate path because of temp change
        if headDirPath is not None and headDirPath == self.headDirPath:
            headDirPath = None  # don't need to recreate path because of headDirPath change

        # always recreates if dirPath is empty or if some creation parameter has changed
        if (not self.dirPath or
            rxed is not None or
            txed is not None or
            samed is not None or
            filed is not None or
            fmt is not None or
            temp is not None or
            headDirPath is not None or
            name is not None):  # need to recreate self.dirPath etc

            if rxed is not None:
                self.rxed = rxed
            if txed is not None:
                self.txed = txed
            if samed is not None:
                self.samed = samed
            if filed is not None:
                self.filed = filed
            if fmt is not None:
                self.fmt = fmt
                if hasattr(self.fmt, "encode"):   # ensure bytes
                    self.fmt = self.fmt.encode("utf-8")

            if self.rxed or self.txed:
                if self.filed:  # use io files
                    if temp is not None:
                        self.temp = True if temp else False
                    if headDirPath is not None:
                        self.headDirpath = headDirPath
                    if name is not None:  # used below for filename
                        self.name = name

                    if self.temp:
                        dirPath = os.path.abspath(
                                            os.path.join(self.TempHeadDir,
                                                         self.prefix,
                                                         self.TailDirPath))
                        if not os.path.exists(dirPath):
                            os.makedirs(dirPath)  # mkdtemp only makes last dir
                        self.dirPath = tempfile.mkdtemp(prefix=self.TempPrefix,
                                                        suffix=self.TempSuffix,
                                                        dir=dirPath)

                    else:
                        self.dirPath = os.path.abspath(
                                            os.path.expanduser(
                                                os.path.join(self.headDirPath,
                                                             self.prefix,
                                                             self.TailDirPath)))

                        if not os.path.exists(self.dirPath):
                            try:
                                os.makedirs(self.dirPath)
                            except OSError as ex:  # can't make dir
                                # use alt=user's directory instead
                                prefix = ".{}".format(self.prefix)  # hide it
                                self.dirPath = os.path.abspath(
                                                os.path.expanduser(
                                                    os.path.join(self.AltHeadDirPath,
                                                                prefix,
                                                                self.TailDirPath)))
                                if not os.path.exists(self.dirPath):
                                    os.makedirs(self.dirPath)
                        else:  # path exists
                            if not os.access(self.dirPath, os.R_OK | os.W_OK):
                                # but can't access it
                                # use alt=user's directory instead
                                prefix = ".{}".format(self.prefix)  # hide it
                                self.dirPath = os.path.abspath(
                                                os.path.expanduser(
                                                    os.path.join(self.AltHeadDirPath,
                                                                 prefix,
                                                                 self.TailDirPath)))
                                if not os.path.exists(self.dirPath):
                                    os.makedirs(self.dirPath)

                    mode = 'wb+'  # bytes io
                    dts = datetime.datetime.now(datetime.timezone.utc).strftime(
                                                         '%Y-%m-%d_%H-%M-%S_%f')
                    if self.samed:
                        fileName = "{}.{}.log".format(self.name, dts)
                        path = os.path.join(self.dirPath, fileName)
                        try:
                            log = io.open(path, mode=mode)
                            if self.rxed:
                                self.rxl = log
                            if self.txed:
                                self.txl = log
                        except IOError:
                            self.rxl = self.txl = None
                            return self.opened

                    else:
                        if self.rxed:
                            fileName = "{}.{}.rx.log".format(self.name, dts)
                            path = os.path.join(self.dirPath, fileName)
                            try:
                                self.rxl = io.open(path, mode=mode)
                            except IOError:
                                self.rxl = None
                                return self.opened

                        if self.txed:
                            fileName = "{}.{}.tx.log".format(self.name, dts)
                            path = os.path.join(self.dirPath, fileName)
                            try:
                                self.txl = io.open(path, mode=mode)
                            except IOError:
                                self.txl = None
                                return self.opened

                else:  # use io memory buffers
                    if self.samed:
                        try:
                            log = io.BytesIO()
                            if self.rxed:
                                self.rxl = log
                            if self.txed:
                                self.txl = log
                        except IOError:
                            self.rxl = self.txl = None
                            return self.opened
                    else:
                        if self.rxed:
                            try:
                                self.rxl = io.BytesIO()
                            except IOError:
                                self.rxl = None
                                return self.opened

                        if self.txed:
                            try:
                                self.txl = io.BytesIO()
                            except IOError:
                                self.txl = None
                                return self.opened

        self.opened = True
        return self.opened


    def flush(self):
        """
        flush files if any and opened.
        A file flush only moves from program buffer to operating system buffer.
        A file fsync moves from operating system buffer to disk.
        """
        if self.filed:
            if not self.rxl.closed:
                self.rxl.flush()
                os.fsync(self.rxl.fileno())
            if not self.txl.closed and not self.samed:
                self.txl.flush()
                os.fsync(self.txl.fileno())


    def close(self, clear=False):
        """
        Close io logs. If clear or self.temp then remove directory at .dirPath
        Parameters:
           clear is boolean, True means clear directory at .dirPath if any
        """
        self.flush()
        self.opened = False
        if self.txl and not self.txl.closed:
            self.txl.close()
        if self.rxl and not self.rxl.closed:
            self.rxl.close()
        if clear or self.temp:
            self.clearDirPath()


    def clearDirPath(self):
        """
        Remove logfile directory at .dirPath
        """
        if self.dirPath and os.path.exists(self.dirPath):
            shutil.rmtree(self.dirPath)


    def readRx(self):
        """
        Returns rx string buffer value if .buffify else None
        """
        if self.rxl and not self.rxl.closed:
            self.rxl.flush()
            self.rxl.seek(0, io.SEEK_SET)
            return (self.rxl.read())
        return None


    def readTx(self):
        """
        Returns tx string buffer value if .buffify else None
        """
        if self.txl and not self.txl.closed:
            self.txl.flush()
            self.txl.seek(0, io.SEEK_SET)
            return (self.txl.read())
        return None


    def writeRx(self, data, who=b''):
        """
        Write bytes data received from source host port address tuple,
        """
        if self.rxed and self.rxl:
            if not isinstance(who, (bytes, bytearray, str)):
                who = str(who)
            if hasattr(who, 'encode'):
                who = who.encode("utf-8")
            if hasattr(data, 'encode'):
                data = data.encode("utf-8")
            self.rxl.write(self.fmt % {b'dx': b'Rx', b'who': who, b'data': data})


    def writeTx(self, data, who=b''):
        """
        Write bytes data transmitted to destination address da,
        """
        if self.txed and self.txl:
            if not isinstance(who, (bytes, bytearray, str)):
                who = str(who)
            if hasattr(who, 'encode'):
                who = who.encode("utf-8")
            if hasattr(data, 'encode'):
                data = data.encode("utf-8")
            self.txl.write(self.fmt % {b'dx': b'Tx', b'who': who, b'data': data})



class WireLogDoer(doing.Doer):
    """
    Basic WireLog Doer

    Inherited Attributes:
        .done is Boolean completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.

    Attributes:
        .wl is WireLog subclass

    Inherited Properties:
        .tyme is float ._tymist.tyme, relative cycle or artificial time
        .tock is float, desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Properties:

    Methods:
        .wind  injects ._tymist dependency
        .__call__ makes instance callable
            Appears as generator function that returns generator
        .do is generator method that returns generator
        .enter is enter context action method
        .recur is recur context action method or generator method
        .exit is exit context method
        .close is close context method
        .abort is abort context method

    Hidden:
       ._tymist is Tymist instance reference
       ._tock is hidden attribute for .tock property
    """

    def __init__(self, wl, **kwa):
        """
        Inherited Parameters:
           tymist is Tymist instance
           tock is float seconds initial value of .tock

        Parameters:
           keeper is Keeper instance
        """
        super(WireLogDoer, self).__init__(**kwa)
        self.wl = wl


    def enter(self):
        """"""
        if not self.wl.opened:
            self.wl.reopen()


    def exit(self):
        """"""
        self.wl.close()
