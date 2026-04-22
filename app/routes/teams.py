from flask import jsonify, request

from .common import get_service, main_bp


@main_bp.post("/team/add")
def team_add():
    try:
        payload = request.get_json(silent=True) or request.form
        team_id = get_service().add_team_by_department_name(
            department_name=str(payload.get("department_name", "")).strip(),
            event_id=int(str(payload.get("event_id", "")).strip()),
            team_name=str(payload.get("team_name", "")).strip(),
        )
        return jsonify({"ok": True, "inserted": 1, "team_id": team_id})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/team/delete")
def team_delete():
    try:
        payload = request.get_json(silent=True) or request.form
        result = get_service().delete_team(
            team_id=int(str(payload.get("team_id", "")).strip()),
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/team/member/add")
def team_member_add():
    try:
        payload = request.get_json(silent=True) or request.form
        result = get_service().adjust_team_member(
            team_id=int(str(payload.get("team_id", "")).strip()),
            athlete_type=str(payload.get("athlete_type", "")).strip(),
            athlete_no=str(payload.get("athlete_no", "")).strip(),
            op="add",
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/team/member/remove")
def team_member_remove():
    try:
        payload = request.get_json(silent=True) or request.form
        result = get_service().adjust_team_member(
            team_id=int(str(payload.get("team_id", "")).strip()),
            athlete_type=str(payload.get("athlete_type", "")).strip(),
            athlete_no=str(payload.get("athlete_no", "")).strip(),
            op="remove",
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400