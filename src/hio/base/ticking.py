# -*- encoding: utf-8 -*-
"""
hio.core.ticking Module
"""
import time
from collections import deque

from ..hioing import ValidationError, VersionError
from ..help.timing import MonoTimer

from .basing import Ctl, Stt


class Ticker():
    """
    Ticker is simulated time cycling object
    Provides relative cycle time in seconds with .tyme property and advanced
    by .tock method.
    .tyme may be artificial time or real time in seconds.

    .cycle method runs generators that are synchronized to cycle time .tyme
           cycle may run as fast as possbile or run in real time.

    Attributes:

    Properties:
        .tyme is float relative cycle time, tyme is artificial time

    """
    def __init__(self, tyme=0.0, tock=1.0):
        """
        Initialize instance
        Parameters:
            tyme is initial value of float cycle time in seconds
            tock is float tock time in seconds
        """
        self.tyme = float(tyme)
        self.tock = float(tock)

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
    def tock(self):
        """
        tock property getter, get ._tock
        .tock is float cycle time .tyme increment in seconds
        """
        return self._tock

    @tock.setter
    def tock(self, tock):
        """
        cycle time increment property setter, set ._tock to tock
        """
        self._tock= float(tock)

    def tick(self, tock=None):
        """
        Advance cycle time .tyme by tock seconds when provided othewise by .tock
        and return new .tyme
        Parameters:
            tock is float of amount of time in seconds to change .tyme
        """
        self.tyme += float(tock if tock is not None else self.tock)
        return self.tyme


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
        .start() = start tymer at current .ticker.tyme
        .restart() = restart tymer at last ._stop so no time lost

    """

    def __init__(self, ticker=None, duration=0.0, start=None):
        """
        Initialization method for instance.
        Parameters:
            ticker is reference to Ticker instance. Uses .tyme property
            duration is float tymer duration in seconds (fractional)
            start is float optional timer start time in seconds. Allows starting
                before or after current .ticker.tyme
        """
        self.ticker = ticker if ticker is not None else Ticker()
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
        .ticker.tyme >= ._stop,
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



