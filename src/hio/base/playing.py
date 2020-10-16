# -*- encoding: utf-8 -*-
"""
hio.core.cycling Module
"""
import time
from collections import deque

from ..hioing import ValidationError, VersionError
from ..help import timing
from . import ticking
from .basing import Ctl, Stt


class Player(ticking.Ticker):
    """
    Player plays nested state machines

    Attributes:

    Properties:


    """
    def __init__(self, real=False, limit=None, **kwa):
        """
        Initialize instance
        Inherited Parameters:
            tyme is initial value of float cycle time in seconds
            tick is float tick time in seconds
        Parameters:
            real is boolean True means run in real time,
                            Otherwise run faster than real
            limit is float seconds for max run time of player. None means no limit.
        """
        super(Player, self).__init__(**kwa)

        self.real = True if real else False
        self.limit = abs(float(limit)) if limit is not None else None
        self.timer = timing.MonoTimer(duration = self.tick)
        # deque of runable generators
        self.doers = list()

    def ready(self, doers=None):
        """
        Returns deeds deque readied for cycling using doers list if any else .doers
        """
        if doers is not None:
            self.doers = doers

        deeds = deque()
        for doer in self.doers:
            doer.makedo()  # reinit generator
            doer.state = Stt.exited
            doer.desire = Ctl.recur
            deeds.append((doer, self.tyme))  # all run first time

        return deeds

    def cycle(self, deeds):
        """
        Cycle once through deeds deque and update in place
        deeds is deque of duples of (doer, retyme) where retyme is tyme in
            seconds when next should run may be real or simulated

        Each cycle checks all generators in deeds deque and runs if retyme past.
        At end of cycle advances .tyme by one .tick by calling .turn()
        """
        for i in range(len(deeds)):  # iterate once over each deed
            doer, retyme = deeds.popleft()  # pop it off

            if retyme <= self.tyme:  # run it now
                try:
                    state = doer.do(doer.desire)  # abortion forces StopIteraction
                    if doer.state in (Stt.entered, Stt.recurring ):  # still entered or recurring
                        deeds.append((doer, retyme + doer.tock))  # reappend for next pass
                    # allows for tock change during run
                except StopIteration:  # returned instead of yielded
                    pass  # effectively doer aborted itself

            elif doer.state in (Stt.entered, Stt.recurring ):
                # not tyme yet and still entered or recurring
                deeds.append((doer, retyme))  # reappend for next pass

        self.turn()  # advance .tyme by one tick


    def run(self, doers=None, limit=None):
        """
        Prepares deeds deque from .doers or doers and then runs .cycle with deeds
        until completion
        Each entry in deeds is duple of (doer, retyme) where retyme is tyme in
            seconds when next should run may be real or simulated
        Each cycle runs all generators in deeds deque by calling .do on each one.

        Once deeds is empty .cycle exits.

        Keyboard interrupt (cntl-c) also forces exit.

        Since finally clause closes generators they must be reinited before then
        can be run again
        """
        deeds = self.ready(doers=doers)

        if doers is not None:
            self.doers = doers

        if limit is not None:
            self.limit = abs(float(limit))

        deeds = deque()
        for doer in self.doers:
            doer.state = Stt.exited
            doer.desire = Ctl.recur
            deeds.append((doer, self.tyme))  # all run first time

        self.timer.start()
        try: #so always clean up resources if exception
            while True:  # until doers complete or exception
                try:  #CNTL-C generates keyboardInterrupt to break out of while loop

                    self.cycle(deeds)  # increments .tyme

                    if self.real:  # wait for real time to expire
                        while not self.timer.expired:
                            time.sleep(self.timer.remaining)
                        self.timer.restart()  #  no time lost

                    if self.limit and self.tyme >= self.limit:
                        break  # use for testing

                    if not deeds:  # no more remaining deeds so done
                        break  # break out of forever loop

                except KeyboardInterrupt: # CNTL-C shutdown skedder
                    break

                except SystemExit: # Forced shutdown of process
                    raise

                except Exception:  # Unknown exception
                    raise


        finally: # finally clause always runs regardless of exception or not
            # Abort any running taskers to reclaim resources
            # Stopped or aborted taskers should have already released resources
            # if last run doer exited due to exception then try finally clause in
            # its generator is responsible for releasing resources

            while(deeds):  # send abort to each remaining doer
                doer, retime = deeds.popleft() #pop it off
                try:
                    state = doer.do(Ctl.abort)
                except StopIteration: #generator returned instead of yielded
                    pass


class Tymer():
    """
    Tymer class to measure cycle time given by .tyme property of Ticker instance.
    tyme is relative cycle time either artificial or real

    Attributes:
        ._start is start tyme in seconds
        ._stop  is stop tyme in seconds

    Properties:
        .duration = tyme duration of tymer in seconds from ._start to ._stop
        .elaspsed = tyme elasped in seconds  since ._start
        .remaining = tyme remaining in seconds  until ._stop
        .expired = True if expired, False otherwise, i.e. .ticker.tyme >= ._stop

    methods:
        .start() = start tymer at current ticker.tyme
        .restart() = restart tymer at last ._stop so no time lost

    """

    def __init__(self, ticker=None, duration=0.0, start=None):
        """
        Initialization method for instance.
        Parameters:
            ticker is reference to Ticker instance. Uses .tyme property
            duration is float tymer duration in seconds (fractional)
            start is float optional timer start time in seconds. Allows starting
                before or after current ticker.tyme
        """
        self.ticker = ticker if ticker is not None else Player()
        start = float(start) if start is not None else self.ticker.tyme
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
        return (self.ticker.tyme - self._start)


    @property
    def remaining(self):
        """
        remaining tyme property getter,
        Returns remaining tyme in seconds (fractional) before ._stop.
        """
        return (self._stop - self.ticker.tyme)


    @property
    def expired(self):
        """
        Returns True if tymer has expired, False otherwise.
        self.ticker.tyme >= ._stop,
        """
        return (self.ticker.tyme >= self._stop)


    def start(self, duration=None, start=None):
        """
        Starts Tymer of duration secs at start time start secs.
            If duration not provided then uses current duration
            If start not provided then starts at current .ticker.tyme
        """
        # remember current duration when duration not provided
        duration = float(duration) if duration is not None else self.duration
        self._start = float(start) if start is not None else self.ticker.tyme
        self._stop = self._start + duration
        return self._start


    def restart(self, duration=None):
        """
        Lossless restart of Tymer at .tyme = ._stop for duration if provided,
        current duration otherwise
        No time lost. Useful to extend Tymer so no time lost
        """
        return self.start(duration=duration, start=self._stop)



