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
from ...help.helping import NonStringIterable

from .hiering import Haul


class Need(Mixin):
    """Need is conditional callable class whose callable returns a boolean.
    The calling it evaluates a need expression. May be used as the transition
    condition of a Gact.

    Attributes:
        bags (Haul): in memory data haul shared by boxwork

    Properties:
        terms (tuple[str]): of string need expression terms, each
            to be logically ANDed together to  form evable boolean expression.
        strict (bool): True means use strict Python syntax with no substituion
                       False means use shorthand syntax with substitution

        composed (bool): True means ._expr holds composed .terms
                         False means not yet composed
        compiled (bool): True means ._code holds compiled ._expr
                         False means not yet compiled


    Hidden:
        _terms (tuple[str]): boolean expression terms.
            ensures setter triggers lazy recompile
        _strict (bool): ensures setter triggers lazy recompile
        _expr (None|str): evalable boolean expression. None means recompose from
            .terms
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

    Shorthand syntax notes:
        Use regex to parse out == != <= >= < > not is is not or
        have a strict=True parameters to use explicit python syntax not shorthand

        Not shorthand:
          "H['root.top'].val > 5"

        Shorthand

          "root.top.val > 5"



        But for conditional expression for need an Iterable list of clauses that
        are implicity ANDed together for evaluation.


        ["H['root.top'].val > 5", "H['root.bottom'].val < 6"]

        Implied H[] and where last part is the dom attribute

        ["root.top.val > 5", "root.bottom.val < 6"]

        for needs  "root.top.val" is resolved as H["root.top"].val

        If access the whole dom then end with dot
        "root.top."  This ensures that no matter what always
        has a '.' in the path for the bag itself not a bag attribute.

         "root.top.  or True"
    """


    def __init__(self,  *, terms=None, bags=None, strict=False, **kwa):
        """Initialization method for instance.

        Parameters:
            terms (NonStringIterable[str]): of string need expression terms, each
                to be logically ANDed together to  form evable boolean expression.
            bags (None|Haul): in memory data haul shared by boxwork
            strict (bool): True means use strict Python syntax with no substituion
                           False means use shorthand syntax with substitution

        """
        super(Need, self).__init__(**kwa)
        self.terms = terms
        self.bags = bags if bags is not None else Haul()
        self.strict = True if strict else False


    def __call__(self):
        """Make Need instance a callable object."""
        if not self.compiled:  # not yet compiled so lazy
            self.compile()  # first time only recompile forces recompose
        B = self.bags  # ensure B in in locals() for eval
        return eval(self._code)


    @property
    def terms(self):
        """Property getter for ._terms. Returns tuple

        Returns:
            terms (tuple[str]): of string need expression terms, each to be
                logically ANDed together to form evable boolean expression.
        """
        return self._terms


    @terms.setter
    def terms(self, terms=None):
        """Property setter for ._terms

        Parameters:
            terms (NonStringIterable[str]): of string need expression terms, each
                to be logically ANDed together to  form evable boolean expression.
        """
        self._terms = tuple((term for term in terms)) if terms is not None else ()
        self._expr = None  # force lazy recomposition
        self._code = None  # force lazy recompilation


    @property
    def strict(self):
        """Property getter for ._strict.

        Returns:
            strict (bool): True means use strict Python syntax with no substituion
                           False means use shorthand syntax with substitution
        """
        return self._strict


    @strict.setter
    def strict(self, strict=False):
        """Property setter for ._strict

        Parameters:
            strict (bool): True means use strict Python syntax with no substituion
                           False means use shorthand syntax with substitution
        """
        self._strict = True if strict else False
        self._expr = None  # force lazy recomposition
        self._code = None  # force lazy recompilation


    @property
    def composed(self):
        """Property composed

        Returns:
            composed (bool): True means ._expr holds composed .terms
                             False means not yet composed
        """
        return True if self._expr is not None else False

    @property
    def compiled(self):
        """Property compiled

        Returns:
            compiled (bool): True means ._code holds compiled ._expr
                             False means not yet compiled
        """
        return True if self._code is not None else False


    def compose(self):
        """Compile .terms into evalable boolean expression str .expr to be
        compiled into ._code code object.
        """
        if not self.terms:  # default is to eval to True
            self._expr = 'True'  # default need to fix
            return


    def compile(self):
        """Compile evable boolean expression str ._expr into compiled code
        object ._code to be evaluated at run time.
        Because code objects are not pickleable the compilation must happen
        at prep (enter) time not init time.
        """
        if not self.composed:
            self.compose()

        self._code = compile(self._expr, '<string>', 'eval')

