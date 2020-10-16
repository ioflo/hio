# -*- encoding: utf-8 -*-
"""
hio.core.deeding Module
"""
from collections import deque

from ..hioing import ValidationError, VersionError
from ..help.timing import MonoTimer
from .basing import Ctl, Stt
from . import ticking
from . import doing
from ..core.tcp import serving, clienting

