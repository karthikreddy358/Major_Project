"""Create explicitly synthetic continuity sequences for demos and sequence research.

This intentionally does not join or relabel source rows as real patients.
"""
from __future__ import annotations

import csv
from pathlib import Path

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "synthetic" / "longitudinal_demo.csv"


def build_rows() -> list[dict[str, object]]:
    journeys = {
        "M001": [22, 24, 23],
        "M002": [28, 36, 49],
        "M003": [22, 37, 58, 76, 84],
        "M004": [31, 34, 33, 35],
    }
    rows = []
    for mother_code, scores in journeys.items():
        for sequence, score in enumerate(scores, start=1):
            rows.append({
                "mother_code": mother_code,
                "sequence_number": sequence,
                "care_stage": "antenatal" if sequence <= 4 else "postnatal",
                "demo_risk_score": score / 100,
                "is_synthetic": True,
            })
    return rows


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic sequence records to {OUTPUT}")
