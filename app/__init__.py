from flask import Flask, jsonify, redirect, render_template
from flask_cors import CORS

from config import Config
from app.models.database import Database
from app.openapi import get_openapi_spec
from app.services import SportsMeetService


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    Database(app.config["DATABASE_PATH"]).initialize()

    from app.routes.v1 import api_v1_bp

    app.register_blueprint(api_v1_bp)

    @app.get("/api/v1/openapi.json")
    def openapi_json():
        return jsonify(get_openapi_spec())

    @app.get("/docs")
    @app.get("/api/docs")
    def api_docs():
        return render_template("swagger.html")

    @app.get("/api/v1/status")
    def system_status():
        service = SportsMeetService(app.config["DATABASE_PATH"])
        service.init_db()
        return jsonify(service.get_initialization_status())

    return app
