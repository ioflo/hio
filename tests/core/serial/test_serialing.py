# -*- encoding: utf-8 -*-
"""
tests.core.test_serialing module

"""
import pytest

from hio.core.serial import serialing

def test_console():
    """
    Tests Console class

    Must configure Debug I/O to use external console window.
    """

    console = serialing.Console()
    result = console.reopen()
    if not result:  # only works on external console window in wingide
        return

    assert result
    assert console.opened
    assert console.fd

    cout = b"Enter 'hello' and hit return: "
    console.put(cout)
    cin = b''
    while not cin:
        cin = console.getLine()
    console.put(b"You typed: " + cin)
    assert b'hello\n' == cin

    console.close()

    """End Test"""

if __name__ == "__main__":
    test_console()
