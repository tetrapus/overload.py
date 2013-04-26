overload.py
===========

Module for overloading functions (with type checking) in python 3.3+

To use, inherit from Overloaded. Function annotations provide type checking.

If an annotation is a class, it checks against type, else it executes the function as a check.

You can select a certain return type by indexing against a class, but note this does not work for validation functions.

