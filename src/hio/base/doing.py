# -*- encoding: utf-8 -*-
"""
hio.core.doing Module
"""
from collections import deque

from ..hioing import ValidationError, VersionError
from . import ticking
from ..core.tcp import serving, clienting

"""
Doer.__call__ on instance returns generator
Doer is generator creator

but has extra methods and scope that plain funtion does not
So have plain functions

whodo

"""
