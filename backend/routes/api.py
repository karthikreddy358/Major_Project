from datetime import datetime, timezone
import json
from pathlib import Path

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy import desc, or_
from werkzeug.security import check_password_hash

from extensions import db
from models.entities import Alert, AntenatalVisit, Delivery, Mother, Newborn, PostnatalVisit, RiskPrediction, User, parse_date
from services.prediction import create_prediction

api = Blueprint("api", __name__, url_prefix="/api")


def mother_payload(mother: Mother) -> dict:
    latest = max(mother.predictions, key=lambda item: (item.prediction_timestamp, item.id), default=None)
    return {"id": mother.id, "mother_code": mother.mother_code, "name": mother.name, "age": mother.age, "blood_group": mother.blood_group, "source_type": mother.source_type, "antenatal_visit_count": len(mother.antenatal_visits), "current_prediction": prediction_payload(latest) if latest else None}


def prediction_payload(prediction: RiskPrediction | None) -> dict | None:
    if prediction is None:
        return None
    return {"id": prediction.id, "risk_score": prediction.risk_score, "risk_level": prediction.risk_level, "model_name": prediction.model_name, "is_demo_prediction": prediction.is_demo_prediction, "timestamp": prediction.prediction_timestamp.isoformat(), "factors": [{"feature": item.feature_name, "value": item.feature_value, "contribution": item.contribution, "direction": item.direction} for item in prediction.factors]}


@api.post("/auth/login")
def login():
    body = request.get_json(silent=True) or {}
    user = User.query.filter_by(email=body.get("email", "").strip().lower()).first()
    if not user or not check_password_hash(user.password_hash, body.get("password", "")):
        return jsonify({"message": "Invalid email or password"}), 401
    return jsonify({"access_token": create_access_token(identity=str(user.id)), "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}})


@api.get("/auth/me")
@jwt_required()
def current_user():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify({"message": "User not found"}), 404
    return jsonify({"id": user.id, "name": user.name, "email": user.email, "role": user.role})


@api.get("/mothers")
@jwt_required()
def list_mothers():
    query = Mother.query.order_by(Mother.mother_code)
    search = request.args.get("search", "").strip()
    if search:
        query = query.filter(or_(Mother.mother_code.ilike(f"%{search}%"), Mother.name.ilike(f"%{search}%")))
    return jsonify({"items": [mother_payload(mother) for mother in query.all()]})


@api.get("/dashboard/stats")
@jwt_required()
def dashboard_stats():
    mothers = Mother.query.all()
    current_predictions = [max(mother.predictions, key=lambda item: (item.prediction_timestamp, item.id), default=None) for mother in mothers]
    current_predictions = [item for item in current_predictions if item]
    return jsonify({
        "total_mothers": len(mothers),
        "active_pregnancies": sum(1 for mother in mothers if mother.antenatal_visits and not mother.deliveries),
        "high_risk_cases": sum(1 for item in current_predictions if item.risk_level == "HIGH"),
        "moderate_risk_cases": sum(1 for item in current_predictions if item.risk_level == "MODERATE"),
        "low_risk_cases": sum(1 for item in current_predictions if item.risk_level == "LOW"),
        "newborns_monitored": sum(len(mother.newborns) for mother in mothers),
    })


@api.post("/mothers")
@jwt_required()
def create_mother():
    body = request.get_json(silent=True) or {}
    if not body.get("mother_code") or not body.get("name"):
        return jsonify({"message": "mother_code and name are required"}), 422
    if Mother.query.filter_by(mother_code=body["mother_code"]).first():
        return jsonify({"message": "mother_code already exists"}), 409
    mother = Mother(mother_code=body["mother_code"], name=body["name"], age=body.get("age"), blood_group=body.get("blood_group"), source_type=body.get("source_type", "synthetic"))
    db.session.add(mother)
    db.session.commit()
    return jsonify(mother_payload(mother)), 201


@api.get("/mothers/<int:mother_id>")
@jwt_required()
def get_mother(mother_id: int):
    mother = db.session.get(Mother, mother_id)
    if not mother:
        return jsonify({"message": "Patient not found"}), 404
    return jsonify(mother_payload(mother))


@api.get("/mothers/<int:mother_id>/timeline")
@jwt_required()
def timeline(mother_id: int):
    mother = db.session.get(Mother, mother_id)
    if not mother:
        return jsonify({"message": "Patient not found"}), 404
    events = [{"type": "antenatal", "date": visit.visit_date.isoformat(), "data": {"id": visit.id, "gestational_age": visit.gestational_age, "systolic_bp": visit.systolic_bp, "diastolic_bp": visit.diastolic_bp, "blood_sugar": visit.blood_sugar, "hemoglobin": visit.hemoglobin}, "prediction": prediction_payload(next((item for item in mother.predictions if item.trigger_visit_id == visit.id), None))} for visit in mother.antenatal_visits]
    events.extend({"type": "delivery", "date": delivery.delivery_date.isoformat(), "data": {"id": delivery.id, "gestational_age": delivery.gestational_age, "delivery_mode": delivery.delivery_mode, "delivery_place": delivery.delivery_place, "complications": delivery.complications}, "prediction": None} for delivery in mother.deliveries)
    events.extend({"type": "newborn", "date": newborn.date_of_birth.isoformat(), "data": {"id": newborn.id, "newborn_code": newborn.newborn_code, "sex": newborn.sex, "birth_weight": newborn.birth_weight, "birth_length": newborn.birth_length, "nicu_required": newborn.nicu_required, "status": newborn.status}, "prediction": None} for newborn in mother.newborns)
    events.extend({"type": "postnatal", "date": visit.visit_date.isoformat(), "data": {"id": visit.id, "days_after_delivery": visit.days_after_delivery, "maternal_bp": visit.maternal_bp, "newborn_weight": visit.newborn_weight, "feeding_status": visit.feeding_status, "newborn_condition": visit.newborn_condition}, "prediction": None} for visit in mother.postnatal_visits)
    events.sort(key=lambda item: item["date"])
    return jsonify({"mother": mother_payload(mother), "events": events})


def add_prediction_for(mother: Mother):
    prediction = create_prediction(mother)
    db.session.add(prediction)
    db.session.flush()
    if prediction.risk_level == "HIGH":
        db.session.add(Alert(mother_id=mother.id, prediction_id=prediction.id, risk_level=prediction.risk_level, risk_score=prediction.risk_score))


@api.post("/mothers/<int:mother_id>/delivery")
@jwt_required()
def add_delivery(mother_id: int):
    mother = db.session.get(Mother, mother_id)
    if not mother:
        return jsonify({"message": "Patient not found"}), 404
    body = request.get_json(silent=True) or {}
    try:
        delivery = Delivery(mother_id=mother_id, delivery_date=parse_date(body.get("delivery_date")), gestational_age=body.get("gestational_age"), delivery_mode=body.get("delivery_mode"), delivery_place=body.get("delivery_place"), complications=body.get("complications"), notes=body.get("notes"))
    except (TypeError, ValueError):
        return jsonify({"message": "Invalid delivery date or numeric value"}), 422
    db.session.add(delivery)
    add_prediction_for(mother)
    db.session.commit()
    return jsonify({"delivery_id": delivery.id, "message": "Delivery record saved"}), 201


@api.post("/mothers/<int:mother_id>/newborn")
@jwt_required()
def add_newborn(mother_id: int):
    mother = db.session.get(Mother, mother_id)
    if not mother:
        return jsonify({"message": "Patient not found"}), 404
    body = request.get_json(silent=True) or {}
    if not body.get("newborn_code"):
        return jsonify({"message": "newborn_code is required"}), 422
    if Newborn.query.filter_by(newborn_code=body["newborn_code"]).first():
        return jsonify({"message": "newborn_code already exists"}), 409
    try:
        newborn = Newborn(mother_id=mother_id, newborn_code=body["newborn_code"], date_of_birth=parse_date(body.get("date_of_birth")), sex=body.get("sex"), birth_weight=body.get("birth_weight"), birth_length=body.get("birth_length"), apgar_score=body.get("apgar_score"), gestational_age=body.get("gestational_age"), nicu_required=body.get("nicu_required"), complications=body.get("complications"), status=body.get("status"))
    except (TypeError, ValueError):
        return jsonify({"message": "Invalid newborn date or numeric value"}), 422
    db.session.add(newborn)
    add_prediction_for(mother)
    db.session.commit()
    return jsonify({"newborn_id": newborn.id, "message": "Newborn record saved"}), 201


@api.post("/mothers/<int:mother_id>/postnatal-visits")
@jwt_required()
def add_postnatal_visit(mother_id: int):
    mother = db.session.get(Mother, mother_id)
    if not mother:
        return jsonify({"message": "Patient not found"}), 404
    body = request.get_json(silent=True) or {}
    newborn_id = body.get("newborn_id")
    if newborn_id and not any(newborn.id == newborn_id for newborn in mother.newborns):
        return jsonify({"message": "Newborn does not belong to this mother"}), 422
    try:
        visit = PostnatalVisit(mother_id=mother_id, newborn_id=newborn_id, visit_date=parse_date(body.get("visit_date")), days_after_delivery=body.get("days_after_delivery"), maternal_bp=body.get("maternal_bp"), maternal_hemoglobin=body.get("maternal_hemoglobin"), newborn_weight=body.get("newborn_weight"), feeding_status=body.get("feeding_status"), newborn_condition=body.get("newborn_condition"), complications=body.get("complications"), notes=body.get("notes"))
    except (TypeError, ValueError):
        return jsonify({"message": "Invalid postnatal date or numeric value"}), 422
    db.session.add(visit)
    add_prediction_for(mother)
    db.session.commit()
    return jsonify({"postnatal_visit_id": visit.id, "message": "Postnatal record saved"}), 201


@api.post("/mothers/<int:mother_id>/antenatal-visits")
@jwt_required()
def add_antenatal_visit(mother_id: int):
    mother = db.session.get(Mother, mother_id)
    if not mother:
        return jsonify({"message": "Patient not found"}), 404
    body = request.get_json(silent=True) or {}
    try:
        visit = AntenatalVisit(mother_id=mother_id, visit_date=parse_date(body.get("visit_date")), gestational_age=body.get("gestational_age"), systolic_bp=body.get("systolic_bp"), diastolic_bp=body.get("diastolic_bp"), blood_sugar=body.get("blood_sugar"), body_temperature=body.get("body_temperature"), heart_rate=body.get("heart_rate"), hemoglobin=body.get("hemoglobin"), previous_complications=body.get("previous_complications"), notes=body.get("notes"))
    except (TypeError, ValueError):
        return jsonify({"message": "Invalid visit date or numeric value"}), 422
    db.session.add(visit)
    db.session.flush()
    prediction = create_prediction(mother, visit.id)
    db.session.add(prediction)
    db.session.flush()
    if prediction.risk_level == "HIGH":
        db.session.add(Alert(mother_id=mother.id, prediction_id=prediction.id, risk_level=prediction.risk_level, risk_score=prediction.risk_score))
    db.session.commit()
    return jsonify({"visit_id": visit.id, "prediction": prediction_payload(prediction), "message": "Visit saved and demo risk analysis completed"}), 201


@api.post("/mothers/<int:mother_id>/predict")
@jwt_required()
def predict(mother_id: int):
    mother = db.session.get(Mother, mother_id)
    if not mother:
        return jsonify({"message": "Patient not found"}), 404
    prediction = create_prediction(mother)
    db.session.add(prediction)
    db.session.flush()
    if prediction.risk_level == "HIGH":
        db.session.add(Alert(mother_id=mother.id, prediction_id=prediction.id, risk_level=prediction.risk_level, risk_score=prediction.risk_score))
    db.session.commit()
    return jsonify(prediction_payload(prediction)), 201


@api.get("/mothers/<int:mother_id>/predictions")
@jwt_required()
def predictions(mother_id: int):
    if not db.session.get(Mother, mother_id):
        return jsonify({"message": "Patient not found"}), 404
    return jsonify({"items": [prediction_payload(item) for item in RiskPrediction.query.filter_by(mother_id=mother_id).order_by(desc(RiskPrediction.prediction_timestamp)).all()]})


@api.get("/alerts")
@jwt_required()
def alerts():
    return jsonify({"items": [{"id": item.id, "mother_id": item.mother_id, "risk_level": item.risk_level, "risk_score": item.risk_score, "status": item.status, "created_at": item.created_at.isoformat()} for item in Alert.query.order_by(desc(Alert.created_at)).all()]})


@api.get("/model/performance")
@jwt_required()
def model_performance():
    evaluation_path = Path(__file__).resolve().parents[2] / "ml" / "artifacts" / "evaluation.json"
    lstm_path = Path(__file__).resolve().parents[2] / "ml" / "artifacts" / "lstm_evaluation.json"
    sequential = {"name": "LSTM", "status": "Pending Evaluation"}
    if lstm_path.exists():
        sequential = {"name": "LSTM", **json.loads(lstm_path.read_text(encoding="utf-8"))}
    if not evaluation_path.exists():
        return jsonify({"baseline": {"name": "XGBoost", "status": "Pending Evaluation"}, "sequential": sequential})
    metrics = json.loads(evaluation_path.read_text(encoding="utf-8"))
    return jsonify({"baseline": {"name": "XGBoost", **metrics}, "sequential": sequential})


@api.put("/alerts/<int:alert_id>/status")
@jwt_required()
def update_alert(alert_id: int):
    alert = db.session.get(Alert, alert_id)
    if not alert:
        return jsonify({"message": "Alert not found"}), 404
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in {"NEW", "REVIEWED", "RESOLVED"}:
        return jsonify({"message": "Status must be NEW, REVIEWED, or RESOLVED"}), 422
    alert.status = status
    alert.reviewed_at = datetime.now(timezone.utc) if status != "NEW" else None
    db.session.commit()
    return jsonify({"id": alert.id, "status": alert.status})