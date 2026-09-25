import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from extensions import db, jwt
from routes.api import api

load_dotenv()


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    default_database = Path(__file__).resolve().parent / "maternasense.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", f"sqlite:///{default_database}")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "development-only-change-me-use-env-secret")
    app.config["ML_MODE"] = os.getenv("ML_MODE", "demo")
    if test_config:
        app.config.update(test_config)
    CORS(app, origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174").split(","), supports_credentials=True)
    db.init_app(app)
    jwt.init_app(app)
    app.register_blueprint(api)

    with app.app_context():
        from models import Alert, AntenatalVisit, Delivery, Mother, Newborn, PostnatalVisit, RiskFactor, RiskPrediction, User  # noqa: F401
        db.create_all()

    @app.get("/api/health")
    def health() -> tuple[dict, int]:
        return jsonify({
            "status": "ok",
            "service": "maternasense-api",
            "ml_mode": app.config["ML_MODE"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }), 200

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"message": "Resource not found"}), 404

    @app.errorhandler(422)
    def unprocessable(_error):
        return jsonify({"message": "Request could not be processed"}), 422

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
