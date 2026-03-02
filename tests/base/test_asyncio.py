# -*- encoding: utf-8 -*-
"""
tests to explore asyncio concepts


"""
import asyncio
import types
import inspect
import warnings

import pytest

def test_asyncio_basic():
    """Test asyncio coroutine and generator concepts
    Test running async def from regular generator using .send instead of await
    """

    async def acf0():  # basic async coroutine
        print(f"    acf0 run")

    assert inspect.iscoroutinefunction(acf0)
    aco0 = acf0()  # create async corouting object from function
    assert inspect.iscoroutine(aco0)
    assert isinstance(aco0, types.CoroutineType)

    async def acf1():  # nested async coroutines
        print(f"----------\n    acf1 start")
        print(f"    acf1 await on acf0")
        await acf0()
        print(f"    acf1 finish")

    assert inspect.iscoroutinefunction(acf1)
    aco1 = acf1()  # create async corouting object from function
    assert inspect.iscoroutine(aco1)
    assert isinstance(aco1, types.CoroutineType)

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

    async def acf2():  # async coroutine to run async generator
        print("----------\n    acf2 start")  # async coroutine object
        async for result in agf0():
            print(f"    acf2 iterating agf0 {result=}")

    assert inspect.iscoroutinefunction(acf2)
    aco2 = acf2()  # create async corouting object from function
    assert inspect.iscoroutine(aco2)
    assert isinstance(aco2, types.CoroutineType)


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


def test_asyncio_run():
    """Test running async def from regular generator using .send instead of await
    but instead asyncio loop with async.sleep()
    """

    """Done Test"""


if __name__ == "__main__":
    test_asyncio_basic()
    test_asyncio_run()
