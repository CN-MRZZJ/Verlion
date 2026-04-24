from flask import jsonify, render_template, request

from app.rules import load_rule_config, save_rule_config

from .common import api_v1_bp, site_v1_bp


@site_v1_bp.get("/pages/rules")
def rules_page():
    return render_template(
        "rules_config.html",
        active_page="rules_config",
        rule_config=load_rule_config(),
    )


@api_v1_bp.get("/rules")
def get_rules():
    return jsonify({"ok": True, "config": load_rule_config()})


@api_v1_bp.put("/rules")
def update_rules():
    try:
        payload = request.get_json(silent=True) or {}
        config = payload.get("config")
        if not isinstance(config, dict):
            raise ValueError("config 必须是对象")
        save_rule_config(config)
        return jsonify({"ok": True, "config": load_rule_config()})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
