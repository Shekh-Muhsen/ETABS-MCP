"""Shared path validator for file I/O operations."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal
from urllib.parse import unquote, urlparse

from etabs_mcp.file_io.const import ALLOWED_FILE_EXTENSIONS

_UNC_RE = re.compile(r"^(?:\\\\|//)", re.ASCII)


class FileIOError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def parse_roots_to_dirs(roots: list) -> list[Path]:
    dirs: list[Path] = []
    for root in roots:
        uri: str = root.uri if hasattr(root, "uri") else str(root)
        parsed = urlparse(uri)
        if parsed.scheme != "file":
            continue
        local = unquote(parsed.path)
        if local.startswith("/") and len(local) > 2 and local[2] == ":":
            local = local[1:]
        dirs.append(Path(local))
    return dirs


def validate_io_path(
    raw_path: str,
    allowed_dirs: list[Path],
    *,
    mode: Literal["read", "write"],
) -> Path:
    """Validate *raw_path* for a file I/O operation and return the resolved path."""
    if not allowed_dirs:
        raise FileIOError(
            "NO_ROOTS",
            "No allowed directories configured. Please update your extension settings.",
        )

    if "\x00" in raw_path:
        raise FileIOError("UNSUPPORTED_FORMAT", "Null bytes are not allowed in file paths")

    try:
        resolved = Path(raw_path).resolve()
    except (OSError, ValueError) as exc:
        raise FileIOError("UNSUPPORTED_FORMAT", f"Invalid path: {exc}") from None

    resolved_str = str(resolved)
    if _UNC_RE.match(resolved_str):
        raise FileIOError("UNC_REJECTED", "Network paths (UNC) are not allowed")

    inside_any = False
    for root_dir in allowed_dirs:
        try:
            resolved.relative_to(root_dir.resolve())
            inside_any = True
            break
        except ValueError:
            continue
    if not inside_any:
        raise FileIOError(
            "PATH_OUTSIDE_ROOTS",
            f"Path is outside all allowed directories: {resolved}",
        )

    ext = resolved.suffix.lower()
    if ext not in ALLOWED_FILE_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_FILE_EXTENSIONS))
        raise FileIOError("UNSUPPORTED_FORMAT", f"Extension '{ext}' is not supported. Allowed: {allowed}")

    if mode == "read":
        if not resolved.is_file():
            raise FileIOError("FILE_NOT_FOUND", f"File does not exist: {resolved}")
    else:
        if not resolved.parent.is_dir():
            raise FileIOError("PARENT_DIR_MISSING", f"Parent directory does not exist: {resolved.parent}")

    return resolved
