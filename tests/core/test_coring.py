# -*- encoding: utf-8 -*-
"""
tests.core.test_coring module

"""
import pytest

from hio.core.coring import (normalizeHost, getDefaultHost, getDefaultBroadcast,
                             arpCreate, arpDelete)

def test_ip_utils():
    """
    Test the ip utility functions in core.coring
    """
    host = normalizeHost("localhost")
    assert host == "127.0.0.1"

    host = getDefaultHost()
    assert host != ""

    bcast = getDefaultBroadcast()
    assert bcast.endswith(".255")

    """Done Test"""




if __name__ == "__main__":
    test_ip_utils()
