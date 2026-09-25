"""Evaluate trained baseline artifacts without fabricating unavailable metrics."""
from __future__ import annotations

import json
from pathlib import Path

from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

from train_xgboost import train

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "ml" / "artifacts"


def evaluate() -> dict[str, object]:
    result = train()
    model = result["model"]
    features = result["test_features"]
    target = result["test_target"]
    transformed = result["preprocessor"].transform(features)
    predicted = model.predict(transformed)
    probabilities = model.predict_proba(transformed)[:, 1]
    metrics = {
        "status": "evaluated",
        "accuracy": round(float(accuracy_score(target, predicted)), 4),
        "precision": round(float(precision_score(target, predicted, zero_division=0)), 4),
        "recall": round(float(recall_score(target, predicted, zero_division=0)), 4),
        "f1": round(float(f1_score(target, predicted, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(target, probabilities)), 4),
        "confusion_matrix": confusion_matrix(target, predicted).tolist(),
        "patient_level_split": False,
        "note": "Row-level evaluation only because the supplied dataset contains no patient identifier.",
    }
    (ARTIFACT_DIR / "evaluation.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))