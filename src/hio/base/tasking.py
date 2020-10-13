# -*- encoding: utf-8 -*-
"""
hio.core.tasking Module
"""

import enum
from collections import deque

from ..hioing import ValidationError, VersionError
from ..help.timing import MonoTimer



Ctl = enum.Enum('Control', 'ready start run stop abort')
Sts = enum.Enum('Status', 'readied started running stopped aborted')


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
        self.cycler = cycler or tasking.Cycler(tyme=0.0)
        self.tick = float(abs(time))  # desired time between runs, 0.0 means asap
        self.status = Sts.stopped  # operational status of tasker
        self.desire = Ctl.stop  # desired control next time Task is iterated
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
            readied -> started -> running -> stopped -> started -> ...
            readied -> started -> running -> stopped -> aborted -> readied -> ...

        """
        self.desire = Ctl.stop  # default what to do next time, override below
        self.status = Sts.aborted # operational status of tasker
        self.done = True

        try:
            while (True):
                control = (yield (self.status))  # accept control and yield status

                if control == Ctl.run:
                    if self.status in (Sts.started, Sts.running):
                        self.run()
                        self.status = Sts.running
                        # .run may change .desire

                    elif self.status in (Sts.readied, Sts.stopped):
                        self.desire == Ctl.start  #  auto start on run

                elif control == Ctl.ready:  # may reready in any status
                    self.ready()
                    self.status = Sts.readied
                    self.desire = Ctl.start  # auto start on ready

                elif control == Ctl.start:  # may restart if stopped
                    if self.status in (Sts.stopped, Sts.readied):
                        self.start()
                        self.status = Sts.started
                        self.done = False  # done state updated by .run or .stop
                        self.desire = Ctl.run  #  auto run on start

                elif control == Ctl.stop:
                    if self.status in (Sts.running, Sts.started):
                        self.stop()
                        self.status = Sts.stopped
                        self.desire = Ctl.stop

                elif control == Ctl.abort:  # may abort from any status.
                    if self.status in (Sts.started, Sts.running):
                        self.stop(aborted=True)
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

    def start(self):
        """
        Placeholder, Override in sub class
        """

    def run(self):
        """
        Placeholder, Override in sub class
        """

    def stop(self, aborted=False):
        """
        Placeholder, Override in sub class

        aborted is boolean. True means stopped on abort, Otherwise false
        """

    def abort(self):
        """
        Placeholder, Override in sub class
        Abort must be idempotent
        """



class Cycler():
    """
    Cycler is nestable hierarchical time slice cycling object
    Provides relative cycle time in seconds with .tyme property and advanced
    by .tock method.
    .tyme may be artificial time or real time in seconds.

    .cycle method runs generators that are synchronized to cycle time .tyme
           cycle may run as fast as possbile or run in real time.

    Attributes:

    Properties:
        .tyme is float relative cycle time, tyme is artificial time

    """
    def __init__(self, tyme=0.0, tick=1.0, real=False, taskers=None):
        """
        Initialize instance
        Parameters:
            tyme is initial value of float cycle time in seconds
            tick is float tick time in seconds
            real is boolean True means run in real time,
                            Otherwise run faster than real
            taskers is list of Tasker instances which have generators
        """
        self.tyme = float(tyme)
        self.tick = float(tick)

        self.real = True if real else False
        self.timer = MonoTimer(duration = self.tick)
        # deque of runable generators
        self.taskers = taskers if taskers is not None else list()

    @property
    def tyme(self):
        """
        tyme property getter, get ._tyme
        .tyme is float cycle time in seconds
        """
        return self._tyme

    @tyme.setter
    def tyme(self, tyme):
        """
        cycle time property setter, set ._tyme to tyme
        """
        self._tyme = float(tyme)

    @property
    def tick(self):
        """
        tick property getter, get ._tick
        .tick is float cycle time .tyme increment in seconds
        """
        return self._tick

    @tick.setter
    def tick(self, tick):
        """
        cycle time increment property setter, set ._tick to tick
        """
        self._tick= float(tick)

    def tock(self, tick=None):
        """
        Advance cycle time .tyme by tick seconds when provided othewise by .tick
        and return new .tyme
        Parameters:
            tick is float of amount of time in seconds to change .tyme
        """
        self.tyme += float(tick if tick is not None else self.tick)
        return self.tyme

    def do(tasks):
        """
        Run the cycle as a generator.
        Allows hierachical cyclers so that scheduling is hierarchical where
        the ordering of each sub cycler is determined by its super cycler

        Parameters:
           tasks is deque of duples (tasker, retyme)
        """
        more = False #are any taskers RUNNING or STARTED

        for i in range(len(tasks)): #attempt to run each ready tasker
            tasker, retyme = tasks.popleft()  # pop it off

            if retyme <= self.tyme:  # run it now
                try:
                    status = tasker.runner.send(tasker.desire)
                    if status != ABORTED:  # tasker did not abort itself
                        tasks.append((tasker, retyme + tasker.tick))
                        # allows for tick change during run

                except StopIteration:  # returned instead of yielded
                    pass  # effectively tasker aborted itself

            else:  # not yet
                tasks.append((tasker, retyme))  # reappend it
                status = tasker.status

            if status in (Sts.running, Sts.started):
                more = True

        return (tasks, more)


    def cycle(self, taskers=None):
        """
        Prepares tasks deque from .taskers
        Each entry in tasks is duple of (tasker, retyme) where retyme is tyme in
            seconds when next should run may be real or simulated
        Each cycle runs all generators in tasks deque by calling .send on each one.
        Generators may have cycler close them with appropriate response to .send
        Cycler may then remove them from tasks
        Once tasks is empty .cycle exits.

        Keyboard interrupt (cntl-c) also forces exit.

        Since finally clause closes generators they must be reinited before then
        can be run again
        """
        if taskers is not None:
            self.taskers = taskers

        tasks = deque()
        for tasker in self.taskers:
            tasker.desire = Ctl.ready
            tasker.status = Sts.aborted
            tasks.append((tasker, self.tyme))


        self.timer.start()

        try: #so always clean up resources if exception
            while True:
                try: #CNTL-C generates keyboardInterrupt to break out of while loop

                    more = False  # are any taskers running or started

                    for i in range(len(tasks)): #attempt to run each ready tasker
                        tasker, retyme = tasks.popleft()  # pop it off

                        if retyme <= self.tyme:  # run it now
                            try:
                                status = tasker.runner.send(tasker.desire)
                                if status != Sts.aborted:  # not aborted
                                    tasks.append((tasker, retyme + tasker.tick))
                                    # allows for tick change during run

                            except StopIteration:  # returned instead of yielded
                                pass  # effectively tasker aborted itself

                        else:  # not yet
                            tasks.append((tasker, retyme))  # reappend it
                            status = tasker.status

                        if status in (Sts.running, Sts.started):
                            more = True

                    if not tasks:  # no pending taskers so done
                        break

                    if not more:  # all taskers stopped or aborted so done
                        break


                    if self.real:  # wait for real time to expire
                        while not self.timer.expired:
                            time.sleep(self.timer.remaining)
                        self.timer.restart()  #  no time lost

                    self.tock()  # advance tyme by one tick


                except KeyboardInterrupt: # CNTL-C shutdown skedder
                    break

                except SystemExit: # Forced shutdown of process
                    raise

                except Exception:  # Unknown exception
                    # Should inform user what exception caused shutdoen
                    raise


        finally: # finally clause always runs regardless of exception or not
            # Abort any running taskers to reclaim resources
            # Stopped or aborted taskers should have already released resources
            # if last run tasker exited due to exception then try finally clause in
            # its generator is responsible for releasing resources

            for i in range(len(tasks)):  # send abort to each remaining tasker
                tasker, retime, period = tasks.popleft() #pop it off
                try:
                    status = tasker.runner.send(ABORT)
                except StopIteration: #generator returned instead of yielded
                    pass


class Tymer():
    """
    Tymer class to measure cycle time given by .tyme property of Cycler instance.
    tyme is relative cycle time either artificial or real

    Attributes:
        ._start is start tyme in seconds
        ._stop  is stop tyme in seconds

    Properties:
        .duration = tyme duration of tymer in seconds from ._start to ._stop
        .elaspsed = tyme elasped in seconds  since ._start
        .remaining = tyme remaining in seconds  until ._stop
        .expired = True if expired, False otherwise, i.e. .cycler.tyme >= ._stop

    methods:
        .start() = start tymer at current cycler.tyme
        .restart() = restart tymer at last ._stop so no time lost

    """

    def __init__(self, cycler=None, duration=0.0, start=None):
        """
        Initialization method for instance.
        Parameters:
            cycler is reference to Cycler instance. Uses .tyme property
            duration is float tymer duration in seconds (fractional)
            start is float optional timer start time in seconds. Allows starting
                before or after current cycler.tyme
        """
        self.cycler = cycler if cycler is not None else Cycler()
        start = float(start) if start is not None else self.cycler.tyme
        self._start = start # need for default duration
        self._stop = self._start + float(duration)  # need for default duration
        self.start(duration=duration, start=start)


    @property
    def duration(self):
        """
        duration property getter,  .duration = ._stop - ._start
        .duration is float duration tyme
        """
        return (self._stop - self._start)


    @property
    def elapsed(self):
        """
        elapsed tyme property getter,
        Returns elapsed tyme in seconds (fractional) since ._start.
        """
        return (self.cycler.tyme - self._start)


    @property
    def remaining(self):
        """
        remaining tyme property getter,
        Returns remaining tyme in seconds (fractional) before ._stop.
        """
        return (self._stop - self.cycler.tyme)


    @property
    def expired(self):
        """
        Returns True if tymer has expired, False otherwise.
        self.cycler.tyme >= ._stop,
        """
        return (self.cycler.tyme >= self._stop)


    def start(self, duration=None, start=None):
        """
        Starts Tymer of duration secs at start time start secs.
            If duration not provided then uses current duration
            If start not provided then starts at current .cycler.tyme
        """
        # remember current duration when duration not provided
        duration = float(duration) if duration is not None else self.duration
        self._start = float(start) if start is not None else self.cycler.tyme
        self._stop = self._start + duration
        return self._start


    def restart(self, duration=None):
        """
        Lossless restart of Tymer at .tyme = ._stop for duration if provided,
        current duration otherwise
        No time lost. Useful to extend Tymer so no time lost
        """
        return self.start(duration=duration, start=self._stop)



