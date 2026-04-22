from flask import Blueprint, jsonify

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/ping")
def ping():
    return jsonify({"ok": True, "message": "auth blueprint ready"})
