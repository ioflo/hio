# -*- encoding: utf-8 -*-
"""
tests.core.test_doing module

"""
import pytest

import os
import sys
import inspect
import types

from hio.base import tyming
from hio.base import doing, multidoing, Doist
from hio.base.doing import ExDoer
from hio.help import helping


def test_multidoer():
    """
    Test MultiDoer class
    """
    doist = doing.Doist(tock=0.25)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == 0.25
    assert doist.real == False
    assert doist.limit == None
    assert doist.doers == []

    doer0 = multidoing.MultiDoer(tock=0.25, tymth=doist.tymen())
    doer1 = multidoing.MultiDoer(tock=0.5, tymth=doist.tymen())
    doers = [doer0, doer1]

    doist.doers = doers
    doist.enter()
    assert len(doist.deeds) == 2
    assert [val[1] for val in doist.deeds] == [0.0, 0.0]
    for doer in doers:
        assert doer.count == 0
        assert doer.done == False

    doist.recur()
    assert doist.tyme == 0.25  # on next cycle
    assert len(doist.deeds) == 2
    assert [val[1] for val in doist.deeds] == [0.25, 0.5]
    assert doer0.count == 1
    assert doer1.count == 1

    doist.recur()
    assert doist.tyme == 0.5  # on next cycle
    assert len(doist.deeds) == 2
    assert [val[1] for val in doist.deeds] == [0.5, 0.5]
    assert doer0.count == 2
    assert doer1.count == 1

    doist.recur()
    assert doist.tyme == 0.75  # on next cycle
    assert len(doist.deeds) == 2
    assert [val[1] for val in doist.deeds] == [0.75, 1.0]
    assert doer0.count == 3
    assert doer1.count == 2


    doist.recur()
    assert doist.tyme == 1.0  # on next cycle
    assert len(doist.deeds) == 1
    assert [val[1] for val in doist.deeds] == [1.0]
    assert doer0.count == 5
    assert doer1.count == 2
    assert doer0.done == True


    doist.recur()
    assert doist.tyme == 1.25  # on next cycle
    assert len(doist.deeds) == 1
    assert doer0.count == 5
    assert doer1.count == 3


    doist.recur()
    assert doist.tyme == 1.50  # on next cycle
    assert len(doist.deeds) == 1
    assert doer0.count == 5
    assert doer1.count == 3


    doist.recur()
    assert doist.tyme == 1.75  # on next cycle
    assert len(doist.deeds) == 0
    assert doer0.count == 5
    assert doer1.count == 5
    assert doer1.done == True

    """Done Test """


if __name__ == "__main__":
    test_multidoer()
