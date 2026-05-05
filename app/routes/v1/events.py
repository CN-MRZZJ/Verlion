from flask import jsonify, request

from .common import api_v1_bp, get_service


@api_v1_bp.get("/events")
def list_events():
    try:
        items = [dict(row) for row in get_service().list_events()]
        return jsonify({"ok": True, "items": items, "total": len(items)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.get("/events/progress")
def list_event_progress():
    try:
        items = get_service().list_event_progress()
        return jsonify({"ok": True, "items": items, "total": len(items)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


def _parse_bool(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "on", "yes"}


@api_v1_bp.put("/events/<int:event_id>/progress")
def update_event_progress(event_id: int):
    try:
        payload = request.get_json(silent=True) or request.form
        checkin_done = _parse_bool(payload.get("checkin_done", ""))
        competition_done = _parse_bool(payload.get("competition_done", ""))
        record_done = _parse_bool(payload.get("record_done", ""))
        publish_done = _parse_bool(payload.get("publish_done", ""))
        result = get_service().set_event_progress(
            event_id=event_id,
            checkin_done=checkin_done,
            competition_done=competition_done,
            record_done=record_done,
            publish_done=publish_done,
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.post("/events/progress/update")
def update_event_progress_compat():
    try:
        payload = request.get_json(silent=True) or request.form
        event_id = int(str(payload.get("event_id", "")).strip())
        checkin_done = _parse_bool(payload.get("checkin_done", ""))
        competition_done = _parse_bool(payload.get("competition_done", ""))
        record_done = _parse_bool(payload.get("record_done", ""))
        publish_done = _parse_bool(payload.get("publish_done", ""))
        result = get_service().set_event_progress(
            event_id=event_id,
            checkin_done=checkin_done,
            competition_done=competition_done,
            record_done=record_done,
            publish_done=publish_done,
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
