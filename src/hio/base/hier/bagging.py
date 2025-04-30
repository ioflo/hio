# -*- encoding: utf-8 -*-
"""hio.base.hier.bagging Module

Provides dom support for items hold

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections import deque, namedtuple
from collections.abc import Iterable, Mapping, Callable
from typing import Any, Type, ClassVar
from dataclasses import dataclass, astuple, asdict, field, fields, InitVar

from ...help import registerify, namify, TymeDom
from ...hioing import HierError



@namify
@registerify
@dataclass
class Bag(TymeDom):
    """Bag is simple TymeDom subclass with generic value field.

    Inherited Non-Field Class Attributes:
        _registry (ClassVar[dict]): dict of subclasses keyed by class.__name__
            Assigned by @registerify decorator
        _names (ClassVar[tuple[str]|None]): tuple of field names for class
            Assigned by @namify decorator

    Inherited Non-Field Attributes:
        _tymth (None|Callable): function wrapper closure returned by
            Tymist.tymen() method. When .tymth is called it returns associated
            Tymist.tyme. Provides injected dependency on Tymist cycle tyme base.
            None means not assigned yet.
            Use ._wind method to assign ._tymth after init of bag.
        _tyme (None|Float): cycle tyme of last update of a bag field.
            None means either ._tymth as not yet been assigned or this bag's
            fields have not yet been updated.

    Inherited Properties:
        _now (None|float): current tyme given by ._tymth if not None.

    Field Attributes:
       value (Any):  generic value field
    """
    value: Any = None  # generic value


