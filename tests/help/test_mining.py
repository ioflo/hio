# -*- encoding: utf-8 -*-
"""tests.help.test_mining module

"""
import pytest

from hio.help import Mine, Renam


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



def test_mine_basic():
    """Basic test Mine class"""
    keys = ('a', 'b', 'c')
    key = '_'.join(keys)
    assert key == 'a_b_c'

    # test staticmethod .tokey()
    assert Mine.tokey(keys) == key == 'a_b_c'
    assert Mine.tokey('a') == 'a'  # str unchanged
    assert Mine.tokey('a_b') == 'a_b'  # str unchanged

    with pytest.raises(KeyError):
        key = Mine.tokey((1, 2, 3))

    with pytest.raises(KeyError):
        key = Mine.tokey(1)

    with pytest.raises(KeyError):
        key = Mine.tokey(("a_", "b", "c"))

    assert Mine.tokey(("a", "b", "")) == "a_b_"   # empty trailing part

    assert Mine.tokey(("", "a", "b")) == "_a_b"   # empty leading part

    # Test staticmethod .tokeys()
    assert Mine.tokeys(key) == keys
    assert Mine.tokeys('') == ('', )
    assert Mine.tokeys('a') == ('a', )

    assert Mine.tokey(Mine.tokeys(key)) == key
    assert Mine.tokeys(Mine.tokey(keys)) == keys

    mine = Mine()  # defaults
    assert mine == {}

    assert isinstance(mine, dict)
    assert issubclass(Mine, dict)

    mine['a'] = 5
    mine['a_b'] = 6
    assert mine['a'] == 5
    assert 'a' in mine
    assert mine.get('a') == 5
    assert mine.a == 5
    mine.b = 8
    assert mine.b == 8
    assert mine['b'] == 8

    mine[keys] = 7
    assert list(mine.items()) == [('a', 5), ('a_b', 6), ('b', 8), ('a_b_c', 7)]

    assert mine.a_b == 6
    mine.a_b = 4
    assert mine.a_b == 4

    with pytest.raises(AttributeError):
        mine.c_d_e

    assert mine[keys] == 7
    assert keys in mine
    assert mine.get(keys) == 7

    assert mine[key] == 7
    assert key in mine
    assert mine.get(key) == 7

    mine[key] = 8
    assert mine[keys] == 8

    del mine[keys]
    assert key not in mine

    with pytest.raises(KeyError):
        del mine[key]

    with pytest.raises(KeyError):
        del mine[keys]

    mine[keys] = 8
    del mine[key]

    with pytest.raises(KeyError):
        del mine[keys]

    with pytest.raises(KeyError):
        del mine[key]

    assert mine.get('c') == None
    assert mine.get(("b", "c")) == None

    mine[''] = 10
    assert '' in mine
    assert mine[''] == 10


    with pytest.raises(KeyError):
        mine['c']

    with pytest.raises(KeyError):
        mine[1] = 'A'

    with pytest.raises(KeyError):
        mine[("a", 2)] = 'B'

    with pytest.raises(KeyError):
        mine[("a", 2)]

    mine = Mine(a=0, a_b=1, a_b_c=2)
    assert list(mine.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2)]

    mine = Mine([('a', 0), ('a_b', 1), ('a_b_c', 2)])
    assert list(mine.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2)]

    # test init with iterable using keys as tuples
    mine = Mine([(('a', ), 0), (('a', 'b'), 1), (('a','b', 'c'), 2)], d=4)
    assert list(mine.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2), ('d', 4)]

    # test init with dict using keys as tuples
    d = {}
    d[("a", )] = 0
    d[("a", "b")] = 1
    d[("a", "b", "c")] = 2
    mine = Mine(d, d=4)
    assert list(mine.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2), ('d', 4)]

    # test update with iterable using keys as tuples
    mine = Mine()
    mine.update([(('a', ), 0), (('a', 'b'), 1), (('a','b', 'c'), 2)], d=4)
    assert list(mine.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2), ('d', 4)]

    # test update with dict using keys as tuples
    d = {}
    d[("a", )] = 0
    d[("a", "b")] = 1
    d[("a", "b", "c")] = 2
    mine = Mine()
    mine.update(d, d=4)
    assert list(mine.items()) == [('a', 0), ('a_b', 1), ('a_b_c', 2), ('d', 4)]

    """Done Test"""




if __name__ == "__main__":
    test_renam()
    test_mine_basic()

