# -*- encoding: utf-8 -*-
"""hio.core.hier.acting Module

Provides hierarchical action support

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections.abc import Callable
from collections import namedtuple

from ... import hioing
from ...hioing import Mixin, HierError
from ...help import Mine, Renam
from .hiering import Context, ActBase, register
from .needing import Need
from .bagging import Bag
from . import boxing




@register()
class Act(ActBase):
    """Act is generic subclass of ActBase meant for do verb acts.

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

    Inherited Attributes:
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork

    Inherited Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act
        context (str): action context for .act

    Hidden
        ._name (str|None): unique name of instance
        ._iopts (dict): input-output-paramters for .act
        ._context (str): action context for .act

    """
    Index = 0  # naming index for default names of this subclasses instances
    #Names = () tuple of aliases for this subclass created by @register

    @classmethod
    def _reregister(cls):
        """Reregisters cls after clear.
        Need to override in each subclass with super to reregister the class hierarchy
        """
        super(Act, cls)._reregister()
        Act.registerbyname()
        for name in Act.Names:
            Act.registerbyname(name)


    def __init__(self, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            context (str|None): action context for .act. Default is "enter"
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:


        """
        super(Act, self).__init__(**kwa)



    def act(self, **iops):
        """Act called by Actor. Should override in subclass."""
        return None


@register()
class Tract(ActBase):
    """Tract (transit act) is subclass of ActBase whose .act evaluates conditional
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
        context (str): action context for .act

    Inherited Attributes:
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork

    Attributes:
        dest (Box): destination Box for this transition.
        need (Need): transition condition to be evaluated

    Hidden
        ._name (str|None): unique name of instance
        ._iopts (dict): input-output-paramters for .act
        ._context (str): action context for .act

    """
    Index = 0  # naming index for default names of this subclasses instances
    #Names = () tuple of aliases for this subclass created by @register

    @classmethod
    def _reregister(cls):
        """Reregisters cls after clear.
        Need to override in each subclass with super to reregister the class hierarchy
        """
        super(Tract, cls)._reregister()
        Tract.registerbyname()
        for name in Tract.Names:
            Tract.registerbyname(name)


    def __init__(self, dest=None, need=None, *, context=Context.transit, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            context (str): action context for .act
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
        super(Tract, self).__init__(context=context, **kwa)
        self.dest = dest if dest is not None else 'next'  # default is next
        self.need = need if need is not None else Need()  # default need evals to True



    def act(self, **iops):
        """Act called by Actor. Should override in subclass."""
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
        context (str): action context for .act

    Inherited Attributes:
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork

    Attributes:

    Used iops:
        _boxer (str):  boxer name


    Hidden
        ._name (str|None): unique name of instance
        ._iopts (dict): input-output-paramters for .act
        ._context (str): action context for .act

    """
    Index = 0  # naming index for default names of this subclasses instances
    #Names = () tuple of aliases for this subclass created by @register

    @classmethod
    def _reregister(cls):
        """Reregisters cls after clear.
        Need to override in each subclass with super to reregister the class hierarchy
        """
        super(EndAct, cls)._reregister()
        EndAct.registerbyname()
        for name in EndAct.Names:
            EndAct.registerbyname(name)


    def __init__(self, context=Context.enter, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            context (str): action context for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb (do etc)


        """
        super(EndAct, self).__init__(context=context, **kwa)

        try:
            boxer = self.iops['_boxer']  # get boxer name
        except KeyError as ex:
            raise HierError(f"Missing iops for '{self.name}' instance "
                            f"of Act self.__class__.__name__") from ex


        keys = ("", "boxer", boxer, "end")  # _boxer_boxername_end
        if keys not in self.mine:
            self.mine[keys] = Bag()  # create bag at end default value = None


    def act(self, **iops):
        """Act called by Actor. Should override in subclass."""
        boxer = self.iops['_boxer']  # get boxer name
        keys = ("", "boxer", boxer, "end")
        self.mine[keys].value = True
