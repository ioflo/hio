# -*- encoding: utf-8 -*-
"""
tests.core.test_doing module

"""
import pytest

import os
import inspect

from hio.base import tyming
from hio.base import doing
from hio.base.basing import State
from hio.base.doing import TryDoer, tryDo
from hio.core.tcp import serving, clienting
from hio.core.serial import serialing


def test_deed():
    """
    Test Deed named tuple
    """
    deed = doing.Deed(dog="dog", retyme=2.0, doer=None)
    assert deed.dog == "dog"
    assert deed.retyme == 2.0
    assert deed.doer == None


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


def test_doize_dodoer_with_bound_method():
    """
    Test decorator @doize with bound method returning generator
    """
    # run until complete normal exit so done==True
    class A():
        def __init__(self):
            self.x = 1

        @doing.doize(tock=0.25)
        def myDo(self, tymth=None, tock=0.0, **opts):
            while self.x <= 3:
                tyme = yield(tock)
                self.x += 1

            return True

    a = A()
    assert a.x == 1

    assert inspect.ismethod(a.myDo)
    assert inspect.isgeneratorfunction(a.myDo)
    # read of bound method attribute is allowed
    assert a.myDo.__func__.tock == a.myDo.tock == 0.25
    assert a.myDo.__func__.done == a.myDo.done == None
    assert a.myDo.__func__.opts == a.myDo.opts == dict()

    with pytest.raises(AttributeError):
        a.myDo.tock = 0.2  # can't write to bound method attribute

    a.myDo.__func__.tock = 0.2  # can write to bound method.__func__ attribute
    assert a.myDo.tock == 0.2

    doist = doing.Doist(limit=1.0)

    myGen = a.myDo(tymth=doist.tymen(), tock=a.myDo.tock, **a.myDo.opts)
    assert inspect.isgenerator(myGen)

    doist.do(doers=[a.myDo])
    assert a.myDo.done
    assert a.x == 4

    a.x =  1
    assert a.x == 1
    doist.tyme = 0.0

    dodoer = doing.DoDoer(doers=[a.myDo])

    doist.do(doers=[dodoer])
    assert a.myDo.done
    assert a.x == 4

    # run forever so forced complete done == False
    class B():
        def __init__(self):
            self.x = 1

        @doing.doize(tock=0.25)
        def myDo(self, tymth=None, tock=0.0, **opts):
            while True:
                tyme = yield(tock)
                self.x += 1
            return True

    b = B()
    assert b.x == 1

    assert inspect.ismethod(b.myDo)
    assert inspect.isgeneratorfunction(b.myDo)
    # read of bound method attribute is allowed
    assert b.myDo.__func__.tock == b.myDo.tock == 0.25
    assert b.myDo.__func__.done == b.myDo.done == None
    assert b.myDo.__func__.opts == b.myDo.opts == dict()

    with pytest.raises(AttributeError):
        b.myDo.tock = 0.2  # can't write to bound method attribute

    b.myDo.__func__.tock = 0.2  # can write to bound method.__func__ attribute
    assert b.myDo.tock == 0.2

    doist = doing.Doist(limit=1.0)

    myGen = b.myDo(tymth=doist.tymen(), tock=b.myDo.tock, **b.myDo.opts)
    assert inspect.isgenerator(myGen)

    doist.do(doers=[b.myDo])
    assert b.myDo.done == False
    assert b.x == 6

    b.x =  1
    assert b.x == 1
    doist.tyme = 0.0

    dodoer = doing.DoDoer(doers=[b.myDo])

    doist.do(doers=[dodoer])
    assert b.myDo.done == False
    assert b.x == 6

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

    # create generator use send and run until normal exit. emulates Doist.enter()
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

    # create generator use send and then explicit close. emulates Doist.enter()
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

    # create generator use send and run until normal exit. emulates Doist.enter()
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

    # create generator use send and then explicit close. emulates Doist.enter()
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
    tock = 1.0
    # create some TryDoers for doers
    doer0 = TryDoer(stop=1)
    doer1 = TryDoer(stop=2)
    doer2 = TryDoer(stop=3)

    doers = [doer0, doer1, doer2]
    dodoer = doing.DoDoer(tock=tock, doers=list(doers))  # make copy
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
    doist.enter()
    doist.recur()
    doist.recur()
    assert doist.tyme == 15.0
    assert not dodoer.done  # dodoer not done
    assert dodoer.always == True
    assert doer0.done
    assert not doer1.done
    assert not doer2.done
    assert len(dodoer.deeds) == 2  # deeds still there

    # Test extend
    # now extend Doers
    doer3 = TryDoer(stop=1)
    doer4 = TryDoer(stop=2)
    moredoers =  [doer3, doer4]
    dodoer.extend(doers=list(moredoers))
    assert dodoer.doers == doers + moredoers
    assert len(dodoer.deeds) == 4
    doers = [doer for dog, retyme, doer in dodoer.deeds]
    assert doers == [doer1, doer2, doer3, doer4]
    doist.recur()
    doist.recur()
    assert doist.tyme == 17.0
    assert not dodoer.done  # dodoer not done
    assert dodoer.always == True
    assert doer0.done
    assert doer1.done
    assert doer2.done
    assert doer3.done
    assert not doer4.done
    assert len(dodoer.deeds) == 1  # deeds still there
    doist.exit()
    assert dodoer.done == False  # forced close so not done
    assert doer0.done
    assert doer1.done
    assert doer2.done
    assert doer3.done
    assert not doer4.done  # forced close so not done
    assert not doist.deeds
    """End Test """


def test_dodoer_remove():
    """
    Test .remove method of DoDoer
    """
    tock = 1.0
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
    assert doist.tyme == 0.0
    assert doist.tock == tock ==  1.0
    assert doist.limit == limit == 5.0
    assert doist.doers == [dodoer]

    assert dodoer.done == None
    assert dodoer.always == True
    assert not dodoer.deeds

    doist.enter()
    assert not dodoer.done
    doist.recur()
    doist.recur()
    assert doist.tyme == 2.0
    assert not dodoer.done  # dodoer not done
    assert dodoer.always == True
    assert doer0.done
    assert not doer1.done
    assert not doer2.done
    assert not doer3.done
    assert not doer4.done
    assert len(dodoer.deeds) == 4  # other deeds still there
    doers = [doer for dog, retyme, doer in dodoer.deeds]
    assert doers == [doer1, doer2, doer3, doer4]  # doer0 is removed
    for dog, retyme, doer in dodoer.deeds:
        assert not doer.done

    dodoer.remove(doers=[doer0, doer1, doer3])
    assert dodoer.doers == [doer2, doer4]
    assert len(dodoer.deeds) == 2
    doers = [doer for dog, retyme, doer in dodoer.deeds]
    assert doers == [doer2, doer4]  # others are removed
    for dog, retyme, doer in dodoer.deeds:
        assert not doer.done
    assert not doer1.done  # forced exit
    assert not doer3.done  # forced exit

    doist.recur()
    doist.recur()
    assert doist.tyme == 4.0
    assert doist.done == None  # never called .do
    assert dodoer.done == True  # all its doers completed
    assert len(dodoer.deeds) == 0  # all done
    assert len(dodoer.doers) == 2  # not removed but completed
    for doer in dodoer.doers:
        assert doer.done
    assert doer0.done  # already clean done before remove
    assert not doer1.done  # forced exit upon remove before done
    assert doer2.done  # clean done
    assert not doer3.done  # forced exit upon remove before done
    assert doer4.done  # clean done
    doist.recur()
    doist.recur()  # does not complete because dodoer not done its always == True
    """Done Test"""


def test_dodoer_remove_by_own_doer():
    """
    Test .remove method of DoDoer called by a doer of DoDoer
    """
    tock = 1.0

    # create DoDoer subclass with doized method to remove other doers
    class RemoveDoDoer(doing.DoDoer):
        """
        Subclass with doized method to remove other doers
        """
        def __init__(self, doers=None, **kwa):
            """
            Add removeDo to doers

            Inherited Parameters:
                tymist is  Tymist instance
                tock is float seconds initial value of .tock
                doers is list of doers (do generator instancs or functions)

            """
            doers = doers if doers is not None else []  # default
            doers.extend([self.removeDo])  # add .removeDo
            super(RemoveDoDoer, self).__init__(doers=doers, **kwa)


        @doing.doize()
        def removeDo(self, tymth=None, tock=0.0, **opts):
            """
             Returns Doist compatibile generator method (doer dog) to process
                to remove all doers but itself

            Parameters:
                tymth is injected function wrapper closure returned by .tymen() of
                    Tymist instance (e.e. Doist/DoDoer). Calling tymth() returns
                    associated Tymist .tyme.
                tock is injected initial tock value from doer.tock
                opts is dict of injected optional additional parameters from doer.opts

            Injected attributes by doize decorator as parameters to this method:
                gf.tock = tock  # default tock attribute for doer
                gf.opts = {}  # default opts for doer

            Usage:
                add to doers list
            """
            rdoers = []
            yield  # enter context also makes generator method
            # recur context
            for doer in self.doers:
                # doize decorated method satisfies '==' but not 'is'
                if doer != self.removeDo:  # must be != vs. is not
                    rdoers.append(doer)
            self.remove(rdoers)
            yield  # extra yield for testing so does a couple of passes after removed
            yield  # extra yield for testing so does a couple of passes after removed
            return True  # once removed then return to remove itself as doer

    # start over with full set to test remove where the remove is called by
    # a doer in the DoDoer.doers
    doer0 = TryDoer(stop=1)
    doer1 = TryDoer(stop=2)
    doer2 = TryDoer(stop=3)
    doer3 = TryDoer(stop=2)
    doer4 = TryDoer(stop=3)
    doers = [doer0, doer1, doer2, doer3, doer4]
    dodoer = RemoveDoDoer(tock=tock, doers=list(doers))
    assert dodoer.tock == tock == 1.0
    assert dodoer.removeDo in  dodoer.doers
    assert len(dodoer.doers) == len(doers) + 1 == 6
    for doer in dodoer.doers:
        assert doer.done == None
    assert dodoer.always == False

    limit = 5.0
    doist = doing.Doist(tock=tock, limit=limit, doers=[dodoer])
    assert doist.tyme == 0.0
    assert doist.tock == tock ==  1.0
    assert doist.limit == limit == 5.0
    assert doist.doers == [dodoer]

    assert dodoer.done == None
    assert dodoer.always == False
    assert not dodoer.deeds

    doist.enter()
    assert not dodoer.done
    doist.recur()  # should run dodoer.removeDo and remove all but itself
    assert doist.tyme == 1.0
    assert doist.deeds
    assert not dodoer.done  # dodoer not done
    assert dodoer.deeds
    assert len(dodoer.doers) == 1
    assert dodoer.removeDo in dodoer.doers
    # force exited so not done
    assert not doer0.done
    assert not doer1.done
    assert not doer2.done
    assert not doer3.done
    assert not doer4.done
    doist.recur()
    assert doist.tyme == 2.0
    assert doist.deeds
    assert not dodoer.done  # dodoer not done
    assert dodoer.deeds
    assert len(dodoer.doers) == 1
    assert dodoer.removeDo in dodoer.doers
    doist.recur()
    assert doist.tyme == 3.0
    assert not doist.deeds
    assert dodoer.done  # dodoer done completed successfully
    assert not dodoer.deeds
    assert len(dodoer.doers) == 1
    assert dodoer.removeDo in dodoer.doers
    assert dodoer.removeDo.done

    """Done Test"""


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




if __name__ == "__main__":
    test_dodoer_remove()
