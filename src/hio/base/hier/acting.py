# -*- encoding: utf-8 -*-
"""hio.core.hier.acting Module

Provides hierarchical action support

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections.abc import Callable, Iterable
from collections import namedtuple

from ... import hioing
from ...hioing import Mixin, HierError
from ...help import Mine, Renam
from .hiering import Nabes, ActBase, register
from .needing import Need
from .bagging import Bag
from . import boxing

from ...help import  NonStringIterable


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
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork

    Attributes:


    Properties:
        deed (Callable|str): action to be called with .iops as parameters else
                executable set of statements with M and D as locals
        compiled (bool): True means ._code holds compiled .deed
                         False means not yet compiled

    Hidden:
        _name (str|None): unique name of instance
        _iopts (dict): input-output-paramters for .act
        _nabe (str): action nabe (context) for .act
        _deed (Callable|str):  action to be called with .iops as parameters else
                executable set of statements with M and D as locals
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
        self.iops.update(M=self.mine, D=self.dock)  # inject .mine and .dock
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
        M = self.mine  # ensure M is in locals() for exec
        D = self.dock  # ensure D is in locals() for exec
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
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork

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
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork

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
        if keys not in self.mine:
            self.mine[keys] = Bag()  # create bag at end default value = None


    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        keys = ("", "boxer", boxer, "end")
        self.mine[keys].value = True


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
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork


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
        self.iops.update(M=self.mine, D=self.dock)  # inject .mine and .dock
        self.lhs = lhs
        self.rhs = rhs
        if isinstance(self.rhs, str):
            self.compile()
        key, field = self.lhs
        if key not in self.mine:
            raise HierError(f"Missing mine bag at key='{key}'")
        if field not in self.mine[key]:
            raise HierError(f"Missing field='{field}' in mine bag at key='{key}'")


    def act(self, **iops):  # passed in by call
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms for deed when deed is callable.
        """
        key, field = self.lhs

        if self.rhs is None:
            self.mine[key][field] = self.rhs

        elif callable(self.rhs):
            self.mine[key][field] = self.rhs(**iops)

        else:
            if not self.compiled:  # not yet compiled so lazy
                self.compile()  # first time only recompile to ._code
            M = self.mine  # ensure M is in locals() for exec
            D = self.dock  # ensure D is in locals() for exec
            # note iops already in locals() for exec
            self.mine[key][field] = eval(self._code)

        return self.mine[key][field]


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
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork

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
        if keys not in self.mine:
            self.mine[keys] = Bag()  # create bag default value = None


    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        keys = ("", "boxer", boxer, "box", box, "lapse")
        # mark box tyme via bag._now tyme
        self.mine[keys].value = self.mine[keys]._now  # _now tyme of mark bag
        return self.mine[keys].value


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
        if keys not in self.mine:
            self.mine[keys] = Bag()  # create bag default value = None


    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        keys = ("", "boxer", boxer, "box", box, "relapse")
        # mark box tyme via bag._now tyme
        self.mine[keys].value = self.mine[keys]._now  # _now tyme of mark bag
        return self.mine[keys].value


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
        if keys not in self.mine:
            self.mine[keys] = Bag()  # create bag default value = None



    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        keys = ("", "boxer", boxer, "box", box, "count")
        bag = self.mine[keys]  # count bag
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
        if keys not in self.mine:
            self.mine[keys] = Bag()  # create bag default value = None


    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        keys = ("", "boxer", boxer, "box", box, "count")
        self.mine[keys].value = None  # reset count to None
        return self.mine[keys].value




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
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork

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

        if key not in self.mine:
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
        if keys not in self.mine:
            self.mine[keys] = Bag()  # create bag default value = None



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
        self.mine[keys].value = self.mine[key]._tyme
        return self.mine[keys].value


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
        if keys not in self.mine:
            self.mine[keys] = Bag()  # create bag default value = None



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
        self.mine[keys].value = self.mine[key]._tyme
        return self.mine[keys].value


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
        if keys not in self.mine:
            self.mine[keys] = Bag()  # create bag default value = None


    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']
        key = self.iops['_key']
        bag = self.mine[key]
        keys = ("", "boxer", boxer, "box", box, "change", key)
        self.mine[keys].value = bag._astuple()  # bag field value tuple as mark
        return self.mine[keys].value



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
        if keys not in self.mine:
            self.mine[keys] = Bag()  # create bag default value = None


    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']
        key = self.iops['_key']
        bag = self.mine[key]
        keys = ("", "boxer", boxer, "box", box, "rechange", key)
        self.mine[keys].value = bag._astuple()  # bag field value tuple as mark
        return self.mine[keys].value

