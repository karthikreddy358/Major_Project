"""Report source CSV shape and quality without modifying raw files."""
from __future__ import annotations

import csv
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def analyze(path: Path) -> dict[str, object]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    columns = list(rows[0]) if rows else []
    duplicate_count = len(rows) - len({tuple(row.get(column, "") for column in columns) for row in rows})
    missing_cells = sum(
        1 for row in rows for column in columns if not str(row.get(column, "")).strip()
    )
    return {
        "file": path.name,
        "rows": len(rows),
        "columns": len(columns),
        "missing_cells": missing_cells,
        "exact_duplicate_rows": duplicate_count,
        "columns_list": columns,
    }


if __name__ == "__main__":
    for csv_path in sorted(RAW_DIR.glob("*.csv")):
        print(analyze(csv_path))
