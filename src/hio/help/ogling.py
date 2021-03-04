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


class Ogler():
    """
    Olgery instances retreive and configure loggers from global logging facility
    Only need one Ogler per application

    Uses python stdlib logging module, logging.getLogger(name).
    Multiple calls to .getLogger() with the same name
    will always return a reference to the same Logger object.

    Attributes:
        .level is logging severity level
        .logFilePath is path to log file
    """
    Prefix = "hio"
    HeadDirPath = "/usr/local/var"  # default in /usr/local/var
    TailDirPath = "log"
    AltHeadDirPath = "~"  #  put in ~ as fallback when desired dir not permitted
    TempHeadDir = "/tmp"
    TempMidfix = "log_"
    TempSuffix = "_test"

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

            file is Boolean True means create logfile Otherwise not
            temp is Boolean If file then True means use temp direction
                                         Otherwise use  headDirpath
            headDirPath is str for custom headDirPath for log file
            clear is Boolean True means clear .path when closing in reopen
        """
        self.name = name if name else 'main'  # for file name
        self.level = level  # basic logger level
        self.temp = True if temp else False
        self.prefix = prefix if prefix is not None else self.Prefix
        self.headDirPath = headDirPath if headDirPath is not None else self.HeadDirPath
        self.tailDirPath = os.path.join(self.prefix, self.TailDirPath)
        self.altTailDirPath = os.path.join(".{}".format(self.prefix), self.TailDirPath)
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
                prefix = "{}_{}".format(self.prefix, self.TempMidfix)
                headDirPath = tempfile.mkdtemp(prefix=prefix,
                                               suffix=self.TempSuffix,
                                               dir="/tmp")
                self.dirPath = os.path.abspath(
                                    os.path.join(headDirPath,
                                                 self.tailDirPath))
                os.makedirs(self.dirPath)

            else:
                self.dirPath = os.path.abspath(
                                    os.path.expanduser(
                                        os.path.join(self.headDirPath,
                                                     self.tailDirPath)))

                if not os.path.exists(self.dirPath):
                    try:
                        os.makedirs(self.dirPath)
                    except OSError as ex:
                        headDirPath = self.AltHeadDirPath
                        self.dirPath = os.path.abspath(
                                            os.path.expanduser(
                                                os.path.join(self.AltHeadDirPath,
                                                             self.altTailDirPath)))
                        if not os.path.exists(self.dirPath):
                            os.makedirs(self.dirPath)
                else:
                    if not os.access(self.dirPath, os.R_OK | os.W_OK):
                        self.dirPath = os.path.abspath(
                                            os.path.expanduser(
                                                os.path.join(self.AltHeadDirPath,
                                                             self.altTailDirPath)))
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
        Close lmdb at .env and if clear or .temp then remove lmdb directory at .path
        Parameters:
           clear is boolean, True means clear lmdb directory
        """
        self.opened = False
        if clear:
            self.clearDirPath()


    def clearDirPath(self):
        """
        Remove logfile directory at .dirPath
        """
        if os.path.exists(self.dirPath):
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

