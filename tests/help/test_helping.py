# -*- encoding: utf-8 -*-
"""
tests.help.test_helping module

"""
import pytest

from hio.help import helping

def test_copy_func():
    """
    Test the utility function for copying functions
    """
    def a(x=1):
        return x
    assert a() == 1
    assert a.__name__ == 'a'
    a.m = 2

    b = helping.copy_func(a, name='b')
    assert b.__name__ == 'b'
    b.m = 4

    assert a.m != b.m
    assert a.__name__ == 'a'

    assert id(a) != id(b)

    """Done Test"""

def test_just():
    """
    Test just function
    """

    x = (1, 2, 3, 4)
    assert tuple(helping.just(3, x)) == (1, 2, 3)

    x = (1, 2, 3)
    assert tuple(helping.just(3, x)) == (1, 2, 3)

    x = (1, 2)
    assert tuple(helping.just(3, x)) == (1, 2, None)

    x = (1, )
    assert tuple(helping.just(3, x)) == (1, None, None)

    x = ()
    assert tuple(helping.just(3, x)) == (None, None, None)

def test_repack():
    """
    Test repack function
    """
    x = (1, 2, 3, 4)
    assert tuple(helping.repack(3, x)) == (1, 2, (3, 4))

    x = (1, 2, 3)
    assert tuple(helping.repack(3, x)) == (1, 2, (3,))

    x = (1, 2)
    assert tuple(helping.repack(3, x)) == (1, 2, ())

    x = (1, )
    assert tuple(helping.repack(3, x)) == (1, None, ())

    x = ()
    assert tuple(helping.repack(3, x)) == (None, None, ())



def test_mdict():
    """
    Test mdict multiple value dict
    """
    from multidict import MultiDict
    from collections.abc import MutableMapping

    m = helping.mdict()
    assert isinstance(m, MultiDict)
    assert isinstance(m, MutableMapping)
    assert not isinstance(m, dict)

    assert repr(m) == 'mdict([])'

    m = helping.mdict(a=1, b=2, c=3)

    m.add("a", 7)
    m.add("b", 8)
    m.add("c", 9)

    assert m.getone("a") == 1
    assert m.nabone("a") == 7

    assert m.get("a") == 1
    assert m.nab("a") == 7

    assert m.getall("a") == [1, 7]
    assert m.naball("a") == [7, 1]

    assert m.nabone("z", 5) == 5
    with pytest.raises(KeyError):
        m.nabone("z")

    assert m.nab("z", 5) == 5
    assert m.nab("z") == None

    assert m.naball("z", []) == []
    with pytest.raises(KeyError):
        m.naball("z")

    assert list(m.keys()) == ['a', 'b', 'c', 'a', 'b', 'c']

    assert m.firsts() == [('a', 1), ('b', 2), ('c', 3)]

    assert m.lasts() == [('a', 7), ('b', 8), ('c', 9)]

    assert repr(m) == "mdict([('a', 1), ('b', 2), ('c', 3), ('a', 7), ('b', 8), ('c', 9)])"

    """End Test"""

def test_imdict():
    """
    Test imdict case insensitive keyed multiple value dict
    """
    from multidict import MultiDict
    from collections.abc import MutableMapping

    m = helping.imdict()
    assert isinstance(m, MultiDict)
    assert isinstance(m, MutableMapping)
    assert not isinstance(m, dict)

    assert repr(m) == 'imdict([])'

    m = helping.mdict(a=1, b=2, c=3)

    m.add("a", 7)
    m.add("b", 8)
    m.add("c", 9)

    assert m.getone("a") == 1
    assert m.nabone("a") == 7

    assert m.get("a") == 1
    assert m.nab("a") == 7

    assert m.getall("a") == [1, 7]
    assert m.naball("a") == [7, 1]

    assert m.nabone("z", 5) == 5
    with pytest.raises(KeyError):
        m.nabone("z")

    assert m.nab("z", 5) == 5
    assert m.nab("z") == None

    assert m.naball("z", []) == []
    with pytest.raises(KeyError):
        m.naball("z")

    assert list(m.keys()) == ['a', 'b', 'c', 'a', 'b', 'c']

    assert m.firsts() == [('a', 1), ('b', 2), ('c', 3)]

    assert m.lasts() == [('a', 7), ('b', 8), ('c', 9)]

    assert repr(m) == "mdict([('a', 1), ('b', 2), ('c', 3), ('a', 7), ('b', 8), ('c', 9)])"

    m = helping.imdict(A=1, b=2, C=3)

    m.add("a", 7)
    m.add("B", 8)
    m.add("c", 9)

    assert list(m.keys()) == ['A', 'b', 'C', 'a', 'B', 'c']
    assert list(m.values()) == [1, 2, 3, 7, 8, 9]
    assert list(m.items()) == [('A', 1), ('b', 2), ('C', 3), ('a', 7), ('B', 8), ('c', 9)]
    assert repr(m) == "imdict([('A', 1), ('b', 2), ('C', 3), ('a', 7), ('B', 8), ('c', 9)])"

    assert m.getone("a") == 1
    assert m.nabone("a") == 7
    assert m.getone("A") == 1
    assert m.nabone("A") == 7

    assert m.get("a") == 1
    assert m.nab("a") == 7
    assert m.get("A") == 1
    assert m.nab("A") == 7

    assert m.getall("a") == [1, 7]
    assert m.naball("a") == [7, 1]
    assert m.getall("A") == [1, 7]
    assert m.naball("A") == [7, 1]

    """End Test"""


if __name__ == "__main__":
    test_imdict()
