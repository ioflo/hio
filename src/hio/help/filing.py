# -*- encoding: utf-8 -*-
"""
hio.help.filing module

"""


import os
import stat
import shutil
import tempfile
from contextlib import contextmanager
import errno
import json

import msgpack

from .. import help
from .. import base

logger = help.ogler.getLogger()


def ocfn(path, mode='r+'):
    """
    Atomically open or create file from filepath.

    If file already exists, Then open file using openMode
    Else create file using write update mode If not binary Else
        write update binary mode
    Returns file object

    If binary Then If new file open with write update binary mode
    """
    try:
        # 436 == octal 0664
        newfd = os.open(path, os.O_EXCL | os.O_CREAT | os.O_RDWR, 436)
        if "b" in mode:
            file = os.fdopen(newfd,"w+b")
        else:
            file = os.fdopen(newfd,"w+")

    except OSError as ex:
        if ex.errno == errno.EEXIST:
            file = open(path, mode)
        else:
            raise
    return file


def dump(data, path):
    '''
    Write data as as type self.ext to path as either json or msgpack
    '''
    if ' ' in path:
        raise IOError("Invalid file path '{0}' "
                                "contains space".format(path))

    root, ext = os.path.splitext(path)
    if ext == '.json':
        with ocfn(path, "w+") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
    elif ext == '.mgpk':
        if not msgpack:
            raise IOError("Invalid file path ext '{0}' "
                        "needs msgpack installed".format(path))
        with ocfn(path, "w+b") as f:
            msgpack.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
    else:
        raise IOError("Invalid file path ext '{0}' "
                    "not '.json' or '.mgpk'".format(path))


def load(path):
    '''
    Return data read from file path as dict
    file may be either json or msgpack given by extension .json or .msgpack
    Otherwise return None
    '''
    try:
        root, ext = os.path.splitext(path)
        if ext == '.json':
            with ocfn(path, "r") as f:
                it = json.load(f)
        elif ext == '.mgpk':
            if not msgpack:
                raise IOError("Invalid file path ext '{0}' "
                            "needs msgpack installed".format(path))
            with ocfn(path, "rb") as f:
                it = msgpack.load(f)
        else:
            it = None
    except EOFError:
        return None
    except ValueError:
        return None
    return it



@contextmanager
def openFiler(cls=None, name="test", temp=True, **kwa):
    """
    Context manager wrapper Filer instances for managing a filesystem directory
    and or files in a directory.

    Defaults to using temporary directory path.
    Context 'with' statements call .close on exit of 'with' block

    Parameters:
        cls is Class instance of subclass instance
        name is str name of ogler instance for filename so can have multiple oglers
             at different paths thar each use different log file directories
        temp is Boolean, True means open in temporary directory, clear on close
                Otherwise open in persistent directory, do not clear on close

    Usage:

    with openFiler(name="bob") as filer:

    with openFiler(name="eve", cls=FilerSubClass) as filer:

    """
    if cls is None:
        cls = Filer
    try:
        filer = cls(name=name, temp=temp, reopen=True, **kwa)
        yield filer

    finally:
        if filer:
            filer.close(clear=filer.temp)  # clears if filer.temp



class Filer():
    """
    Filer instances manage file directories and files to hold keri installation
    specific resources like databases and configuration files.


    Attributes:
        .name (str): unique path component used in directory or file path name
        .base (str): another unique path component inserted before name
        .temp (bool): True means use /tmp directory
        .headDirPath is head directory path
        .path is full directory path
        .perm is numeric os permissions for directory and/or file(s)
        .filed (bool): True means .path ends in file.
                       False means .path ends in directory
        .mode (str): file open mode if filed
        .fext (str): file extension if filed
        .file (File)
        .opened is Boolean, True means directory created and if file then file
                is opened. False otherwise


    File/Directory Creation Mode Notes:
        .Perm provides default restricted access permissions to directory and/or files
        stat.S_ISVTX | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
        0o1700==960

        stat.S_ISVTX  is Sticky bit. When this bit is set on a directory it means
            that a file in that directory can be renamed or deleted only by the
            owner of the file, by the owner of the directory, or by a privileged process.
            When this bit is set on a file it means nothing
        stat.S_IRUSR Owner has read permission.
        stat.S_IWUSR Owner has write permission.
        stat.S_IXUSR Owner has execute permission.
    """
    HeadDirPath = "/usr/local/var"  # default in /usr/local/var
    TailDirPath = "hio"
    CleanTailDirPath = "hio/clean"
    AltHeadDirPath = "~"  # put in ~ as fallback when desired not permitted
    AltTailDirPath = ".hio"
    AltCleanTailDirPath = ".hio/clean"
    TempHeadDir = "/tmp"
    TempPrefix = "hio_"
    TempSuffix = "_test"
    Perm = stat.S_ISVTX | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR  # 0o1700==960
    Mode = "w+"
    Fext = "txt"

    def __init__(self, name='main', base="", temp=False, headDirPath=None,
                 perm=None, reopen=True, clear=False, reuse=False, clean=False,
                 filed=False, mode=None, fext=None, **kwa):
        """
        Setup directory of file at .path

        Parameters:
            name (str): directory path name differentiator directory/file
                When system employs more than one keri installation, name allows
                differentiating each instance by name
            base (str): optional directory path segment inserted before name
                that allows further differentation with a hierarchy. "" means
                optional.
            temp (bool): assign to .temp
                True then open in temporary directory, clear on close
                Otherwise then open persistent directory, do not clear on close
            headDirPath (str): optional head directory pathname for main database
                Default .HeadDirPath
            mode (int): optional numeric os dir permissions for database
                directory and database files. Default .DirMode
            reopen (bool): True means (re)opened by this init
                           False  means not (re)opened by this init but later
            clear (bool): True means remove directory upon close if reopon
                          False means do not remove directory upon close if reopen
            reuse (bool): True means reuse self.path if already exists
                          False means do not reuse but remake self.path
            clean (bool): True means path uses clean tail variant
                             False means path uses normal tail variant
            filed (bool): True means .path is file path not directory path
                          False means .path is directiory path not file path
            mode (str): File open mode when filed
            fext (str): File extension when filed

        """
        self.name = name
        self.base = base
        self.temp = True if temp else False
        self.headDirPath = headDirPath if headDirPath is not None else self.HeadDirPath
        self.perm = perm if perm is not None else self.Perm
        self.path = None
        self.filed = True if filed else False
        self.mode = mode if mode is not None else self.Mode
        self.fext = fext if fext is not None else self.Fext
        self.file = None
        self.opened = False

        if reopen:
            self.reopen(clear=clear, reuse=reuse, clean=clean, **kwa)


    def reopen(self, temp=None, headDirPath=None, perm=None, clear=False,
               reuse=False, clean=False, mode=None, fext=None, **kwa):
        """
        Open if closed or close and reopen if opened or create and open if not

        Parameters:
            temp (bool): assign to .temp
                         True means open in temporary directory, clear on close
                         False means open persistent directory, do not clear on close
            headDirPath (str): optional head directory pathname for main database
                               Default .HeadDirpath
            perm (int): optional numeric os dir permissions for database
                         directory and database files. Default .Perm
            clear (bool): True means remove directory upon close
                             False means do not remove directory upon close
            reuse (bool): True means reuse self.path if already exists
                             False means do not reuse but remake self.path
            clean (bool): True means path uses clean tail variant
                             False means path uses normal tail variant
            mode (str): file open mode when .filed
            fext (str): File extension when .filed
        """
        self.close(clear=clear)

        if temp is not None:
            self.temp = temp
        if headDirPath is not None:
            self.headDirPath = headDirPath
        if perm is not None:
            self.perm = perm
        if mode is not None:
            self.mode = mode
        if fext is not None:
            self.fext = fext

        if not self.path or not os.path.exists(self.path) or not reuse:
            self.path, self.file = self.remake(name=self.name,
                                               base=self.base,
                                               temp=self.temp,
                                               headDirPath=self.headDirPath,
                                               perm=self.perm,
                                               clean=clean,
                                               filed=self.filed,
                                               mode=self.mode,
                                               fext=self.fext,
                                               **kwa)
        elif self.filed:
            self.file = ocfn(self.path, mode=self.mode)

        self.opened = True if not self.filed else not self.file.closed

        return self.opened


    def remake(self, *, name="", base="", temp=None, headDirPath=None, perm=None,
                clean=False, filed=False, mode=None, fext=None, **kwa):
        """
        Make and return (path. file) by opening or creating and opening if not
        preexistent, directory or file at  path

        Parameters:
            name (str): unique name alias portion of path
            base (str): optional base inserted before name in path
            temp (bool): optional
                None means ignore,
                True means open temporary directory, may clear on close
                False menans open persistent directory, may not clear on close

            headDirPath (str): optional head directory pathname of main database

            perm (int): directory or file permissions such as
                stat.S_IRUSR Owner has read permission.
                stat.S_IWUSR Owner has write permission.
                stat.S_IXUSR Owner has execute permission.

            clean (bool): True means make path for cleaned version and  remove
                          old directory or file at clean path if any.
                          False means make path normally (not clean)

            filed (bool): True means .path is file path not directory path
                          False means .path is directiory path not file path
            mode (str): file open mode when .filed such as "w+"
            fext (str): File extension when .filed
        """
        file = None
        temp = True if temp else False

        # use class defaults here so can use makePath for other dirs and files
        if headDirPath is None:
            headDirPath = self.HeadDirPath
        if perm is None:
            perm = self.Perm
        if mode is None:
            mode = self.Mode
        if fext is None:
            fext = self.Fext

        tailDirPath = self.CleanTailDirPath if clean else self.TailDirPath
        altTailDirPath = self.AltCleanTailDirPath if clean else self.AltTailDirPath

        if filed:
            root, ext = os.path.splitext(name)
            if not ext:
                name = f"{name}.{fext}"

        if temp:
            headDirPath = tempfile.mkdtemp(prefix=self.TempPrefix,
                                           suffix=self.TempSuffix,
                                           dir=self.TempHeadDir)

            path = os.path.abspath(
                                os.path.join(headDirPath,
                                             tailDirPath,
                                             base,
                                             name))

            if clean and os.path.exists(path):
                if os.path.isfile(path):
                    if filed:
                        os.remove(path)  # rm only file not dir
                    else:
                        head, tail = os.path.split(path)
                        shutil.rmtree(head)  # rm directory and all files
                else:
                    shutil.rmtree(path)

            if filed:
                head, tail = os.path.split(path)
                if not os.path.exists(head):
                    os.makedirs(head)
                file = ocfn(path, mode=mode)
            else:
                os.makedirs(path)

        else:
            path = os.path.abspath(
                        os.path.expanduser(
                            os.path.join(headDirPath,
                                         tailDirPath,
                                         base,
                                         name)))

            if clean and os.path.exists(path):
                if os.path.isfile(path):
                    if filed:
                        os.remove(path)  # rm only file not dir
                    else:
                        head, tail = os.path.split(path)
                        shutil.rmtree(head)  # rm directory and all files
                else:
                    shutil.rmtree(path)

            if not os.path.exists(path):  # no path so attempt to create
                try:
                    if filed:
                        head, tail = os.path.split(path)
                        if not os.path.exists(head):
                            os.makedirs(head)
                        file = ocfn(path, mode=mode)
                    else:
                        os.makedirs(path)

                except OSError as ex:  # use alt instead should always succeed
                    headDirPath = self.AltHeadDirPath
                    path = os.path.abspath(
                                os.path.expanduser(
                                    os.path.join(headDirPath,
                                                 altTailDirPath,
                                                 base,
                                                 name)))
                    if not os.path.exists(path):
                        if filed:
                            head, tail = os.path.split(path)
                            if not os.path.exists(head):
                                os.makedirs(head)
                            file = ocfn(path, mode=mode)
                        else:
                            os.makedirs(path)

            else:  # verify access
                if not os.access(path, os.R_OK | os.W_OK): # use alt instead
                    headDirPath = self.AltHeadDirPath
                    path = os.path.abspath(
                                os.path.expanduser(
                                    os.path.join(headDirPath,
                                                 altTailDirPath,
                                                 base,
                                                 name)))
                    if not os.path.exists(path):
                        if filed:
                            head, tail = os.path.split(path)
                            if not os.path.exists(head):
                                os.makedirs(head)
                            file = ocfn(path, mode=mode)
                        else:
                            os.makedirs(path)
                else:
                    if filed:
                        file = ocfn(path, mode=mode)

            os.chmod(path, perm)  # set dir/file permissions

        return (path, file)


    def close(self, clear=False):
        """
        Close .file if any and if clear rm directory or file at .path

        Parameters:
           clear (bool): True means remove dir or file at .path
        """
        if self.file:
            self.file.close()
        self.opened = False

        if clear:
            self._cleaPath()

        return self.opened


    def _cleaPath(self):
        """
        Remove directory/file at end of .path
        """
        if self.path and os.path.exists(self.path):
            if os.path.isfile(self.path):
                if self.filed:
                    self.file = None
                    os.remove(self.path)  # rm only file not head dir

                if self.temp:  # remove head directory anyway
                    head, tail = os.path.split(self.path)
                    shutil.rmtree(head)  # rm directory and all files
            else:
                shutil.rmtree(self.path)



class FilerDoer(base.Doer):
    """
    Basic Baser Doer ( LMDB Database )

    Attributes:  (inherited)
        done (bool): completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.

    Attributes:
        .filer is Filer subclass

    Properties:  (inherited)
        .tyme is float relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        .tymth is function wrapper closure returned by Tymist .tymeth() method.
            When .tymth is called it returns associated Tymist .tyme.
            .tymth provides injected dependency on Tymist tyme base.
        .tock is float, desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Properties:

    Methods:
        .wind  injects ._tymth dependency from associated Tymist to get its .tyme
        .__call__ makes instance callable
            Appears as generator function that returns generator
        .do is generator method that returns generator
        .enter is enter context action method
        .recur is recur context action method or generator method
        .exit is exit context method
        .close is close context method
        .abort is abort context method

    Hidden:
       ._tymth is injected function wrapper closure returned by .tymen() of
            associated Tymist instance that returns Tymist .tyme. when called.
       ._tock is hidden attribute for .tock property
    """

    def __init__(self, filer, **kwa):
        """
        Inherited Parameters:
           tymist is Tymist instance
           tock is float seconds initial value of .tock

        Parameters:
           filer is Filer instance
        """
        super(FilerDoer, self).__init__(**kwa)
        self.filer = filer

    def enter(self):
        """"""
        if not self.filer.opened:
            self.filer.reopen()

    def exit(self):
        """"""
        self.filer.close(clear=self.filer.temp)
