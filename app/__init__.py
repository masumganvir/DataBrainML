"""
DataWise AI — Enterprise AutoML & MLOps Platform
Root Application Package extending backend/app.
"""

from __future__ import annotations

import os
import sys

_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.abspath(os.path.join(_current_dir, ".."))
_backend_dir = os.path.join(_root_dir, "backend")
_backend_app_dir = os.path.join(_backend_dir, "app")

if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

if os.path.exists(_backend_app_dir) and _backend_app_dir not in __path__:
    __path__.append(_backend_app_dir)
