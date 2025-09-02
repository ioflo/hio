# -*- encoding: utf-8 -*-
"""tests.base.hier.test_acting module

"""

import os
import platform
import tempfile
import inspect
from dataclasses import dataclass
from typing import Any, Type

import pytest

import hio
from hio.base import Doist, Tymist
from hio.base.hier import Nabes, Rules, Hog, openHog, HogDoer, Hold, Bag
from hio.help import TymeDom, namify, registerify
from hio.help.timing import nowIso8601  # timing so pytest mock nowIso8601 works


def test_hog_basic():
    """Test Hog class"""
    Hog._clearall()  # clear Hog.Instances for debugging

    # at some point could create utility function here that walks the .mro
    # hierachy using inspect to collect all the keyword args  to reserve them
    # and double check Hog.Reserved is correct
    # python how to get the keywords for given method signature including superclasses

    hog = Hog(temp=True)  # test defaults
    assert hog.temp
    assert hog.name == "Hog0"
    assert hog.opened
    assert hog.filed
    assert hog.extensioned
    assert hog.fext == 'hog'
    assert hog.file
    assert not hog.file.closed
    assert os.path.exists(hog.path)

    tempDirPath = (os.path.join(os.path.sep, "tmp")
                       if platform.system() == "Darwin"
                       else tempfile.gettempdir())
    tempDirPath = os.path.normpath(tempDirPath)
    path = os.path.normpath(hog.path)  # '/tmp/hio_u36wdtp5_test/hio/Hog1.hog'
    assert path.startswith(os.path.join(tempDirPath, "hio_"))
    assert hog.path.endswith(os.path.join('_test', 'hio', 'Hog0.hog'))

    assert Hog.Registry[Hog.__name__] is Hog
    assert Hog.Registry['log'] is Hog
    assert Hog.Registry['Log'] is Hog

    assert hog() == {}  # default returns iops
    assert hog.nabe == Nabes.afdo
    assert hog.hold
    assert not hog.hold.subery
    assert hog.hits == {}
    assert hog.header.startswith('rid')
    assert hog.rid.startswith(hog.name) # 'Hog0_KQzSlod5EfC1TvKsr0VvkQ'

    assert list(hog.hold.keys()) == ['_hold_subery']

    hog.close(clear=True)
    assert not hog.opened
    assert not hog.file
    assert not os.path.exists(hog.path)


    """Done Test"""


def test_open_hog():
    """Test openHog context manager"""
    Hog._clearall()  # clear Hog.Instances for debugging

    with openHog() as hog:  # test defaults
        assert hog.temp
        assert hog.name == "Hog0"
        assert hog.opened
        assert hog.filed
        assert hog.extensioned
        assert hog.fext == 'hog'
        assert hog.file
        assert not hog.file.closed
        assert os.path.exists(hog.path)

        tempDirPath = (os.path.join(os.path.sep, "tmp")
                           if platform.system() == "Darwin"
                           else tempfile.gettempdir())
        tempDirPath = os.path.normpath(tempDirPath)
        path = os.path.normpath(hog.path)  # '/tmp/hio_u36wdtp5_test/hio/Hog1.hog'
        assert path.startswith(os.path.join(tempDirPath, "hio_"))
        assert hog.path.endswith(os.path.join('_test', 'hio', 'Hog0.hog'))

        assert Hog.Registry[Hog.__name__] is Hog
        assert Hog.Registry['log'] is Hog
        assert Hog.Registry['Log'] is Hog

        assert hog() == {}  # default returns iops
        assert hog.nabe == Nabes.afdo
        assert hog.hold
        assert not hog.hold.subery
        assert hog.hits == {}
        assert hog.header.startswith('rid')

        assert list(hog.hold.keys()) == ['_hold_subery']

    assert not hog.opened
    assert not hog.file
    assert not os.path.exists(hog.path)

    """Done Test"""


def test_hog_doer():
    """Test HogDoer"""
    Hog._clearall()  # clear Hog.Instances for debugging

    # create two HogDoer instances and run them

    hog0 = Hog(name='test0', temp=True, reopen=False)
    assert hog0.temp
    assert hog0.name == "test0"
    assert not hog0.opened
    assert hog0.filed
    assert hog0.extensioned
    assert hog0.fext == 'hog'
    assert not hog0.file
    assert not hog0.path

    hogDoer0 = HogDoer(hog=hog0)
    assert hogDoer0.hog == hog0
    assert not hogDoer0.hog.opened

    hog1 = Hog(name='test1', temp=True, reopen=False)
    assert not hog1.opened
    assert not hog1.file
    assert not hog1.path

    hogDoer1 = HogDoer(hog=hog1)
    assert hogDoer1.hog == hog1
    assert not hogDoer1.hog.opened

    limit = 0.25
    tock = 0.03125
    doist = Doist(limit=limit, tock=tock)

    doers = [hogDoer0, hogDoer1]

    doist.doers = doers
    doist.enter()
    assert len(doist.deeds) == 2
    assert [val[1] for val in doist.deeds] == [0.0, 0.0]  #  retymes
    for doer in doers:
        assert doer.hog.opened
        assert doer.hog.file
        assert os.path.join('_test', 'hio', 'test') in doer.hog.path

    doist.recur()
    assert doist.tyme == 0.03125  # on next cycle
    assert len(doist.deeds) == 2
    for doer in doers:
        assert doer.hog.opened
        assert doer.hog.file

    for dog, retyme, index in doist.deeds:
        dog.close()

    for doer in doers:
        assert not doer.hog.opened
        assert not doer.hog.file
        assert not os.path.exists(doer.hog.path)


    # start over but not opened
    doist.tyme = 0.0
    doist.do(doers=doers)
    assert doist.tyme == limit
    for doer in doers:
        assert not doer.hog.opened
        assert not doer.hog.file
        assert not os.path.exists(doer.hog.path)

    """End Test"""


def test_hog_log(mockHelpingNowIso8601):
    """Test Hog clas with logging"""
    Hog._clearall()  # clear Hog.Instances for debugging

    @namify
    @registerify
    @dataclass
    class LocationBag(TymeDom):
        """Vector Bag dataclass

        Field Attributes:
            latN (Any):  latitude North fractional minutes
            lonE (Any):  longitude East fractional minutes
        """
        latN: Any = None
        lonE: Any = None

        def __hash__(self):
            """Define hash so can work with ordered_set
            __hash__ is not inheritable in dataclasses so must be explicitly defined
            in every subclass
            """
            return hash((self.__class__.__name__,) + self._astuple())  # almost same as __eq__



    # at some point could create utility function here that walks the .mro
    # hierachy using inspect to collect all the keyword args  to reserve them
    # and double check Hog.Reserved is correct
    # python how to get the keywords for given method signature including superclasses

    tymist = Tymist()

    dts = hio.help.timing.nowIso8601()  # mocked version testing that mocking worked
    assert dts == '2021-06-27T21:26:21.233257+00:00'


    boxerName = "BoxerTest"
    boxName = "BoxTop"
    iops = dict(_boxer=boxerName, _box=boxName)

    uid = 'KQzSlod5EfC1TvKsr0VvkQ'  # for test
    rid = f"{boxerName}_{uid}"

    hold = Hold()

    tymeKey = hold.tokey(("", "boxer", boxerName, "tyme"))
    hold[tymeKey] = Bag()
    hold[tymeKey].value = tymist.tyme

    activeKey = hold.tokey(("", "boxer", boxerName, "active"))
    hold[activeKey] = Bag()
    hold[activeKey].value = boxName

    tockKey = hold.tokey(("", "boxer", boxerName, "tock"))
    hold[tockKey] = Bag()
    hold[tockKey].value = tymist.tock

    tymth = tymist.tymen()
    for dom in hold.values():  # wind hold
        if isinstance(dom, TymeDom):
            dom._wind(tymth=tymth)

    name = "pig"

    # Test rule "every" default, when no hits logs box state as default hits
    hog = Hog(name=name, iops=iops, hold=hold, temp=True, rid=rid)  # test defaults
    assert hog.temp
    assert hog.name == name
    assert hog.iops == iops
    assert hog.nabe == Nabes.afdo
    assert hog.hold == hold

    assert hog.base == boxerName
    assert hog.opened
    assert hog.filed
    assert hog.extensioned
    assert hog.fext == 'hog'
    assert hog.file
    assert not hog.file.closed
    assert os.path.exists(hog.path)

    tempDirPath = (os.path.join(os.path.sep, "tmp")
                       if platform.system() == "Darwin"
                       else tempfile.gettempdir())
    tempDirPath = os.path.normpath(tempDirPath)
    path = os.path.normpath(hog.path)  # '/tmp/hio_u36wdtp5_test/hio/Hog1.hog'
    assert path.startswith(os.path.join(tempDirPath, "hio_"))
    assert hog.path.endswith(os.path.join('_test', 'hio', boxerName, f'{name}.hog'))

    assert Hog.Registry[Hog.__name__] is Hog
    assert Hog.Registry['log'] is Hog
    assert Hog.Registry['Log'] is Hog

    assert hog.rule == Rules.every
    assert not hog.started
    assert not hog.onced

    # run hog once
    assert hog() == iops  # default returns iops
    assert hog.nabe == Nabes.afdo
    assert hog.hold
    assert not hog.hold.subery
    assert hog.hits == \
    {
        'tyme': '_boxer_BoxerTest_tyme',
        'active': '_boxer_BoxerTest_active',
        'tock': '_boxer_BoxerTest_tock'
    }
    assert hog.started
    assert hog.onced
    assert hog.first == 0.0
    assert hog.last == 0.0
    assert hog.rid == rid
    assert hog.stamp == dts
    assert hog.header.startswith('rid')
    assert hog.header == ('rid\tbase\tname\tstamp\trule\tcount\n'
                    'BoxerTest_KQzSlod5EfC1TvKsr0VvkQ\tBoxerTest\tpig\t2021-06-27T21:26:21.233257+00:00\tevery\t0\n'
                    'tyme.key\tactive.key\ttock.key\n'
                    '_boxer_BoxerTest_tyme\t_boxer_BoxerTest_active\t_boxer_BoxerTest_tock\n'
                    'tyme.value\tactive.value\ttock.value\n')

    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    assert lines == \
    [
        'rid\tbase\tname\tstamp\trule\tcount\n',
        'BoxerTest_KQzSlod5EfC1TvKsr0VvkQ\tBoxerTest\tpig\t'
        '2021-06-27T21:26:21.233257+00:00\tevery\t0\n',
        'tyme.key\tactive.key\ttock.key\n',
        '_boxer_BoxerTest_tyme\t_boxer_BoxerTest_active\t_boxer_BoxerTest_tock\n',
        'tyme.value\tactive.value\ttock.value\n',
        '0.0\tBoxTop\t0.03125\n'
    ]

    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ','BoxerTest','pig','2021-06-27T21:26:21.233257+00:00','every','0'),
        ('tyme.key', 'active.key', 'tock.key'),
        ('_boxer_BoxerTest_tyme', '_boxer_BoxerTest_active', '_boxer_BoxerTest_tock'),
        ('tyme.value', 'active.value', 'tock.value'),
        ('0.0', 'BoxTop', '0.03125')
    ]

    assert list(hog.hold.keys()) == \
    [
        '_hold_subery',
        '_boxer_BoxerTest_tyme',
        '_boxer_BoxerTest_active',
        '_boxer_BoxerTest_tock',
    ]

    # run again
    tymist.tick()
    hold[tymeKey].value = tymist.tyme
    assert hog() == iops  # default returns iops
    assert hog.last != hog.first
    assert hog.last == tymist.tyme
    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ', 'BoxerTest','pig','2021-06-27T21:26:21.233257+00:00','every','0'),
        ('tyme.key', 'active.key', 'tock.key'),
        ('_boxer_BoxerTest_tyme', '_boxer_BoxerTest_active', '_boxer_BoxerTest_tock'),
        ('tyme.value', 'active.value', 'tock.value'),
        ('0.0', 'BoxTop', '0.03125'),
        ('0.03125', 'BoxTop', '0.03125')
    ]


    hog.close(clear=True)
    assert not hog.opened
    assert not hog.file
    assert not os.path.exists(hog.path)

    # Test rule "once"
    name = "dog"
    tymist.tyme = 0.0
    tymth = tymist.tymen()
    for dom in hold.values():  # wind hold
        if isinstance(dom, TymeDom):
            dom._wind(tymth=tymth)
    hold[tymeKey].value = tymist.tyme
    hold[activeKey].value = boxName
    hold[tockKey].value = tymist.tock

    hog = Hog(name=name, iops=iops, hold=hold, temp=True, rid=rid, rule=Rules.once)
    assert hog.rule == Rules.once
    assert not hog.started
    assert not hog.onced

    # run hog once
    assert hog() == iops  # default returns iops
    assert hog.hits == \
    {
        'tyme': '_boxer_BoxerTest_tyme',
        'active': '_boxer_BoxerTest_active',
        'tock': '_boxer_BoxerTest_tock'
    }
    assert hog.started
    assert hog.onced
    assert hog.first == 0.0
    assert hog.last == 0.0
    assert hog.rid == rid
    assert hog.stamp == dts

    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ', 'BoxerTest','dog','2021-06-27T21:26:21.233257+00:00','once','0'),
        ('tyme.key', 'active.key', 'tock.key'),
        ('_boxer_BoxerTest_tyme', '_boxer_BoxerTest_active', '_boxer_BoxerTest_tock'),
        ('tyme.value', 'active.value', 'tock.value'),
        ('0.0', 'BoxTop', '0.03125')
    ]

    # run again
    tymist.tick()
    hold[tymeKey].value = tymist.tyme
    assert hog() == iops  # default returns iops
    assert hog.last == hog.first  # since once does not log again
    assert hog.last != tymist.tyme
    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ', 'BoxerTest','dog','2021-06-27T21:26:21.233257+00:00','once','0'),
        ('tyme.key', 'active.key', 'tock.key'),
        ('_boxer_BoxerTest_tyme', '_boxer_BoxerTest_active', '_boxer_BoxerTest_tock'),
        ('tyme.value', 'active.value', 'tock.value'),
        ('0.0', 'BoxTop', '0.03125'),
    ]

    hog.close(clear=True)
    assert not hog.opened
    assert not hog.file
    assert not os.path.exists(hog.path)

    # Test vector hold bag with rule "every"
    name = "cat"
    tymist.tyme = 0.0
    tymth = tymist.tymen()


    homeKey = hold.tokey(("location", "home", ))
    hold[homeKey] = LocationBag(latN=45.0, lonE=-90.0)

    awayKey = hold.tokey(("location", "away", ))
    hold[awayKey] = LocationBag(latN=40.0, lonE=10.0)

    for dom in hold.values():  # wind hold
        if isinstance(dom, TymeDom):
            dom._wind(tymth=tymth)

    hold[tymeKey].value = tymist.tyme
    hold[activeKey].value = boxName
    hold[tockKey].value = tymist.tock
    hold[homeKey].latN = 40.7607
    hold[homeKey].lonE = -111.8939
    hold[awayKey].latN = 39.3999
    hold[awayKey].lonE = 8.2245

    # vector locations as hits with default rule every
    hog = Hog(name=name, iops=iops, hold=hold, temp=True, rid=rid,
              home=homeKey, away=awayKey)
    assert hog.rule == Rules.every
    assert not hog.started
    assert not hog.onced
    assert hog.hits =={'home': 'location_home', 'away': 'location_away'}

    # run hog once
    assert hog() == iops  # default returns iops
    assert hog.hits == \
    {
        'tyme': '_boxer_BoxerTest_tyme',
        'home': 'location_home',
        'away': 'location_away'
    }

    assert hog.started
    assert hog.onced
    assert hog.first == 0.0
    assert hog.last == 0.0
    assert hog.rid == rid
    assert hog.stamp == dts

    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ','BoxerTest','cat','2021-06-27T21:26:21.233257+00:00','every','0'),
        ('tyme.key', 'home.key', 'away.key'),
        ('_boxer_BoxerTest_tyme', 'location_home', 'location_away'),
        ('tyme.value', 'home.latN', 'home.lonE', 'away.latN', 'away.lonE'),
        ('0.0', '40.7607', '-111.8939', '39.3999', '8.2245')
    ]

    # run again
    tymist.tick()
    hold[tymeKey].value = tymist.tyme
    hold[awayKey].latN = 41.5020
    hold[awayKey].lonE = 9.5123

    assert hog() == iops  # default returns iops
    assert hog.last != hog.first  # since once does not log again
    assert hog.last == tymist.tyme
    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ', 'BoxerTest', 'cat', '2021-06-27T21:26:21.233257+00:00', 'every', '0'),
        ('tyme.key', 'home.key', 'away.key'),
        ('_boxer_BoxerTest_tyme', 'location_home', 'location_away'),
        ('tyme.value', 'home.latN', 'home.lonE', 'away.latN', 'away.lonE'),
        ('0.0', '40.7607', '-111.8939', '39.3999', '8.2245'),
        ('0.03125', '40.7607', '-111.8939', '41.502', '9.5123')
    ]

    hog.close(clear=True)
    assert not hog.opened
    assert not hog.file
    assert not os.path.exists(hog.path)

    # Test rule update
    name = "fox"
    tymist.tyme = 0.0
    tymth = tymist.tymen()

    for dom in hold.values():  # wind hold
        if isinstance(dom, TymeDom):
            dom._wind(tymth=tymth)

    # reset given rewound tyme
    hold[tymeKey].value = tymist.tyme
    hold[activeKey].value = boxName
    hold[tockKey].value = tymist.tock
    hold[homeKey].latN = 40.7607
    hold[homeKey].lonE = -111.8939
    hold[awayKey].latN = 40.0
    hold[awayKey].lonE = 7.0

    # vector locations as hits with rule update
    hog = Hog(name=name, iops=iops, hold=hold, temp=True, rid=rid, rule=Rules.update,
              home=homeKey, away=awayKey)
    assert hog.rule == Rules.update
    assert not hog.started
    assert not hog.onced
    assert hog.hits == {'home': 'location_home', 'away': 'location_away'}

    # run hog once
    assert hog() == iops  # default returns iops
    assert hog.hits == \
    {
        'tyme': '_boxer_BoxerTest_tyme',
        'home': 'location_home',
        'away': 'location_away'
    }
    assert hog.marks == {'location_home': 0.0, 'location_away': 0.0}
    assert hog.started
    assert hog.onced
    assert hog.first == 0.0
    assert hog.last == 0.0
    assert hog.rid == rid
    assert hog.stamp == dts

    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ','BoxerTest','fox','2021-06-27T21:26:21.233257+00:00','update','0'),
        ('tyme.key', 'home.key', 'away.key'),
        ('_boxer_BoxerTest_tyme', 'location_home', 'location_away'),
        ('tyme.value', 'home.latN', 'home.lonE', 'away.latN', 'away.lonE'),
        ('0.0', '40.7607', '-111.8939', '40.0', '7.0')
    ]

    # run again update but not change value
    tymist.tick()
    hold[tymeKey].value = tymist.tyme
    hold[awayKey].latN = 40.0  # update without changing value
    hold[awayKey].lonE = 7.0   # update without changing value

    assert hog() == iops  # default returns iops
    assert hog.last != hog.first  # since once does not log again
    assert hog.last == tymist.tyme
    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ','BoxerTest','fox','2021-06-27T21:26:21.233257+00:00','update','0'),
        ('tyme.key', 'home.key', 'away.key'),
        ('_boxer_BoxerTest_tyme', 'location_home', 'location_away'),
        ('tyme.value', 'home.latN', 'home.lonE', 'away.latN', 'away.lonE'),
        ('0.0', '40.7607', '-111.8939', '40.0', '7.0'),
        ('0.03125', '40.7607', '-111.8939', '40.0', '7.0')
    ]

    # run again update but change value
    tymist.tick()
    hold[tymeKey].value = tymist.tyme
    hold[homeKey].latN = 45.4545  # update change value
    hold[homeKey].lonE = -112.1212  # update change value
    hold[awayKey].latN = 41.0505  # update change value
    hold[awayKey].lonE = 8.0222   # update change value

    assert hog() == iops  # default returns iops
    assert hog.last == tymist.tyme
    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ',
         'BoxerTest','fox','2021-06-27T21:26:21.233257+00:00','update','0'),
        ('tyme.key', 'home.key', 'away.key'),
        ('_boxer_BoxerTest_tyme', 'location_home', 'location_away'),
        ('tyme.value', 'home.latN', 'home.lonE', 'away.latN', 'away.lonE'),
        ('0.0', '40.7607', '-111.8939', '40.0', '7.0'),
        ('0.03125', '40.7607', '-111.8939', '40.0', '7.0'),
        ('0.0625', '45.4545', '-112.1212', '41.0505', '8.0222')
    ]

    # run again no update
    tymist.tick()
    hold[tymeKey].value = tymist.tyme
    assert tymist.tyme == 0.09375

    assert hog() == iops  # default returns iops
    assert hog.last != tymist.tyme
    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ',
         'BoxerTest','fox','2021-06-27T21:26:21.233257+00:00','update','0'),
        ('tyme.key', 'home.key', 'away.key'),
        ('_boxer_BoxerTest_tyme', 'location_home', 'location_away'),
        ('tyme.value', 'home.latN', 'home.lonE', 'away.latN', 'away.lonE'),
        ('0.0', '40.7607', '-111.8939', '40.0', '7.0'),
        ('0.03125', '40.7607', '-111.8939', '40.0', '7.0'),
        ('0.0625', '45.4545', '-112.1212', '41.0505', '8.0222')
    ]

    # run again update not change
    tymist.tick()
    hold[tymeKey].value = tymist.tyme
    assert tymist.tyme == 0.125
    hold[homeKey].latN = 45.4545  # update do not change value

    assert hog() == iops  # default returns iops
    assert hog.last == tymist.tyme
    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ','BoxerTest','fox','2021-06-27T21:26:21.233257+00:00','update','0'),
        ('tyme.key', 'home.key', 'away.key'),
        ('_boxer_BoxerTest_tyme', 'location_home', 'location_away'),
        ('tyme.value', 'home.latN', 'home.lonE', 'away.latN', 'away.lonE'),
        ('0.0', '40.7607', '-111.8939', '40.0', '7.0'),
        ('0.03125', '40.7607', '-111.8939', '40.0', '7.0'),
        ('0.0625', '45.4545', '-112.1212', '41.0505', '8.0222'),
        ('0.125', '45.4545', '-112.1212', '41.0505', '8.0222')
    ]

    hog.close(clear=True)
    assert not hog.opened
    assert not hog.file
    assert not os.path.exists(hog.path)

    # Test rule change
    name = "owl"
    tymist.tyme = 0.0
    tymth = tymist.tymen()

    for dom in hold.values():  # wind hold
        if isinstance(dom, TymeDom):
            dom._wind(tymth=tymth)

    # reset given rewound tyme
    hold[tymeKey].value = tymist.tyme
    hold[activeKey].value = boxName
    hold[tockKey].value = tymist.tock
    hold[homeKey].latN = 40.0
    hold[homeKey].lonE = -113.0
    hold[awayKey].latN = 42.0
    hold[awayKey].lonE = 8.0

    # vector locations as hits with rule change
    hog = Hog(name=name, iops=iops, hold=hold, temp=True, rid=rid, rule=Rules.change,
              home=homeKey, away=awayKey)
    assert hog.rule == Rules.change
    assert not hog.started
    assert not hog.onced
    assert hog.hits == {'home': 'location_home', 'away': 'location_away'}

    # run hog once
    assert hog() == iops  # default returns iops
    assert hog.hits == \
    {
        'tyme': '_boxer_BoxerTest_tyme',
        'home': 'location_home',
        'away': 'location_away'
    }
    assert hog.marks == \
    {
        'location_home': (40.0, -113.0),
        'location_away': (42.0, 8.0)
    }
    assert hog.started
    assert hog.onced
    assert hog.first == 0.0
    assert hog.last == 0.0
    assert hog.rid == rid
    assert hog.stamp == dts

    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ','BoxerTest','owl','2021-06-27T21:26:21.233257+00:00','change','0'),
        ('tyme.key', 'home.key', 'away.key'),
        ('_boxer_BoxerTest_tyme', 'location_home', 'location_away'),
        ('tyme.value', 'home.latN', 'home.lonE', 'away.latN', 'away.lonE'),
        ('0.0', '40.0', '-113.0', '42.0', '8.0')
    ]

    # run again , update but not change value
    tymist.tick()
    hold[tymeKey].value = tymist.tyme
    hold[awayKey].latN = 42.0  # update but not change value
    hold[awayKey].lonE = 8.0  # update but not change value

    assert hog() == iops  # default returns iops
    assert hog.last == hog.first  # since once does not log again
    assert hog.last != tymist.tyme
    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ','BoxerTest','owl','2021-06-27T21:26:21.233257+00:00','change','0'),
        ('tyme.key', 'home.key', 'away.key'),
        ('_boxer_BoxerTest_tyme', 'location_home', 'location_away'),
        ('tyme.value', 'home.latN', 'home.lonE', 'away.latN', 'away.lonE'),
        ('0.0', '40.0', '-113.0', '42.0', '8.0')
    ]

    # run again change value
    tymist.tick()
    hold[tymeKey].value = tymist.tyme
    hold[homeKey].latN = 45.4545  # update change value
    hold[homeKey].lonE = -112.1212  # update change value
    hold[awayKey].latN = 41.0505  # update change value
    hold[awayKey].lonE = 8.0222   # update change value

    assert hog() == iops  # default returns iops
    assert hog.last == tymist.tyme
    assert hog.marks == \
    {
        'location_home': (45.4545, -112.1212),
        'location_away': (41.0505, 8.0222)
    }

    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
       ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
       ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ','BoxerTest','owl','2021-06-27T21:26:21.233257+00:00','change','0'),
       ('tyme.key', 'home.key', 'away.key'),
       ('_boxer_BoxerTest_tyme', 'location_home', 'location_away'),
       ('tyme.value', 'home.latN', 'home.lonE', 'away.latN', 'away.lonE'),
       ('0.0', '40.0', '-113.0', '42.0', '8.0'),
       ('0.0625', '45.4545', '-112.1212', '41.0505', '8.0222')
    ]

    # run again no update
    tymist.tick()
    hold[tymeKey].value = tymist.tyme
    assert tymist.tyme == 0.09375

    assert hog() == iops  # default returns iops
    assert hog.last != tymist.tyme
    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
       ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
       ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ','BoxerTest','owl','2021-06-27T21:26:21.233257+00:00','change','0'),
       ('tyme.key', 'home.key', 'away.key'),
       ('_boxer_BoxerTest_tyme', 'location_home', 'location_away'),
       ('tyme.value', 'home.latN', 'home.lonE', 'away.latN', 'away.lonE'),
       ('0.0', '40.0', '-113.0', '42.0', '8.0'),
       ('0.0625', '45.4545', '-112.1212', '41.0505', '8.0222')
    ]

    # run again change only one
    tymist.tick()
    hold[tymeKey].value = tymist.tyme
    assert tymist.tyme == 0.125
    hold[homeKey].latN = 46.0  # change value

    assert hog() == iops  # default returns iops
    assert hog.last == tymist.tyme
    assert hog.marks == \
    {
        'location_home': (46.0, -112.1212),
        'location_away': (41.0505, 8.0222)
    }
    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ','BoxerTest','owl','2021-06-27T21:26:21.233257+00:00','change','0'),
        ('tyme.key', 'home.key', 'away.key'),
        ('_boxer_BoxerTest_tyme', 'location_home', 'location_away'),
        ('tyme.value', 'home.latN', 'home.lonE', 'away.latN', 'away.lonE'),
        ('0.0', '40.0', '-113.0', '42.0', '8.0'),
        ('0.0625', '45.4545', '-112.1212', '41.0505', '8.0222'),
        ('0.125', '46.0', '-112.1212', '41.0505', '8.0222')
    ]

    hog.close(clear=True)
    assert not hog.opened
    assert not hog.file
    assert not os.path.exists(hog.path)

    # Test rule span
    name = "cow"
    tymist.tyme = 0.0
    tymth = tymist.tymen()
    span = tymist.tock * 2  # every other run

    for dom in hold.values():  # wind hold
        if isinstance(dom, TymeDom):
            dom._wind(tymth=tymth)

    # reset given rewound tyme
    hold[tymeKey].value = tymist.tyme
    hold[activeKey].value = boxName
    hold[tockKey].value = tymist.tock
    hold[homeKey].latN = 40.0
    hold[homeKey].lonE = -113.0
    hold[awayKey].latN = 42.0
    hold[awayKey].lonE = 8.0

    # vector locations as hits with rule span
    hog = Hog(name=name, iops=iops, hold=hold, temp=True, rid=rid,
              rule=Rules.span, span=span, home=homeKey, away=awayKey)
    assert hog.rule == Rules.span
    assert not hog.started
    assert not hog.onced
    assert hog.hits == {'home': 'location_home', 'away': 'location_away'}

    # run hog once
    assert hog() == iops  # default returns iops
    assert hog.hits == \
    {
        'tyme': '_boxer_BoxerTest_tyme',
        'home': 'location_home',
        'away': 'location_away'
    }
    assert hog.marks == {}
    assert hog.started
    assert hog.onced
    assert hog.first == 0.0
    assert hog.last == 0.0
    assert hog.rid == rid
    assert hog.stamp == dts

    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ','BoxerTest','cow','2021-06-27T21:26:21.233257+00:00','span','0'),
        ('tyme.key', 'home.key', 'away.key'),
        ('_boxer_BoxerTest_tyme', 'location_home', 'location_away'),
        ('tyme.value', 'home.latN', 'home.lonE', 'away.latN', 'away.lonE'),
        ('0.0', '40.0', '-113.0', '42.0', '8.0')
    ]

    # run again , update and change value but span not enough
    tymist.tick()
    hold[tymeKey].value = tymist.tyme
    hold[homeKey].latN = 45.4545  # update change value
    hold[homeKey].lonE = -112.1212  # update change value
    hold[awayKey].latN = 41.0505  # update change value
    hold[awayKey].lonE = 8.0222   # update change value

    assert hog() == iops  # default returns iops
    assert hog.last == hog.first  # since once does not log again
    assert hog.last != tymist.tyme
    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ','BoxerTest','cow','2021-06-27T21:26:21.233257+00:00','span','0'),
        ('tyme.key', 'home.key', 'away.key'),
        ('_boxer_BoxerTest_tyme', 'location_home', 'location_away'),
        ('tyme.value', 'home.latN', 'home.lonE', 'away.latN', 'away.lonE'),
        ('0.0', '40.0', '-113.0', '42.0', '8.0')
    ]

    # run again do not update or change but should log due to span
    tymist.tick()
    hold[tymeKey].value = tymist.tyme

    assert hog() == iops  # default returns iops
    assert hog.last == tymist.tyme
    assert hog.marks == {}

    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ','BoxerTest','cow','2021-06-27T21:26:21.233257+00:00','span','0'),
        ('tyme.key', 'home.key', 'away.key'),
        ('_boxer_BoxerTest_tyme', 'location_home', 'location_away'),
        ('tyme.value', 'home.latN', 'home.lonE', 'away.latN', 'away.lonE'),
        ('0.0', '40.0', '-113.0', '42.0', '8.0'),
        ('0.0625', '45.4545', '-112.1212', '41.0505', '8.0222')
    ]

    # run again change but span not enough
    tymist.tick()
    hold[tymeKey].value = tymist.tyme
    assert tymist.tyme == 0.09375
    hold[homeKey].latN = 47.0  # update change value
    hold[homeKey].lonE = -114.0  # update change value

    assert hog() == iops  # default returns iops
    assert hog.last != tymist.tyme
    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ','BoxerTest','cow','2021-06-27T21:26:21.233257+00:00','span','0'),
        ('tyme.key', 'home.key', 'away.key'),
        ('_boxer_BoxerTest_tyme', 'location_home', 'location_away'),
        ('tyme.value', 'home.latN', 'home.lonE', 'away.latN', 'away.lonE'),
        ('0.0', '40.0', '-113.0', '42.0', '8.0'),
        ('0.0625', '45.4545', '-112.1212', '41.0505', '8.0222')
    ]

    # run again change different one span enough
    tymist.tick()
    hold[tymeKey].value = tymist.tyme
    assert tymist.tyme == 0.125
    hold[awayKey].latN = 39.0  # change value

    assert hog() == iops  # default returns iops
    assert hog.last == tymist.tyme
    assert hog.marks =={}
    hog.file.seek(0, os.SEEK_SET)  # seek to beginning of file
    lines = hog.file.readlines()
    lines = [tuple(line.rstrip('\n').split('\t')) for line in lines]
    assert lines == \
    [
        ('rid', 'base', 'name', 'stamp', 'rule', 'count'),
        ('BoxerTest_KQzSlod5EfC1TvKsr0VvkQ','BoxerTest','cow','2021-06-27T21:26:21.233257+00:00','span','0'),
        ('tyme.key', 'home.key', 'away.key'),
        ('_boxer_BoxerTest_tyme', 'location_home', 'location_away'),
        ('tyme.value', 'home.latN', 'home.lonE', 'away.latN', 'away.lonE'),
        ('0.0', '40.0', '-113.0', '42.0', '8.0'),
        ('0.0625', '45.4545', '-112.1212', '41.0505', '8.0222'),
        ('0.125', '47.0', '-114.0', '39.0', '8.0222')
    ]

    hog.close(clear=True)
    assert not hog.opened
    assert not hog.file
    assert not os.path.exists(hog.path)
    """Done Test"""


if __name__ == "__main__":
    test_hog_basic()
    test_open_hog()
    test_hog_doer()


