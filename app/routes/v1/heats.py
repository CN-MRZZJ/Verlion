from flask import jsonify, request

from app.grouping import get_algorithm, list_algorithms
from app.grouping.schema import GroupingConfig, GroupingInput, Participant

from .common import api_v1_bp, get_service


@api_v1_bp.get("/events/<int:event_id>/heats")
def get_event_heats(event_id: int):
    try:
        result = get_service().get_heats_for_event(event_id)
        return jsonify({"ok": True, "data": result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.post("/events/<int:event_id>/heats")
def create_event_heats(event_id: int):
    try:
        payload = request.get_json(silent=True) or {}
        config = GroupingConfig(
            lanes_per_heat=int(payload.get("lanes_per_heat", 8)),
            algorithm=str(payload.get("algorithm", "random")),
            params=payload.get("params", {}),
        )

        service = get_service()

        def _read(repo):
            rows = repo.list_event_participants(event_id)
            participants = []
            for r in rows:
                participants.append(Participant(
                    athlete_id=int(r["id"]),
                    name=str(r["name"]),
                    athlete_type=str(r["athlete_type"]),
                    department=str(r["department_name"] or ""),
                ))
            hc = repo.get_heats_config(event_id)
            heat_rounds = int(hc["heat_rounds"]) if hc else 1
            return participants, heat_rounds

        participants, heat_rounds = service._repo_read(_read)
        if not participants:
            return jsonify({"ok": False, "error": "该项目没有报名运动员"}), 400

        algorithm = get_algorithm(config.algorithm)
        input = GroupingInput(event_id=event_id, participants=participants, config=config, heat_rounds=heat_rounds)
        output = algorithm.run(input)
        service.save_grouping_output(output)

        return jsonify({"ok": True, "data": service.get_heats_for_event(event_id)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.delete("/events/<int:event_id>/heats")
def delete_event_heats(event_id: int):
    try:
        get_service().clear_heats_for_event(event_id)
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.put("/events/<int:event_id>/heats/<int:heat_id>/entries/<int:entry_id>")
def update_heat_entry(event_id: int, heat_id: int, entry_id: int):
    try:
        payload = request.get_json(silent=True) or request.form
        lane = payload.get("lane")
        if lane is not None:
            lane = int(lane)
        target_heat_id = int(payload.get("heat_id", heat_id))
        if lane is None and target_heat_id == heat_id:
            return jsonify({"ok": False, "error": "lane 或 heat_id 至少提供一个"}), 400
        get_service().swap_or_move_heat_entry(entry_id, target_heat_id, lane)
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.put("/events/<int:event_id>/heats/config")
def set_heats_config(event_id: int):
    try:
        payload = request.get_json(silent=True) or request.form
        heat_rounds = int(payload.get("heat_rounds", 1))
        if not 1 <= heat_rounds <= 4:
            return jsonify({"ok": False, "error": "heat_rounds 必须在 1-4 之间"}), 400
        get_service().set_heats_config(event_id, heat_rounds)
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.post("/events/<int:event_id>/rounds/<int:round_id>/advance")
def advance_round(event_id: int, round_id: int):
    try:
        payload = request.get_json(silent=True) or {}
        strategy = str(payload.get("strategy", "per_heat_top"))
        lanes_per_heat = int(payload.get("lanes_per_heat", 8))
        algorithm = str(payload.get("algorithm", "seeded"))
        params = payload.get("params", {})
        result = get_service().advance_to_next_round(event_id, round_id, strategy, lanes_per_heat, algorithm, params)
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.get("/events/advancement-strategies")
def list_advancement_strategies():
    from app.grouping.advancement import list_advancements
    return jsonify({"ok": True, "strategies": list_advancements()})


@api_v1_bp.get("/events/heats/algorithms")
def list_heat_algorithms():
    return jsonify({"ok": True, "algorithms": list_algorithms()})
