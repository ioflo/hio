# -*- encoding: utf-8 -*-
"""
tests.core.test_coring module

"""

import pytest

from hio.core.coring import (normalizeHost, arpCreate, arpDelete)

def test_ip_utils():
    """
    Test the ip utility functions in core.coring
    """
    host = normalizeHost("localhost")
    assert host == "127.0.0.1"

    # netifaces not fully supported on macos only linux now
    #host = getDefaultHost()
    #assert host != ""

    #bcast = getDefaultBroadcast()
    #assert bcast.endswith(".255") or bcast.endswith(".127") or bcast.endswith(".63")

    """Done Test"""




if __name__ == "__main__":
    test_ip_utils()
