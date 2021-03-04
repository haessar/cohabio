"""
Each sub-module should contain functions "add_X" and "del_X", where X is the name of the sub-module.
e.g. "add_london", "del_london" in london.py
"""
import os
import pkgutil

__all__ = list(module for _, module, _ in pkgutil.iter_modules([os.path.dirname(__file__)]))
