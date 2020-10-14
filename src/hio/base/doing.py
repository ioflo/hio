# -*- encoding: utf-8 -*-
"""
hio.core.doing Module
"""

import enum
from collections import deque

from ..hioing import ValidationError, VersionError
from ..help.timing import MonoTimer



Ctl = enum.Enum('Control', 'ready enter recur exit abort')
Sts = enum.Enum('Status', 'readied entered recurring exited aborted')


class Tasker():
    """
    Base class for async coroutines

    Attributes:
        .cycler is Cycler instance that runs tasker
        .tick is desired time in seconds between runs, non negative, zero means asap
        .status is operational status of tasker
        .desire is desired control asked by this or other taskers
        .done is tasker completion state True or False
        .doer = generator that runs tasker

    """

    def __init__(self, cycler=None, tick=0.0):
        """
        Initialize instance.
        Parameters:

        """
        self.cycler = cycler or cycling.Cycler(tyme=0.0)
        self.tick = float(abs(time))  # desired time between runs, 0.0 means asap
        self.status = Sts.exited  # operational status of tasker
        self.desire = Ctl.exit  # desired control next time Task is iterated
        self.done = True  # tasker completion state reset on restart
        self.doer = None  # reference to generator
        self.remake()  # make generator assign to .run and advance to yield


    def remake(self):
        """
        Re-make run generator
        .send(None) same as .next()
        """
        self.doer = self.makeDoer() # make generator
        status = self.doer.send(None) # advance to first yield to allow send(cmd) on next iteration

    def do(control):
        """
        Invoke .doer with control
        """
        self.doer.send(control)


    def makeDoer(self):
        """
        Create generator to run this tasker

        Simplified state machine switch on control not state
        has less code because of defaults that just ignore control
        when it's not applicable to current status
        Status cycles:
            readied -> entered -> recurring -> exited -> readied -> ...
            readied -> entered -> recurring -> exited -> aborted -> readied -> ...

        """
        self.desire = Ctl.exit  # default what to do next time, override below
        self.status = Sts.aborted # operational status of tasker
        self.done = True

        try:
            while (True):
                control = (yield (self.status))  # accept control and yield status

                if control == Ctl.recur:
                    if self.status in (Sts.entered, Sts.recurring):
                        self.recur()
                        self.status = Sts.recurring  # stary in recurring
                        # .recur may change .desire

                    elif self.status in (Sts.readied, Sts.exited):
                        self.desire == Ctl.enter  #  auto enter on run

                elif control == Ctl.ready:
                    if self.status in (Sts.exited, Sts.aborted):
                        self.ready()
                        self.status = Sts.readied
                        self.done = False  # done state updated by .run or .stop
                        self.enter()
                        self.status = Sts.entered
                        self.recur()
                        self.status = Sts.recurring
                        self.desire = Ctl.recur  # auto enter after ready

                elif control == Ctl.enter:
                    if self.status in (Sts.readied):
                        self.done = False  # done state updated by .run or .stop
                        self.enter()
                        self.status = Sts.entered
                        self.recur()
                        self.status = Sts.recurring
                        self.desire = Ctl.recur  #  auto recur after enter

                elif control == Ctl.exit:
                    if self.status in (Sts.entered, Sts.recurring):
                        self.exit()
                        self.status = Sts.exited
                        self.desire = Ctl.exit  #  stay in exited

                elif control == Ctl.abort:  # may abort from any status.
                    if self.status in (Sts.entered, Sts.recurring):
                        self.exit(aborted=True)
                        self.status = Sts.exited
                    self.abort()  # Idempotent
                    self.status = Sts.aborted
                    self.desire = Ctl.abort

                else: # control == unknown error condition bad control
                    self.abort()  # Idempotent
                    self.status = Sts.aborted
                    self.desire = Ctl.abort
                    # so not change done because inadvertent abort
                    break #break out of while loop. this will cause stopIteration

        finally: #in case uncaught exception
            self.status = Sts.aborted
            self.desire = Ctl.abort


    def ready(self):
        """
        Placeholder, Override in sub class
        """

    def enter(self):
        """
        Placeholder, Override in sub class
        """

    def recur(self):
        """
        Placeholder, Override in sub class
        """

    def exit(self, aborted=False):
        """
        Placeholder, Override in sub class

        aborted is boolean. True means stopped on abort, Otherwise false
        """

    def abort(self):
        """
        Placeholder, Override in sub class
        Abort must be idempotent
        """

