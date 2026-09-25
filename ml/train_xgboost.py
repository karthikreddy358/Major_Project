"""Train the single-observation XGBoost baseline on the inspected dataset."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from preprocessing import build_preprocessor, load_maternal_risk

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "raw" / "Maternal_Risk.csv"
ARTIFACT_DIR = ROOT / "ml" / "artifacts"


def train() -> dict[str, object]:
    features, target, quality = load_maternal_risk(DATASET)
    train_features, test_features, train_target, test_target = train_test_split(
        features, target, test_size=0.2, random_state=42, stratify=target,
    )
    preprocessor = build_preprocessor()
    transformed_train = preprocessor.fit_transform(train_features)
    model = XGBClassifier(
        n_estimators=120, max_depth=3, learning_rate=0.08, subsample=0.85,
        colsample_bytree=0.85, objective="binary:logistic", eval_metric="logloss",
        random_state=42, n_jobs=1,
    )
    model.fit(transformed_train, train_target)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, ARTIFACT_DIR / "xgboost_model.pkl")
    joblib.dump(preprocessor, ARTIFACT_DIR / "preprocessor.pkl")
    joblib.dump({0: "low risk", 1: "high risk"}, ARTIFACT_DIR / "label_encoder.pkl")
    metadata = {**quality, "feature_columns": list(features.columns), "target_column": "RiskLevel", "test_rows": len(test_features), "patient_level_split": False, "split_limitation": "No patient identifier exists in the supplied dataset; this is a row-level baseline evaluation."}
    (ARTIFACT_DIR / "training_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return {"model": model, "preprocessor": preprocessor, "test_features": test_features, "test_target": test_target, "metadata": metadata}


if __name__ == "__main__":
    result = train()
    print(json.dumps(result["metadata"], indent=2))