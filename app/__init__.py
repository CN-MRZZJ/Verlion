from flask import Flask, Response, jsonify, redirect, url_for

from config import Config
from app.models.database import Database
from app.openapi import get_openapi_spec, swagger_ui_html
from app.rules import age_group_label, age_group_labels, age_group_options
from app.rules import athlete_age_group_label, event_age_group_label


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    Database(app.config["DATABASE_PATH"]).initialize()

    from app.routes.v1 import api_v1_bp, site_v1_bp

    app.register_blueprint(site_v1_bp)
    app.register_blueprint(api_v1_bp)

    @app.context_processor
    def template_rules():
        return {
            "age_group_label": age_group_label,
            "age_group_labels": age_group_labels(),
            "athlete_age_group_label": athlete_age_group_label,
            "event_age_group_label": event_age_group_label,
            "athlete_age_group_labels": age_group_labels("athlete"),
            "event_age_group_labels": age_group_labels("event"),
            "athlete_age_group_options": age_group_options("athlete"),
            "event_age_group_options": age_group_options("event"),
        }

    @app.get("/")
    def root_redirect():
        return redirect(url_for("site_v1.home"))

    @app.get("/api/v1/openapi.json")
    def openapi_json():
        return jsonify(get_openapi_spec())

    @app.get("/api/docs")
    def swagger_docs():
        return Response(swagger_ui_html(), mimetype="text/html")

    return app
