"""Validation and data-freezing utilities for file I/O."""

from __future__ import annotations

import os
from pathlib import Path
from types import MappingProxyType
from typing import Any

from pydantic import ValidationError

from etabs_mcp.file_io.models import FlatOutput, MultiSheetOutput
from etabs_mcp.file_io.path_validator import FileIOError


def validate_return_value(path: Path, value: Any) -> None:
    ext = path.suffix.lower()
    if isinstance(value, (list, tuple)):
        try:
            FlatOutput.model_validate(value)
        except ValidationError as exc:
            raise FileIOError("INVALID_RETURN_SHAPE", _format_errors(exc)) from None
    elif isinstance(value, dict):
        if ext == ".csv":
            raise FileIOError(
                "SHAPE_EXTENSION_MISMATCH",
                "Multi-sheet data cannot be written to a CSV file; use .xlsx or provide a flat list of rows",
            )
        try:
            MultiSheetOutput.model_validate(value)
        except ValidationError as exc:
            raise FileIOError("INVALID_RETURN_SHAPE", _format_errors(exc)) from None
    else:
        raise FileIOError(
            "INVALID_RETURN_SHAPE",
            "Return value must be a list of lists (flat) or a dict of sheets (multi-sheet)",
        )


def _format_errors(exc: ValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return str(exc)
    parts = []
    for err in errors:
        loc = " -> ".join(str(part) for part in err.get("loc", ()))
        msg = err.get("msg", "")
        parts.append(f"{loc}: {msg}" if loc else msg)
    return "; ".join(parts)


def validate_args_allowed_dirs(allowed_dirs: list[str] | None) -> list[Path]:
    if not allowed_dirs:
        return []
    result: list[Path] = []
    for dir_str in allowed_dirs:
        expanded = Path(dir_str).expanduser()
        absolute = expanded.resolve(strict=False)
        normalized_original = Path(os.path.normpath(absolute))
        try:
            resolved = absolute.resolve(strict=True)
            normalized_resolved = Path(os.path.normpath(resolved))
            result.append(normalized_resolved)
        except OSError:
            result.append(normalized_original)
    return result


def deep_freeze(data: Any) -> Any:
    if data is None or isinstance(data, (str, int, float, bool)):
        return data
    if isinstance(data, (list, tuple)):
        return tuple(deep_freeze(item) for item in data)
    if isinstance(data, dict):
        return MappingProxyType({k: deep_freeze(v) for k, v in data.items()})
    return data
