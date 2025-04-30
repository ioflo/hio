# -*- encoding: utf-8 -*-
"""
tests.base.hier.test_hiering module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest

import inspect

from hio.base.hier import WorkDom, Nabes


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
    test_inspect_stuff()
