# -*- encoding: utf-8 -*-
"""
tests  core.wms.wmsing module

"""
import pytest

import platform
import time
import socket
import os
import tempfile
import shutil

try:
    import win32file
except ImportError:
    pass

from hio import hioing
from hio.base import tyming, doing
from hio.core import wiring
from hio.core.wms import wmsing

def test_wms_basic():
    """ Test the uxd connection between two peers

    """
    if platform.system() != "Windows":
        return
    pass

    """Done Test"""


if __name__ == "__main__":
    test_wms_basic()
