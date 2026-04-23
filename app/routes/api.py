from flask import Response, jsonify, request

from .common import get_service, main_bp


@main_bp.get("/api/athlete/query")
def api_athlete_query():
    try:
        athlete_type = request.args.get("athlete_type", "").strip()
        keyword = request.args.get("keyword", "").strip()
        items = get_service().query_athletes(athlete_type=athlete_type, keyword=keyword)
        return jsonify({"ok": True, "items": items, "total": len(items)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.get("/api/athlete/registered-events")
def api_athlete_registered_events():
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


@main_bp.get("/api/team/query")
def api_team_query():
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


@main_bp.get("/api/team/members")
def api_team_members():
    try:
        team_id = int(str(request.args.get("team_id", "")).strip())
        items = get_service().get_team_members(team_id)
        return jsonify({"ok": True, "items": items, "total": len(items)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.get("/api/event-progress")
def api_event_progress():
    try:
        items = get_service().list_event_progress()
        return jsonify({"ok": True, "items": items, "total": len(items)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/api/event-progress/update")
def api_event_progress_update():
    try:
        payload = request.get_json(silent=True) or request.form
        event_id = int(str(payload.get("event_id", "")).strip())
        record_done = str(payload.get("record_done", "")).strip().lower() in {"1", "true", "on", "yes"}
        print_done = str(payload.get("print_done", "")).strip().lower() in {"1", "true", "on", "yes"}
        result = get_service().set_event_progress(
            event_id=event_id,
            record_done=record_done,
            print_done=print_done,
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.get("/api/events")
def api_events():
    return jsonify([dict(row) for row in get_service().list_events()])


@main_bp.get("/api/athletes")
def api_athletes():
    return jsonify([dict(row) for row in get_service().list_athletes()])


@main_bp.get("/api/data/<view>")
def api_data(view: str):
    try:
        service = get_service()
        page = int(request.args.get("page", "1"))
        page_size = int(request.args.get("page_size", "20"))
        keyword = request.args.get("keyword", "").strip()
        department_name = request.args.get("department_name", "").strip()
        gender = request.args.get("gender", "").strip()
        age_group = request.args.get("age_group", "").strip()
        category = request.args.get("category", "").strip()
        scoring_strategy = request.args.get("scoring_strategy", "").strip()
        sort_by = request.args.get("sort_by", "").strip()
        sort_dir = request.args.get("sort_dir", "desc").strip().lower()
        return jsonify(
            {
                "ok": True,
                **service.get_grid_page(
                    view_name=view,
                    page=page,
                    page_size=page_size,
                    keyword=keyword,
                    department_name=department_name,
                    gender=gender,
                    age_group=age_group,
                    category=category,
                    scoring_strategy=scoring_strategy,
                    sort_by=sort_by,
                    sort_dir=sort_dir,
                ),
            }
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.get("/export/data/<view>")
def export_data(view: str):
    try:
        service = get_service()
        content = service.export_grid_csv(
            view_name=view,
            keyword=request.args.get("keyword", "").strip(),
            department_name=request.args.get("department_name", "").strip(),
            gender=request.args.get("gender", "").strip(),
            age_group=request.args.get("age_group", "").strip(),
            category=request.args.get("category", "").strip(),
            scoring_strategy=request.args.get("scoring_strategy", "").strip(),
        )
        filename = f"{view}_export.csv"
        return Response(
            content,
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
