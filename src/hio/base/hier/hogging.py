# -*- encoding: utf-8 -*-
"""
hio.base.hier.hogging Module

Provides support for hold logging (hogging)


"""
from __future__ import annotations  # so type hints of classes get resolved later

import os
import uuid
from contextlib import contextmanager
import inspect
from collections import namedtuple, deque
from base64 import urlsafe_b64encode as encodeB64
from base64 import urlsafe_b64decode as decodeB64

from ...hioing import HierError
from ...help import timing  # import timing to pytest mock of nowIso8601 works
from ...help.helping import ocfn
from ..doing import Doer
from ..filing import Filer
from .hiering import Nabes
from .acting import ActBase, register


Ruleage = namedtuple("Rules", 'once every span update change')
Rules = Ruleage(once='once', every='every', span='span', update='update', change='change')

@register(names=('log', 'Log'))
class Hog(ActBase, Filer):
    """Hog is Act that supports metrical logging of hold items based on logging
    rules such as time period, update, or change.

    Act comes before Filer in .__mro__ so Act.name property is used not Filer.name

    Inherited Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Instances (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.

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

    Class Attributes:
        ReservedTags (dict[str]): of reserved tags to protect from collision with
                                  defined parameter names that may not be used for
                                  log tags when using **kwa to provide hold
                                  log leys. Uses dict since inclusion test is
                                  faster than with list

    Inherited Attributes  see Act, File
        hold (Hold): data shared by boxwork

        name (str): overriden by .name property from Act (see name property)
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


    Inherited Properties  see Act, File
        name (str): unique name string of instance used for registering Act
                    instance in Act registry as well providing a unique path
                    component used in file path name
        iops (dict): input-output-parameters for .act
        nabe (str): action nabe (context) for .act


    Attributes:
        started (bool): True means logging has begun with header
                        False means logging has not yet begun needs header
        first (float|None): tyme when began logging, None means not yet running
        last (float|None): tyme when last logged, None means not yet running
                      realtime equiv of last = began + (last - first)
        rule (str): condition for log to fire one of Rules
                    (once, every, span, update, change)
        span (float): tyme span seconds for periodic logging 0.0 means everytyme
        onced (bool): True means logged at least one (first) record
                      False means not yet logged one (first) record
        header (str): header for log file(s)
        rid (str):  universally unique run ID for given run of hog
        flushSpan (float): tyme span seconds between flushes (flush)
                           0.0 means everytyme
        flushForce (bool): True means force flush on every log
                               False means only flush at appropriate times
        flushLast (float|None): tyme last flushed, None means not yet running
        cycleCount (int): number of cycled logs, 0 means do not cycle (count)
        cyclePeriod (float): min tyme span for cycling logs (cycle). 0.0 means
                           cycle based on cycleHigh not tyme span. One of
                           cycleSpan or cycleHigh must be non zero
        cycleSize (int): maximum size in bytes allowed for each cycled log
                         0 means no maximum. One of cycleSpan or cycleHigh must
                         be non zero
        cyclePaths (list[str]): paths for cycled logs
        cycleLast (float|None): tyme last cycled. None means not yet running
        hits (dict): hold items to log. Item label is log header tag
                      Item value is hold key that provides value to log
        marks (dict): tyme or value tuples marks of hold items logged with
                      updated or changed rule. Label is hold key.
        activeKey (str|None): hold key to active box name of boxer given by iops
                              None otherwise
        tockKey (str|None): hold key to tock value of boxer given by iops
                            None otherwise
        tockKey (str|None): hold key to tyme value of boxer given by iops
                            None otherwise


    Hidden:
        _name (str): unique name of instance for .name property
        _iopts (dict): input-output-paramters for .act for .iops property
        _nabe (str): action nabe (context) for .act for .nabe property


    As ActBase subclass that is managed inside boxwork, the Hog is created and
    inited by Boxer.make which is run in the enter context of the BoxerDoer.
    So opening file during init is compatible as its in the enter context of the
    its Doer even though its not in the endo context of its box.
    It still needs to be closed. Unlike the hold subery the Boxer doesn't know
    about any Hogs runing as acts inside its boxes so can't close in its BoxerDoer
    exit context. So much be closed inside with a close do act

    Since filed it should reopen without truncating so does not overwrite
    existing log file of same name so uses mode = 'a+'.
    Need to test reopen logic
    Always rewrites header on first log after restart which may have changed
    log behavior so header demarcation enables recognition of log parameters.
    Log header includes rid (unique run id) and datatime stamp so can always
    uniquely match a given run data to header even when reusing same log file.
    This is most important when rotating logs.
    Because each individual log record after header always starts with tyme as
    floating point decimal, processor can find header demarcations interior to
    log file not merely at start.
    """
    ReservedTags = dict(name=True, iops=True, nabe=True, hold=True, base=True,
                 temp=True, headDirPath=True, perm=True, reopen=True,
                 clear=True, reuse=True, clean=True, filed=True,
                 extensioned=True, )

    Proem = "__"  # prepended to rid (run ID) in header to ensure 24 bit boundary alignment


    @classmethod
    def _genRid(cls):
        """Generates random universally unique hog run ID rid, not iteration

        Returns:
            rid (str): run id in 24 bit aligned Base64
        """
        ps = 2  # pad size, use unit test to ensure .Proem is at least length 2
        rid = encodeB64(bytes([0] * ps) + uuid.uuid1().bytes)[ps:] # prepad, convert, and strip
        rid = cls.Proem[:ps] + rid.decode()  # fully qualified rid with Proem
        return rid # hog run id uuid for this run (not iteration), same size as CESR salt


    def __init__(self, iops=None, nabe=Nabes.afdo, base="", filed=True,
                       extensioned=True, mode='a+', fext="hog", reuse=True,
                       rid=None, rule=Rules.every, span=0.0,
                       flushSpan=60.0, flushForce=False,
                       cycleCount=0, cycleSpan=0.0, cycleSize=0,
                       hits=None, **kwa):
        """Initialize instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index. Used for .name property which is
                 used for registering Act instance in Act registry as well
                 providing a unique path component used in file path name.
                 When system employs more than one installation, name allows
                 differentiating each installation by name
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for act. default is "endo"
            hold (None|Hold): data shared across boxwork

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
            rid (str|None):  universally unique run ID for given run of hog
                             None means create one using uuid lib
            rule (str|None): condition for log to fire, one of Rules default every
                            (once, every, span, update, change)
            span (float): periodic tyme span seconds when rule is spanned
                          0.0 means every tyme
            flushSpan (float): flush tyme span seconds, tyme between flushes
                          0.0 means every tyme
            flushForce (bool): True means force flush on every log
                               False means only flush at appropriate times
            cycleCount (int): number of cycled logs, 0 means do not cycle
            cycleSapn (float): cycle tyme span, tyme between log cycles
            cycleSize (int): maximum size in bytes allowed for each cycled log
                       0 means no maximum
            hits (None|dict): hold items to log. Item label is log header tag
                      Item value is hold key that provides value to log
                    None means use unreserved items in **kwa wrt .ReservedTags


        When made (created and inited) by boxer.do then have "_boxer" and
        "_box" keys in self.iops = dict(_boxer=self.name, _box=m.box.name, **iops)

        """
        if not base:
            if iops and "_boxer" in iops:  # '_boxer' in iops when made by boxer
                base = iops['_boxer']  # set base to boxer.name

        super(Hog, self).__init__(iops=iops,
                                  nabe=nabe,
                                  base=base,
                                  filed=filed,
                                  extensioned=extensioned,
                                  mode=mode,
                                  fext=fext,
                                  reuse=reuse,
                                  **kwa)


        self.started = False
        self.first = None
        self.last = None
        self.rule = rule  # maybe should make property so readonly after init
        self.span = span
        self.onced = False
        self.rid = rid
        self.stamp = '' # need to init
        self.header = ''  # need to init
        self.flushSpan = flushSpan
        self.flushForce = flushForce
        self.flushLast = None

        if cycleCount and cycleSpan == 0.0 and cycleSize == 0:
            raise HierError(f"For non-zero count one of {cycleSpan=} or "
                            f"{cycleSize=} must be non-zero")

        self.cycleCount = max(min(cycleCount, 999), 0)
        self.cycleSpan = cycleSpan
        self.cycleSize = cycleSize
        self.cyclePaths = []  # need to init
        self.cycleLast = None

        self.activeKey = None
        self.tockKey = None
        self.tymeKey = None
        if "_boxer" in self.iops:  # assign keys for boxer box state
            boxerName = self.iops["_boxer"]
            self.activeKey = self.hold.tokey(("", "boxer", boxerName, "active"))
            self.tockKey = self.hold.tokey(("", "boxer", boxerName, "tock"))
            self.tymeKey = self.hold.tokey(("", "boxer", boxerName, "tyme"))

        if hits is None:
            hits = {}
            for tag, val in kwa.items():
                if tag not in self.ReservedTags:
                    hits[tag] = val  # value is key of hold to log

        self.hits = hits
        self.marks = {}

        if self.cycleCount > 0:
            self.cyclePaths = []
            for k in range(1, self.cycleCount + 1):
                root, ext = os.path.splitext(self.path)
                path = f"{root}_{k:03}{ext}"  # ext includes leading dot
                self.cyclePaths.append(path)
                # trial open to ensure can make
                try:
                    file = ocfn(path, 'r')  # do not truncate in case reusing
                except OSError as ex:
                    raise HierError("Failed making cycle paths") from ex

                file.close()


    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input/output parms, same as self.iops. Puts **iops in
                         local scope in case act compliles exec/eval str

        When made by boxer.do then have "_boxer" and "_box" keys in self.iops
           iops = dict(_boxer=self.name, _box=m.box.name, **iops)
        """
        if not self.started:

            if self.rid is None:
                self.rid = self._genRid()
                ##mid = encodeB64(bytes([0] * ps) + uuid.uuid4().bytes)[ps:] # prepad, convert, and strip
                ##mid = self.code.encode() + mid  # fully qualified mid with prefix code
                ## hog id uuid for this run (not iteration)
                ## create B64 version of uuid with stripped trailing pad bytes
                #uid = encodeB64(bytes.fromhex(uuid.uuid1().hex))[:-2].decode()
                ##self.rid = self.name + "_" + uid
                #self.rid = self.Proem + uid  # same as CESR salt
            self.stamp = timing.nowIso8601()  # current real datetime as ISO8601 string

            metaLine = (f"rid\tbase\tname\tstamp\trule\tcount\n")

            metaValLine = (f"{self.rid}\t{self.base}\t{self.name}"
                           f"\t{self.stamp}\t{self.rule}\t{self.cycleCount}\n")

            if self.tymeKey and self.tymeKey in self.hold:  # need tyme for logging
                hits = dict(tyme=self.tymeKey)  # logging tyme
                for tag, key in self.hits.items():  # copy valid .hits
                    if key in self.hold:  # invalid hold key
                        hits[tag] = key  # make copy in order

            else: # need tyme in order to log anything with respect to tyme
                hits = {}  # nothing to log

            self.hits = hits

            if len(self.hits) == 1:  # only tyme so default to boxer state
                if self.activeKey and self.activeKey in self.hold:
                    self.hits["active"] = self.activeKey
                if self.tockKey and self.tockKey in self.hold:
                    self.hits["tock"] = self.tockKey

            tagKeyLine = '\t'.join(f"{tag}.key" for tag in self.hits.keys()) + "\n"
            keyLine = '\t'.join(key for key in self.hits.values()) + "\n"

            # need to expand tags for hits with vector bags in hold
            tagValLine = ('\t'.join(f"{tag}.{fld}" for tag, key in self.hits.items()
                                    for fld in self.hold[key]._names) + "\n")

            self.header = metaLine + metaValLine + tagKeyLine + keyLine + tagValLine
            self.file.write(self.header)
            self.started = True

        tyme = self.hold[self.hits["tyme"]].value if self.hits else None

        if not self.onced:
            self.first = tyme
            # always flush on first write to ensure header synced on disk
            self.log(self.record(), tyme, force=True)
            if self.hits:
                for tag, key in self.hits.items():
                    if tag != "tyme":  # do not mark tyme hold
                        if self.rule == Rules.update:  # create mark
                            self.marks[key] = self.hold[key]._tyme
                        elif self.rule == Rules.change:  # create mark
                            self.marks[key] = self.hold[key]._astuple()

            self.onced = True
        else:
            match self.rule:
                case Rules.every:
                    self.log(self.record(), tyme)
                case Rules.span:
                    if tyme is not None and tyme - self.last >= self.span:
                        self.log(self.record(), tyme)

                case Rules.update:
                    if tyme is not None:
                        updated = False
                        for key, mark in self.marks.items():  # marked tyme
                            holdTyme = self.hold[key]._tyme
                            if holdTyme > mark:  # updated since marked
                                self.marks[key] = holdTyme
                                updated = True
                        if updated:
                            self.log(self.record(), tyme)

                case Rules.change:
                    if tyme is not None:
                        changed = False
                        for key, mark in self.marks.items():  # marked value tuple
                            holdValue = self.hold[key]._astuple()
                            if holdValue != mark:  # changed since marked
                                self.marks[key] = holdValue
                                changed = True
                        if changed:
                            self.log(self.record(), tyme)

                case _:
                    pass

        return iops


    def log(self, record, tyme, force=False):
        """Write one record to file and flush when indicated

        Parameters:
            record (str):  one line of tab delimited newline ended values
            tyme (float):  tyme of log record
            force (bool): True means force flush even when not flushSpan elapsed
                          False means do not force flush only if flushSpan elapsed
        """
        self.file.write(record)
        self.last = tyme

        if force or self.flushForce or (tyme - self.flushLast) >= self.flushSpan:
            self.flush()
            self.flushLast = tyme

        if self.cycleCount:
            cycled = False
            if self.cycleSpan:
                if self.cycleLast is None:
                    delta = tyme - self.first
                else:
                    delta = tyme - self.cycleLast

                if delta >= self.cycleSpan:
                    self.cycle(tyme=tyme)
                    cycled = True

            if self.cycleSize and not cycled:
                try:
                    size = os.path.getsize(self.path)
                except OSError as ex:
                    pass
                else:
                    if size >= self.cycleSize:
                        self.cycle(tyme=tyme)


    def record(self):
        """Generate on record line .hits values from .hold

        Returns:
           record (str): one newline delimited line of tab delimited values
                         from .hits. Each hit time value is key into hold
                         vector holds each get entry in record per field


        """
        # hit values are hold keys
        if self.hits:
            return ('\t'.join(f"{self.hold[key][fld]}"
                                for key in self.hits.values()
                                    for fld in self.hold[key]._names) + "\n")
        else:
            return ""


    def cycle(self, tyme):
        """Cycle log files

        Parameters:
            tyme (float): current tyme of cycle
        """
        self.flush
        cycles = deque([self.path])
        cycles.extend(self.cyclePaths)

        cycled = False  # if cycling is successful
        new = cycles.pop()
        while cycles:
            old = cycles.pop()
            try:
                if old == self.path:
                    self.close()
                os.replace(old, new)  # rename old to new thereby clobbering old
                cycled = True
            except OSError as ex:
                cycled = False  # failed to cycle so do not clobber self.file
                break
            new = old  # old path is now free to use

        if not cycled:  # reopen cleanly just in case
            self.reopen(reuse=True)  # reopen reuse, .mode is "a+" so saves
        else:  # all cycled so recreate self.file
            self.reopen() # not reuse so recreates empty

        self.file.write(self.header)  # rewrite header
        self.flush()
        self.flushLast = tyme
        self.cycleLast = tyme


@contextmanager
def openHog(cls=None, name=None, temp=True, reopen=True, clear=False, **kwa):
    """Context manager wrapper Hog instances for managing a filesystem directory
    and or files in a directory.

    Defaults to using temporary directory path.
    Context 'with' statements call .close on exit of 'with' block

    Parameters:
        cls is Class instance of subclass instance
        name is str name of Filer instance path part so can have multiple Filers
             at different paths that each use different dirs or files
        temp is Boolean, True means open in temporary directory, clear on close
                Otherwise open in persistent directory, do not clear on close
        reopen (bool): True (re)open with this init
                           False not (re)open with this init but later (default)
        clear (bool): True means remove directory upon close when reopening
                          False means do not remove directory upon close when reopening
    See hogging.Hog for other keyword parameter passthroughs

    Usage:

    with openHog(name="bob") as hog:

    with openHog(name="eve", cls=HogSubClass) as hog:

    """
    hog = None
    if cls is None:
        cls = Hog
    try:
        hog = cls(name=name, temp=temp, reopen=reopen, clear=clear, **kwa)
        yield hog

    finally:
        if hog:
            hog.close(clear=hog.temp or clear)  # clears if hog.temp



class HogDoer(Doer):
    """
    Basic Hog Doer

    Attributes:
        done (bool): completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.
        hog (Hog): instance

    Properties:
        tyme (float): relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        tymth (func): closure returned by Tymist .tymeth() method.
            When .tymth is called it returns associated Tymist .tyme.
            .tymth provides injected dependency on Tymist tyme base.
        tock (float)): desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    """

    def __init__(self, hog, **kwa):
        """
        Parameters:
           tymist (Tymist): instance
           tock (float): initial value of .tock in seconds
           hog (Hog): instance
        """
        super(HogDoer, self).__init__(**kwa)
        self.hog = hog


    def enter(self, *, temp=None):
        """Do 'enter' context actions. Override in subclass. Not a generator method.
        Set up resources. Comparable to context manager enter.

        Parameters:
            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any
        """
        # inject temp into file resources here if any
        if not self.hog.opened:
            self.hog.reopen(temp=temp)


    def exit(self):
        """"""
        self.hog.close(clear=self.hog.temp)
