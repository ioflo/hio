# -*- encoding: utf-8 -*-
"""hio.core.hier.bagging Module

Provides dom support for items in Mine or Dock for shared data store support

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections import deque, namedtuple
from collections.abc import Iterable, Mapping, Callable
from typing import Any, Type
from dataclasses import dataclass, astuple, asdict, field

from ...help import RawDom

@dataclass
class BagDom(RawDom):
    """BagDom is base class for Bag subclasses with common fields.


    Attributes:
        _tyme (None|Float): tyme of last update of bag during prep/run time
                            None means not yet updated during prep/run time.
                            bag may be initialized during init time but
                            does not get a non-None tyme until its first update
                            during prep/run time.
    """
    _tyme: None|float = None  # tyme of last update


@dataclass
class Bag(BagDom):
    """Bag is simple BagDom sublclass with generic value field.


    Inherited Attributes:
        _tyme (None|Float): tyme of last update of bag during prep/run time
                            None means not yet updated during prep/run time.
                            bag may be initialized during init time but
                            does not get a non-None tyme until its first update
                            during prep/run time.

    Attributes:
       value (Any):
    """
    value: Any = None  # generic value
