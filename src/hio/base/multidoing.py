# -*- encoding: utf-8 -*-
"""
hio.core.multidoing Module

Provides multiprocessing support



"""
import os
import time
import logging
import json
import multiprocessing as mp

from collections import deque, namedtuple
from dataclasses import dataclass, astuple, asdict, field


from . import tyming
from .doing import Doist, Doer
from .. import hioing
from .. import help
from ..help import timing, helping
from ..help.helping import RawDom
from ..help import ogling

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


@dataclass
class CrewDom(RawDom):
    """Configuration dataclass of crew subprocess Doist parameters for crew doist
    and its CrewDoer to be injected by BossDoer.
    Use this when storing configuration in database or file. Use RawDom
    serialization hidden methods:

    Inherited Class Methods:
        _fromdict(cls, d: dict): return dataclass converted from dict d
        __iter__(self): asdict(self)
        _asdict(self): return self converted to dict
        _asjson(self): return self converted to json
        _ascbor(self): return self converted to cbor
        _asmgpk(self): return self converted to mgpk

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


    Inherited Class Methods:
        _fromdict(cls, d: dict): return dataclass converted from dict d
        __iter__(self): asdict(self)
        _asdict(self): return self converted to dict
        _asjson(self): return self converted to json
        _ascbor(self): return self converted to cbor
        _asmgpk(self): return self converted to mgpk

    Attributes:
        name (str): unique identifier as source of memo
        kin (str): type of memo
        load (dict): type specific payload of memo
    """
    name: str ='child'  # unique identifier of source
    kin: str = 'ACK'    # type of memo
    load: dict = field(default_factory=dict)  # type specific payload


class BossDoer(Doer):
    """BossDoer spawns multiple crew hand subprocesses and injects each with
    a Doist and Doers. The boss Doists runs the BossDoer in the parent process.
    Each crew hand Doist runs a CrewDoer that coordinates with the BossDoer.

    Analogy Boss runs a Crew of Hans. The parent process has a boss Doist which
    runs a BossDoer. Each crew hand is a child process with its own crew doist
    that runs its own CrewDoer

    See Doer for inherited attributes, properties, and methods.

    Inherited Attributes:
        done (bool): completion state:
                     True means completed fully. Otherwise incomplete.
                     Incompletion value may be None or False.
        opts (dict): schedulaer injects options from .opts into its .do generator
                     function as **opts parameter.


    Inherited Properties:
        tyme (float): is float relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        tymth (closure): function wrapper closure returned by Tymist.tymen()
                        method. When .tymth is called it returns associated
                        Tymist.tyme. Provides injected dependency on Tymist
                        tyme base.
        tock (float): desired time in seconds between runs or until next run,
                 non negative, zero means run asap


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


    Attributes:
        name (str): unique identifier for this MultDoer boss
                    used to manage local resources
        peer (BossMemoer): underlying transport instance subclass of Memoer
        loads (list[dict]): BossDoer info to be injected into CrewDoer .start()
                            containing both crew doist parmss for Process target
                            kwargs and and CrewDoer parms
                            (see Loadage._asdict() or CrewDom._asdict())
        ctx (mp.context.SpawnContext | None): context under which to spawn processes
        crew (dict): values are child Process instances keyed by name



    Properties:


    """

    def __init__(self, *, name='boss', peer=None, loads=None, temp=False, **kwa):
        """Initialize instance.

        Inherited Parameters:
            tymth (closure): injected function wrapper closure returned by
                Tymist.tymen() instance. Calling tymth() returns associated
                Tymist.tyme.
            tock (float): seconds initial value of .tock
            opts (dict): injected options into its .do generator by scheduler

        Parameters:
            name (str): unique identifier for this BossDoer boss to be used
                        to manage local resources
            peer (BossMemoer | None): underlying transport instance subclass of Memoer
            loads (list[dict]): parameters used to spinup crew hand subprocess
                                .start(). See fields of Loadage and Bossage
            temp (bool): True means logger or other file resources created by
                            .start() will use temp
                         False otherwise


        """
        super(BossDoer, self).__init__(**kwa)
        self.name = name
        if not peer:
            peer = BossMemoer(name=self.name, reopen=False)  # default not opened reopen in enter
        self.peer = peer
        self.loads = loads if loads is not None else []
        self.temp = temp

        self.ctx = mp.get_context('spawn')
        self.crew = {}



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
        logger = ogler.getLogger()  # get so picks up test ogler.level
        logger.debug("BossDoer Enter: name=%s size=%d, ppid=%d, pid=%d, module=%s, temp=%s,ogler=%s.",
            self.name, len(self.loads), os.getppid(), os.getpid(), __name__, temp, ogler.name)
        self.peer.reopen(temp=temp)
        logger.debug("Boss name=%s Peer: name=%s path=%s opened=%s.",
                    self.name, self.peer.name, self.peer.path, self.peer.opened)
        boss = Bossage(name=self.peer.name, path=self.peer.path)  # use peer at enter

        for load in self.loads:
            #logger.debug("Load: %s.", load)
            name = load["name"]
            doers = load["doers"]
            if not doers or not isinstance(doers[0], CrewDoer):  # first doer must be CrewDoer
                raise hioing.MultiError(f"No crew doer for crew hand doist={name}.")

            doers[0].boss = boss  # assign boss contact info to crew doer

            if name not in self.crew:  # ensure unique by name
                hand = self.ctx.Process(name=name,
                                         target=self.start,
                                         kwargs=load)
                self.crew[hand.name] = hand
                hand.start()
            else:
                raise hioing.MultiError(f"Non-unique crew hand {name=} in loads.")


    def recur(self, tyme):
        """Do 'recur' context."""
        logger = ogler.getLogger()  # get so picks up test ogler.level
        self.peer.service()
        if not self.ctx.active_children():
            return True   # complete
        return False  # incomplete recur again


    def exit(self):
        """Do 'exit' (try finally) context."""
        logger = ogler.getLogger()
        self.peer.close(clear=True)
        logger.debug("Boss name=%s Peer: name=%s path=%s opened=%s.",
                self.name, self.peer.name, self.peer.path, self.peer.opened)
        logger.debug("BossDoer Exit: name=%s, ppid=%d, pid=%d, module=%s, ogler=%s.",
                self.name, os.getppid(), os.getpid(), __name__, ogler.name)


    def close(self):
        """Do 'close' context."""
        logger = ogler.getLogger()  # get so picks up test ogler.level


    def abort(self, ex):
        """Do 'abort' context."""
        logger = ogler.getLogger()  # get so picks up test ogler.level


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
        logger = ogler.getLogger()  # do here so picks up level inside subprocess

        logger.debug("Crew Start: name=%s, ppid=%d, pid=%s, module=%s, temp=%s, ogler=%s.",
                        name, os.getppid(), os.getpid(), __name__, temp, ogler.name)
        time.sleep(0.01)

        doist = Doist(name=name, tyme=tyme, tock=tock, real=real, limit=limit,
                      doers=doers, temp=temp)
        doist.do()

        logger.debug("Crew End: name=%s, ppid=%d, pid=%s, module=%s, temp=%s, ogler=%s.",
                        name, os.getppid(), os.getpid(), __name__, temp, ogler.name)


class CrewDoer(Doer):
    """CrewDoer runs interface between a given crew hand subprocess and its
    boss process. This must be first doer run by crew hand subprocess doist.

    Attributes:
        name (str): crew hand name for managing local resources to subprocess
        peer (CrewMemoer): underlying transport instance subclass of Memoer
        count (int): iteration counter for debugging

    """

    def __init__(self, *, name='crew', boss=Bossage(name=None, path=None),
                          peer=None, **kwa):
        """Initialize instance.

        Inherited Parameters:
            tymth (closure): injected function wrapper closure returned by
                Tymist.tymen() instance. Calling tymth() returns associated
                Tymist.tyme.
            tock (float): seconds initial value of .tock
            opts (dict): injected options into its .do generator by scheduler

        Parameters:
            name (str): unique identifier for this BossDoer boss to be used
                        to manage local resources
            boss (Bossage): contact info for BossDoer. assigned by boss at enter
            peer (CrewMemoer | None): underlying transport instance subclass of Memoer

            temp (bool): True means logger or other file resources created by
                            .start() will use temp
                         False otherwise
        """
        super(CrewDoer, self).__init__(**kwa)
        self.name = name
        self.boss = boss
        self.peer = peer if peer is not None else CrewMemoer(name=self.name, reopen=False)
        self.count = None


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
        logger = ogler.getLogger()  # get so picks up test ogler.level
        self.count = 0
        logger.debug("CrewDoer Enter: name=%s pid=%d, temp=%s, ogler=%s, count=%d.",
                    self.name, os.getpid(), temp, ogler.name, self.count)
        logger.debug("Crew name=%s Boss: name=%s path=%s.",
                            self.name, self.boss.name, self.boss.path)
        self.peer.reopen(temp=temp)
        logger.debug("Crew name=%s Peer: name=%s path=%s opened=%s.",
                    self.name, self.peer.name, self.peer.path, self.peer.opened)

        memo = dict(name=self.name, kin="REG", load={})
        memo = json.dumps(memo, separators=(",", ":"), ensure_ascii=False)
        dst = self.boss.path
        self.peer.memoit(memo, dst)


    def recur(self, tyme):
        """Do 'recur' context."""
        logger = ogler.getLogger()
        self.count += 1
        logger.debug("CrewDoer Recur: name=%s, pid=%d, ogler=%s, count=%d.",
                    self.name, os.getpid(), ogler.name, self.count)
        self.peer.service()
        if self.count > 3:
            return True  # complete
        return False  # incomplete


    def exit(self):
        """Do 'exit' (try finally) context."""
        logger = ogler.getLogger()
        self.count += 1
        self.peer.close(clear=True)
        logger.debug("Crew name=%s Peer: name=%s path=%s opened=%s.",
                    self.name, self.peer.name, self.peer.path, self.peer.opened)
        logger.debug("CrewDoer Exit: name=%s pid=%d, ogler=%s, count=%d.",
                    self.name, os.getpid(), ogler.name, self.count)

    def close(self):
        """Do 'close' context."""
        logger = ogler.getLogger()
        self.count += 1


    def abort(self, ex):
        """Do 'abort' context."""
        logger = ogler.getLogger()
        self.count += 1



class BossMemoer(PeerMemoer):
    """Class for sending memograms over UXD transport
    Mixin base classes Peer and Memoer to attain memogram over uxd transport.


    Inherited Class Attributes:
        MaxGramSize (int): absolute max gram size on tx with overhead
        See memoing.Memoer Class
        See Peer Class

    Inherited Attributes:
        See memoing.Memoer Class
        See Peer Class

    Class Attributes:

    Attributes:

    """


    def __init__(self, *, reopen=False, bc=4, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            reopen (bool): True (re)open with this init
                           False not (re)open with this init but later (default)
            bc (int | None): count of transport buffers of MaxGramSize

            See memoing.Memoer for other inherited paramters
            See Peer for other inherited paramters


        Parameters:

        """
        super(BossMemoer, self).__init__(reopen=reopen, bc=bc, **kwa)


    def serviceRxMemos(self):
        """Service all memos in .rxms (greedy) if any

        Override in subclass to handle result(s) and put them somewhere
        """
        logger = ogler.getLogger()

        while self.rxms:
            memo, src, vid = self._serviceOneRxMemo()
            logger.debug("Boss Peer RX: name=%s rx from src=%s memo=%s.",
                                self.name, src, memo)
            memo = json.loads(memo)
            if memo['kin'] == "REG":
                pass # register src path with name


            dst = src
            mack = dict(name=self.name, kin="ACK", load={})
            mack = json.dumps(mack,separators=(",", ":"),ensure_ascii=False)
            self.memoit(mack, dst)



class CrewMemoer(PeerMemoer):
    """Class for sending memograms over UXD transport
    Mixin base classes Peer and Memoer to attain memogram over uxd transport.


    Inherited Class Attributes:
        MaxGramSize (int): absolute max gram size on tx with overhead
        See memoing.Memoer Class
        See Peer Class

    Inherited Attributes:
        See memoing.Memoer Class
        See Peer Class

    Class Attributes:

    Attributes:

    """
    def __init__(self, *, reopen=False, bc=4, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            reopen (bool): True (re)open with this init
                           False not (re)open with this init but later (default)
            bc (int | None): count of transport buffers of MaxGramSize

            See memoing.Memoer for other inherited paramters
            See Peer for other inherited paramters


        Parameters:

        """
        super(CrewMemoer, self).__init__(reopen=reopen, bc=bc, **kwa)

    def serviceRxMemos(self):
        """Service all memos in .rxms (greedy) if any

        Override in subclass to handle result(s) and put them somewhere
        """
        logger = ogler.getLogger()

        while self.rxms:
            memo, src, vid = self._serviceOneRxMemo()
            logger.debug("Crew Peer RX: name=%s rx from src=%s memo=%s.",
                                self.name, src, memo)
            memo = json.loads(memo)
