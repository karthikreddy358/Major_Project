import os
import tempfile
from datetime import date

import pytest

from app import create_app
from extensions import db
from models.entities import AntenatalVisit, Mother, User


@pytest.fixture()
def client():
    database = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    database.close()
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database.name}", "JWT_SECRET_KEY": "test-secret-key-with-more-than-32-bytes"})
    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.add(User.demo_worker())
        mother = Mother(mother_code="MTEST", name="Synthetic Test Mother", age=25, source_type="synthetic")
        db.session.add(mother)
        db.session.flush()
        db.session.add(AntenatalVisit(mother_id=mother.id, visit_date=date(2026, 9, 20), gestational_age=24, systolic_bp=118, diastolic_bp=78))
        db.session.commit()
    with app.test_client() as test_client:
        yield test_client
    with app.app_context():
        db.session.remove()
        db.engine.dispose()
    os.unlink(database.name)


def auth_headers(client):
    response = client.post("/api/auth/login", json={"email": "demo@maternasense.local", "password": "demo-password"})
    return {"Authorization": f"Bearer {response.get_json()['access_token']}"}


def test_login_and_timeline(client):
    headers = auth_headers(client)
    response = client.get("/api/mothers/1/timeline", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["events"][0]["type"] == "antenatal"


def test_visit_prediction_and_alert_flow(client):
    headers = auth_headers(client)
    response = client.post("/api/mothers/1/antenatal-visits", headers=headers, json={"visit_date": "2026-09-24", "systolic_bp": 145, "blood_sugar": 10, "previous_complications": True})
    assert response.status_code == 201
    assert response.get_json()["prediction"]["risk_level"] == "HIGH"
    assert client.get("/api/alerts", headers=headers).get_json()["items"]


def test_missing_patient_returns_404(client):
    headers = auth_headers(client)
    assert client.get("/api/mothers/999/timeline", headers=headers).status_code == 404


def test_delivery_newborn_and_postnatal_are_linked(client):
    headers = auth_headers(client)
    delivery = client.post("/api/mothers/1/delivery", headers=headers, json={"delivery_date": "2026-10-01", "delivery_mode": "Vaginal"})
    assert delivery.status_code == 201
    newborn = client.post("/api/mothers/1/newborn", headers=headers, json={"newborn_code": "NTEST", "date_of_birth": "2026-10-01", "sex": "Female", "birth_weight": 3.1})
    assert newborn.status_code == 201
    newborn_id = newborn.get_json()["newborn_id"]
    postnatal = client.post("/api/mothers/1/postnatal-visits", headers=headers, json={"visit_date": "2026-10-08", "newborn_id": newborn_id, "days_after_delivery": 7, "newborn_weight": 3.2})
    assert postnatal.status_code == 201
    events = client.get("/api/mothers/1/timeline", headers=headers).get_json()["events"]
    assert {event["type"] for event in events} == {"antenatal", "delivery", "newborn", "postnatal"}