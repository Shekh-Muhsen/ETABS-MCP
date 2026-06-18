"""Pydantic models for file I/O return-value validation."""

from __future__ import annotations

import unicodedata
from typing import Annotated, Any

from pydantic import BaseModel, RootModel, field_validator, model_validator

from etabs_mcp.file_io.const import (
    MAX_CELL_SIZE,
    MAX_OUTPUT_COLUMNS,
    MAX_OUTPUT_ROWS,
    MAX_OUTPUT_SHEETS,
    MAX_SHEET_NAME_LENGTH,
)

CellValue = str | int | float | bool | None

_FORMULA_PREFIXES = ("=", "+", "-", "@")
_LINE_SEPARATORS = frozenset("\n\r\x0b\x0c  ")


def _check_formula_injection(v: str) -> None:
    normalized = unicodedata.normalize("NFKC", v)
    if any(ch in _LINE_SEPARATORS for ch in normalized):
        raise ValueError("Cell values cannot contain line separators to prevent CSV row splitting")
    idx = 0
    for ch in normalized:
        if ch.isspace() or unicodedata.category(ch) == "Cf":
            idx += 1
        else:
            break
    if normalized[idx: idx + 1] in _FORMULA_PREFIXES:
        raise ValueError("Cell values cannot start with '=', '+', '-', or '@' to prevent formula injection")


def check_cell(v: Any, reject_formula: bool = True) -> CellValue:
    if isinstance(v, (bool, int, float)):
        return v
    if isinstance(v, str):
        if len(v) > MAX_CELL_SIZE:
            raise ValueError(f"String too long: {len(v)}; limit {MAX_CELL_SIZE}")
        if reject_formula:
            _check_formula_injection(v)
        return v
    if v is None:
        return v
    raise ValueError(f"Cell value must be a JSON primitive, got {type(v).__name__}")


Row = Annotated[list[CellValue], "A row of cell values"]


class FlatOutput(RootModel[list[Row]]):
    @model_validator(mode="before")
    @classmethod
    def _coerce_sequences(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            return [list(row) if isinstance(row, (list, tuple)) else row for row in v]
        return v

    @model_validator(mode="after")
    def _check_limits(self) -> FlatOutput:
        rows = self.root
        if len(rows) > MAX_OUTPUT_ROWS + 1:
            raise ValueError(f"Too many rows: {len(rows)}; limit {MAX_OUTPUT_ROWS}")
        for row in rows:
            if len(row) > MAX_OUTPUT_COLUMNS:
                raise ValueError(f"Too many columns: {len(row)}; limit {MAX_OUTPUT_COLUMNS}")
            for cell in row:
                check_cell(cell)
        return self


class SheetData(BaseModel):
    columns: list[CellValue]
    rows: list[Row]

    @model_validator(mode="before")
    @classmethod
    def _coerce_sequences(cls, v: Any) -> Any:
        if isinstance(v, dict):
            data = dict(v)
            if "columns" in data and isinstance(data["columns"], tuple):
                data["columns"] = list(data["columns"])
            if "rows" in data and isinstance(data["rows"], (list, tuple)):
                data["rows"] = [list(r) if isinstance(r, (list, tuple)) else r for r in data["rows"]]
            return data
        return v

    @model_validator(mode="after")
    def _check_limits(self) -> SheetData:
        all_rows = [self.columns, *self.rows]
        for row in all_rows:
            if len(row) > MAX_OUTPUT_COLUMNS:
                raise ValueError(f"Too many columns: {len(row)}; limit {MAX_OUTPUT_COLUMNS}")
            for cell in row:
                check_cell(cell)
        if len(self.rows) > MAX_OUTPUT_ROWS:
            raise ValueError(f"Too many rows: {len(self.rows)}; limit {MAX_OUTPUT_ROWS}")
        return self


class MultiSheetOutput(RootModel[dict[str, SheetData]]):
    @field_validator("root", mode="before")
    @classmethod
    def _check_sheet_count(cls, v: Any) -> Any:
        if isinstance(v, dict) and len(v) > MAX_OUTPUT_SHEETS:
            raise ValueError(f"Too many sheets: {len(v)}; limit {MAX_OUTPUT_SHEETS}")
        return v

    @model_validator(mode="after")
    def _check_sheet_names(self) -> MultiSheetOutput:
        for name in self.root:
            if len(name) > MAX_SHEET_NAME_LENGTH:
                raise ValueError(f"Sheet name '{name}' exceeds {MAX_SHEET_NAME_LENGTH} characters")
        return self
