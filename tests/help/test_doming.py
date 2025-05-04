# -*- encoding: utf-8 -*-
"""tests.help.test_doming module

"""
import pytest

import functools
from typing import Any, Type
from collections.abc import Callable
from dataclasses import (dataclass, astuple, asdict, fields, field,
                         FrozenInstanceError)

import json
import msgpack
import cbor2 as cbor

from hio.base import Tymist
from hio.help import (MapDom, IceMapDom, modify, modize,  RawDom, IceRawDom,
                      registerify, RegDom, IceRegDom, namify, TymeDom, IceTymeDom)
from hio.help.doming import dictify, datify


def test_datify():
    """
    Test convert dict to dataclass

    dataclass, astuple, asdict, fields,
    """
    @dataclass
    class Point:
        x: float
        y: float

    @dataclass
    class Line:
        a: Point
        b: Point

    line = Line(Point(1,2), Point(3,4))
    assert asdict(line) == {'a': {'x': 1, 'y': 2}, 'b': {'x': 3, 'y': 4}}
    assert line == datify(Line, asdict(line))

    pdict = dict(x=3, y=4)
    pdata = datify(Point, pdict)
    assert isinstance(pdata, Point)

    bad = dict(a=3, y=4)
    pdata = datify(Point, bad)
    assert not isinstance(pdata, Point)

    @dataclass
    class Circle:
        radius: float

        @staticmethod
        def _datify(d):
            p = d["perimeter"]
            r = p / 2 / 3.14

            return Circle(radius=r)

    d = {'area': 50.24, 'perimeter': 25.12}
    c = datify(Circle, d)
    assert c.radius == 4

    """End Test"""


def test_dictify():
    """
    Test convert dataclass to dict
    """

    @dataclass
    class Point:
        x: float
        y: float

    @dataclass
    class Line:
        a: Point
        b: Point

    line = Line(Point(1, 2), Point(3, 4))
    assert dictify(line) == {'a': {'x': 1, 'y': 2}, 'b': {'x': 3, 'y': 4}}

    @dataclass
    class Circle:
        radius: float

        def _dictify(self):
            d = dict(
                area=self.radius**2*3.14,
                perimeter=2*self.radius*3.14
            )

            return d

    c = Circle(radius=4)
    assert dictify(c) == {'area': 50.24, 'perimeter': 25.12}


def test_ice_map_dom():
    """Test IceMapDom dataclass """

    md = IceMapDom()
    assert isinstance(md, IceMapDom)

    assert md.__dataclass_params__.frozen == True
    assert hash(md) == hash(md)      # test hash

    assert md._asdict() == {}
    assert md._astuple() == ()

    with pytest.raises(FrozenInstanceError):
        md.value = True

    fd = IceMapDom._fromdict({})
    assert isinstance(fd, IceMapDom)
    assert fd == md

    bad = dict(val=0)  # field label "val" instead of "value"
    with pytest.raises(ValueError):
        IceMapDom._fromdict(bad)

    with pytest.raises(FrozenInstanceError):
        md.value = True


    @dataclass(frozen=True)
    class TestIceMapDom(IceMapDom):
        name:  str = 'test'
        value:  int = 5

    tmd = TestIceMapDom()
    assert isinstance(tmd, IceMapDom)
    assert isinstance(tmd, TestIceMapDom)
    assert tmd.name == 'test'
    assert tmd.value == 5

    assert tmd.__dataclass_params__.frozen == True
    assert hash(tmd) == hash(tmd)      # test hash

    d = tmd._asdict()
    assert d == {'name': 'test', 'value': 5}
    assert tmd._astuple() == ("test", 5)

    assert 'name' in tmd
    assert 'value' in tmd

    with pytest.raises(FrozenInstanceError):
        tmd.val = True

    fd = TestIceMapDom._fromdict(d)
    assert isinstance(fd, TestIceMapDom)
    assert fd == tmd

    bad = dict(val=0)  # field label "val" instead of "value"
    with pytest.raises(ValueError):
        TestIceMapDom._fromdict(bad)
    """Done Test"""


def test_ice_raw_dom():
    """Test IceRawDom dataclass """

    rd = IceRawDom()
    assert isinstance(rd, IceRawDom)
    d = rd._asdict()
    assert d == {}
    fd = IceRawDom._fromdict(d)
    assert isinstance(fd, IceRawDom)

    assert rd.__dataclass_params__.frozen == True
    assert hash(rd) == hash(rd)      # test hash

    assert rd._astuple() == ()

    bad = dict(name='test', val=0)  # non fields
    with pytest.raises(ValueError):
        IceRawDom._fromdict(bad)

    with pytest.raises(FrozenInstanceError):
        rd.value = True

    j = rd._asjson()
    assert isinstance(j, bytes)
    assert j == b'{}'
    fj = IceRawDom._fromjson(j)
    assert fj == rd
    j = j.decode()
    fj = IceRawDom._fromjson(j)
    assert rd == fj

    bad = b'{"name":"test","val":5}'  # field label "val" instead of "value"
    with pytest.raises(ValueError):
        IceRawDom._fromjson(bad)

    c = rd._ascbor()
    assert c == b'\xa0'
    assert isinstance(c, bytes)
    fc = IceRawDom._fromcbor(c)
    assert rd == fc

    bad = cbor.dumps(dict(name='test', val=0)) # field label "val" instead of "value"
    assert bad == b'\xa2dnamedtestcval\x00'
    with pytest.raises(ValueError):
        IceRawDom._fromcbor(bad)

    m = rd._asmgpk()
    assert m == b'\x80'
    assert isinstance(m, bytes)
    fm = IceRawDom._frommgpk(m)
    assert rd == fm

    bad = msgpack.dumps(dict(name='test', val=0)) # field label "val" instead of "value"
    assert bad == b'\x82\xa4name\xa4test\xa3val\x00'
    with pytest.raises(ValueError):
        IceRawDom._frommgpk(bad)


    # test subclass
    @dataclass(frozen=True)
    class TestIceRawDom(IceRawDom):
        name:  str = 'test'
        value:  int = 5

    trd = TestIceRawDom()
    assert isinstance(trd, IceRawDom)
    assert isinstance(trd, TestIceRawDom)
    assert trd.name == 'test'
    assert trd.value == 5

    assert trd.__dataclass_params__.frozen == True
    assert hash(trd) == hash(trd)      # test hash

    with pytest.raises(FrozenInstanceError):
        rd.val = True

    assert 'name' in trd  # contains works for field attributes only
    assert 'value' in trd  # contains works for field attributes only

    d = trd._asdict()
    assert d == {'name': 'test', 'value': 5}
    fd = TestIceRawDom._fromdict(d)
    assert isinstance(fd, TestIceRawDom)
    assert fd == trd

    assert trd._astuple() == ("test", 5)

    bad = dict(name='test', val=0)  # field label "val" instead of "value"
    with pytest.raises(ValueError):
        TestIceRawDom._fromdict(bad)

    with pytest.raises(ValueError):
        IceRawDom._fromdict(d)  # since fields of d don't match RawDom which does not have fields

    j = trd._asjson()
    assert isinstance(j, bytes)
    assert j == b'{"name":"test","value":5}'
    fj = TestIceRawDom._fromjson(j)
    assert fj == trd
    j = j.decode()
    fj = TestIceRawDom._fromjson(j)
    assert fj == trd

    bad = b'{"name":"test","val":5}'  # field label "val" instead of "value"
    with pytest.raises(ValueError):
        TestIceRawDom._fromjson(bad)

    c = trd._ascbor()
    assert c == b'\xa2dnamedtestevalue\x05'
    assert isinstance(c, bytes)
    fc = TestIceRawDom._fromcbor(c)
    assert fc == trd

    bad = cbor.dumps(dict(name='test', val=0)) # field label "val" instead of "value"
    assert bad == b'\xa2dnamedtestcval\x00'
    with pytest.raises(ValueError):
        TestIceRawDom._fromcbor(bad)

    m = trd._asmgpk()
    assert m == b'\x82\xa4name\xa4test\xa5value\x05'
    assert isinstance(m, bytes)
    fm = TestIceRawDom._frommgpk(m)
    assert fm == trd

    bad = msgpack.dumps(dict(name='test', val=0)) # field label "val" instead of "value"
    assert bad == b'\x82\xa4name\xa4test\xa3val\x00'
    with pytest.raises(ValueError):
        TestIceRawDom._frommgpk(bad)
    """Done Test"""


def test_ice_reg_dom():
    """Test IceRegDom class"""
    assert IceRegDom._registry
    assert IceRegDom.__name__ in IceRegDom._registry
    assert IceRegDom._registry[IceRegDom.__name__] == IceRegDom


    rd = IceRegDom()  # defaults
    assert isinstance(rd, IceRegDom)
    assert rd._registry[rd.__class__.__name__] == IceRegDom

    assert rd.__dataclass_params__.frozen == True
    assert hash(rd) == hash(rd)      # test hash

    # test _asdict
    assert rd._asdict() == {}  # no fields so empty

    # test _astuple
    assert rd._astuple() == ()  # no fields so empty

    # test hash
    assert hash(rd) == hash(rd)

    @registerify
    @dataclass(frozen=True)
    class TestIceRegDom(IceRegDom):
        """TestIceRegDom dataclass

        Field Attributes:
            value (Any):  generic value field
        """
        value: Any = None  # generic value


    trd = TestIceRegDom()
    assert isinstance(trd, IceRegDom)
    assert isinstance(trd, TestIceRegDom)
    assert trd._registry[trd.__class__.__name__] == TestIceRegDom
    assert trd.value == None

    assert trd.__dataclass_params__.frozen == True
    assert hash(trd) == hash(trd)      # test hash

    with pytest.raises(FrozenInstanceError):
        trd.value = True

    with pytest.raises(FrozenInstanceError):
        trd.val = True

    # test _asdict
    assert trd._asdict() == {'value': None}

    # test _astuple
    assert trd._astuple() == (None,)

    # test hash
    assert hash(trd) == hash(trd)

    """Done Test"""


def test_ice_tyme_dom():
    """Test IceTymeDom class"""
    tymist = Tymist()

    assert IceTymeDom._registry
    assert IceTymeDom.__name__ in IceTymeDom._registry
    assert IceTymeDom._registry[IceTymeDom.__name__] == IceTymeDom

    assert IceTymeDom._names == ()
    # no fields just InitVar and ClassVar attributes
    flds = fields(IceTymeDom)
    assert len(flds) == 0

    td = IceTymeDom()  # defaults
    assert isinstance(td, IceTymeDom)
    assert td._names == ()
    assert td._tymth == None
    assert td._now == None
    assert td._tyme == None

    assert td.__dataclass_params__.frozen == True
    assert hash(td) == hash(td)      # test hash

    td = IceTymeDom(_tymth=tymist.tymen(), _tyme=1.0)
    assert td._names == ()
    assert not td._tymth
    assert td._now == None
    assert td._tyme == None

    tymist.tick()
    assert td._now == None
    tymist.tick()
    assert td._now == None

    # can't add non-field attributes to frozen dataclass
    with pytest.raises(FrozenInstanceError):
        td.value = 1

    # test _asdict
    assert td._asdict() == {}  # no fields so empty

    # test _astuple
    assert td._astuple() == ()  # no fields so empty



    @namify
    @registerify
    @dataclass(frozen=True)
    class TestIceTymeDom(IceTymeDom):
        """TestIceTymeDom dataclass

        Field Attributes:
            value (Any):  generic value field
        """
        value: Any = None  # generic value


    assert TestIceTymeDom._names == ('value', )

    ttd = TestIceTymeDom()
    assert isinstance(ttd, IceTymeDom)
    assert isinstance(ttd, TestIceTymeDom)
    assert ttd._registry[ttd.__class__.__name__] == TestIceTymeDom
    assert ttd._names == ('value', )
    assert not ttd._tymth
    assert ttd._now is None
    assert ttd._tyme is None
    assert ttd.value == None

    assert ttd.__dataclass_params__.frozen == True
    assert hash(ttd) == hash(ttd)  # test hash

    # test _asdict
    assert ttd._asdict() == {'value': None}

    # test _astuple
    assert ttd._astuple() == (None,)

    # can't add non-field attributes to frozen dataclass
    with pytest.raises(FrozenInstanceError):
        ttd.value = "hello"

    ttd = TestIceTymeDom(_tymth=tymist.tymen(), _tyme=0.0, value=10)
    assert isinstance(ttd, TestIceTymeDom)
    assert ttd._registry[ttd.__class__.__name__] == TestIceTymeDom
    assert ttd._names == ('value', )
    assert not ttd._tymth
    assert ttd._now is None
    assert ttd._tyme == None
    assert ttd.value == 10

    assert ttd.__dataclass_params__.frozen == True
    assert hash(ttd) == hash(ttd)      # test hash
    """Done Test"""


def test_map_dom():
    """Test MapDom dataclass """

    md = MapDom()
    assert isinstance(md, MapDom)

    assert md._asdict() == {}
    assert md._astuple() == ()

    fd = MapDom._fromdict({})
    assert isinstance(fd, MapDom)
    assert fd == md

    bad = dict(val=0)  # field label "val" instead of "value"
    with pytest.raises(ValueError):
        MapDom._fromdict(bad)

    # non-field attributes
    md.nym = "rest"
    md.val = 6

    assert md["nym"] == 'rest'
    assert md["val"] == 6

    md["nym"] = 'best'
    assert md.nym == 'best'

    md._update(nym='test', val=7)
    assert md.nym == 'test'
    assert md.val == 7

    assert 'nym' not in md  # contains not work for non-field attributes
    assert 'val' not in md  # contains not work for non-field attributes

    assert md._asdict() == {}
    assert md._astuple() == ()


    @dataclass
    class TestMapDom(MapDom):
        name:  str = 'test'
        value:  int = 5


    tmd = TestMapDom()
    assert isinstance(tmd, MapDom)
    assert isinstance(tmd, TestMapDom)
    assert tmd.name == 'test'
    assert tmd.value == 5

    d = tmd._asdict()
    assert isinstance(d, dict)
    assert d == {'name': 'test', 'value': 5}

    assert tmd._astuple() == ("test", 5)

    fd = TestMapDom._fromdict(d)
    assert isinstance(fd, TestMapDom)
    assert fd == tmd

    bad = dict(name='test', val=0)  # field label "val" instead of "value"
    with pytest.raises(ValueError):
        TestMapDom._fromdict(bad)

    tmd.name = "rest"
    tmd.value = 6

    assert tmd["name"] == 'rest'
    assert tmd["value"] == 6

    tmd["name"] = 'best'
    assert tmd.name == 'best'

    tmd._update(name='test', value=7)
    assert tmd.name == 'test'
    assert tmd.value == 7

    assert 'name' in tmd  # contains works for fields but not non-fields
    assert 'value' in tmd # contains works for fields but not non-fields

    # non-field attributes
    tmd.nym = "rest"
    tmd.val = 6

    assert tmd["nym"] == 'rest'
    assert tmd["val"] == 6

    tmd["nym"] = 'best'
    assert tmd.nym == 'best'

    tmd._update(nym='test', val=7)
    assert tmd.nym == 'test'
    assert tmd.val == 7

    assert not 'nym' in md  # contains fails for  non-fields
    assert not 'val' in md  # contains fails for  non-fields

    assert tmd._asdict() == {'name': 'test', 'value': 7}
    assert tmd._astuple() == ("test", 7)

    """Done Test"""



def test_modify():
    """Test modify wrapper. Test different use cases
    as inline wrapper with call time injected works (standard)
    as inline wrapper with default lexical works
    as inline wrapper with call time inject works that is preserved
    as decorator with default lexical works
    as decorator with call time works paramter that is preserved

    """
    @dataclass
    class TestDom(MapDom):
        count: int = 0
        names: list = field(default_factory=list)


    def fun(we):
        n0 = we(name='top')
        n1 = we()
        n2 = we()
        n3 = we()
        return(n0, n1, n2, n3)

    # Test standard wrapper call
    def we0(name=None, *, mods=None):
        m = mods
        if "count" not in m:
            m.count = 0
        if "names" not in m:
            m.names = []

        if not name:
            name = "x" + str(m.count)
        m.count += 1
        m.names.append(name)
        return name

    # first time
    works = TestDom()
    we = modify(works)(we0)  # wrapper it
    names = fun(we)
    assert names == ('top', 'x1', 'x2', 'x3')
    assert works._asdict() == {'count': 4, 'names': ['top', 'x1', 'x2', 'x3']}

    # call again as wrapped already
    names = fun(we)  # call again
    assert names == ('top', 'x5', 'x6', 'x7')
    assert works._asdict() == {'count': 8, 'names': ['top', 'x1', 'x2', 'x3', 'top', 'x5', 'x6', 'x7']}

    # override replace works
    vorks = TestDom()
    name = we(mods=vorks)
    assert name == 'x0'
    assert vorks._asdict() == {'count': 1, 'names': ['x0']}

    # resume back befoe override
    name = we()
    assert name == 'x8'
    assert works._asdict() == {'count': 9, 'names': ['top', 'x1', 'x2', 'x3', 'top', 'x5', 'x6', 'x7', 'x8']}

    # default lexical works in wrapper call
    def we1(name=None, *, mods=None):
        m = mods
        if "count" not in m:
            m.count = 0
        if "names" not in m:
            m.names = []

        if not name:
            name = "x" + str(m.count)
        m.count += 1
        m.names.append(name)
        return name

    # test lexical closure in wrapper
    works = None
    we = modify(works, TestDom)(we1)
    names = fun(we)
    assert names == ('top', 'x1', 'x2', 'x3')
    assert works == None  # not visible outside closure

    # call again as wrapped already
    names = fun(we)  # call again
    assert names == ('top', 'x5', 'x6', 'x7')
    assert works == None  # not visible outside closure

    # override replace works inside
    vorks = TestDom()
    name = we(mods=vorks)
    assert name == 'x0'
    assert vorks._asdict() == {'count': 1, 'names': ['x0']}

    # do again but now without override
    name = we()
    assert name == 'x8'
    assert works == None  # not visible

    # decorated
    works = TestDom()

    @modify(works)
    def we1(name=None, *, mods=None):
        m = mods
        if "count" not in m:
            m.count = 0
        if "names" not in m:
            m.names = []

        if not name:
            name = "x" + str(m.count)
        m.count += 1
        m.names.append(name)
        return name

    # test decoration with lexical scope of works, same scope in test so can view.
    # normally would be in different scopes
    names = fun(we1)
    assert names == ('top', 'x1', 'x2', 'x3')
    assert works._asdict() == {'count': 4, 'names': ['top', 'x1', 'x2', 'x3']}

    # call again
    names = fun(we1)  # call again
    assert names == ('top', 'x5', 'x6', 'x7')
    assert works._asdict() == {'count': 8, 'names': ['top', 'x1', 'x2', 'x3', 'top', 'x5', 'x6', 'x7']}

    # override replace works
    vorks = TestDom()
    name = we1(mods=vorks)
    assert name == 'x0'
    assert vorks._asdict() == {'count': 1, 'names': ['x0']}

    # do again but now without override
    name = we1()
    assert name == 'x8'
    assert works._asdict() == {'count': 9, 'names': ['top', 'x1', 'x2', 'x3', 'top', 'x5', 'x6', 'x7', 'x8']}

    """Done Test"""


def test_modize():
    """Test modize wrapper. Test different use cases
    as inline wrapper with call time injected works (standard)
    as inline wrapper with default lexical works
    as inline wrapper with call time inject works that is preserved
    as decorator with default lexical works
    as decorator with call time works paramter that is preserved

    """
    def fun(we):
        n0 = we(name='top')
        n1 = we()
        n2 = we()
        n3 = we()
        return(n0, n1, n2, n3)

    # Test standard wrapper call
    def we0(name=None, *, mods=None):
        m = mods
        if "count" not in m:
            m["count"] = 0
        if "names" not in m:
            m["names"] = []

        if not name:
            name = "x" + str(m["count"])
        m['count'] += 1
        m["names"].append(name)

        return name

    # first time
    works = dict(count=0, names=[])
    we = modize(works)(we0)  # wrapper it
    names = fun(we)
    assert names == ('top', 'x1', 'x2', 'x3')
    assert works == {'count': 4, 'names': ['top', 'x1', 'x2', 'x3']}

    # call again as wrapped already
    names = fun(we)  # call again
    assert names == ('top', 'x5', 'x6', 'x7')
    assert works == {'count': 8, 'names': ['top', 'x1', 'x2', 'x3', 'top', 'x5', 'x6', 'x7']}

    # override replace works
    vorks = {}
    name = we(mods=vorks)
    assert name == 'x0'
    assert vorks == {'count': 1, 'names': ['x0']}

    # resume back befoe override
    name = we()
    assert name == 'x8'
    assert works == {'count': 9, 'names': ['top', 'x1', 'x2', 'x3', 'top', 'x5', 'x6', 'x7', 'x8']}

    # default lexical works in wrapper call
    def we1(name=None, *, mods=None):
        w = mods
        if "count" not in w:
            w["count"] = 0
        if "names" not in w:
            w["names"] = []

        if not name:
            name = "x" + str(w["count"])
        w['count'] += 1
        w["names"].append(name)

        return name

    # test lexical closure in wrapper
    works = None
    we = modize(works)(we1)
    names = fun(we)
    assert names == ('top', 'x1', 'x2', 'x3')
    assert works == None  # not visible outside closure

    # call again as wrapped already
    names = fun(we)  # call again
    assert names == ('top', 'x5', 'x6', 'x7')
    assert works == None  # not visible outside closure

    # override replace works inside
    vorks = {}
    name = we(mods=vorks)
    assert name == 'x0'
    assert vorks == {'count': 1, 'names': ['x0']}

    # do again but now without override
    name = we()
    assert name == 'x8'
    assert works == None  # not visible

    # decorated
    works = dict(count=0, names=[])

    @modize(works)
    def we1(name=None, *, mods=None):
        w = mods
        if "count" not in w:
            w["count"] = 0
        if "names" not in w:
            w["names"] = []

        if not name:
            name = "x" + str(w["count"])
        w['count'] += 1
        w["names"].append(name)

        return name

    # test decoration with lexical scope of works, same scope in test so can view.
    # normally would be in different scopes
    names = fun(we1)
    assert names == ('top', 'x1', 'x2', 'x3')
    assert works == {'count': 4, 'names': ['top', 'x1', 'x2', 'x3']}

    # call again
    names = fun(we1)  # call again
    assert names == ('top', 'x5', 'x6', 'x7')
    assert works == {'count': 8, 'names': ['top', 'x1', 'x2', 'x3', 'top', 'x5', 'x6', 'x7']}

    # override replace works
    vorks = {}
    name = we1(mods=vorks)
    assert name == 'x0'
    assert vorks == {'count': 1, 'names': ['x0']}

    # do again but now without override
    name = we1()
    assert name == 'x8'
    assert works == {'count': 9, 'names': ['top', 'x1', 'x2', 'x3', 'top', 'x5', 'x6', 'x7', 'x8']}

    """Done Test"""


def test_raw_dom():
    """Test RawDom dataclass """

    rd = RawDom()
    assert isinstance(rd, RawDom)
    d = rd._asdict()
    assert d == {}
    fd = RawDom._fromdict(d)
    assert isinstance(fd, RawDom)

    assert rd._astuple() == ()

    bad = dict(name='test', val=0)  # non fields
    with pytest.raises(ValueError):
        RawDom._fromdict(bad)

    j = rd._asjson()
    assert isinstance(j, bytes)
    assert j == b'{}'
    fj = RawDom._fromjson(j)
    assert fj == rd
    j = j.decode()
    fj = RawDom._fromjson(j)
    assert rd == fj

    bad = b'{"name":"test","val":5}'  # field label "val" instead of "value"
    with pytest.raises(ValueError):
        RawDom._fromjson(bad)

    c = rd._ascbor()
    assert c == b'\xa0'
    assert isinstance(c, bytes)
    fc = RawDom._fromcbor(c)
    assert rd == fc

    bad = cbor.dumps(dict(name='test', val=0)) # field label "val" instead of "value"
    assert bad == b'\xa2dnamedtestcval\x00'
    with pytest.raises(ValueError):
        RawDom._fromcbor(bad)

    m = rd._asmgpk()
    assert m == b'\x80'
    assert isinstance(m, bytes)
    fm = RawDom._frommgpk(m)
    assert rd == fm

    bad = msgpack.dumps(dict(name='test', val=0)) # field label "val" instead of "value"
    assert bad == b'\x82\xa4name\xa4test\xa3val\x00'
    with pytest.raises(ValueError):
        RawDom._frommgpk(bad)


    # test subclass
    @dataclass
    class TestRawDom(RawDom):
        name:  str = 'test'
        value:  int = 5

    trd = TestRawDom()
    assert isinstance(trd, TestRawDom)
    assert isinstance(trd, RawDom)
    assert trd.name == 'test'
    assert trd.value == 5

    assert trd["name"] == 'test'
    assert trd["value"] == 5

    trd["name"] = 'best'
    assert trd.name == 'best'

    trd._update(name='test')
    assert trd.name == 'test'

    assert 'name' in trd
    assert 'value' in trd

    trd = TestRawDom()
    assert isinstance(trd, TestRawDom)
    assert isinstance(trd, RawDom)
    assert trd.name == 'test'
    assert trd.value == 5

    d = trd._asdict()
    assert d == {'name': 'test', 'value': 5}
    fd = TestRawDom._fromdict(d)
    assert isinstance(fd, TestRawDom)
    assert fd == trd

    assert trd._astuple() == ("test", 5)

    bad = dict(name='test', val=0)  # field label "val" instead of "value"
    with pytest.raises(ValueError):
        TestRawDom._fromdict(bad)

    with pytest.raises(ValueError):
        RawDom._fromdict(d)  # since fields of d don't match RawDom which does not have fields

    j = trd._asjson()
    assert isinstance(j, bytes)
    assert j == b'{"name":"test","value":5}'
    fj = TestRawDom._fromjson(j)
    assert fj == trd
    j = j.decode()
    fj = TestRawDom._fromjson(j)
    assert fj == trd

    bad = b'{"name":"test","val":5}'  # field label "val" instead of "value"
    with pytest.raises(ValueError):
        TestRawDom._fromjson(bad)

    c = trd._ascbor()
    assert c == b'\xa2dnamedtestevalue\x05'
    assert isinstance(c, bytes)
    fc = TestRawDom._fromcbor(c)
    assert fc == trd

    bad = cbor.dumps(dict(name='test', val=0)) # field label "val" instead of "value"
    assert bad == b'\xa2dnamedtestcval\x00'
    with pytest.raises(ValueError):
        TestRawDom._fromcbor(bad)

    m = trd._asmgpk()
    assert m == b'\x82\xa4name\xa4test\xa5value\x05'
    assert isinstance(m, bytes)
    fm = TestRawDom._frommgpk(m)
    assert fm == trd

    bad = msgpack.dumps(dict(name='test', val=0)) # field label "val" instead of "value"
    assert bad == b'\x82\xa4name\xa4test\xa3val\x00'
    with pytest.raises(ValueError):
        TestRawDom._frommgpk(bad)
    """Done Test"""


def test_reg_dom():
    """Test RegDom class"""
    assert RegDom._registry
    assert RegDom.__name__ in RegDom._registry
    assert RegDom._registry[RegDom.__name__] == RegDom


    rd = RegDom()  # defaults
    assert isinstance(rd, RegDom)
    assert rd._registry[rd.__class__.__name__] == RegDom

    assert rd.__dataclass_params__.frozen == False
    assert hash(rd) == hash(rd)      # test hash

    # test _asdict
    assert rd._asdict() == {}  # no fields so empty

    # test _astuple
    assert rd._astuple() == ()  # no fields so empty

    # test hash
    assert hash(rd) == hash(rd)

    @registerify
    @dataclass
    class TestRegDom(RegDom):
        """TestRegDom dataclass

        Field Attributes:
            value (Any):  generic value field
        """
        value: Any = None  # generic value

        def __hash__(self):
            """Define hash so can work with ordered_set
            __hash__ is not inheritable in dataclasses so must be explicitly defined
            in every subclass
            """
            return hash((self.__class__.__name__,) + self._astuple())  # almost same as __eq__


    trd = TestRegDom()
    assert isinstance(trd, RegDom)
    assert isinstance(trd, TestRegDom)
    assert trd._registry[trd.__class__.__name__] == TestRegDom
    assert trd.value == None

    assert trd.__dataclass_params__.frozen == False
    assert hash(trd) == hash(trd)      # test hash

    # test _asdict
    assert trd._asdict() == {'value': None}

    # test _astuple
    assert trd._astuple() == (None,)

    # test hash
    assert hash(trd) == hash(trd)

    """Done Test"""


def test_tyme_dom():
    """Test TymeDom class"""
    tymist = Tymist()

    assert TymeDom._registry
    assert TymeDom.__name__ in TymeDom._registry
    assert TymeDom._registry[TymeDom.__name__] == TymeDom

    assert TymeDom._names == ()
    # no fields just InitVar and ClassVar attributes
    flds = fields(TymeDom)
    assert len(flds) == 0

    td = TymeDom()  # defaults
    assert isinstance(td, TymeDom)
    assert td._names == ()
    assert td._tymth == None
    assert td._now == None
    assert td._tyme == None

    assert td.__dataclass_params__.frozen == False
    assert hash(td) == hash(td)      # test hash

    td = TymeDom(_tymth=tymist.tymen())
    assert td._names == ()
    assert td._tymth
    assert td._now == 0.0 == tymist.tyme
    assert td._tyme == None

    tymist.tick()
    assert td._now == tymist.tock
    tymist.tick()
    assert td._now == 2 * tymist.tock

    # adding attribute does not make it a dataclass field
    td.value = 1
    assert td._tyme == None
    assert td.value == 1
    assert td["value"] == 1

    # test __setitem__
    td["value"] = 2
    assert td._tyme == None
    assert td["value"] == 2

    td["stuff"] = 3
    assert td._tyme == None
    assert td["stuff"] == 3
    assert td.stuff == 3

    flds = fields(td)  # or equiv dataclasses.fields(TymeDom)
    assert len(flds) == 0

    td = TymeDom(_tyme=1.0)
    assert td._names == ()
    assert not td._tymth
    assert td._now == None
    assert td._tyme == 1.0


    td = TymeDom(_tyme=1.0, _tymth=tymist.tymen())
    assert td._names == ()
    assert td._tymth
    assert td._now == 2 * tymist.tock
    assert td._tyme == 1.0

    # test ._update
    tymist = Tymist()
    td = TymeDom(_tymth=tymist.tymen())
    assert td._names == ()
    assert td._tymth
    assert td._now == 0.0 == tymist.tyme
    assert td._tyme == None

    td._update(value=1)
    assert td._tyme == None
    assert td.value == 1
    assert td["value"] == 1

    # test _asdict
    assert td._asdict() == {}  # no fields so empty

    # test _astuple
    assert td._astuple() == ()  # no fields so empty

    # test hash
    assert hash(td) == hash(td)

    @namify
    @registerify
    @dataclass
    class TestTymeDom(TymeDom):
        """TestTymeDom dataclass

        Field Attributes:
            value (Any):  generic value field
        """
        value: Any = None  # generic value

        def __hash__(self):
            """Define hash so can work with ordered_set
            __hash__ is not inheritable in dataclasses so must be explicitly defined
            in every subclass
            """
            return hash((self.__class__.__name__,) + self._astuple())  # almost same as __eq__



    assert TestTymeDom._names == ('value', )

    ttd = TestTymeDom(_tymth=tymist.tymen())
    assert isinstance(ttd, TymeDom)
    assert isinstance(ttd, TestTymeDom)
    assert ttd._registry[ttd.__class__.__name__] == TestTymeDom
    assert ttd._names == ('value', )
    assert ttd._tymth
    assert ttd._now == 0.0 == tymist.tyme
    assert ttd._tyme == None
    assert ttd.value == None

    # test _asdict
    assert ttd._asdict() == {'value': None}

    # test _astuple
    assert ttd._astuple() == (None,)

    ttd.value = "hello"
    assert ttd._tyme == 0.0 == ttd._now == tymist._tyme
    # test _asdict
    assert ttd._asdict() == {'value': "hello"}

    # test _astuple
    assert ttd._astuple() == ("hello",)

    # test hash
    assert hash(ttd) == hash(ttd)

    ttd = TestTymeDom(_tymth=tymist.tymen(), value=10)
    assert isinstance(ttd, TymeDom)
    assert isinstance(ttd, TestTymeDom)
    assert ttd._registry[ttd.__class__.__name__] == TestTymeDom
    assert ttd._names == ('value', )
    assert ttd._tymth
    assert ttd._now == 0.0 == tymist.tyme
    assert ttd._tyme == None
    ttd.value = 12
    assert ttd._tyme == 0.0
    """Done Test"""


if __name__ == "__main__":
    test_datify()
    test_dictify()
    test_ice_map_dom()
    test_ice_raw_dom()
    test_ice_reg_dom()
    test_ice_tyme_dom()
    test_map_dom()
    test_modify()
    test_modize()
    test_raw_dom()
    test_reg_dom()
    test_tyme_dom()



