# -*- encoding: utf-8 -*-
"""
tests.core.test_serialing module

"""
import pytest

import os

from hio.core.serial import serialing


def test_console():
    """
    Tests Console class

    Must configure Debug I/O to use external console window.
    """
    console = serialing.Console()
    assert console.bs == 256
    assert console.fd == None
    assert not console.opened
    assert len(console.rxbs) == 0

    result = console.reopen()
    if not result:  # only works on external console window in wingide
        return

    assert result
    assert console.opened
    assert console.fd
    assert os.isatty(console.fd)

    cout = b"Enter 'hello' and hit return: "
    console.put(cout)
    cin = b''
    while not cin:
        cin = console.get()

    console.put(b"You typed: " + cin + b'\n')
    assert cin ==  b'hello'
    assert len(console.rxbs) == 0

    console.close()

    # test small buffer stiches together full line
    result = console.reopen()
    if not result:  # only works on external console window in wingide
        return

    assert result
    assert console.opened
    assert console.fd
    assert os.isatty(console.fd)

    cout = b"Enter 'the lazy fox' and hit return: "
    console.put(cout)
    cin = b''
    while not cin:
        cin = console.get(bs=8)

    console.put(b"You typed: " + cin + b'\n')
    assert len(cin) > 8
    assert cin ==  b'the lazy fox'
    assert len(console.rxbs) == 0
    console.close()

    """End Test"""


if __name__ == "__main__":
    test_console()
