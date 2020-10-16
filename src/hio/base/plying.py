# -*- encoding: utf-8 -*-
"""
hio.core.plying Module
"""
import time
from collections import deque

from ..hioing import ValidationError, VersionError
from ..help.timing import MonoTimer
from . import ticking


class Plier(ticking.Ticker):
    """
    Plier is coroutine scheduler
    Provides relative cycle time in seconds with .tyme property and advanced
    by .tock method.
    .tyme may be artificial time or real time in seconds.

    .cycle method runs generators that are synchronized to cycle time .tyme
           cycle may run as fast as possbile or run in real time.

    Attributes:

    Properties:
        .tyme is float relative cycle time, tyme is artificial time

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
            limit is float seconds for max run time of plier. None means no limit.
        """
        super(Plier, self).__init__(**kwa)

        self.real = True if real else False
        self.limit = abs(float(limit)) if limit is not None else None
        self.timer = MonoTimer(duration = self.tick)
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

