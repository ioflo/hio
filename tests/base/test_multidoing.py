# -*- encoding: utf-8 -*-
"""
tests.base.test_multidoing module

"""
import platform

import pytest

import os
import sys
import time
import inspect
import types
import logging
import json

from dataclasses import dataclass, astuple, asdict, field

from hio.help import helping
from hio.help.doming import datify, dictify
from hio.base import tyming
from hio.base import doing, multidoing, Doist
from hio.base.doing import ExDoer
from hio.base.multidoing import Bosser, Crewer, ogler, EndDom, TagDex, Retag

# Any subprocess started by this modules __main__ will inherit this module scope.
# Therefore Doist or Doers that reference this ogler will get a picked copy of it.
# The suprocess scope than then change copied ogler.level, ogler.temp and run
# ogler.reopen with or without temp parameter to reopen log file
ogler.level = logging.DEBUG  # using multidoing ogler
ogler.temp = True  # for testing set to True
#ogler.reopen()
logger = ogler.getLogger(name='test')


def test_retag_regex():
    """Test Retag regex for detecting tag value of JSON serialized memo"""

    memo = '{"tag":"REG","name":"boss","load":{}}'
    match = Retag.match(memo)
    assert match
    assert match is not None
    assert "REG" == match.group(1)
    assert "REG" == match.group("tag")

    if match := Retag.match(memo):
        assert match.group("tag") == "REG"
    else:
        assert False

    memo = ''
    match = Retag.match(memo)
    assert not match
    assert match is None

    memo = '123#$'
    match = Retag.match(memo)
    assert not match
    assert match is None

    with pytest.raises(AttributeError):
        tag = Retag.match(memo).group("tag")

    memo = '{"tag": "REG", "name": "boss", "load": {}}'
    with pytest.raises(AttributeError):
        tag = Retag.match(memo).group("tag")

    if not (match := Retag.match(memo)):
        tag = None
    else:
        tag = match.group("tag")

    assert tag is None


    memo = '{"tag": "reg", "name": "boss", "load": {}}'
    with pytest.raises(AttributeError):
        tag = Retag.match(memo).group("tag")

    memo = '{"tag":"A", "name": "boss", "load": {}}'
    assert Retag.match(memo).group("tag") == 'A'

    memo = '{"tag":"AB", "name": "boss", "load": {}}'
    assert Retag.match(memo).group("tag") == 'AB'

    memo = '{"tag":"ABC", "name": "boss", "load": {}}'
    assert Retag.match(memo).group("tag") == 'ABC'

    memo = '{"tag":"ABCD", "name": "boss", "load": {}}'
    assert Retag.match(memo).group("tag") == 'ABCD'

    # test memo with correct tag but malformed fields
    memo = '{"tag":"REG", "alias": "boss", "load": {}}'
    tag = Retag.match(memo).group("tag")
    assert tag in TagDex
    with pytest.raises(ValueError):
        mdom = TagDex[tag]._fromjson(memo)


    """Done Test"""


def test_memo_doms():
    """Test dataclass Doms used for memos"""
    # Test MemoDom
    memodom = multidoing.MemoDom()
    assert memodom.tag == 'REG'
    assert memodom.name == 'hand'
    assert memodom.load == {}

    d = dictify(memodom)
    assert datify(multidoing.MemoDom, d) == memodom

    d = memodom._asdict()
    assert d == {'tag': 'REG', 'name': 'hand', 'load': {}}

    md = multidoing.MemoDom._fromdict(d)
    assert md == memodom

    # Test RegDom
    regdom = multidoing.RegDom()
    assert regdom.tag == 'REG'
    assert regdom.name == 'hand'
    assert regdom.load == {}

    d = dictify(regdom)
    assert datify(multidoing.RegDom, d) == regdom

    d = regdom._asdict()
    assert d == {'tag': 'REG', 'name': 'hand', 'load': {}}

    rd = multidoing.RegDom._fromdict(d)
    assert rd == regdom

    # Test AckDom
    ackdom = multidoing.AckDom()
    assert ackdom.tag == 'ACK'
    assert ackdom.name == 'boss'
    assert ackdom.load == multidoing.AddrDom(tag='REG', name='hand', addr='')

    d = ackdom._asdict()
    assert d == {'tag': 'ACK', 'name': 'boss', 'load':
                 {'tag': 'REG', 'name': 'hand', 'addr': ''}}

    ad = multidoing.AckDom._fromdict(d)
    assert ad == ackdom

    # Test AddrDom
    addrdom = multidoing.AddrDom(tag='REG', name='hand', addr='myaddress')
    assert addrdom.tag == 'REG'
    assert addrdom.name == 'hand'
    assert addrdom.addr == 'myaddress'
    d = addrdom._asdict()
    assert d == { 'tag': 'REG', 'name': 'hand','addr': 'myaddress'}

    add = multidoing.AddrDom._fromdict(d)
    assert add == addrdom

    ackdom = multidoing.AckDom(load=addrdom)
    assert ackdom.tag == 'ACK'
    assert ackdom.name == 'boss'
    assert ackdom.load == addrdom

    d = ackdom._asdict()
    assert d == {'tag': 'ACK', 'name': 'boss', 'load':
                 { 'tag': 'REG', 'name': 'hand', 'addr': 'myaddress'}}

    ad = multidoing.AckDom._fromdict(d)
    assert ad == ackdom

    # Test EndDom
    enddom = multidoing.EndDom()
    assert enddom.tag == 'END'
    assert enddom.name == 'boss'
    assert enddom.load == {}

    d = dictify(enddom)
    assert datify(multidoing.EndDom, d) == enddom

    d = enddom._asdict()
    assert d == {'tag': 'END', 'name': 'boss', 'load': {}}

    ed = multidoing.EndDom._fromdict(d)
    assert ed == enddom

    # Test BokDom
    bokdom = multidoing.BokDom()
    assert bokdom.tag == 'BOK'
    assert bokdom.name == 'boss'
    assert bokdom.load == {}

    d = dictify(bokdom)
    assert datify(multidoing.BokDom, d) == bokdom

    d = bokdom._asdict()
    assert d == { 'tag': 'BOK', 'name': 'boss', 'load': {}}

    bd = multidoing.BokDom._fromdict(d)
    assert bd == bokdom

    book = dict(hand0="hand0path", hand1="hand1path", hand2="hand2path")

    bokdom = multidoing.BokDom(name='bossy', load=book)
    assert bokdom.tag == 'BOK'
    assert bokdom.name == 'bossy'
    assert bokdom.load == book

    d = dictify(bokdom)
    assert datify(multidoing.BokDom, d) == bokdom

    d = bokdom._asdict()
    assert d == {'tag': 'BOK', 'name': 'bossy', 'load':
                 {
                    'hand0': 'hand0path',
                    'hand1': 'hand1path',
                    'hand2': 'hand2path'
                 }
                }

    bd = multidoing.BokDom._fromdict(d)
    assert bd == bokdom

    # test TagDex
    assert isinstance(multidoing.TagDex, multidoing.TagDomCodex)

    assert 'REG' in multidoing.TagDex
    assert multidoing.TagDex.REG == multidoing.RegDom

    assert asdict(multidoing.TagDex) == {
        'REG': multidoing.RegDom,
        'ACK': multidoing.AckDom,
        'END': multidoing.EndDom,
        'BOK': multidoing.BokDom,
    }

    dom = multidoing.RegDom(name='testy')
    memo = dom._asjson()
    assert memo == b'{"tag":"REG","name":"testy","load":{}}'
    memo = memo.decode()  # make str from bytes
    tag = multidoing.Retag.match(memo).group("tag")
    assert tag == 'REG'
    assert tag in multidoing.TagDex

    rdom = getattr(multidoing.TagDex, tag)._fromjson(memo)
    assert rdom == dom

    d = json.loads(memo)
    rdom = getattr(multidoing.TagDex, tag)(**d)
    assert rdom == dom

    assert multidoing.TagDex['REG'] == multidoing.RegDom
    assert multidoing.TagDex['ACK'] == multidoing.AckDom
    assert multidoing.TagDex['END'] == multidoing.EndDom
    assert multidoing.TagDex['BOK'] == multidoing.BokDom


    mdoer = multidoing.MultiDoerBase()
    assert mdoer.Tagex == multidoing.TagDex

    """Done test"""



def test_boss_crew_basic():
    """Test Bosser and Crewer classes basic. Crew doist exit at doist time limit
    which causes boss doer to exit done true because no active children
    """

    if platform.system() == 'Windows':
        pytest.skip("Windows not supported")

    logger.debug("***** Basic Boss Crew Test *****")
    name = 'hand'  # crew hand name
    crewdoer = Crewer(tock=0.01)  # don't assign tymth now must be rewound inside subprocess
    # crew doist load
    load = dict(name=name, tyme=0.0, tock=0.01, real=True, limit=0.08, doers=[crewdoer], temp=True, boss=None)

    doer = Bosser(name="boss", tock=0.01, loads=[load])
    assert doer.loads[0] == load
    assert not doer.opened
    doers = [doer]

    doist = doing.Doist(tock=0.01, real=True, limit=3.0, doers=doers, temp=True)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == 0.01
    assert doist.real == True
    assert doist.limit == 3.0
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
    Test Bosser and Crewer classes with multiple crew hands.
    Each Crew doist exits at doist time limit which causes boss doer to exit
    done true once all exit because no active children
    """

    if platform.system() == 'Windows':
        pytest.skip("Windows not supported")

    logger.debug("***** Basic Boss with Multi Crew Test *****")
    loads = []

    name = 'hand0'  # crew doista and crew hand doer name
    crewdoer = Crewer(tock=0.01)  # don't assign tymth now must be rewound inside subprocess
    # crew doist load
    load = dict(name=name, tyme=0.0, tock=0.01, real=True, limit=0.08, doers=[crewdoer], temp=True, boss=None)
    loads.append(load)

    name = 'hand1'  # crew doista and crew hand doer name
    crewdoer = Crewer(tock=0.01)  # don't assign tymth now must be rewound inside subprocess
    # crew doist load
    load = dict(name=name, tyme=0.0, tock=0.01, real=True, limit=0.08, doers=[crewdoer], temp=True, boss=None)
    loads.append(load)

    name = 'hand3'  # crew doista and crew hand doer name
    crewdoer = Crewer(tock=0.01)  # don't assign tymth now must be rewound inside subprocess
    # crew doist load
    load = dict(name=name, tyme=0.0, tock=0.01, real=True, limit=0.07, doers=[crewdoer], temp=True, boss=None)
    loads.append(load)

    name = 'hand4'  # crew doista and crew hand doer name
    crewdoer = Crewer(tock=0.01)  # don't assign tymth now must be rewound inside subprocess
    # crew doist load
    load = dict(name=name, tyme=0.0, tock=0.01, real=True, limit=0.07, doers=[crewdoer], temp=True, boss=None)
    loads.append(load)


    doer = Bosser(name="boss", tock=0.01, loads=loads)
    assert len(doer.loads) == 4
    assert not doer.opened
    doers = [doer]

    doist = doing.Doist(tock=0.01, real=True, limit=3.0, doers=doers, temp=True)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == 0.01
    assert doist.real == True
    assert doist.limit == 3.0
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
    Test Bosser and Crewer with terminate SIGTERM. Boss doist exit at limit
    before crew doist exits at limit so Bosser calls proc.termintate() which
    sends SIGTERM to Crewer

    """

    if platform.system() == 'Windows':
        pytest.skip("Windows not supported")

    logger.debug("***** Boss Crew Terminate *****")
    name = 'hand'  # crew hand name
    crewdoer = Crewer(tock=0.01)  # don't assign tymth now must be rewound inside subprocess
    # crew doist load
    load = dict(name=name, tyme=0.0, tock=0.01, real=True, limit=None, doers=[crewdoer], temp=True, boss=None)

    doer = Bosser(name="boss", tock=0.01, loads=[load])
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

class Test0Bosser(Bosser):
    """Bosser with custome recur for testing"""

    def __init__(self, **kwa):
        """Initialize instance."""
        super(Test0Bosser, self).__init__(**kwa)


    def recur(self, tyme):
        """Do 'recur' context."""
        done = super(Test0Bosser, self).recur(tyme=tyme)

        return done


class Test0Crewer(Crewer):
    """Crewer with custom recur for testing"""

    def __init__(self, **kwa):
        """Initialize instance."""
        super(Test0Crewer, self).__init__(**kwa)


    def recur(self, tyme):
        """Do 'recur' context."""
        done = super(Test0Crewer, self).recur(tyme=tyme)

        if self.registered:
            if tyme > self.tock * 3:
                self.logger.debug("Hand name=%s registered and done at tyme=%f.",
                              self.name, tyme)
                return True  # complete

        return False  # incomplete


def test_crewer_own_exit():
    """
    Test Bosser and Crewer where crew doer exits on own based on tyme after
    registered which causes boss doer to exit because no active children.
    """

    if platform.system() == 'Windows':
        pytest.skip("Windows not supported")

    logger.debug("***** Boss with Crew Own Exit *****")
    name = 'hand'  # crew hand name
    crewdoer = Test0Crewer(tock=0.01)  # don't assign tymth now must be rewound inside subprocess
    load = dict(name=name, tyme=0.0, tock=0.01, real=True, limit=None, doers=[crewdoer], temp=True, boss=None)

    doer = Test0Bosser(name="boss", tock=0.01, loads=[load])
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


class Test1Bosser(Bosser):
    """Bosser with custome recur for testing"""

    def __init__(self, **kwa):
        """Initialize instance."""
        super(Test1Bosser, self).__init__(**kwa)


    def recur(self, tyme):
        """Do 'recur' context."""
        done = super(Test1Bosser, self).recur(tyme=tyme)

        if self.crewed:
            if self.ctx.active_children():
                if tyme > 15 * self.tock:
                    for name, dom in self.crew.items():  # dom is CrewDom instance
                        memo = EndDom(name=self.name)._asjson().decode()
                        if dom.proc.is_alive() and not dom.exiting:
                            dst = self.getAddr(name=name)
                            self.memoit(memo, dst)
                            dom.exiting = True  # now exiting

            else:  # all crew hands completed
                return True

        return False  # incomplete recur again


class Test1Crewer(Crewer):
    """Crewer with custom recur for testing"""

    def __init__(self, **kwa):
        """Initialize instance."""
        super(Test1Crewer, self).__init__(**kwa)


    def recur(self, tyme):
        """Do 'recur' context."""
        done = super(Test1Crewer, self).recur(tyme=tyme)

        if self.registered:
            self.logger.debug("Hand name=%s registered at tyme=%f.",
                              self.name, tyme)


        return False  # incomplete


def test_boss_crew_memo_cmd_end():
    """
    Test Bosser and Crewer where boss sends memo to command end of crew.
    """

    if platform.system() == 'Windows':
        pytest.skip("Windows not supported")

    logger.debug("***** Boss Send Memo END Command Test *****")
    name = 'hand'  # crew hand name
    crewdoer = Test1Crewer(tock=0.01)  # don't assign tymth now must be rewound inside subprocess
    load = dict(name=name, tyme=0.0, tock=0.01, real=True, limit=None, doers=[crewdoer], temp=True, boss=None)

    doer = Test1Bosser(name="boss", tock=0.01, loads=[load])
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


if __name__ == "__main__":
    test_retag_regex()
    test_memo_doms()
    test_boss_crew_basic()
    test_boss_crew_basic_multi()
    test_boss_crew_terminate()
    test_crewer_own_exit()
    test_boss_crew_memo_cmd_end()


