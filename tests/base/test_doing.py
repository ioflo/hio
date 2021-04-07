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
       .stop is stop count where doer completes

    Inherited Properties:
        .tyme is float relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        .tymth is function wrapper closure returned by Tymist .tymeth() method.
            When .tymth is called it returns associated Tymist .tyme.
            .tymth provides injected dependency on Tymist tyme base.
        .tock is float, desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Properties:

    Methods:
        .wind  injects ._tymth dependency from associated Tymist to get its .tyme
        .__call__ makes instance callable
            Appears as generator function that returns generator
        .do is generator method that returns generator
        .enter is enter context action method
        .recur is recur context action method or generator method
        .exit is exit context method
        .close is close context method
        .abort is abort context method
    """

    def __init__(self, stop=3, **kwa):
        """
        Initialize instance.
        Inherited Parameters:
           tymist is Tymist instance
           tock is float seconds initial value of .tock
        Parameters:
           stop is count when complete

        """
        super(TryDoer, self).__init__(**kwa)
        self.states = []
        self.count = None
        self.stop = stop

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
        if self.count > self.stop:
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
def tryDo(states, tymth, tock=0.0,  **opts):
    """
    Generator function test example non-class based generator.
    Calling this function returns generator
    """
    feed = "Default"
    count = 0

    try:
        # enter context

        states.append(State(tyme=tymth(), context="enter", feed=feed, count=count))
        while (True):  # recur context
            feed = (yield (count))  # yields tock then waits for next send
            count += 1
            states.append(State(tyme=tymth(), context="recur", feed=feed, count = count))
            if count > 3:
                break  # normal exit

    except GeneratorExit:  # close context, forced exit due to .close
        count += 1
        states.append(State(tyme=tymth(), context='close', feed=feed, count=count))

    except Exception:  # abort context, forced exit due to uncaught exception
        count += 1
        states.append(State(tyme=tymth(), context='abort', feed=feed, count=count))
        raise

    finally:  # exit context,  unforced exit due to normal exit of try
        count += 1
        states.append(State(tyme=tymth(), context='exit', feed=feed, count=count))

    return (True)  # return value of yield from, or yield ex.value of StopIteration


def test_doify():
    """
    Test wrapper function doify()
    """
    def genfun(tymth, tock=0.0, **opts):
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

    g0 = gf0(tymth=tymist.tymen(), tock=gf0.tock, **gf0.opts)
    assert inspect.isgenerator(g0)
    g1 = gf0(tymth=tymist.tymen(), tock=gf1.tock, **gf1.opts)
    assert inspect.isgenerator(g1)

    assert id(g0) != id(g1)
    """End Test"""

def test_doize():
    """
    Test decorator @doize
    """
    @doing.doize(tock=0.25)
    def genfun(tymth, tock=0.0, **opts):
        tyme = yield(tock)

    assert inspect.isgeneratorfunction(genfun)
    assert genfun.tock == 0.25
    assert genfun.done == None
    assert genfun.opts == dict()

    tymist = tyming.Tymist()

    gen = genfun(tymth=tymist.tymen(), tock=genfun.tock, **genfun.opts)
    assert inspect.isgenerator(gen)
    """End Test"""


def test_doize_with_bound_method():
    """
    Test decorator @doize with bound method returning generator
    """
    #@doing.doize(tock=0.25)
    #def genfun(tymth, tock=0.0, **opts):
        #tyme = yield(tock)

    #assert inspect.isgeneratorfunction(genfun)
    #assert genfun.tock == 0.25
    #assert genfun.done == None
    #assert genfun.opts == dict()

    #tymist = tyming.Tymist()

    #gen = genfun(tymth=tymist.tymen(), tock=genfun.tock, **genfun.opts)
    #assert inspect.isgenerator(gen)
    """End Test"""


def test_doer():
    """
    Test Doer base class
    """
    tock = 1.0
    doer = doing.Doer()
    assert doer.tock == 0.0
    assert doer.tymth == None

    tymist = tyming.Tymist()
    doer = doing.Doer(tymth=tymist.tymen(), tock=tock)
    assert doer.tock == tock == 1.0
    doer.tock = 0.0
    assert doer.tock ==  0.0

    # create generator use send and explicit close
    args = {}
    dog = doer(tymth=doer.tymth, tock=doer.tock, **args)
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
    dog = doer(tymth=doer.tymth, tock=doer.tock)
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
    dog = doer(tymth=doer.tymth, tock=tock)
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

    dog = doer(tymth=doer.tymth, tock=tock)
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
    redoer = doing.ReDoer()
    assert redoer.tock == 0.0

    tymist = tyming.Tymist()
    redoer = doing.ReDoer(tymth=tymist.tymen(), tock=tock)
    assert redoer.tock == tock == 1.0
    redoer.tock = 0.0
    assert redoer.tock ==  0.0

    # create generator use send and run until normal exit. emulates Doist.ready
    args = {}
    dog = redoer(tymth=redoer.tymth, tock=redoer.tock, **args)
    assert inspect.isgenerator(dog)

    result = dog.send(None)
    assert result == redoer.tock == 0.0

    tymist.tick()
    result = dog.send(tymist.tyme)
    assert result == redoer.tock == 0.0

    tymist.tick()
    result = dog.send(tymist.tyme)
    assert result == redoer.tock == 0.0

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
    dog = redoer(tymth=redoer.tymth, tock=redoer.tock, **args)
    assert inspect.isgenerator(dog)

    result = dog.send(None)
    assert result == redoer.tock == 0.0

    tymist.tick()
    result = dog.send(tymist.tyme)
    assert result == redoer.tock == 0.0

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
    dog = redoer(tymth=redoer.tymth, tock=redoer.tock, **args)
    assert inspect.isgenerator(dog)

    result = next(dog)
    assert result == redoer.tock == 0.0

    result = next(dog)
    assert result == redoer.tock == 0.0

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
    dodoer = doing.DoDoer()
    assert dodoer.tock == 0.0

    tymist = tyming.Tymist()
    dodoer = doing.DoDoer(tymth=tymist.tymen(), tock=tock)
    assert dodoer.tock == tock == 1.0
    dodoer.tock = 0.0
    assert dodoer.tock ==  0.0

    # create generator use send and run until normal exit. emulates Doist.ready
    args = {}
    dog = dodoer(tymth=dodoer.tymth, tock=dodoer.tock, **args)
    assert inspect.isgenerator(dog)
    assert dodoer.doers == []

    result = dog.send(None)
    assert result == dodoer.tock == 0.0
    assert dodoer.doers == []

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
    dog = dodoer(tymth=dodoer.tymth, tock=dodoer.tock, doers=doers, **args)
    assert inspect.isgenerator(dog)
    assert dodoer.doers == []

    result = dog.send(None)
    assert result == dodoer.tock == 0.0
    assert dodoer.doers == doers

    tymist.tick()
    result = dog.send(tymist.tyme)
    assert result == dodoer.tock == 0.0

    tymist.tick()
    result = dog.send(tymist.tyme)
    assert result == dodoer.tock == 0.0

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

def test_dodoer_always():
    """
    Test DoDoer class with tryDoer and always
    """
    # create some TryDoers for doers
    doer0 = TryDoer(stop=1)
    doer1 = TryDoer(stop=2)
    doer2 = TryDoer(stop=3)

    doers = [doer0, doer1, doer2]
    tock = 1.0
    dodoer = doing.DoDoer(tock=tock, doers=list(doers))
    assert dodoer.tock == tock == 1.0
    assert dodoer.doers == doers
    for doer in dodoer.doers:
        assert doer.done == None
    assert dodoer.always == False

    limit = 5.0
    doist = doing.Doist(tock=tock, limit=limit, doers=[dodoer])
    assert doist.tock == tock ==  1.0
    assert doist.limit == limit == 5.0
    assert doist.doers == [dodoer]
    assert dodoer.done == None
    assert dodoer.always == False
    assert not dodoer.deeds

    # limit = 5 is long enough that all TryDoers complete
    doist.do()
    assert doist.tyme == 4.0
    assert dodoer.done
    assert dodoer.tyme == doist.tyme
    assert dodoer.always == False
    for doer in dodoer.doers:
        assert doer.done
        assert doer.tyme == dodoer.tyme == doist.tyme
    assert not dodoer.deeds

    # redo but with limit == so not all complete
    doist.do(limit=2)
    assert doist.tyme == 6.0
    assert not dodoer.done
    assert dodoer.always == False
    assert doer0.done
    assert not doer1.done
    assert not doer2.done
    assert not dodoer.deeds

    # redo but with ddoer.always == True but limit enough to complete
    dodoer.always = True
    assert dodoer.always == True
    doist.do(limit=5)
    assert doist.tyme == 11.0
    assert not dodoer.done  # dodoer not done
    assert dodoer.always == True
    for doer in dodoer.doers:   #  but all its doers are done
        assert doer.done
    assert not dodoer.deeds

    # redo but with ddoer.always == True but limit not enought to complete
    assert dodoer.always == True
    doist.do(limit=2)
    assert doist.tyme == 13.0
    assert not dodoer.done  # dodoer not done
    assert dodoer.always == True
    assert doer0.done
    assert not doer1.done
    assert not doer2.done
    assert not dodoer.deeds

    # redo but with ddoer.always == True but manual run doist so does not
    # force complete doers
    assert dodoer.always == True
    assert doist.tyme == 13.0
    deeds = doist.ready(doers=[dodoer])
    doist.once(deeds)
    doist.once(deeds)
    assert doist.tyme == 15.0
    assert not dodoer.done  # dodoer not done
    assert dodoer.always == True
    assert doer0.done
    assert not doer1.done
    assert not doer2.done
    assert len(dodoer.deeds) == 2  # deeds still there

    # now extend deeds
    doer3 = TryDoer(stop=1)
    doer4 = TryDoer(stop=2)
    moredoers =  [doer3, doer4]
    dodoer.extend(doers=list(moredoers))
    assert dodoer.doers == doers + moredoers
    assert len(dodoer.deeds) == 4
    indices = [index for dog, retyme, index in dodoer.deeds]
    assert indices == [1, 2, 3, 4]
    doist.once(deeds)
    doist.once(deeds)
    assert doist.tyme == 17.0
    assert not dodoer.done  # dodoer not done
    assert dodoer.always == True
    assert doer0.done
    assert doer1.done
    assert doer2.done
    assert doer3.done
    assert not doer4.done
    assert len(dodoer.deeds) == 1  # deeds still there
    doist.close(deeds)
    assert dodoer.done == False  # forced close so not done
    assert doer0.done
    assert doer1.done
    assert doer2.done
    assert doer3.done
    assert not doer4.done  # forced close so not done
    assert not deeds


    # start over with full set to test remove
    doer0 = TryDoer(stop=1)
    doer1 = TryDoer(stop=2)
    doer2 = TryDoer(stop=3)
    doer3 = TryDoer(stop=2)
    doer4 = TryDoer(stop=3)
    doers = [doer0, doer1, doer2, doer3, doer4]
    dodoer = doing.DoDoer(tock=tock, doers=list(doers), always=True)
    assert dodoer.tock == tock == 1.0
    assert dodoer.doers ==doers
    for doer in dodoer.doers:
        assert doer.done == None
    assert dodoer.always == True

    limit = 5.0
    doist = doing.Doist(tock=tock, limit=limit, doers=[dodoer])
    assert doist.tock == tock ==  1.0
    assert doist.limit == limit == 5.0
    assert doist.doers == [dodoer]

    assert dodoer.done == None
    assert dodoer.always == True
    assert not dodoer.deeds

    deeds = doist.ready(doers=[dodoer])
    assert not dodoer.done
    doist.once(deeds)
    doist.once(deeds)
    assert doist.tyme == 2.0
    assert not dodoer.done  # dodoer not done
    assert dodoer.always == True
    assert doer0.done
    assert not doer1.done
    assert not doer2.done
    assert not doer3.done
    assert not doer4.done
    assert len(dodoer.deeds) == 4  # deeds still there
    dodoer.remove(doers=[doer0, doer1, doer3])
    assert dodoer.doers == [doer2, doer4]
    assert len(dodoer.deeds) == 2


    """End Test """


def test_exDo():
    """
    Test exDo generator function non-class based
    """
    doizeExDo = doing.doizeExDo
    assert inspect.isgeneratorfunction(doizeExDo)
    assert hasattr(doizeExDo, "tock")
    assert hasattr(doizeExDo, "opts")
    assert "states" in  doizeExDo.opts
    assert doizeExDo.opts["states"] == None
    doizeExDo.opts["states"] = []

    tymist = tyming.Tymist()

    dog = doizeExDo(tymth=tymist.tymen(), tock=doizeExDo.tock, **doizeExDo.opts)
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
    assert doizeExDo.opts["states"] == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                                   State(tyme=0.0, context='recur', feed='Hello', count=1),
                                   State(tyme=0.0, context='recur', feed='Hi', count=2),
                                   State(tyme=0.0, context='close', feed=None, count=3),
                                   State(tyme=0.0, context='exit', feed=None, count=4)]

    doizeExDo.opts["states"] = []
    dog = doizeExDo(tymth=tymist.tymen(), tock=1.0, **doizeExDo.opts)
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
    assert doizeExDo.opts["states"] == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                                   State(tyme=0.0, context='recur', feed='Hello', count=1),
                                   State(tyme=0.0, context='recur', feed='Hi', count=2),
                                   State(tyme=0.0, context='close', feed=None, count=3),
                                   State(tyme=0.0, context='exit', feed=None, count=4)]


    doizeExDo.opts["states"] = []
    dog = doizeExDo(tymth=tymist.tymen(), tock=1.0, **doizeExDo.opts)
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
    assert doizeExDo.opts["states"] == [State(tyme=0.0, context='enter', feed=0.0, count=0),
                                   State(tyme=0.0, context='recur', feed=None, count=1),
                                   State(tyme=0.0, context='recur', feed=None, count=2),
                                   State(tyme=0.0, context='close', feed=None, count=3),
                                   State(tyme=0.0, context='exit', feed=None, count=4)]

    """End Test """


def test_trydoer_break():
    """
    Test TryDoer testing class with break to normal exit
    """
    tymist = tyming.Tymist(tock=0.125)
    doer = TryDoer(tymth=tymist.tymen(), tock=0.25)
    assert doer.tock == 0.25
    assert doer.states ==  []
    assert tymist.tyme == 0.0

    do = doer(tymth=doer.tymth, tock=doer.tock)
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
    Test TryDoer testing class with close to force exit
    """
    tymist = tyming.Tymist(tock=0.125)
    doer = TryDoer(tymth=tymist.tymen(), tock=0.25)
    assert doer.tock == 0.25
    assert doer.states ==  []
    assert tymist.tyme == 0.0

    do = doer(tymth=doer.tymth, tock=doer.tock)
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
    Test TryDoer testing class with throw to force exit
    """
    tymist = tyming.Tymist(tock=0.125)
    doer = TryDoer(tymth=tymist.tymen(), tock=0.25)
    assert doer.tock == 0.25
    assert doer.states ==  []
    assert tymist.tyme == 0.0

    do = doer(tymth=doer.tymth, tock=doer.tock)
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
    Test trydo testing function example with break to normal exit
    """
    assert inspect.isgeneratorfunction(tryDo)
    assert hasattr(tryDo, "tock")
    assert hasattr(tryDo, "opts")

    tymist = tyming.Tymist(tock=0.125)
    assert tymist.tyme == 0.0
    states = []

    do = tryDo(tymth=tymist.tymen(), states=states, tock=0.25)
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
    Test trydo testing function example with close to force exit
    """
    tymist = tyming.Tymist(tock=0.125)
    assert tymist.tyme == 0.0
    states = []

    do = tryDo(tymth=tymist.tymen(), states=states, tock=0.25)
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
    Test trydo testing function example with throw to force exit
    """
    tymist = tyming.Tymist(tock=0.125)
    assert tymist.tyme == 0.0
    states = []

    do = tryDo(tymth=tymist.tymen(), states=states, tock=0.25)
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
    # client needs tymth in order to init its .tymer
    client = clienting.Client(tymth=doist.tymen(), host="localhost", port=port)
    assert client.tyme == doist.tyme

    serdoer = doing.ServerDoer(tymth=doist.tymen(), server=server)
    assert serdoer.server ==  server
    assert serdoer.tyme ==  serdoer.server.tyme == doist.tyme
    clidoer = doing.ClientDoer(tymth=doist.tymen(), client=client)
    assert clidoer.client == client
    assert clidoer.tyme == clidoer.client.tyme == doist.tyme

    assert serdoer.tock == 0.0  # ASAP
    assert clidoer.tock == 0.0  # ASAP

    doers = [serdoer, clidoer]

    msgTx = b"Hello me maties!"
    clidoer.client.tx(msgTx)

    doist.do(doers=doers)
    assert doist.tyme == limit
    assert server.opened == False
    assert client.opened == False

    assert not client.txbs
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
    client = clienting.Client(tymth=doist.tymen(), host="localhost", port=port)

    serdoer = doing.EchoServerDoer(tymth=doist.tymen(), server=server)
    assert serdoer.server == server
    assert serdoer.tyme ==  serdoer.server.tyme == doist.tyme
    clidoer = doing.ClientDoer(tymth=doist.tymen(), client=client)
    assert clidoer.client == client
    assert clidoer.tyme == clidoer.client.tyme == doist.tyme

    assert serdoer.tock == 0.0  # ASAP
    assert clidoer.tock == 0.0  # ASAP

    doers = [serdoer, clidoer]

    msgTx = b"Hello me maties!"
    clidoer.client.tx(msgTx)

    doist.do(doers=doers)
    assert doist.tyme == limit
    assert server.opened == False
    assert client.opened == False

    assert not client.txbs
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
    test_echo_server_client()
