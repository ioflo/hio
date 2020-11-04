# -*- encoding: utf-8 -*-
"""
tests.core.test_serialing module

"""
import pytest

from hio.core.serial import serialing

def test_console():
    """
    Tests Console class
    """

    console = serialing.Console()
    result = console.reopen()
    assert result
    assert console.opened
    assert console.fd

    cout = "Enter 'hello' and hit return: "
    console.put(cout)
    cin = ''
    while not cin:
        cin = console.getLine()
    console.put("You typed: " + cin)
    assert 'hello\n' == cin

    console.close()

    """End Test"""

if __name__ == "__main__":
    test_console()
