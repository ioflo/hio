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

