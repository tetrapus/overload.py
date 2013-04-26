import inspect
from inspect import Parameter, Signature
import functools
from collections import OrderedDict

class OverloadedFunction(object):
    
    def __doc__():
        def fget(self):
            return self._doc + ("\n\n".join("%s%s%s" % (f.__qualname__, 
                                                        inspect.signature(f), 
                                                       ("\n    %s"%f.__doc__) if hasattr(f, "__doc__") and f.__doc__ else "") for f in self._functions))
        def fset(self, x):
            if x != self._functions[0].__doc__:
                self._doc = "%s: %s\n\n" % (self._functions[0].__qualname__, x)
        return locals()
    __doc__ = property(**__doc__())
    _doc = ""

    def __new__(cls, funct):
        if funct.__class__ == OverloadedFunction:
            return funct
        self = super().__new__(cls)
        self._functions = [funct]
        return functools.wraps(funct)(self)

    def addfunct(self, funct):
        self._functions.append(funct)

    def bindto(self, instance):
        for i in self._functions:
            i.__self__ = instance

    def _typematch(self, arguments, parameters):
        for name, param in parameters.items():
            if param.annotation is not Parameter.empty:
                test = param.annotation
                if type(test) == type:
                    if not isinstance(arguments[name], test):
                        return False
                else:
                    if not test(arg):
                        return False
        return True

    def __call__(self, *x, **y):
        # This is a little fucked, but here it goes.
        for funct in self._functions:
            signature = inspect.signature(funct)
            try:
                bound = signature.bind(funct.__self__, *x, **y)
            except TypeError:
                continue
            if self._typematch(bound.arguments, signature.parameters):
                rtype = signature.return_annotation
                rval = funct(*bound.args, **bound.kwargs)
                if rtype is not Signature.empty:
                    if type(rtype) == type:
                        if isinstance(rval, rtype):
                            return rval
                    else:
                        if rtype(rval):
                            return rval
                else:
                    return rval
                raise TypeError("Type returned by function does not pass type check.")
        raise TypeError("No defined function matches provided arguments.")

    def __getitem__(self, key):
        functs = [i for i in self._functions if issubclass(key, inspect.signature(i).return_annotation)]
        if not functs:
            raise TypeError("No function signatures match requested return type.")
        filtered = OverloadedFunction(functs.pop(0))
        for i in functs:
            filtered.addfunct(i)
        return filtered

class OverloadedNamespace(OrderedDict):
    def __setitem__(self, name, value):
        if callable(value):
            if name in self:
                # Overload
                super().__setitem__(name, OverloadedFunction(self[name]))
                self[name].addfunct(value)
            elif inspect.getfullargspec(value).annotations:
                super().__setitem__(name, OverloadedFunction(value))
            else:
                super().__setitem__(name, value)
        else:
            super().__setitem__(name, value)


class Overload(type):
    """
    A metaclass for specifying an overloaded function.
    """

    @classmethod
    def __prepare__(cls, name, bases):
        return OverloadedNamespace()

    def __new__(cls, name, bases, clsdict):
        return super().__new__(cls, name, bases, dict(clsdict))

class Overloaded(metaclass=Overload):
    def __init__(self):
        for var in dir(self):
            if isinstance(getattr(self, var), OverloadedFunction):
                getattr(self, var).bindto(self)
