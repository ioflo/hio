# -*- encoding: utf-8 -*-
"""hio.base.hier.acting Module

Provides hierarchical action support

"""
from __future__ import annotations  # so type hints of classes get resolved later


import functools

from collections.abc import Callable, Iterable
from collections import namedtuple

from ... import hioing
from ...hioing import Mixin, HierError
from .hiering import Nabes
from .needing import Need
from .bagging import Bag
from . import boxing
from .holding import Hold
from ...help import  NonStringIterable, isNonStringIterable, modify, Renam


def actify(name, *, base=None, attrs=None):
    """Parametrized decorator that converts the decorated function func into
    .act method of new subclass of class base with .__name__ name. If not
    provided then uses Act as base. When provided base must be subclass of ActBase.
    Registers new subclass in ActBase.Registry. Then instantiates cls and returns
    instance.

    Returns:
        instance (cls): instance of new subclass

    Updates the class attributes of new subclass with attrs if any.

    Any callable usually function that is not already a subclass of ActBase can be
    converted to a subclass of ActBase and then registered in the Registry by its
    given name. Usually when defining a class simply make is a subclass of ActBase.
    But when given a function on can decorate it with actify so that a new
    subclass of ActBase is created and registered.

    Usage:
        @actify(name="Tact")
        def test(self, **kwa):  # signature for .act with **iops as **kwa
            assert kwa == self.iops
            return self.iops

        t = test(iops=dict(what=1), hello="hello", nabe=Nabe.redo)

    Notes:
    In Python, when a function is assigned as the value of a class attribute,
    the value of that attribute is automagically converted to a bound method of
    that class with injected self as first argument.

    class A():
        def a(self):
           print(self)

    a = A()
    a.a()
    <__main__.A object at 0x1059ffc50>

    def b(self):
        print(self)

    A.b = b
    a.b()
    <__main__.A object at 0x1059ffc50>


    """
    base = base if base is not None else ActBase
    if not issubclass(base, ActBase):
        raise hioing.HierError(f"Expected ActBase subclass got {base=}.")

    attrs = attrs if attrs is not None else {}
    # assign Act attrs
    attrs.update(dict(Registry=base.Registry, Instances=base.Instances, Index=0,
                      Names=() ))
    cls = type(name, (base, ), attrs)  # create new subclass of base of Act.
    cls.registerbyname()  # register subclass in cls.Registry by cls.__name__

    def decorator(func):
        if not isinstance(func, Callable):
            raise hioing.HierError(f"Expected Callable got {func=}.")
        cls.act = func  # assign as bound method .act with injected self.

        @functools.wraps(func)
        def inner(*pa, **kwa):
            return cls(*pa, **kwa)  # instantiate and return instance
        return inner
    return decorator


def registerone(cls):
    """Class Decorator to add cls as cls.Registry entry for itself keyed by its
    own .__name__. Need class decorator so that class object is already created
    by registration time when decorator is applied
    """
    name = cls.__name__
    if name in cls.Registry:
        raise hioing.HierError(f"Act by {name=} already registered.")
    cls.Registry[name] = cls
    return cls


def register(names=None):
    """Parametrized class Decorator to add cls as cls.Registry entry for itself
    keyed by its own .__name__ as well as being keyed by alises in names.
    A class decorator is necessary so that the class object is already created
    when decorator is applied.

    Parameters:
        names (None|str|Iterator): iterator of names as aliases besides class
            name to register class in Act registry and assigned to cls.Names

    """
    if not names:
        names = tuple()
    elif isinstance(names, str):
        names = (names, )  # make one tuple of str
    else:
        names = tuple(names)  # make tuple of iterable

    def decorator(cls):
        name = cls.__name__
        if name in cls.Registry:  # already registration for name
            if cls.Registry[name] is not cls:  # different cls at name
                raise hioing.HierError(f"Different Act by same {name=} already "
                                       f"registered.")
        else:  # not yet regisered under name
            cls.Registry[name] = cls
        cls.Names = names  # creates class specific attribute .Names
        for name in names:
            if name in cls.Registry:   # already registration for name
                if cls.Registry[name] is not cls:  # different cls at name
                    raise hioing.HierError(f"Different Act by same {name=} already "
                                           f"registered.")
            else:  # not yet registered under name
                cls.Registry[name] = cls
        return cls
    return decorator


@register()
class ActBase(Mixin):
    """Act Base Class. Callable with Registry of itself and its subclasses.

    Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Instances (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.
        Names (tuple[str]): tuple of aliases (names) under which this subclas
                            appears in .Registry. Created by @register

    Attributes:
        hold (Hold): data shared by boxwork


    Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act
        nabe (str): action nabe (context) for .act

    Hidden
        ._name (str|None): unique name of instance
        ._iopts (dict): input-output-paramters for .act
        ._nabe (str): action nabe (context) for .act

    """
    Registry = {}  # subclass registry
    Instances = {}  # instance name registry
    Index = 0  # naming index for default names of this subclasses instances
    #Names = ()  # tuple of aliases for this subclass created by @register


    @classmethod
    def registerbyname(cls, name=None):
        """Adds cls to cls.Registry entry by name. Raises HierError if already
        registered.

        Parameters:
            cls (Type[Act]): class to be registered
            name (None|str): key to register cls under.
                             When None then use cls.__name__
        """
        name = name if name is not None else cls.__name__
        if name in cls.Registry:  # already registration for name
            if cls.Registry[name] is not cls:  # different cls at name
                raise hioing.HierError(f"Different Act by same {name=} already "
                                           f"registered.")
        else:  # not yet registered under name
            cls.Registry[name] = cls
        return cls

    @classmethod
    def _clear(cls):
        """Clears Instances and and Index for testing purposes"""
        cls.Instances = {}
        cls.Index = 0


    @classmethod
    def _clearall(cls):
        """Clears Instances and and Index for testing purposes"""
        registry = ActBase.Registry.values()
        registry = set(registry)  # so only one copy, accounts for aliases
        for klas in registry:
            klas._clear()



    def __init__(self, *, name=None, iops=None, nabe=Nabes.endo, hold=None, **kwa):
        """Initialization method for instance.

        Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for act. default is "endo"
            hold (None|Hold): data shared across boxwork

        """
        super(ActBase, self).__init__(**kwa) # in case of MRO
        self.name = name  # set name property
        self._iops = dict(iops) if iops is not None else {}  # make copy
        self._nabe = nabe if nabe is not Nabes.native else Nabes.endo
        self.hold = hold if hold is not None else Hold()


    def __call__(self):
        """Make ActBase instance a callable object.
        Call its .act method with self.iops as parameters
        """
        return self.act(**self.iops)


    def act(self, **iops):
        """Act called by Actor. Should override in subclass."""
        return iops  # for debugging


    @property
    def name(self):
        """Property getter for ._name

        Returns:
            name (str): unique identifier of instance
        """
        return self._name


    @name.setter
    def name(self, name=None):
        """Property setter for ._name

        Parameters:
            name (str|None): unique identifier of instance. When None generate
                unique name using .Index
        """
        while name is None or name in self.Instances:
                name = self.__class__.__name__ + str(self.Index)
                self.__class__.Index += 1   # do not shadow class attribute

        if not Renam.match(name):
            raise HierError(f"Invalid {name=}.")

        self.Instances[name] = self
        self._name = name


    @property
    def iops(self):
        """Property getter for ._iopts. Makes ._iopts read only

        Returns:
            iops (dict): input-output-parameters for .act
        """
        return self._iops


    @property
    def nabe(self):
        """Property getter for ._nabe. Makes ._nabe read only

        Returns:
            nabe (str): action nabe (context) for .act
        """
        return self._nabe





@register()
class Act(ActBase):
    """Act for do verb deeds as  or executable statements orcallables.
    At make (compile) time any callable that is available in the scope of the
    do verb in the boxer.make method can be passed in as the deed parameter and
    will be executed with ,iops as its parameters.

    do(deed)

    Inherited Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Instances (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.
        Names (tuple[str]): tuple of aliases (names) under which this subclas
                            appears in .Registry. Created by @register

    Overridden Class Attributes
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.


    Inherited Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act
        nabe (str): action nabe (context) for .act

    Inherited Attributes:
        hold (Hold): data shared by boxwork

    Attributes:


    Properties:
        deed (Callable|str): action to be called with .iops as parameters else
                executable set of statements with H as local
        compiled (bool): True means ._code holds compiled .deed
                         False means not yet compiled

    Hidden:
        _name (str|None): unique name of instance
        _iopts (dict): input-output-paramters for .act
        _nabe (str): action nabe (context) for .act
        _deed (Callable|str):  action to be called with .iops as parameters else
                executable set of statements with H as local
        _code (None|CodeType): compiled executable boolean statements from .deed
                               None means not yet compiled from .deed

    """
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, deed=None, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str|None): action nabe (context) for .act. Default is "endo"
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:
            deed (None|Callable):  callable to be actioned with iops

        """
        super(Act, self).__init__(**kwa)
        self._code = None
        self.iops.update(H=self.hold)  # inject .hold
        self.deed = deed if deed is not None else (lambda **iops: iops)
        if not callable(self.deed):  # need to compile
            self.compile()  # compile at init time so know if compilable


    def act(self, **iops):  # passed in by call
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms for deed when deed is callable.


        """
        if callable(self.deed):
            return self.deed(**iops)

        if not self.compiled:  # not yet compiled so lazy
            self.compile()  # first time only recompile to ._code
        H = self.hold  # ensure H is in locals() for exec
        # note iops already in locals() for exec
        return exec(self._code)


    @property
    def deed(self):
        """Property getter for ._deed

        Returns:
            deed (str): evalable boolean expression or callable.
        """
        return self._deed


    @deed.setter
    def deed(self, deed):
        """Property setter for ._expr

        Parameters:
            expr (str): evalable boolean expression.
        """
        self._deed = deed
        self._code = None  # force lazy recompilation


    @property
    def compiled(self):
        """Property compiled

        Returns:
            compiled (bool): True means ._code holds compiled ._expr
                             False means not yet compiled
        """
        return True if self._code is not None else False


    def compile(self):
        """Compile executable statements in .deed to ._code
        ._code to be executed (exec) at run time.
        Because code objects are not pickleable the instantiation compilation
        must happen after any unpickling of any instances if any.
        """
        self._code = compile(self.deed, '<string>', 'exec')




@register()
class Goact(ActBase):
    """Goact (go act) is subclass of ActBase whose .act evaluates conditional
    need expression to determine if a transition condition is satified for
    transition to its destination box.

    Inherited Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Instances (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.
        Names (tuple[str]): tuple of aliases (names) under which this subclas
                            appears in .Registry. Created by @register

    Overridden Class Attributes
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.

    Inherited Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act
        nabe (str): action nabe (context) for .act

    Inherited Attributes:
        hold (Hold): data shared by boxwork

    Attributes:
        dest (Box): destination Box for this transition.
        need (Need): transition condition to be evaluated

    Hidden
        _name (str|None): unique name of instance
        _iops (dict): input-output-paramters for .act
        _context (str): action context for .act

    """
    Index = 0  # naming index for default names of this subclasses instances
    #Names = () tuple of aliases for this subclass created by @register



    def __init__(self, dest=None, need=None, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:
            dest (None|str|Box): destination Box for this transition.
                When None then resolve later to next box of current box
                When str is box name then resolve to box with that name
                When Box instance then use directly
            need (None|str|Need): transition condition to be evaluated
                When None then always evaluates to True
                When str = bool expression then create Need from expression
                When Need instance then use directly

        """
        kwa.update(nabe=Nabes.godo)  # override must be godo nabe
        super(Goact, self).__init__(**kwa)
        self.dest = dest if dest is not None else 'next'  # default is next
        self.need = need if need is not None else Need()  # default need evals to True
        if self.nabe != Nabes.godo:
            raise HierError(f"Invalid nabe='{self.nabe}' for Goact "
                            f"'{self.name}'")



    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        if self.need():
            if not isinstance(self.dest, boxing.Box):
                raise HierError(f"Unresolved dest={self.dest}")
            return self.dest
        else:
            return None


@register(names=('end', 'End'))
class EndAct(ActBase):
    """EndAct is subclass of ActBase whose .act indicates a desire to end the
    boxer by setting bag at .iops "end" .value to True. Where "end" is at key
    "_boxer_boxername_end".



    Inherited Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Instances (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.
        Names (tuple[str]): tuple of aliases (names) under which this subclas
                            appears in .Registry. Created by @register

    Overridden Class Attributes
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.


    Inherited Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act
        nabe (str): action nabe (context) for .act

    Inherited Attributes:
        hold (Hold): data shared by boxwork

    Attributes:

    Used iops:
        _boxer (str):  boxer name


    Hidden
        _name (str|None): unique name of instance
        _iops (dict): input-output-parameters for .act
        _nabe (str): action nabe (context) for .act

    """
    Index = 0  # naming index for default names of this subclasses instances

    def __init__(self, nabe=Nabes.endo, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb (do etc)


        """
        super(EndAct, self).__init__(nabe=nabe, **kwa)

        try:
            boxer = self.iops['_boxer']  # get boxer name
        except KeyError as ex:
            raise HierError(f"Missing iops '_boxer' for '{self.name}' instance "
                            f"of Act self.__class__.__name__") from ex


        keys = ("", "boxer", boxer, "end")  # _boxer_boxername_end
        if keys not in self.hold:
            self.hold[keys] = Bag()  # create bag at end default value = None


    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        keys = ("", "boxer", boxer, "end")
        self.hold[keys].value = True


@register()
class Beact(ActBase):
    """Beact for be verb deeds

    be(lhs, rhs)  left_hand_side = right_hand_side

    Inherited Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Instances (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.
        Names (tuple[str]): tuple of aliases (names) under which this subclas
                            appears in .Registry. Created by @register

    Overridden Class Attributes
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.


    Inherited Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act
        nabe (str): action nabe (context) for .act

    Inherited Attributes:
        hold (Hold): data shared by boxwork

    Properties:
        lhs (tuple[str]): left hand sige of assignment of form (key,field)
            to be assigned as .mine[key][field]
        rhs (None|str|Callable):
            When None assign directly
            When str compile to evable expression
            When Callable then call directly with iops
        compiled (bool): True means ._code holds compiled rhs
                         False means not yet compiled

    Hidden:
        _name (str|None): unique name of instance
        _iopts (dict): input-output-paramters for .act
        _nabe (str): action nabe (context) for .act
        _lhs (tuple[str]): of form (key, field)
        _rhs (None|str|Callable):  When None assign directly
                                   When str compile to evable expression
                                   When Callable then call directly with iops
        _code (None|CodeType): compiled evalable boolean expression .rhs
                               None means not yet compiled from .rhs

    """
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, lhs: str|tuple([str]), rhs: None|str|Callable=None, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str|None): action nabe (context) for .act. Default is "endo"
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:
            lhs (str|tuple(str])): left hand side of assignment in mine[key][field]
                when str of form key.field in mine to be assigned.
                Resolves lhs to (key, field)
            rhs (None|str|Callable): right hand side of assignment
                When None assign directly
                When str compile to evable expression
                When Callable then call directly with iops

        """
        super(Beact, self).__init__(**kwa)
        self._code = None
        self.iops.update(H=self.hold)  # inject .hold
        self.lhs = lhs
        self.rhs = rhs
        if isinstance(self.rhs, str):
            self.compile()
        key, field = self.lhs
        if key not in self.hold:
            raise HierError(f"Missing mine bag at key='{key}'")
        if field not in self.hold[key]:
            raise HierError(f"Missing field='{field}' in mine bag at key='{key}'")


    def act(self, **iops):  # passed in by call
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms for deed when deed is callable.
        """
        key, field = self.lhs

        if self.rhs is None:
            self.hold[key][field] = self.rhs

        elif callable(self.rhs):
            self.hold[key][field] = self.rhs(**iops)

        else:
            if not self.compiled:  # not yet compiled so lazy
                self.compile()  # first time only recompile to ._code
            H = self.hold  # ensure H is in locals() for exec
            # note iops already in locals() for exec
            self.hold[key][field] = eval(self._code)

        return self.hold[key][field]


    @property
    def lhs(self):
        """Property getter for ._lhs

        Returns:
            lhs (tuple[str]): of form (key, field)
        """
        return self._lhs


    @lhs.setter
    def lhs(self, lhs):
        """Property setter for ._lhs

        Parameters:
            lhs (str|tuple[str]): left hand side of assignment in mine[key][field]
                when str of form key.field in mine to be assigned.
                Resolves lhs to (key, field)
        """
        if isinstance(lhs, str):
            self._lhs = tuple(lhs.rsplit(".", maxsplit=1))
        else:
            self._lhs = (key, field) = tuple(lhs)


    @property
    def rhs(self):
        """Property getter for ._rhs

        Returns:
            rhs (None|str|Callable):  right hand side of assignment
                When None assign directly
                When str compile to evable expression
                When Callable then call directly with iops
        """
        return self._rhs


    @rhs.setter
    def rhs(self, rhs):
        """Property setter for ._rhs

        Parameters:
            rhs (None|str|Callable):  right hand side of assignment
                When None assign directly
                When str compile to evable expression
                When Callable then call directly with iops
        """
        self._rhs = rhs
        self._code = None  # force lazy recompilation

    @property
    def compiled(self):
        """Property compiled

        Returns:
            compiled (bool): True means ._code holds compiled ._expr
                             False means not yet compiled
        """
        return True if self._code is not None else False


    def compile(self):
        """Compile evable boolean expression str ._expr into compiled code
        object ._code to be evaluated at run time.
        Because code objects are not pickleable the compilation must happen
        at prep (enter) time not init time.
        """
        self._code = compile(self.rhs, '<string>', 'eval')




# Dark  DockMark

@register()
class Mark(ActBase):
    """Mark (Mine Mark) is base classubclass of ActBase whose .act marks a
    box for a special need condition.

    Inherited Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Instances (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.
        Names (tuple[str]): tuple of aliases (names) under which this subclas
                            appears in .Registry. Created by @register

    Overridden Class Attributes
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.


    Inherited Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act
        nabe (str): action nabe (context) for .act

    Inherited Attributes:
        hold (Hold): data shared by boxwork

    Attributes:
        bag (Bag): marked bag in Mine

    Used iops:
        _boxer (str):  boxer name
        _box (str): box name in boxer


    Hidden
        _name (str|None): unique name of instance
        _iopts (dict): input-output-paramters for .act
        _nabe (str): action nabe (context) for .act


    """
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, nabe=Nabes.enmark, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb
            _box (str): box name in boxer.  Implicit iop injected by verb


        """
        super(Mark, self).__init__(nabe=nabe, **kwa)

        try:
            boxer = self.iops['_boxer']  # get boxer name to ensure existence
        except KeyError as ex:
            raise HierError(f"Missing iops '_boxer' for '{self.name}' instance "
                            f"of Act self.__class__.__name__") from ex

        try:
            box = self.iops['_box']  # get box name to ensure existence
        except KeyError as ex:
            raise HierError(f"Missing iops '_box' for '{self.name}' instance "
                            f"of Act self.__class__.__name__") from ex

    def act(self, **iops):
        """Act called by ActBase.

        Override in subclass

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name



@register()
class LapseMark(Mark):
    """LapseMark marks box in mine for tyme lapse special need. Enables
    condition to transit based on elapsed time in a box.

    """
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, nabe=Nabes.enmark, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb
            _box (str): box name in boxer.  Implicit iop injected by verb
            _key (str): marked bag key. Injected by on verb


        """
        super(LapseMark, self).__init__(nabe=nabe, **kwa)
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        keys = ("", "boxer", boxer, "box", box, "lapse")
        if keys not in self.hold:
            self.hold[keys] = Bag()  # create bag default value = None


    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        keys = ("", "boxer", boxer, "box", box, "lapse")
        # mark box tyme via bag._now tyme
        self.hold[keys].value = self.hold[keys]._now  # _now tyme of mark bag
        return self.hold[keys].value


@register()
class RelapseMark(Mark):
    """RelapseMark marks box in mine for tyme relapse special need. Enables
    condition to transit based on elapsed time in a box.

    """
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, nabe=Nabes.remark, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb
            _box (str): box name in boxer.  Implicit iop injected by verb
            _key (str): marked bag key. Injected by on verb


        """
        super(RelapseMark, self).__init__(nabe=nabe, **kwa)
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        keys = ("", "boxer", boxer, "box", box, "relapse")
        if keys not in self.hold:
            self.hold[keys] = Bag()  # create bag default value = None


    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        keys = ("", "boxer", boxer, "box", box, "relapse")
        # mark box tyme via bag._now tyme
        self.hold[keys].value = self.hold[keys]._now  # _now tyme of mark bag
        return self.hold[keys].value


@register(names=('count',))
class Count(Mark):
    """Count tracks count of box in mine for count special need in the nabe
    where this act is actioned.

    """
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, nabe=Nabes.redo, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb
            _box (str): box name in boxer.  Implicit iop injected by verb

        """
        super(Count, self).__init__(nabe=nabe, **kwa)
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']   # get box name
        keys = ("", "boxer", boxer, "box", box, "count")
        if keys not in self.hold:
            self.hold[keys] = Bag()  # create bag default value = None



    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        keys = ("", "boxer", boxer, "box", box, "count")
        bag = self.hold[keys]  # count bag
        if bag.value is None:
            bag.value = 0  # start counter
        else:
            bag.value += 1  # inc counter
        return bag.value


@register(names=('discount',))
class Discount(Mark):
    """Discount resets count to None of box in mine for count special need
    in the nabe where this act is actioned, usually Nabe.exdo.

    """
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, nabe=Nabes.exdo, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action  nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb
            _box (str): box name in boxer.  Implicit iop injected by verb

        """
        super(Discount, self).__init__(nabe=nabe, **kwa)
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']   # get box name
        keys = ("", "boxer", boxer, "box", box, "count")
        if keys not in self.hold:
            self.hold[keys] = Bag()  # create bag default value = None


    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        keys = ("", "boxer", boxer, "box", box, "count")
        self.hold[keys].value = None  # reset count to None
        return self.hold[keys].value




@register()
class BagMark(Mark):
    """BagMark (Mine Mark) is base classubclass of ActBase whose .act marks a
    bag value when in a box for a special need condition.

    Inherited Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Instances (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.
        Names (tuple[str]): tuple of aliases (names) under which this subclas
                            appears in .Registry. Created by @register

    Overridden Class Attributes
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.


    Inherited Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act
        nabe (str): action nabe (context) for .act

    Inherited Attributes:
        hold (Hold): data shared by boxwork

    Attributes:
        bag (Bag): marked bag in Mine

    Used iops:
        _boxer (str):  boxer name
        _box (str): box name in boxer
        _key (str): marked bag key. Injected by on verb


    Hidden
        _name (str|None): unique name of instance
        _iopts (dict): input-output-paramters for .act
        _nabe (str): action nabe (context) for .act


    """
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, nabe=Nabes.enmark, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb
            _box (str): box name in boxer.  Implicit iop injected by verb
            _key (str): marked bag key. Injected by on verb


        """
        super(BagMark, self).__init__(nabe=nabe, **kwa)

        try:
            key = self.iops['_key']  # get bag key in mine to ensure existence
        except KeyError as ex:
            raise HierError(f"Missing iops '_key' for '{self.name}' instance "
                            f"of Act self.__class__.__name__") from ex

        if key not in self.hold:
            raise HierError("Missing bag at '{key=}' for mark.")


    def act(self, **iops):
        """Act called by ActBase.

        Override in subclass

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        key = self.iops['_key']  # get bag key



@register()
class UpdateMark(BagMark):
    """UpdateMark marks bag in mine for tyme update special need

    """
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, nabe=Nabes.enmark, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb
            _box (str): box name in boxer.  Implicit iop injected by verb
            _key (str): marked bag key. Injected by on verb


        """
        super(UpdateMark, self).__init__(nabe=nabe, **kwa)
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        key = self.iops['_key']  # get bag key
        keys = ("", "boxer", boxer, "box", box, "update", key)
        if keys not in self.hold:
            self.hold[keys] = Bag()  # create bag default value = None



    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']
        key = self.iops['_key']
        keys = ("", "boxer", boxer, "box", box, "update", key)
        # mark bag tyme
        self.hold[keys].value = self.hold[key]._tyme
        return self.hold[keys].value


@register()
class ReupdateMark(BagMark):
    """ReupdateMark marks bag in mine for tyme reupdate special need

    """
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, nabe=Nabes.remark, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb
            _box (str): box name in boxer.  Implicit iop injected by verb
            _key (str): marked bag key. Injected by on verb


        """
        super(ReupdateMark, self).__init__(nabe=nabe, **kwa)
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        key = self.iops['_key']  # get bag key

        keys = ("", "boxer", boxer, "box", box, "reupdate", key)
        if keys not in self.hold:
            self.hold[keys] = Bag()  # create bag default value = None



    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']
        key = self.iops['_key']
        keys = ("", "boxer", boxer, "box", box, "reupdate", key)
        # mark bag tyme
        self.hold[keys].value = self.hold[key]._tyme
        return self.hold[keys].value


@register()
class ChangeMark(BagMark):
    """ChangeMark marks bag in mine for value change special need
    Creates tuple of non-hidden fields in associated bag.

    """
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, nabe=Nabes.enmark, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb
            _box (str): box name in boxer.  Implicit iop injected by verb
            _key (str): marked bag key. Injected by on verb


        """
        super(ChangeMark, self).__init__(nabe=nabe, **kwa)
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        key = self.iops['_key']  # get bag key

        keys = ("", "boxer", boxer, "box", box, "change", key)
        if keys not in self.hold:
            self.hold[keys] = Bag()  # create bag default value = None


    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']
        key = self.iops['_key']
        bag = self.hold[key]
        keys = ("", "boxer", boxer, "box", box, "change", key)
        self.hold[keys].value = bag._astuple()  # bag field value tuple as mark
        return self.hold[keys].value



@register()
class RechangeMark(BagMark):
    """RechangeMark marks bag in mine for value rechange special need
    Creates tuple of non-hidden fields in associated bag.

    """
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, nabe=Nabes.remark, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb
            _box (str): box name in boxer.  Implicit iop injected by verb
            _key (str): marked bag key. Injected by on verb


        """
        super(RechangeMark, self).__init__(nabe=nabe, **kwa)
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        key = self.iops['_key']  # get bag key

        keys = ("", "boxer", boxer, "box", box, "rechange", key)
        if keys not in self.hold:
            self.hold[keys] = Bag()  # create bag default value = None


    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']
        key = self.iops['_key']
        bag = self.hold[key]
        keys = ("", "boxer", boxer, "box", box, "rechange", key)
        self.hold[keys].value = bag._astuple()  # bag field value tuple as mark
        return self.hold[keys].value

