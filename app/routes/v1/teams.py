from flask import jsonify, request

from .common import api_v1_bp, get_service


@api_v1_bp.get("/teams")
def list_teams():
    try:
        keyword = request.args.get("keyword", "").strip()
        department_name = request.args.get("department_name", "").strip()
        event_id_raw = request.args.get("event_id", "").strip()
        event_id = int(event_id_raw) if event_id_raw else None
        items = get_service().query_teams(
            keyword=keyword,
            department_name=department_name,
            event_id=event_id,
        )
        return jsonify({"ok": True, "items": items, "total": len(items)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.post("/teams")
def create_team():
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


@api_v1_bp.post("/teams/batch-add")
def batch_add_teams():
    try:
        payload = request.get_json(silent=True) or request.form
        if hasattr(payload, "getlist"):
            department_names = payload.getlist("department_names")
        else:
            department_names = payload.get("department_names", [])
            if isinstance(department_names, str):
                department_names = [x.strip() for x in department_names.replace("，", ",").replace("\n", ",").split(",")]
        result = get_service().batch_add_teams_by_departments(
            event_id=int(str(payload.get("event_id", "")).strip()),
            department_names=department_names,
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.post("/teams/delete")
def delete_team_compat():
    try:
        payload = request.get_json(silent=True) or request.form
        team_id = int(str(payload.get("team_id", "")).strip())
        result = get_service().delete_team(team_id=team_id)
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.delete("/teams/<int:team_id>")
def delete_team(team_id: int):
    try:
        result = get_service().delete_team(team_id=team_id)
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.get("/teams/<int:team_id>/members")
def list_team_members(team_id: int):
    try:
        items = get_service().get_team_members(team_id)
        return jsonify({"ok": True, "items": items, "total": len(items)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.get("/teams/members")
def list_team_members_compat():
    try:
        team_id = int(str(request.args.get("team_id", "")).strip())
        items = get_service().get_team_members(team_id)
        return jsonify({"ok": True, "items": items, "total": len(items)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.post("/teams/<int:team_id>/members")
def add_team_member(team_id: int):
    try:
        payload = request.get_json(silent=True) or request.form
        result = get_service().adjust_team_member(
            team_id=team_id,
            athlete_type=str(payload.get("athlete_type", "")).strip(),
            athlete_no=str(payload.get("athlete_no", "")).strip(),
            op="add",
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.post("/teams/members/add")
def add_team_member_compat():
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


@api_v1_bp.delete("/teams/<int:team_id>/members")
def remove_team_member(team_id: int):
    try:
        payload = request.get_json(silent=True) or request.form
        result = get_service().adjust_team_member(
            team_id=team_id,
            athlete_type=str(payload.get("athlete_type", "")).strip(),
            athlete_no=str(payload.get("athlete_no", "")).strip(),
            op="remove",
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.post("/teams/members/remove")
def remove_team_member_compat():
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
