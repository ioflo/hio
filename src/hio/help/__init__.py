# -*- encoding: utf-8 -*-
"""
hio.help package

"""

# Setup module global ogler as package logger factory. This must be done on
# import to ensure global is defined so all modules in package have access to
# logggers via help.ogler.getLoggers().
# May always change level and reopen log file if need be.

from . import ogling

# initialize global ogler at hio.help.ogler always instantiated by default
ogler = ogling.initOgler(prefix='hio')  # init only runs  once on import

from .helping import isNonStringIterable, isNonStringSequence, isIterator, Reat
from .helping import NonStringIterable, NonStringSequence
from .decking import Deck
from .hicting import Hict, Mict
from .timing import Timer, MonoTimer, TimerError, RetroTimerError
from .naming import Namer
from .doming import RawDom, MapDom, IceMapDom, modify, modize
from .mining import Renam, Mine

