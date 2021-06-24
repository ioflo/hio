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


def test_non_string_iterable():
    """
    Test the metaclass nonStringIterable
    """
    a = bytearray(b'abc')
    w = dict(a=1, b=2, c=3)
    x = 'abc'
    y = b'abc'
    z = [1, 2, 3]

    assert isinstance(a, helping.NonStringIterable)
    assert isinstance(w, helping.NonStringIterable)
    assert not isinstance(x, helping.NonStringIterable)
    assert not isinstance(y, helping.NonStringIterable)
    assert isinstance(z, helping.NonStringIterable)


def test_non_string_sequence():
    """
    Test the metaclass nonStringSequence
    """
    a = bytearray(b'abc')
    w = dict(a=1, b=2, c=3)
    x = 'abc'
    y = b'abc'
    z = [1, 2, 3]

    assert isinstance(a, helping.NonStringSequence)
    assert not isinstance(w, helping.NonStringSequence)
    assert not isinstance(x, helping.NonStringSequence)
    assert not isinstance(y, helping.NonStringSequence)
    assert isinstance(z, helping.NonStringSequence)


def testIsIterator(self):
    """
    Test the utility function isIterator
    """
    o = [1, 2, 3]
    assert not helping.isIterator(o)
    i = iter(o)
    assert helping.isIterator(i)

    def genf():
        yield ""
        yield ""

    assert not helping.isIterator(genf))
    gen = genf()
    assert helping.isIterator(gen))


def testAttributize(self):
    """
    Test the utility decorator attributize generator
    """
    global headed

    console.terse("{0}\n".format(self.testAttributize.__doc__))

    def gf(skin, x):
        skin.x = 5
        skin.y = 'a'
        cnt = 0
        while cnt < x:
            yield cnt
            cnt += 1

    agf = classing.attributize(gf)
    ag = agf(3)
    self.assertTrue(classing.isIterator(ag))
    self.assertFalse(hasattr(ag, 'x'))
    self.assertFalse(hasattr(ag, 'y'))
    n = next(ag)  # body of gf is not run until first next call
    self.assertEqual(n, 0)
    self.assertTrue(hasattr(ag, 'x'))
    self.assertTrue(hasattr(ag, 'y'))
    self.assertEqual(ag.x, 5)
    self.assertEqual(ag.y, 'a')
    n = next(ag)
    self.assertEqual(n, 1)


    # Set up like WSGI for generator function
    @classing.attributize
    def bar(skin, req=None, rep=None):
        """
        Generator function with "skin" parameter for skin wrapper to
        attach attributes
        """
        skin._status = 400
        skin._headers = odict(example="Hi")
        yield b""
        yield b""
        yield b"Hello There"
        return b"Goodbye"

    # now use it like WSGI server does
    msgs = []
    gen = bar()
    self.assertTrue(classing.isIterator(gen))
    self.assertFalse(hasattr(gen, '_status'))
    self.assertFalse(hasattr(gen, '_headers'))

    headed = False

    def write(msg):
        """
        Simulate WSGI write
        """
        global headed

        if not headed:  # add headers
            if hasattr(gen, "_status"):
                if gen._status is not None:
                    msgs.append(str(gen._status))
            if hasattr(gen, "_headers"):
                for key, val in gen._headers.items():
                    msgs.append("{}={}".format(key, val))

            headed = True

        msgs.append(msg)

    igen = iter(gen)
    self.assertIs(igen, gen)
    done = False
    while not done:
        try:
            msg = next(igen)
        except StopIteration as ex:
            if hasattr(ex, "value") and ex.value:
                write(ex.value)
            write(b'')  # in case chunked send empty chunk to terminate
            done = True
        else:
            if msg:  # only write if not empty allows async processing
                write(msg)

    self.assertEqual(msgs, ['400', 'example=Hi', b'Hello There', b'Goodbye', b''])


    # Set up like WSGI for generator method
    class R:
        @classing.attributize
        def bar(self, skin, req=None, rep=None):
            """
            Generator function with "skin" parameter for skin wrapper to
            attach attributes
            """
            self.name = "Peter"
            skin._status = 400
            skin._headers = odict(example="Hi")
            yield b""
            yield b""
            yield b"Hello There " + self.name.encode()
            return b"Goodbye"

    # now use it like WSGI server does
    r = R()
    msgs = []
    gen = r.bar()
    self.assertTrue(classing.isIterator(gen))
    self.assertFalse(hasattr(gen, '_status'))
    self.assertFalse(hasattr(gen, '_headers'))

    headed = False

    def write(msg):
        """
        Simulate WSGI write
        """
        global headed

        if not headed:  # add headers
            if hasattr(gen, "_status"):
                if gen._status is not None:
                    msgs.append(str(gen._status))
            if hasattr(gen, "_headers"):
                for key, val in gen._headers.items():
                    msgs.append("{}={}".format(key, val))

            headed = True

        msgs.append(msg)

    igen = iter(gen)
    self.assertIs(igen, gen)
    done = False
    while not done:
        try:
            msg = next(igen)
        except StopIteration as ex:
            if hasattr(ex, "value") and ex.value:
                write(ex.value)
            write(b'')  # in case chunked send empty chunk to terminate
            done = True
        else:
            if msg:  # only write if not empty allows async processing
                write(msg)

    self.assertEqual(msgs, ['400', 'example=Hi', b'Hello There Peter', b'Goodbye', b''])




if __name__ == "__main__":
    test_non_string_sequence()
