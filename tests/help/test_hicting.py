# -*- encoding: utf-8 -*-
"""
tests.help.test_helping module

"""
import pytest

from hio.help import hicting



def test_hict():
    """
    Test Hict header case insensitive keyed multiple value dict
    """
    from multidict import MultiDict
    from collections.abc import MutableMapping

    h = hicting.Hict()
    assert isinstance(h, MultiDict)
    assert isinstance(h, MutableMapping)
    assert not isinstance(h, dict)

    assert repr(h) == 'Hict([])'

    h = hicting.Mict(a=1, b=2, c=3)

    h.add("a", 7)
    h.add("b", 8)
    h.add("c", 9)

    assert h.getone("a") == 1
    assert h.nabone("a") == 7

    assert h.get("a") == 1
    assert h.nab("a") == 7

    assert h.getall("a") == [1, 7]
    assert h.naball("a") == [7, 1]

    assert h.nabone("z", 5) == 5
    with pytest.raises(KeyError):
        h.nabone("z")

    assert h.nab("z", 5) == 5
    assert h.nab("z") == None

    assert h.naball("z", []) == []
    with pytest.raises(KeyError):
        h.naball("z")

    assert list(h.keys()) == ['a', 'b', 'c', 'a', 'b', 'c']

    assert h.firsts() == [('a', 1), ('b', 2), ('c', 3)]

    assert h.lasts() == [('a', 7), ('b', 8), ('c', 9)]

    assert repr(h) == "Mict([('a', 1), ('b', 2), ('c', 3), ('a', 7), ('b', 8), ('c', 9)])"

    h = hicting.Hict(A=1, b=2, C=3)

    h.add("a", 7)
    h.add("B", 8)
    h.add("c", 9)

    assert list(h.keys()) == ['A', 'b', 'C', 'a', 'B', 'c']
    assert list(h.values()) == [1, 2, 3, 7, 8, 9]
    assert list(h.items()) == [('A', 1), ('b', 2), ('C', 3), ('a', 7), ('B', 8), ('c', 9)]
    assert repr(h) == "Hict([('A', 1), ('b', 2), ('C', 3), ('a', 7), ('B', 8), ('c', 9)])"

    assert h.getone("a") == 1
    assert h.nabone("a") == 7
    assert h.getone("A") == 1
    assert h.nabone("A") == 7

    assert h.get("a") == 1
    assert h.nab("a") == 7
    assert h.get("A") == 1
    assert h.nab("A") == 7

    assert h.getall("a") == [1, 7]
    assert h.naball("a") == [7, 1]
    assert h.getall("A") == [1, 7]
    assert h.naball("A") == [7, 1]

    """End Test"""


def test_mict():
    """
    Test Mict multiple value dict
    """
    from multidict import MultiDict
    from collections.abc import MutableMapping

    m = hicting.Mict()
    assert isinstance(m, MultiDict)
    assert isinstance(m, MutableMapping)
    assert not isinstance(m, dict)

    assert repr(m) == 'Mict([])'

    m = hicting.Mict(a=1, b=2, c=3)

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

    assert repr(m) == "Mict([('a', 1), ('b', 2), ('c', 3), ('a', 7), ('b', 8), ('c', 9)])"

    """End Test"""


if __name__ == "__main__":
    test_hict()
    test_mict()
