# -*- encoding: utf-8 -*-
"""
tests.core.test_wiring module

"""
import sys
import os
import tempfile
import shutil

import pytest

from hio.core import wiring


def test_openWL():
    """
    test contextmanager decorator openWL for WireLog files and WireLog
    """
    # test not filed and not same
    with wiring.openWL() as wl:  # default is temp = True
        assert isinstance(wl, wiring.WireLog)
        assert wl.rxed is True
        assert wl.txed is True
        assert wl.samed is False
        assert wl.filed is False
        assert wl.fmt == wl.Format == b'\n%(dx)s %(who)s:\n%(data)s\n'
        assert wl.name == "test"
        assert wl.temp == True
        assert wl.prefix == 'hio'
        assert wl.headDirPath == wl.HeadDirPath == "/usr/local/var"
        assert wl.dirPath is None  # filed == False
        assert not wl.rxl.closed
        assert not wl.txl.closed
        assert wl.opened

        wl.writeRx(data=b'ABCDEFG', who=b"bob")
        wl.writeTx(data=b'0123456', who=b"bob")
        wl.writeRx(data=b'ZYXWVU', who=b"eve")
        wl.writeTx(data=b'987654', who=b"eve")

        assert wl.readRx() == (b'\nrx bob:\nABCDEFG\n'
                               b'\nrx eve:\nZYXWVU\n')
        assert wl.readTx() == (b'\ntx bob:\n0123456\n'
                               b'\ntx eve:\n987654\n')

        wl.writeRx(data=b'HIJKLM', who=b"eve")
        wl.writeTx(data=b'789012', who=b"eve")
        wl.writeRx(data=b'TSRWPO', who=b"bob")
        wl.writeTx(data=b'321098', who=b"bob")

        assert wl.readRx() == (b'\nrx bob:\nABCDEFG\n'
                             b'\nrx eve:\nZYXWVU\n'
                             b'\nrx eve:\nHIJKLM\n'
                             b'\nrx bob:\nTSRWPO\n')
        assert wl.readTx() == (b'\ntx bob:\n0123456\n'
                               b'\ntx eve:\n987654\n'
                               b'\ntx eve:\n789012\n'
                               b'\ntx bob:\n321098\n')

    assert wl.rxl.closed
    assert wl.txl.closed
    assert not wl.opened

    # test not filed but samed
    with wiring.openWL(samed=True) as wl:  # default is temp = True
        assert isinstance(wl, wiring.WireLog)
        assert wl.rxed is True
        assert wl.txed is True
        assert wl.samed is True
        assert wl.filed is False
        assert wl.fmt == wl.Format == b'\n%(dx)s %(who)s:\n%(data)s\n'
        assert wl.name == "test"
        assert wl.temp == True
        assert wl.prefix == 'hio'
        assert wl.headDirPath == wl.HeadDirPath == "/usr/local/var"
        assert wl.dirPath is None  # filed == False
        assert not wl.rxl.closed
        assert not wl.txl.closed
        assert wl.rxl is wl.txl
        assert wl.opened

        wl.writeRx(data=b'ABCDEFG', who=b"bob")
        wl.writeTx(data=b'0123456', who=b"bob")
        wl.writeRx(data=b'ZYXWVU', who=b"eve")
        wl.writeTx(data=b'987654', who=b"eve")

        assert wl.readRx() == (b'\nrx bob:\nABCDEFG\n'
                               b'\ntx bob:\n0123456\n'
                               b'\nrx eve:\nZYXWVU\n'
                               b'\ntx eve:\n987654\n')
        assert wl.readTx() == (b'\nrx bob:\nABCDEFG\n'
                               b'\ntx bob:\n0123456\n'
                               b'\nrx eve:\nZYXWVU\n'
                               b'\ntx eve:\n987654\n')

        wl.writeRx(data=b'HIJKLM', who=b"eve")
        wl.writeTx(data=b'789012', who=b"eve")
        wl.writeRx(data=b'TSRWPO', who=b"bob")
        wl.writeTx(data=b'321098', who=b"bob")

        assert wl.readRx() == (b'\nrx bob:\nABCDEFG\n'
                               b'\ntx bob:\n0123456\n'
                               b'\nrx eve:\nZYXWVU\n'
                               b'\ntx eve:\n987654\n'
                               b'\nrx eve:\nHIJKLM\n'
                               b'\ntx eve:\n789012\n'
                               b'\nrx bob:\nTSRWPO\n'
                               b'\ntx bob:\n321098\n')
        assert wl.readTx() == (b'\nrx bob:\nABCDEFG\n'
                               b'\ntx bob:\n0123456\n'
                               b'\nrx eve:\nZYXWVU\n'
                               b'\ntx eve:\n987654\n'
                               b'\nrx eve:\nHIJKLM\n'
                               b'\ntx eve:\n789012\n'
                               b'\nrx bob:\nTSRWPO\n'
                               b'\ntx bob:\n321098\n')

    assert wl.rxl.closed
    assert wl.txl.closed
    assert not wl.opened

    # test filed and temp
    with wiring.openWL(filed=True) as wl:  # default is temp = True
        assert isinstance(wl, wiring.WireLog)
        assert wl.rxed is True
        assert wl.txed is True
        assert wl.samed is False
        assert wl.filed is True
        assert wl.fmt == wl.Format == b'\n%(dx)s %(who)s:\n%(data)s\n'
        assert wl.name == "test"
        assert wl.temp == True
        assert wl.prefix == 'hio'
        assert wl.headDirPath == wl.HeadDirPath == "/usr/local/var"
        assert os.path.exists(wl.dirPath)
        assert wl.dirPath.startswith("/tmp/hio/wire/log/test_")
        assert wl.dirPath.endswith("_temp")
        assert not wl.rxl.closed
        assert wl.rxl.name.endswith(".rx.log")
        assert not wl.txl.closed
        assert wl.txl.name.endswith(".tx.log")
        assert wl.opened

        wl.writeRx(data=b'ABCDEFG', who=b"bob")
        wl.writeTx(data=b'0123456', who=b"bob")
        wl.writeRx(data=b'ZYXWVU', who=b"eve")
        wl.writeTx(data=b'987654', who=b"eve")

        assert wl.readRx() == (b'\nrx bob:\nABCDEFG\n'
                               b'\nrx eve:\nZYXWVU\n')
        assert wl.readTx() == (b'\ntx bob:\n0123456\n'
                               b'\ntx eve:\n987654\n')

        wl.writeRx(data=b'HIJKLM', who=b"eve")
        wl.writeTx(data=b'789012', who=b"eve")
        wl.writeRx(data=b'TSRWPO', who=b"bob")
        wl.writeTx(data=b'321098', who=b"bob")

        assert wl.readRx() == (b'\nrx bob:\nABCDEFG\n'
                             b'\nrx eve:\nZYXWVU\n'
                             b'\nrx eve:\nHIJKLM\n'
                             b'\nrx bob:\nTSRWPO\n')
        assert wl.readTx() == (b'\ntx bob:\n0123456\n'
                               b'\ntx eve:\n987654\n'
                               b'\ntx eve:\n789012\n'
                               b'\ntx bob:\n321098\n')

    assert wl.rxl.closed
    assert wl.txl.closed
    assert not os.path.exists(wl.dirPath)
    assert not wl.opened

    # test filed and temp and samed
    with wiring.openWL(samed=True, filed=True) as wl:  # default is temp = True
        assert isinstance(wl, wiring.WireLog)
        assert wl.rxed is True
        assert wl.txed is True
        assert wl.samed is True
        assert wl.filed is True
        assert wl.fmt == wl.Format == b'\n%(dx)s %(who)s:\n%(data)s\n'
        assert wl.name == "test"
        assert wl.temp == True
        assert wl.prefix == 'hio'
        assert wl.headDirPath == wl.HeadDirPath == "/usr/local/var"
        assert os.path.exists(wl.dirPath)
        assert wl.dirPath.startswith("/tmp/hio/wire/log/test_")
        assert wl.dirPath.endswith("_temp")
        assert wl.rxl is wl.txl
        assert not wl.rxl.closed
        assert wl.rxl.name.endswith(".log")
        assert not wl.txl.closed
        assert wl.txl.name.endswith(".log")
        assert wl.opened

        wl.writeRx(data=b'ABCDEFG', who=b"bob")
        wl.writeTx(data=b'0123456', who=b"bob")
        wl.writeRx(data=b'ZYXWVU', who=b"eve")
        wl.writeTx(data=b'987654', who=b"eve")

        assert wl.readRx() == (b'\nrx bob:\nABCDEFG\n'
                               b'\ntx bob:\n0123456\n'
                               b'\nrx eve:\nZYXWVU\n'
                               b'\ntx eve:\n987654\n')
        assert wl.readTx() == (b'\nrx bob:\nABCDEFG\n'
                               b'\ntx bob:\n0123456\n'
                               b'\nrx eve:\nZYXWVU\n'
                               b'\ntx eve:\n987654\n')

        wl.writeRx(data=b'HIJKLM', who=b"eve")
        wl.writeTx(data=b'789012', who=b"eve")
        wl.writeRx(data=b'TSRWPO', who=b"bob")
        wl.writeTx(data=b'321098', who=b"bob")

        assert wl.readRx() == (b'\nrx bob:\nABCDEFG\n'
                               b'\ntx bob:\n0123456\n'
                               b'\nrx eve:\nZYXWVU\n'
                               b'\ntx eve:\n987654\n'
                               b'\nrx eve:\nHIJKLM\n'
                               b'\ntx eve:\n789012\n'
                               b'\nrx bob:\nTSRWPO\n'
                               b'\ntx bob:\n321098\n')
        assert wl.readTx() == (b'\nrx bob:\nABCDEFG\n'
                               b'\ntx bob:\n0123456\n'
                               b'\nrx eve:\nZYXWVU\n'
                               b'\ntx eve:\n987654\n'
                               b'\nrx eve:\nHIJKLM\n'
                               b'\ntx eve:\n789012\n'
                               b'\nrx bob:\nTSRWPO\n'
                               b'\ntx bob:\n321098\n')

    assert wl.rxl.closed
    assert wl.txl.closed
    assert not os.path.exists(wl.dirPath)
    assert not wl.opened

    # test filed but not temp
    with wiring.openWL(temp=False, filed=True) as wl:
        assert isinstance(wl, wiring.WireLog)
        assert wl.rxed is True
        assert wl.txed is True
        assert wl.samed is False
        assert wl.filed is True
        assert wl.fmt == wl.Format == b'\n%(dx)s %(who)s:\n%(data)s\n'
        assert wl.name == "test"
        assert wl.temp == False
        assert wl.prefix == 'hio'
        assert wl.headDirPath == wl.HeadDirPath == "/usr/local/var"
        assert os.path.exists(wl.dirPath)
        assert wl.dirPath == '/usr/local/var/hio/wire/log'
        assert not wl.rxl.closed
        assert wl.rxl.name.startswith('/usr/local/var/hio/wire/log/test.')
        assert wl.rxl.name.endswith('.rx.log')
        assert not wl.txl.closed
        assert wl.txl.name.startswith('/usr/local/var/hio/wire/log/test.')
        assert wl.txl.name.endswith('.tx.log')
        assert wl.opened

        wl.writeRx(data=b'ABCDEFG', who=b"bob")
        wl.writeTx(data=b'0123456', who=b"bob")
        wl.writeRx(data=b'ZYXWVU', who=b"eve")
        wl.writeTx(data=b'987654', who=b"eve")

        assert wl.readRx() == (b'\nrx bob:\nABCDEFG\n'
                               b'\nrx eve:\nZYXWVU\n')
        assert wl.readTx() == (b'\ntx bob:\n0123456\n'
                               b'\ntx eve:\n987654\n')

        wl.writeRx(data=b'HIJKLM', who=b"eve")
        wl.writeTx(data=b'789012', who=b"eve")
        wl.writeRx(data=b'TSRWPO', who=b"bob")
        wl.writeTx(data=b'321098', who=b"bob")

        assert wl.readRx() == (b'\nrx bob:\nABCDEFG\n'
                             b'\nrx eve:\nZYXWVU\n'
                             b'\nrx eve:\nHIJKLM\n'
                             b'\nrx bob:\nTSRWPO\n')
        assert wl.readTx() == (b'\ntx bob:\n0123456\n'
                               b'\ntx eve:\n987654\n'
                               b'\ntx eve:\n789012\n'
                               b'\ntx bob:\n321098\n')

        rxlpath = wl.rxl.name
        txlpath = wl.txl.name

    assert wl.rxl.closed
    assert wl.txl.closed
    assert os.path.exists(wl.dirPath)
    assert not wl.opened
    assert os.path.exists(rxlpath)
    os.remove(rxlpath)
    assert not os.path.exists(rxlpath)
    assert os.path.exists(txlpath)
    os.remove(txlpath)
    assert not os.path.exists(txlpath)

    # test filed but not temp and samed
    with wiring.openWL(temp=False, samed=True, filed=True, clear=True) as wl:
        assert isinstance(wl, wiring.WireLog)
        assert wl.rxed is True
        assert wl.txed is True
        assert wl.samed is True
        assert wl.filed is True
        assert wl.fmt == wl.Format == b'\n%(dx)s %(who)s:\n%(data)s\n'
        assert wl.name == "test"
        assert wl.temp == False
        assert wl.prefix == 'hio'
        assert wl.headDirPath == wl.HeadDirPath == "/usr/local/var"
        assert os.path.exists(wl.dirPath)
        assert wl.dirPath == '/usr/local/var/hio/wire/log'
        assert wl.rxl is wl.txl
        assert not wl.rxl.closed
        assert wl.rxl.name.startswith('/usr/local/var/hio/wire/log/test.')
        assert wl.rxl.name.endswith('.log')
        assert not wl.txl.closed
        assert wl.txl.name.startswith('/usr/local/var/hio/wire/log/test.')
        assert wl.txl.name.endswith('.log')
        assert wl.opened

        wl.writeRx(data=b'ABCDEFG', who=b"bob")
        wl.writeTx(data=b'0123456', who=b"bob")
        wl.writeRx(data=b'ZYXWVU', who=b"eve")
        wl.writeTx(data=b'987654', who=b"eve")

        assert wl.readRx() == (b'\nrx bob:\nABCDEFG\n'
                               b'\ntx bob:\n0123456\n'
                               b'\nrx eve:\nZYXWVU\n'
                               b'\ntx eve:\n987654\n')
        assert wl.readTx() == (b'\nrx bob:\nABCDEFG\n'
                               b'\ntx bob:\n0123456\n'
                               b'\nrx eve:\nZYXWVU\n'
                               b'\ntx eve:\n987654\n')

        wl.writeRx(data=b'HIJKLM', who=b"eve")
        wl.writeTx(data=b'789012', who=b"eve")
        wl.writeRx(data=b'TSRWPO', who=b"bob")
        wl.writeTx(data=b'321098', who=b"bob")

        assert wl.readRx() == (b'\nrx bob:\nABCDEFG\n'
                               b'\ntx bob:\n0123456\n'
                               b'\nrx eve:\nZYXWVU\n'
                               b'\ntx eve:\n987654\n'
                               b'\nrx eve:\nHIJKLM\n'
                               b'\ntx eve:\n789012\n'
                               b'\nrx bob:\nTSRWPO\n'
                               b'\ntx bob:\n321098\n')
        assert wl.readTx() == (b'\nrx bob:\nABCDEFG\n'
                               b'\ntx bob:\n0123456\n'
                               b'\nrx eve:\nZYXWVU\n'
                               b'\ntx eve:\n987654\n'
                               b'\nrx eve:\nHIJKLM\n'
                               b'\ntx eve:\n789012\n'
                               b'\nrx bob:\nTSRWPO\n'
                               b'\ntx bob:\n321098\n')

        lpath = wl.rxl.name

    assert wl.rxl.closed
    assert wl.txl.closed
    assert os.path.exists(wl.dirPath)
    assert not wl.opened
    assert os.path.exists(lpath)
    os.remove(lpath)
    assert not os.path.exists(lpath)
    """ End Test """




if __name__ == "__main__":
    test_openWL()
