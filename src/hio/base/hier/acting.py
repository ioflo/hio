# -*- encoding: utf-8 -*-
"""
hio.core.hier.acting Module

Provides hierarchical action support

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections.abc import Callable
from collections import namedtuple

from ... import hioing
from ...hioing import Mixin, HierError
from .hiering import Reat, Haul, ActBase, register




@register
class Act(ActBase):
    """Act is generic subclass of ActBase meant for do verb acts.

    Inherited Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Names (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference

    Overridden Class Attributes
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.



    Inherited Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act

    Hidden
        ._name (str|None): unique name of instance
        ._iopts (dict): input-output-paramters for .act

    """
    Index = 0  # naming index for default names of this subclasses instances

    @classmethod
    def _reregister(cls):
        """Reregisters cls after clear.
        Need to override in each subclass with super to reregister the class hierarchy
        """
        super(Act, cls)._reregister()
        register(Act)


    def __init__(self, dest=None, need=None, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.

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
        super(Act, self).__init__(**kwa)
        self.dest = dest
        self.need = need



    def act(self, **iops):
        """Act called by Actor. Should override in subclass."""

        return None  # conditional not met


@register
class Tract(ActBase):
    """Tract (transit act) is subclass of ActBase whose .act evaluates conditional
    need expression to determine if a transition condition is satified for
    transition to its destination box.

    Inherited Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Names (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference

    Overridden Class Attributes
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.



    Inherited Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act

    Hidden
        ._name (str|None): unique name of instance
        ._iopts (dict): input-output-paramters for .act

    """
    Index = 0  # naming index for default names of this subclasses instances

    @classmethod
    def _reregister(cls):
        """Reregisters cls after clear.
        Need to override in each subclass with super to reregister the class hierarchy
        """
        super(Tract, cls)._reregister()
        register(Tract)


    def __init__(self, dest=None, need=None, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.

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
        super(Tract, self).__init__(**kwa)
        self.dest = dest
        self.need = need



    def act(self, **iops):
        """Act called by Actor. Should override in subclass."""

        return None  # conditional not met

