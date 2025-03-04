# -*- encoding: utf-8 -*-
"""
tests.core.test_doing module

"""
import pytest

import os
import sys
import inspect
import types
import logging

from hio.help import helping
from hio.base import tyming
from hio.base import doing, multidoing, Doist
from hio.base.doing import ExDoer
from hio.base.multidoing import BossDoer, CrewDoer, ogler

# Any subprocess started by this modules __main__ will inherit this module scope.
# Therefore Doist or Doers that reference this ogler will get a picked copy of it.
# The suprocess scope than then change copied ogler.level, ogler.temp and run
# ogler.reopen with or without temp parameter to reopen log file
ogler.level = logging.DEBUG  # using multidoing ogler
ogler.temp = True  # for testing set to True
ogler.reopen()
logger = ogler.getLogger(name='test')


def test_boss_crew_stepped():
    """
    Test BossDoer and CrewDoer classes basic
    """
    logger.debug("***** Stepped Boss Doist Test *****")


    doist = doing.Doist(tock=0.01, real=True, temp=True)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == 0.01
    assert doist.real == True
    assert doist.limit == None
    assert doist.doers == []

    crewdoer = CrewDoer(tock=0.05, name='hand')  # don't assign tymth now must be rewound inside subprocess
    load = dict(name='crew', tyme=0.0, tock=0.01, real=True, limit=None, doers=[crewdoer], temp=True, boss=None)

    doer = BossDoer(name="boss", tock=0.01, tymth=doist.tymen(), loads=[load])
    assert doer.loads[0] == load
    doers = [doer]



    doist.doers = doers
    doist.enter(temp=True)  # since we don't call doist.do temp does not get injected
    assert len(doist.deeds) == 1
    assert doer.opened
    assert doer.done == False
    assert doer.crew

    doist.recur()
    assert doist.tyme == 0.01  # on next cycle
    assert len(doist.deeds) == 1

    while not doer.done:
        doist.recur()


    assert len(doist.deeds) == 0
    assert not doer.opened
    assert doer.done == True

    # Verify changes to ogler in child subprocesses not affect parent ogler
    from hio.help import ogler
    assert ogler.prefix == "hio"
    assert ogler.name == "main"
    assert ogler.level == logging.CRITICAL
    assert not ogler.opened
    assert not ogler.path


    """Done Test """


def test_boss_crew_basic():
    """
    Test BossDoer and CrewDoer classes basic
    """
    logger.debug("***** Basic  Boss Doist Test *****")

    crewdoer = CrewDoer(name='hand', tock=0.05)  # don't assign tymth now must be rewound inside subprocess
    load = dict(name='crew', tyme=0.0, tock=0.01, real=True, limit=None, doers=[crewdoer], temp=True, boss=None)

    doer = BossDoer(name="boss", tock=0.01, loads=[load])
    assert doer.loads[0] == load
    assert not doer.opened
    doers = [doer]

    doist = doing.Doist(tock=0.01, real=True, doers=doers, temp=True)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == 0.01
    assert doist.real == True
    assert doist.limit == None
    assert doist.doers == [doer]

    doist.do()

    assert len(doist.deeds) == 0
    assert doer.done == True
    assert not doer.opened

    # Verify changes to ogler in child subprocesses not affect parent ogler
    from hio.help import ogler
    assert ogler.prefix == "hio"
    assert ogler.name == "main"
    assert ogler.level == logging.CRITICAL
    assert not ogler.opened
    assert not ogler.path


    """Done Test """


if __name__ == "__main__":
    test_boss_crew_stepped()
    test_boss_crew_basic()
