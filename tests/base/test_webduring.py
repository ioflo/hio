# -*- encoding: utf-8 -*-
"""Browser-safe WebDuror contract tests."""

import asyncio

import pytest

import hio
from hio.base import (
    DomIoSetSuber,
    DomIoSuber,
    DomSuber,
    IoSetSuber,
    IoSuber,
    Suber,
    WebDuror,
    openWebDuror,
)
from hio.base.hier import Can


def run(coro):
    return asyncio.run(coro)


class FakeStorageHandle:
    """Async storage handle with local writes and explicit sync commit."""

    def __init__(self, backend, namespace):
        self.backend = backend
        self.namespace = namespace
        self._local = dict(self.backend.persisted.get(namespace, {}))

    def get(self, key, default=None):
        return self._local.get(key, default)

    def __getitem__(self, key):
        return self._local[key]

    def __setitem__(self, key, value):
        self._local[key] = value

    async def sync(self):
        self.backend.synced.append(self.namespace)
        self.backend.persisted[self.namespace] = dict(self._local)


class FakeStorageBackend:
    """Minimal async opener that mimics PyScript storage commit semantics."""

    def __init__(self):
        self.persisted = {}
        self.opened = []
        self.synced = []

    async def open(self, namespace):
        self.opened.append(namespace)
        return FakeStorageHandle(self, namespace)


def test_webduror_constructor_lifecycle():
    async def main():
        with pytest.raises(hio.HierError, match="async open"):
            WebDuror(reopen=True)

        duror = WebDuror()
        with pytest.raises(hio.HierError, match="requires pyscript.storage or storageOpener"):
            await duror.reopen(stores=(b"docs.",))

        storage = FakeStorageBackend()
        duror = WebDuror(storageOpener=storage.open)
        assert not duror.opened

        assert await duror.reopen(stores=(b"docs.",))
        docs = duror.env.open_db(key=b"docs.")
        assert docs.flags() == {"dupsort": False}

        with pytest.raises(hio.HierError, match="not declared"):
            duror.env.open_db(key=b"unknown.")

        await duror.aclose()

    run(main())


def test_webduror_base_namespaces_are_isolated():
    async def main():
        storage = FakeStorageBackend()
        first = WebDuror(name="same", base="a", storageOpener=storage.open)
        await first.reopen(stores=(b"docs.",))
        fsdb = first.env.open_db(key=b"docs.")
        assert first.pinVal(sdb=fsdb, key=b"k", val=b"a")
        await first.aclose()

        same = WebDuror(name="same", base="a", storageOpener=storage.open)
        await same.reopen(stores=(b"docs.",))
        ssdb = same.env.open_db(key=b"docs.")
        assert same.getVal(sdb=ssdb, key=b"k") == b"a"
        await same.aclose()

        other = WebDuror(name="same", base="b", storageOpener=storage.open)
        await other.reopen(stores=(b"docs.",))
        osdb = other.env.open_db(key=b"docs.")
        assert other.getVal(sdb=osdb, key=b"k") is None
        await other.aclose(clear=True)

        cleanup = WebDuror(name="same", base="a", storageOpener=storage.open)
        await cleanup.reopen(stores=(b"docs.",))
        await cleanup.aclose(clear=True)

    run(main())


def test_webduror_aclose_and_context_cleanup_edges():
    async def main():
        unopened = WebDuror()
        assert await unopened.aclose(clear=True) is False

        async def broken_opener(namespace):
            raise RuntimeError(f"open failed for {namespace}")

        with pytest.raises(RuntimeError, match="open failed"):
            async with openWebDuror(stores=(b"docs.",), storageOpener=broken_opener):
                raise AssertionError("unreachable")

    run(main())


def test_webduror_version_persists_through_flush_and_reopen():
    async def main():
        storage = FakeStorageBackend()
        duror = WebDuror(storageOpener=storage.open)
        await duror.reopen(stores=(b"docs.",))
        assert duror.version == hio.__version__

        duror.version = "1.2.3"
        assert await duror.flush() == 1
        await duror.aclose()

        reopened = WebDuror(storageOpener=storage.open)
        await reopened.reopen(stores=(b"docs.",))
        assert reopened.getVer() == "1.2.3"
        reopened.version = "2.0.0"
        await reopened.flush()
        await reopened.aclose()

        final = WebDuror(storageOpener=storage.open)
        await final.reopen(stores=(b"docs.",))
        assert final.version == "2.0.0"
        await final.aclose()

    run(main())


def test_webduror_plain_values_and_suffix_parity():
    async def main():
        storage = FakeStorageBackend()
        duror = WebDuror(storageOpener=storage.open)
        await duror.reopen(stores=(b"beep.",))
        sdb = duror.env.open_db(key=b"beep.")

        assert duror.getVal(sdb=sdb, key=b"A") is None
        assert not duror.remVal(sdb=sdb, key=b"A")
        assert duror.putVal(sdb=sdb, key=b"A", val=b"whatever")
        assert not duror.putVal(sdb=sdb, key=b"A", val=b"ignored")
        assert duror.getVal(sdb=sdb, key=b"A") == b"whatever"
        assert duror.pinVal(sdb=sdb, key=b"A", val=b"\xff\x00")
        assert duror.getVal(sdb=sdb, key=b"A") == b"\xff\x00"
        assert duror.pinVal(sdb=sdb, key=b"\xff\x00.key", val=b"\x00\xff.value")
        assert await duror.flush() == 1
        await duror.reopen(stores=(b"beep.",))
        sdb = duror.env.open_db(key=b"beep.")
        assert duror.getVal(sdb=sdb, key=b"\xff\x00.key") == b"\x00\xff.value"
        assert duror.cntVals(sdb=sdb) == 2
        assert duror.remVal(sdb=sdb, key=b"A")
        assert duror.remVal(sdb=sdb, key=b"\xff\x00.key")
        assert duror.getVal(sdb=sdb, key=b"A") is None

        for key, val in ((b"a.1", b"wow"), (b"a.2", b"wee"), (b"b.1", b"woo")):
            assert duror.putVal(sdb=sdb, key=key, val=val)
        assert list(duror.getTopItemIter(sdb=sdb)) == [
            (b"a.1", b"wow"),
            (b"a.2", b"wee"),
            (b"b.1", b"woo"),
        ]
        assert duror.remTopVals(sdb=sdb, top=b"a.")
        assert list(duror.getTopItemIter(sdb=sdb)) == [(b"b.1", b"woo")]
        assert duror.remTopVals(sdb=sdb)
        assert duror.cntVals(sdb=sdb) == 0

        key = "ABCDEFG.FFFFFF"
        assert WebDuror.suffix(key, 0) == b"ABCDEFG.FFFFFF.00000000000000000000000000000000"
        assert WebDuror.suffix(key.encode(), 64) == b"ABCDEFG.FFFFFF.00000000000000000000000000000040"
        maxed = WebDuror.suffix(key, WebDuror.MaxSuffix)
        assert maxed == b"ABCDEFG.FFFFFF.ffffffffffffffffffffffffffffffff"
        assert WebDuror.unsuffix(maxed) == (b"ABCDEFG.FFFFFF", WebDuror.MaxSuffix)

        await duror.aclose(clear=True)

    run(main())


def test_webduror_io_and_ioset_parity():
    async def main():
        storage = FakeStorageBackend()
        duror = WebDuror(storageOpener=storage.open)
        await duror.reopen(stores=(b"io.", b"ioset."))

        key0 = b"ABC_ZYX"
        key1 = b"DEF_WVU"
        key2 = b"GHI_TSR"
        vals0 = [b"z", b"m", b"x", b"a"]
        vals1 = [b"w", b"n", b"y", b"d"]
        vals2 = [b"p", b"o", b"h", b"f"]

        sdb = duror.env.open_db(key=b"io.")
        assert duror.getIoVals(sdb=sdb, key=key0) == []
        assert duror.getIoValFirst(sdb=sdb, key=key0) is None
        assert duror.getIoValLast(sdb=sdb, key=key0) is None
        assert not duror.remIoVals(sdb=sdb, key=key0)

        assert duror.putIoVals(sdb=sdb, key=key0, vals=vals0)
        assert duror.getIoVals(sdb=sdb, key=key0) == vals0
        assert duror.addIoVal(sdb=sdb, key=key0, val=b"a")
        assert duror.getIoVals(sdb=sdb, key=key0) == vals0 + [b"a"]
        assert duror.getIoValFirst(sdb=sdb, key=key0) == b"z"
        assert duror.getIoValLast(sdb=sdb, key=key0) == b"a"
        assert duror.popIoVal(sdb=sdb, key=key0) == b"z"
        assert duror.pinIoVals(sdb=sdb, key=key0, vals=[b"q", b"e"])
        assert duror.getIoVals(sdb=sdb, key=key0) == [b"q", b"e"]

        assert duror.putIoVals(sdb=sdb, key=key1, vals=vals1)
        assert duror.putIoVals(sdb=sdb, key=key2, vals=vals2)
        assert list(duror.getTopIoItemIter(sdb=sdb, top=b"DEF")) == [
            (b"DEF_WVU", b"w"),
            (b"DEF_WVU", b"n"),
            (b"DEF_WVU", b"y"),
            (b"DEF_WVU", b"d"),
        ]

        sdb = duror.env.open_db(key=b"ioset.")
        assert duror.putIoSetVals(sdb=sdb, key=key0, vals=vals0)
        assert not duror.putIoSetVals(sdb=sdb, key=key0, vals=[b"a"])
        assert duror.addIoSetVal(sdb=sdb, key=key0, val=b"b")
        assert not duror.addIoSetVal(sdb=sdb, key=key0, val=b"a")
        assert duror.getIoVals(sdb=sdb, key=key0) == vals0 + [b"b"]
        assert duror.remIoSetVal(sdb=sdb, key=key0, val=b"x")
        assert duror.getIoVals(sdb=sdb, key=key0) == [b"z", b"m", b"a", b"b"]
        assert duror.pinIoSetVals(sdb=sdb, key=key0, vals=[b"z", b"z", b"a"])
        assert duror.getIoVals(sdb=sdb, key=key0) == [b"z", b"a"]
        assert duror.popIoVal(sdb=sdb, key=key0) == b"z"
        assert duror.cntIoVals(sdb=sdb, key=key0) == 1

        await duror.aclose(clear=True)

    run(main())


def test_existing_wrappers_work_against_webduror():
    async def main():
        storage = FakeStorageBackend()
        duror = WebDuror(storageOpener=storage.open)
        await duror.reopen(stores=(b"bags.", b"io.", b"ioset.", b"cans.", b"drqs.", b"dsqs."))

        suber = Suber(db=duror, subkey="bags.")
        assert not suber.sdb.flags()["dupsort"]
        assert suber.put(keys=("a", "1"), val="alpha")
        assert not suber.put(keys=("a", "1"), val="ignored")
        assert suber.pin(keys=("a", "1"), val="beta")
        assert suber.get(keys=("a", "1")) == "beta"
        assert suber.rem(keys=("a", "1"))

        io = IoSuber(db=duror, subkey="io.")
        assert io.put(keys=("queue", "1"), vals=["one", "two"])
        assert io.get(keys=("queue", "1")) == ["one", "two"]
        assert io.pop(keys=("queue", "1")) == "one"
        assert io.get(keys=("queue", "1")) == ["two"]

        ioset = IoSetSuber(db=duror, subkey="ioset.")
        assert ioset.put(keys=("set", "1"), vals=["one", "two"])
        assert not ioset.add(keys=("set", "1"), val="one")
        assert ioset.add(keys=("set", "1"), val="three")
        assert ioset.get(keys=("set", "1")) == ["one", "two", "three"]
        assert ioset.rem(keys=("set", "1"), val="two")
        assert ioset.get(keys=("set", "1")) == ["one", "three"]

        dom = DomSuber(db=duror, subkey="cans.")
        dom.pin(keys="can", val=Can(value="alpha"))
        assert isinstance(dom.get(keys="can"), Can)
        assert dom.get(keys="can").value == "alpha"

        domio = DomIoSuber(db=duror, subkey="drqs.")
        assert domio.put(keys="queue", vals=[Can(value="one"), Can(value="two")])
        assert [can.value for can in domio.get(keys="queue")] == ["one", "two"]

        domioset = DomIoSetSuber(db=duror, subkey="dsqs.")
        assert domioset.put(keys="set", vals=[Can(value="one"), Can(value="one"), Can(value="two")])
        assert [can.value for can in domioset.get(keys="set")] == ["one", "two"]

        await duror.flush()
        await duror.aclose()

    run(main())


def test_webduror_flush_aclose_reopen_and_clear():
    async def main():
        storage = FakeStorageBackend()
        writer = WebDuror(storageOpener=storage.open)
        await writer.reopen(stores=(b"docs.",))
        sdb = writer.env.open_db(key=b"docs.")
        assert writer.pinVal(sdb=sdb, key=b"key", val=b"value")

        reader = WebDuror(storageOpener=storage.open)
        await reader.reopen(stores=(b"docs.",))
        rsdb = reader.env.open_db(key=b"docs.")
        assert reader.getVal(sdb=rsdb, key=b"key") is None
        await reader.aclose()

        assert await writer.flush() == 1
        await writer.reopen(stores=(b"docs.",))
        sdb = writer.env.open_db(key=b"docs.")
        assert writer.getVal(sdb=sdb, key=b"key") == b"value"

        assert writer.pinVal(sdb=sdb, key=b"next", val=b"value")
        await writer.aclose()
        reopened = WebDuror(storageOpener=storage.open)
        await reopened.reopen(stores=(b"docs.",))
        rsdb = reopened.env.open_db(key=b"docs.")
        assert reopened.getVal(sdb=rsdb, key=b"next") == b"value"
        await reopened.aclose(clear=True)

        cleared = WebDuror(storageOpener=storage.open)
        await cleared.reopen(stores=(b"docs.",))
        csdb = cleared.env.open_db(key=b"docs.")
        assert cleared.getVal(sdb=csdb, key=b"key") is None
        await cleared.aclose()

    run(main())


def test_webduror_sync_close_flushes_and_clears_on_running_loop():
    async def main():
        storage = FakeStorageBackend()
        writer = WebDuror(storageOpener=storage.open)
        await writer.reopen(stores=(b"docs.",))
        sdb = writer.env.open_db(key=b"docs.")
        assert writer.pinVal(sdb=sdb, key=b"key", val=b"value")

        assert writer.close()
        await asyncio.sleep(0)

        reader = WebDuror(storageOpener=storage.open)
        await reader.reopen(stores=(b"docs.",))
        rsdb = reader.env.open_db(key=b"docs.")
        assert reader.getVal(sdb=rsdb, key=b"key") == b"value"
        assert reader.pinVal(sdb=rsdb, key=b"next", val=b"value")

        assert reader.close(clear=True)
        await asyncio.sleep(0)

        cleared = WebDuror(storageOpener=storage.open)
        await cleared.reopen(stores=(b"docs.",))
        csdb = cleared.env.open_db(key=b"docs.")
        assert cleared.getVal(sdb=csdb, key=b"key") is None
        assert cleared.getVal(sdb=csdb, key=b"next") is None
        await cleared.aclose()

    run(main())


def test_webduror_sync_close_flushes_without_running_loop():
    storage = FakeStorageBackend()
    writer = WebDuror(storageOpener=storage.open)
    run(writer.reopen(stores=(b"docs.",)))
    sdb = writer.env.open_db(key=b"docs.")
    assert writer.pinVal(sdb=sdb, key=b"key", val=b"value")

    assert writer.close()

    reader = WebDuror(storageOpener=storage.open)
    run(reader.reopen(stores=(b"docs.",)))
    rsdb = reader.env.open_db(key=b"docs.")
    assert reader.getVal(sdb=rsdb, key=b"key") == b"value"

    assert reader.close(clear=True)

    cleared = WebDuror(storageOpener=storage.open)
    run(cleared.reopen(stores=(b"docs.",)))
    csdb = cleared.env.open_db(key=b"docs.")
    assert cleared.getVal(sdb=csdb, key=b"key") is None
    run(cleared.aclose())
