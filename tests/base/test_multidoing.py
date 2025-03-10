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
import json

from hio.help import helping
from hio.help.helping import datify, dictify
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



def test_memo_doms():
    """Test dataclass Doms used for memos"""
    memodom = multidoing.MemoDom()
    assert memodom.name == 'hand'
    assert memodom.tag == 'REG'
    assert memodom.load == {}

    d = dictify(memodom)
    assert datify(multidoing.MemoDom, d) == memodom


    """Done test"""

def test_boss_crew_basic():
    """Test BossDoer and CrewDoer classes basic. Crew doist exit at doist time limit
    which causes boss doer to exit done true because no active children
    """
    logger.debug("***** Basic Boss Crew Test *****")
    name = 'hand'  # crew hand name
    crewdoer = CrewDoer(tock=0.01)  # don't assign tymth now must be rewound inside subprocess
    # crew doist load
    load = dict(name=name, tyme=0.0, tock=0.01, real=True, limit=0.08, doers=[crewdoer], temp=True, boss=None)

    doer = BossDoer(name="boss", tock=0.01, loads=[load])
    assert doer.loads[0] == load
    assert not doer.opened
    doers = [doer]

    doist = doing.Doist(tock=0.01, real=True, limit=0.50, doers=doers, temp=True)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == 0.01
    assert doist.real == True
    assert doist.limit == 0.50
    assert doist.doers == [doer]

    doist.do()

    logger.debug("Boss doist done=%s at tyme=%f.", doist.done, doist.tyme)
    assert doist.done  # ended because time limit of crew ended so crew is done
    assert doer.done  # exit due to crew done
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


def test_boss_crew_basic_multi():
    """
    Test BossDoer and CrewDoer classes with multiple crew hands.
    Each Crew doist exits at doist time limit which causes boss doer to exit
    done true once all exit because no active children
    """
    logger.debug("***** Basic Boss with Multi Crew Test *****")
    loads = []

    name = 'hand0'  # crew doista and crew hand doer name
    crewdoer = CrewDoer(tock=0.01)  # don't assign tymth now must be rewound inside subprocess
    # crew doist load
    load = dict(name=name, tyme=0.0, tock=0.01, real=True, limit=0.08, doers=[crewdoer], temp=True, boss=None)
    loads.append(load)

    name = 'hand1'  # crew doista and crew hand doer name
    crewdoer = CrewDoer(tock=0.01)  # don't assign tymth now must be rewound inside subprocess
    # crew doist load
    load = dict(name=name, tyme=0.0, tock=0.01, real=True, limit=0.08, doers=[crewdoer], temp=True, boss=None)
    loads.append(load)

    name = 'hand3'  # crew doista and crew hand doer name
    crewdoer = CrewDoer(tock=0.01)  # don't assign tymth now must be rewound inside subprocess
    # crew doist load
    load = dict(name=name, tyme=0.0, tock=0.01, real=True, limit=0.07, doers=[crewdoer], temp=True, boss=None)
    loads.append(load)

    name = 'hand4'  # crew doista and crew hand doer name
    crewdoer = CrewDoer(tock=0.01)  # don't assign tymth now must be rewound inside subprocess
    # crew doist load
    load = dict(name=name, tyme=0.0, tock=0.01, real=True, limit=0.07, doers=[crewdoer], temp=True, boss=None)
    loads.append(load)


    doer = BossDoer(name="boss", tock=0.01, loads=loads)
    assert len(doer.loads) == 4
    assert not doer.opened
    doers = [doer]

    doist = doing.Doist(tock=0.01, real=True, limit=0.50, doers=doers, temp=True)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == 0.01
    assert doist.real == True
    assert doist.limit == 0.50
    assert doist.doers == [doer]

    doist.do()

    logger.debug("Boss doist done=%s at tyme=%f.", doist.done, doist.tyme)
    assert doist.done  # ended because time limit of crew ended so crew is done
    assert doer.done  # exit due to crew done
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


def test_boss_crew_terminate():
    """
    Test BossDoer and CrewDoer with terminate SIGTERM. Boss doist exit at limit
    before crew doist exits at limit so BossDoer calls proc.termintate() which
    sends SIGTERM to CrewDoer

    """
    logger.debug("***** Boss Crew Terminate *****")
    name = 'hand'  # crew hand name
    crewdoer = CrewDoer(tock=0.01)  # don't assign tymth now must be rewound inside subprocess
    # crew doist load
    load = dict(name=name, tyme=0.0, tock=0.01, real=True, limit=None, doers=[crewdoer], temp=True, boss=None)

    doer = BossDoer(name="boss", tock=0.01, loads=[load])
    assert doer.loads[0] == load
    assert not doer.opened
    doers = [doer]

    doist = doing.Doist(tock=0.01, real=True, limit=0.24, doers=doers, temp=True)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == 0.01
    assert doist.real == True
    assert doist.limit == 0.24
    assert doist.doers == [doer]

    doist.do()

    logger.debug("Boss doist done=%s at tyme=%f.", doist.done, doist.tyme)
    assert not doist.done  # ended because time limit of boss ended before crew done
    assert not doer.done  # exit due to terminate before done
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

class Test0BossDoer(BossDoer):
    """BossDoer with custome recur for testing"""

    def __init__(self, **kwa):
        """Initialize instance."""
        super(Test0BossDoer, self).__init__(**kwa)


    def recur(self, tyme):
        """Do 'recur' context."""
        done = super(Test0BossDoer, self).recur(tyme=tyme)

        return done


class Test0CrewDoer(CrewDoer):
    """CrewDoer with custom recur for testing"""

    def __init__(self, **kwa):
        """Initialize instance."""
        super(Test0CrewDoer, self).__init__(**kwa)


    def recur(self, tyme):
        """Do 'recur' context."""
        done = super(Test0CrewDoer, self).recur(tyme=tyme)

        if self.registered:
            if tyme > self.tock * 3:
                self.logger.debug("Hand name=%s registered and done at tyme=%f.",
                              self.name, tyme)
                return True  # complete

        return False  # incomplete


def test_crewdoer_own_exit():
    """
    Test BossDoer and CrewDoer where crew doer exits on own based on tyme after
    registered which causes boss doer to exit because no active children.
    """

    logger.debug("***** Boss with Crew Own Exit *****")
    name = 'hand'  # crew hand name
    crewdoer = Test0CrewDoer(tock=0.01)  # don't assign tymth now must be rewound inside subprocess
    load = dict(name=name, tyme=0.0, tock=0.01, real=True, limit=None, doers=[crewdoer], temp=True, boss=None)

    doer = Test0BossDoer(name="boss", tock=0.01, loads=[load])
    assert doer.loads[0] == load
    assert not doer.opened
    doers = [doer]

    doist = doing.Doist(tock=0.01, real=True, limit=None, doers=doers, temp=True)
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

class Test1BossDoer(BossDoer):
    """BossDoer with custome recur for testing"""

    def __init__(self, **kwa):
        """Initialize instance."""
        super(Test1BossDoer, self).__init__(**kwa)


    def recur(self, tyme):
        """Do 'recur' context."""
        done = super(Test1BossDoer, self).recur(tyme=tyme)

        if self.crewed:
            if self.ctx.active_children():
                if tyme > 15 * self.tock:
                    for name, dom in self.crew.items():  # dom is CrewDom instance
                        memo = dict(name=self.name, tag="END", load={})
                        memo = json.dumps(memo,separators=(",", ":"),ensure_ascii=False)
                        if dom.proc.is_alive() and not dom.exiting:
                            dst = self.getAddr(name=name)
                            self.memoit(memo, dst)
                            dom.exiting = True  # now exiting

            else:  # all crew hands completed
                return True


        return False  # incomplete recur again


class Test1CrewDoer(CrewDoer):
    """CrewDoer with custom recur for testing"""

    def __init__(self, **kwa):
        """Initialize instance."""
        super(Test1CrewDoer, self).__init__(**kwa)


    def recur(self, tyme):
        """Do 'recur' context."""
        done = super(Test1CrewDoer, self).recur(tyme=tyme)

        if self.registered:
            self.logger.debug("Hand name=%s registered at tyme=%f.",
                              self.name, tyme)


        return False  # incomplete


def test_boss_crew_memo_cmd_end():
    """
    Test BossDoer and CrewDoer where boss sends memo to command end of crew.
    """
    logger.debug("***** Boss Send Memo END Command Test *****")
    name = 'hand'  # crew hand name
    crewdoer = Test1CrewDoer(tock=0.01)  # don't assign tymth now must be rewound inside subprocess
    load = dict(name=name, tyme=0.0, tock=0.01, real=True, limit=None, doers=[crewdoer], temp=True, boss=None)

    doer = Test1BossDoer(name="boss", tock=0.01, loads=[load])
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




    """Done Test"""

if __name__ == "__main__":
    test_memo_doms()
    test_boss_crew_basic()
    test_boss_crew_basic_multi()
    test_boss_crew_terminate()
    test_crewdoer_own_exit()
    test_boss_crew_memo_cmd_end()


