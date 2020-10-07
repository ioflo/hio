# -*- encoding: utf-8 -*-
"""
hio.core.cycling Module
"""

from ..hioing import ValidationError, VersionError


class Cycler():
    """
    Cycler is root hierarchical time slice cycling object
    Uses relative cycle time in seconds tracked by .tyme property and advanced
    by .tock method.
    .tyme may be artificial time or real time in seconds.

    Attributes:

    Properties:
        .tyme is float relative cycle time, tyme is artificial time

    """
    def __init__(self, tyme=0.0, tick=1.0):
        """
        Initialize instance
        Parameters:
            tyme is float cycle time in seconds
            time is float tick time in seconds
        """
        self.tyme = float(tyme)
        self.tick = float(tick)

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

    def cycle(self):
        """
        Cycles runs all generators in runable list by calling next() method until
        none left.

        Keyboard interrupt (cntl-c) to end forever loop.

        Since finally clause closes taskers they must be restarted before
        run can be executed again
        """
        self.timer.restart()

        #make local reference for speed put out side loop?
        ready = self.ready
        #stopped = self.stopped
        aborted = self.aborted

        try: #so always clean up resources if exception
            while True:
                try: #CNTL-C generates keyboardInterrupt to break out of while loop

                    more = False #are any taskers RUNNING or STARTED

                    for i in range(len(ready)): #attempt to run each ready tasker
                        tasker, retime, period = ready.popleft() #pop it off

                        if retime > stamp: #not time yet
                            ready.append((tasker, retime, period)) #reappend it
                            status = tasker.status

                        else: #run it
                            try:
                                status = tasker.runner.send(tasker.desire)
                                if status == ABORTED: #aborted so abort tasker
                                    aborted.append((tasker, stamp, period))
                                    console.profuse("     Tasker Self Aborted: {0}\n".format(tasker.name))
                                else:
                                    ready.append((tasker,
                                                  retime + tasker.period,
                                                  tasker.period))  # append allows for period change

                            except StopIteration: #generator returned instead of yielded
                                aborted.append((tasker, stamp, period))
                                console.profuse("     Tasker Aborted due to StopIteration: {0}\n".format(tasker.name))

                        if status == RUNNING or status == STARTED:
                            more = True

                    if not ready: #no pending taskers so done
                        break

                    if not more: #all taskers stopped or aborted
                        break

                    #update time stamps
                    if self.real:
                        while not self.timer.expired:
                            time.sleep(self.timer.remaining)
                        self.timer.repeat()

                    self.stamp += self.period
                    stamp = self.stamp


                except KeyboardInterrupt: # CNTL-C shutdown skedder

                    break

                except SystemExit: # User know why shutting down

                    raise

                except Exception: # Let user know what exception caused shutdoen

                    raise


        finally: # finally clause always runs regardless of exception or not
            # Abort any running taskers to reclaim resources
            #S topped or aborted taskers should have already released resources
            # if last run tasker exited due to exception then try finally clause in
            # its generator is responsible for releasing resources

            for i in range(len(ready)): #run each ready tasker once
                tasker,retime,period = ready.popleft() #pop it off

                try:
                    status = tasker.runner.send(ABORT)
                    console.terse("Tasker '{0}' aborted\n".format(tasker.name))
                except StopIteration: #generator returned instead of yielded
                    console.terse("Tasker '{0}' generator already exited\n".format(tasker.name))

                #tasker.runner.close() #kill generator


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



