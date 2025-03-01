# -*- encoding: utf-8 -*-
"""
hio.core.multidoing Module

Provides multiprocessing support



"""
import os
import time
import multiprocessing as mp

from collections import deque, namedtuple
from dataclasses import dataclass, astuple, asdict, field


from .. import hioing
from . import tyming
from ..help import timing, helping
from ..help.helping import RawDom
from .doing import Doist, Doer


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


def spinup(name, tyme, tock, real, limit, doers):
    """Process target function to make and run doist after child subprocess has
    been started.

    Doist must be built after process started so local tymth closure is created
    inside subprocess so that when doist winds its doers the tymth is locally found.
    """
    print(f"Child: {name=} starting.")
    print('    module name:', __name__)
    print('    parent process:', os.getppid())
    print('    process id:', os.getpid())
    time.sleep(0.01)

    doist = Doist(name=name, tock=tock, real=real, limit=limit, doers=doers)
    doist.do()

    print(f"Child: {name=} ended.")
    print('    module name:', __name__)
    print('    parent process:', os.getppid())
    print('    process id:', os.getpid())



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

    def __init__(self, loads=None, **kwa):
        """Initialize instance.


        Inherited Parameters:
            tymth (closure): injected function wrapper closure returned by
                Tymist.tymen() instance. Calling tymth() returns associated
                Tymist.tyme.
            tock (float): seconds initial value of .tock
            opts (dict): injected options into its .do generator by scheduler

        Parameters:
            loads: (list[dict]): each expanded to kwargs used to spinup a
                                 child process' doist




        """
        super(MultiDoer, self).__init__(**kwa)
        self.tots = {}
        self.ctx = mp.get_context('spawn')
        self.loads = loads if loads is not None else []
        self.count = None


    def enter(self):
        """Start processes with config from .tots"""
        self.count = 0
        for load in self.loads:
            tot = self.ctx.Process(name=load["name"],
                                     target=spinup,
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

