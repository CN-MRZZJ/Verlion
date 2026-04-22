from flask import jsonify, request

from .common import get_service, main_bp


@main_bp.post("/athlete/add")
def athlete_add():
    try:
        payload = request.get_json(silent=True) or request.form
        athlete_id = get_service().add_athlete_by_department_name(
            athlete_type=str(payload.get("athlete_type", "")).strip(),
            athlete_no=str(payload.get("athlete_no", "")).strip(),
            name=str(payload.get("name", "")).strip(),
            gender=str(payload.get("gender", "")).strip(),
            department_name=str(payload.get("department_name", "")).strip(),
            age_group=str(payload.get("age_group", "")).strip() or None,
        )
        return jsonify({"ok": True, "inserted": 1, "athlete_id": athlete_id})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/athlete/delete")
def athlete_delete():
    try:
        payload = request.get_json(silent=True) or request.form
        result = get_service().delete_athlete_by_no(
            athlete_type=str(payload.get("athlete_type", "")).strip(),
            athlete_no=str(payload.get("athlete_no", "")).strip(),
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/athlete/registration/add")
def athlete_registration_add():
    try:
        payload = request.get_json(silent=True) or request.form
        result = get_service().adjust_athlete_registration(
            athlete_type=str(payload.get("athlete_type", "")).strip(),
            athlete_no=str(payload.get("athlete_no", "")).strip(),
            event_id=int(str(payload.get("event_id", "")).strip()),
            op="add",
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/athlete/registration/remove")
def athlete_registration_remove():
    try:
        payload = request.get_json(silent=True) or request.form
        result = get_service().adjust_athlete_registration(
            athlete_type=str(payload.get("athlete_type", "")).strip(),
            athlete_no=str(payload.get("athlete_no", "")).strip(),
            event_id=int(str(payload.get("event_id", "")).strip()),
            op="remove",
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400