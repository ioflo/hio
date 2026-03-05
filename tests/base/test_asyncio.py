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
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError as ex:
        pass


    async def acf0():  # basic async coroutine
        return True

    assert inspect.iscoroutinefunction(acf0)
    aco0 = acf0()  # create async corouting object from function
    assert inspect.iscoroutine(aco0)
    assert isinstance(aco0, types.CoroutineType)
    assert inspect.isawaitable(aco0)

    async def acf1():  # nested async coroutines
        result = await acf0()
        return result

    assert inspect.iscoroutinefunction(acf1)
    aco1 = acf1()  # create async corouting object from function
    assert inspect.iscoroutine(aco1)
    assert isinstance(aco1, types.CoroutineType)
    assert inspect.isawaitable(aco1)

    # using send to execute basic coroutine object
    try:
        # no result returned since raises exception
        result = aco0.send(None)  # empty send(None)  replaces await like next()
    except StopIteration as ex:
        assert ex.value == True # but return shows up in ex.value

    try:
        # no result returned since raises exception
        result = aco0.send(None)  # send(None)  replaces await like next()
    except RuntimeError as ex:  # can't reuse already awaited coroutine
        assert ex.args[0] == 'cannot reuse already awaited coroutine'

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
        assert ex.args[0] == 'cannot reuse already awaited coroutine'

    # start over
    aco0 = acf0()  # create async corouting object from function
    assert inspect.iscoroutine(aco0)

    try:
        # no result returned since raises exception
        result = aco0.send(None)  # send(None)  replaces await like next()
    except StopIteration as ex:
        assert ex.value == True  # but result returned in ex.value

    # now close it
    assert aco0.close() is None  # close is idempotent

    try:
        # no result returned since raises exception
        result = aco0.send(None)  # send(None)  replaces await like next()
    except RuntimeError as ex:  # already closed so same as reuse
        assert ex.args[0] == 'cannot reuse already awaited coroutine'



    def gf0(): # regular generator
        got = (yield 0)
        assert got == 'A'
        got = (yield 1)
        assert got == 'B'
        return 2  # regular generator may return non-empty

    assert inspect.isgeneratorfunction(gf0)
    go0 = gf0()  # make generator
    assert inspect.isgenerator(go0)
    assert isinstance(go0, types.GeneratorType)


    def gf1(): # regular generator that sends to async coroutine
        got = (yield 0)
        assert got == 'A'
        aco1 = acf1()  # create async corouting object from function
        try:
            result = aco1.send(None)
        except StopIteration as ex:
            assert ex.value == True
            result = ex.value
        got = (yield result)
        assert got == "B"
        return 2  # regular generator may return non-empty

    assert inspect.isgeneratorfunction(gf1)
    go1 = gf1()  # make generator
    assert inspect.isgenerator(go1)
    assert isinstance(go1, types.GeneratorType)



    # using send to execute coroutine object with nested await
    try:
        # no result returned since raises exception
        result = aco1.send(None)  # send(None)  replaces await like next()
    except StopIteration as ex:
        assert ex.value == True  # result bubbles up through awaits

    try:
        # no result returned since raises exception
        result = aco1.send(None)  # end(None)  replaces await like next()
    except RuntimeError as ex:  # can't reuse already awaited coroutine
        assert ex.args[0] == 'cannot reuse already awaited coroutine'


    # now regenerate ac01 to run nested await
    # nested await runs fine when only regenerate top level async coroutine object
    aco1 = acf1()  # create async corouting object from function
    assert inspect.iscoroutine(aco1)

    try:
        # no result returned since raises exception
        result = aco1.send(None)  # empty send(None) replaces await like next()
    except StopIteration as ex:
                assert ex.value == True  # result bubbles up through awaits

    try:
        # no result returned since raises exception
        result = aco1.send(None)  # empty send(None)  replaces await like next()
    except RuntimeError as ex:  # can't reuse already awaited coroutine
        assert ex.args[0] == 'cannot reuse already awaited coroutine'


    # test regular generator
    result = go0.send(None)  # send None same as next()
    assert result == 0
    result = go0.send("A")
    assert result == 1
    try:
        result = go0.send("B")  # no result since exception
    except StopIteration as ex:
        assert ex.value == 2  # final return as ex.value

    try:
        result = go0.send("C")
    except StopIteration as ex:
        assert ex.value is None  # previously finished so no return value

    go0.close()  # close and see what happens

    try:
        result = go0.send("C")
    except StopIteration as ex:
        assert ex.value is None  # previously finished so no return value

    # do over with next
    go0 = gf0()
    assert inspect.isgenerator(go0)

    result = next(go0)  # next instead of send(None)
    assert result == 0
    result = go0.send("A")
    assert result == 1
    try:
        result = go0.send("B")
    except StopIteration as ex:
        assert ex.value == 2  # return value shows up here


    # use regular generator to run async coroutine using send
    result = go1.send(None)  # send None same as next()
    assert result == 0
    result = go1.send("A")
    assert result == True  # bubbled up from await inside send
    try:
        result = go1.send("B")
    except StopIteration as ex:
        assert ex.value == 2  # return value

    # redo
    go1 = gf1()  # make generator
    assert inspect.isgenerator(go1)

    result = go1.send(None)  # send None same as next()
    assert result == 0
    result = go1.send("A")
    assert result == True  # bubbled up from await inside send
    try:
        result = go1.send("B")
    except StopIteration as ex:
        assert ex.value == 2  # return value

    # Async Generator
    async def agf0():  # async generator function
        got = (yield 1)
        got = (yield 2)
        got = (yield 3)
        return  # only empty return allowed for async generator

    assert inspect.isasyncgenfunction(agf0)
    ago0 = agf0()  # create async generator object from async generator function
    assert inspect.isasyncgen(ago0)
    assert isinstance(ago0, types.AsyncGeneratorType)
    assert not inspect.isawaitable(ago0)

    async def acf2():  # async coroutine to run async generator
        results = [result async for result in agf0()]
        assert results == [1, 2, 3]
        return results

    assert inspect.iscoroutinefunction(acf2)
    aco2 = acf2()  # create async corouting object from function
    assert inspect.iscoroutine(aco2)
    assert isinstance(aco2, types.CoroutineType)
    assert inspect.isawaitable(aco2)

    def gf2(): # regular generator that sends to async coroutine running async gen
        got = (yield 0)
        assert got == "A"
        aco2 = acf2()  # create async corouting object from function
        try:
            result = aco2.send(None)
        except StopIteration as ex:
            assert ex.value == [1, 2, 3]
            result = ex.value
        got = (yield result)
        assert got == "B"
        return 2  # regular generator may return non-empty

    assert inspect.isgeneratorfunction(gf2)
    go2 = gf2()  # make generator
    assert inspect.isgenerator(go2)
    assert isinstance(go2, types.GeneratorType)


    # using send to execute async generator objects
    # async generators have .asend and .athrow methods but not .send, .throw, or .close
    # using .asend results in runtime warning
    # result = ago0.asend(None)  # first advance must be send(None) like next()

    # try using async generator inside async coroutine
    try:
        # no result returned since raises exception
        result = aco2.send(None)  # send(None)  replaces await like next()
    except StopIteration as ex:
        assert ex.value == [1, 2, 3]  # return value bubbles up to in ex.value

    try:
        # no result returned since raises exception
        result = aco2.send(None)  # end(None)  replaces await like next()
    except RuntimeError as ex:  # can't reuse already awaited coroutine
        assert ex.args[0] == 'cannot reuse already awaited coroutine'

    # test restarts
    aco2 = acf2()  # create async corouting object from function
    assert inspect.iscoroutine(aco2)

    try:
        # no result returned since raises exception
        result = aco2.send(None)  # send(None)  replaces await like next()
    except StopIteration as ex:
        assert ex.value == [1, 2, 3]  # return value bubbles up to in ex.value

    try:
        # no result returned since raises exception
        result = aco2.send(None)  # end(None)  replaces await like next()
    except RuntimeError as ex:  # can't reuse already awaited coroutine
        assert ex.args[0] == 'cannot reuse already awaited coroutine'

    # test regular generator that runs async coroutine that runs async generator
    result = go2.send(None)  # send None same as next()
    assert result == 0
    result = go2.send("A")
    assert result == [1, 2, 3]  # async def return generator bubble up
    try:
        result = go2.send("B")
    except StopIteration as ex:
        assert ex.value == 2  # final return

    # redo
    go2 = gf2()  # make generator
    assert inspect.isgenerator(go2)

    result = go2.send(None)  # send None same as next()
    assert result == 0
    result = go2.send("A")
    assert result == [1, 2, 3]  # async def return generator bubble up
    try:
        result = go2.send("B")
    except StopIteration as ex:
        assert ex.value == 2  # final return

    """Done Test"""

def test_asyncio_await_method():
    """Test classes that define .__await__ method and how that works
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError as ex:
        pass

        # proves can no longer use yield from of asyncio.sleep() inside of __await__
    class AsyncOperation:
        def __init__(self, delay):
            self.delay = delay

        def __await__(self):
            yield from asyncio.sleep(self.delay)
            return f"Completed after {self.delay}s"

    async def main():
        op = AsyncOperation(1.5)
        result = await op

    with pytest.raises(TypeError):
        asyncio.run(main())


    class Waitless():
        """Await method does not have yield"""

        def __await__(self):
            return True


    waitless = Waitless()

    assert inspect.isawaitable(waitless)
    assert not inspect.iscoroutine(waitless)

    result = waitless.__await__()
    assert result == True

    async def wot():
        result = await Waitless()

    assert inspect.iscoroutinefunction(wot)
    woto = wot()  # create async corouting object from function
    assert inspect.iscoroutine(woto)
    assert inspect.isawaitable(woto)

    with pytest.raises(TypeError):
        #"__await__() returned non-iterator of type 'bool'"
        result = woto.send(None)  # send(None) replaces await


    class Waitbad():
        """Await method does have yield value raises RuntimeError"""
        def __await__(self):
            got = (yield False)
            return True

    waitbad = Waitbad()
    assert inspect.isawaitable(waitbad)
    assert not inspect.iscoroutine(waitbad)

    gen = waitbad.__await__()
    assert inspect.isgenerator(gen)

    with pytest.raises(RuntimeError):
        #RuntimeError: Task got bad yield: False
        asyncio.run(waitbad)


    class Waitful():
        """Await method does have yield empty"""
        def __init__(self):
            self.gots = []

        def __await__(self):
            got = yield
            self.gots.append(got)
            return self.gots

    waitful = Waitful()
    assert waitful.gots == []
    assert inspect.isawaitable(waitful)
    assert not inspect.iscoroutine(waitful)

    gen = waitful.__await__()
    assert inspect.isgenerator(gen)

    asyncio.run(waitful)
    assert waitful.gots == [None]

    async def wit():
        result = await Waitful()
        assert result
        return result

    assert inspect.iscoroutinefunction(wit)
    wito = wit()  # create async corouting object from function
    assert inspect.iscoroutine(wito)
    assert inspect.isawaitable(wito)

    result = wito.send(None)  # send(None) replaces await
    assert result is None

    try:
        result = wito.send("A")
    except StopIteration as ex:
        assert ex.value == ['A']

    # Conclusion __await__() acts like a generator with await acting like yield from

    asyncio.run(wit())

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
        results = []
        result = await asyncio.sleep(0.1)
        results.append(dict(result=result,
                            dt=f"bot {datetime.now().time().isoformat('milliseconds')}"))
        result = await asyncio.sleep(0.1)
        results.append(dict(result=result,
                            dt=f"bot {datetime.now().time().isoformat('milliseconds')}"))
        return results

    assert inspect.iscoroutinefunction(bot)

    boto = bot()  # create async corouting object from function
    assert inspect.iscoroutine(boto)
    assert inspect.isawaitable(boto)
    with pytest.raises(RuntimeError) as ex:
        boto.send(None)
    assert ex.value.args[0] == 'no running event loop'

    async def top():  # top coroutine with nested sub coroutine
        result = await bot()
        return result

    assert inspect.iscoroutinefunction(top)
    topo = top()  # create async corouting object from function
    assert inspect.iscoroutine(topo)
    assert inspect.isawaitable(topo)
    with pytest.raises(RuntimeError) as ex:
        topo.send(None)
    assert ex.value.args[0] == 'no running event loop'

    guff = dict()  # global so can see after run
    ruff = dict()

    def genor(): # regular generator that wraps async coroutine
        count = 0
        results = []
        gots = []
        got = (yield count)
        count += 1
        assert got == 1
        gots.append(got)
        topo = top()  # create async corouting object from function
        while True:
            try:
                result = topo.send(None)
                assert result
                results.append(dict(result=result,
                                    dt=f"genor {datetime.now().time().isoformat('milliseconds')}"))
            except StopIteration as ex:
                result = ex.value
                assert len(result) == 2
                results.append(dict(result=result,
                                    dt=f"genor {datetime.now().time().isoformat('milliseconds')}"))
                break
            got = (yield result)
            gots.append(got)
            count += 1
            guff["gots"] = gots
            guff["results"] = results
        return guff

    assert inspect.isgeneratorfunction(genor)
    dog = genor()  # make generator
    assert inspect.isgenerator(dog)



    async def bdo(): # scheduler of genor
        results = []
        dog = genor()  # create dog
        done = False
        count = 0
        try:
            result = dog.send(None)
            results.append(dict(result=result,
                                dt=f"bdo {datetime.now().time().isoformat('milliseconds')}"))
        except StopIteration as ex:  # never executes this
            result = ex.value
            results.append(dict(result=result,
                                dt=f"bdo {datetime.now().time().isoformat('milliseconds')}"))
            assert result == None
            done = True

        while not done:
            await asyncio.sleep(0.1)
            count += 1
            try:
                result = dog.send(count)
                results.append(dict(result=result,
                                dt=f"bdo {datetime.now().time().isoformat('milliseconds')}"))
            except StopIteration as ex:
                result = ex.value
                assert len(result) == 2
                results.append(dict(result=result,
                                dt=f"bdo {datetime.now().time().isoformat('milliseconds')}"))
                done = True
        ruff["results"] = results
        return ruff

    asyncio.run(bdo())
    """
    assert guff == \
    {
        'gots': [1, 2, 3],
        'results':
        [
            {
                'result': <Future finished result=None>,
                'dt': 'genor 11:01:22.927'
            },
            {
                'result': <Future finished result=None>,
                'dt': 'genor 11:01:23.028'},
            {
                'result':
                [
                    {'result': None, 'dt': 'bot 11:01:23.028'},
                    {'result': None, 'dt': 'bot 11:01:23.129'}
                ],
                'dt': 'genor 11:01:23.129'
            }
        ]
    }
    """

    """
    assert ruff == \
    {
        'results':
        [
            {
                'result': 0,
                'dt': 'bdo 14:35:27.333'
            },
            {
                'result': <Future finished result=None>,
                'dt': 'bdo 14:35:27.433'
            },
            {
                'result': <Future finished result=None>,
                'dt': 'bdo 14:35:27.534'
            },
            {
                'result':
                {
                    'gots': [1, 2, 3],
                    'results':
                    [
                        {
                            'result': <Future finished result=None>,
                            'dt': 'genor 14:35:27.433'
                        },
                        {
                            'result': <Future finished result=None>,
                            'dt': 'genor 14:35:27.534'
                        },
                        {
                            'result':
                            [
                                {
                                    'result': None,
                                    'dt': 'bot 14:35:27.534'
                                },
                                {
                                    'result': None,
                                    'dt': 'bot 14:35:27.635'
                                }
                            ],
                            'dt': 'genor 14:35:27.635'
                        }
                    ]
                },
                'dt': 'bdo 14:35:27.635'
            }
        ]
    }

    """

    # try with different approach

    async def foo():  # basic async coroutine
        results = []
        result = await asyncio.sleep(0.1)
        results.append(dict(result=result,
                            dt=f"foo {datetime.now().time().isoformat('milliseconds')}"))
        result = await asyncio.sleep(0.1)
        results.append(dict(result=result,
                            dt=f"foo {datetime.now().time().isoformat('milliseconds')}"))
        return results

    async def bar():  # top coroutine with nested sub coroutine
        result = await foo()
        return dict(result=result,
                    dt=f"bar {datetime.now().time().isoformat('milliseconds')}")

    tuff = dict()  # global

    def rdoer(): # regular generator that wraps async coroutine
        count = 0
        gots = []
        results = []
        got = (yield count)
        count += 1
        gots.append(dict(got = got,
                         dt = f"rdoer {datetime.now().time().isoformat('milliseconds')}"))
        baro = bar()  # create async corouting object from function
        while True:
            try:
                result = baro.send(None)
                results.append(dict(result=result,
                                    dt=f"rdoer {datetime.now().time().isoformat('milliseconds')}"))
            except StopIteration as ex:
                result = ex.value
                results.append(dict(result=result,
                                    dt=f"rdoer {datetime.now().time().isoformat('milliseconds')}"))
                break
            got = (yield count)
            count += 1
            gots.append(dict(got = got,
                             dt = f"rdoer {datetime.now().time().isoformat('milliseconds')}"))
        tuff.update(dict(gots=gots, results=results))
        return tuff

    puff = dict()  # global

    class ADoist():
        """scheduler that is asyncio aware via ado"""

        async def ado(self): # scheduler of doer
            results = []
            dog = rdoer()  # create dog
            done = False
            count = 0
            try:
                result = dog.send(None)
                results.append(dict(result=result,
                                    dt=f"ADoist {datetime.now().time().isoformat('milliseconds')}"))
            except StopIteration as ex:
                result = ex.value
                results.append(dict(result=result,
                                    dt=f"ADoist {datetime.now().time().isoformat('milliseconds')}"))
                done = True

            while not done:
                #await asyncio.sleep(0.1)
                count += 1
                try:
                    result = dog.send(count)
                    results.append(dict(result=result,
                                        dt=f"ADoist {datetime.now().time().isoformat('milliseconds')}"))
                except StopIteration as ex:
                    result = ex.value
                    results.append(dict(result=result,
                                        dt=f"ADoist {datetime.now().time().isoformat('milliseconds')}"))
                    done = True
                await asyncio.sleep(0.1)

            puff.update(dict(results=results))
            return puff

    asyncio.run(ADoist().ado())
    assert True
    """assert tuff == \
    {
        'gots':
        [
            {'got': 1, 'dt': 'rdoer 15:13:17.214'},
            {'got': 2, 'dt': 'rdoer 15:13:17.315'},
            {'got': 3, 'dt': 'rdoer 15:13:17.417'}
        ],
        'results':
        [
            {
                'result': <Future finished result=None>,
                'dt': 'rdoer 15:13:17.214'
            },
            {
                'result': <Future finished result=None>,
                'dt': 'rdoer 15:13:17.315'},
            {
                'result':
                {
                    'result':
                    [
                        {'result': None, 'dt': 'foo 15:13:17.315'},
                        {'result': None, 'dt': 'foo 15:13:17.417'}
                    ],
                    'dt': 'bar 15:13:17.417'
                },
                'dt': 'rdoer 15:13:17.417'
            }
        ]
    }
    """
    """
    assert puff == \
    {
        'results':
        [
            {
                'result': 0,
                'dt': 'ADoist 15:29:15.895'
            },
            {
                'result': 1,
                'dt': 'ADoist 15:29:15.996'
            },
            {
                'result': 2,
                'dt': 'ADoist 15:29:16.098'
            },
            {
                'result':
                {
                    'gots':
                    [
                        {'got': 1, 'dt': 'rdoer 15:29:15.996'},
                        {'got': 2, 'dt': 'rdoer 15:29:16.097'},
                        {'got': 3, 'dt': 'rdoer 15:29:16.199'}
                    ],
                    'results':
                    [
                        {
                            'result': <Future finished result=None>,
                            'dt': 'rdoer 15:29:15.996'
                        },
                        {
                            'result': <Future finished result=None>,
                            'dt': 'rdoer 15:29:16.098'
                        },
                        {
                            'result':
                            {
                                'result':
                                [
                                    {'result': None, 'dt': 'foo 15:29:16.097'},
                                    {'result': None, 'dt': 'foo 15:29:16.199'}
                                ],
                                'dt': 'bar 15:29:16.199'},
                            'dt': 'rdoer 15:29:16.199'}
                    ]
                },
                'dt': 'ADoist 15:29:16.199'
            }
        ]
    }
    """


    """Done Test"""



if __name__ == "__main__":
    test_asyncio_basic()
    test_asyncio_await_method()
    test_asyncio_doist()
