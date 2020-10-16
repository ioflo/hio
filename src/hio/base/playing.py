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
            tock is float tock time in seconds
        Parameters:
            real is boolean True means run in real time,
                            Otherwise run faster than real
            limit is float seconds for max run time of player. None means no limit.
        """
        super(Player, self).__init__(**kwa)

        self.real = True if real else False
        self.limit = abs(float(limit)) if limit is not None else None
        self.timer = timing.MonoTimer(duration = self.tock)
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
        At end of cycle advances .tyme by one .tock by calling .turn()
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

        self.tick()  # advance .tyme by one tock


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


