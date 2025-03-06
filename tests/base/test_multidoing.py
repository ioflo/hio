# -*- encoding: utf-8 -*-
"""
tests.core.test_doing module

"""
import pytest

import os
import sys
import time
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
#ogler.reopen()
logger = ogler.getLogger(name='test')



def test_boss_crew_basic():
    """
    Test BossDoer and CrewDoer classes basic
    """
    logger.debug("***** Basic  Boss Doist Test *****")
    name = 'hand'  # crew hand name
    crewdoer = CrewDoer(tock=0.05)  # don't assign tymth now must be rewound inside subprocess
    load = dict(name=name, tyme=0.0, tock=0.01, real=True, limit=None, doers=[crewdoer], temp=True, boss=None)

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

    logger.debug("Boss doist done=%s at tyme=%f.", doist.done, doist.tyme)
    assert doist.done
    assert len(doist.deeds) == 0
    assert doer.done == True
    assert not doer.opened
    assert doer.logger

    # Verify changes to ogler in child subprocesses not affect parent ogler
    from hio.help import ogler
    assert ogler.prefix == "hio"
    assert ogler.name == "main"
    assert ogler.level == logging.CRITICAL
    assert not ogler.opened
    assert not ogler.path


    """Done Test """


#def test_boss_crew_stepped():
    #"""
    #Test BossDoer and CrewDoer classes basic
    #"""
    #logger.debug("***** Stepped Boss Doist Test *****")

    #tock = 0.01
    #doist = doing.Doist(tock=tock, real=True, temp=True)
    #assert doist.tyme == 0.0  # on next cycle
    #assert doist.tock == tock
    #assert doist.real == True
    #assert doist.limit == None
    #assert doist.doers == []

    #crewdoer = CrewDoer(tock=0.05, name='hand')  # don't assign tymth now must be rewound inside subprocess
    #load = dict(name='crew', tyme=0.0, tock=0.01, real=True, limit=None, doers=[crewdoer], temp=True, boss=None)

    #doer = BossDoer(name="boss", tock=0.01, tymth=doist.tymen(), loads=[load])
    #assert doer.loads[0] == load
    #doers = [doer]

    #doist.doers = doers
    #doist.done = False  # setup before enter
    #doist.enter(temp=True)  # since we don't call doist.do temp does not get injected
    #assert len(doist.deeds) == 1
    #assert doer.opened
    #assert doer.done == False
    #assert doer.crew
    #assert doer.logger
    #assert hasattr(doer, "addrByName")

    #doist.timer.start()
    #tymer = tyming.Tymer(tymth=doist.tymen(), duration=doist.limit)
    #while True:  # until doers complete or exception or keyboardInterrupt
        #try:
            #doist.recur()  # increments .tyme runs recur context

            #if doist.real:  # wait for real time to expire
                #while not doist.timer.expired:
                    #time.sleep(max(0.0, doist.timer.remaining))
                #doist.timer.restart()  #  no time lost

            #if not doist.deeds:  # no deeds
                #doist.done = True
                #break  # break out of forever loop

            #if doist.limit and tymer.expired:  # reached limit before all deeds done
                #break  # break out of forever loop

        #except KeyboardInterrupt:  # Forced shutdown due to SIGINT, use CNTL-C to shutdown from shell
            #break

        #except SystemExit: # Forced shutdown of process via sys.exit()
            #raise

        #except Exception:  # Forced shutdown due to uncaught exception
            #raise

        #finally: # finally clause always runs regardless of exception or not.
            #doist.exit()  # force close remaining deeds throws GeneratorExit

    #logger.debug("Boss doist done=%s at tyme=%f.", doist.done, doist.tyme)
    #assert doist.done
    #assert len(doist.deeds) == 0
    #assert not doer.opened
    #assert doer.done == True
    #assert doer.getAddr(name="hand")

    ## Verify changes to ogler in child subprocesses not affect parent ogler
    #from hio.help import ogler
    #assert ogler.prefix == "hio"
    #assert ogler.name == "main"
    #assert ogler.level == logging.CRITICAL
    #assert not ogler.opened
    #assert not ogler.path

    #"FileNotFoundError same as ENOENT"

    #"""Done Test """



if __name__ == "__main__":
    test_boss_crew_basic()
    #test_boss_crew_stepped()
