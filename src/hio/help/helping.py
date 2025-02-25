# -*- encoding: utf-8 -*-
"""
hio.help.helping module

"""
import types
import functools
import inspect
import os
import errno
import stat
import json

import base64
import re

from collections import deque
from collections.abc import Iterable, Sequence, Generator
from abc import ABCMeta

import msgpack
import cbor2 as cbor


# Utilities
def isign(i):
    """
    Integer sign function
    Returns:
        (int): 1 if i > 0, -1 if i < 0, 0 otherwise

    """
    return (1 if i > 0 else -1 if i < 0 else 0)


def sceil(r):
    """
    Symmetric ceiling function
    Returns:
       sceil (int): value that is symmetric ceiling of r away from zero

    Because int() provides a symmetric floor towards zero, just inc int(r) by:
     1 when r - int(r) >  0  (r positive)
    -1 when r - int(r) <  0  (r negative)
     0 when r - int(r) == 0  (r integral already)
    abs(r) > abs(int(r) or 0 when abs(r)
    """
    return (int(r) + isign(r - int(r)))


def copyfunc(f, name=None):
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


def attributize(genie):
    """
    Decorator function:

    Python generators do not support adding attributes.
    Adding support for attributes provides a way to pass information
    from a WSGI App that returns a generator to a WSGI server via the generator
    after the WSGI app has already started returning its body. The hio.http.Server
    WSGI server looks for the attributes ._status and ._headers and substitutes
    these if present. This allows a streaming WSGI App body iterator to later
    modify the headers and status taht will be returned before the body iterator
    began iterating. This is useful for web hooks or backend requests that are
    serviced by an async coroutine based WSGI app so that they may leverage
    the streaming support of standard WSGI but use a the coroutine based
    hio.http.Server as an async WSGI server.

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


def isNonStringIterable(obj):
    """
    Returns: (bool) True if obj is non-string iterable, False otherwise

    Another way that is less future proof
    return (hasattr(x, '__iter__') and not isinstance(x, (str, bytes)))
    """
    return (not isinstance(obj, (str, bytes)) and isinstance(obj, Iterable))

nonStringIterable = isNonStringIterable  # legacy interface


def isNonStringSequence(obj):
    """
    Returns: (bool) True if obj is non-string sequence, False otherwise
    """
    return (not isinstance(obj, (str, bytes)) and isinstance(obj, Sequence) )

nonStringSequence = isNonStringSequence  # legacy interface


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


def ocfn(path, mode='r+', perm=(stat.S_IRUSR | stat.S_IWUSR)):
    """
    Atomically open or create file from filepath.

    If file already exists, Then open file using openMode
    Else create file using write update mode If not binary Else
        write update binary mode
    Returns file object

    If binary Then If new file open with write update binary mode

    x = stat.S_IRUSR | stat.S_IWUSR
    384 == 0o600
    436 == octal 0664
    """
    try:

        newfd = os.open(path, os.O_EXCL | os.O_CREAT | os.O_RDWR, perm)
        if "b" in mode:
            file = os.fdopen(newfd,"w+b")  # w+ truncate read and/or write
        else:
            file = os.fdopen(newfd,"w+")  # w+ truncate read and/or write

    except OSError as ex:
        if ex.errno == errno.EEXIST:
            file = open(path, mode)  # r+ do not truncate read and/or write
        else:
            raise
    return file


def dump(data, path):
    """
    Serialize data dict and write to file given by path where serialization is
    given by path's extension of either JSON, MsgPack, or CBOR for extension
    .json, .mgpk, or .cbor respectively
    """

    if ' ' in path:
        raise IOError(f"Invalid file path '{path}' contains space.")

    root, ext = os.path.splitext(path)
    if ext == '.json':
        with ocfn(path, "w+b") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
    elif ext == '.mgpk':
        with ocfn(path, "w+b") as f:
            msgpack.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
    elif ext == '.cbor':
        with ocfn(path, "w+b") as f:
            cbor.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
    else:
        raise IOError(f"Invalid file path ext '{path}' "
                      f"not '.json', '.mgpk', or 'cbor'.")


def load(path):
    """
    Return data read from file path as dict
    file may be either json, msgpack, or cbor given by extension .json, .mgpk, or
    .cbor respectively
    Otherwise raise IOError
    """
    root, ext = os.path.splitext(path)
    if ext == '.json':
        with ocfn(path, "rb") as f:
            it = json.load(f)
    elif ext == '.mgpk':
        with ocfn(path, "rb") as f:
            it = msgpack.load(f)
    elif ext == '.cbor':
        with ocfn(path, "rb") as f:
            it = cbor.load(f)
    else:
        raise IOError(f"Invalid file path ext '{path}' "
                     f"not '.json', '.mgpk', or 'cbor'.")

    return it


# Base64 utilities

# Mappings between Base64 Encode Index and Decode Characters
#  B64ChrByIdx is dict where each key is a B64 index and each value is the B64 char
#  B64IdxByChr is dict where each key is a B64 char and each value is the B64 index
# Map Base64 index to char
B64ChrByIdx = dict((index, char) for index, char in enumerate([chr(x) for x in range(65, 91)]))
B64ChrByIdx.update([(index + 26, char) for index, char in enumerate([chr(x) for x in range(97, 123)])])
B64ChrByIdx.update([(index + 52, char) for index, char in enumerate([chr(x) for x in range(48, 58)])])
B64ChrByIdx[62] = '-'
B64ChrByIdx[63] = '_'
# Map char to Base64 index
B64IdxByChr = {char: index for index, char in B64ChrByIdx.items()}

B64REX = rb'^[0-9A-Za-z_-]*\Z'   # [A-Za-z0-9\-\_]  bytes
# Usage: if Reb64.match(bext): or if not Reb64.match(bext): bext is bytes
Reb64 = re.compile(B64REX)  # compile is faster

def intToB64(i, l=1):
    """Converts int i to at least l Base64 chars as str.
    Returns:
        b64 (str): Base64 converstion of i of length minimum l. If more than
                    l chars are needed to represent i in Base64 then returned
                    str is lengthed appropriately. When less then l chars is
                    needed then returned str is prepadded with 'A' character.

    l is min number of b64 digits left padded with Base64 0 == "A" char
    The length of return bytes extended to accomodate full Base64 encoding of i
    """
    d = deque()  # deque of characters base64

    while l:
        d.appendleft(B64ChrByIdx[i % 64])
        i = i // 64
        if not i:
            break
    for j in range(l - len(d)):  # range(x)  x <= 0 means do not iterate
        d.appendleft("A")
    return ("".join(d))


def intToB64b(i, l=1):
    """Converts int i to at least l Base64 chars as bytes.

    Returns:
        b64 (bytes): Base64 converstion of i of length minimum l. If more than
                     l bytes are needed to represent i in Base64 then returned
                     bytes is extended appropriately. When less then l bytes
                     is needed then returned bytes is prepadded with b'A' bytes.

    Parameters:
        i (int): to be converted
        l (int): min number of b64 digits. When empty these are left padded with
                 Base64 0 == b'A' digits.
                 The length of return bytes is extended to accomodate full
                 Base64 encoding of i regardless of l.
    """
    return (intToB64(i=i, l=l).encode())


def b64ToInt(s):
    """Converts Base64 to int
    Returns:
        i (int): conversion s (str | bytes) to int

    Parameters:
        s (str | bytes): to be converted
    """
    if not s:
        raise ValueError("Empty string, conversion undefined.")
    if hasattr(s, 'decode'):
        s = s.decode("utf-8")
    i = 0
    for e, c in enumerate(reversed(s)):
        i |= B64IdxByChr[c] << (e * 6)  # same as i += B64IdxByChr[c] * (64 ** e)
    return i



def codeB64ToB2(s):
    """Convert Base64 chars in s to B2 bytes

    Returns:
        bs (bytes): conversion (decode) of s Base64 chars to Base2 bytes.
        Where the number of total bytes returned is equal to the minimun number of
        chars (octet) sufficient to hold the total converted concatenated chars from s,
        with one sextet per each Base64 char of s. Assumes no pad chars in s.


    Sextets are left aligned with pad bits in last (rightmost) byte to support
    mid padding of code portion with respect to rest of primitive.
    This is useful for decoding as bytes, code characters from the front of
    a Base64 encoded string of characters.

    Parameters:
        s (str | bytes): Base64 str or bytes to convert

    """
    i = b64ToInt(s)
    i <<= 2 * (len(s) % 4)  # add 2 bits right zero padding for each sextet
    n = sceil(len(s) * 3 / 4)  # compute min number of ocetets to hold all sextets
    return (i.to_bytes(n, 'big'))


def codeB2ToB64(b, l):
    """Convert l sextets from base2 b to base64 str

    Returns:
        code (str): conversion (encode) of l Base2 sextets from front of b
        to Base64 chars.

    One char for each of l sextets from front (left) of b.
    This is useful for encoding as code characters, sextets from the front of
    a Base2 bytes (byte string). Must provide l because of ambiguity between l=3
    and l=4. Both require 3 bytes in b. Trailing pad bits are removed so
    returned sextets as characters are right aligned .

    Parameters:
        b (bytes | str): target from which to nab sextets
        l (int): number of sextets to convert from front of b
    """
    if hasattr(b, 'encode'):
        b = b.encode("utf-8")  # convert to bytes
    n = sceil(l * 3 / 4)  # number of bytes needed for l sextets
    if n > len(b):
        raise ValueError("Not enough bytes in {} to nab {} sextets.".format(b, l))
    i = int.from_bytes(b[:n], 'big')  # convert only first n bytes to int
    # check if prepad bits are zero
    tbs = 2 * (l % 4)  # trailing bit size in bits
    i >>= tbs  # right shift out trailing bits to make right aligned
    return (intToB64(i, l))  # return as B64


def nabSextets(b, l):
    """Nab l sextets from front of b
    Returns:
        sextets (bytes): first l sextets from front (left) of b as bytes
        (byte string). Length of bytes returned is minimum sufficient to hold
        all l sextets. Last byte returned is right bit padded with zeros which
        is compatible with mid padded codes on front of primitives

    Parameters:
        b (bytes | str): target from which to nab sextets
        l (int): number of sextets to nab from front of b

    """
    if hasattr(b, 'encode'):
        b = b.encode()  # convert to bytes
    n = sceil(l * 3 / 4)  # number of bytes needed for l sextets
    if n > len(b):
        raise ValueError("Not enough bytes in {} to nab {} sextets.".format(b, l))
    i = int.from_bytes(b[:n], 'big')
    p = 2 * (l % 4)
    i >>= p  # strip of last bits
    i <<= p  # pad with empty bits
    return (i.to_bytes(n, 'big'))
