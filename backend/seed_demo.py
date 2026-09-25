import sys
from datetime import date, timedelta

from app import app
from extensions import db
from models.entities import AntenatalVisit, Mother, User
from services.prediction import create_prediction


def seed() -> None:
    with app.app_context():
        if "--reset" in sys.argv:
            db.drop_all()
            db.create_all()
        if not User.query.filter_by(email="demo@maternasense.local").first():
            db.session.add(User.demo_worker())
        if Mother.query.count() == 0:
            profiles = [
                ("M001", "Synthetic Low Model Score", 26, ["low"] * 2),
                ("M002", "Synthetic Moderate Model Score", 29, ["moderate"] * 3),
                ("M003", "Synthetic High Model Score", 24, ["low", "moderate", "high", "high"]),
                ("M004", "Synthetic Maternal + Newborn", 31, ["low"] * 2),
            ]
            for code, name, age, levels in profiles:
                mother = Mother(mother_code=code, name=name, age=age, source_type="synthetic")
                db.session.add(mother)
                db.session.flush()
                for index, level in enumerate(levels, start=1):
                    high_signal = level == "high"
                    moderate_signal = level == "moderate"
                    visit = AntenatalVisit(mother_id=mother.id, visit_date=date.today() - timedelta(days=(len(levels) - index) * 21), gestational_age=12 + index * 5, systolic_bp=145 if high_signal else 140 if moderate_signal else 118, diastolic_bp=90 if high_signal else 82, blood_sugar=10 if high_signal else 7.2, body_temperature=98.4, heart_rate=82 if high_signal else 76, hemoglobin=10.8 if high_signal else 12.4, previous_complications=high_signal)
                    mother.antenatal_visits.append(visit)
                    db.session.flush()
                    prediction = create_prediction(mother, visit.id)
                    db.session.add(prediction)
        db.session.commit()
        print(f"Seeded {Mother.query.count()} synthetic mothers and {User.query.count()} users. Use --reset to recreate clean demo data.")


if __name__ == "__main__":
    seed()