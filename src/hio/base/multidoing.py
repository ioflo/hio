# -*- encoding: utf-8 -*-
"""
hio.core.multidoing Module

Provides multiprocessing support



"""
import time
import types
import inspect
from inspect import isgeneratorfunction
from collections import deque, namedtuple

from .. import hioing
from . import tyming
from ..help import timing, helping
from .doing import Doist, Doer


class MultiDoer(Doer):
    """
    MultiDoer spawns multiprocesses with Doists

    See Doer for inherited attributes, properties, and methods.

    Inherited Attributes:
        done (bool): completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.
        opts (dict): injected options into its .do generator by scheduler


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
       count (int): iteration count

    Properties:


    """

    def __init__(self, load=None, **kwa):
        """Initialize instance.


        """
        super(MultiDoer, self).__init__(**kwa)
        self.load = load if load is not None else dict()
        self.count = None


    def enter(self):
        """"""
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

