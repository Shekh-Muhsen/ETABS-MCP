"""
ETABS multi-instance connection support.

Public API
----------
``ETABSInstance``
    Frozen dataclass representing a running ETABS instance with fields
    ``alias``, ``pid``, ``file_path``, ``version``.

``InstanceRegistry``
    Lightweight PID-to-alias map.  Assigns stable, monotonic aliases
    (``etabs1``, ``etabs2``, …) to ETABS processes.  Aliases are never
    reused within a server session.

``connect_and_run(fn, pid, timeout) -> Any``
    Spin a short-lived STA thread, attach to the ETABS COM object,
    execute ``fn(model)`` where ``model`` is ``SapModel``, and return
    the result.  Raises ``TimeoutError`` if the call exceeds *timeout*
    seconds.

Connection approach
-------------------
ETABS exposes its API through a Helper COM object.  The correct pattern is::

    helper = win32com.client.Dispatch("ETABSv1.Helper")
    etabs_obj = helper.GetObject("CSI.ETABS.API.ETABSObject")
    model = etabs_obj.SapModel

``_get_etabs_model()`` tries the Helper first (including version-specific
helpers for ETABS 20/21/22), then falls back to ``GetActiveObject``.
"""

from __future__ import annotations

import ctypes
import logging
import sys
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar

from etabs_mcp.version import check_version_warning

logger = logging.getLogger(__name__)

if sys.platform == "win32":
    import comtypes.client  # type: ignore[import-untyped]
    import pythoncom  # type: ignore[import-untyped]


# ---------------------------------------------------------------------------
# Process enumeration helpers
# ---------------------------------------------------------------------------

_ETABS_EXE_NAMES = frozenset({
    "etabs.exe",
    "etabs64.exe",
})


def _find_etabs_pids() -> list[int]:
    """Return PIDs of running ETABS processes via Windows Toolhelp32 snapshot."""
    if sys.platform != "win32":
        return []

    TH32CS_SNAPPROCESS = 0x00000002

    class PROCESSENTRY32(ctypes.Structure):
        _fields_ = [
            ("dwSize", ctypes.c_ulong),
            ("cntUsage", ctypes.c_ulong),
            ("th32ProcessID", ctypes.c_ulong),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", ctypes.c_ulong),
            ("cntThreads", ctypes.c_ulong),
            ("th32ParentProcessID", ctypes.c_ulong),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", ctypes.c_ulong),
            ("szExeFile", ctypes.c_char * 260),
        ]

    kernel32 = ctypes.windll.kernel32
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        return []

    pids: list[int] = []
    try:
        entry = PROCESSENTRY32()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
        if kernel32.Process32First(snapshot, ctypes.byref(entry)):
            while True:
                name = entry.szExeFile.decode("utf-8", errors="ignore").lower()
                if name in _ETABS_EXE_NAMES or name.startswith("etabs"):
                    pids.append(entry.th32ProcessID)
                if not kernel32.Process32Next(snapshot, ctypes.byref(entry)):
                    break
    finally:
        kernel32.CloseHandle(snapshot)

    return pids


# ---------------------------------------------------------------------------
# COM connection helper
# ---------------------------------------------------------------------------

# ProgIDs tried in priority order.  Version-specific helpers are tried first
# because they connect more reliably than the generic "ETABSv1.Helper" on some
# ETABS installations.
_HELPER_PROGIDS = [
    "ETABSv1.Helper",
    "ETABSv22.Helper",
    "ETABSv21.Helper",
    "ETABSv20.Helper",
    "ETABSv19.Helper",
    "ETABSv18.Helper",
    "ETABSv17.Helper",
    "ETABS2016.Helper",
    "ETABS2015.Helper",
]

_ETABS_API_PROGID = "CSI.ETABS.API.ETABSObject"


def _get_etabs_model() -> Any:
    """Return the ETABS ``SapModel`` COM object for the running instance.

    Tries each Helper ProgID in ``_HELPER_PROGIDS`` first, then falls back to
    ``GetActiveObject`` directly.  Raises ``OSError`` when no ETABS instance
    can be found.

    Must be called from an STA thread that has already called
    ``pythoncom.CoInitialize()``.
    """
    last_exc: Exception | None = None

    for progid in _HELPER_PROGIDS:
        try:
            helper = comtypes.client.CreateObject(progid)
            etabs_obj = helper.GetObject(_ETABS_API_PROGID)
            if etabs_obj is None:
                last_exc = OSError(f"{progid}.GetObject returned None — OAPI may not be enabled")
                continue
            return etabs_obj.SapModel
        except Exception as exc:
            last_exc = exc

    raise OSError(
        "Could not connect to a running ETABS instance. "
        "Make sure ETABS is open with a model loaded. "
        f"Last error: {last_exc}"
    )


# ---------------------------------------------------------------------------
# ETABSInstance — typed result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ETABSInstance:
    """A running ETABS instance discovered via COM."""

    alias: str
    pid: int
    file_path: str
    version: str
    warning: str | None = field(default=None)

    def asdict(self) -> dict[str, object]:
        d: dict[str, object] = {
            "alias": self.alias,
            "pid": self.pid,
            "file_path": self.file_path,
            "version": self.version,
        }
        if self.warning is not None:
            d["warning"] = self.warning
        return d


# ---------------------------------------------------------------------------
# InstanceRegistry — PID → alias map
# ---------------------------------------------------------------------------


class InstanceRegistry:
    """Lightweight map from process IDs to stable session aliases.

    Aliases are monotonic (``etabs1``, ``etabs2``, …) and are never
    reused within a server session, even if the original process closes.
    """

    def __init__(self) -> None:
        self._pid_to_alias: dict[int, str] = {}
        self._next_num = 1
        self._lock = threading.Lock()

    def assign_alias(self, pid: int) -> str:
        with self._lock:
            if pid not in self._pid_to_alias:
                self._pid_to_alias[pid] = f"etabs{self._next_num}"
                self._next_num += 1
            return self._pid_to_alias[pid]

    def resolve(self, alias: str) -> int | None:
        with self._lock:
            for pid, a in self._pid_to_alias.items():
                if a == alias:
                    return pid
            return None

    # ------------------------------------------------------------------
    # Instance discovery
    # ------------------------------------------------------------------

    def get_active_instances(self) -> list[ETABSInstance]:
        """Return all running ETABS instances discoverable via COM.

        Attempts ``GetActiveObject("CSI.ETABS.API.ETABSObject")`` for each
        ETABS process found.  Falls back gracefully when no ETABS is running.

        Returns ``[]`` on non-Windows platforms.
        """
        if sys.platform != "win32":
            return []

        result: list[ETABSInstance] = []
        error: list[Exception] = []

        def _scan() -> None:
            try:
                pythoncom.CoInitialize()
                try:
                    try:
                        model = _get_etabs_model()
                    except OSError:
                        # No running ETABS instance — normal when ETABS is closed
                        return

                    # File path
                    try:
                        file_path: str = model.GetModelFilename(True)
                    except Exception:
                        file_path = ""

                    # Version — GetVersion() returns [VersionString, BuildNum, ret]
                    try:
                        ver_result = model.GetVersion()
                        if isinstance(ver_result, (list, tuple)):
                            version = str(ver_result[0]) if ver_result else "unknown"
                        else:
                            version = str(ver_result)
                    except Exception:
                        version = "unknown"

                    # PID — scan process list for ETABS executables
                    etabs_pids = _find_etabs_pids()
                    pid = etabs_pids[0] if etabs_pids else 0

                    alias = self.assign_alias(pid)
                    result.append(
                        ETABSInstance(
                            alias=alias,
                            pid=pid,
                            file_path=file_path,
                            version=version,
                            warning=check_version_warning(version),
                        )
                    )
                finally:
                    pythoncom.CoUninitialize()
            except Exception as exc:
                error.append(exc)

        t = threading.Thread(target=_scan, daemon=True)
        t.start()
        t.join(timeout=30.0)

        if t.is_alive():
            logger.warning("ETABS COM scan timed out after 30s")

        if error:
            raise error[0]
        return result


# ---------------------------------------------------------------------------
# connect_and_run — per-execution STA thread
# ---------------------------------------------------------------------------

T = TypeVar("T")


def connect_and_run(
    fn: Callable[[Any], T],
    pid: int = 0,
    timeout: float = 120.0,
) -> T:
    """Attach to the running ETABS instance and run *fn(model)*.

    Spins a short-lived daemon STA thread, calls ``_get_etabs_model()``
    (Helper-based, with GetActiveObject fallback), executes ``fn(model)``
    where ``model`` is ``SapModel``, and returns the result.

    Raises ``TimeoutError`` on timeout (daemon thread is abandoned).
    Raises any exception thrown by ``fn``.
    """
    result_box: list[Any] = [None]
    done = threading.Event()

    def _worker() -> None:
        try:
            pythoncom.CoInitialize()
            try:
                model = _get_etabs_model()
                result_box[0] = fn(model)
            finally:
                pythoncom.CoUninitialize()
        except Exception as exc:
            result_box[0] = exc
        finally:
            done.set()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()

    if not done.wait(timeout=timeout):
        raise TimeoutError(f"COM call did not complete within {timeout}s")

    value = result_box[0]
    if isinstance(value, Exception):
        raise value
    return value
