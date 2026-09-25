from datetime import datetime, timezone

from models.entities import AntenatalVisit, Mother, RiskFactor, RiskPrediction


def calculate_demo_prediction(mother: Mother) -> dict:
    visits = sorted(mother.antenatal_visits, key=lambda visit: visit.visit_date)
    latest = visits[-1] if visits else None
    score = 0.18 + min(len(visits) * 0.04, 0.16)
    factors: list[dict] = []
    if latest:
        if latest.systolic_bp and latest.systolic_bp >= 140:
            score += 0.24
            factors.append({"feature_name": "systolic_bp", "feature_value": latest.systolic_bp, "contribution": 0.24, "direction": "increased"})
        if latest.blood_sugar and latest.blood_sugar >= 9:
            score += 0.18
            factors.append({"feature_name": "blood_sugar", "feature_value": latest.blood_sugar, "contribution": 0.18, "direction": "increased"})
        if latest.previous_complications:
            score += 0.16
            factors.append({"feature_name": "previous_complications", "feature_value": True, "contribution": 0.16, "direction": "increased"})
    score = round(min(score, 0.95), 2)
    level = "HIGH" if score >= 0.7 else "MODERATE" if score >= 0.4 else "LOW"
    if not factors:
        factors.append({"feature_name": "care_history_length", "feature_value": len(visits), "contribution": round(len(visits) * 0.04, 2), "direction": "increased"})
    return {"risk_score": score, "risk_level": level, "model_name": "DEMO_DETERMINISTIC", "factors": factors, "is_demo_prediction": True, "timestamp": datetime.now(timezone.utc)}


def create_prediction(mother: Mother, trigger_visit_id: int | None = None) -> RiskPrediction:
    result = calculate_demo_prediction(mother)
    prediction = RiskPrediction(mother_id=mother.id, trigger_visit_id=trigger_visit_id, risk_score=result["risk_score"], risk_level=result["risk_level"], model_name=result["model_name"], is_demo_prediction=True, prediction_timestamp=result["timestamp"])
    prediction.factors = [RiskFactor(**factor) for factor in result["factors"]]
    return prediction