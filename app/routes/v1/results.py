from flask import jsonify, request

from .common import api_v1_bp, get_service


@api_v1_bp.get("/results")
def list_results():
    try:
        page = int(request.args.get("page", "1"))
        page_size = int(request.args.get("page_size", "20"))
        keyword = request.args.get("keyword", "").strip()
        event_id = request.args.get("event_id", "").strip()
        department_name = request.args.get("department_name", "").strip()
        gender = request.args.get("gender", "").strip()
        age_group = request.args.get("age_group", "").strip()
        category = request.args.get("category", "").strip()
        scoring_strategy = request.args.get("scoring_strategy", "").strip()
        sort_by = request.args.get("sort_by", "").strip()
        sort_dir = request.args.get("sort_dir", "desc").strip().lower()
        service = get_service()
        data = service.get_grid_page(
            view_name="results",
            page=page,
            page_size=page_size,
            keyword=keyword,
            event_id=event_id,
            department_name=department_name,
            gender=gender,
            age_group=age_group,
            category=category,
            scoring_strategy=scoring_strategy,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        return jsonify({"ok": True, **data})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.post("/results")
def create_result():
    try:
        payload = request.get_json(silent=True) or request.form
        event_id_text = payload.get("event_id")
        rank_text = payload.get("rank")
        athlete_type = str(payload.get("athlete_type", "")).strip()
        athlete_id_text = payload.get("athlete_id")
        athlete_no_text = str(payload.get("athlete_no", "")).strip()
        team_id_text = payload.get("team_id")
        performance = payload.get("performance")

        if not event_id_text:
            raise ValueError("event_id 必填")

        result_id = get_service().record_result(
            event_id=int(str(event_id_text).strip()),
            rank=int(str(rank_text).strip()) if rank_text else None,
            athlete_type=athlete_type if athlete_type else None,
            athlete_ref_id=int(str(athlete_id_text).strip()) if athlete_id_text else None,
            athlete_no=athlete_no_text if athlete_no_text else None,
            team_id=int(str(team_id_text).strip()) if team_id_text else None,
            performance=str(performance).strip() if performance else None,
            entered_by=str(payload.get("entered_by", "")).strip(),
        )
        return jsonify({"ok": True, "result_id": result_id})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
