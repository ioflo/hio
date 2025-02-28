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
    MultiDoer spawns multiprocesses with doits


    See Doer for inherited attributes, properties, and methods.

    Attributes:
       .count is iteration count

    """

    def __init__(self, **kwa):
        """
        Initialize instance.
        """
        super(MultiDoer, self).__init__(**kwa)
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

