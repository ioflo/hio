# -*- encoding: utf-8 -*-
"""
hio.base Package
"""

import importlib

from .tyming import Tymist, Tymee, Tymer
from .doing import Doist, doize, doify, Doer, DoDoer
from .filing import openFiler, Filer, FilerDoer
from .webduring import WebSubDb, WebDuror, openWebDuror

__all__ = (
    "Tymist",
    "Tymee",
    "Tymer",
    "Doist",
    "doize",
    "doify",
    "Doer",
    "DoDoer",
    "openFiler",
    "Filer",
    "FilerDoer",
    "WebSubDb",
    "WebDuror",
    "openWebDuror",
    "Duror",
    "openDuror",
    "SuberBase",
    "Suber",
    "IoSuber",
    "IoSetSuber",
    "DomSuberBase",
    "DomSuber",
    "DomIoSuber",
    "DomIoSetSuber",
    "Subery",
    "Bosser",
    "Crewer",
    "TagDex",
)


_DURING_EXPORTS = (
    "Duror",
    "openDuror",
    "SuberBase",
    "Suber",
    "IoSuber",
    "IoSetSuber",
    "DomSuberBase",
    "DomSuber",
    "DomIoSuber",
    "DomIoSetSuber",
    "Subery",
)

_MULTIDOING_EXPORTS = (
    "Bosser",
    "Crewer",
    "TagDex",
)

# When during or multidoing is imported, import it at runtime so lmdb is not
# loaded when running in wasm. This imports the module/function, caches it,
# and returns it.
def __getattr__(name):
    if name == "during" or name in _DURING_EXPORTS:
        module = importlib.import_module(".during", __name__)
        globals()["during"] = module
        if name == "during":
            return module
        value = getattr(module, name)
        globals()[name] = value
        return value

    if name == "multidoing" or name in _MULTIDOING_EXPORTS:
        module = importlib.import_module(".multidoing", __name__)
        globals()["multidoing"] = module
        if name == "multidoing":
            return module
        value = getattr(module, name)
        globals()[name] = value
        return value

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
