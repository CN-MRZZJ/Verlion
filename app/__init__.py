from flask import Flask, redirect, url_for

from config import Config
from app.models.database import Database


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    Database(app.config["DATABASE_PATH"]).initialize()

    from app.routes.v1 import api_v1_bp, site_v1_bp

    app.register_blueprint(site_v1_bp)
    app.register_blueprint(api_v1_bp)

    @app.get("/")
    def root_redirect():
        return redirect(url_for("site_v1.home"))

    return app
