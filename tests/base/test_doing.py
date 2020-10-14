# -*- encoding: utf-8 -*-
"""
tests.core.test_doing module

"""
import pytest

from hio.base.basing import Ctl, Sts
from hio.base.doing import Doer
from hio.base import cycling

def test_doer():
    """
    Test Doer class
    """
    doer = Doer()
    assert isinstance(doer.cycler, cycling.Cycler)
    assert doer.cycler.tyme == 0.0
    assert doer.tock == 0.0
    assert doer.desire == Ctl.exit
    assert doer.status == Sts.exited
    assert doer.done == True

    try:
        status = doer.do(Ctl.recur)
        assert status == Sts.recurring
        assert doer.status == status == Sts.recurring
        assert doer.done == False
        assert doer.desire == Ctl.exit
        status = doer.do(doer.desire)
        assert status == Sts.exited
        assert doer.status == status == Sts.exited
        assert doer.done == True
        assert doer.desire == Ctl.exit
        status = doer.do(doer.desire)
        assert status == Sts.exited
        assert doer.status == status == Sts.exited
        assert doer.done == True
        assert doer.desire == Ctl.exit

    except StopIteration:
        pass



    """End Test """



if __name__ == "__main__":
    test_doer()
