from flask import jsonify, request

from app.rules import invalidate_rules_cache

from .common import api_v1_bp, get_service

_ALLOWED_STRATEGIES = {"time", "length", "count", "count_miss"}


@api_v1_bp.get("/event-types")
def list_event_types():
    try:
        items = get_service().list_event_types()
        return jsonify({"ok": True, "items": items, "total": len(items)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.post("/event-types")
def create_event_type():
    try:
        payload = request.get_json(silent=True) or {}
        code = str(payload.get("code", "")).strip()
        name = str(payload.get("name", "")).strip()
        scoring_strategy = str(payload.get("scoring_strategy", "")).strip()
        competition_format = str(payload.get("competition_format", "heats")).strip()
        if not code:
            raise ValueError("code 不能为空")
        if not name:
            raise ValueError("name 不能为空")
        if scoring_strategy not in _ALLOWED_STRATEGIES:
            raise ValueError(f"scoring_strategy 必须为 {'/'.join(sorted(_ALLOWED_STRATEGIES))}")
        if competition_format not in ("heats", "knockout", "round_robin"):
            raise ValueError("competition_format 必须为 heats/knockout/round_robin")
        code = get_service().insert_event_type(code, name, scoring_strategy, competition_format)
        invalidate_rules_cache()
        return jsonify({"ok": True, "code": code})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.get("/event-types/<code>")
def get_event_type(code: str):
    try:
        item = get_service().get_event_type(code)
        if not item:
            return jsonify({"ok": False, "error": "不存在"}), 404
        return jsonify({"ok": True, "item": item})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.put("/event-types/<code>")
def update_event_type(code: str):
    try:
        payload = request.get_json(silent=True) or {}
        updates = {}
        if "name" in payload:
            name = str(payload["name"]).strip()
            if not name:
                raise ValueError("name 不能为空")
            updates["name"] = name
        if "scoring_strategy" in payload:
            val = str(payload["scoring_strategy"]).strip()
            if val not in _ALLOWED_STRATEGIES:
                raise ValueError(f"scoring_strategy 必须为 {'/'.join(sorted(_ALLOWED_STRATEGIES))}")
            updates["scoring_strategy"] = val
        if "competition_format" in payload:
            val = str(payload["competition_format"]).strip()
            if val not in ("heats", "knockout", "round_robin"):
                raise ValueError("competition_format 必须为 heats/knockout/round_robin")
            updates["competition_format"] = val
        if not updates:
            raise ValueError("至少需要提供 name、scoring_strategy 或 competition_format")
        get_service().update_event_type(code, **updates)
        invalidate_rules_cache()
        return jsonify({"ok": True, "code": code})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.delete("/event-types/<code>")
def delete_event_type(code: str):
    try:
        ok, error = get_service().delete_event_type(code)
        if not ok:
            return jsonify({"ok": False, "error": error}), 400
        invalidate_rules_cache()
        return jsonify({"ok": True, "deleted": code})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
