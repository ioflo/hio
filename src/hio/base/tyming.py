# -*- encoding: utf-8 -*-
"""
hio.core.tyming Module
"""
import time
from collections import deque

from ..hioing import ValidationError, VersionError
from ..help.timing import MonoTimer

from .basing import Ctl, Stt


class Tymist():
    """
    Tymist keeps artificial or simulated or cycle time, called tyme.
    Provides relative cycle time, tyme, in seconds with .tyme property
    in incremets of .tock seconds.
    .tyme is advanced one .tock increment with .tick method.
    .tyme may be synchronized with real time by a .tyme manager

    Attributes:

    Properties:
        .tyme is float relative cycle time, .tyme is artificial time
        .tock is float tyme increment of .tick()

    Methods:
        .tick increments .tyme by one .tock or provided tock

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


class Tymee():
    """
    Tymee has .tyme property that returns the artificial or simulated or cycle time
    from its referenced Tymist instance ._tymist.

    Attributes:

    Properties:
        .tyme is float relative cycle time, .tyme is artificial time

    Methods:

    Hidden:
        ._tymist is Tymist instance reference

    """
    def __init__(self, tymist=None):
        """
        Initialize instance
        Parameters:
            tymist is reference to Tymist instance
        """
        self._tymist = tymist if tymist is not None else Tymist()

    @property
    def tyme(self):
        """
        tyme property getter, get ._tyme
        .tyme is float cycle time in seconds
        """
        return self._tymist.tyme


class Tymer(Tymee):
    """
    Tymer class to measure cycle time given by .tyme property of Tymist instance.
    tyme is relative cycle time either artificial or real

    Inherited Properties:
        .tyme is cycle time of ._tymist

    Inhereited Hidden:
        ._tymist is Tymist instance reference

    Attributes:
        ._start is start tyme in seconds
        ._stop  is stop tyme in seconds

    Properties:
        .duration = tyme duration of tymer in seconds from ._start to ._stop
        .elaspsed = tyme elasped in seconds  since ._start
        .remaining = tyme remaining in seconds  until ._stop
        .expired = True if expired, False otherwise, i.e. .tyme >= ._stop

    methods:
        .start() = start tymer at current .tyme
        .restart() = restart tymer at last ._stop so no time lost

    """

    def __init__(self, tymist=None, duration=0.0, start=None):
        """
        Initialization method for instance.
        Parameters:
            tymist is reference to Tymer instance. Uses .tyme property
            duration is float tymer duration in seconds (fractional)
            start is float optional timer start time in seconds. Allows starting
                before or after current .tyme
        """
        if tymist is None:
            tymist = Tymist()
        super(Tymer, self).__init__(tymist=tymist)
        start = float(start) if start is not None else self.tyme
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
        return (self.tyme - self._start)


    @property
    def remaining(self):
        """
        remaining tyme property getter,
        Returns remaining tyme in seconds (fractional) before ._stop.
        """
        return (self._stop - self.tyme)


    @property
    def expired(self):
        """
        Returns True if tymer has expired, False otherwise.
        .tyme >= ._stop,
        """
        return (self.tyme >= self._stop)


    def start(self, duration=None, start=None):
        """
        Starts Tymer of duration secs at start time start secs.
            If duration not provided then uses current duration
            If start not provided then starts at current .tyme
        """
        # remember current duration when duration not provided
        duration = float(duration) if duration is not None else self.duration
        self._start = float(start) if start is not None else self.tyme
        self._stop = self._start + duration
        return self._start


    def restart(self, duration=None):
        """
        Lossless restart of Tymer at .tyme = ._stop for duration if provided,
        current duration otherwise
        No time lost. Useful to extend Tymer so no time lost
        """
        return self.start(duration=duration, start=self._stop)



