# -*- encoding: utf-8 -*-
"""
hio.core.multidoing Module

Provides multiprocessing support



"""
import os
import time
import logging
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

ogler = ogling.initOgler(prefix='hio_mp', name="boss", level=logging.DEBUG)
logger = ogler.getLogger()


@dataclass
class DoistDom(RawDom):
    """Configuration dataclass of crew subprocess Doist parameters for MultiDoer
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
    """
    name: str ='child'  # unique identifier of child process and associated resources
    tyme: float = 0.0    # child doist start tyme
    tock: float | None = None  # child doist tyme lag between runs, None means ASAP
    real: bool = True  # child doist True means run in real time, tyme is real time
    limit: float | None = None  # child doist tyme limit. None mean run forever
    doers: list = field(default_factory=list)  # child doist list of doers
    temp: bool = False  # use temporary file resources if any


class MultiDoer(Doer):
    """
    MultiDoer spawns multiprocesses with Doists

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
        ctx (mp.context.SpawnContext | None): context under which to spawn processes
        loads (list[dict]): each expanded to kwargs used to spinup a
                            crew doist in a child process
        tots (dict): values are child Process instances keyed by name


    Properties:


    """

    def __init__(self, *, name='boss', loads=None, temp=False, **kwa):
        """Initialize instance.


        Inherited Parameters:
            tymth (closure): injected function wrapper closure returned by
                Tymist.tymen() instance. Calling tymth() returns associated
                Tymist.tyme.
            tock (float): seconds initial value of .tock
            opts (dict): injected options into its .do generator by scheduler

        Parameters:
            name (str): unique identifier for this MultiDoer boss to be used
                        to manage local resources
            loads (list[dict]): each expanded to kwargs used to spinup a
                                 child process' doist
            temp (bool): True means logger or other resources in spinup uses temp
                         False other wise

        """
        super(MultiDoer, self).__init__(**kwa)
        self.name = name
        self.loads = loads if loads is not None else []
        self.temp = temp
        self.tots = {}
        self.ctx = mp.get_context('spawn')


    def enter(self, *, temp=None):
        """Do 'enter' context actions.
        Start processes with config from .tots
        Not a generator method.
        Set up resources. Comparable to context manager enter.

        Parameters:
            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any

        Doist or DoDoer winds its doers on enter

        """
        logger.info("Boss Enter: name=%s size=%d, ppid=%d, pid=%d, module=%s.",
                self.name, len(self.loads), os.getppid(), os.getpid(), __name__)
        self.count = 0
        for load in self.loads:
            tot = self.ctx.Process(name=load["name"],
                                     target=self.spinup,
                                     kwargs=load)
            self.tots[tot.name] = tot
            tot.start()


    def recur(self, tyme):
        """"""
        self.count += 1

        if not self.ctx.active_children():
            return True   # complete
        return False  # incomplete recur again

    def exit(self):
        """"""
        self.count += 1
        logger.info("Boss Exit: name=%s, ppid=%d, pid=%d, module=%s.",
                self.name, os.getppid(), os.getpid(), __name__)


    def close(self):
        """"""
        self.count += 1


    def abort(self, ex):
        """"""
        self.count += 1


    @staticmethod
    def spinup(name, tyme, tock, real, limit, doers, temp):
        """Process target function to make and run doist after crew subprocess has
        been started.

        Paramters:
            name (str): unique identifier for child doist and its resources
            tyme (float): child doist start tyme
            tock (float | None): child doist tyme lag between runs, None means ASAP
            real (bool): child doist runtime
                         True means run in real time, tyme is real time
                         False means run in faster than real time, tyme is relative
            limit (float | None): child doist tyme limit. None mean run forever
            doers (list): child doist list of doers. Do not assign tymist to doers
                          when creating.
            temp (bool): use temp resources such as file pathing

        Doist must be built after process started so local tymth closure is created
        inside subprocess so that when doist winds the tyme for its doers
        the tymth closure is locally sourced.
        """
        #When run inside subprocess ogler is a copy so can change ogler.level,
        # ogler.temp and reopen log file or pass in temp to reopen
        ogler.level = logging.INFO
        ogler.reopen(name=name, temp=temp)
        logger = ogler.getLogger()

        logger.info("Crew Start: name=%s, ppid=%d, pid=%s, module=%s.",
                                name, os.getppid(), os.getpid(), __name__)
        time.sleep(0.01)

        doist = Doist(name=name, tock=tock, real=real, limit=limit, doers=doers)
        doist.do()

        logger.info("Crew End: name=%s, ppid=%d, pid=%s, module=%s.",
                             name, os.getppid(), os.getpid(), __name__)


class CrewDoer(Doer):
    """CrewDoer runs interface between crew subprocess and its boss process.
    This must be first doer run by crew subprocess doist.

    Attributes:
        name (str): crew member name for managing local resources to subprocess

    """

    def __init__(self, *, name='crew', **kwa):
        """
        Initialize instance.
        """
        super(CrewDoer, self).__init__(**kwa)
        self.name = name
        self.count = None


    def enter(self, *, temp=None):
        """Do 'enter' context actions. Override in subclass. Not a generator method.
        Set up resources. Comparable to context manager enter.


        Parameters:
            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any

        Inject temp into file resources here if any

        Doist or DoDoer winds its doers on enter
        """
        self.count = 0
        #ogler.level = logging.INFO
        #ogler.reopen(name=self.name, temp=temp)
        logger = ogler.getLogger()
        logger.info("CrewDoer Enter: name=%s pid=%d, ogler=%s, count=%d.",
                    self.name, os.getpid(), ogler.name, self.count)



    def recur(self, tyme):
        """"""
        self.count += 1
        logger = ogler.getLogger()
        logger.info("CrewDoer Recur: name=%s, pid=%d, ogler=%s, count=%d.",
                    self.name, os.getpid(), ogler.name, self.count)
        if self.count > 3:
            return True  # complete
        return False  # incomplete

    def exit(self):
        """"""
        self.count += 1
        logger = ogler.getLogger()
        logger.info("CrewDoer Exit: name=%s pid=%d, ogler=%s, count=%d.",
                    self.name, os.getpid(), ogler.name, self.count)

    def close(self):
        """"""
        self.count += 1


    def abort(self, ex):
        """"""
        self.count += 1
