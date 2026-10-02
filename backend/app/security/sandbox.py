"""
DataWise AI — Python AST Code Sandbox & Security Inspector

Safely inspects and validates generated Python code:
  1. AST tree traversal to disallow dangerous imports and calls
  2. Whitelist of allowed scientific and data science packages
  3. Execution inside a restricted namespace without filesystem/network access
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

import pandas as pd


ALLOWED_MODULES: Set[str] = {
    "numpy", "np",
    "pandas", "pd",
    "sklearn",
    "scipy",
    "math",
    "datetime",
    "re",
    "typing",
    "collections",
    "itertools",
    "copy",
}

BLOCKED_MODULES: Set[str] = {
    "os", "sys", "subprocess", "socket", "http", "urllib", "requests", "shutil",
    "importlib", "pty", "posix", "ctypes", "pickle", "shelve", "builtins",
    "pathlib", "tempfile", "io", "tarfile", "zipfile"
}

BLOCKED_CALLS: Set[str] = {
    "eval", "exec", "__import__", "open", "compile", "globals", "locals",
    "breakpoint", "help", "exit", "quit"
}


@dataclass
class CodeValidationResult:
    is_safe: bool
    violations: List[str]


class SecurityASTVisitor(ast.NodeVisitor):
    def __init__(self):
        self.violations: List[str] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            base_module = alias.name.split(".")[0]
            if base_module in BLOCKED_MODULES:
                self.violations.append(f"Blocked import: '{alias.name}'")
            elif base_module not in ALLOWED_MODULES:
                self.violations.append(f"Unwhitelisted import: '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base_module = node.module.split(".")[0]
            if base_module in BLOCKED_MODULES:
                self.violations.append(f"Blocked from-import: '{node.module}'")
            elif base_module not in ALLOWED_MODULES:
                self.violations.append(f"Unwhitelisted from-import: '{node.module}'")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in BLOCKED_CALLS:
                self.violations.append(f"Blocked function call: '{node.func.id}()'")
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in ("system", "popen", "spawn", "execve", "eval"):
                self.violations.append(f"Blocked method call: '.{node.func.attr}()'")
        self.generic_visit(node)


def validate_python_code(code_str: str) -> CodeValidationResult:
    """Validates python code against strict safety rules before execution."""
    if not code_str or not code_str.strip():
        return CodeValidationResult(is_safe=True, violations=[])

    try:
        tree = ast.parse(code_str)
    except SyntaxError as err:
        return CodeValidationResult(is_safe=False, violations=[f"SyntaxError: {err}"])

    visitor = SecurityASTVisitor()
    visitor.visit(tree)

    return CodeValidationResult(
        is_safe=len(visitor.violations) == 0,
        violations=visitor.violations,
    )


def safe_execute_transform(code_str: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Executes a user or agent transformation function on a copy of the dataframe
    inside a restricted execution environment.
    Expects the code to define a function `def transform(df): ...` returning a DataFrame.
    """
    validation = validate_python_code(code_str)
    if not validation.is_safe:
        raise ValueError(f"Code validation failed: {'; '.join(validation.violations)}")

    import numpy as np
    import sklearn

    def safe_import(name, *args, **kwargs):
        base = name.split(".")[0]
        if base not in ALLOWED_MODULES:
            raise ImportError(f"Import of module '{name}' is disallowed in sandbox.")
        return __import__(name, *args, **kwargs)

    safe_builtins = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "dict": dict,
        "list": list,
        "set": set,
        "tuple": tuple,
        "float": float,
        "int": int,
        "str": str,
        "bool": bool,
        "isinstance": isinstance,
        "print": lambda *args, **kwargs: None,  # no-op print
        "__import__": safe_import,
    }

    restricted_globals: Dict[str, Any] = {
        "__builtins__": safe_builtins,
        "pd": pd,
        "pandas": pd,
        "np": np,
        "numpy": np,
        "sklearn": sklearn,
    }

    local_namespace: Dict[str, Any] = {}
    exec(code_str, restricted_globals, local_namespace)

    if "transform" not in local_namespace or not callable(local_namespace["transform"]):
        raise ValueError("Provided code must define a callable function named 'transform(df)'")

    df_copy = df.copy(deep=True)
    result = local_namespace["transform"](df_copy)

    if not isinstance(result, pd.DataFrame):
        raise TypeError(f"transform(df) must return a pandas.DataFrame, got {type(result).__name__}")

    return result
