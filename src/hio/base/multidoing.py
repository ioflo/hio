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


logger = help.ogler.getLogger()


@dataclass
class DoistDom(RawDom):
    """Configuration dataclass to child process Doist parameters for MultiDoer

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

    def __iter__(self):
        return iter(asdict(self))



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
        ctx: (mp.context.SpawnContext | None): context under which to spawn processes
        loads: (list[dict]): each expanded to kwargs used to spinup a
                             child process' doist
        tots (dict): values are child Process instances keyed by name
        count (int): iteration count

    Properties:


    """

    def __init__(self, loads=None, temp=False, **kwa):
        """Initialize instance.


        Inherited Parameters:
            tymth (closure): injected function wrapper closure returned by
                Tymist.tymen() instance. Calling tymth() returns associated
                Tymist.tyme.
            tock (float): seconds initial value of .tock
            opts (dict): injected options into its .do generator by scheduler

        Parameters:
            loads (list[dict]): each expanded to kwargs used to spinup a
                                 child process' doist
            temp (bool): True means logger or other resources in spinup uses temp
                         False other wise

        """
        super(MultiDoer, self).__init__(**kwa)
        self.loads = loads if loads is not None else []
        self.temp = temp
        self.tots = {}
        self.ctx = mp.get_context('spawn')
        self.count = None


    def enter(self, *, temp=None):
        """Do 'enter' context actions.
        Start processes with config from .tots
        Not a generator method.
        Set up resources. Comparable to context manager enter.

        Parameters:
            temp (bool | None): True means use temporary local file resources if any
                                None means ignore parameter value use self.temp

        Doist or DoDoer winds its doers on enter

        """

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


    def close(self):
        """"""
        self.count += 1


    def abort(self, ex):
        """"""
        self.count += 1


    @staticmethod
    def spinup(name, tyme, tock, real, limit, doers, temp):
        """Process target function to make and run doist after child subprocess has
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
        ogler = ogling.initOgler(prefix='hio_multi', name="hio_multi", level=logging.DEBUG,
                                              temp=temp, reopen=True, clear=True)
        logger = ogler.getLogger()

        logger.info("Child Starting: name=%s, ppid=%d, pid=%s, module=%s.",
                                name, os.getppid(), os.getpid(), __name__)
        time.sleep(0.01)

        doist = Doist(name=name, tock=tock, real=real, limit=limit, doers=doers)
        doist.do()

        logger.info("Child Ended: name=%s, ppid=%d, pid=%s, module=%s.",
                             name, os.getppid(), os.getpid(), __name__)


