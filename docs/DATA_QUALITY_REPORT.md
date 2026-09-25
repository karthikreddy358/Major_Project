# Data Quality Report

Analysis date: 2026-09-20

## Summary

| File | Rows | Columns | Missing cells | Exact duplicate rows | Identifier/date fields |
|---|---:|---:|---:|---:|---|
| `Maternal_Risk.csv` | 808 | 7 | 0 | 463 | None observed |
| `Dataset - Updated.csv` | 1,205 | 12 | 53 | 18 | None observed |
| `Final.csv` | 136,136 | 95 | 0 | 0 | None observed |

Missing-cell total for `Dataset - Updated.csv` includes missing target values and feature values. Blank categorical/numeric cells were counted as missing; no imputation has been performed.

## Cleaning Plan

1. Preserve each supplied CSV as a raw source and assign a dataset name; do not silently overwrite source content.
2. Normalize column names only in processed copies, retaining a source-column mapping.
3. Remove or explicitly flag exact duplicate rows according to the training experiment; report both raw and distinct counts.
4. Treat missing predictors with a fitted training-only imputation pipeline.
5. Exclude rows with missing labels from supervised training unless a documented label policy is adopted.
6. Split at patient level only when a genuine patient identifier exists. These files do not provide one, so this limitation must be reported for baseline experiments.
7. Generate synthetic sequences separately, with explicit provenance and no claim that they are linked source patients.

## Target Review

- `Maternal_Risk.csv`: binary label `RiskLevel`; values are `low risk` and `high risk`.
- `Dataset - Updated.csv`: binary label `Risk Level`; 18 labels are missing.
- `Final.csv`: no single risk label. Candidate outcome-like columns require a documented research question and data dictionary before use.

## Limitations

The attachments do not include dataset documentation, sampling information, clinical definitions, collection dates, or provenance. Observed field names alone are not sufficient to infer clinical meaning, validity, or generalizability. The application must present these datasets as research inputs, not clinically validated evidence.