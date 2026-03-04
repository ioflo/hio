# -*- encoding: utf-8 -*-
"""
tests to explore asyncio concepts


"""
import asyncio
import types
import inspect
import time
from datetime import datetime

import pytest

def test_asyncio_basic():
    """Test asyncio coroutine and generator concepts
    Test running async def from regular generator using .send instead of await
    """

    async def acf0():  # basic async coroutine
        print(f"    acf0 run")
        return True

    assert inspect.iscoroutinefunction(acf0)
    aco0 = acf0()  # create async corouting object from function
    assert inspect.iscoroutine(aco0)
    assert isinstance(aco0, types.CoroutineType)
    assert inspect.isawaitable(aco0)

    async def acf1():  # nested async coroutines
        print(f"----------\n    acf1 start")
        print(f"    acf1 await on acf0")
        result = await acf0()
        print(f"    acf1 finish with {result=}")

    assert inspect.iscoroutinefunction(acf1)
    aco1 = acf1()  # create async corouting object from function
    assert inspect.iscoroutine(aco1)
    assert isinstance(aco1, types.CoroutineType)
    assert inspect.isawaitable(aco1)

    async def agf0():  # async generator function
        print(f"    agf0 start")  # async coroutine object
        got = (yield 1)
        print(f"    agf0 resume {got=}")
        got = (yield 2)
        print(f"    agf0 resume again {got=}")
        got = (yield 3)
        print(f"    agf0 finish {got=}")
        return  # only empty return allowed for async generator

    assert inspect.isasyncgenfunction(agf0)
    ago0 = agf0()  # create async generator object from async generator function
    assert inspect.isasyncgen(ago0)
    assert isinstance(ago0, types.AsyncGeneratorType)
    assert not inspect.isawaitable(ago0)

    async def acf2():  # async coroutine to run async generator
        print("----------\n    acf2 start")  # async coroutine object
        async for result in agf0():
            print(f"    acf2 iterating agf0 {result=}")

    assert inspect.iscoroutinefunction(acf2)
    aco2 = acf2()  # create async corouting object from function
    assert inspect.iscoroutine(aco2)
    assert isinstance(aco2, types.CoroutineType)
    assert inspect.isawaitable(aco2)


    def gf0(): # regular generator
        print(f"----------\n    gf0 start")
        got = (yield 0)
        print(f"    gf0 resume {got=}")
        got = (yield 1)
        print(f"    gf0 resume again {got=}")
        return 2  # regular generator may return non-empty

    assert inspect.isgeneratorfunction(gf0)
    go0 = gf0()  # make generator
    assert inspect.isgenerator(go0)
    assert isinstance(go0, types.GeneratorType)


    def gf1(): # regular generator that sends to async coroutine
        print(f"----------\n    gf1 start")
        got = (yield 0)
        print(f"    gf1 resume {got=}")
        print(f"    gf1 now .send(None) to aco1 from acf1 to emulate await")
        aco1 = acf1()  # create async corouting object from function
        try:
            aco1.send(None)
        except StopIteration:
            print(f"    gf1 successfully iterated acf1")
        got = (yield 1)
        print(f"   gf1 finish {got=}\n----------\n")
        return 2  # regular generator may return non-empty

    assert inspect.isgeneratorfunction(gf1)
    go1 = gf1()  # make generator
    assert inspect.isgenerator(go1)
    assert isinstance(go1, types.GeneratorType)


    def gf2(): # regular generator that sends to async coroutine running async gen
        print(f"----------\n    gf2 start")
        got = (yield 0)
        print(f"    gf2 resume {got=}")
        print(f"    gf2 now .send(None) to aco2 from acf2 to emulate await")
        aco2 = acf2()  # create async corouting object from function
        try:
            aco2.send(None)
        except StopIteration:
            print(f"    gf2 successfully iterated acf1")
        got = (yield 1)
        print(f"   gf2 finish {got=}\n----------\n")
        return 2  # regular generator may return non-empty

    assert inspect.isgeneratorfunction(gf2)
    go2 = gf2()  # make generator
    assert inspect.isgenerator(go2)
    assert isinstance(go2, types.GeneratorType)



    # using send to execute basic coroutine object
    try:
        # no result returned since raises exception
        result = aco0.send(None)  # empty send(None)  replaces await like next()
    except StopIteration as ex:
        print(f"aco0 send raises {ex=}")

    try:
        # no result returned since raises exception
        result = aco0.send(None)  # send(None)  replaces await like next()
    except RuntimeError as ex:  # can't reuse already awaited coroutine
        print(f"aco0 send again raises {ex=}")

    assert aco0.close() is None  # close is idempotent

    # start over
    aco0 = acf0()  # create async corouting object from function
    assert inspect.iscoroutine(aco0)

    # now close it
    assert aco0.close() is None  # close is idempotnet

    try:
        # no result returned since raises exception
        result = aco0.send(None)  # send(None)  replaces await like next()
    except RuntimeError as ex:  # already closed so same as reuse
        print(f"aco0 send after close raises {ex=}")

    # start over
    aco0 = acf0()  # create async corouting object from function
    assert inspect.iscoroutine(aco0)

    try:
        # no result returned since raises exception
        result = aco0.send(None)  # send(None)  replaces await like next()
    except StopIteration as ex:
        print(f"aco0 send raises {ex=}")

    # now close it
    assert aco0.close() is None  # close is idempotent

    try:
        # no result returned since raises exception
        result = aco0.send(None)  # send(None)  replaces await like next()
    except RuntimeError as ex:  # already closed so same as reuse
        print(f"aco0 send after close raises {ex=}")


    # using send to execute coroutine object with nested await
    try:
        # no result returned since raises exception
        result = aco1.send(None)  # send(None)  replaces await like next()
    except StopIteration as ex:
        print(f"aco1 send raises {ex=}")

    try:
        # no result returned since raises exception
        result = aco1.send(None)  # end(None)  replaces await like next()
    except RuntimeError as ex:  # can't reuse already awaited coroutine
        print(f"aco1 send again raises {ex=}")


    # now regenerate ac01 to run nested await
    # nested await runs fine when only regenerate top level async coroutine object
    aco1 = acf1()  # create async corouting object from function
    assert inspect.iscoroutine(aco1)

    try:
        # no result returned since raises exception
        result = aco1.send(None)  # empty send(None) replaces await like next()
    except StopIteration as ex:
        print(f"aco1 send raises {ex=}")

    try:
        # no result returned since raises exception
        result = aco1.send(None)  # empty send(None)  replaces await like next()
    except RuntimeError as ex:  # can't reuse already awaited coroutine
        print(f"aco1 send again raises {ex=}")


    # test regular generator
    result = go0.send(None)  # send None same as next()
    print(f"go0 zeroth send {result=}")
    result = go0.send("A")
    print(f"go0 send 'A' {result=}")
    try:
        result = go0.send("B")
    except StopIteration as ex:
        print(f"go0 send raises {ex=}")
        print(f"go0 send 'B' result={ex.value} from excepton.value")

    try:
        result = go0.send("C")
    except StopIteration as ex:
        print(f"go0 send 'C' raises {ex=}")
        print(f"go0 send 'C' result={ex.value} from excepton.value")

    go0.close()  # close and see what happens

    try:
        result = go0.send("C")
    except StopIteration as ex:
        print(f"go0 send 'C' after close raises {ex=}")
        print(f"go0 send 'C' after close result={ex.value} from excepton.value")


    # do over with next
    go0 = gf0()
    assert inspect.isgenerator(go0)

    result = next(go0)  # next instead of send(None)
    print(f"go0 next {result=}")
    result = go0.send("A")
    print(f"go0 send 'A' {result=}")
    try:
        result = go0.send("B")
    except StopIteration as ex:
        print(f"go0 send raises {ex=}")
        print(f"go0 send 'B' result={ex.value} from excepton.value")


    # use regular generator to run async coroutine using send
    """
    ----------
        acf1 start
        acf1 await on acf0
    acf0 run
        acf1 finish
        gf1 successfully iterated acf1
    go1 send 'A' result=1
        gf1 resume again got='B'
    go1 send raises ex=StopIteration(2)
    go1 send 'B' result=2 from excepton.value
    """
    result = go1.send(None)  # send None same as next()
    print(f"go1 zeroth send {result=}")
    result = go1.send("A")
    print(f"go1 send 'A' {result=}")
    try:
        result = go1.send("B")
    except StopIteration as ex:
        print(f"go1 send raises {ex=}")
        print(f"go1 send 'B' result={ex.value} from excepton.value")

    # redo
    go1 = gf1()  # make generator
    assert inspect.isgenerator(go1)

    result = go1.send(None)  # send None same as next()
    print(f"go1 zeroth send {result=}")
    result = go1.send("A")
    print(f"go1 send 'A' {result=}")
    try:
        result = go1.send("B")
    except StopIteration as ex:
        print(f"go1 send raises {ex=}")
        print(f"go1 send 'B' result={ex.value} from excepton.value")

    # using send to execute async generator objects
    # async generators have .asend and .athrow methods but not .send, .throw, or .close
    # using .asend results in runtime warning
    # result = ago0.asend(None)  # first advance must be send(None) like next()
    """
    coro1 zeroth asend result=<async_generator_asend object at 0x10b42fac0>
    /Users/Load/Data/Code/public/hio/tests/base/test_asyncio.py:236:
    RuntimeWarning: coroutine method 'asend' of 'test_basic_asyncio.<locals>.agf0' was never awaited

    This code snippet did not work to turn warning into catchable exception

    with warnings.catch_warnings(record=True) as w:
        warnings.filterwarnings("error")

        try:
            result = ago0.asend(None)  # first advance must be send(None) like next()
        except Exception as ex:
            print(f"-------\n  ago0 asend warning={ex}")
    """

    # try using async generator inside async coroutine
    try:
        # no result returned since raises exception
        result = aco2.send(None)  # send(None)  replaces await like next()
    except StopIteration as ex:
        print(f"aco2 send raises {ex=}")

    try:
        # no result returned since raises exception
        result = aco2.send(None)  # end(None)  replaces await like next()
    except RuntimeError as ex:  # can't reuse already awaited coroutine
        print(f"aco2 send again raises {ex=}")

    # test restarts
    aco2 = acf2()  # create async corouting object from function
    assert inspect.iscoroutine(aco2)

    try:
        # no result returned since raises exception
        result = aco2.send(None)  # send(None)  replaces await like next()
    except StopIteration as ex:
        print(f"aco2 send raises {ex=}")

    try:
        # no result returned since raises exception
        result = aco2.send(None)  # end(None)  replaces await like next()
    except RuntimeError as ex:  # can't reuse already awaited coroutine
        print(f"aco2 send again raises {ex=}")

    # test regular generator that runs async coroutine that runs async generator
    result = go2.send(None)  # send None same as next()
    print(f"go2 zeroth send {result=}")
    result = go2.send("A")
    print(f"go2 send 'A' {result=}")
    try:
        result = go2.send("B")
    except StopIteration as ex:
        print(f"go2 send raises {ex=}")
        print(f"go2 send 'B' result={ex.value} from excepton.value")

    # redo
    go2 = gf2()  # make generator
    assert inspect.isgenerator(go2)

    result = go2.send(None)  # send None same as next()
    print(f"go2 zeroth send {result=}")
    result = go2.send("A")
    print(f"go2 send 'A' {result=}")
    try:
        result = go2.send("B")
    except StopIteration as ex:
        print(f"go2 send raises {ex=}")
        print(f"go2 send 'B' result={ex.value} from excepton.value")

    """Done Test"""

def test_asyncio_await_method():
    """Test classes that define .__await__ method and how that works
    """
    class Waitless():
        """Await method does not have yield"""

        def __await__(self):
            print(f"------------\n  Waitless instance without yield in __await__\n----------")
            return True


    waitless = Waitless()

    assert inspect.isawaitable(waitless)
    assert not inspect.iscoroutine(waitless)

    result = waitless.__await__()
    assert result == True

    async def wot():
        print(f"----------\n    wot start")
        print(f"    wot await on waitless")
        result = await Waitless()
        print(f"    wot finish with {result=}")

    assert inspect.iscoroutinefunction(wot)
    woto = wot()  # create async corouting object from function
    assert inspect.iscoroutine(woto)
    assert inspect.isawaitable(woto)

    try:
        result = woto.send(None)  # send(None) replaces await
    except TypeError as ex:
        print(f"  woto send raises {ex=}")
        #"__await__() returned non-iterator of type 'bool'"


    class Waitful():
        """Await method does have yield"""

        def __await__(self):
            print(f"------------\n  Waitless instance with yield in __await__\n----------")
            got = (yield False)
            print(f"  waitful yield {got=}")
            return True


    waitful = Waitful()

    assert inspect.isawaitable(waitful)
    assert not inspect.iscoroutine(waitful)

    gen = waitful.__await__()
    assert inspect.isgenerator(gen)

    async def wit():
        print(f"----------\n    wit start")
        print(f"    wit await on waitful")
        result = await Waitful()
        print(f"    wit finish with {result=}")

    assert inspect.iscoroutinefunction(wit)
    wito = wit()  # create async corouting object from function
    assert inspect.iscoroutine(wito)
    assert inspect.isawaitable(wito)

    result = wito.send(None)  # send(None) replaces await
    assert result == False
    try:
        result = wito.send("A")
    except StopIteration as ex:
        print(f"  wito send raises {ex=}")
        print(f"  wito ex.value={ex.value}")


    """Done Test"""


def test_asyncio_run():
    """Test running async def from regular generator using .send instead of await
    but instead asyncio loop with async.sleep()
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError as ex:
        pass


    async def bot():  # basic async coroutine
        print(f"      bot start")
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError as ex:
            pass
        else:
            print(f"      bot sleep")
            await asyncio.sleep(0.1)

        print(f"      bot run more")

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError as ex:
            pass
        else:
            print(f"      bot sleep")
            await asyncio.sleep(0.1)

        print(f"      bot finish")

    assert inspect.iscoroutinefunction(bot)
    try:
        boto = bot()  # create async corouting object from function
        assert inspect.iscoroutine(boto)
        assert inspect.isawaitable(boto)
        boto.send(None)
    except StopIteration as ex:
        pass

    async def top():  # top coroutine with nested sub coroutine
        print(f"----------\n    top start")
        print(f"    top await on bot")
        await bot()
        print(f"    top finish")

    assert inspect.iscoroutinefunction(top)
    try:
        topo = top()  # create async corouting object from function
        assert inspect.iscoroutine(topo)
        assert inspect.isawaitable(topo)
        topo.send(None)
    except StopIteration as ex:
        pass


    def doer(): # regular generator that wraps async coroutine
        print(f"----------\n  doer start")
        got = (yield 0)
        print(f"  doer run top")
        topo = top()  # create async corouting object from function
        try:
            topo.send(None)
        except StopIteration:
            print(f" doer ran top")
        got = (yield 1)
        print(f" doer finish")
        return True

    assert inspect.isgeneratorfunction(doer)
    dog = doer()  # make generator
    assert inspect.isgenerator(dog)


    def doit(): # scheduler of doer
        print(f"----------\ndoit start")
        print(f"doit run doer")
        dog = doer()  # create
        done = False
        count = 0
        try:
            print(f"doit starting dog")
            dog.send(None)
        except StopIteration:
            print(f"doit finished dog at {count=}")
            done = True

        while not done:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError as ex:
                pass
            else:
                print(f"doit sleep")
                loop.create_task(asyncio.sleep(0.1))
            count += 1
            try:
                print(f"doit recur dog")
                dog.send(count)
            except StopIteration:
                print(f"doit finished dog at {count=}")
                done = True
        print(f"doit finish\n---------")

    async def arun():
        doit()

    assert inspect.iscoroutinefunction(arun)
    try:
        aruno = arun()
        assert inspect.iscoroutine(aruno)
        assert inspect.isawaitable(aruno)
        aruno.send(None)
    except StopIteration as ex:
        pass

    asyncio.run(arun())


    """Does not work
    loop = asyncio.new_event_loop()
    loop.run_forever()
    doit()
    loop.stop()
    loop.close()
    """

    """This test raises the following RuntimeWarnings when the explicit calls
    to the async def functions to create async def objects are executed but
    not sent
    boto = bot() but not followed by boto.send(None)
    topo = top() but not followed by topo.send(None)
    aruno = arun()  but not followed by aruno.send(None)

    <sys>:0: RuntimeWarning: coroutine 'test_asyncio_run.<locals>.bot' was never awaited
    RuntimeWarning: Enable tracemalloc to get the object allocation traceback
    <sys>:0: RuntimeWarning: coroutine 'test_asyncio_run.<locals>.top' was never awaited
    RuntimeWarning: Enable tracemalloc to get the object allocation traceback
    <sys>:0: RuntimeWarning: coroutine 'test_asyncio_run.<locals>.arun' was never awaited
    RuntimeWarning: Enable tracemalloc to get the object allocation traceback

    """

    """Done Test"""



def test_asyncio_doist():
    """Test running async def from regular generator using .send instead of await
    but instead asyncio loop with async.sleep()
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError as ex:
        pass


    async def bot():  # basic async coroutine
        print(f"      bot start at {datetime.now().time().isoformat('milliseconds')}")
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError as ex:
            pass
        else:
            print(f"      bot sleep at {datetime.now().time().isoformat('milliseconds')}")
            await asyncio.sleep(0.1)

        print(f"      bot run more at {datetime.now().time().isoformat('milliseconds')}")

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError as ex:
            pass
        else:
            print(f"      bot sleep at {datetime.now().time().isoformat('milliseconds')}")
            await asyncio.sleep(0.1)

        print(f"      bot finish at {datetime.now().time().isoformat('milliseconds')}")

    assert inspect.iscoroutinefunction(bot)
    try:
        boto = bot()  # create async corouting object from function
        assert inspect.iscoroutine(boto)
        assert inspect.isawaitable(boto)
        boto.send(None)
    except StopIteration as ex:
        pass

    async def top():  # top coroutine with nested sub coroutine
        print(f"----------\n    top start")
        print(f"    top await on bot")
        await bot()
        print(f"    top finish")

    assert inspect.iscoroutinefunction(top)
    try:
        topo = top()  # create async corouting object from function
        assert inspect.iscoroutine(topo)
        assert inspect.isawaitable(topo)
        topo.send(None)
    except StopIteration as ex:
        pass


    def doer(): # regular generator that wraps async coroutine
        print(f"----------\n  doer start")
        got = (yield 0)
        print(f"  doer run top")
        topo = top()  # create async corouting object from function
        try:
            topo.send(None)
        except StopIteration:
            print(f" doer ran top")
        got = (yield 1)
        print(f" doer finish")
        return True

    assert inspect.isgeneratorfunction(doer)
    dog = doer()  # make generator
    assert inspect.isgenerator(dog)


    class a_doist():
        """scheduler that is asyncio aware"""

        def __await__(self):
            yield
            self.do()
            yield


        def do(self): # scheduler of doer
            print(f"\n================\n  do start at {datetime.now().time().isoformat('milliseconds')}")
            print(f"  do enter")
            dog = doer()  # create dog
            done = False
            count = 0
            try:
                print(f"  do enter dog")
                dog.send(None)
            except StopIteration:
                print(f"  do exit dog at {count=}")
                done = True

            while not done:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError as ex:
                    print(f"  do non-asyncio sleep at {datetime.now().time().isoformat('milliseconds')}")
                    time.sleep(0.1)
                else:
                    print(f"  do asyncio sleep at {datetime.now().time().isoformat('milliseconds')}")
                    loop.create_task(asyncio.sleep(0.1))
                count += 1
                try:
                    print(f"  do recur dog")
                    dog.send(count)
                except StopIteration:
                    print(f"  do exit dog at {count=}")
                    done = True
            print(f"  do finish at {datetime.now().time().isoformat('milliseconds')}\n============")

    asyncio.run(a_doist())

    """This raises the following RuntimeWarnings when the explicit calls
    to the async def functions to create async def objects are executed  but
    not sent

    boto = bot() but not followed by boto.send(None)
    topo = top() but not followed by topo.send(None)


    <sys>:0: RuntimeWarning: coroutine 'test_asyncio_doist.<locals>.bot' was never awaited
    RuntimeWarning: Enable tracemalloc to get the object allocation traceback
    <sys>:0: RuntimeWarning: coroutine 'test_asyncio_doist.<locals>.top' was never awaited
    RuntimeWarning: Enable tracemalloc to get the object allocation traceback

    """

    async def bdo(): # scheduler of doer
        print(f"\n================\n  bdo start at {datetime.now().time().isoformat('milliseconds')}")
        print(f"  do enter")
        dog = doer()  # create dog
        done = False
        count = 0
        try:
            print(f"  bdo enter dog")
            dog.send(None)
        except StopIteration:
            print(f"  bdo exit dog at {count=}")
            done = True

        while not done:
            await asyncio.sleep(0.1)
            count += 1
            try:
                print(f"  bdo recur dog")
                dog.send(count)
            except StopIteration:
                print(f"  bdo exit dog at {count=}")
                done = True
        print(f"  bdo finish at {datetime.now().time().isoformat('milliseconds')}\n============")

    asyncio.run(bdo())



    # try with different approach

    async def foo():  # basic async coroutine
        print(f"      foo start")
        print(f"      foo sleep at {datetime.now().time().isoformat('milliseconds')}")
        await asyncio.sleep(0.1)
        print(f"      foo run more")
        print(f"      foo sleep at {datetime.now().time().isoformat('milliseconds')}")
        await asyncio.sleep(0.1)
        print(f"      foo finish at {datetime.now().time().isoformat('milliseconds')}")

    async def bar():  # top coroutine with nested sub coroutine
        print(f"----------\n    bar start")
        print(f"    bar await on foo")
        await foo()
        print(f"    bar finish")


    def adoer(): # regular generator that wraps async coroutine
        print(f"----------\n  adoer start")
        got = (yield 0)
        print(f"  adoer run bar")
        baro = bar()  # create async corouting object from function
        while True:
            try:
                baro.send(None)
            except StopIteration:
                print(f" adoer ran bar")
                break
            got = (yield 1)
        print(f" adoer finish")
        return True


    class ADoist():
        """scheduler that is asyncio aware via ado"""

        async def ado(self): # scheduler of doer
            print(f"\n================\n  ado start at {datetime.now().time().isoformat('milliseconds')}")
            print(f"  ado enter")
            dog = adoer()  # create dog
            done = False
            count = 0
            try:
                print(f"  ado enter dog")
                dog.send(None)
            except StopIteration:
                print(f"  ado exit dog at {count=}")
                done = True

            while not done:
                print(f"  ado await asyncio.sleep at {datetime.now().time().isoformat('milliseconds')}")
                await asyncio.sleep(0.1)
                count += 1
                try:
                    print(f"  ado recur dog at {datetime.now().time().isoformat('milliseconds')}")
                    dog.send(count)
                except StopIteration:
                    print(f"  ado exit dog at {count=}")
                    done = True

            print(f"  ado finish at {datetime.now().time().isoformat('milliseconds')}\n============")

    asyncio.run(ADoist().ado())


    # not work
    #class Doist():
        #"""scheduler that is asyncio sleep via helper sleep"""

        #async def asleep(self):
            #await asyncio.sleep(0.1)

        #async def ado(self):
            #self.do()

        #def do(self): # scheduler of doer
            #print(f"\n================\n  do start at {datetime.now().time().isoformat('milliseconds')}")
            #print(f"  do enter")
            #dog = adoer()  # create dog
            #done = False
            #count = 0
            #try:
                #print(f"  do enter dog")
                #dog.send(None)
            #except StopIteration:
                #print(f"  do exit dog at {count=}")
                #done = True

            #while not done:
                #print(f"  do send asleep at {datetime.now().time().isoformat('milliseconds')}")
                #self.asleep().send(None)
                #count += 1
                #try:
                    #print(f"  do recur dog at {datetime.now().time().isoformat('milliseconds')}")
                    #dog.send(count)
                #except StopIteration:
                    #print(f"  do exit dog at {count=}")
                    #done = True

            #print(f"  ado finish at {datetime.now().time().isoformat('milliseconds')}\n============")

    #asyncio.run(Doist().ado())


    #class Doist():
        #"""scheduler that is asyncio sleep via helper sleep"""

        #async def ado(self):
            #self.do()

        #def do(self): # scheduler of doer
            #print(f"\n================\n  do start at {datetime.now().time().isoformat('milliseconds')}")
            #print(f"  do enter")
            #dog = adoer()  # create dog
            #done = False
            #count = 0
            #try:
                #print(f"  do enter dog")
                #dog.send(None)
            #except StopIteration:
                #print(f"  do exit dog at {count=}")
                #done = True

            #while not done:
                #sleep = asyncio.sleep(0.1)
                #try:
                    #sleep.send(None)
                #except StopIteration as ex:
                    #pass

                #try:
                    #print(f"  do recur dog at {datetime.now().time().isoformat('milliseconds')}")
                    #dog.send(count)
                #except StopIteration:
                    #print(f"  do exit dog at {count=}")
                    #done = True

            #print(f"  ado finish at {datetime.now().time().isoformat('milliseconds')}\n============")

    #asyncio.run(Doist().ado())


    """Done Test"""



if __name__ == "__main__":
    test_asyncio_basic()
    test_asyncio_await_method()
    test_asyncio_run()
    test_asyncio_doist()
