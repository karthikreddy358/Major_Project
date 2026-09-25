from datetime import date, datetime, timezone

from werkzeug.security import generate_password_hash

from extensions import db


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="HEALTHCARE_WORKER")
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    @classmethod
    def demo_worker(cls) -> "User":
        return cls(
            name="Demo Healthcare Worker",
            email="demo@maternasense.local",
            password_hash=generate_password_hash("demo-password"),
            role="HEALTHCARE_WORKER",
        )


class Mother(db.Model):
    __tablename__ = "mothers"
    id = db.Column(db.Integer, primary_key=True)
    mother_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    blood_group = db.Column(db.String(8), nullable=True)
    source_type = db.Column(db.String(24), nullable=False, default="synthetic")
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    antenatal_visits = db.relationship("AntenatalVisit", backref="mother", cascade="all, delete-orphan")
    deliveries = db.relationship("Delivery", backref="mother", cascade="all, delete-orphan")
    newborns = db.relationship("Newborn", backref="mother", cascade="all, delete-orphan")
    postnatal_visits = db.relationship("PostnatalVisit", backref="mother", cascade="all, delete-orphan")
    predictions = db.relationship("RiskPrediction", backref="mother", cascade="all, delete-orphan")
    alerts = db.relationship("Alert", backref="mother", cascade="all, delete-orphan")


class AntenatalVisit(db.Model):
    __tablename__ = "antenatal_visits"
    id = db.Column(db.Integer, primary_key=True)
    mother_id = db.Column(db.Integer, db.ForeignKey("mothers.id"), nullable=False, index=True)
    visit_date = db.Column(db.Date, nullable=False)
    gestational_age = db.Column(db.Float, nullable=True)
    systolic_bp = db.Column(db.Float, nullable=True)
    diastolic_bp = db.Column(db.Float, nullable=True)
    blood_sugar = db.Column(db.Float, nullable=True)
    body_temperature = db.Column(db.Float, nullable=True)
    heart_rate = db.Column(db.Float, nullable=True)
    hemoglobin = db.Column(db.Float, nullable=True)
    previous_complications = db.Column(db.Boolean, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class Delivery(db.Model):
    __tablename__ = "deliveries"
    id = db.Column(db.Integer, primary_key=True)
    mother_id = db.Column(db.Integer, db.ForeignKey("mothers.id"), nullable=False, index=True)
    delivery_date = db.Column(db.Date, nullable=False)
    gestational_age = db.Column(db.Float, nullable=True)
    delivery_mode = db.Column(db.String(32), nullable=True)
    delivery_place = db.Column(db.String(120), nullable=True)
    complications = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class Newborn(db.Model):
    __tablename__ = "newborns"
    id = db.Column(db.Integer, primary_key=True)
    mother_id = db.Column(db.Integer, db.ForeignKey("mothers.id"), nullable=False, index=True)
    newborn_code = db.Column(db.String(32), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    sex = db.Column(db.String(16), nullable=True)
    birth_weight = db.Column(db.Float, nullable=True)
    birth_length = db.Column(db.Float, nullable=True)
    apgar_score = db.Column(db.Float, nullable=True)
    gestational_age = db.Column(db.Float, nullable=True)
    nicu_required = db.Column(db.Boolean, nullable=True)
    complications = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class PostnatalVisit(db.Model):
    __tablename__ = "postnatal_visits"
    id = db.Column(db.Integer, primary_key=True)
    mother_id = db.Column(db.Integer, db.ForeignKey("mothers.id"), nullable=False, index=True)
    newborn_id = db.Column(db.Integer, db.ForeignKey("newborns.id"), nullable=True, index=True)
    visit_date = db.Column(db.Date, nullable=False)
    days_after_delivery = db.Column(db.Integer, nullable=True)
    maternal_bp = db.Column(db.String(32), nullable=True)
    maternal_hemoglobin = db.Column(db.Float, nullable=True)
    newborn_weight = db.Column(db.Float, nullable=True)
    feeding_status = db.Column(db.String(64), nullable=True)
    newborn_condition = db.Column(db.String(64), nullable=True)
    complications = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class RiskPrediction(db.Model):
    __tablename__ = "risk_predictions"
    id = db.Column(db.Integer, primary_key=True)
    mother_id = db.Column(db.Integer, db.ForeignKey("mothers.id"), nullable=False, index=True)
    trigger_visit_id = db.Column(db.Integer, nullable=True)
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(16), nullable=False)
    model_name = db.Column(db.String(64), nullable=False)
    prediction_timestamp = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    is_demo_prediction = db.Column(db.Boolean, nullable=False, default=True)
    factors = db.relationship("RiskFactor", backref="prediction", cascade="all, delete-orphan")


class RiskFactor(db.Model):
    __tablename__ = "risk_factors"
    id = db.Column(db.Integer, primary_key=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey("risk_predictions.id"), nullable=False, index=True)
    feature_name = db.Column(db.String(80), nullable=False)
    feature_value = db.Column(db.String(80), nullable=True)
    contribution = db.Column(db.Float, nullable=False)
    direction = db.Column(db.String(16), nullable=False)


class Alert(db.Model):
    __tablename__ = "alerts"
    id = db.Column(db.Integer, primary_key=True)
    mother_id = db.Column(db.Integer, db.ForeignKey("mothers.id"), nullable=False, index=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey("risk_predictions.id"), nullable=False)
    risk_level = db.Column(db.String(16), nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(16), nullable=False, default="NEW")
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)


def parse_date(value: str | None) -> date:
    if not value:
        return date.today()
    return date.fromisoformat(value)