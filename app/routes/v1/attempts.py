from flask import jsonify, request

from .common import api_v1_bp, get_service


@api_v1_bp.get("/attempts")
def list_attempts():
    try:
        event_id_text = request.args.get("event_id")
        athlete_type = request.args.get("athlete_type", "").strip()
        athlete_id_text = request.args.get("athlete_ref_id")
        team_id_text = request.args.get("team_id")
        round_id_text = request.args.get("round_id")

        if not event_id_text:
            raise ValueError("event_id 必填")

        athlete_ref_id = int(athlete_id_text) if athlete_id_text else None
        team_id = int(team_id_text) if team_id_text else None

        if (athlete_ref_id is not None) == (team_id is not None):
            raise ValueError("必须且只能传 athlete_ref_id 或 team_id 其中之一")

        with get_service().db.connect() as conn:
            from app.models.repositories import SportsRepository
            repo = SportsRepository(conn)
            rows = repo.list_attempts_for_target(
                event_id=int(event_id_text),
                athlete_type=athlete_type if athlete_ref_id is not None else None,
                athlete_ref_id=athlete_ref_id,
                team_id=team_id,
                round_id=int(round_id_text) if round_id_text else None,
            )
            items = [dict(r) for r in rows]
            return jsonify({"ok": True, "items": items, "total": len(items)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.put("/attempts/<int:attempt_id>/void")
def void_attempt(attempt_id: int):
    try:
        payload = request.get_json(silent=True) or {}
        is_void = bool(payload.get("is_void", True))
        get_service().void_attempt(attempt_id, is_void)
        return jsonify({"ok": True, "attempt_id": attempt_id, "is_void": is_void})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
