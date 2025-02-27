# -*- encoding: utf-8 -*-
"""
tests.core.test_serialing module

"""
import pytest
import platform
import os
import sys
import time

from hio.base import doing
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
    if platform.system() != 'Windows':
        assert console.fd
    
    # Check isatty only on non-Windows platforms
    if platform.system() != 'Windows':
        assert os.isatty(console.fd)

    # On Windows we'd use msvcrt.putch for output
    cout = b"Enter 'hello' and hit return: "
    console.put(cout)
    
    # Give the user time to see the prompt and respond
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
    if platform.system() != 'Windows':
        assert console.fd
    
    # Check isatty only on non-Windows platforms
    if platform.system() != 'Windows':
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



def test_console_doer():
    """
    Test ConsoleDoer class

    Must run in WindIDE with Debug I/O configured as external console
    """
    tock = 0.03125
    ticks = 8
    limit = tock * ticks
    doist = doing.Doist(tock=tock, real=True, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == limit
    assert doist.doers == []

    console = serialing.Console()
    doer = serialing.ConsoleDoer(console=console)

    doers = [doer]
    doist.do(doers=doers)
    assert doist.tyme == limit
    assert console.opened == False



def test_echo_console():
    """
    Test EchoConsoleDoer class

    Must run in WingIDE with Debug I/O configured as external console
    """

    port = None  # Let the Console class handle platform-specific defaults
    
    try:  # check to see if running in external console
        console = serialing.Console()
        result = console.reopen()
        if not result:
            return  # not in external console
        console.close()
    except Exception as ex:
        # any error indicates we're not in the right environment
        pytest.skip(f"Not running in appropriate console environment: {str(ex)}")
        return

    tock = 0.03125
    ticks = 16
    limit = 0.0
    # limit = ticks *  tock
    doist = doing.Doist(tock=tock, real=True, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == 0.0
    # assert doist.limit == limit == 0.5
    assert doist.doers == []

    console = serialing.Console()
    echoer = serialing.EchoConsoleDoer(console=console)

    doers = [echoer]
    doist.do(doers=doers)
    # assert doist.tyme == limit
    assert console.opened == False


if __name__ == "__main__":
    test_console()
    test_echo_console()
