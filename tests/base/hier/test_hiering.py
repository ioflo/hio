# -*- encoding: utf-8 -*-
"""
tests.base.hier.test_hiering module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest

import os
import sys
import time
import inspect
import types
import logging
import json
import inspect

from collections.abc import Callable
from dataclasses import dataclass, astuple, asdict, field


from hio import hioing
from hio.help import helping, Mine, Renam
from hio.base import tyming
from hio.base.hier import WorkDom, Nabes, ActBase, actify, Box, Boxer, Boxery


def test_nabe():
    """Test Nabe namedtuple"""

    assert Nabes.native == "native"
    assert Nabes._asdict() == {'native': 'native',
                                'predo': 'predo',
                                'remark': 'remark',
                                'rendo': 'rendo',
                                'enmark': 'enmark',
                                'endo': 'endo',
                                'redo': 'redo',
                                'afdo': 'afdo',
                                'godo': 'godo',
                                'exdo': 'exdo',
                                'rexdo': 'rexdo'}


def test_workdom():
    """Test WorkDom dataclass"""

    w = WorkDom()
    assert isinstance(w, WorkDom)
    assert w.box is None
    assert w.over is None
    assert w.bxpre == 'box'
    assert w.bxidx == 0
    assert w.acts == {}
    assert w.nabe == Nabes.native



def test_actbase():
    """Test ActBase Class"""

    # clear registries for debugging
    ActBase._clearall()

    assert ActBase.__name__ == 'ActBase'
    assert ActBase.__name__ in ActBase.Registry
    assert ActBase.Registry[ActBase.__name__] == ActBase
    assert ActBase.Instances == {}
    assert ActBase.Index == 0
    assert ActBase.Names == ()

    act = ActBase()
    assert ActBase.Names == ()
    assert isinstance(act, Callable)
    assert act.name == 'ActBase0'
    assert act.iops == {}
    assert act.nabe == Nabes.endo
    assert act.mine == Mine()
    assert act.dock == None
    assert hasattr(act, 'name')   # hasattr works for properties and attributes
    assert act.name in ActBase.Instances
    assert ActBase.Instances[act.name] == act
    assert ActBase.Index == 1
    assert act() == {}


    act = ActBase()
    assert ActBase.Names == ()
    assert isinstance(act, Callable)
    assert act.name == 'ActBase1'
    assert act.iops == {}
    assert act.nabe == Nabes.endo
    assert act.mine == Mine()
    assert act.dock == None
    assert hasattr(act, 'name')   # hasattr works for properties and attributes
    assert act.name in ActBase.Instances
    assert ActBase.Instances[act.name] == act
    assert ActBase.Index == 2
    assert act() == {}


    """Done Test"""


def test_actify():
    """Test Actor registry base stuff class and subclasses"""

    @actify(name="Tact")
    def test(self, **kwa):  # signature for .act with **iops as **kwa
        assert kwa == self.iops
        return self.iops

    t = test(iops=dict(what=1), hello="hello", nabe=Nabes.redo)  # signature for Act.__init__
    assert t.name == "Tact0"
    assert t.iops == dict(what=1)
    assert t.nabe == Nabes.redo
    assert t.__class__.__name__ == "Tact"
    assert t.__class__.__name__ in t.Registry
    assert t.Registry[t.__class__.__name__] == t.__class__
    assert t.name in t.Instances
    assert t.Instances[t.name] == t
    assert isinstance(t, ActBase)
    assert t() == t.iops
    assert t.Names == ()

    x = test(bye="bye")  # signature for Act.__init__
    assert x.name == "Tact1"
    assert x.iops == {}
    assert x.nabe == Nabes.endo
    assert x.__class__.__name__ == "Tact"
    assert x.__class__.__name__ in t.Registry
    assert x.Registry[t.__class__.__name__] == t.__class__
    assert x.name in t.Instances
    assert x.Instances[t.name] == t
    assert isinstance(t, ActBase)
    assert x() == x.iops
    assert t.Names == ()

    assert x.__class__ == t.__class__
    klas = ActBase.Registry["Tact"]
    assert isinstance(t, klas)
    assert isinstance(x, klas)

    @actify(name="Pact")
    def pest(self, **kwa):  # signature for .act
        assert kwa == self.iops
        assert "why" in kwa
        assert kwa["why"] == 1
        return self.iops

    p = pest(name="spot", iops=dict(why=1))  # same signature as Act.__init__
    assert p.name == 'spot'
    assert p.iops == dict(why=1)
    assert p.nabe == Nabes.endo
    assert "Pact" in p.Registry
    klas = p.Registry["Pact"]
    assert isinstance(p, klas)
    assert p.Instances[p.name] == p
    assert p() == dict(why=1)
    assert t.Names == ()

    @actify(name="Bact")
    def best(self, *, how=None):  # signature for .act
        assert how == 5
        assert self.iops["how"] == how
        return self.iops

    b = best(iops=dict(how=5))  # signature for Act.__init__
    assert b.name == 'Bact0'
    assert b.iops == dict(how=5)
    assert b.nabe == Nabes.endo
    assert "Bact" in b.Registry
    klas = b.Registry["Bact"]
    assert isinstance(b, klas)
    assert b.Instances[b.name] == b
    assert b() == dict(how=5)
    assert t.Names == ()


    """Done Test"""




def test_inspect_stuff():
    """Test inpect stuff to see how works"""

    def f(name, over):
        av = inspect.getargvalues(inspect.currentframe())
        """ArgInfo(args=['name', 'over'],
                   varargs=None,
                   keywords=None,
                   locals={'name': 'test', 'over': 'up',
                   'av': ...)   """
        pass

    sig = inspect.signature(f)

    f(name="test", over="up")

    _name = ''
    def d(name=None, over=None):
        # '_name' is only in locals because it is referenced in the assignment
        # statement below. If _name is never referenced inside function be()
        # then it never makes it into locals(). The interpreter only populates
        # locals with varialbls in local scope it needs not all variables in
        # local scope it could access if it needed to.
        x = _name
        assert '_name' in locals()
        assert '_name' not in globals()

    d(name="test", over="up")
    assert '_name' not in globals()
    assert _name == ''

    _game = ''  # nonlocal scope since not at module level global scope is module scope
    def e(name=None, over=None):
        _game = "where"
        x = _game
        assert '_game' in locals()
        assert '_game' not in globals()

    e(name="test", over="up")
    assert '_game' not in globals()
    assert _game == ''

    _came = 'outside'  # nonlocal scope since not at module level global scope is module scope
    def c(name=None, over=None):
        nonlocal _came
        assert _came == 'outside'
        _came = "inside"

        assert '_came' in locals()
        assert '_came' not in globals()

    c(name="test", over="up")
    assert '_came' not in globals()
    assert _came == 'inside'


    global _blame  # module scope vs nonlocal scope
    assert not '_blame' in globals()  # not in globals until assigned a value
    _blame = ''
    assert '_blame' in globals()  # why is this

    def g(name=None, over=None):
        global _blame

        assert not '_blame' in locals()
        assert '_blame' in globals()  # unless assigned someplace else
        x = _blame
        _blame = "who"

    g(name="test", over="up")
    assert '_blame' in globals()
    assert _blame == "who"


    _fame = ''  # not a global at this point
    assert '_fame' not in globals()

    def h(name=None, over=None):
        global _fame

        assert not '_fame' in globals()
        _fame = 'why'  # now a global
        assert '_fame' in globals()

    h(name="test", over="up")
    assert _fame not in globals()
    assert _fame == ''  # not changed outside if not declared in global outside


    # double nested globals
    def j():
        global _tame
        assert _tame == 'here'
        _tame = "far"
        assert '_tame' in globals()

    assert '_tame' not in globals()

    global _tame
    _tame = 'here'
    assert '_tame' in globals()

    def i(name=None, over=None):
        j()
    i()
    assert '_tame' in globals()
    assert _tame == "far"


    def k():
        def l():
            global _tame
            assert _tame == 'far'
            _tame = "near"
            assert '_tame' in globals()  # closure?
        l()
    k()
    assert '_tame' in globals()
    assert _tame == "near"

    """Done Test"""



if __name__ == "__main__":
    test_nabe()
    test_workdom()
    test_actbase()
    test_actify()
    test_inspect_stuff()
