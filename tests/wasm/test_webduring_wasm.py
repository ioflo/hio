# -*- encoding: utf-8 -*-
"""
tests.wasm.test_webduring_wasm module

WASM smoke tests for WebDuror, run inside Pyodide via pytest-pyodide.
"""
import os

import pytest


if os.environ.get("RUN_WASM_TESTS") != "true":
    pytest.skip(
        "WASM tests require RUN_WASM_TESTS=true with a pytest-pyodide runtime",
        allow_module_level=True,
    )

pytest_pyodide = pytest.importorskip("pytest_pyodide")
run_in_pyodide = pytest_pyodide.run_in_pyodide
copy_files_to_pyodide = pytest_pyodide.decorator.copy_files_to_pyodide

WASM_PACKAGES = ["cbor2", "micropip", "msgpack", "multidict", "sortedcontainers"]

HIO_FILES = [
    ("src/hio/__init__.py", "/home/pyodide/hio/__init__.py"),
    ("src/hio/hioing.py", "/home/pyodide/hio/hioing.py"),
    ("src/hio/base/__init__.py", "/home/pyodide/hio/base/__init__.py"),
    ("src/hio/base/basing.py", "/home/pyodide/hio/base/basing.py"),
    ("src/hio/base/doing.py", "/home/pyodide/hio/base/doing.py"),
    ("src/hio/base/during.py", "/home/pyodide/hio/base/during.py"),
    ("src/hio/base/filing.py", "/home/pyodide/hio/base/filing.py"),
    ("src/hio/base/tyming.py", "/home/pyodide/hio/base/tyming.py"),
    ("src/hio/base/webduring.py", "/home/pyodide/hio/base/webduring.py"),
    ("src/hio/help/__init__.py", "/home/pyodide/hio/help/__init__.py"),
    ("src/hio/help/decking.py", "/home/pyodide/hio/help/decking.py"),
    ("src/hio/help/doming.py", "/home/pyodide/hio/help/doming.py"),
    ("src/hio/help/helping.py", "/home/pyodide/hio/help/helping.py"),
    ("src/hio/help/hicting.py", "/home/pyodide/hio/help/hicting.py"),
    ("src/hio/help/mining.py", "/home/pyodide/hio/help/mining.py"),
    ("src/hio/help/naming.py", "/home/pyodide/hio/help/naming.py"),
    ("src/hio/help/ogling.py", "/home/pyodide/hio/help/ogling.py"),
    ("src/hio/help/timing.py", "/home/pyodide/hio/help/timing.py"),
]


@copy_files_to_pyodide(file_list=HIO_FILES)
@run_in_pyodide(packages=WASM_PACKAGES)
async def test_webduror_wasm_contract(selenium):
    """Verify WebDuror imports and core storage behavior in WASM."""
    import sys
    import micropip

    await micropip.install("ordered_set")
    sys.path.insert(0, "/home/pyodide")

    import hio
    import hio.base
    from hio.base import WebDuror

    assert "hio.base.during" not in sys.modules
    assert "pysodium" not in sys.modules
    assert "pychloride" not in sys.modules

    class FakeHandle:
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
            self.backend.persisted[self.namespace] = dict(self._local)

    class FakeBackend:
        def __init__(self):
            self.persisted = {}

        async def open(self, namespace):
            return FakeHandle(self, namespace)

    backend = FakeBackend()
    duror = WebDuror(name="wasm", storageOpener=backend.open)
    await duror.reopen(stores=(b"docs.", b"io.", b"ioset."))
    docs = duror.env.open_db(key=b"docs.")
    io = duror.env.open_db(key=b"io.")
    ioset = duror.env.open_db(key=b"ioset.")

    assert duror.version == hio.__version__
    assert duror.pinVal(sdb=docs, key=b"alpha", val=b"one")
    assert duror.pinVal(sdb=docs, key=b"\xff.key", val=b"\x00.value")
    assert duror.addIoVal(sdb=io, key=b"queue", val=b"first")
    assert duror.putIoSetVals(sdb=ioset, key=b"set", vals=[b"a", b"a", b"b"])
    assert duror.getIoVals(sdb=ioset, key=b"set") == [b"a", b"b"]
    assert await duror.flush() == 3
    await duror.aclose()

    reopened = WebDuror(name="wasm", storageOpener=backend.open)
    await reopened.reopen(stores=(b"docs.", b"io.", b"ioset."))
    docs = reopened.env.open_db(key=b"docs.")
    io = reopened.env.open_db(key=b"io.")
    ioset = reopened.env.open_db(key=b"ioset.")

    assert reopened.getVal(sdb=docs, key=b"alpha") == b"one"
    assert reopened.getVal(sdb=docs, key=b"\xff.key") == b"\x00.value"
    assert reopened.getIoVals(sdb=io, key=b"queue") == [b"first"]
    assert reopened.getIoVals(sdb=ioset, key=b"set") == [b"a", b"b"]
    await reopened.aclose(clear=True)

    cleared = WebDuror(name="wasm", storageOpener=backend.open)
    await cleared.reopen(stores=(b"docs.",))
    docs = cleared.env.open_db(key=b"docs.")
    assert cleared.getVal(sdb=docs, key=b"alpha") is None
    await cleared.aclose()

    assert "hio.base.during" not in sys.modules
    assert "pysodium" not in sys.modules
    assert "pychloride" not in sys.modules
