"""
COM object proxy for the ETABS sandbox.

Wraps pywin32 CDispatch objects to block access to internal attributes
(_oleobj_, _ApplyTypes_, etc.) and validates file-path arguments on
methods that interact with the filesystem.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

_UNC_RE = re.compile(r"^(?:\\\\|//|\\\\\?\\UNC\\)", re.ASCII | re.IGNORECASE)


# ---------------------------------------------------------------------------
# Path-validation infrastructure
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _PathRule:
    arg_index: int
    allowed_extensions: frozenset[str]

    def validate(self, args: tuple[Any, ...], method_name: str) -> None:
        if self.arg_index >= len(args):
            raise ValueError(f"'{method_name}' requires a file path as positional argument {self.arg_index}")
        validate_file_path(args[self.arg_index], allowed_extensions=self.allowed_extensions, method_name=method_name)


@dataclass(frozen=True)
class _CompositePathRule:
    dir_arg_index: int
    name_arg_index: int
    allowed_extensions: frozenset[str]

    def validate(self, args: tuple[Any, ...], method_name: str) -> None:
        if self.dir_arg_index >= len(args) or self.name_arg_index >= len(args):
            raise ValueError(
                f"'{method_name}' requires a directory (arg {self.dir_arg_index}) "
                f"and a filename (arg {self.name_arg_index})"
            )
        dir_part = args[self.dir_arg_index]
        name_part = args[self.name_arg_index]
        if not isinstance(dir_part, str) or not isinstance(name_part, str):
            raise ValueError(f"'{method_name}' requires string arguments for directory and filename")
        validate_file_path(
            os.path.join(dir_part, name_part),
            allowed_extensions=self.allowed_extensions,
            method_name=method_name,
        )


# ETABS COM methods that accept a filesystem path.
VALIDATED_COM_METHODS: dict[str, _PathRule | _CompositePathRule] = {
    # SapModel.File sub-object methods
    "OpenFile": _PathRule(arg_index=0, allowed_extensions=frozenset({".edb"})),
    "SaveAs": _PathRule(arg_index=0, allowed_extensions=frozenset({".edb"})),
}

_PROTECTED_DIR_PREFIXES: tuple[str, ...] = (
    os.sep + "windows" + os.sep,
    os.sep + "program files" + os.sep,
    os.sep + "program files (x86)" + os.sep,
    os.sep + "programdata" + os.sep,
    os.sep + "system volume information" + os.sep,
    os.sep + "$recycle.bin" + os.sep,
)


def validate_file_path(
    path: str,
    *,
    allowed_extensions: frozenset[str],
    method_name: str,
) -> None:
    """Raise ``ValueError`` if *path* is unsafe for a COM file operation."""
    if not isinstance(path, str) or not path.strip():
        raise ValueError(f"'{method_name}' requires a non-empty file path string")

    if "\x00" in path:
        raise ValueError(f"Null bytes are not allowed in file paths (blocked in '{method_name}')")

    if _UNC_RE.match(path):
        raise ValueError(f"UNC paths are not allowed (blocked in '{method_name}')")

    if ".." in path.replace("/", os.sep).split(os.sep):
        raise ValueError(f"Path traversal ('..') is not allowed in '{method_name}'")

    try:
        normalized = os.path.normpath(path)
    except (ValueError, OSError) as exc:
        raise ValueError(f"Invalid path passed to '{method_name}': {exc}") from None

    if not os.path.isabs(normalized):
        raise ValueError(f"'{method_name}' requires an absolute file path, got relative path")

    _, ext = os.path.splitext(normalized)
    if ext.lower() not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise ValueError(f"'{method_name}' only allows files with extensions: {allowed}; got '{ext}'")

    _, tail = os.path.splitdrive(normalized.lower())
    tail_with_sep = tail if tail.endswith(os.sep) else tail + os.sep
    for prefix in _PROTECTED_DIR_PREFIXES:
        if tail_with_sep.startswith(prefix):
            raise ValueError(f"'{method_name}' cannot access files in a protected system directory")


class COMProxy:
    """Runtime proxy that restricts attribute access on COM dispatch objects.

    Blocks:
    - Dunder attributes (__class__, __init__, etc.)
    - Single-underscore pywin32 internals (_oleobj_, _ApplyTypes_, etc.)
    - Filesystem methods with unsafe path arguments

    Recursively wraps returned COM sub-objects so that sub-APIs
    (e.g. model.PointObj, model.File) are also protected.
    """

    __slots__ = ("_com_obj",)

    def __init__(self, com_obj: Any) -> None:
        object.__setattr__(self, "_com_obj", com_obj)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(f"access to '{name}' is not allowed on COM objects in the sandbox")
        if name.startswith("_"):
            raise AttributeError(f"access to '{name}' is not allowed on COM objects in the sandbox")

        obj = object.__getattribute__(self, "_com_obj")
        value = getattr(obj, name)

        wrapped = _maybe_wrap(value)
        if wrapped is not value:
            return wrapped

        if callable(value):
            rule = VALIDATED_COM_METHODS.get(name)
            if rule is not None:
                return _ValidatedFileMethodWrapper(value, name, rule)
            return _SafeMethodWrapper(value, name)

        return value

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("cannot set attributes on COM objects in the sandbox")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("cannot delete attributes on COM objects in the sandbox")

    def __repr__(self) -> str:
        return "<sandbox ETABS COM proxy>"


class _SafeMethodWrapper:
    __slots__ = ("_method", "_name")

    def __init__(self, method: Any, name: str) -> None:
        object.__setattr__(self, "_method", method)
        object.__setattr__(self, "_name", name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        for arg in args:
            if isinstance(arg, str) and _UNC_RE.match(arg):
                name = object.__getattribute__(self, "_name")
                raise ValueError(f"UNC paths are not allowed in COM method calls (blocked in '{name}')")
        for val in kwargs.values():
            if isinstance(val, str) and _UNC_RE.match(val):
                name = object.__getattribute__(self, "_name")
                raise ValueError(f"UNC paths are not allowed in COM method calls (blocked in '{name}')")
        method = object.__getattribute__(self, "_method")
        result = method(*args, **kwargs)
        return _maybe_wrap(result)

    def __repr__(self) -> str:
        name = object.__getattribute__(self, "_name")
        return f"<sandbox COM method '{name}'>"


class _ValidatedFileMethodWrapper:
    __slots__ = ("_method", "_name", "_rule")

    def __init__(self, method: Any, name: str, rule: _PathRule | _CompositePathRule) -> None:
        object.__setattr__(self, "_method", method)
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_rule", rule)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        name = object.__getattribute__(self, "_name")
        rule: _PathRule | _CompositePathRule = object.__getattribute__(self, "_rule")

        for arg in args:
            if isinstance(arg, str) and _UNC_RE.match(arg):
                raise ValueError(f"UNC paths are not allowed in COM method calls (blocked in '{name}')")
        for val in kwargs.values():
            if isinstance(val, str) and _UNC_RE.match(val):
                raise ValueError(f"UNC paths are not allowed in COM method calls (blocked in '{name}')")

        rule.validate(args, name)

        method = object.__getattribute__(self, "_method")
        result = method(*args, **kwargs)
        return _maybe_wrap(result)

    def __repr__(self) -> str:
        name = object.__getattribute__(self, "_name")
        return f"<sandbox validated COM method '{name}'>"


def _maybe_wrap(value: Any) -> Any:
    """Wrap COM dispatch objects recursively; pass through primitives."""
    if hasattr(type(value), "_oleobj_") or (isinstance(value, type) and hasattr(value, "_oleobj_")):
        return COMProxy(value)
    if isinstance(value, type):
        return COMProxy(value)
    return value
