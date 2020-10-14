# -*- encoding: utf-8 -*-
"""
hio.core.cycling Module
"""


import enum
from collections import deque

from ..hioing import ValidationError, VersionError
from ..help.timing import MonoTimer

from .basing import Ctl, Sts


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
    def __init__(self, tyme=0.0, tick=1.0, real=False, limit=None, doers=None):
        """
        Initialize instance
        Parameters:
            tyme is initial value of float cycle time in seconds
            tick is float tick time in seconds
            real is boolean True means run in real time,
                            Otherwise run faster than real
            limit is float seconds for max run time of cycler. None means no limit.
            doers is list of Doers instances with generator methods
        """
        self.tyme = float(tyme)
        self.tick = float(tick)

        self.real = True if real else False
        self.limit = abs(float(limit)) if limit is not None else None
        self.timer = MonoTimer(duration = self.tick)
        # deque of runable generators
        self.doers = doers if doers is not None else list()

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

    def turn(self, tick=None):
        """
        Advance cycle time .tyme by tick seconds when provided othewise by .tick
        and return new .tyme
        Parameters:
            tick is float of amount of time in seconds to change .tyme
        """
        self.tyme += float(tick if tick is not None else self.tick)
        return self.tyme


    def cycle(self, doers=None):
        """
        Prepares deeds deque from .doers or doers
        Each entry in deeds is duple of (doer, retyme) where retyme is tyme in
            seconds when next should run may be real or simulated
        Each cycle runs all generators in deeds deque by calling .do on each one.

        Once deeds is empty .cycle exits.

        Keyboard interrupt (cntl-c) also forces exit.

        Since finally clause closes generators they must be reinited before then
        can be run again
        """
        if doers is not None:
            self.doers = doers

        deeds = deque()
        for doer in self.doers:
            doer.status = Sts.exited
            doer.desire = Ctl.recur
            deeds.append((doer, self.tyme))  # all run first time

        self.timer.start()
        try: #so always clean up resources if exception
            while True:
                try: #CNTL-C generates keyboardInterrupt to break out of while loop
                    mores = deque()  # remaining deeds for next pass

                    while(deeds): #attempt to run each doer once
                        doer, retyme = deeds.popleft()  # pop it off

                        if retyme <= self.tyme:  # run it now
                            try:
                                status = doer.do(doer.desire)
                                # aborted always forces StopIteraction
                                # reappend for next pass
                                mores.append((doer, retyme + doer.tock))
                                # allows for tock change during run
                            except StopIteration:  # returned instead of yielded
                                pass  # effectively tasker aborted itself

                        elif doer.status in (Sts.recurring, Sts.entered):  # remains
                            mores.append((doer, retyme))  # reappend it

                    if mores:  # no remaining doers so done
                        deeds = mores
                        mores = deeds  # deeds now empty

                    else:
                        break  # break out of forever loop

                    if self.real:  # wait for real time to expire
                        while not self.timer.expired:
                            time.sleep(self.timer.remaining)
                        self.timer.restart()  #  no time lost

                    self.turn()  # advance tyme by one tick

                    if self.limit and self.tyme >= self.limit:
                        break

                except KeyboardInterrupt: # CNTL-C shutdown skedder
                    break

                except SystemExit: # Forced shutdown of process
                    raise

                except Exception:  # Unknown exception
                    raise


        finally: # finally clause always runs regardless of exception or not
            # Abort any running taskers to reclaim resources
            # Stopped or aborted taskers should have already released resources
            # if last run tasker exited due to exception then try finally clause in
            # its generator is responsible for releasing resources

            while(deeds):  # send abort to each remaining doer
                doer, retime, period = deeds.popleft() #pop it off
                try:
                    status = doer.do(Ctl.abort)
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



