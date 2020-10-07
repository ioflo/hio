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
    def __init__(self, tyme=None, tick=None):
        """
        Initialize instance
        Parameters:
            tyme is float cycle time in seconds
            time is fload tick time in seconds
        """
        self.tyme = float(tyme) if tyme is not None else 0.0
        self.tick = float(tick) if tick is not None else 1.0

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



class Tymer():
    """
    Tymer class to measure cycle time given by .tyme property of Cycler instance.
    tyme is relative cycle time either artificial or real

    Attributes:
        ._start is start tyme in seconds
        ._stop  is stop tyme in seconds

    Properties:
        .duration = tyme duration of tymer from ._start to ._stop
        .elaspsed = tyme elasped since start
        .remaining = tyme remaining until stop
        .expired = True if expired, False otherwise, i.e. .cycler.tyme >= ._stop

    methods:
        .start() = start tymer at current cycler.tyme
        .restart() = restart tymer at last ._stop so no time lost

    """

    def __init__(self, cycler=None, duration=0.0):
        """
        Initialization method for instance.
        Parameters:
            cycler is reference to Cycler instance. Uses .tyme property
            duration in seconds (fractional)
        """
        self._stop =  0.0
        self._start = 0.0
        self.cycler = cycler if cycler is not None else Cycler()
        self.start(duration=duration)


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


    def start(self, tyme=None, duration=None):
        """
        Starts Tymer at start time tyme secs for duration secs.
            If tyme not provided then starts at current .cycler.tyme
            If duration not provided then uses current duration
        """
        # remember current duration when duration not provided
        duration = duration if duration is not None else self.duration
        self._start = float(tyme if tyme else self.cycler.tyme)
        self._stop = self._start + float(duration )
        return self._start


    def restart(self, duration=None):
        """
        Lossless restart of Tymer at .tyme = ._stop for duration if provided,
        current duration otherwise
        No time lost. Useful to extend Tymer so no time lost
        """
        return self.start(tyme=self._stop, duration=duration)



