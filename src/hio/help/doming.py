# -*- encoding: utf-8 -*-
"""hio.help.doming module

Support for Dataclass Object Mapper Dom classes
"""

from __future__ import annotations  # so type hints of classes get resolved later

import functools
import json
import msgpack
import cbor2 as cbor

from typing import Any, Type, ClassVar
from collections.abc import Callable
from dataclasses import dataclass, astuple, asdict, fields, field, InitVar

# DOM Utilities dataclass utility classes


def dictify(val):
    """
    Returns a serializable dict represention of a dataclass.  If the dataclass
    contains a `_dictify method, use it instead of `asdict`

    Parameters:
         val the dataclass instance to turn into a dict.
    """
    dit = getattr(val, "_dictify", None)
    if callable(dit):
        return dit()

    return asdict(val)


def datify(cls, d):
    """Returns instance of dataclass cls converted from dict d. If the dataclass
    cls or any nested dataclasses contains a `_datify` method, the use it instead
    of default fieldtypes conversion.

    Parameters:
    cls is dataclass class
    d is dict
    """
    try:
        dat = getattr(cls, "_datify", None)
        if callable(dat):
            return dat(d)

        fieldtypes = {f.name: f.type for f in fields(cls)}
        return cls(**{f: datify(fieldtypes[f], d[f]) for f in d})  # recursive
    except Exception:  # Fields in dict d don't match dataclass or something else
        return d  # not a dataclass so end recursion and next level up will process



@dataclass(frozen=True)
class IceMapDom:
    """Base class for frozen dataclasses (codexes) that support map syntax
    Adds support for dunder methods for map syntax dc[name].
    Converts exceptions from attribute syntax to raise map syntax when using
    map syntax.

    Note: iter astuple

    Enables dataclass instances to use Mapping item syntax
    """
    def __getitem__(self, name):
        try:
            return getattr(self, name)
        except AttributeError as ex:
            raise IndexError(ex.args) from ex

    def __iter__(self):
        return iter(self._asdict())

    #def __iter__(self):
        #return iter(astuple(self))


    def _asdict(self):
        """Returns dict version of record"""
        return dictify(self)


    def _astuple(self):
        """Returns dict version of record"""
        return tuple(self._asdict().values())


class MapDom:
    """MapDom is a base class for dataclasses that support map syntax
    Adds support for dunder methods for map syntax dc[name].
    Converts exceptions from attribute syntax to raise map syntax when using
    map syntax.

    Note: iter asdict

    Enables dataclass instances to use Mapping item syntax

    Class Methods:
        _fromdict(cls, d: dict): return dataclass converted from dict d

    Methods:
        __getitem__(self, name)  map like interface
        __setitem__(self, name, value)  map like interface
        __iter__():  asdict(self)
        _asdict(): return self converted to dict
        _astuple(): return self converted to tuple
        _update(*pa,**kwa): update attributes using dict like update syntax
    """

    @classmethod
    def _fromdict(cls, d: dict):
        """returns instance of cls initialized from dict d """
        dom = datify(cls, d)
        if not isinstance(dom, cls):
            raise ValueError("Invalid dict={d} to datify as dataclass={cls}.")
        return dom


    def __getitem__(self, name):
        try:
            return getattr(self, name)
        except AttributeError as ex:
            raise IndexError(ex.args) from ex


    def __setitem__(self, name, value):
        try:
            return setattr(self, name, value)
        except AttributeError as ex:
            raise IndexError(ex.args) from ex

    # dataclasses to not allow delattr
    #def __delitem__(self, name):
        #try:
            #return delattr(self, name)
        #except AttributeError as ex:
            #raise IndexError(ex.args) from ex

    def __iter__(self):
        return iter(self._asdict())


    def _asdict(self):
        """Returns dict version of record"""
        return dictify(self)


    def _astuple(self):
        """Returns dict version of record"""
        return tuple(self._asdict().values())


    def _update(self, *pa, **kwa):
        """Use item update syntax
        """
        if len(pa) > 1:
            raise TypeError(f"Expected 1 positional argument got {len(pa)}.")

        if pa:
            di = pa[0]
            if isinstance(di, Mapping):
                for k, v in di.items():
                    self[k] = v
            elif isinstance(di, Iterable):
                for k, v in di:
                    self[k] = v
            else:
                raise TypeError(f"Expected Mapping or Iterable got {type(di)}.")

        for k, v in kwa.items():
            self[k] = v



def modify(mods: MapDom|None=None, klas: Type[MapDom]=MapDom)->Callable[..., Any]:
    """Wrapper with argument(s) that injects mods dataclass instance that must
    be a subclass of MapDom. When mods is provided it is injected as the keyword
    arg 'mods' into the wrapped function.
    If mods is None then an instance of klas is created and injected instead.
    This creates a lexical closure of this injection. The value of klas must
    also be a a MapDom subclass.

    Parameters:
        mods (WorkDom|None): default None. Instance of dataclass to be injected
        klas (Type[WorkDom]): defualt WorkDom. Class of dataclass to be injected
                             as default when mods not provided.

    If wrapped function call itself includes mods as an arg whose value is
    not None then does not inject. This allows override of a single call.
    Subsequent calls will resume using the lexical closure or the wrapped
    injected mods whichever was provided.

    Assumes wrapped function defines mods argument as a keyword only parameter
    using '*' such as:
       def f(name='box, over=None, *, mods=None):

    To use inline:
        mods = WorkDom(box=None, over=None, bepre='box', beidx=0)
        g = modify(mods)(f)

    Later calling g as:
        g(name="mid", over="top")
    Actually has mods inject as if called as:
        g(name="mid", over="top", mods=mods)

    Also can be used on a method not just a function.
       def m(self, name='box, over=None, *, mods=None):

    To use inline:
        mods = dict(box=None, over=None, bepre='box', beidx=0)
        m = modify(mods)(self.m)

    Later calling m as:
        m(name="mid", over="top")
    Actually has mods injectd as if called as:
        m(name="mid", over="top", mods=mods)  where self is also injected into method

    Since mods is a mutable collection i.e. dataclass, not an immutable object
    using @decorator syntax on could be problematic as the injected mods would
    be a lexical closure defined in the defining scope not the calling scope.
    Depends on what the use case it for it.

    Example:
        mods = WorkDom(box=None, over=None, bepre='box', beidx=0)
        @modify(mods=mods)
        def f(name="box), over=None, *, mods=None)

    Later calling f as:
        f(name="mid", over="top")
    Actually has mods injected as if called as:
        f(name="mid", over="top", mods=mods)

    But the mods in this case is from the defining scope,not the calling scope.

    Likewise passing in mods=None would result in a lexical closure of mods
    with default values initially that would be shared everywhere f() is called.

    When f() is called with an explicit mods such as f(mods=mods) then that
    call will use the passed in mods not the injected mods. This allows a per
    call override of the injected mods.

    """
    mods = mods if mods is not None else klas()  # lexical closure so not None
    def decorator(f):
        @functools.wraps(f)
        def inner(*pa, **kwa):
            if 'mods' not in kwa or kwa['mods'] is None:  # missing or None
                kwa.update(mods=mods)  # replace or add mods to kwa
            return f(*pa, **kwa)
        return inner
    return decorator


def modize(mods: dict|None=None) -> Callable[..., Any]:
    """Wrapper with argument(s) that injects dict or mods dataclass instance
    that must be a subclass of MapDom as lexical closure into the wrapped function
    as keyword parameter 'mods' .

    If wrapped function call itself includes mods as an arg whose value is
    not None then does not inject. This allows override of a single call.
    Subsequent calls will resume using the lexical closure or the wrapped
    injected mods whichever was provided.

    Assumes wrapped function defines mods argument as a keyword only parameter
    using '*' such as:
       def f(name='box, over=None, *, mods=None):

    To use inline:
        mods = dict(box=None, over=None, bepre='box', beidx=0)
        g = modize(mods)(f)

    Later calling g as:
        g(name="mid", over="top")
    Actually has mods injected as if called as:
        g(name="mid", over="top", mods=mods)

    If method then works as well.
       def f(self, name='box, over=None, *, mods=None):

    To use inline:
        mods = dict(box=None, over=None, bepre='box', beidx=0)
        f = modize(mods)(self.f)

    Later calling f as:
        f(name="mid", over="top")
    Actually has mods injected as if called as:
        f(name="mid", over="top", mods=mods)  the self is automaticall supplied

    Since mods is a mutable collection i.e. dict, not an immutable string then
    using it as decorator could be problematic as the mods would have lexical
    defining scope not calling scope.
    Which is ok if mods has lexical module scope intentionally.

    Example:
        mods = dict(box=None, over=None, bepre='box', beidx=0)

        @modize(mods=mods)
        def f(name="box), over=None, *, mods=None)

    Later calling as:
        f(name="mid", over="top")
    Actually has mods injected as if called as:
        f(name="mid", over="top", mods=mods)

    But the mods in this case is from the defining scope not the calling scope.

    Likewise passing in mods=None would result in a lexical closure of mods
    with default values initially that would be shared everywhere f() is called
    with whatever values each call changes in the lexical closure of mods.
    """
    mods = mods if mods is not None else {}  # {} in lexical closure when None
    def decorator(f):
        @functools.wraps(f)
        def inner(*pa, **kwa):
            if 'mods' not in kwa or kwa['mods'] is None:  # missing or None
                kwa.update(mods=mods)  # replace or add works to kwa
            return f(*pa, **kwa)
        return inner
    return decorator



@dataclass
class RawDom(MapDom):
    """RawDom is subclass of MapDom that adds methods for converting to/from
    raw format serializations in JSON, CBOR, and MGPK. RawDom is a base class
    for such dataclasses. The serialization process is to transform dataclass into
    dict and then serialize into raw. The deserialization process is and to
    deserialize into dict and then convert to dataclass. This allows dataclass
    to stored in databases or to be sent over the wire in messages in raw format.


    Inherited Class Methods:
        _fromdict(cls, d: dict): return dataclass converted from dict d

    Class Methods:
        _fromjson(cls, s: str|bytes): return dataclass converted from json s
        _fromcbor(cls, s: bytes): return dataclass converted from cbor s
        _frommgpk(cls, s: bytes): return dataclass converted from mgpk s

    Inherited Methods:
        __getitem__(self, name)  map like interface
        __setitem__(self, name, value)  map like interface
        __iter__(self): asdict(self)
        _asdict(self): return self converted to dict
        _astuple(): return self converted to tuple
        _update(*pa,**kwa): update attributes using dict like update syntax

    Methods:
        _asjson(self): return bytes self converted to json
        _ascbor(self): return bytes self converted to cbor
        _asmgpk(self): return bytes self converted to mgpk
    """

    @classmethod
    def _fromjson(cls, s: str | bytes):
        """returns instance of clas initialized from json str or bytes s """
        if hasattr(s, "decode"):  # bytes
            s = s.decode() # convert to str
        d = json.loads(s)  # convert to dict
        dom = datify(cls, d)
        if not isinstance(dom, cls):
            raise ValueError("Invalid dict={d} to datify as dataclass={cls}.")
        return dom


    @classmethod
    def _fromcbor(cls, s: bytes):
        """returns instance of clas initialized from cbor bytes or str s """
        d = cbor.loads(s)  # convert to dict
        dom = datify(cls, d)
        if not isinstance(dom, cls):
            raise ValueError("Invalid dict={d} to datify as dataclass={cls}.")
        return dom


    @classmethod
    def _frommgpk(cls, s: bytes):
        """returns instance of clas initialized from mgpk bytes or str s """
        d = msgpack.loads(s)  # convert to dict
        dom = datify(cls, d)
        if not isinstance(dom, cls):
            raise ValueError("Invalid dict={d} to datify as dataclass={cls}.")
        return dom


    def __getitem__(self, name):
        try:
            return getattr(self, name)
        except AttributeError as ex:
            raise IndexError(ex.args) from ex


    def __setitem__(self, name, value):
        try:
            return setattr(self, name, value)
        except AttributeError as ex:
            raise IndexError(ex.args) from ex

    # dataclasses don't allow deletion of attributes
    #def __delitem__(self, name):
        #try:
            #return delattr(self, name)
        #except AttributeError as ex:
            #raise IndexError(ex.args) from ex

    def _update(self, *pa, **kwa):
        """Use item update syntax
        """
        if len(pa) > 1:
            raise TypeError(f"Expected 1 positional argument got {len(pa)}.")

        if pa:
            di = pa[0]
            if isinstance(di, Mapping):
                for k, v in di.items():
                    self[k] = v
            elif isinstance(di, Iterable):
                for k, v in di:
                    self[k] = v
            else:
                raise TypeError(f"Expected Mapping or Iterable got {type(di)}.")

        for k, v in kwa.items():
            self[k] = v


    def __iter__(self):
        return iter(self._asdict())


    def _asdict(self):
        """Returns dict version of record"""
        return dictify(self)


    def _astuple(self):
        """Returns dict version of record"""
        return tuple(self._asdict().values())


    def _asjson(self):
        """Returns json bytes version of record"""
        return json.dumps(self._asdict(),
                          separators=(",", ":"),
                          ensure_ascii=False).encode()  # ensure bytes


    def _ascbor(self):
        """Returns cbor bytes version of record"""
        return cbor.dumps(self._asdict())


    def _asmgpk(self):
        """Returns mgpk bytes version of record"""
        return msgpack.dumps(self._asdict())



def registerify(cls):
    """Class Decorator to add cls as cls._registry entry for itself keyed by its
    own .__name__. Need class decorator so that class object is already created
    by registration time when decorator is applied
    """
    name = cls.__name__
    if name in cls._registry:
        raise HierError(f"RegDom subclass {name=} already registered.")
    cls._registry[name] = cls
    return cls


@registerify
@dataclass
class RegDom(RawDom):
    """RegDom is base class for Dom subclasses that have class registry as
    as non field ClassVar that holds mapping between class name and class object.
    Use the registerify decorator to populate the registry with a given dataclass.

    This allows registry based creation of instances from the class name.

    Non-Field Class Attributes:
        _registry (ClassVar[dict]): dict of subclasses keyed by class.__name__
            Assigned by @registerify decorator

    """
    _registry:  ClassVar[dict] = {}  # subclass registry


def namify(cls):
    """Class decorator for dataclass to populate ClassVar ._names with names
    of all fields in dataclass
    """
    cls._names = tuple(field.name for field in fields(cls))
    return cls


@namify
@registerify
@dataclass
class TymeDom(RegDom):
    """TymeDom is base class for Dom dataclasses that are registered and support
    the cycle tyme stamping of updates to named fields using non-field attributes.
    Use decorator registerify to populate ._registry
    Use deocrator namify to populate ._names which holds names of field attributes

    Inherited Non-Field Class Attributes:
        _registry (ClassVar[dict]): dict of subclasses keyed by class.__name__
            Assigned by @registerify decorator

    Non-Field Class Attributes:
        _names (ClassVar[tuple[str]|None]): tuple of field names for class
            Assigned by @namify decorator

    Non-Field Attributes:
        _tymth (None|Callable): function wrapper closure returned by
            Tymist.tymen() method. When .tymth is called it returns associated
            Tymist.tyme. Provides injected dependency on Tymist cycle tyme base.
            None means not assigned yet.
            Use ._wind method to assign ._tymth after init of bag.
        _tyme (None|Float): cycle tyme of last update of a bag field.
            None means either ._tymth as not yet been assigned or this bag's
            fields have not yet been updated.

    Properties:
        _now (None|float): current tyme given by ._tymth if not None.

    """
    _names: ClassVar[tuple[str]|None] = None  # Assigned in  __post_init__
    _tymth: InitVar[None|Callable] = None  # tymth closure not a field
    _tyme: InitVar[None|float] = None  # tyme of last update

    def __post_init__(self, _tymth, _tyme):
        self._tymth = _tymth
        self._tyme = _tyme


    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name in self._names:
            super().__setattr__("_tyme", self._now)


    def __setitem__(self, k, v):
        try:
            return setattr(self, k, v)
        except AttributeError as ex:
            raise IndexError(ex.args) from ex


    def _update(self, *pa, **kwa):
        """Use item update syntax
        """
        if pa:
            if len(pa) > 1:
                raise TypeError(f"Expected 1 positional argument got {len(pa)}.")

            di = pa[0]
            if isinstance(di, Mapping):
                for k, v in di.items():
                    self[k] = v
            elif isinstance(di, NonStringIterable):
                for k, v in di:
                    self[k] = v
            else:
                raise TypeError(f"Expected Mapping or NonStringIterable got"
                                f" {type(di)}.")

        for k, v in kwa.items():
            self[k] = v


    @property
    def _now(self):
        """Gets current tyme from injected ._tymth closure from Tymist.
        tyme is float cycle time in seconds
        Returns:
            _now (float | None): tyme from self.tymth() when wound else None
        """
        return self._tymth() if self._tymth else None


    def _wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Override in subclasses to update any dependencies on a change in
        tymist.tymth base
        """
        self._tymth = tymth
