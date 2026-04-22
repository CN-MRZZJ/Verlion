from flask import jsonify, request

from .common import get_service, main_bp


@main_bp.post("/record-result")
def record_result():
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
        )
        return jsonify({"ok": True, "result_id": result_id})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400