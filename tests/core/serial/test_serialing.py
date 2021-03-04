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
    assert console.bs == 256
    assert console.fd == None
    assert not console.opened
    assert len(console._line) == 0

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

    console.put(b"You typed: " + cin + b'\n')
    assert cin ==  b'hello'
    assert len(console._line) == 0

    console.close()

    # test small buffer stiches together full line
    result = console.reopen()
    if not result:  # only works on external console window in wingide
        return

    assert result
    assert console.opened
    assert console.fd

    cout = b"Enter 'the lazy fox' and hit return: "
    console.put(cout)
    cin = b''
    while not cin:
        cin = console.getLine(bs=8)

    console.put(b"You typed: " + cin + b'\n')
    assert len(cin) > 8
    assert cin ==  b'the lazy fox'
    assert len(console._line) == 0
    console.close()

    """End Test"""


def test_consoleserver():
    """
    Tests ConsoleServer class

    Must configure Debug I/O to use external console window.
    """
    server = serialing.ConsoleServer()
    assert server.bs == 256
    assert server.fd == None
    assert not server.opened
    assert len(server._line) == 0
    assert not server.puts
    assert not server.lines

    result = server.reopen()
    if not result:  # only works on external console window in wingide
        return

    assert result
    assert server.opened
    assert server.fd

    server.puts.extend(b"Enter 'hello' and hit return: ")

    while not server.lines:
        server.service()

    line = server.lines.popleft()
    assert  line ==  b'hello'
    server.puts.extend(b"You typed: " + line + b'\n')

    server.puts.extend(b"Enter 'the lazy fox' and hit return: ")
    while not server.lines:
        server.service()

    line = server.lines.popleft()
    assert line ==  b'the lazy fox'
    server.puts.extend(b"You typed: " + line + b'\n')

    server.close()


if __name__ == "__main__":
    test_consoleserver()
