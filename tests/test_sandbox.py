"""Unit tests for the ETABS MCP sandbox."""

import pytest

from etabs_mcp.sandbox.ast import capture_last_expr, validate_code
from etabs_mcp.sandbox.executor import Executor


class MockModel:
    """Minimal mock for SapModel used in sandbox tests."""

    class _PointObj:
        def Count(self):
            return 3

        def GetNameList(self):
            return 0, 3, ["1", "2", "3"]

    PointObj = _PointObj()

    def SetPresentUnits(self, units: int) -> int:
        return 0

    def GetModelIsLocked(self) -> bool:
        return False


# ── AST validation tests ──────────────────────────────────────────


def test_import_blocked():
    result = validate_code("import os")
    assert not result.is_valid
    assert any("import" in e.message for e in result.errors)


def test_dunder_blocked():
    result = validate_code("model.__class__")
    assert not result.is_valid


def test_dir_blocked():
    result = validate_code("dir(model)")
    assert not result.is_valid


def test_getattr_blocked():
    result = validate_code("getattr(model, 'x')")
    assert not result.is_valid


def test_valid_code():
    result = validate_code("x = 1 + 2")
    assert result.is_valid


# ── Executor tests ────────────────────────────────────────────────


def test_execute_simple():
    exc = Executor()
    mock = MockModel()
    r = exc.execute("result = 1 + 2", mock)
    assert r.success
    assert r.result == 3


def test_execute_model_access():
    exc = Executor()
    mock = MockModel()
    r = exc.execute("model.SetPresentUnits(6)", mock)
    assert r.success


def test_execute_last_expr():
    exc = Executor()
    mock = MockModel()
    r = exc.execute("1 + 1", mock)
    assert r.success
    assert r.result == 2


def test_execute_import_blocked():
    exc = Executor()
    mock = MockModel()
    r = exc.execute("import os", mock)
    assert not r.success
    assert r.error is not None


def test_execute_print_captured():
    exc = Executor()
    mock = MockModel()
    r = exc.execute("print('hello etabs')", mock)
    assert r.success
    assert "hello etabs" in r.stdout


def test_capture_last_expr():
    source, captured = capture_last_expr("x = 1\nx + 1")
    assert captured
    assert "__result__" in source


def test_input_data_injected():
    exc = Executor()
    mock = MockModel()
    r = exc.execute("result = input_data[0]", mock, input_data=["a", "b"])
    assert r.success
    assert r.result == "a"
