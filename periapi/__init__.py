#!/usr/bin/env python3
"""
Periscope API for the masses
"""

from ._version import __version__
from .api import PeriAPI
from .autocap import AutoCap

__all__ = ['PeriAPI', 'AutoCap', '__version__']
