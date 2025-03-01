# -*- encoding: utf-8 -*-
"""
hio.core.multidoing Module

Provides multiprocessing support



"""
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
class LoadDom(RawDom):
    """Configuration dataclass to load up a child process of MultiDoer

    Attributes:
        name (str): identifier of child process and element of path based resources.
        doers (list[Doers]): List of Doers to be run by child process Doist
        doist (Doist): doist to run the doers in this child
        process (mp.Process): instance of process
    """
    name: str ='child'  # name of
    doers: list = field(default_factory=list)
    doist: Doist | None = None
    process: None = None



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
        tots (dict): values are child process instances keyed by name
        count (int): iteration count

    Properties:


    """

    def __init__(self, load=None, **kwa):
        """Initialize instance.


        Inherited Parameters:
            tymth (closure): injected function wrapper closure returned by
                Tymist.tymen() instance. Calling tymth() returns associated
                Tymist.tyme.
            tock (float): seconds initial value of .tock
            opts (dict): injected options into its .do generator by scheduler

        Parameters:
            load (dict[str, LoadDom] | None): LoadDom dataclass instances used to
                                        child processes to be spawned.




        """
        super(MultiDoer, self).__init__(**kwa)
        self.ctx = mp.get_context('spawn')
        self.tots = {}
        if load:
            for l in load:
                self.tots[l.name] = l
                l.doist = Doist(doers=l.doers)

        self.count = None


    def enter(self):
        """Start processes with config from .spawn"""
        self.count = 0

    def recur(self, tyme):
        """"""
        self.count += 1

        if self.count > 3:
            return True  # complete
        return False  # incomplete

    def exit(self):
        """"""
        self.count += 1


    def close(self):
        """"""
        self.count += 1


    def abort(self, ex):
        """"""
        self.count += 1

