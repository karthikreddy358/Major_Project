"""Preprocessing for the observed cross-sectional maternal-risk baseline."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

FEATURE_COLUMNS = ["Age", "SystolicBP", "DiastolicBP", "BS", "BodyTemp", "HeartRate"]
TARGET_COLUMN = "RiskLevel"


def load_maternal_risk(path: str | Path) -> tuple[pd.DataFrame, pd.Series, dict[str, int]]:
    frame = pd.read_csv(path)
    missing_columns = set(FEATURE_COLUMNS + [TARGET_COLUMN]) - set(frame.columns)
    if missing_columns:
        raise ValueError(f"Maternal risk dataset is missing columns: {sorted(missing_columns)}")
    raw_rows = len(frame)
    frame = frame.drop_duplicates().copy()
    frame = frame.dropna(subset=[TARGET_COLUMN])
    features = frame[FEATURE_COLUMNS]
    target = frame[TARGET_COLUMN].str.strip().str.lower().map({"low risk": 0, "high risk": 1})
    if target.isna().any():
        raise ValueError("RiskLevel contains an unsupported label")
    quality = {"raw_rows": raw_rows, "distinct_rows": len(frame), "exact_duplicate_rows": raw_rows - len(frame)}
    return features, target.astype("int64"), quality


def build_preprocessor() -> ColumnTransformer:
    numeric = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    return ColumnTransformer([("numeric", numeric, FEATURE_COLUMNS)], remainder="drop")