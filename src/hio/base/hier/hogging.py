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
from collections import namedtuple

from ..doing import Doer
from ..filing import Filer
from .hiering import Nabes
from .acting import ActBase, register
from ...help import timing

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
        span (float): tyme span for periodic logging
        header (str): header for log file(s)
        rid (str):  universally unique run ID for given run of hog
        flushSpan (float): tyme span between flushes (flush)
        flushLast (float|None): tyme last flushed, None means not yet running
        cycleCount (int): number of cycled logs, 0 means do not cycle (count)
        cyclePaths (list[str]): paths for cycled logs
        cycleSpan (float): min tyme span for cycling logs (cycle). 0.0 means
                           cycle based on cycleHigh not tyme span. One of
                           cycleSpan or cycleHigh must be non zero
        cycleLast (float|None): tyme last cycled. None means not yet running
        cycleLow (int): minimum size in bytes required for cycling log based on
                        cycleSpan. 0 means no minimum
        cycleHigh (int): maximum size in bytes allowed for each cycled log
                         0 means no maximum. One of cycleSpan or cycleHigh must
                         be non zero
        hits (dict): hold items to log. Item label is log header tag
                      Item value is hold key that provides value to log
        marks (dict): tyme or value tuples marks of hold items logged with
                      updated or changed rule. Label is hold key.


    Hidden:
        _name (str): unique name of instance for .name property
        _iopts (dict): input-output-paramters for .act for .iops property
        _nabe (str): action nabe (context) for .act for .nabe property


    """
    ReservedTags = dict(name=True, iops=True, nabe=True, hold=True, base=True,
                 temp=True, headDirPath=True, perm=True, reopen=True,
                 clear=True, reuse=True, clean=True, filed=True,
                 extensioned=True, )


    def __init__(self, iops=None, nabe=Nabes.afdo, base="", filed=True,
                       extensioned=True, mode='a+', fext="hog", reuse=True,
                       rid=None, rule=Rules.every, span=0.0, flush=0.0,
                       count=0, cycle=0.0, low=0, high=0, hits=None, **kwa):
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
            span (float): periodic time span when rule is spanned. 0.0 means
                          every tyme
            flush (float): flush tyme span, tyme between flushes, 0.0 means
                          every tyme
            count (int): number of cycled logs, 0 means do not cycle
            cycle (float): cycle tyme span, tyme between log cycles
            low (int): minimum size in bytes required for cycling log
                       0 means no minimum
            high (int): maximum size in bytes allowed for each cycled log
                       0 means no maximum
            hits (None|dict): hold items to log. Item label is log header tag
                      Item value is hold key that provides value to log
                    None means use unreserved items in **kwa wrt .ReservedTags


        When made (created and inited) by boxer.do then have "_boxer" and
        "_box" keys in self.iops = dict(_boxer=self.name, _box=m.box.name, **iops)


        since filed it should reopen without truncating so does not overwrite
        existing log file of same name. use mode 'a+'.  Otherwise when reopening
        would need to seek to end of file as default 'r+' goes to beginning.
        Need to test reopen logic
        Always init by writing header so
        even if change logs the header demarcation allows recovery of logged
        data that includes different sets of logs.
        header should include UUID and date time stamp so even when process
        quits and restarts have known uniqueness of data. This includes matching
        up cycle sets of logs where the cycle count changes so there may be
        stale cycle logs from old bigger set but same name.
        Because each log record of data always starts with tyme as float,
        which starts with numeric characters any consumer of log file can find restart demarcations of restart
        header interior (not at start) because header starts with non numeric
        characters  This way rotating logs

        """
        if not base:
            if iops and "_boxer" in iops:  # '_boxer' in iops when made by boxer
                base = iops['_boxer']  # set base to boxer.name

        super(Hog, self).__init__(iops=iops,
                                  nabe=nabe,
                                  base=base,
                                  filed=filed,
                                  extensioned=extensioned,
                                  fext=fext,
                                  reuse=reuse,
                                  **kwa)


        self.started = False
        self.first = None
        self.last = None
        self.rule = rule
        self.span = span
        self.rid = rid
        self.stamp = '' # need to init
        self.header = ''  # need to init
        self.flushSpan = flush
        self.flushLast = None
        self.cycleCount = count
        self.cyclePaths = []  # need to init
        self.cycleSpan = cycle
        self.cycleLast = None
        self.cycleLow = low
        self.cycleHigh = high

        if hits is None:
            hits = {}
            for tag, val in kwa.items():
                if tag not in self.ReservedTags:
                    hits[tag] = val  # value is key of hold to log

        self.hits = hits
        self.marks = {}


    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input/output parms, same as self.iops. Puts **iops in
                         local scope in case act compliles exec/eval str

        When made by boxer.do then have "_boxer" and "_box" keys in self.iops
           iops = dict(_boxer=self.name, _box=m.box.name, **iops)
        """
        if not self.started:
            # using mode "a+" don't need to seek to end
            # self.file.seek(0, os.SEEK_END)  # seek to end of file
            if self.rid is None:
                self.rid = self.name + "_" + uuid.uuid1().hex  # hog id uuid for this run (not iteration)
            self.stamp = timing.nowIso8601()  # current real datetime as ISO8601 string

            self.header = (f"rid\t{self.rid}\tstamp\t{self.stamp}\trule\t{self.rule}"
                           f"\tcount\t{self.cycleCount}\n")

        return iops



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
