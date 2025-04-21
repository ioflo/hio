# -*- encoding: utf-8 -*-
"""
hio.core.hier.needing Module

Provides hierarchical action support

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections.abc import Callable, Iterable
from collections import namedtuple
from types import CodeType

from ... import hioing
from ...hioing import Mixin, HierError
from ...help import Mine


class Need(Mixin):
    """Need is conditional callable class whose callable returns a boolean.
    The calling it evaluates a need expression. May be used as the transition
    condition of a Gact.

    Attributes:
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork

    Properties:
        expr (str): evalable boolean expression.
        compiled (bool): True means ._code holds compiled ._expr
                         False means not yet compiled


    Hidden:
        _expr (str): evalable boolean expression.
        _code (None|CodeType): compiled evalable boolean expression .expr
            None means not yet compiled from .expr



    Compilation Notes:
        c = compile("True", '<string>', 'eval')
        c
        <code object <module> at 0x1042f2250, file "<string>", line 1>
        type(c)
        <class 'code'>
        import types
        isinstance(c, types.CodeType)
        True

        import pickle
        s = pickle.dumps(c)
        builtins.TypeError: cannot pickle code objects

        eval(c)
        True

        So  the need returned by an on() call must keep around the string
        representation for multiprocessing because the code object itself is not
        pickleable and must be recompiled inside the child process.
        Also having the string rep around can be helpful in debugging if define
        __repr__ and __str__ for need objects.

    Expr syntax notes:
        M (Mine) memory (non-durable) and D (Dock) durable support attribute syntax
        with locally scope variables M ref for mine and D ref for dock.


        so need syntax does not heed to "quote" paths keys into the bags
        containers Mine dict subclasses with attribute support.

        M.root_dog.value  is equivalent to self.mine["root_dog"].value or
                                           self.mine[("root", "dog")].value

        So need term  "M.root_dog.value > 5" should compile directly and eval
        as long as M is in the locals() and M is a Mine instance.

        Likewise for
        D.root_dog.value where D is a Dock and root_dog is a key in the Dock.

        So no need to do substitutions or shorthand
        The hierarchy in the .mine and .dock is indicated by '_' separated keys
        The Box Boxer Actor names are forbidden from having '_" as an element
        with Renam regex test.

    """


    def __init__(self,  *, expr='True', mine=None, dock=None, **kwa):
        """Initialization method for instance.

        Parameters:
            expr (str): evalable boolean expression.
                        if empty or None then use default = 'True'
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork


        """
        super(Need, self).__init__(**kwa)
        self.expr = expr
        self.mine = mine if mine is not None else Mine()
        self.dock = dock   # stub fix later when have Dock class
        self.compile()  # compile at init time so now it will compile


    def __call__(self, **iops):
        """Make Need instance a callable object.

        Parameters:
            iops (dict):  run time input output parms for need.
                          Usually provided when need is Act deed.

        """
        if not self.compiled:  # not yet compiled so lazy
            self.compile()  # first time only recompile
        M = self.mine  # ensure M is in locals() for eval
        D = self.dock  # ensure D is in locals() for eval
        return eval(self._code)


    @property
    def expr(self):
        """Property getter for ._expr

        Returns:
            expr (str): evalable boolean expression.
        """
        return self._expr


    @expr.setter
    def expr(self, expr):
        """Property setter for ._expr

        Parameters:
            expr (str): evalable boolean expression.
        """
        self._expr = expr if expr else 'True'
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
        self._code = compile(self.expr, '<string>', 'eval')

