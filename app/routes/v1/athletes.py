from flask import jsonify, request

from .common import api_v1_bp, get_service


@api_v1_bp.get("/athletes")
def list_athletes():
    try:
        athlete_type = request.args.get("athlete_type", "").strip()
        keyword = request.args.get("keyword", "").strip()
        page = int(request.args.get("page", "1"))
        page_size = int(request.args.get("page_size", "20"))
        result = get_service().query_athletes(athlete_type=athlete_type, keyword=keyword, page=page, page_size=page_size)
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.post("/athletes")
def create_athlete():
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


@api_v1_bp.post("/athletes/delete")
def delete_athlete_compat():
    try:
        payload = request.get_json(silent=True) or request.form
        athlete_type = str(payload.get("athlete_type", "")).strip()
        athlete_no = str(payload.get("athlete_no", "")).strip()
        result = get_service().delete_athlete_by_no(athlete_type=athlete_type, athlete_no=athlete_no)
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.delete("/athletes/<athlete_type>/<athlete_no>")
def delete_athlete(athlete_type: str, athlete_no: str):
    try:
        result = get_service().delete_athlete_by_no(athlete_type=athlete_type, athlete_no=athlete_no)
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.get("/athletes/<athlete_type>/<athlete_no>/registrations")
def athlete_registered_events(athlete_type: str, athlete_no: str):
    try:
        items = get_service().get_registered_individual_events(
            athlete_type=athlete_type,
            athlete_no=athlete_no,
        )
        return jsonify({"ok": True, "items": items, "total": len(items)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.get("/athletes/registered-events")
def athlete_registered_events_compat():
    try:
        athlete_type = request.args.get("athlete_type", "").strip()
        athlete_no = request.args.get("athlete_no", "").strip()
        items = get_service().get_registered_individual_events(
            athlete_type=athlete_type,
            athlete_no=athlete_no,
        )
        return jsonify({"ok": True, "items": items, "total": len(items)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.post("/athletes/<athlete_type>/<athlete_no>/registrations/<int:event_id>")
def add_athlete_registration(athlete_type: str, athlete_no: str, event_id: int):
    try:
        result = get_service().adjust_athlete_registration(
            athlete_type=athlete_type,
            athlete_no=athlete_no,
            event_id=event_id,
            op="add",
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.post("/athletes/registrations/add")
def add_athlete_registration_compat():
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


@api_v1_bp.delete("/athletes/<athlete_type>/<athlete_no>/registrations/<int:event_id>")
def remove_athlete_registration(athlete_type: str, athlete_no: str, event_id: int):
    try:
        result = get_service().adjust_athlete_registration(
            athlete_type=athlete_type,
            athlete_no=athlete_no,
            event_id=event_id,
            op="remove",
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.post("/athletes/registrations/remove")
def remove_athlete_registration_compat():
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
