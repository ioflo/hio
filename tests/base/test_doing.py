# -*- encoding: utf-8 -*-
"""
tests.core.test_doing module

"""
import pytest

import os
import inspect

from hio.base import tyming
from hio.base import doing
from hio.base.doing import State
from hio.core.tcp import serving, clienting
from hio.core.serial import serialing


#  for testing purposes
class TryDoer(doing.Doer):
    """
    TryDoer supports testing with methods to record sends and yields

    Inherited Attributes:
        .done is Boolean completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.

    Attributes:
       .states is list of State namedtuples (tyme, context, feed, count)
       .count is context count

    Inherited Properties:
        .tyme is float ._tymist.tyme, relative cycle or artificial time
        .tock is float, desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Properties:

    Methods:
        .wind  injects ._tymist dependency
        .__call__ makes instance callable
            Appears as generator function that returns generator
        .do is generator method that returns generator
        .enter is enter context action method
        .recur is recur context action method or generator method
        .exit is exit context method
        .close is close context method
        .abort is abort context method
    """

    def __init__(self, **kwa):
        """
        Initialize instance.
        Parameters:
           tymist is Tymist instance
           tock is float seconds initial value of .tock

        """
        super(TryDoer, self).__init__(**kwa)
        self.states = []
        self.count = None

    def enter(self):
        """
        """
        feed = "Default"
        self.count = 0
        self.states.append(State(tyme=self.tyme, context="enter",
                                 feed=feed, count=self.count))

    def recur(self, tyme):
        """

        """
        self.count += 1
        self.states.append(State(tyme=self.tyme, context="recur",
                                 feed=tyme, count=self.count))
        if self.count > 3:
            return True  # complete
        return False  # incomplete

    def exit(self):
        """
        """
        self.count += 1
        self.states.append(State(tyme=self.tyme, context='exit',
                                 feed=None, count=self.count))

    def close(self):
        """
        """
        self.count += 1
        self.states.append(State(tyme=self.tyme, context='close',
                                 feed=None, count=self.count))

    def abort(self, ex):
        """
        """
        self.count += 1
        self.states.append(State(tyme=self.tyme, context='abort',
                                 feed=ex.args[0], count=self.count))



@doing.doize()
def tryDo(states, tymist, tock=0.0,  **opts):
    """
    Generator function test example non-class based generator.
    Calling this function returns generator
    """
    feed = "Default"
    count = 0

    try:
        # enter context

        states.append(State(tyme=tymist.tyme, context="enter", feed=feed, count=count))
        while (True):  # recur context
            feed = (yield (count))  # yields tock then waits for next send
            count += 1
            states.append(State(tyme=tymist.tyme, context="recur", feed=feed, count = count))
            if count > 3:
                break  # normal exit

    except GeneratorExit:  # close context, forced exit due to .close
        count += 1
        states.append(State(tyme=tymist.tyme, context='close', feed=feed, count=count))

    except Exception:  # abort context, forced exit due to uncaught exception
        count += 1
        states.append(State(tyme=tymist.tyme, context='abort', feed=feed, count=count))
        raise

    finally:  # exit context,  unforced exit due to normal exit of try
        count += 1
        states.append(State(tyme=tymist.tyme, context='exit', feed=feed, count=count))

    return (True)  # return value of yield from, or yield ex.value of StopIteration


def test_doify():
    """
    Test wrapper function doify()
    """
    def genfun(tymist=None, tock=0.0, **opts):
        tyme = yield(tock)

    assert inspect.isgeneratorfunction(genfun)

    gf0 = doing.doify(genfun, name='gf0', tock=0.25)
    gf1 = doing.doify(genfun, name='gf1', tock=0.125)

    assert inspect.isgeneratorfunction(gf0)
    assert inspect.isgeneratorfunction(gf1)
    assert id(gf0) != id(gf1)

    assert gf0.__name__ == 'gf0'
    assert gf1.__name__ == 'gf1'
    assert gf0.tock == 0.25
    assert gf1.tock == 0.125
    assert gf0.done == None
    assert gf1.done == None
    assert gf0.opts == dict()
    assert gf1.opts == dict()

    tymist = tyming.Tymist()

    g0 = gf0(tymist=tymist, tock=gf0.tock, **gf0.opts)
    assert inspect.isgenerator(g0)
    g1 = gf0(tymist=tymist, tock=gf1.tock, **gf1.opts)
    assert inspect.isgenerator(g1)

    assert id(g0) != id(g1)
    """End Test"""

def test_doize():
    """
    Test decorator @doize
    """
    @doing.doize(tock=0.25)
    def genfun(tymist=None, tock=0.0, **opts):
        tyme = yield(tock)

    assert inspect.isgeneratorfunction(genfun)
    assert genfun.tock == 0.25
    assert genfun.done == None
    assert genfun.opts == dict()

    tymist = tyming.Tymist()

    gen = genfun(tymist=tymist, tock=genfun.tock, **genfun.opts)
    assert inspect.isgenerator(gen)

    """End Test"""

def test_doer():
    """
    Test Doer base class
    """
    tock = 1.0
    doer = doing.Doer()
    assert isinstance(doer._tymist, tyming.Tymist)
    assert doer.tock == 0.0

    tymist = tyming.Tymist()
    doer = doing.Doer(tymist=tymist, tock=tock)
    assert doer._tymist == tymist
    assert doer.tock == tock == 1.0
    doer.tock = 0.0
    assert doer.tock ==  0.0

    # create generator use send and explicit close
    args = {}
    dog = doer(tymist=doer._tymist, tock=doer.tock, **args)
    assert inspect.isgenerator(dog)
    result = dog.send(None)
    assert result == doer.tock == 0.0
    result = dog.send("Hello")
    assert result == doer.tock == 0.0
    result = dog.send("Hi")
    assert result == doer.tock == 0.0
    result = dog.close()
    assert result == None  # no yielded value on close
    with pytest.raises(StopIteration):  # send after close
        try:
            result = dog.send("what?")
        except StopIteration as ex:
            assert ex.value == None
            raise

    # use next instead of send
    dog = doer(tymist=doer._tymist, tock=doer.tock)
    assert inspect.isgenerator(dog)
    result = next(dog)
    assert result == doer.tock == 0.0
    result = next(dog)
    assert result == doer.tock == 0.0
    result = next(dog)
    assert result == doer.tock == 0.0
    result = dog.close()
    assert result == None
    with pytest.raises(StopIteration):  # send after close
        try:
            result = dog.send("what?")
        except StopIteration as ex:
            assert ex.value == None
            raise

    #  use different tock
    dog = doer(tymist=doer._tymist, tock=tock)
    assert inspect.isgenerator(dog)
    result = next(dog)
    assert result  == tock == 1.0
    result = next(dog)
    assert result == tock == 1.0
    result = next(dog)
    assert result == tock == 1.0
    result = dog.close()
    assert result == None

    with pytest.raises(StopIteration):
        result = dog.send("what?")

    doer.tock = 0.0

    dog = doer(tymist=doer._tymist, tock=tock)
    assert inspect.isgenerator(dog)
    result = next(dog)
    assert result == tock == 1.0
    result = next(dog)
    assert result == 1.0
    result = next(dog)
    assert result == 1.0
    result = dog.close()
    assert result == None
    with pytest.raises(StopIteration):  # send after close
        try:
            result = dog.send("what?")
        except StopIteration as ex:
            assert ex.value == None
            raise
    """End Test """

def test_redoer():
    """
    Test ReDoer base class
    """
    tock = 1.0
    doer = doing.ReDoer()
    assert isinstance(doer._tymist, tyming.Tymist)
    assert doer.tock == 0.0

    tymist = tyming.Tymist()
    doer = doing.ReDoer(tymist=tymist, tock=tock)
    assert doer._tymist == tymist
    assert doer.tock == tock == 1.0
    doer.tock = 0.0
    assert doer.tock ==  0.0

    # create generator use send and run until normal exit. emulates Doist.ready
    args = {}
    dog = doer(tymist=doer._tymist, tock=doer.tock, **args)
    assert inspect.isgenerator(dog)

    result = dog.send(None)
    assert result == doer.tock == 0.0

    tymist.tick()
    result = dog.send(tymist.tyme)
    assert result == doer.tock == 0.0

    tymist.tick()
    result = dog.send(tymist.tyme)
    assert result == doer.tock == 0.0

    tymist.tick()
    with pytest.raises(StopIteration):
        try:
            result = dog.send(tymist.tyme)
        except StopIteration as ex:
            assert ex.value == True
            raise

    tymist.tick()
    with pytest.raises(StopIteration):  # send after break
        try:
            result = dog.send(tymist.tyme)
        except StopIteration as ex:
            assert ex.value == None
            raise

    # create generator use send and then explicit close. emulates Doist.ready
    args = {}
    dog = doer(tymist=doer._tymist, tock=doer.tock, **args)
    assert inspect.isgenerator(dog)

    result = dog.send(None)
    assert result == doer.tock == 0.0

    tymist.tick()
    result = dog.send(tymist.tyme)
    assert result == doer.tock == 0.0

    result = dog.close()
    assert result == None  # no yielded value on close

    tymist.tick()
    with pytest.raises(StopIteration):  # send after close
        try:
            result = dog.send(tymist.tyme)
        except StopIteration as ex:
            assert ex.value == None
            raise


    # use next instead of send
    args = {}
    dog = doer(tymist=doer._tymist, tock=doer.tock, **args)
    assert inspect.isgenerator(dog)

    result = next(dog)
    assert result == doer.tock == 0.0

    result = next(dog)
    assert result == doer.tock == 0.0

    result = dog.close()
    assert result == None  # no yielded value on close

    tymist.tick()
    with pytest.raises(StopIteration):  # send after close
        try:
            result = dog.send(tymist.tyme)
        except StopIteration as ex:
            assert ex.value == None
            raise

    """End Test """

def test_dodoer():
    """
    Test DoDoer class
    """
    tock = 1.0
    doer = doing.DoDoer()
    assert isinstance(doer._tymist, tyming.Tymist)
    assert doer.tock == 0.0

    tymist = tyming.Tymist()
    doer = doing.DoDoer(tymist=tymist, tock=tock)
    assert doer._tymist == tymist
    assert doer.tock == tock == 1.0
    doer.tock = 0.0
    assert doer.tock ==  0.0

    # create generator use send and run until normal exit. emulates Doist.ready
    args = {}
    dog = doer(tymist=doer._tymist, tock=doer.tock, **args)
    assert inspect.isgenerator(dog)
    assert doer.doers == []


    result = dog.send(None)
    assert result == doer.tock == 0.0
    assert doer.doers == []

    tymist.tick()  # empty doers does list so ends right away
    with pytest.raises(StopIteration):
        try:
            result = dog.send(tymist.tyme)
        except StopIteration as ex:
            assert ex.value == True
            raise

    tymist.tick()
    with pytest.raises(StopIteration):  # send after break
        try:
            result = dog.send(tymist.tyme)
        except StopIteration as ex:
            assert ex.value == None
            raise


    # create some doers
    doer0 = doing.Doer()
    doer1 = doing.Doer()
    doer2 = doing.Doer()

    doers = [doer0, doer1, doer2]

    # create generator use send and then explicit close. emulates Doist.ready
    args = {}
    dog = doer(tymist=doer._tymist, tock=doer.tock, doers=doers, **args)
    assert inspect.isgenerator(dog)
    assert doer.doers == []

    result = dog.send(None)
    assert result == doer.tock == 0.0
    assert doer.doers == doers

    tymist.tick()
    result = dog.send(tymist.tyme)
    assert result == doer.tock == 0.0

    tymist.tick()
    result = dog.send(tymist.tyme)
    assert result == doer.tock == 0.0

    result = dog.close()
    assert result == None  # no yielded value on close

    tymist.tick()
    with pytest.raises(StopIteration):  # send after close
        try:
            result = dog.send(tymist.tyme)
        except StopIteration as ex:
            assert ex.value == None
            raise
    """End Test """

def test_exampleDo():
    """
    Test exampleDo generator function non-class based
    """
    exDo = doing.exDo
    assert inspect.isgeneratorfunction(exDo)
    assert hasattr(exDo, "tock")
    assert hasattr(exDo, "opts")
    assert "states" in  exDo.opts
    assert exDo.opts["states"] == None
    exDo.opts["states"] = []

    tymist = tyming.Tymist()

    dog = exDo(tymist=tymist, tock=exDo.tock, **exDo.opts)
    assert inspect.isgenerator(dog)
    tock = dog.send(None)
    assert tock == 0.0
    tock = dog.send("Hello")
    assert tock == 0.0
    tock = dog.send("Hi")
    assert tock == 0.0
    tock = dog.close()
    assert tock == None
    with pytest.raises(StopIteration):
        tock = dog.send("what?")
    assert exDo.opts["states"] == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                                   State(tyme=0.0, context='recur', feed='Hello', count=1),
                                   State(tyme=0.0, context='recur', feed='Hi', count=2),
                                   State(tyme=0.0, context='close', feed=None, count=3),
                                   State(tyme=0.0, context='exit', feed=None, count=4)]

    exDo.opts["states"] = []
    dog = exDo(tymist=tymist, tock=1.0, **exDo.opts)
    assert inspect.isgenerator(dog)
    tock = dog.send(None)
    assert tock == 1.0
    tock = dog.send("Hello")
    assert tock == 1.0
    tock = dog.send("Hi")
    assert tock == 1.0
    tock = dog.close()
    assert tock == None
    with pytest.raises(StopIteration):
        tock = dog.send("what?")
    assert exDo.opts["states"] == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                                   State(tyme=0.0, context='recur', feed='Hello', count=1),
                                   State(tyme=0.0, context='recur', feed='Hi', count=2),
                                   State(tyme=0.0, context='close', feed=None, count=3),
                                   State(tyme=0.0, context='exit', feed=None, count=4)]


    exDo.opts["states"] = []
    dog = exDo(tymist=tymist, tock=1.0, **exDo.opts)
    assert inspect.isgenerator(dog)
    tock = next(dog)
    assert tock == 1.0
    tock = next(dog)
    assert tock == 1.0
    tock = next(dog)
    assert tock == 1.0
    tock = dog.close()
    assert tock == None
    with pytest.raises(StopIteration):
        tock = dog.send("what?")
    assert exDo.opts["states"] == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                                   State(tyme=0.0, context='recur', feed=None, count=1),
                                   State(tyme=0.0, context='recur', feed=None, count=2),
                                   State(tyme=0.0, context='close', feed=None, count=3),
                                   State(tyme=0.0, context='exit', feed=None, count=4)]

    """End Test """


def test_trydoer_break():
    """
    Test WhoDoer testing class with break to normal exit
    """
    tymist = tyming.Tymist(tock=0.125)
    doer = TryDoer(tymist=tymist, tock=0.25)
    assert doer._tymist == tymist
    assert doer._tymist.tock == 0.125
    assert doer.tock == 0.25
    assert doer.states ==  []
    assert tymist.tyme == 0.0

    do = doer(tymist=doer._tymist, tock=doer.tock)
    assert inspect.isgenerator(do)
    result = do.send(None)
    assert result == 0.25
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0)]
    result = do.send("Hello")
    assert result  == 0.25
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1)]


    tymist.tick()
    result = do.send("Hi")
    assert result ==  0.25
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2)]
    tymist.tick()
    result = do.send("Blue")
    assert result == 0.25
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2),
                           State(tyme=0.25, context='recur', feed='Blue', count=3)]

    tymist.tick()
    try:
        result = do.send("Red")
    except StopIteration as ex:
        assert ex.value == True  #  clean return
        assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                               State(tyme=0.0, context='recur', feed='Hello', count=1),
                               State(tyme=0.125, context='recur', feed='Hi', count=2),
                               State(tyme=0.25, context='recur', feed='Blue', count=3),
                               State(tyme=0.375, context='recur', feed='Red', count=4),
                               State(tyme=0.375, context='exit', feed=None, count=5)]

    # send after break
    tymist.tick()
    try:
        result = do.send("Red")
    except StopIteration as ex:
        assert ex.value == None  #  after break no StopIteration value
        assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                               State(tyme=0.0, context='recur', feed='Hello', count=1),
                               State(tyme=0.125, context='recur', feed='Hi', count=2),
                               State(tyme=0.25, context='recur', feed='Blue', count=3),
                               State(tyme=0.375, context='recur', feed='Red', count=4),
                               State(tyme=0.375, context='exit', feed=None, count=5)]
    """End Test """


def test_trydoer_close():
    """
    Test WhoDoer testing class with close to force exit
    """
    tymist = tyming.Tymist(tock=0.125)
    doer = TryDoer(tymist=tymist, tock=0.25)
    assert doer._tymist == tymist
    assert doer._tymist.tock == 0.125
    assert doer.tock == 0.25
    assert doer.states ==  []
    assert tymist.tyme == 0.0

    do = doer(tymist=doer._tymist, tock=doer.tock)
    assert inspect.isgenerator(do)
    result = do.send(None)
    assert result == 0.25
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0)]
    result = do.send("Hello")
    assert result  == 0.25
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1)]


    tymist.tick()
    result = do.send("Hi")
    assert result ==  0.25
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2)]
    tymist.tick()
    result = do.close()
    assert result == None  # not clean return no return from close
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2),
                           State(tyme=0.25, context='close', feed=None, count=3),
                           State(tyme=0.25, context='exit', feed=None, count=4)]

    # send after close
    tymist.tick()
    try:
        result = do.send("what?")
    except StopIteration as ex:
        assert ex.value == None  # after close no StopIteration value
        assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                               State(tyme=0.0, context='recur', feed='Hello', count=1),
                               State(tyme=0.125, context='recur', feed='Hi', count=2),
                               State(tyme=0.25, context='close', feed=None, count=3),
                               State(tyme=0.25, context='exit', feed=None, count=4)]

    """End Test """


def test_trydoer_throw():
    """
    Test WhoDoer testing class with throw to force exit
    """
    tymist = tyming.Tymist(tock=0.125)
    doer = TryDoer(tymist=tymist, tock=0.25)
    assert doer._tymist == tymist
    assert doer._tymist.tock == 0.125
    assert doer.tock == 0.25
    assert doer.states ==  []
    assert tymist.tyme == 0.0

    do = doer(tymist=doer._tymist, tock=doer.tock)
    assert inspect.isgenerator(do)
    result = do.send(None)
    assert result == 0.25
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0)]
    result = do.send("Hello")
    assert result  == 0.25
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1)]


    tymist.tick()
    result = do.send("Hi")
    assert result ==  0.25
    assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2)]
    tymist.tick()
    try:
        result = do.throw(ValueError, "Bad")
    except ValueError as ex:
        assert ex.args[0] == "Bad"  # exception alue is thrown value
        assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                                State(tyme=0.0, context='recur', feed='Hello', count=1),
                                State(tyme=0.125, context='recur', feed='Hi', count=2),
                                State(tyme=0.25, context='abort', feed='Bad', count=3),
                                State(tyme=0.25, context='exit', feed=None, count=4)]

    # send after throw
    tymist.tick()
    try:
        result = do.send("what?")
    except StopIteration as ex:
        assert ex.value == None  # after throw no StopIteration value
        assert doer.states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                                State(tyme=0.0, context='recur', feed='Hello', count=1),
                                State(tyme=0.125, context='recur', feed='Hi', count=2),
                                State(tyme=0.25, context='abort', feed='Bad', count=3),
                                State(tyme=0.25, context='exit', feed=None, count=4)]


def test_trydo_break():
    """
    Test trialdog testing function example with break to normal exit
    """
    assert inspect.isgeneratorfunction(tryDo)
    assert hasattr(tryDo, "tock")
    assert hasattr(tryDo, "opts")

    tymist = tyming.Tymist(tock=0.125)
    assert tymist.tyme == 0.0
    states = []

    do = tryDo(states=states, tymist=tymist, tock=0.25)
    assert inspect.isgenerator(do)
    result = do.send(None)
    assert result == 0
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0)]
    result = do.send("Hello")
    assert result == 1
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1)]
    tymist.tick()
    result = do.send("Hi")
    assert result ==  2
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2)]
    tymist.tick()
    result = do.send("Blue")
    assert result == 3
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2),
                           State(tyme=0.25, context='recur', feed='Blue', count=3)]

    tymist.tick()
    try:
        result = do.send("Red")
    except StopIteration as ex:
        assert ex.value == True  #  clean return
        assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                               State(tyme=0.0, context='recur', feed='Hello', count=1),
                               State(tyme=0.125, context='recur', feed='Hi', count=2),
                               State(tyme=0.25, context='recur', feed='Blue', count=3),
                               State(tyme=0.375, context='recur', feed='Red', count=4),
                               State(tyme=0.375, context='exit', feed='Red', count=5)]

    # send after break
    tymist.tick()
    try:
        result = do.send("Red")
    except StopIteration as ex:
        assert ex.value == None  #  no value after already finished
        assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                               State(tyme=0.0, context='recur', feed='Hello', count=1),
                               State(tyme=0.125, context='recur', feed='Hi', count=2),
                               State(tyme=0.25, context='recur', feed='Blue', count=3),
                               State(tyme=0.375, context='recur', feed='Red', count=4),
                               State(tyme=0.375, context='exit', feed='Red', count=5)]
    """End Test """


def test_trydo_close():
    """
    Test traildog testing function example with close to force exit
    """
    tymist = tyming.Tymist(tock=0.125)
    assert tymist.tyme == 0.0
    states = []

    do = tryDo(states=states, tymist=tymist, tock=0.25)
    assert inspect.isgenerator(do)
    result = do.send(None)
    assert result == 0
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0)]
    result = do.send("Hello")
    assert result  == 1
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1)]


    tymist.tick()
    result = do.send("Hi")
    assert result ==  2
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2)]
    tymist.tick()
    result = do.close()
    assert result == None
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2),
                           State(tyme=0.25, context='close', feed='Hi', count=3),
                           State(tyme=0.25, context='exit', feed='Hi', count=4)]

    tymist.tick()
    try:
        result = do.send("what?")
    except StopIteration as ex:
        assert ex.value == None  # not clean return
        assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                               State(tyme=0.0, context='recur', feed='Hello', count=1),
                               State(tyme=0.125, context='recur', feed='Hi', count=2),
                               State(tyme=0.25, context='close', feed='Hi', count=3),
                               State(tyme=0.25, context='exit', feed='Hi', count=4)]

    """End Test """


def test_trydo_throw():
    """
    Test trialdog testing function example with throw to force exit
    """
    tymist = tyming.Tymist(tock=0.125)
    assert tymist.tyme == 0.0
    states = []

    do = tryDo(states=states, tymist=tymist, tock=0.25)
    assert inspect.isgenerator(do)
    result = do.send(None)
    assert result == 0
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0)]
    result = do.send("Hello")
    assert result  == 1
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1)]


    tymist.tick()
    result = do.send("Hi")
    assert result ==  2
    assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                           State(tyme=0.0, context='recur', feed='Hello', count=1),
                           State(tyme=0.125, context='recur', feed='Hi', count=2)]
    tymist.tick()
    try:
        result = do.throw(ValueError, "Bad")
    except ValueError as ex:
        assert ex.args[0] == "Bad"
        assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                                State(tyme=0.0, context='recur', feed='Hello', count=1),
                                State(tyme=0.125, context='recur', feed='Hi', count=2),
                                State(tyme=0.25, context='abort', feed='Hi', count=3),
                                State(tyme=0.25, context='exit', feed='Hi', count=4)]

    tymist.tick()
    try:
        result = do.send("what?")
    except StopIteration as ex:
        assert ex.value == None  # not clean return
        assert states == [State(tyme=0.0, context='enter', feed='Default', count=0),
                                State(tyme=0.0, context='recur', feed='Hello', count=1),
                                State(tyme=0.125, context='recur', feed='Hi', count=2),
                                State(tyme=0.25, context='abort', feed='Hi', count=3),
                                State(tyme=0.25, context='exit', feed='Hi', count=4)]



def test_server_client():
    """
    Test ServerDoer ClientDoer classes
    """
    tock = 0.03125
    ticks = 16
    limit = ticks *  tock
    doist = doing.Doist(tock=tock, real=True, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == limit == 0.5
    assert doist.doers == []

    port = 6120
    server = serving.Server(host="", port=port)
    client = clienting.Client(host="localhost", port=port)

    serdoer = doing.ServerDoer(tymist=doist, server=server)
    assert serdoer.server.tymist == serdoer._tymist == doist
    assert serdoer.server ==  server
    clidoer = doing.ClientDoer(tymist=doist, client=client)
    assert clidoer.client.tymist == clidoer._tymist == doist
    assert clidoer.client == client

    assert serdoer.tock == 0.0  # ASAP
    assert clidoer.tock == 0.0  # ASAP

    doers = [serdoer, clidoer]
    for doer in doers:
        assert doer._tymist == doist

    msgTx = b"Hello me maties!"
    clidoer.client.tx(msgTx)

    doist.do(doers=doers)
    assert doist.tyme == limit
    assert server.opened == False
    assert client.opened == False

    assert not client.txes
    ca, ix = list(server.ixes.items())[0]
    msgRx = bytes(ix.rxbs)
    assert msgRx == msgTx

    """End Test """

def test_echo_server_client():
    """
    Test EchoServerDoer ClientDoer classes
    """
    tock = 0.03125
    ticks = 16
    limit = ticks *  tock
    doist = doing.Doist(tock=tock, real=True, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == limit == 0.5
    assert doist.doers == []

    port = 6120
    server = serving.Server(host="", port=port)
    client = clienting.Client(host="localhost", port=port)

    serdoer = doing.EchoServerDoer(tymist=doist, server=server)
    assert serdoer.server.tymist == serdoer._tymist == doist
    assert serdoer.server ==  server
    clidoer = doing.ClientDoer(tymist=doist, client=client)
    assert clidoer.client.tymist == clidoer._tymist == doist

    assert serdoer.tock == 0.0  # ASAP
    assert clidoer.tock == 0.0  # ASAP

    doers = [serdoer, clidoer]
    for doer in doers:
        assert doer._tymist == doist

    msgTx = b"Hello me maties!"
    clidoer.client.tx(msgTx)

    doist.do(doers=doers)
    assert doist.tyme == limit
    assert server.opened == False
    assert client.opened == False

    assert not client.txes
    msgEx = bytes(client.rxbs)  # echoed back message
    assert msgEx == msgTx

    ca, ix = list(server.ixes.items())[0]
    assert bytes(ix.rxbs) == b""  # empty server rxbs becaue echoed

    """End Test """


def test_echo_console():
    """
    Test EchoConsoleDoer class

    Must run in WindIDE with Debug I/O configured as external console
    """
    port = os.ctermid()  # default to console

    try:  # check to see if running in external console
        fd = os.open(port, os.O_NONBLOCK | os.O_RDWR | os.O_NOCTTY)
    except OSError as ex:
        # maybe complain here
        return  # not in external console
    else:
        os.close(fd)  #  cleanup


    tock = 0.03125
    ticks = 16
    limit = 0.0
    # limit = ticks *  tock
    doist = doing.Doist(tock=tock, real=True, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == 0.0
    # assert doist.limit == limit == 0.5
    assert doist.doers == []

    console = serialing.Console()
    echoer = doing.EchoConsoleDoer(console=console)

    doers = [echoer]
    doist.do(doers=doers)
    # assert doist.tyme == limit
    assert console.opened == False


    """End Test """


if __name__ == "__main__":
    test_echo_console()
