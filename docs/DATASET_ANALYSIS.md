# Dataset Analysis

Analysis date: 2026-09-20

## Important Linkage Finding

The supplied files do not contain a reliable shared patient identifier, visit identifier, event date, or timestamp. Rows must not be joined across files as though they belong to the same mother. The application will therefore keep source datasets separate and use a clearly labelled synthetic longitudinal demonstration dataset for timeline and sequential-model workflows.

No claim is made here about whether the records are real, anonymized, or synthetic because the attachments did not include source documentation. The provenance recorded below is limited to the supplied filenames and observed schemas.

## Dataset Summary

| Dataset | Source | Rows | Columns | Target | Useful Features | Limitations | Longitudinal Capability | Usage in Project |
|---|---|---:|---:|---|---|---|---|---|
| `Maternal_Risk.csv` | Supplied attachment: `archive (1)`; upstream source not documented | 808 | 7 | `RiskLevel` (`low risk`, `high risk`) | Age, systolic/diastolic BP, blood sugar, body temperature, heart rate | 463 exact duplicate rows; no BMI, pregnancy history, dates, IDs, delivery, newborn, or postnatal fields | None; cross-sectional rows | Source for a compact maternal-risk baseline after duplicate handling is documented | XGBoost baseline candidate and demo feature mapping |
| `Dataset - Updated.csv` | Supplied attachment: `archive (2)`; upstream source not documented | 1,205 | 12 | `Risk Level` (`Low`, `High`); 18 missing target values | Age, BP, blood sugar, body temperature, BMI, previous complications, diabetes flags, mental-health flag, heart rate | 18 exact duplicate rows; 35 missing feature values across several columns; no dates, IDs, delivery, newborn, or postnatal fields | None; cross-sectional rows | Candidate maternal/pregnancy baseline dataset with explicit missing-value handling | XGBoost baseline candidate; not joined to the other datasets |
| `Final.csv` | Supplied attachment: `archive (3)`; upstream source not documented | 136,136 | 95 | No explicit overall risk target; observed outcome-like fields include `Preg_Complication`, `ChildAlive`, `Birth_Size`, and `Anemia_level` | Maternal demographics, antenatal visit count, delivery mode/place, birth weight/size, maternal/child health and care indicators, household context | Wide survey snapshot; no patient ID, dates, visit-level measurements, or explicit prediction target; fields are encoded and require a data dictionary | None; cross-sectional/retrospective survey records | Separate maternal-child context and outcome-analysis source; not a direct timeline source | Feature exploration, outcome definition study, and schema mapping only until a defensible target is selected |

## Quality Findings

### `Maternal_Risk.csv`

- Missing values: none observed in the 808 rows.
- Exact duplicate rows: 463, leaving 345 distinct complete rows.
- Numeric fields: `Age`, `SystolicBP`, `DiastolicBP`, `BS`, `BodyTemp`, `HeartRate`.
- Categorical field: `RiskLevel`.
- Candidate identifier/date columns: none.
- Class distribution: 478 `low risk`, 330 `high risk`.

### `Dataset - Updated.csv`

- Missing values: `Systolic BP` 5, `Diastolic` 4, `BS` 2, `BMI` 18, `Previous Complications` 2, `Preexisting Diabetes` 2, `Heart Rate` 2, and `Risk Level` 18.
- Exact duplicate rows: 18.
- Numeric fields: all observed predictors are numeric-coded.
- Categorical field: `Risk Level`.
- Candidate identifier/date columns: none.
- Non-missing class distribution: 713 `Low`, 474 `High`.

### `Final.csv`

- Missing values: none observed in the 136,136 rows.
- Exact duplicate rows: none observed.
- The 95 columns are numeric-coded except `State`; the file has no explicit ID or date column.
- `Antenatal_visits` is a count, not a visit-level event key. `ChildAge_mnths` is an age measure, not a record timestamp.
- The file includes both maternal and child/delivery variables in the same survey row, so it represents a linked snapshot within the source survey, not a longitudinal event history suitable for the requested timeline.

## Proposed Unified Internal Representation

The application database will use the following domain entities:

```text
Mother
  - sourced_record_ref (nullable; never treated as a cross-file join key)
  - demographic/context fields supported by an imported record
  - AntenatalVisit[]
  - Delivery (optional)
  - Newborn[] (optional)
  - PostnatalVisit[]
  - RiskPrediction[]
```

Source mapping:

- `Maternal_Risk.csv`: antenatal-style maternal observation features and its supplied risk label, stored as source observations.
- `Dataset - Updated.csv`: maternal/pregnancy observation features and its supplied risk label, stored as a separate source dataset.
- `Final.csv`: maternal-child survey snapshot fields, mapped only where definitions are sufficiently clear; encoded fields retain their source meaning and are not silently renamed into clinical measurements.
- Synthetic longitudinal data: generated separately from compatible observed feature distributions, marked `is_synthetic = true`, and used only for the continuity timeline, deterministic demo inference, and sequential demonstration when no real sequences exist.

## Target and Modelling Decision

`Maternal_Risk.csv` and `Dataset - Updated.csv` have explicit classification labels and are suitable candidates for a single-observation baseline, subject to deduplication, missing-value policy, and a documented train/test split. `Final.csv` has no single authoritative risk target; a target must be selected and justified before training, and no model metric will be displayed until evaluation is actually run.

Because no supplied file contains repeated observations for identifiable patients, an LSTM trained on these files would not represent real longitudinal trajectories. The project will not make that claim. A separate synthetic sequence generator will create research/demo sequences with provenance labels for the sequential workflow.

## Safe Data Policy

- Do not concatenate the three files by row position or by matching demographic values.
- Do not create fake IDs and describe them as original patient links.
- Preserve raw files unchanged under `data/raw/` once project scaffolding begins.
- Record every cleaning and transformation in `docs/DATA_QUALITY_REPORT.md`.
- Keep research/demo predictions visibly distinct from real model inference.