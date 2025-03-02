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
from hio.base.multidoing import BossDoer, CrewDoer



def test_boss_crew_basic():
    """
    Test BossDoer and CrewDoer classes basic
    """
    doist = doing.Doist(tock=0.01, real=True)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == 0.01
    assert doist.real == True
    assert doist.limit == None
    assert doist.doers == []

    exdoer = ExDoer(tock=0.05)  # don't assign tymth now must be rewound inside subprocess
    load = dict(name='TestCrew0', tyme=0.0, tock=0.01, real=True, limit=None, doers=[exdoer], temp=True)

    doer = BossDoer(name="TestBoss", tock=0.01, tymth=doist.tymen(), loads=[load])
    assert doer.loads[0] == load
    doers = [doer]

    doist.doers = doers
    doist.enter()
    assert len(doist.deeds) == 1
    assert doer.count == 0
    assert doer.done == False
    assert doer.tots

    doist.recur()
    assert doist.tyme == 0.01  # on next cycle
    assert len(doist.deeds) == 1
    assert doer.count == 1

    while not doer.done:
        doist.recur()


    assert len(doist.deeds) == 0
    assert doer.done == True

    # Verify changes to ogler in child subprocesses not affect parent ogler
    from hio.help import ogler
    assert ogler.prefix == "hio"
    assert ogler.name == "main"
    assert ogler.level == logging.CRITICAL
    assert not ogler.opened
    assert not ogler.path


    """Done Test """


if __name__ == "__main__":
    test_boss_crew_basic()
