# -*- encoding: utf-8 -*-
"""
hio.help.helping module

"""
import types
import functools
import inspect

from collections.abc import Iterable, Sequence, Generator
from abc import ABCMeta

from multidict import MultiDict, CIMultiDict
from orderedset import OrderedSet as oset

def copy_func(f, name=None):
    """
    Copy a function in detail.
    To change name of func provide name parameter

    functools to update_wrapper assigns and updates following attributes
    WRAPPER_ASSIGNMENTS = ('__module__', '__name__', '__qualname__', '__doc__',
                       '__annotations__')
    WRAPPER_UPDATES = ('__dict__',)
    Based on
    https://stackoverflow.com/questions/6527633/how-can-i-make-a-deepcopy-of-a-function-in-python
    https://stackoverflow.com/questions/13503079/how-to-create-a-copy-of-a-python-function
    """
    g = types.FunctionType(f.__code__,
                           f.__globals__,
                           name=f.__name__,
                           argdefs=f.__defaults__,
                           closure=f.__closure__
                          )
    g = functools.update_wrapper(g, f)
    g.__kwdefaults__ = f.__kwdefaults__
    if name:
        g.__name__ = name
    return g


def repack(n, seq, default=None):
    """ Repacks seq into a generator of len n and returns the generator.
        The purpose is to enable unpacking into n variables.
        The first n-1 elements of seq are returned as the first n-1 elements of the
        generator and any remaining elements are returned in a tuple as the
        last element of the generator
        default (None) is substituted for missing elements when len(seq) < n

        Example:

        x = (1, 2, 3, 4)
        tuple(repack(3, x))
        (1, 2, (3, 4))

        x = (1, 2, 3)
        tuple(repack(3, x))
        (1, 2, (3,))

        x = (1, 2)
        tuple(repack(3, x))
        (1, 2, ())

        x = (1, )
        tuple(repack(3, x))
        (1, None, ())

        x = ()
        tuple(repack(3, x))
        (None, None, ())

    """
    it = iter(seq)
    for i in range(n - 1):
        yield next(it, default)
    yield tuple(it)


def just(n, seq, default=None):
    """ Returns a generator of just the first n elements of seq and substitutes
        default (None) for any missing elements. This guarantees that a generator of exactly
        n elements is returned. This is to enable unpacking into n varaibles

        Example:

        x = (1, 2, 3, 4)
        tuple(just(3, x))
        (1, 2, 3)
        x = (1, 2, 3)
        tuple(just(3, x))
        (1, 2, 3)
        x = (1, 2)
        tuple(just(3, x))
        (1, 2, None)
        x = (1, )
        tuple(just(3, x))
        (1, None, None)
        x = ()
        tuple(just(3, x))
        (None, None, None)

    """
    it = iter(seq)
    for i in range(n):
        yield next(it, default)


class NonStringIterable(metaclass=ABCMeta):
    """
    Allows isinstance check for iterable that is not a string
    if isinstance(x, NonStringIterable):
    """
    @classmethod
    def __subclasshook__(cls, C):
        if cls is NonStringIterable:
            if (not issubclass(C, (str, bytes)) and issubclass(C, Iterable)):
                return True
        return NotImplemented


class NonStringSequence(metaclass=ABCMeta):
    """
    Allows isinstance check for sequence that is not a string
    if isinstance(x, NonStringSequence):
    """
    @classmethod
    def __subclasshook__(cls, C):
        if cls is NonStringSequence:
            if (not issubclass(C, (str, bytes)) and issubclass(C, Sequence)):
                return True
        return NotImplemented


def nonStringIterable(obj):
    """
    Returns: (Boolean) True if obj is non-string iterable, False otherwise

    Another way that is less future proof
    return (hasattr(x, '__iter__') and not isinstance(x, (str, bytes)))
    """
    return (not isinstance(obj, (str, bytes)) and isinstance(obj, Iterable))


def nonStringSequence(obj):
    """
    Returns: (Boolean) True if obj is non-string sequence, False otherwise
    """
    return (not isinstance(obj, (str, bytes)) and isinstance(obj, Sequence) )


def isIterator(obj):
    """
    Returns True if obj is an iterator object, that is,

    has an __iter__ method
    has a __next__ method
    .__iter__ is callable and returns obj

    Otherwise returns False

    """
    if (hasattr(obj, "__iter__") and
        hasattr(obj, "__next__") and
        callable(obj.__iter__) and
        obj.__iter__() is obj
       ):
        return True
    return False


def attributize(genie):
    """
    Decorator function:

    Python generators do not support adding attributes.
    Adding support for attributes provides a way to pass information
    from a WSGI App that returns a generator to a WSGI server via the generator
    after the WSGI app has already started returning the its body. This allows
    a streaming WSGI App body iterator to later modify the headers and status
    returns before the body iterator began iterating. This is useful for web
    hooks or backend requents from a coroutine based async WSGI server and
    WSGI app that leverage the streaming support of standard WSGI.

    This decorator takes a Duck Typing approach to decorating
    a generator function or method that returns a new function type instance that
    when called will return a generator like object that supports attributes.
    the new wrapped object acts like a generator but with attributes.

    Parameters:
        genie (generator function, generator method): is either
            a generator function that returns a generator object
            a generator method that returns a generator object

    If genie is a generator function then a reference to its wrapper
         is injected as the first positional argument to the orginal
         generator function. The convention is to use the parameter 'me' to refer
         to the injected reference to the wrapper.

    If genie is a generator method, that is, its first parameter is 'self'
        then a reference to its wrapper is injected as the second
        positional argument to the original generator method. the convention
        is to use the parameter 'me' to refer to the injected reference to the
        wrapper so as not to collide with the 'self' instance reference.

    When wrapped the new type is AttributiveGenerator

    Usage:
    # decorated generator function
    @attributize
    def bar(me, req=None, rep=None):
        me._status = 400  # or copy from rep.status
        me._headers = odict(example="Hi")  # or copy from rep.headers
        yield b""
        yield b""
        yield b"Hello There"
        return b"Goodbye"

    gen = bar()
    msg = next(gen)  # attributes set after first next
    gen._status
    gen._headers

    # decorated generator method
    class R:
        @attributize
        def bar(self, me, req=None, rep=None):
            self.name = "Peter"
            me._status = 400  # or copy from rep.status
            me._headers = odict(example="Hi")  # or copy from rep.headers
            yield b""
            yield b""
            yield b"Hello There " + self.name.encode()
            return b"Goodbye"

    r = R()
    gen = r.bar()
    msg = next(gen)   # attributes set after first next
    gen._status
    gen._headers

    # use as function wrapper directly instead of as decorator
    def gf(me, x):  # convention injected reference to attributed wrapper is 'me'
        me.x = 5
        me.y = 'a'
        cnt = 0
        while cnt < x:
            yield cnt
            cnt += 1

    agf = attributize(gf)
    ag = agf(3)
    # body of gf is not run until first next call
    assert isIterator(ag)
    assert not hasattr(ag, 'x')
    assert not hasattr(ag, 'y')
    n = next(ag)  # first run here which sets up attributes
    assert n == 0
    assert hasattr(ag, 'x')
    assert hasattr(ag, 'y')
    assert ag.x == 5
    assert ag.y =='a'
    n = next(ag)
    assert n == 1

    Adding attributes to this injected reference makes them available
    as attributes of the resultant wrapper.

    The HTTP WSGI server at hio.core.http.serving.Server uses an instance of
    hio.core.http.serving.Responder to generate the response for each WSGI request.
    The Responder instance checks its WSGI app generator for existence of the
    attributes ._status and ._headers. If so then it overrides its default
    response status with ._status and updates its default response headers
    with the headers in ._header. This allows a backend (webhook) to conveniently
    influence the response status and headers. The response body is returned by
    the generator itself.

    Background:
    Unlike Python functions, Python generators do not support  custom attributes
    and the generator locals dict at .gi_frame.f_locals dissappears once the
    generator is complete so its inconvenient.

    Fixed attributes of generator objects.
    ['.__next__', '__iter__', 'close', 'gi_code', 'gi_frame', 'gi_running',
    'gi_yieldfrom', 'send', 'throw']
    """

    def wrapper(*args, **kwargs):
        """
        When called returns instance of AttributiveGenerator instead of generator.
        """
        def __iter__(self):  # default attribute
            return self

        def send(self):   # default attribute
            raise NotImplementedError

        def throw(self):   # default attribute
            raise NotImplementedError

        # use type() to create dynamic instance of class AttributiveGenerator
        # dict spec for type() is {'__iter__': lambda self: self, 'send': ,}
        tdict = { '__iter__': __iter__, 'send': send, 'throw':  throw,}
        AG = type("AttributiveGenerator", (Generator,), tdict)  # make custom type
        ag = AG()  # create  instance so we can inject it into genfunc

        # create generator and inject ag ref for me parameter  ag = me
        fargs = inspect.getfullargspec(genie).args
        if fargs and fargs[0] == 'self':
            gen = genie(args[0], ag, *args[1:], **kwargs)  # inject self and me
        else:
            gen = genie(ag, *args, **kwargs)  # inject me only

        # now replace default class references with real gen attributes. "duckify"
        for attr in ('__next__', 'close', 'send', 'throw',
                     'gi_code', 'gi_frame', 'gi_running', 'gi_yieldfrom'):
            setattr(AG, attr, getattr(gen, attr))

        functools.update_wrapper(wrapper=ag, wrapped=gen)  # fix up wrapper
        return ag

    return wrapper
