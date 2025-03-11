# -*- encoding: utf-8 -*-
"""
hio.core.multidoing Module

Provides multiprocessing support



"""
import os
import sys
import time
import logging
import json
import signal
import multiprocessing as mp

from collections import deque, namedtuple
from dataclasses import dataclass, astuple, asdict, field
import typing


from . import tyming
from .doing import Doist, Doer
from .. import hioing
from .. import help
from ..help import timing, helping
from ..help.helping import RawDom
from ..help import ogling

from ..help.naming import Namer
from ..core.uxd import PeerMemoer

ogler = ogling.initOgler(prefix='hio_mp', name="Boss", level=logging.ERROR)





"""Bossage (namedtuple):
BossDoer info to be injected in CrewDoer as BossDoer enter time
Fields:
   name (str | None): name of Boss for resource management
   path (str | None): UXD cmd memo path used by crew to talk to their boss
"""
Bossage = namedtuple("Bossage", "name path")

"""Loadage (namedtuple):
BossDoer info to be injected into CrewDoer .start() containing both crew doist
parms for Process target kwargs and and CrewDoer parms

Fields:
   name (str): child doist identifier for resources.
   tyme (float): child doist start tyme
   tock (float | None): child doist tock, tyme lag between runs
   real (bool): child doist True means run in real time, tyme is real time
   limit (float | None): child doist tyme limit. None means run forever
   doers (list[Doers]): child doist List of Doers
   temp (bool | None): True means use temporary file resources
   boss (Bossage | None): BossDoer  info for CrewDoer. May be filled at enter time
                      CrewDoer uses to contact BossDoer.
"""
Loadage = namedtuple("Loadage", "name tyme tock real limit doers temp boss")


"""RawDom hidden methods


    Inherited Class Methods:
        _fromdict(cls, d: dict): return dataclass converted from dict d
        _fromjson(cls, s: str|bytes): return dataclass converted from json s
        _fromcbor(cls, s: bytes): return dataclass converted from cbor s
        _frommgpk(cls, s: bytes): return dataclass converted from mgpk s

    Inherited Methods:
        __iter__(self): asdict(self)
        _asdict(self): return self converted to dict
        _asjson(self): return bytes self converted to json
        _ascbor(self): return bytes self converted to cbor
        _asmgpk(self): return bytes self converted to mgpk

"""
@dataclass
class HandDom(RawDom):
    """Configuration dataclass of CrewDoer crew hand info managed by its BossDoer
    boss.

    Attributes:
        proc (typing.Any | None): crew hand subprocess or None
        exiting (bool): True means commanded to exit but may not have exited yet
                        False means not yet commanded to exit

    """
    proc: typing.Any = None  # crew hand subprocess
    exiting: bool = False  # True means commanded to exit but may not have exited yet


@dataclass
class CrewDom(RawDom):
    """Configuration dataclass of crew subprocess Doist parameters for crew doist
    and its CrewDoer to be injected by BossDoer.
    Use this when storing configuration in database or file. Use RawDom
    serialization hidden methods:


    Attributes:
        name (str): child doist identifier for resources.
        tyme (float): child doist start tyme
        tock (float | None): child doist tock, tyme lag between runs
        real (bool): child doist True means run in real time, tyme is real time
        limit (float | None): child doist tyme limit. None means run forever
        doers (list[Doers]): child doist List of Doers
        temp (bool | None): True means use temporary file resources
        boss (Bossage | None): BossDoer  info for CrewDoer. May be filled at enter time
                                CrewDoer uses to contact BossDoer.
    """
    name: str ='child'  # unique identifier of child process and associated resources
    tyme: float = 0.0    # child doist start tyme
    tock: float | None = None  # child doist tyme lag between runs, None means ASAP
    real: bool = True  # child doist True means run in real time, tyme is real time
    limit: float | None = None  # child doist tyme limit. None mean run forever
    doers: list = field(default_factory=list)  # child doist list of doers
    temp: bool | None = False  # use temporary file resources if any
    boss: (Bossage | None) = Bossage(name=None, path=None)  # BossDoer info


@dataclass
class MemoDom(RawDom):
    """Inter Boss Crew Hand structured memo dataclass. Used for control messages
    Between Boss and Crew Doers via their .peer UXD BossMemoer or CrewMemoer.

    Attributes:
        tag (str): type of memo
        name (str): unique identifier as source of memo
        load (dict): type specific payload of memo
    """
    tag: str = 'REG'    # type of memo
    name: str ='hand'  # unique identifier of source
    load: dict = field(default_factory=dict)  # type specific payload


@dataclass
class AddrDom(RawDom):
    """Load Field Value of ACK

    Attributes:
        tag (str): type of memo being acked
        name (str): unique identifier as source of memo being acked
        addr (dict): addr of source of memo being acked
    """
    tag: str = 'REG'    # type of memo being acked
    name: str ='hand'  # unique identifier of source of ack
    addr: str = ''  # addr of source of acked memo



@dataclass
class AckDom(RawDom):
    """Inter Boss Crew Hand structured memo dataclass. Used for control messages
    Between Boss and Crew Doers via their .peer UXD BossMemoer or CrewMemoer.


    Attributes:
        tag (str): type of memo
        name (str): unique identifier as source of memo
        load (AddrDom): info of acked memo
    """
    tag: str = 'ACK'    # type of memo
    name: str ='boss'  # unique identifier of source
    load: AddrDom = field(default_factory=AddrDom)  # instance of AddrDom



class MultiDoerBase(Namer, PeerMemoer, Doer):
    """MultiDoerBase is base class for Doers in multiprocessing. Each subclass
    has support for UXD peer communications via PeerMemoer super class. As well
    as support for local logging given scope of module global ogler at enter time.

    See Namer, PeerMemoer, and Doer for inherited attributes, properties, and methods.

    Inherited Class Attributes:
        See Namer, PeerMemoer and Doer Classes

    Inherited Attributes:  (See Doer and PeerMemoer for all)
        done (bool): completion state:
                     True means completed fully. Otherwise incomplete.
                     Incompletion value may be None or False.
        opts (dict): schedulaer injects options from .opts into its .do generator
                     function as **opts parameter.
        name (str): unique identifier for this instance used to manage local resources
        temp (bool): True means logger or other file resources created by
                        .start() will use temp
                     False otherwise
        reopen (bool): True (re)open with this init
                       False not (re)open with this init but later (default)
        bc (int | None): count of transport buffers of MaxGramSize

    Attributes:
        logger (Logger | None): from module scope ogler created at enter time
                        with local resources.
        graceful (bool): indication to gracefully exit on next recur. Set by
                         .force signal handler. Must add check in .self.recur
                         if self.graceful: sys.exit()
                         True means exit on next recur
                         False otherwise.

    Inherited Properties:
        tyme (float): is float relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        tymth (closure): function wrapper closure returned by Tymist.tymen()
                        method. When .tymth is called it returns associated
                        Tymist.tyme. Provides injected dependency on Tymist
                        tyme base.
        tock (float): desired time in seconds between runs or until next run,
                 non negative, zero means run asap
        addrByName (dict): mapping between (name, address) pairs, these
            must be one-to-one so that inverse is also one-to-one
        nameByAddr (dict): mapping between (address, name) pairs, these
            must be one-to-one so that inverse is also one-to-one
        countNameAddr (int): count of entries in .addrByName


    Properties:

    Inherited Methods:
        __call__()  makes instance callable as generator function returning generator
        do() generator method that returns generator
        enter() is enter context action method
        recur() recur context action method or generator method
        clean() clean context action method
        exit() exit context method
        close() close context method
        abort() abort context method
        wind()  injects ._tymth dependency from associated Tymist to get its .tyme
        clearAllNameAddr()
        getAddr(name)
        getName(addr)
        addNameAddr(name, addr)
        remNameAddr(name=None, addr=None)
        changeAddrAtName(name=None, addr=None)
        changeNameAtAddr(addr=None, name=None)

    """

    def __init__(self, *, name='base', temp=False, reopen=False, bc=4, **kwa):
        """Initialize instance.

        Inherited Parameters:  (see Doer and PeerMemoer for all)
            name (str): unique identifier for this BossDoer boss to be used
                        to manage local resources
            temp (bool): True means logger or other file resources created by
                            .start() will use temp
                         False otherwise
            reopen (bool): True (re)open with this init
                           False not (re)open with this init but later (default)
            bc (int | None): count of transport buffers of MaxGramSize

        Parameters:


        """
        super(MultiDoerBase, self).__init__(name=name,
                                            temp=temp,
                                            reopen=reopen,
                                            bc=bc,
                                            **kwa)

        self.logger = None  # assign later from ogler in enter time/scope
        self.graceful = False  # indiction by .force signal handler to exit on next recur



    def force(self, signum, frame):  # signal handler for forced but graceful exit
        self.graceful = True  # exit gracefully in recur
        self.logger.debug("Caught signal=%d so graceful forced exit.", signum)


    def enter(self, *, temp=None):
        """Do 'enter' context.
        Set up resources. Comparable to context manager enter.
        Start processes with config from .loads
        Not a generator method.

        Parameters:
            temp (bool | None): True means use temporary file resources if any.
                                None means ignore parameter value. Use self.temp.

        Inject temp or self.temp into file resources here if any
        Doist or DoDoer winds its doers on enter

        """
        self.logger = ogler.getLogger()  # uses ogler in enter scope
        signal.signal(signal.SIGINT, self.force)  # register signal handers
        signal.signal(signal.SIGTERM, self.force) # register signal handers


    def recur(self, tyme):
        """Do 'recur' context.
        Must be overidden in subclass
        """
        if self.graceful:  # signal handler.force caught signal so exit here
            sys.exit()

        self.service()

        return False  # this  is just a default


    def dumps(self, d):
        """Returns compact JSON serialization of d suitable for .memoit.

        Parameters:
            d (dict | list): object to be serialized

        Returns:
            s (str): serialized JSON
        """
        return json.dumps(d, separators=(",", ":"),ensure_ascii=False )


class BossDoer(MultiDoerBase):
    """BossDoer spawns multiple crew hand subprocesses and injects each with
    a Doist and Doers. The boss Doists runs the BossDoer in the parent process.
    Each crew hand Doist runs a CrewDoer that coordinates with the BossDoer.

    Analogy Boss runs a Crew of Hans. The parent process has a boss Doist which
    runs a BossDoer. Each crew hand is a child process with its own crew doist
    that runs its own CrewDoer

    See MultiDoerBase for all inherited attributes, properties, and methods.

    Inherited Class Attributes:
        See MultiDoerBase Class


    Inherited Attributes:  (See MultiDoerBase Class for all)
        name (str): unique identifier for this instance
                    used to manage local resources
        logger (Logger | None): from module scope ogler created at enter time
                        with local resources.
        graceful (bool): indication to gracefully exit on next recur. Set by
                         .force signal handler. Must add check in .self.recur
                         if self.graceful: sys.exit()
                         True means exit on next recur
                         False otherwise.

    Attributes:
        loads (list[dict]): BossDoer info to be injected into CrewDoer .start()
                            containing both crew doist parmss for Process target
                            kwargs and and CrewDoer parms
                            (see Loadage._asdict() or CrewDom._asdict())
        ctx (mp.context.SpawnContext | None): context under which to spawn processes
        crew (dict): values HandDom instances keyed by name
        crewed (bool): True means all crew members have registered memo interface
                            with this boss.
                       False means not yet


    Inherited Properties:
        See MultiDoerBase Class

    Properties:

    Inherited Methods:
        See MultiDoerBase Class
    """

    def __init__(self, *, name='boss',loads=None, **kwa):
        """Initialize instance.

        Inherited Parameters:  (see Doer and PeerMemoer for all)
            name (str): unique identifier for this instance to be used
                        to manage local resources

        Parameters:
            loads (list[dict]): parameters used to spinup crew hand subprocess
                                .start(). See fields of Loadage and Bossage

        """
        super(BossDoer, self).__init__(name=name, **kwa)
        self.loads = loads if loads is not None else []
        self.ctx = mp.get_context('spawn')
        self.crew = {}  # dict of HandDom instances keyed by crew name
        self.crewed = False  # True means crew successfully registered with boss



    def enter(self, *, temp=None):
        """Do 'enter' context.
        Set up resources. Comparable to context manager enter.
        Start processes with config from .loads
        Not a generator method.

        Parameters:
            temp (bool | None): True means use temporary file resources if any.
                                None means ignore parameter value. Use self.temp.

        Inject temp or self.temp into file resources here if any

        Doist or DoDoer winds its doers on enter
        """
        super(BossDoer, self).enter(temp=temp)

        self.logger.debug("BossDoer Enter: name=%s size=%d, ppid=%d, pid=%d, "
                          "module=%s, temp=%s, ogler=%s tyme=%f.",
                          self.name, len(self.loads), os.getppid(), os.getpid(),
                          __name__, temp, ogler.name, self.tyme)

        self.reopen(temp=temp)
        self.logger.debug("Boss name=%s path=%s opened=%s.",
                    self.name, self.path, self.opened)
        boss = Bossage(name=self.name, path=self.path)  # use peer at enter

        for load in self.loads:
            name = load["name"]
            doers = load["doers"]
            if not doers or not isinstance(doers[0], CrewDoer):  # first doer must be CrewDoer
                raise hioing.MultiError(f"No crew doer for crew hand doist={name}.")

            doers[0].boss = boss  # assign boss contact info to crew doer
            doers[0].name = name  # make name of CrewDoer same as name of crew doist

            if name not in self.crew:  # ensure unique by name
                proc = self.ctx.Process(name=name,
                                         target=self.start,
                                         kwargs=load)
                dom = HandDom(proc=proc, exiting=False)
                self.crew[proc.name] = dom
                proc.start()
            else:
                raise hioing.MultiError(f"Non-unique crew hand {name=} in loads.")



    def recur(self, tyme):
        """Do 'recur' context."""
        #self.logger.debug("BossDoer Recur: name=%s, pid=%d, ogler=%s, tyme=%f.",
                          #self.name, os.getpid(), ogler.name, tyme)

        if self.graceful:  # signal handler.force caught signal so exit here
            sys.exit()

        self.service()

        if self.crewed:
            if not self.ctx.active_children():
                return True  # childred exited on their own so unforced exit

        # otherwise run forever

        return False  # incomplete recur again


    def exit(self):
        """Do 'exit' (try finally) context."""
        self.logger.debug("BossDoer Exit: name=%s, ppid=%d, pid=%d, module=%s, "
                          "ogler=%s, tyme=%f.", self.name, os.getppid(),
                          os.getpid(), __name__, ogler.name, self.tyme)

        self.close(clear=True)

        self.logger.debug("Boss name=%s path=%s opened=%s.",
                self.name, self.path, self.opened)

        for name, dom in self.crew.items():  # dom is CrewDom instance
            if dom.proc.is_alive():
                dom.proc.terminate()  # force exit with SIGTERM
                self.logger.debug("Boss name=%s pid=%d terminating hand name=%s "
                                  "pid=%d.", self.name, os.getpid(), name,
                                  dom.proc.pid)


    def cease(self):
        """Do 'cease' context."""


    def abort(self, ex):
        """Do 'abort' context."""


    def serviceRxMemos(self):
        """Service all memos in .rxms (greedy) if any

        Override in subclass to handle result(s) and put them somewhere
        """
        while self.rxms:
            memo, src, vid = self._serviceOneRxMemo()
            self.logger.debug("Boss Peer RX: name=%s rx from src=%s memo=%s.",
                                self.name, src, memo)
            memo = json.loads(memo)
            tag = memo['tag']
            if tag == "REG":
                name = memo['name']
                try:  # add to address book
                    self.addNameAddr(name=name, addr=src)
                except hioing.NamerError as ex:
                    self.changeAddrAtName(name=name, addr=src)
                # Send ACK to REG to src crew hand
                dst = src
                mack = dict(tag="ACK", name=self.name, load=dict(tag='REG', name=name, addr=src))
                mack = self.dumps(mack)
                self.memoit(mack, dst)


                if self.countNameAddr == len(self.crew):
                    self.crewed = True
                    self.logger.debug("Boss name=%s crewed=%s with size=%d at "
                                      "tyme=%f.", self.name, self.crewed,
                                      len(self.crew), self.tyme)

                    # send address book of crew hands to all crew hands
                    book = self.addrByName  # dict of (name, addr) pairs
                    mbok = dict(tag="BOK", name=self.name, load=book)
                    mbok = self.dumps(mbok)
                    for name, dom in self.crew.items():  # dom is CrewDom instance
                        if dom.proc.is_alive():
                            dst = self.getAddr(name=name)
                            self.memoit(mbok, dst)



    @staticmethod
    def start(*, name='crew', tyme=0.0, tock=None, real=True, limit=None,
               doers=None, temp=None, boss=None):
        """Process target function to spinup and run doist inside crew subprocess
        after it has been started.

        Parameters:
            name (str): unique crew hand name to be used to manage resources
            tyme (float): crew doist initial value of cycle time in seconds
            tock (float | None): crew doist tock time in seconds. None means run Asap
            real (bool): crew doist True means run in real time,
                        Otherwise run faster than real
            limit (float | None): crew doist seconds for max run time of doist.
                                  None means no limit.
            doers (iterable[Doer] | None): crew doist Doer class instances
                                   First entry must be CrewDoer
            temp (bool | None): True means use temp file resources by injection.
                                Otherwise ignore do not inject.
            boss (Bossage | None): boss info. May be filled at enter time
                                  CrewDoer uses to contact BossDoer.


        Doist must be built after process started so local tymth closure is created
        inside subprocess so that when doist winds the tyme for its doers
        the tymth closure is locally sourced.

        When run inside subprocess, this static method provides the outside
        scope for any Doist and doers that reference objects inside the
        __main__ moduleo that calls this method such as ogler.
        The subprocess gets a picked copy of these module globals. Any Doer
        inside then has access to the module globals and can update them as
        neede. In the case of ogler this means changing ogler.level, ogler.temp
        and running ogler.reopen(temp=temp) as appropriate.
        """
        logger = ogler.getLogger()  # uses ogler from subprocess scope

        logger.debug("Crew Start: name=%s, ppid=%d, pid=%s, module=%s, temp=%s, ogler=%s.",
                        name, os.getppid(), os.getpid(), __name__, temp, ogler.name)
        time.sleep(0.01)

        doist = Doist(name=name, tyme=tyme, tock=tock, real=real, limit=limit,
                      doers=doers, temp=temp)
        try:
            doist.do()

        finally:
            logger.debug("Crew End: name=%s, ppid=%d, pid=%s, module=%s, temp=%s, "
                         "ogler=%s, doist.tyme=%f.", name, os.getppid(), os.getpid(),
                         __name__, temp, ogler.name, doist.tyme)



class CrewDoer(MultiDoerBase):
    """CrewDoer runs interface between a given crew hand subprocess and its
    boss process. This must be first doer run by crew hand subprocess doist.

    See MultiDoerBase for all inherited attributes, properties, and methods.

    Inherited Class Attributes:
        See MultiDoerBase Class


    Inherited Attributes:  (See MultiDoerBase Class for all)
        name (str): unique identifier for this instance
                    used to manage local resources
        logger (Logger | None): from module scope ogler created at enter time
                        with local resources.
        graceful (bool): indication to gracefully exit on next recur. Set by
                         .force signal handler. Must add check in .self.recur
                         if self.graceful: sys.exit()
                         True means exit on next recur
                         False otherwise.

    Attributes:
        boss (Bossage | None): contact info for communicating with boss
        registered (bool): True means .path acked registered with boss memoing
                           False not yet registered


    Inherited Properties:
        See MultiDoerBase Class

    Properties:

    Inherited Methods:
        See MultiDoerBase Class

    """

    def __init__(self, *, name='crew', boss=None, **kwa):
        """Initialize instance.

        Inherited Parameters:
            name (str): unique identifier for this instance to be used
                        to manage local resources
            temp (bool): True means logger or other file resources created by

        Parameters:
            boss (Bossage): contact info for BossDoer. assigned by boss at enter


        """
        super(CrewDoer, self).__init__(name=name, **kwa)
        self.boss = boss if boss is not None else Bossage(name=None, path=None)
        self.registered = False  # True means .path acked registered with boss memoing


    def force(self, signum, frame):  # signal handler for forced but graceful exit
        self.graceful = True  # exit gracefully in recur
        self.logger.debug("Doer name=%s caught signal=%d so graceful forced exit.",
                          self.name, signum)


    def enter(self, *, temp=None):
        """Do 'enter' context.
        Set up resources. Comparable to context manager enter.
        Not a generator method.

        Parameters:
            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any

        Doist or DoDoer winds its doers on enter
        """
        super(CrewDoer, self).enter(temp=temp)

        self.logger.debug("CrewDoer Enter: hand name=%s pid=%d, temp=%s, ogler=%s, "
                          "tyme=%f.", self.name, os.getpid(), temp, ogler.name,
                          self.tyme)

        self.logger.debug("Hand name=%s Boss: name=%s path=%s.",
                            self.name, self.boss.name, self.boss.path)
        self.addNameAddr(name=self.boss.name, addr=self.boss.path)

        self.reopen(temp=temp)

        self.logger.debug("Hand name=%s path=%s opened=%s.",
                    self.name, self.path, self.opened)

        memo = dict( tag="REG", name=self.name, load={})
        memo = self.dumps(memo)
        dst = self.boss.path
        self.memoit(memo, dst)



    def recur(self, tyme):
        """Do 'recur' context."""
        self.logger.debug("CrewDoer Recur: hand name=%s, pid=%d, ogler=%s, tyme=%f.",
                          self.name, os.getpid(), ogler.name, tyme)
        if self.graceful:  # signal handler.force caught signal so exit here
            sys.exit()

        self.service()


        return False  # incomplete


    def exit(self):
        """Do 'exit' (try finally) context."""
        self.close(clear=True)

        self.logger.debug("CrewDoer Exit: hand name=%s pid=%d, ogler=%s, tyme=%f.",
                          self.name, os.getpid(), ogler.name, self.tyme)
        self.logger.debug("Hand name=%s path=%s opened=%s.",
                    self.name, self.path, self.opened)


    def cease(self):
        """Do 'cease' context."""



    def abort(self, ex):
        """Do 'abort' context."""



    def serviceRxMemos(self):
        """Service all memos in .rxms (greedy) if any

        Override in subclass to handle result(s) and put them somewhere
        """
        while self.rxms:
            memo, src, vid = self._serviceOneRxMemo()
            self.logger.debug("Hand Peer RX: name=%s rx from src=%s memo=%s.",
                                self.name, src, memo)
            memo = json.loads(memo)
            tag = memo['tag']

            if tag == "END":
                name = memo["name"]
                if name == self.boss.name and src == self.boss.path:
                    self.logger.debug("Hand name=%s exiting.", self.name)
                    self.graceful = True  # next recur graceful exit

            elif tag == "ACK":
                name = memo["name"]
                if name == self.boss.name and memo['load']['tag'] == 'REG':
                    self.registered = True
                    self.logger.debug("Hand name=%s registered with boss=%s",
                                        self.name, self.boss.name)

            elif tag == "BOK":
                name = memo["name"]
                if name == self.boss.name:
                    load = memo['load']
                    self.logger.debug("Hand name=%s got from boss=%s "
                                      "address book update of other crew"
                                      " hands if any.",
                                      self.name, self.boss.name)
                    for name, addr in load.items():
                        if name != self.name:  # don't put self in own address book
                            self.addNameAddr(name=name, addr=addr)



