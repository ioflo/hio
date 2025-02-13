# -*- encoding: utf-8 -*-
"""
tests.help.test_naming module

"""
import pytest

from hio import hioing
from hio.help import Namer

def test_namer():
    """
    Test Namer class
    """
    namer = Namer()
    assert not namer.addrByName
    assert not namer.nameByAddr

    assert namer.addEntry("alpha", "/path/to/alpha")
    assert namer.addEntry("beta", "/path/to/beta")
    assert namer.addEntry("gamma", "/path/to/gamma")
    assert not namer.addEntry("gamma", "/path/to/gamma")  # already added

    assert namer.addrByName == {'alpha': '/path/to/alpha',
                                'beta': '/path/to/beta',
                                'gamma': '/path/to/gamma'}

    assert namer.nameByAddr == {'/path/to/alpha': 'alpha',
                                '/path/to/beta': 'beta',
                                '/path/to/gamma': 'gamma'}

    with pytest.raises(hioing.NamerError):
        namer.addEntry("", "")

    with pytest.raises(hioing.NamerError):
        namer.addEntry("delta", "")

    with pytest.raises(hioing.NamerError):
        namer.addEntry("", "/path/to/delta")

    with pytest.raises(hioing.NamerError):
        namer.addEntry("delta", "/path/to/alpha")

    with pytest.raises(hioing.NamerError):
        namer.addEntry("alpha", "/path/to/delta")

    assert namer.addEntry("delta", "/path/to/delta")

    assert namer.addrByName == {'alpha': '/path/to/alpha',
                                'beta': '/path/to/beta',
                                'gamma': '/path/to/gamma',
                                'delta': '/path/to/delta'}


    assert namer.nameByAddr == {'/path/to/alpha': 'alpha',
                                '/path/to/beta': 'beta',
                                '/path/to/gamma': 'gamma',
                                '/path/to/delta': 'delta'}

    assert not namer.remEntry(name="delta", addr="/path/to/alpha")

    assert namer.remEntry(name="delta", addr="/path/to/delta")
    assert not namer.remEntry(name="delta", addr="/path/to/delta")
    assert not namer.remEntry(name="delta")
    assert not namer.remEntry(addr="/path/to/delta")

    assert namer.remEntry(name="gamma")
    assert namer.remEntry(addr="/path/to/beta")

    assert namer.addrByName == {'alpha': '/path/to/alpha'}

    assert namer.nameByAddr == {'/path/to/alpha': 'alpha'}

    assert namer.addEntry("beta", "/path/to/beta")
    assert namer.addEntry("gamma", "/path/to/gamma")
    assert namer.addEntry("delta", "/path/to/delta")

    assert not namer.changeAddrAtName(name='alpha', addr="/path/to/alpha")
    assert namer.changeAddrAtName(name='alpha', addr="/alt/path/to/alpha")
    assert not namer.changeNameAtAddr(addr="/path/to/alpha", name="alphaneo")
    assert not namer.changeAddrAtName(name='alphaneo', addr="/path/to/alpha")
    with pytest.raises(hioing.NamerError):
        assert namer.changeAddrAtName(name='alpha', addr="/path/to/beta")

    assert not namer.changeNameAtAddr(addr="/path/to/beta", name='beta')
    assert namer.changeNameAtAddr(addr="/path/to/beta", name='betaneo')
    assert not namer.changeAddrAtName(name="beta", addr="/alt/path/to/beta")
    assert not namer.changeNameAtAddr(addr="/alt/path/to/beta", name='beta')
    with pytest.raises(hioing.NamerError):
        assert namer.changeNameAtAddr(addr="/path/to/beta", name='delta')


    assert namer.addrByName == {'alpha': '/alt/path/to/alpha',
                                'gamma': '/path/to/gamma',
                                'delta': '/path/to/delta',
                                'betaneo': '/path/to/beta'}


    assert namer.nameByAddr == {'/path/to/beta': 'betaneo',
                                '/path/to/gamma': 'gamma',
                                '/path/to/delta': 'delta',
                                '/alt/path/to/alpha': 'alpha'}

    namer.clearEntries()
    assert not namer.addrByName
    assert not namer.nameByAddr



    """End Test"""


if __name__ == "__main__":
    test_namer()

