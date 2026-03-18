# -*- encoding: utf-8 -*-
"""hio.help.timing module

"""
import time
import datetime
import asyncio

from .. import hioing


class TimerError(hioing.HioError):
    """Generic Timer Errors. Usage: raise TimerError("error message")."""

class RetroTimerError(TimerError):
    """Error due to real time being retrograded before start time of timer.
    Usage: raise RetroTimerError("error message").
    """


class Timer(hioing.Mixin):
    """Class to manage real elaspsed time using time module.

    Attribute notes:
        - ._start is start tyme in seconds
        - ._stop is stop tyme in seconds

    Property notes:
        - .duration is float time duration in seconds of timer from ._start to ._stop
        - .elaspsed is float time elasped in seconds since ._start
        - .remaining is float time remaining in seconds until ._stop
        - .expired is boolean, True if expired, False otherwise, i.e. time >= ._stop

    Method notes:
        - start() starts timer at current time
        - restart() restarts timer at last ._stop so no time lost
    """

    def __init__(self, duration=0.0, start=None, **kwa):
        """Initialization method for instance.
        Parameters:
            duration is float duration of timer in seconds (fractional)
            start is float optional start time in seconds allows starting before
               or after current time
        """
        super(Timer, self).__init__(**kwa)  # Mixin for Mult-inheritance MRO
        self._start = float(start) if start is not None else time.time()
        self._stop = self._start + float(duration)  # need for default duration
        self.start(duration=duration, start=start)


    @property
    def duration(self):
        """duration property getter,  .duration = ._stop - ._start
        .duration is float duration tyme
        """
        return (self._stop - self._start)


    @property
    def elapsed(self):
        """elapsed time property getter,
        Returns elapsed time in seconds (fractional) since ._start.
        """
        return (time.time() - self._start)


    @property
    def remaining(self):
        """remaining time property getter,
        Returns remaining time in seconds (fractional) before ._stop.
        """
        return (self._stop - time.time())


    @property
    def expired(self):
        """expired property

        Returns True if timer has expired, False otherwise.
        time.time() >= ._stop,
        """
        return (time.time() >= self._stop)


    def start(self, duration=None, start=None):
        """Starts Timer of duration secs at start time start secs.
            If duration not provided then uses current duration
            If start not provided then starts at current time.time()
        """
        # remember current duration when duration not provided
        duration = float(duration) if duration is not None else self.duration
        self._start = float(start) if start is not None else time.time()
        self._stop = self._start + duration
        return self._start


    def restart(self, duration=None):
        """Lossless restart of Timer at start = ._stop for duration if provided,
        Otherwise current duration.
        No time lost. Useful to extend Timer so no time lost
        """
        return self.start(duration=duration, start=self._stop)



class MonoTimer(Timer):
    """Class to manage real elaspsed time using time module but with monotonically
    increating time guarantee in spite of system time being retrograded.

    If the system clock is retrograded (moved back in time) while the timer is
    running then time.time() could move to before the start time.
    MonoTimer detects this retrograde and if retro is True then
    retrogrades the start and stop times back Otherwise it raises a TimerRetroError.
    MonoTimer is not able to detect a prograded clock (moved forward in time)

    Attributes:
        ._start is start time in seconds
        ._stop  is stop time in seconds
        ._last is last measured time in seconds with retrograde handling
        .retro is boolean If True retrograde ._start and ._stop when time is retrograded.

    Properties:
        .duration is float time duration in seconds of timer from ._start to ._stop
        .elaspsed is float time elasped in seconds since ._start
        .remaining is float time remaining in seconds until ._stop
        .expired is boolean True if expired, False otherwise, i.e. time >= ._stop
        .latest is float latest measured time in seconds with retrograte handling

    Methods:
        - start: start timer at current time and return start time
        - restart: restart timer at last ._stop with no time lost, returns start time
    """

    def __init__(self, duration=0.0, start=None, retro=True):
        """Initialization method for instance.
        duration is in seconds (fractional).
        start is an optional start time in seconds allowing start before or
        after current time.
        retro is boolean. True means automatically shift timer whenever a
        retrograded clock is detected, otherwise raise RetroTimerError.
        """
        self._start = float(start) if start is not None else time.time()
        self._stop = self._start + float(duration)  # need for default duration
        self._last = self._start
        self.retro = True if retro else False  #  ensure boolean
        self.start(duration=duration, start=start)


    @property
    def elapsed(self):
        """elapsed time property getter,
        Returns elapsed time in seconds (fractional) since ._start.
        """
        return (self.latest - self._start)


    @property
    def remaining(self):
        """remaining time property getter,
        Returns remaining time in seconds (fractional) before ._stop.
        """
        return (self._stop - self.latest)


    @property
    def expired(self):
        """Returns True if timer has expired, False otherwise.
        .latest >= ._stop,
        """
        return (self.latest >= self._stop)

    @property
    def latest(self):
        """latest measured time property getter,
        Returns latest measured time in seconds adjusted for retrograded system time.
        """
        delta = time.time() - self._last  # current time - last time checked
        if delta < 0:  # system clock has retrograded
            if self.retro:
                self._start += delta
                self._stop += delta
            else:
                raise RetroTimerError("System time retrograded by {0} seconds"
                                      " while timer running.".format(delta))

        self._last += delta
        return self._last


class AsyncTimer(Timer):
    """Class to manage real elaspsed time using asyncio event loop time.
    Namely asyncio.get_event_loop().time()

    Attributes:
        ._start is start tyme in seconds
        ._stop  is stop tyme in seconds

    Properties:
        .duration is float time duration in seconds of timer from ._start to ._stop
        .elaspsed is float time elasped in seconds since ._start
        .remaining is float time remaining in seconds until ._stop
        .expired is boolean, True if expired, False otherwise, i.e. time >= ._stop

    Methods:
        - start: start timer at current time
        - restart: restart timer at last ._stop so no time lost
    """

    def __init__(self, duration=0.0, start=None, **kwa):
        """Initialization method for instance.
        Parameters:
            duration is float duration of timer in seconds (fractional)
            start is float optional start time in seconds allows starting before
               or after current time
        """
        super(Timer, self).__init__(**kwa)  # Mixin for Mult-inheritance MRO
        self._start = float(start) if start is not None else time.time()
        self._stop = self._start + float(duration)  # need for default duration
        self.start(duration=duration, start=start)


    @property
    def duration(self):
        """duration property getter,  .duration = ._stop - ._start
        .duration is float duration tyme
        """
        return (self._stop - self._start)


    @property
    def elapsed(self):
        """elapsed time property getter,
        Returns elapsed time in seconds (fractional) since ._start.
        """
        return (asyncio.get_event_loop().time() - self._start)


    @property
    def remaining(self):
        """remaining time property getter,
        Returns remaining time in seconds (fractional) before ._stop.
        """
        return (self._stop - asyncio.get_event_loop().time())


    @property
    def expired(self):
        """expired property

        Returns True if timer has expired, False otherwise.
        time.time() >= ._stop,
        """
        return (asyncio.get_event_loop().time() >= self._stop)


    def start(self, duration=None, start=None):
        """Starts Timer of duration secs at start time start secs.
            If duration not provided then uses current duration
            If start not provided then starts at current time.time()
        """
        # remember current duration when duration not provided
        duration = float(duration) if duration is not None else self.duration
        self._start = float(start) if start is not None else asyncio.get_event_loop().time()
        self._stop = self._start + duration
        return self._start


    def restart(self, duration=None):
        """Lossless restart of Timer at start = ._stop for duration if provided,
        Otherwise current duration.
        No time lost. Useful to extend Timer so no time lost
        """
        return self.start(duration=duration, start=self._stop)


# datetime utilities
def nowUTC():
    """Returns timezone aware datetime of current UTC time
    Convenience function that allows monkeypatching in tests to mock time
    """
    return (datetime.datetime.now(datetime.timezone.utc))


def nowIso8601():
    """Returns timezone aware datetime of current UTC time in RFC-3339 profile
    of ISO 8601 format. Uses now(timezone.utc)

    YYYY-MM-DDTHH:MM:SS.ffffff+HH:MM[:SS[.ffffff]]
    .strftime('%Y-%m-%dT%H:%M:%S.%f%z')
    '2020-08-22T17:50:09.988921+00:00'
    Assumes TZ aware
    For nanosecond use instead attotime or datatime64 in pandas or numpy
    """
    return (nowUTC().isoformat(timespec='microseconds'))


def toIso8601(dt=None):
    """Returns str datetime dt in RFC-3339 profile of ISO 8601 format.
    Converts datetime object dt to ISO 8601 formt
    If dt is missing use now(timezone.utc)

    YYYY-MM-DDTHH:MM:SS.ffffff+HH:MM[:SS[.ffffff]]
    .strftime('%Y-%m-%dT%H:%M:%S.%f%z')
    '2020-08-22T17:50:09.988921+00:00'
    Assumes TZ aware
    For nanosecond use instead attotime or datatime64 in pandas or numpy
    """
    if dt is None:
        dt = nowUTC()  # make it aware

    return (dt.isoformat(timespec='microseconds'))  # force include microseconds


def fromIso8601(dts):
    """Returns datetime object from RFC-3339 profile of ISO 8601 format str or bytes.
    Converts dts from ISO 8601 format to datetime object

    YYYY-MM-DDTHH:MM:SS.ffffff+HH:MM[:SS[.ffffff]]
    .strftime('%Y-%m-%dT%H:%M:%S.%f%z')
    '2020-08-22T17:50:09.988921+00:00'
    Assumes TZ aware
    For nanosecond use instead attotime or datatime64 in pandas or numpy
    """
    if hasattr(dts, "decode"):
        dts = dts.decode("utf-8")
    return (datetime.datetime.fromisoformat(dts))
