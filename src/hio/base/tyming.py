# -*- encoding: utf-8 -*-
"""
hio.core.tyming Module
"""
import time
from collections import deque

from ..hioing import ValidationError, VersionError
from .. import hioing
from ..help.timing import MonoTimer

# from .basing import Ctl, Stt



class Tymist(hioing.Mixin):
    """
    Tymist keeps artificial or simulated or cycle time, called tyme.
    Provides relative cycle time, tyme, in seconds with .tyme property
    in incremets of .tock seconds.
    .tyme is advanced one .tock increment with .tick method.
    .tyme may be synchronized with real time by a .tyme manager

    Class Attributes:
        .Tock is default .tock

    Attributes:

    Properties:
        .tyme is float relative cycle time, .tyme is artificial time
        .tock is float tyme increment of .tick()

    Methods:
        .tick increments .tyme by one .tock or provided tock

    """
    Tock = 0.03125  # 1/32

    def __init__(self, tyme=0.0, tock=None, **kwa):
        """
        Initialize instance
        Parameters:
            tyme is initial value of float cycle time in seconds
            tock is float tock time in seconds
        """
        super(Tymist,self).__init__(**kwa)  # Mixin for Mult-inheritance MRO
        self.tyme = float(tyme)
        self.tock = float(tock) if tock is not None else self.Tock

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

    def tymen(self):
        """
        Returns function wrapper closure tymth, when called tymth() returns .tyme.
        This enables read only injection of .tyme into any object via tymth()
        that wants to be on or access this Tymist's tyme base.
        """
        def tymth():
            return self.tyme
        return tymth



class Tymee(hioing.Mixin):
    """
    Tymee has .tyme property that returns the artificial or simulated or cycle time
    from its referenced Tymist instance ._tymist.

    Attributes:

    Properties:
        .tyme is float relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        .tymth is function wrapper closure returned by Tymist .tymeth() method.
            When .tymth is called it returns associated Tymist .tyme.
            .tymth provides injected dependency on Tymist tyme base.

    Methods:
        .wind  injects ._tymth dependency from associated Tymist to get its .tyme

    Hidden:
        ._tymth is injected function wrapper closure returned by .tymen() of
            associated Tymist instance that returns Tymist .tyme. when called.

    """
    def __init__(self, tymth=None, **kwa):
        """
        Initialize instance
        Parameters:
            tymth is injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
        """
        super(Tymee, self).__init__(**kwa)  # Mixin for Mult-inheritance MRO
        self._tymth = tymth  # maybe wound later to set to not None


    @property
    def tyme(self):
        """
        tyme property getter, get ._tyme
        .tyme is float cycle time in seconds
        """
        return self._tymth()


    @property
    def tymth(self):
        """
        tymth property getter, get ._tymth
        returns own copy of tymist.tynth function wrapper closure for subsequent
        injection into related objects that want to be on same tymist tyme base.
        """
        return self._tymth


    @tymth.setter
    def tymth(self, tymth):
        """
        tymth property setter, sets ._tymth to tymth.
        tymth is function wrapper closure that returns tymist.tyme
        """
        self._tymth = tymth


    def wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Override in subclasses to update any dependencies on a change in
        tymist.tymth base
        """
        self.tymth = tymth


class Tymer(Tymee):
    """
    Tymer class to measure cycle time given by .tyme property of Tymist instance.
    tyme is relative cycle time either artificial or real

    Inherited Attributes

    Attributes:

    Inherited Properties:
        .tyme is float relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        .tymth is function wrapper closure returned by Tymist .tymeth() method.
            When .tymth is called it returns associated Tymist .tyme.
            .tymth provides injected dependency on Tymist tyme base.

    Properties:
        .duration = tyme duration of tymer in seconds from ._start to ._stop
        .elaspsed = tyme elasped in seconds  since ._start
        .remaining = tyme remaining in seconds  until ._stop
        .expired = True if expired, False otherwise, i.e. .tyme >= ._stop

    Inherited Methods:
        .wind is injects ._tymth dependency

    Methods:
        .start() = start tymer at current .tyme
        .restart() = restart tymer at last ._stop so no time lost

    Hidden:
        ._tymth is injected function wrapper closure returned by .tymen() of
            associated Tymist instance that returns Tymist .tyme. when called.
        ._start is start tyme in seconds
        ._stop  is stop tyme in seconds

    """
    Duration = 0.0  # default duration when not provided

    def __init__(self, duration=None, start=None, **kwa):
        """
        Initialization method for instance.
        Parameters:
            duration is float tymer duration in seconds (fractional)
            start is float optional timer start time in seconds. Allows starting
                before or after current .tyme
        """
        super(Tymer, self).__init__(**kwa)
        duration = float(duration) if duration is not None else self.Duration
        if start is None and not self.tymth:  # needed so default .duration works
            start = 0.0
        self._start = float(start) if start is not None else self.tyme
        self._stop = self._start + float(duration)  # needed so default .duration
        self.start(duration=duration, start=self._start)


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


    def wind(self, tymth):
        """
        Inject new ._tymist and any other bundled tymee references
        Update any dependencies on a change in ._tymist:
            starts over itself at new ._tymists time
        """
        super(Tymer, self).wind(tymth)
        self.start()


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



