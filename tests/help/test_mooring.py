# -*- encoding: utf-8 -*-
"""tests.help.test_mooring module

"""
import pytest

from hio.help import Moor, Renam


def test_renam():
    """Test regular expression Renam for component name """
    name = "hello"
    assert Renam.match(name)

    name = "_hello"
    assert not Renam.match(name)

    name = "hello_goodbye"
    assert not Renam.match(name)

    name = "hello_"
    assert not Renam.match(name)

    name = "hell1"
    assert Renam.match(name)

    name = "1hello"
    assert not Renam.match(name)

    name = "hello.hello"
    assert not Renam.match(name)
    """Done Test"""



def test_moor_basic():
    """Basic test Moor class"""
    keys = ('a', 'b', 'c')
    key = '_'.join(keys)
    assert key == 'a_b_c'

    # test staticmethod .tokey()
    assert Moor.tokey(keys) == key == 'a_b_c'
    assert Moor.tokey('a') == 'a'  # str unchanged
    assert Moor.tokey('a_b') == 'a_b'  # str unchanged

    with pytest.raises(KeyError):
        key = Moor.tokey((1, 2, 3))

    with pytest.raises(KeyError):
        key = Moor.tokey(1)

    with pytest.raises(KeyError):
        key = Moor.tokey(("a_", "b", "c"))

    assert Moor.tokey(("a", "b", "")) == "a_b_"   # empty trailing part

    assert Moor.tokey(("", "a", "b")) == "_a_b"   # empty leading part

    # Test staticmethod .tokeys()
    assert Moor.tokeys(key) == keys
    assert Moor.tokeys('') == ('', )
    assert Moor.tokeys('a') == ('a', )

    assert Moor.tokey(Moor.tokeys(key)) == key
    assert Moor.tokeys(Moor.tokey(keys)) == keys

    moor = Moor()  # defaults
    assert moor == {}

    assert isinstance(moor, dict)
    assert issubclass(Moor, dict)

    moor['a'] = 5
    moor['a_b'] = 6
    assert moor['a'] == 5
    assert 'a' in moor
    assert moor.get('a') == 5
    assert moor.a == 5
    moor.b = 8
    assert moor.b == 8
    assert moor['b'] == 8

    moor[keys] = 7
    assert list(moor.items()) == [('a', 5), ('a_b', 6), ('b', 8), ('a_b_c', 7)]

    assert moor.a_b == 6
    moor.a_b = 4
    assert moor.a_b == 4

    with pytest.raises(AttributeError):
        moor.c_d_e

    assert moor[keys] == 7
    assert keys in moor
    assert moor.get(keys) == 7

    assert moor[key] == 7
    assert key in moor
    assert moor.get(key) == 7

    moor[key] = 8
    assert moor[keys] == 8

    del moor[keys]
    assert key not in moor

    with pytest.raises(KeyError):
        del moor[key]

    with pytest.raises(KeyError):
        del moor[keys]

    moor[keys] = 8
    del moor[key]

    with pytest.raises(KeyError):
        del moor[keys]

    with pytest.raises(KeyError):
        del moor[key]

    assert moor.get('c') == None
    assert moor.get(("b", "c")) == None

    moor[''] = 10
    assert '' in moor
    assert moor[''] == 10


    with pytest.raises(KeyError):
        moor['c']

    with pytest.raises(KeyError):
        moor[1] = 'A'

    with pytest.raises(KeyError):
        moor[("a", 2)] = 'B'

    with pytest.raises(KeyError):
        moor[("a", 2)]

    moor = Moor(a=0, a_b=1, a_b_c=2)
    assert list(moor.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2)]

    moor = Moor([('a', 0), ('a_b', 1), ('a_b_c', 2)])
    assert list(moor.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2)]

    # test init with iterable using keys as tuples
    moor = Moor([(('a', ), 0), (('a', 'b'), 1), (('a','b', 'c'), 2)], d=4)
    assert list(moor.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2), ('d', 4)]

    # test init with dict using keys as tuples
    d = {}
    d[("a", )] = 0
    d[("a", "b")] = 1
    d[("a", "b", "c")] = 2
    moor = Moor(d, d=4)
    assert list(moor.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2), ('d', 4)]

    # test update with iterable using keys as tuples
    moor = Moor()
    moor.update([(('a', ), 0), (('a', 'b'), 1), (('a','b', 'c'), 2)], d=4)
    assert list(moor.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2), ('d', 4)]

    # test update with dict using keys as tuples
    d = {}
    d[("a", )] = 0
    d[("a", "b")] = 1
    d[("a", "b", "c")] = 2
    moor = Moor()
    moor.update(d, d=4)
    assert list(moor.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2), ('d', 4)]

    """Done Test"""




if __name__ == "__main__":
    test_renam()
    test_moor_basic()

