# -*- encoding: utf-8 -*-
"""hio.help.during module

Support for Durable storage using LMDB
"""

from __future__ import annotations  # so type hints of classes get resolved later

import os
import platform
import stat
import tempfile
from contextlib import contextmanager

import lmdb
from ordered_set import OrderedSet as oset

import hio

from hio import HierError
from .doing import Doer
from .filing import Filer
from ..help import isNonStringIterable, RegDom



class Duror(Filer):
    """Manages an an LMDB database directory and environment.

    Inherited Class Attributes:  (see Filer)
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


    Inherited Attributes:  (see Filer)
        name (str): unique path component at end of path for directory or file
        base (str): another unique path component inserted before name
        temp (bool): True means use TempHeadDir in /tmp directory
        headDirPath (str): head directory path
        path (str | None):  full directory or file path once created else None
        perm (int):  octal OS permissions for path directory and/or file
        filed (bool): True means .path ends in file.
                      False means .path ends in directory
        extensioned (bool): When not filed:
                                True means ensure .path ends with fext
                                False means do not ensure .path ends with fext
        mode (str): file open mode if filed
        fext (str): file extension if filed
        file (File | None): File instance when filed and created.
        opened (bool): True means directory created and if filed then file
                is opened. False otherwise


    Attributes:
        env (lmdb.env): LMDB main (super) database environment
        readonly (bool): True means open LMDB env as readonly

    Properties:
        version

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
    HeadDirPath = os.path.join(os.path.sep, "usr", "local", "var")  # default in /usr/local/var
    TailDirPath = os.path.join("hio", "db")
    CleanTailDirPath = os.path.join("hio", "clean", "db")
    AltHeadDirPath = os.path.expanduser("~")  # put in ~ as fallback when desired not permitted
    AltTailDirPath = os.path.join(".hio", "db")
    AltCleanTailDirPath = os.path.join(".hio", "clean", "db")
    TempHeadDir = (os.path.join(os.path.sep, "tmp")
                   if platform.system() == "Darwin" else tempfile.gettempdir())
    TempPrefix = "hio_lmdb_"
    TempSuffix = "_test"
    Perm = stat.S_ISVTX | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR  # 0o1700==960
    MaxNamedDBs = 16
    MapSize = 104857600
    SuffixSize = 32  # does not include separator
    MaxSuffix = int("f"*(SuffixSize), 16)


    def __init__(self, readonly=False, **kwa):
        """Setup main database directory at .dirpath.
        Create main database environment at .env using .path.

        Inherited Parameters: (see Filer)
            name (str): Unique identifier of file. Unique directory path name
                differentiator directory/file
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
            perm (int): optional numeric os dir permissions for database
                directory and database files. Default .DirMode
            reopen (bool): True (re)open with this init
                           False not (re)open with this init but later (default)
            clear (bool): True means remove directory upon close when reopening
                          False means do not remove directory upon close when reopening
            reuse (bool): True means reuse self.path if already exists
                          False means do not reuse but remake self.path
            clean (bool): True means path uses clean tail variant
                             False means path uses normal tail variant
            filed (bool): True means .path is file path not directory path
                          False means .path is directiory path not file path
            extensioned (bool): When not filed:
                                True means ensure .path ends with fext
                                False means do not ensure .path ends with fext
            mode (str): File open mode when filed
            fext (str): File extension when filed or extensioned

        Parameters:
            readonly (bool): True means open database in readonly mode
                                False means open database in read/write mode

        """

        self.env = None
        self._version = None
        self.readonly = True if readonly else False
        super(Duror, self).__init__(**kwa)


    def reopen(self, readonly=False, **kwa):
        """Open if closed or close and reopen if opened or create and open if not
        if not preexistent, directory path for lmdb at .path and then
        Open lmdb and assign to .env

        Inherited Parameters:  (see Filer)
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

        Parameters:
            readonly (bool): True means open database in readonly mode
                                False means open database in read/write mode
        """
        exists = self.exists(name=self.name, base=self.base)
        opened = super(Duror, self).reopen(**kwa)
        if readonly is not None:
            self.readonly = readonly

        # open lmdb major database instance
        # creates files data.mdb and lock.mdb in .dbDirPath
        self.env = lmdb.open(self.path,
                             max_dbs=self.MaxNamedDBs,
                             map_size=self.MapSize,
                             mode=self.perm,
                             readonly=self.readonly)

        self.opened = True if opened and self.env else False

        if self.opened and not self.readonly and (not exists or self.temp):
            self.version = hio.__version__

        return self.opened

    @property
    def version(self):
        """ Return the version of database stored in __version__ key.

        This value is read through cached in memory

        Returns:
            version (str): semver string
                the version of the database or None if not set in the database

        """
        if self._version is None:
            self._version = self.getVer()

        return self._version

    @version.setter
    def version(self, version):
        """Set the version of the database in memory and in the __version__ key

        Parameters:
            version (str): The new semver formatted version of the database

        """
        if hasattr(version, "decode"):
            version = version.decode("utf-8")  # convert bytes to str

        self._version = version
        self.setVer(self._version)


    def close(self, clear=False):
        """Close lmdb at .env
        if clear or .temp then remove lmdb directory at .path

        Parameters:
           clear (bool), True means clear lmdb directory after close
                         Otherwise do not clear after close
        """
        if self.env:
            try:
                self.env.close()
            except:
                pass

        self.env = None

        return super(Duror, self).close(clear=clear)


    def getVer(self):
        """Returns the value of the the semver formatted version in the
        __version__ key in this database

        Returns:
            str: semver formatted version of the database

        """
        with self.env.begin() as txn:
            cursor = txn.cursor()
            version = cursor.get(b'__version__')
            return version.decode("utf-8") if version is not None else None


    def setVer(self, version):
        """ Set the version of the database in the __version__ key

        Parameters:
            version (str): The new semver formatted version str of the database

        """
        if hasattr(version, "encode"):
            version = version.encode("utf-8")  # convert str to bytes

        with self.env.begin(write=True) as txn:
            cursor = txn.cursor()
            cursor.replace(b'__version__', version)


    # For subdbs with no duplicate values allowed at each key. (dupsort==False)
    def putVal(self, sdb, key, val):
        """Write serialized bytes val to location key in db (subdb)
        Does not overwrite.
        Returns:
            result (bool):  True if val successfully written
                            False if val at key already exitss

        Parameters:
            db (lmdb._Database): opened named subdb with dupsort=False
            key (bytes): within subdb's keyspace
            val (bytes):  to be written at key
        """
        with self.env.begin(db=sdb, write=True, buffers=True) as txn:
            try:
                return (txn.put(key, val, overwrite=False))
            except lmdb.BadValsizeError as ex:
                raise KeyError(f"Key: `{key}` is either empty, too big (for lmdb),"
                               " or wrong DUPFIXED size.") from ex


    def setVal(self, sdb, key, val):
        """Write serialized bytes val to location key in db
        Overwrites existing val if any
        Returns:
            result (bool): True If val successfully written
                           False otherwise

        Parameters:
            db (lmdb._Database): opened named subdb with dupsort=False
            key (bytes): within subdb's keyspace
            val (bytes):  to be written at key
        """
        with self.env.begin(db=sdb, write=True, buffers=True) as txn:
            try:
                return (txn.put(key, val))
            except lmdb.BadValsizeError as ex:
                raise KeyError(f"Key: `{key}` is either empty, too big (for lmdb),"
                               " or wrong DUPFIXED size.") from ex


    def getVal(self, sdb, key):
        """Get val at key in db

        Returns:
            val (bytes|memoryview):  None if no entry at key

        Parameters:
            db (lmdb._Database): opened named subdb with dupsort=False
            key (bytes): within subdb's keyspace

        """
        with self.env.begin(db=sdb, write=False, buffers=True) as txn:
            try:
                return(txn.get(key))
            except lmdb.BadValsizeError as ex:
                raise KeyError(f"Key: `{key}` is either empty, too big (for lmdb),"
                               " or wrong DUPFIXED size.") from ex


    def delVal(self, sdb, key):
        """Deletes value at key in db.

        Returns:
            result (bool): True If key exists in database
                           False otherwise

        Parameters:
            db (lmdb._Database): opened named subdb with dupsort=False
            key (bytes): within subdb's keyspace
        """
        with self.env.begin(db=sdb, write=True, buffers=True) as txn:
            try:
                return (txn.delete(key))
            except lmdb.BadValsizeError as ex:
                raise KeyError(f"Key: `{key}` is either empty, too big (for lmdb),"
                               " or wrong DUPFIXED size.") from ex


    def cntVals(self, sdb):
        """Counts entries in subdb db

        Returns:
            count (int): number of entries in subdb db, or zero otherwise

        Parameters:
            db (lmdb._Database): opened named subdb with dupsort=False
        """
        with self.env.begin(db=sdb, write=False, buffers=True) as txn:
            cursor = txn.cursor()
            count = 0
            for _, _ in cursor:
                count += 1
            return count


    def getTopItemIter(self, sdb, top=b''):
        """Iterates over branch of subdb db rooted at top key

        Returns:
            items (Iterator): of (full key, val) tuples over a branch of the db
                given by top key where: full key is full database key for val
                not truncated top key

        Raises StopIteration Error when empty.

        Parameters:
            db (lmdb._Database): instance of named sub db with dupsort==False
            top (bytes): truncated top key, a key space prefix to get all the items
                        from multiple branches of the key space. If top key is
                        empty then gets all items in database.
                        In Python str.startswith('') always returns True so if branch
                        key is empty string it matches all keys in db with startswith.
        """
        with self.env.begin(db=sdb, write=False, buffers=True) as txn:
            cursor = txn.cursor()
            if cursor.set_range(top):  # move to val at key >= key if any
                for ckey, cval in cursor.iternext():  # get key, val at cursor
                    ckey = bytes(ckey)
                    if not ckey.startswith(top): #  prev entry if any last in branch
                        break  # done
                    yield (ckey, cval)  # another entry in branch startswith key
            return  # done raises StopIteration


    def delTopVals(self, sdb, top=b''):
        """Deletes all values in branch of db given top key.

        Returns:
            result (bool): True if values were deleted at key.
                           False otherwise if no values at key

        Parameters:
            db (lmdb._Database): instance of named sub db with dupsort==False
            top (bytes): truncated top key, a key space prefix to get all the items
                        from multiple branches of the key space. If top key is
                        empty then deletes all items in database

        Raises StopIteration Error when empty.

        """
        # when deleting can't use cursor.iternext() because the cursor advances
        # twice (skips one) once for iternext and once for delete.
        with self.env.begin(db=sdb, write=True, buffers=True) as txn:
            result = False
            cursor = txn.cursor()
            if cursor.set_range(top):  # move to val at key >= key if any
                ckey, cval = cursor.item()
                while ckey:  # end of database key == b''
                    ckey = bytes(ckey)
                    if not ckey.startswith(top): #  prev entry if any last in branch
                        break  # done
                    result = cursor.delete() or result # delete moves cursor to next item
                    ckey, cval = cursor.item()  # cursor now at next item after deleted
            return result


    # insertion ordered FIFO collection set
    @staticmethod
    def suffix(key: bytes|str|memoryview, ion: int, *, sep: bytes|str=b'.'):
        """
        Returns:
           iokey (bytes): actual DB key after concatenating suffix as hex version
           of insertion ordering ordinal int ion using separator sep.

        Parameters:
            key (bytes|str|memoryview): apparent effective database key (unsuffixed)
            ion (int)): insertion ordered ordinal numberfor set of vals
            sep (bytes): separator character(s) for concatenating suffix
        """
        if isinstance(key, memoryview):
            key = bytes(key)
        elif hasattr(key, "encode"):
            key = key.encode()  # encode str to bytes
        if hasattr(sep, "encode"):
            sep = sep.encode()
        ion =  b"%032x" % ion
        return sep.join((key, ion))

    @staticmethod
    def unsuffix(iokey: bytes|str|memoryview, *, sep: bytes|str=b'.'):
        """
        Returns:
           result (tuple): (bytes: key, int: ion) from splitting iokey at rightmost
            separator sep.
            Where key is bytes apparent effective DB key
            Where ion is int insertion orderered ordinal number converted from
                stripped off hex suffix

        Parameters:
            iokey (bytes|str|memoryview): actual database key suffixed
            sep (bytes): separator character(s) for splitting suffix
        """
        if isinstance(iokey, memoryview):
            iokey = bytes(iokey)
        elif hasattr(iokey, "encode"):
            iokey = iokey.encode()  # encode str to bytes
        if hasattr(sep, "encode"):
            sep = sep.encode()
        key, ion = iokey.rsplit(sep=sep, maxsplit=1)
        ion = int(ion, 16)
        return (key, ion)


    def putIoSetVals(self, sdb, key, vals, *, sep=b'.'):
        """Adds each val in vals to insertion ordered set of values all with the
        same apparent effective key for each val that is not already in set of
        vals at key.
        Uses hidden ordinal key suffix for insertion ordering.
        The suffix is appended and stripped transparently.

        Returns:
           result (bool): True if added to set. False if already in set.

        Parameters:
            db (lmdb._Database): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
            vals (Iterable): serialized values to add to set of vals at key

        """
        result = False
        vals = oset(vals)  # make set
        with self.env.begin(db=sdb, write=True, buffers=True) as txn:
            ion = 0
            iokey = self.suffix(key, ion, sep=sep)  # start zeroth entry if any
            cursor = txn.cursor()
            if cursor.set_range(iokey):  # move to val at key >= iokey if any
                pvals = oset()  # pre-existing vals at key
                for iokey, val in cursor.iternext():  # get iokey, val at cursor
                    ckey, cion = self.unsuffix(iokey, sep=sep)
                    if ckey == key:
                        pvals.add(val)  # another entry at key
                        ion = cion + 1  # ion to add at is increment of cion
                    else:  # prev entry if any was the last entry for key
                        break  # done
                vals -= pvals  # remove vals already in pvals

            for i, val in enumerate(vals):
                iokey = self.suffix(key, ion+i, sep=sep)  # ion is at add on amount
                result = cursor.put(iokey,
                                    val,
                                    dupdata=False,
                                    overwrite=False) or result  # not short circuit
            return result


    def addIoSetVal(self, sdb, key, val, *, sep=b'.'):
        """Add val idempotently to insertion ordered set of values all with the
        same apparent effective key if val not already in set of vals at key. A
        Uses hidden ordinal key suffix for insertion ordering.
        The suffix is appended and stripped transparently.

        Returns:
           result (bool): True is added to set. False if already in set.

        Parameters:
            db (lmdb._Database): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
            val (bytes): serialized value to add

        """
        with self.env.begin(db=sdb, write=True, buffers=True) as txn:
            vals = oset()
            ion = 0
            iokey = self.suffix(key, ion, sep=sep)  # start zeroth entry if any
            cursor = txn.cursor()
            if cursor.set_range(iokey):  # move to val at key >= iokey if any
                for iokey, cval in cursor.iternext():  # get iokey, val at cursor
                    ckey, cion = self.unsuffix(iokey, sep=sep)
                    if ckey == key:
                        vals.add(cval)  # another entry at key
                        ion = cion + 1 # ion to add at is increment of cion
                    else:  # prev entry if any was the last entry for key
                        break  # done

            if val in vals:  # already in set
                return False

            iokey = self.suffix(key, ion, sep=sep)  # ion is at add on amount
            return cursor.put(iokey, val, dupdata=False, overwrite=False)


    def setIoSetVals(self, sdb, key, vals, *, sep=b'.'):
        """Erase all vals at key and then add unique vals as insertion ordered set of
        values all with the same apparent effective key.
        Uses hidden ordinal key suffix for insertion ordering.
        The suffix is appended and stripped transparently.

        Returns:
           result (bool): True is added to set.

        Parameters:
            db (lmdb._Database): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
            vals (abc.Iterable): serialized values to add to set of vals at key
        """
        self.delIoSetVals(sdb=sdb, key=key, sep=sep)
        result = False
        vals = oset(vals)  # make set
        with self.env.begin(db=sdb, write=True, buffers=True) as txn:
            for i, val in enumerate(vals):
                iokey = self.suffix(key, i, sep=sep)  # ion is at add on amount
                result = txn.put(iokey, val, dupdata=False, overwrite=True) or result
            return result



    def getIoSetVals(self, sdb, key, *, ion=0, sep=b'.'):
        """Gets list of all the insertion orderd set of values at key

        Returns:
            ioset (oset): the insertion ordered set of values at same apparent
                           effective key.
                          Uses hidden ordinal key suffix for insertion ordering.
                          The suffix is appended and stripped transparently.

        Parameters:
            db (lmdb._Database): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
            ion (int): starting ordinal value, default 0

        """
        with self.env.begin(db=sdb, write=False, buffers=True) as txn:
            vals = []
            iokey = self.suffix(key, ion, sep=sep)  # start ion th value for key zeroth default
            cursor = txn.cursor()
            if cursor.set_range(iokey):  # move to val at key >= iokey if any
                for iokey, val in cursor.iternext():  # get iokey, val at cursor
                    ckey, cion = self.unsuffix(iokey, sep=sep)
                    if ckey != key:  # prev entry if any was the last entry for key
                        break  # done
                    vals.append(val)  # another entry at key
            return vals


    def getIoSetValsIter(self, sdb, key, *, ion=0, sep=b'.'):
        """Gets Iterator of all the insertion ordered set of values at key

        Returns:
            ioset (Iterator): iterator over insertion ordered set of values
                              at same apparent effective key.
                              Uses hidden ordinal key suffix for insertion ordering.
                              The suffix is appended and stripped transparently.

        Raises StopIteration Error when empty.

        Parameters:
            db (lmdb._Database): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
            ion (int): starting ordinal value, default 0
        """
        with self.env.begin(db=sdb, write=False, buffers=True) as txn:
            iokey = self.suffix(key, ion, sep=sep)  # start ion th value for key zeroth default
            cursor = txn.cursor()
            if cursor.set_range(iokey):  # move to val at key >= iokey if any
                for iokey, val in cursor.iternext():  # get key, val at cursor
                    ckey, cion = self.unsuffix(iokey, sep=sep)
                    if ckey != key: #  prev entry if any was the last entry for key
                        break  # done
                    yield (val)  # another entry at key
            return  # done raises StopIteration


    def getIoSetValLast(self, sdb, key, *, sep=b'.'):
        """Gets last value (last in) of insertion ordered set values at key
        Returns:
            val (bytes): last added empty at apparent effective key if any,
                         otherwise None if no entry

        Uses hidden ordinal key suffix for insertion ordering.
            The suffix is appended and stripped transparently.

        Parameters:
            db (lmdb._Database): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
        """
        val = None
        ion = None  # no last value
        iokey = self.suffix(key, ion=self.MaxSuffix, sep=sep)  # make iokey at max and walk back
        with self.env.begin(db=sdb, write=False, buffers=True) as txn:
            cursor = txn.cursor()  # create cursor to walk back
            if not cursor.set_range(iokey):  # max is past end of database
                # Three possibilities for max past end of database
                # 1. last entry in db is for same key
                # 2. last entry in db is for other key before key
                # 3. database is empty
                if cursor.last():  # not 3. empty db, so either 1. or 2.
                    ckey, cion = self.unsuffix(cursor.key(), sep=sep)
                    if ckey == key:  # 1. last is last entry for same key
                        ion = cion  # so set ion to cion
            else:  # max is not past end of database
                # Two possibilities for max not past end of databseso
                # 1. cursor at max entry at key
                # 2. other key after key with entry in database
                ckey, cion = self.unsuffix(cursor.key(), sep=sep)
                if ckey == key:  # 1. last entry for key is already at max
                    ion = cion
                else:  # 2. other key after key so backup one entry
                    # Two possibilities: 1. no prior entry 2. prior entry
                    if cursor.prev():  # prev entry, maybe same or earlier pre
                        # 2. prior entry with two possiblities:
                        # 1. same key
                        # 2. other key before key
                        ckey, cion = self.unsuffix(cursor.key(), sep=sep)
                        if ckey == key:  # prior (last) entry at key
                            ion = cion  # so set ion to the cion

            if ion is not None:
                iokey = self.suffix(key, ion=ion, sep=sep)
                val = cursor.get(iokey)

            return val


    def cntIoSetVals(self, sdb, key, *, sep=b'.'):
        """Count all values with the same apparent effective key.
        Uses hidden ordinal key suffix for insertion ordering.
        The suffix is appended and stripped transparently.

        Returns:
            count (int): count values in set at apparent effective key

        Parameters:
            db (lmdb._Database): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
        """
        return len(self.getIoSetVals(sdb=sdb, key=key, sep=sep))


    def delIoSetVals(self, sdb, key, *, sep=b'.'):
        """Deletes all values at apparent effective key.
        Uses hidden ordinal key suffix for insertion ordering.
        The suffix is appended and stripped transparently.

        Returns:
            result (bool): True if values were deleted at key. False otherwise
                if no values at key

        Parameters:
            db (lmdb._Database): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
        """
        result = False
        with self.env.begin(db=sdb, write=True, buffers=True) as txn:
            iokey = self.suffix(key, 0, sep=sep)  # start at zeroth value for key
            cursor = txn.cursor()
            if cursor.set_range(iokey):  # move to val at key >= iokey if any
                iokey, cval = cursor.item()
                while iokey:  # end of database iokey == b'' cant internext.
                    ckey, cion = self.unsuffix(iokey, sep=sep)
                    if ckey != key:  # past key
                        break
                    result = cursor.delete() or result  # delete moves cursor to next item
                    iokey, cval = cursor.item()  # cursor now at next item after deleted
            return result


    def delIoSetVal(self, sdb, key, val, *, sep=b'.'):
        """Deletes matching val at apparent effective key if exists.
        Uses hidden ordinal key suffix for insertion ordering.
        The suffix is appended and stripped transparently.

        Because the insertion order of val is not provided must perform a linear
        search over set of values.

        Another problem is that vals may get added and deleted in any order so
        the max suffix ion may creep up over time. The suffix ordinal max > 2**16
        is an impossibly large number, however, so the suffix will not max out
        practically.But its not the most elegant solution.

        In some cases a better approach would be to use getIoSetItemsIter which
        returns the actual iokey not the apparent effetive key so can delete
        using the iokey without searching for the value. This is most applicable
        when processing escrows where all the escrowed items are processed linearly
        and one needs to delete some of them in stride with their processing.

        Returns:
            result (bool): True if val was deleted at key. False otherwise
                if val not found at key

        Parameters:
            db (lmdb._Database): instance of named sub db with dupsort==False
            key (bytes): Apparent effective key
            val (bytes): value to delete
        """
        with self.env.begin(db=sdb, write=True, buffers=True) as txn:
            iokey = self.suffix(key, 0, sep=sep)  # start zeroth value for key
            cursor = txn.cursor()
            if cursor.set_range(iokey):  # move to val at key >= iokey if any
                for iokey, cval in cursor.iternext():  # get iokey, val at cursor
                    ckey, cion = self.unsuffix(iokey, sep=sep)
                    if ckey != key:  # prev entry if any was the last entry for key
                        break  # done
                    if val == cval:
                        return cursor.delete()  # delete also moves to next so doubly moved
            return False


    def getTopIoSetItemIter(self, sdb, top=b'', *, sep=b'.'):
        """Gets Iterator of all values in branch rooted at top key
        The suffix is appended and stripped transparently.

        Returns:
            items (Iterator[(key,val)]): iterator of tuples (key, val) where
                key is apparent key with hidden insertion ordering suffixe removed
                from effective key. Iterates over top branch of insertion
                ordered set values where each effective key has trailing hidden
                suffix of serialization of insertion ordering ordinal.

            Uses hidden ordinal key suffix for insertion ordering.

        Raises StopIteration Error when empty.

        Parameters:
            db (lmdb._Database): instance of named sub db with dupsort==False
            top (bytes): top key in db. When top is empty then every item in db.
            sep (bytes): sep character for attached io suffix
        """
        for iokey, val in self.getTopItemIter(sdb=sdb, top=top):
            key, ion = self.unsuffix(iokey, sep=sep)
            yield (key, val)


@contextmanager
def openDuror(*, cls=None, name="test", temp=True, **kwa):
    """Context manager wrapper for Duror instances.
    Defaults to temporary databases.
    Context 'with' statements call .close on exit of 'with' block

    Parameters:
        cls (Type[Duror]): Class (subclass) defaults to Duror when None
        name (str):  of Duror dirPath so can have multiple holders
             that each use different dirPath name
        temp (bool):  True means open in temporary directory, clear on close
                    Otherwise open in persistent directory, do not clear on close

    Usage:

    with openHolder(name="gen1") as baser1:
        baser1.env  ....

    with openHolder(name="gen2, cls=Baser)

    """
    duror = None
    if cls is None:
        cls = Duror
    try:
        duror = cls(name=name, temp=temp, reopen=True, **kwa)
        yield duror

    finally:
        if duror:
            duror.close(clear=duror.temp)  # clears if lmdber.temp



class DurorDoer(Doer):
    """Duror Doer

    Attributes:
        done (bool): completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.
        duror (Duror): instance

    Inherited Properties:
        tyme (float): relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        tymth (func): closure returned by Tymist .tymeth() method.
            When .tymth is called it returns associated Tymist .tyme.
            .tymth provides injected dependency on Tymist tyme base.
        tock (float)): desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    """

    def __init__(self, duror, **kwa):
        """Init instance

        Inherited Parameters:
           tymist (Tymist): instance
           tock (float): initial value of .tock in seconds

        Parameters:
           duror (Duror): instance
        """
        super(DurorDoer, self).__init__(**kwa)
        self.duror = duror


    def enter(self, *, temp=None):
        """Do 'enter' context actions. Override in subclass. Not a generator method.
        Set up resources. Comparable to context manager enter.

        Parameters:
            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any
        """
        # inject temp into file resources here if any
        if not self.duror.opened:
            self.duror.reopen(temp=temp)


    def exit(self):
        """"""
        self.duror.close(clear=self.duror.temp)



class SuberBase():
    """Base class for Sub DBs of Duror
    Provides common methods for subclasses
    Do not instantiate but use a subclass

    Class Attribues:
        Sep (str): default separator to convert keys iterator to key bytes for db key

    Attributes:
        db (dbing.LMDBer): base LMDB db
        sdb (lmdb._Database): instance of lmdb named sub db for this Suber
        sep (str): separator for combining keys tuple of strs into key bytes
        verify (bool): True means reverify when ._des from db when applicable
                       False means do not reverify. Default False
    """
    Sep = '_'  # separator for combining key iterables

    def __init__(self, db: Duror, *,
                       subkey: str='docs.',
                       dupsort: bool=False,
                       sep: str=None,
                       verify: bool=False,
                       **kwa):
        """Parameters:
            db (dbing.LMDBer): base db
            subkey (str):  LMDB sub database key
            dupsort (bool): True means enable duplicates at each key
                               False (default) means do not enable duplicates at
                               each key
            sep (str): separator to convert keys iterator to key bytes for db key
                       default is self.Sep == '.'
            verify (bool): True means reverify when ._des from db when applicable
                           False means do not reverify. Default False
        """
        super(SuberBase, self).__init__()  # for multi inheritance
        self.db = db
        self.sdb = self.db.env.open_db(key=subkey.encode("utf-8"), dupsort=dupsort)
        self.sep = sep if sep is not None else self.Sep
        self.verify = True if verify else False



    def _tokey(self, keys: str|bytes|memoryview|Iterable[str|bytes|memoryview],
                topive: bool=False):
        """Converts keys to key bytes with proper separators and returns key bytes.
        If keys is already str or bytes or memoryview then returns key bytes.
        Else If keys is iterable (non-str) of strs or bytes then joins with
        separator converts to key bytes and returns. When keys is iterable and
        topive is True then enables partial key from top branch of key space given
        by partial keys by appending separator to end of partial key

        Returns:
           key (bytes): each element of keys is joined by .sep. If topive then
                        last char of key is .sep

        Parameters:
           keys (str | bytes | memoryview | Iterable[str | bytes]): db key or
                        Iterable of (str | bytes) to form key.
           topive (bool): True means treat as partial key tuple from top branch of
                       key space given by partial keys. Resultant key ends in .sep
                       character.
                       False means treat as full branch in key space. Resultant key
                       does not end in .sep character.
                       When last item in keys is empty str then will treat as
                       partial ending in sep regardless of topive value

        """
        if hasattr(keys, "encode"):  # str
            return keys.encode("utf-8")
        if isinstance(keys, memoryview):  # memoryview of bytes
            return bytes(keys)  # return bytes
        elif hasattr(keys, "decode"): # bytes
            return keys
        if topive and keys[-1]:  # topive and keys is not already partial
            keys = tuple(keys) + ('',)  # cat empty str so join adds trailing sep
        return (self.sep.join(key.decode() if hasattr(key, "decode") else key
                              for key in keys).encode())


    def _tokeys(self, key: str | bytes | memoryview):
        """Converts key bytes to keys tuple of strs by decoding and then splitting
        at separator .sep.

        Returns:
           keys (tuple[str]): makes tuple by splitting key at sep

        Parameters:
           key (str | bytes | memoryview): db key.

        """
        if isinstance(key, memoryview):  # memoryview of bytes
            key = bytes(key)
        if hasattr(key, "decode"):  # bytes
            key = key.decode()  # convert to str
        return tuple(key.split(self.sep))


    def _ser(self, val: str|bytes|memoryview):
        """
        Serialize value to bytes to store in db
        Parameters:
            val (str | bytes | memoryview): encodable as bytes
        """
        if isinstance(val, memoryview):  # memoryview is always bytes
            val = bytes(val)  # return bytes
        return (val.encode() if hasattr(val, "encode") else val)


    def _des(self, val: bytes|memoryview):
        """Deserialize val to str
        Parameters:
            val (bytes | memoryview): decodable as str
        """
        if isinstance(val, memoryview):  # memoryview is always bytes
            val = bytes(val)  # convert to bytes
        return (val.decode() if hasattr(val, "decode") else val)


    def trim(self, keys: str|bytes|memoryview|Iterable=b"", *, topive=False):
        """Removes all entries whose keys startswith keys. Enables removal of whole
        branches of db key space. To ensure that proper separation of a branch
        include empty string as last key in keys. For example ("a","") deletes
        'a.1'and 'a.2' but not 'ab'

        Parameters:
            keys (Iteratabke[str | bytes | memoryview]): of key parts that may be
                a truncation of a full keys tuple in  in order to address all the
                items from multiple branches of the key space.
                If keys is empty then trims all items in database.
                Either append "" to end of keys Iterable to ensure get properly
                separated top branch key or use top=True.

            topive (bool): True means treat as partial key tuple from top branch of
                       key space given by partial keys. Resultant key ends in .sep
                       character.
                       False means treat as full branch in key space. Resultant key
                       does not end in .sep character.
                       When last item in keys is empty str then will treat as
                       partial ending in sep regardless of top value


        Returns:
           result (bool): True if val at key exists so delete successful. False otherwise
        """
        return(self.db.delTopVals(sdb=self.sdb, top=self._tokey(keys, topive=topive)))


    def getFullItemIter(self, keys: str|bytes|memoryview|Iterable[str|bytes]="",
                       *, topive=False):
        """Iterator over items in .db that returns full items with subclass
        specific special hidden parts shown for debugging or testing.

        Returns:
            items (Iterator[tuple[key,val]]): (key, val) tuples of each item
            over the all the items in subdb whose key startswith key made from
            keys. Keys may be keyspace prefix to return branches of key space.
            When keys is empty then returns all items in subdb.
            This is meant to return full parts of items in both keyspace and
            valuespace which may be useful in debugging or testing.

        Parameters:
            keys (str|bytes|memoryview|Iteratable[str | bytes | memoryview]):
                of key parts that may be
                a truncation of a full keys tuple in  in order to address all the
                items from multiple branches of the key space.
                If keys is empty then gets all items in database.
                Either append "" to end of keys Iterable to ensure get properly
                separated top branch key or use top=True.
                In Python str.startswith('') always returns True so if branch
                key is empty string it matches all keys in db with startswith.


            topive (bool): True means treat as partial key tuple from top branch of
                       key space given by partial keys. Resultant key ends in .sep
                       character.
                       False means treat as full branch in key space. Resultant key
                       does not end in .sep character.
                       When last item in keys is empty str then will treat as
                       partial ending in sep regardless of top value

        """
        for key, val in self.db.getTopItemIter(sdb=self.sdb,
                                               top=self._tokey(keys, topive=topive)):
            yield (self._tokeys(key), self._des(val))


    def getItemIter(self, keys: str|bytes|memoryview|Iterable="",
                       *, topive=False):
        """Iterator over items in .db subclasses that do special hidden transforms
        on either the keyspace or valuespace should override this method to hide
        hidden parts from the returned items. For example, adding either
        a hidden key space suffix or hidden val space proem to ensure insertion
        order. Use getFullItemIter instead to return full items with hidden parts
        shown for debugging or testing.

        Returns:
            items (Iterator[tuple[key,val]]): (key, val) tuples of each item
            over the all the items in subdb whose key startswith key made from
            keys. Keys may be keyspace prefix to return branches of key space.
            When keys is empty then returns all items in subdb



        Parameters:
            keys (str|bytes|memoryview|Iterable[str|bytes|memoryview]): of key
                parts that may be
                a truncation of a full keys tuple in  in order to address all the
                items from multiple branches of the key space.
                If keys is empty then gets all items in database.
                Either append "" to end of keys Iterable to ensure get properly
                separated top branch key or use top=True.
                In Python str.startswith('') always returns True so if branch
                key is empty string it matches all keys in db with startswith.


            topive (bool): True means treat as partial key tuple from top branch of
                key space given by partial keys. Resultant key ends in .sep
                character.
                False means treat as full branch in key space. Resultant key
                does not end in .sep character.
                When last item in keys is empty str then will treat as
                partial ending in sep regardless of top value

        """
        for key, val in self.db.getTopItemIter(sdb=self.sdb,
                                               top=self._tokey(keys, topive=topive)):
            yield (self._tokeys(key), self._des(val))

    def cntAll(self):
        """Counts all entries in subdb self.sdb

        Returns:
            count (int): all entries in .sdb
        """
        return self.db.cntVals(sdb=self.sdb)



class Suber(SuberBase):
    """Subclass of SuberBase with no LMDB duplicates (i.e. multiple values at same key).

    Inherited Class Attribues:
        Sep (str): default separator to convert keys iterator to key bytes for db key

    Inherited Attributes:
        db (dbing.LMDBer): base LMDB db
        sdb (lmdb._Database): instance of lmdb named sub db for this Suber
        sep (str): separator for combining keys tuple of strs into key bytes
        verify (bool): True means reverify when ._des from db when applicable
                       False means do not reverify. Default False

    """

    def __init__(self, db: Duror, *,
                       subkey: str = 'docs.',
                       dupsort: bool=False, **kwa):
        """
        Inherited Parameters:
            db (dbing.LMDBer): base db
            subkey (str):  LMDB sub database key
            dupsort (bool): True means enable duplicates at each key
                               False (default) means do not enable duplicates at
                               each key. Set to False
            sep (str): separator to convert keys iterator to key bytes for db key
                       default is self.Sep == '.'
            verify (bool): True means reverify when ._des from db when applicable
                           False means do not reverify. Default False

        Parameters:
            db (dbing.LMDBer): base db
            subkey (str):  LMDB sub database key
        """
        super(Suber, self).__init__(db=db, subkey=subkey, dupsort=False, **kwa)


    def put(self, keys: str|bytes|memoryview|Iterable[str|bytes|memoryview],
                  val: bytes|str|memoryview):
        """
        Puts val at key made from keys. Does not overwrite

        Parameters:
            keys (str|bytes|memoryview|Iterable[str|bytes|memoryview]): of key
                                      strs to be combined in order to form key
            val (bytes|str|memoryview): value from ._ser

        Returns:
            result (bool): True If successful, False otherwise, such as key
                              already in database.
        """
        return (self.db.putVal(sdb=self.sdb,
                               key=self._tokey(keys),
                               val=self._ser(val)))


    def pin(self, keys: str|bytes|memoryview|Iterable[str|bytes|memoryview],
                  val: bytes|str|memoryview):
        """
        Pins (sets) val at key made from keys. Overwrites.

        Parameters:
            keys (str|bytes|memoryview|Iterable[str|bytes|memoryview]): of key
                                      strs to be combined in order to form key
            val (bytes|str|memoryview): value from ._ser

        Returns:
            result (bool): True If successful. False otherwise.
        """
        return (self.db.setVal(sdb=self.sdb,
                               key=self._tokey(keys),
                               val=self._ser(val)))


    def get(self, keys:  str|bytes|memoryview|Iterable[str|bytes|memoryview]):
        """
        Gets val at keys

        Parameters:
            keys ( str|bytes|memoryview|Iterable[str|bytes|memoryview]): of key
                                       strs to be combined in order to form key

        Returns:
            data (str): decoded as utf-8 or whatever ._des provides
            None if no entry at keys

        Usage:
            Use walrus operator to catch and raise missing entry
            if (data := mydb.get(keys)) is None:
                raise ExceptionHere
            use data here

        """
        val = self.db.getVal(sdb=self.sdb, key=self._tokey(keys))
        return (self._des(val) if val is not None else None)


    def rem(self, keys:  str|bytes|memoryview|Iterable[str|bytes|memoryview]):
        """
        Removes entry at keys

        Parameters:
            keys ( str|bytes|memoryview|Iterable[str|bytes|memoryview]): of key
                                       strs to be combined in order to form key

        Returns:
           result (bool): True if key exists so delete successful. False otherwise
        """
        return(self.db.delVal(sdb=self.sdb, key=self._tokey(keys)))






class IoSetSuber(SuberBase):
    """Insertion Ordered Set Suber factory class that supports
    a set of distinct entries at a given effective database key but with
    dupsort==False. Effective data model is that there are multiple values in a
    set of values where every member of the set has the same key (duplicate key).
    The set of values is an ordered set using insertion order. Any given value
    may appear only once in the set (not a list).

    This works similarly to the IO value duplicates for the LMDBer class with a
    sub db  of LMDB (dupsort==True) but without its size limitation of 511 bytes
    for each value when dupsort==True.
    Here the key is augmented with a hidden numbered suffix that provides a
    an ordered set of values at each effective key (duplicate key). The suffix
    is appended and stripped transparently. The set of multiple items with
    duplicate keys are retrieved in insertion order when iterating or as a list
    of the set elements.

    Inherited Class Attribues:
        Sep (str): default separator to convert keys iterator to key bytes for db key

    ClassAttributes:
        IonSep (str): default separator to suffix insertion order ordinal number

    Inherited Attributes:
        db (dbing.LMDBer): base LMDB db
        sdb (lmdb._Database): instance of lmdb named sub db for this Suber
        sep (str): separator for combining keys tuple of strs into key bytes
        verify (bool): True means reverify when ._des from db when applicable
                       False means do not reverify. Default False

    Attributes
        ionsep (str): separator to suffix insertion order ordinal number
                       default is self.IonSep == '.'
    """
    IonSep = '.'  # separator for suffixing insertion order ordinal number

    def __init__(self, db: dbing.LMDBer, *,
                       subkey: str='docs.',
                       dupsort: bool=False,
                       ionsep: str=None, **kwa):
        """
        Inherited Parameters:
            db (dbing.LMDBer): base db
            subkey (str):  LMDB sub database key
            dupsort (bool): True means enable duplicates at each key
                               False (default) means do not enable duplicates at
                               each key
            sep (str): separator to convert keys iterator to key bytes for db key
                       default is self.Sep == '.'
            verify (bool): True means reverify when ._des from db when applicable
                           False means do not reverify. Default False

        Parameters:
            ionsep (str|None): separator to suffix insertion order ordinal number
                       default is self.IonSep == '.'
        """
        super(IoSetSuber, self).__init__(db=db, subkey=subkey, dupsort=False, **kwa)
        self.ionsep = ionsep if ionsep is not None else self.IonSep


    def put(self, keys: str | bytes | memoryview | Iterable,
                  vals: str | bytes | memoryview | Iterable):
        """
        Puts all vals at effective key made from keys and hidden ordinal suffix.
        that are not already in set of vals at key. Does not overwrite.

        Parameters:
            keys (str | bytes | memoryview | Iterable): of key parts to be
                    combined in order to form key
            vals (str | bytes | memoryview | Iterable): of str serializations

        Returns:
            result (bool): True If successful, False otherwise.

        """
        if not isNonStringIterable(vals):  # not iterable
            vals = (vals, )  # make iterable
        return (self.db.putIoSetVals(sdb=self.sdb,
                                     key=self._tokey(keys),
                                     vals=[self._ser(val) for val in vals],
                                     sep=self.ionsep))


    def add(self, keys: str | bytes | memoryview | Iterable,
            val: str | bytes | memoryview):
        """
        Add val idempotently to vals at effective key made from keys and hidden
        ordinal suffix. Idempotent means that added value is not already in set
        of vals at key. Does not overwrite or add same value at same key more
        than once.

        Parameters:
            keys (str | bytes | memoryview | Iterable): of key parts to be
                    combined in order to form key
            val (str | bytes | memoryview): serialization

        Returns:
            result (bool): True means unique value added among duplications,
                            False means duplicate of same value already exists.

        """
        return (self.db.addIoSetVal(sdb=self.sdb,
                                    key=self._tokey(keys),
                                    val=self._ser(val),
                                    sep=self.ionsep))


    def pin(self, keys: str | bytes | memoryview | Iterable,
                  vals: str | bytes | memoryview | Iterable):
        """
        Pins (sets) vals at effective key made from keys and hidden ordinal suffix.
        Overwrites. Removes all pre-existing vals that share same effective keys
        and replaces them with vals

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key
            vals (Iterable): str serializations

        Returns:
            result (bool): True If successful, False otherwise.

        """
        if not isNonStringIterable(vals):  # not iterable
            vals = (vals, )  # make iterable
        return (self.db.setIoSetVals(sdb=self.sdb,
                                     key=self._tokey(keys),
                                     vals=[self._ser(val) for val in vals],
                                     sep=self.ionsep))


    def get(self, keys: str | bytes | memoryview | Iterable):
        """
        Gets vals set list at key made from effective keys

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key

        Returns:
            vals (Iterable):  each item in list is str
                          empty list if no entry at keys

        """
        return ([self._des(val) for val in
                    self.db.getIoSetValsIter(sdb=self.sdb,
                                             key=self._tokey(keys),
                                             sep=self.ionsep)])


    def getIter(self, keys: str | bytes | memoryview | Iterable):
        """
        Gets vals iterator at effecive key made from keys and hidden ordinal suffix.
        All vals in set of vals that share same effecive key are retrieved in
        insertion order.

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key

        Returns:
            vals (Iterator):  str values. Raises StopIteration when done

        """
        for val in self.db.getIoSetValsIter(sdb=self.sdb,
                                            key=self._tokey(keys),
                                            sep=self.ionsep):
            yield self._des(val)


    def getLast(self, keys: str | bytes | memoryview | Iterable):
        """
        Gets last val inserted at effecive key made from keys and hidden ordinal
        suffix.

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key

        Returns:
            val (str):  value str, None if no entry at keys

        """
        val = self.db.getIoSetValLast(sdb=self.sdb, key=self._tokey(keys))
        return (self._des(val) if val is not None else val)



    def rem(self, keys: str | bytes | memoryview | Iterable,
                   val: str | bytes | memoryview = b''):
        """
        Removes entry at effective key made from keys and hidden ordinal suffix
        that matches val if any. Otherwise deletes all values at effective key.

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key
            val (str):  value at key to delete. Subclass ._ser method may
                        accept different value types
                        if val is empty then remove all values at key

        Returns:
           result (bool): True if effective key with val exists so rem successful.
                           False otherwise

        """
        if val:
            return self.db.delIoSetVal(sdb=self.sdb,
                                       key=self._tokey(keys),
                                       val=self._ser(val),
                                       sep=self.ionsep)
        else:
            return self.db.delIoSetVals(sdb=self.sdb,
                                       key=self._tokey(keys),
                                       sep=self.ionsep)


    def cnt(self, keys: str | bytes | memoryview | Iterable):
        """
        Return count of  values at effective key made from keys and hidden ordinal
        suffix. Zero otherwise

        Parameters:
            keys (Iterable): of key strs to be combined in order to form key
        """
        return (self.db.cntIoSetVals(sdb=self.sdb,
                                     key=self._tokey(keys),
                                     sep=self.ionsep))


    def getItemIter(self, keys: str | bytes | memoryview | Iterable = "",
                    *, topive=False):
        """
        Return iterator over all the items in top branch defined by keys where
        keys may be truncation of full branch.

        Returns:
            items (Iterator): of (key, val) tuples over the all the items in
            subdb whose effective key startswith key made from keys.
            Keys may be keyspace prefix in order to return branches of key space.
            When keys is empty then returns all items in subdb.
            Returned key in each item has ordinal suffix removed.

        Parameters:
            keys (Iterable): tuple of bytes or strs that may be a truncation of
                a full keys tuple in  in order to address all the items from
                multiple branches of the key space. If keys is empty then gets
                all items in database.
                Either append "" to end of keys Iterable to ensure get properly
                separated top branch key or use top=True.
                In Python str.startswith('') always returns True so if branch
                key is empty string it matches all keys in db with startswith.

            topive (bool): True means treat as partial key tuple from top branch of
                key space given by partial keys. Resultant key ends in .sep
                character.
                False means treat as full branch in key space. Resultant key
                does not end in .sep character.
                When last item in keys is empty str then will treat as
                partial ending in sep regardless of top value

        """
        for key, val in self.db.getTopIoSetItemIter(sdb=self.sdb,
                top=self._tokey(keys, topive=topive), sep=self.ionsep):
            yield (self._tokeys(key), self._des(val))



class DomSuberBase(SuberBase):
    """Subclass of Suber with values that are serialized RegDom subclasses.

    forces .sep to '_'
    changes ._ser and ._des methods to serialize RegDom subclasses for db
    with default prosep for class name proem from json body is `\n`

    Adds type of Dom as proem to value which is stripped off when deserializing
    type of Dom need to get it from value as class name
    need Can class registry so can look up class by name

    Inherited Class Attribues:
        Sep (str): default separator to convert keys iterator to key bytes for db key

    Inherited Attributes:
        db (dbing.LMDBer): base LMDB db
        sdb (lmdb._Database): instance of lmdb named sub db for this Suber
        sep (str): separator for combining keys tuple of strs into key bytes
        verify (bool): True means reverify when ._des from db when applicable
                       False means do not reverify. Default False

    ClassAttributes:
        ProSep (str): separator class name proem to serialized RegDom instance

    Attributes
        prosep (str): separator class name proem to serialized RegDom instance
                      default is self.ProSep == '\n'

    """
    ProSep = '\n'  # separator class name proem to serialized RegDom instance

    def __init__(self, db: Duror, *, subkey: str = 'bags.', sep='_', prosep=None,
                 **kwa):
        """
        Inherited Parameters:
            db (Duror): base db
            subkey (str):  LMDB sub database key
            dupsort (bool): True means enable duplicates at each key
                               False (default) means do not enable duplicates at
                               each key. Set to False
            sep (str): separator to convert keys iterator to key bytes for db key
                       default is self.Sep == '.'
            verify (bool): True means reverify when ._des from db when applicable
                           False means do not reverify. Default False

        Parameters:
            prosep (str|None): separator class name proem to serialized RegDom instance
                               default is self.ProSep == '\n'
        """
        super(DomSuberBase, self).__init__(db=db, subkey=subkey, sep=sep, **kwa)
        self.prosep = prosep if prosep is not None else self.ProSep


    def _ser(self, val: RegDom):
        """Serialize value to json bytes to store in db with proem that is
        class name. Must be in registry. Uses b'\n' as separator between
        proem class name and json serialization of val

        Parameters:
            val (RegDom): encodable as bytes json
        """
        try:
            klas = val._registry[val.__class__.__name__]
        except (KeyError, AttributeError) as ex:
            raise HierError(f"Unregistered subclass instance={val}") from ex

        return (klas.__name__.encode() + self.prosep.encode() + val._asjson())


    def _des(self, val: bytes|memoryview):
        """Deserialize val to RegDom subclass instance as given by proem
        prepended to json serialization of RegDom subclass instance
        Uses b'\n' as separator between proem class name and json serialization
        of val

        Parameters:
            val (bytes|memoryview): proem\njson

        Returns:
            dom (RegDom): instance of RegDom subclass as registered under proem

        """
        if isinstance(val, memoryview):  # memoryview is always bytes
            val = bytes(val)  # convert to bytes

        proem, ser = val.split(sep=self.prosep.encode(), maxsplit=1)
        proem = proem.decode()
        try:
            klas = RegDom._registry[proem]
        except KeyError as ex:
            raise HierError(f"Unregistered serialized subclass={proem}") from ex

        return (klas._fromjson(ser))


class DomSuber(DomSuberBase, Suber):
    """Subclass of (DomSuberBase, Suber) with values that are serialized CanDom
    subclasses.

    forces .sep to '_'
    forces .prosep to '\n'

    Adds type of Dom as proem to value which is stripped off when deserializing
    type of Dom need to get it from value as class name
    need Can class registry so can look up class by name

    """

    def __init__(self, db: Duror, *, subkey: str = 'cans.', sep='_', prosep='\n',
                 **kwa):
        """
        Inherited Parameters:
            db (Duror): base db
            subkey (str):  LMDB sub database key
            dupsort (bool): True means enable duplicates at each key
                               False (default) means do not enable duplicates at
                               each key. Set to False
            sep (str): separator to convert keys iterator to key bytes for db key
                       default is self.Sep == '.'
            verify (bool): True means reverify when ._des from db when applicable
                           False means do not reverify. Default False
            prosep (str|None): separator class name proem to serialized CanDom instance
                               default is self.ProSep == '\n'


        """
        super(DomSuber, self).__init__(db=db, subkey=subkey,
                                       sep=sep, prosep=prosep, **kwa)


    #def _ser(self, val: RegDom):
        #"""Serialize value to json bytes to store in db with proem that is
        #class name. Must be in registry. Uses b'\n' as separator between
        #proem class name and json serialization of val

        #Parameters:
            #val (RegDom): encodable as bytes json
        #"""
        #if not isinstance(val, RegDom):
            #raise HierError(f"Expected instance of RegDom got {val}")

        #return super(DomSuber, self)._ser(val=val)



    #def _des(self, val: bytes|memoryview):
        #"""Deserialize val to RegDom subclass instance as given by proem
        #prepended to json serialization of CanDom subclass instance
        #Uses b'\n' as separator between proem class name and json serialization
        #of val

        #Parameters:
            #val (bytes|memoryview): proem\njson

        #Returns:
            #dom (RegDom): instance as registered under proem

        #"""
        #return (super(DomSuber, self)._des(val=val))


class DomIoSetSuber(DomSuberBase, IoSetSuber):
    """Subclass of (DomSuberBase, IoSetSuber) with values that are serialized
    TymeDom subclasses.

    forces .ser to '_'
    changes ._ser and ._des methods to serialize RegDom subclasses for db

    Adds type of Dom as proem to value which is stripped off when deserializing
    type of Dom need to get it from value as class name
    need Bag class registry so can look up Klas by name

    """

    def __init__(self, db: Duror, *, subkey: str = 'cans.', sep='_', **kwa):
        """
        Inherited Parameters:
            db (Duror): base db
            subkey (str):  LMDB sub database key
            dupsort (bool): True means enable duplicates at each key
                               False (default) means do not enable duplicates at
                               each key. Set to False
            sep (str): separator to convert keys iterator to key bytes for db key
                       default is self.Sep == '.'
            verify (bool): True means reverify when ._des from db when applicable
                           False means do not reverify. Default False


        """
        super(DomIoSetSuber, self).__init__(db=db, subkey=subkey, sep=sep, **kwa)


    def _ser(self, val: str|bytes|memoryview):
        """
        Serialize value to bytes to store in db
        Parameters:
            val (str | bytes | memoryview): encodable as bytes
        """
        if isinstance(val, memoryview):  # memoryview is always bytes
            val = bytes(val)  # return bytes

        return (val.encode() if hasattr(val, "encode") else val)


    def _des(self, val: bytes|memoryview):
        """Deserialize val to str
        Parameters:
            val (bytes | memoryview): decodable as str
        """
        if isinstance(val, memoryview):  # memoryview is always bytes
            val = bytes(val)  # convert to bytes
        return (val.decode("utf-8") if hasattr(val, "decode") else val)



class Subery(Duror):
    """Subery subclass of Duror for managing subdbs of Duror for durable storage
    of action data

    ToDo:  change DomIoSetSuber

    """
    def __init__(self, **kwa):
        """
        Setup named sub databases.

        Inherited Parameters:  (see Duror)


        """
        super(Subery, self).__init__(**kwa)


    def reopen(self, **kwa):
        """Open sub databases

        Attributes:
            cans (Suber): subdb whose values are serialized Can instances
                Can is a durable Bag
            drqs (IoSetSub): subdb whose values are serialized Durq instances
                Durq is a durable Deck (deque)

        """
        super(Subery, self).reopen(**kwa)

        self.cans = DomSuber(db=self, subkey='cans.')
        self.drqs = IoSetSuber(db=self, subkey="drqs.")

        return self.env

