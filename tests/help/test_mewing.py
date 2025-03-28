# -*- encoding: utf-8 -*-
"""tests.help.test_mewing module

"""
import pytest

from hio.help import Mew, Renam


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



def test_mew_basic():
    """Basic test Mew class"""
    keys = ('a', 'b', 'c')
    key = '_'.join(keys)
    assert key == 'a_b_c'

    # test staticmethod .tokey()
    assert Mew.tokey(keys) == key == 'a_b_c'
    assert Mew.tokey('a') == 'a'  # str unchanged
    assert Mew.tokey('a_b') == 'a_b'  # str unchanged

    with pytest.raises(KeyError):
        key = Mew.tokey((1, 2, 3))

    with pytest.raises(KeyError):
        key = Mew.tokey(1)

    with pytest.raises(KeyError):
        key = Mew.tokey(("a_", "b", "c"))

    assert Mew.tokey(("a", "b", "")) == "a_b_"   # empty trailing part

    assert Mew.tokey(("", "a", "b")) == "_a_b"   # empty leading part

    # Test staticmethod .tokeys()
    assert Mew.tokeys(key) == keys
    assert Mew.tokeys('') == ('', )
    assert Mew.tokeys('a') == ('a', )

    assert Mew.tokey(Mew.tokeys(key)) == key
    assert Mew.tokeys(Mew.tokey(keys)) == keys

    mew = Mew()  # defaults
    assert mew == {}

    assert isinstance(mew, dict)
    assert issubclass(Mew, dict)

    mew['a'] = 5
    mew['a_b'] = 6
    assert mew['a'] == 5
    assert 'a' in mew
    assert mew.get('a') == 5
    assert mew.a == 5
    mew.b = 8
    assert mew.b == 8
    assert mew['b'] == 8

    mew[keys] = 7
    assert list(mew.items()) == [('a', 5), ('a_b', 6), ('b', 8), ('a_b_c', 7)]

    assert mew.a_b == 6
    mew.a_b = 4
    assert mew.a_b == 4

    with pytest.raises(AttributeError):
        mew.c_d_e

    assert mew[keys] == 7
    assert keys in mew
    assert mew.get(keys) == 7

    assert mew[key] == 7
    assert key in mew
    assert mew.get(key) == 7

    mew[key] = 8
    assert mew[keys] == 8

    del mew[keys]
    assert key not in mew

    with pytest.raises(KeyError):
        del mew[key]

    with pytest.raises(KeyError):
        del mew[keys]

    mew[keys] = 8
    del mew[key]

    with pytest.raises(KeyError):
        del mew[keys]

    with pytest.raises(KeyError):
        del mew[key]

    assert mew.get('c') == None
    assert mew.get(("b", "c")) == None

    mew[''] = 10
    assert '' in mew
    assert mew[''] == 10


    with pytest.raises(KeyError):
        mew['c']

    with pytest.raises(KeyError):
        mew[1] = 'A'

    with pytest.raises(KeyError):
        mew[("a", 2)] = 'B'

    with pytest.raises(KeyError):
        mew[("a", 2)]

    mew = Mew(a=0, a_b=1, a_b_c=2)
    assert list(mew.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2)]

    mew = Mew([('a', 0), ('a_b', 1), ('a_b_c', 2)])
    assert list(mew.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2)]

    # test init with iterable using keys as tuples
    mew = Mew([(('a', ), 0), (('a', 'b'), 1), (('a','b', 'c'), 2)], d=4)
    assert list(mew.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2), ('d', 4)]

    # test init with dict using keys as tuples
    d = {}
    d[("a", )] = 0
    d[("a", "b")] = 1
    d[("a", "b", "c")] = 2
    mew = Mew(d, d=4)
    assert list(mew.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2), ('d', 4)]

    # test update with iterable using keys as tuples
    mew = Mew()
    mew.update([(('a', ), 0), (('a', 'b'), 1), (('a','b', 'c'), 2)], d=4)
    assert list(mew.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2), ('d', 4)]

    # test update with dict using keys as tuples
    d = {}
    d[("a", )] = 0
    d[("a", "b")] = 1
    d[("a", "b", "c")] = 2
    mew = Mew()
    mew.update(d, d=4)
    assert list(mew.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2), ('d', 4)]

    """Done Test"""




if __name__ == "__main__":
    test_renam()
    test_mew_basic()

