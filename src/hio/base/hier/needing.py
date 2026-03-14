# -*- encoding: utf-8 -*-
"""
hio.base.hier.needing Module

Provides hierarchical action support

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections.abc import Callable, Iterable
from collections import namedtuple
from types import CodeType

from ... import hioing
from ...hioing import Mixin, HierError
from .holding import Hold


class Need(Mixin):
    """Need is conditional callable class whose callable returns a boolean.
    The calling it evaluates a need expression. May be used as the transition
    condition of a Gact.

    Attributes:
        hold (Hold): data shared by boxwork

    Properties:
        expr (str): evaluable boolean expression.
        compiled (bool): True means ._code holds compiled ._expr; False means not yet compiled


    Hidden:
        _expr (str): evaluable boolean expression.
        _code (None|CodeType): compiled evaluable boolean expression .expr; None means not yet compiled from .expr



    Compilation Notes:
        The need returned by an ``on()`` call keeps the string expression because
        compiled code objects are not pickleable. In multiprocessing, the child
        process recompiles the expression from the string form. Keeping the string
        representation also helps debugging and introspection.

    Expression Syntax Notes:
        ``H`` is a local reference to ``self.hold`` during evaluation. Need
        expressions can use dotted hold paths directly, for example,
        ``H.root_dog.value``. This is equivalent to either
        ``self.hold["root_dog"].value`` or ``self.hold[("root", "dog")].value``.

        The expression ``H.root_dog.value > 5`` compiles and evaluates directly
        as long as ``H`` is present in locals and references a ``Hold`` instance.
        No substitution shorthand is required. Hierarchy in ``.hold`` uses
        underscore-separated keys, so Box/Boxer/Actor names may not contain
        ``_`` (enforced by the ``Renam`` regex).

    """


    def __init__(self,  *, expr='True', hold=None, **kwa):
        """Initialization method for instance.

        Parameters:
            expr (str): evaluable boolean expression.
                        if empty or None then use default = 'True'
            hold (None|Hold): data shared by boxwork
        """
        super(Need, self).__init__(**kwa)
        self.expr = expr
        self.hold = hold if hold is not None else Hold()
        self.compile()  # compile at init time so now it will compile


    def __call__(self, **iops):
        """Make Need instance a callable object.

        Parameters:
            iops (dict):  run time input output parameters for need.
                          Usually provided when need is Act deed.

        """
        if not self.compiled:  # not yet compiled so lazy
            self.compile()  # first time only recompile
        H = self.hold  # ensure H is in locals() for eval
        return eval(self._code)


    @property
    def expr(self):
        """Property getter for ._expr

        Returns:
            expr (str): evaluable boolean expression.
        """
        return self._expr


    @expr.setter
    def expr(self, expr):
        """Property setter for ._expr

        Parameters:
            expr (str): evaluable boolean expression.
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
        """Compile evaluable boolean expression str ._expr into compiled code
        object ._code to be evaluated at run time.
        Because code objects are not pickleable the compilation must happen
        at prep (enter) time not init time.
        """
        self._code = compile(self.expr, '<string>', 'eval')
