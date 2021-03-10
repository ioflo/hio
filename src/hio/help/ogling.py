# -*- encoding: utf-8 -*-
"""
hio.help.ogling module

Provides python stdlib logging module support

"""
import sys
import os
import logging
import logging.handlers
import tempfile
import shutil
from contextlib import contextmanager


def initOgler(level=logging.CRITICAL, **kwa):
    """
    Initialize the ogler global instance once
    Usage:
       # At top level of module in project
       # assign ogler as module global instance availabe at modulename.ogler
       ogler = hio.help.ogling.initOgler()

       # module is mypackage.help  then ogler at mypackage.help.ogler

    Critical is most severe to restrict logging by default

    Parameters:
        force is Boolean True is to force reinit even if global ogler is not None
        level is default logging level

    This should be called in package .__init__ to insure that global ogler is
    defined by default. Users may then reset level and reopen log file if need be
    before calling ogler.getLoggers()
    """
    return Ogler(level=level, **kwa)


@contextmanager
def openOgler(cls=None, name="test", temp=True, **kwa):
    """
    Context manager wrapper Ogler instances.
    Defaults to temporary file logs.
    Context 'with' statements call .close on exit of 'with' block

    Parameters:
        cls is Class instance of subclass instance
        name is str name of ogler instance for filename so can have multiple oglers
             at different paths thar each use different log file directories
        temp is Boolean, True means open in temporary directory, clear on close
                Otherwise open in persistent directory, do not clear on close

    Usage:

    with openOgler(name="bob") as ogler:
        logger = ogler.getLogger()  ....

    with openOgler(name="eve", cls=SubclassedOgler)

    """
    if cls is None:
        cls = Ogler
    try:
        ogler = cls(name=name, temp=temp, reopen=True, **kwa)
        yield ogler

    finally:
        ogler.close()  # if .temp also clears


class Ogler():
    """
    Olgery instances retreive and configure loggers from global logging facility
    Only need one Ogler per application

    Uses python stdlib logging module, logging.getLogger(name).
    Multiple calls to .getLogger() with the same name
    will always return a reference to the same Logger object.

    Attributes:
        .name is str used in file name
        .level is logging severity level
        .temp is Boolean True means use /tmp directory
        .prefix is str used as part of path prefix and formating
        .headDirPath is str used as head of path
        .tailDirpath is str used as tail of path
        .altTailDirPath is str used a alternate tail of path
        .dirPath is full directory path
        .path is full file path
        .opened is Boolean, True means file is opened Otherwise False
    """
    Prefix = "hio"
    HeadDirPath = "/usr/local/var"  # default in /usr/local/var
    TailDirPath = "logs"
    AltHeadDirPath = "~"  #  put in ~ as fallback when desired dir not permitted
    TempHeadDir = "/tmp"
    TempPrefix = "test_"
    TempSuffix = "_temp"

    def __init__(self, name='main', level=logging.ERROR, temp=False,
                 prefix=None, headDirPath=None, reopen=False, clear=False):
        """
        Init Loggery factory instance

        Parameters:
            name is application specific log file name
            level is int logging level from logging. Higher is more restrictive.
                This sets the minimum level of the baseLogger and failLogger
                relative to the global level.
                Logs will output if action level is at or above set level.

                Level    Numeric value
                CRITICAL 50
                ERROR    40
                WARNING  30
                INFO     20
                DEBUG    10
                NOTSET    0

            temp is Boolean True means use /tmp directory If .filed and clear on close
                            False means use  headDirpath If .filed
            prefix is str to include in path and logging template
            headDirPath is str for custom headDirPath for log file
            reopen is Booblean True means reopen path if anything changed
            clear is Boolean True means clear .dirPath when closing in reopen
        """
        self.name = name if name else 'main'  # for file name
        self.level = level  # basic logger level
        self.temp = True if temp else False
        self.prefix = prefix if prefix is not None else self.Prefix
        self.headDirPath = headDirPath if headDirPath is not None else self.HeadDirPath
        self.dirPath = None
        self.path = None
        self.opened = False

        #create formatters
        fmt = "{}: %(message)s".format(self.prefix)
        self.baseFormatter = logging.Formatter(fmt)  # basic format

        #create console handlers and assign formatters
        self.baseConsoleHandler = logging.StreamHandler()  # sys.stderr
        self.baseConsoleHandler.setFormatter(self.baseFormatter)
        if sys.platform == 'darwin':
            address = '/var/run/syslog'
        else:
            address = '/dev/log'
        self.baseSysLogHandler = logging.handlers.SysLogHandler(address=address)
        self.baseSysLogHandler.setFormatter(self.baseFormatter)
        # SysLogHandler only appears to log a ERROR level despite the set level
        #self.baseSysLogHandler.encodePriority(self.baseSysLogHandler.LOG_USER,
                                              #self.baseSysLogHandler.LOG_DEBUG)
        if reopen:
            self.reopen(headDirPath=self.headDirPath, clear=clear)


    def reopen(self, name=None, temp=None, headDirPath=None, clear=False):
        """
        Use or Create if not preexistent, directory path for file .path
        First closes .path if already opened. If clear is True then also clears
        .path before reopening

        Parameters:
            name is optional name
                if None or unchanged then ignore otherwise recreate path
                    When recreating path, If not provided use .name
            temp is optional boolean:
                If None ignore Otherwise
                    Assign to .temp
                    If True then open temporary directory,
                    If False then open persistent directory
            headDirPath is optional str head directory pathname of main database
                if None or unchanged then ignore otherwise recreate path
                   When recreating path, If not provided use default .HeadDirpath
            clear is Boolean True means clear .path when closing
        """
        if self.opened:
            self.close(clear=clear)

        # check for changes in path parts if need to recreate
        if name is not None and name == self.name:
            name = None  # don't need to recreate path because of name change

        if temp is not None and temp == self.temp:
            temp = None  # don't need to recreate path because of temp change

        if headDirPath is not None and headDirPath == self.headDirPath:
            headDirPath = None  # don't need to recreate path because of headDirPath change

        # always recreates if path is empty or if path part has changed
        if (not self.dirPath or
            temp is not None or
            headDirPath is not None or
            name is not None):  # need to recreate self.dirPath, self.path, self.trPath

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

            fileName = "{}.log".format(self.name)
            self.path = os.path.join(self.dirPath, fileName)

            #create file handlers and assign formatters
            self.baseFileHandler = logging.handlers.TimedRotatingFileHandler(
                self.path, when='H', interval=1, backupCount=48)
            self.baseFileHandler.setFormatter(self.baseFormatter)

        self.opened = True


    def close(self, clear=False):
        """
        Close lmdb at .env and if clear or self.temp then remove directory at .path
        Parameters:
           clear is boolean, True means clear directory
        """
        self.opened = False
        if clear or self.temp:
            self.clearDirPath()


    def clearDirPath(self):
        """
        Remove logfile directory at .dirPath
        """
        if self.dirPath and os.path.exists(self.dirPath):
            shutil.rmtree(self.dirPath)


    def resetLevel(self, name=__name__, level=None, globally=False):
        """
        Resets the level of preexisting loggers to level. If level is None then
        use .level
        """
        level = level if level is not None else self.level
        if globally:
            self.level = level
        logger = logging.getLogger(name)  # singleton
        logger.setLevel(level)


    def getLogger(self, name=__name__, level=None):
        """
        Returns Basic Logger
        default is to name logger after module
        """
        logger = logging.getLogger(name)
        logger.propagate = False  # disable propagation of events
        level = level if level is not None else self.level
        logger.setLevel(level)
        for handler in list(logger.handlers):  # remove so no duplicate handlers
            logger.removeHandler(handler)
        logger.addHandler(self.baseConsoleHandler)
        logger.addHandler(self.baseSysLogHandler)
        if self.opened:
            logger.addHandler(self.baseFileHandler)
        return logger

