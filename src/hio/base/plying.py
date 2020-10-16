# -*- encoding: utf-8 -*-
"""
hio.core.plying Module
"""
import time
from collections import deque

from ..hioing import ValidationError, VersionError
from ..help import timing
from . import ticking


class Plier(ticking.Ticker):
    """
    Plier is coroutine scheduler
    Provides relative cycle time in seconds with .tyme property and advanced
    by .tick method of .tock sized increments.
    .tyme may be artificial time or real time in seconds.

    .ply method runs generators once that are synchronized to cycle time .tyme
           cycle may run as fast as possbile or run in real time.

    .run method continually runs .ply until generators are complete

    Inherited Attributes:

    Inherited Properties:
        .tyme is float relative cycle time, .tyme is artificial time
        .tock is float tyme increment of .tick()

    Inherited Methods:
        .tick increments .tyme by one .tock or provided tock

    Attributes:
        .real is boolean. True means run in real time, Otherwise as fast as possible.
        .limit is float maximum tyme limit to run then closes all doers
        .timer is MonoTimer for real time intervals

    """
    def __init__(self, real=False, limit=None, doers=None, **kwa):
        """
        Initialize instance
        Inherited Parameters:
            tyme is float initial value of cycle time in seconds
            tock is float tock time in seconds

        Parameters:
            real is boolean True means run in real time,
                            Otherwise run faster than real
            limit is float seconds for max run time of plier. None means no limit.
            doers is list of doers
        """
        super(Plier, self).__init__(**kwa)

        self.real = True if real else False
        self.limit = abs(float(limit)) if limit is not None else None
        self.timer = timing.MonoTimer(duration = self.tock)
        self.doers = list()  # list of runable generators


    def ready(self, doers=None):
        """
        Returns plys deque entered for plying using doers list if any else .doers
        """
        if doers is not None:
            self.doers = doers

        plys = deque()
        for doer in self.doers:
            do = doer.do(ticker=self)  # make generator
            plys.append((do, self.tyme))  #  ply is duple of (do, retyme)
        return plys


    def ply(self, plys):
        """
        Cycle once through plys deque and update in place
        plys is deque of duples of (do, retyme) where retyme is tyme in
            seconds when next should run may be real or simulated

        Each cycle checks all generators in plys deque and runs if retyme past.
        At end of cycle advances .tyme by one .tock by calling .tick()
        """
        for i in range(len(plys)):  # iterate once over each deed
            do, retyme = plys.popleft()  # pop it off

            if retyme <= self.tyme:  # run it now
                try:
                    tock = do.send(None)  #  nothing to send for now
                    plys.append((do, retyme + tock))  # reappend for next pass
                    # allows for tock change during run
                except StopIteration:  # returned instead of yielded
                    pass  # effectively do exited or aborted itself

            else:  # not retyme yet
                plys.append((do, retyme))  # reappend for next pass

        self.tick()  # advance .tyme by one plier .tock


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
        if limit is not None:
            self.limit = abs(float(limit))

        plys = self.ready(doers=doers)

        self.timer.start()
        try: #so always clean up resources if exception
            while True:  # until doers complete or exception
                try:  #CNTL-C generates keyboardInterrupt to break out of while loop

                    self.ply(plys)  # increments .tyme

                    if self.real:  # wait for real time to expire
                        while not self.timer.expired:
                            time.sleep(self.timer.remaining)
                        self.timer.restart()  #  no time lost

                    if self.limit and self.tyme >= self.limit:
                        break  # use for testing

                    if not plys:  # no more remaining plys so done
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

            while(plys):  # .close each remaining do in plys
                do, retime = plys.popleft() #pop it off
                try:
                    tock = do.close()  # force GeneratorExit
                except StopIteration:  # Hmm? What happened?
                    pass

