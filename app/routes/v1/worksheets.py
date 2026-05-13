from urllib.parse import quote

from flask import Response, current_app, jsonify, request

from .common import api_v1_bp, get_service


@api_v1_bp.get("/worksheets/checkin.xlsx")
def export_checkin_xlsx():
    try:
        event_id = int(str(request.args.get("event_id", "")).strip())
        round_id = int(str(request.args.get("round_id", "")).strip())
        heat_id_text = request.args.get("heat_id", "").strip()
        heat_id = int(heat_id_text) if heat_id_text else None
        template_name = str(request.args.get("template_name", "")).strip()
        if not template_name:
            event = get_service()._repo_read(lambda repo: repo.get_event_by_id(event_id))
            is_track = str(event["event_type"]) == "track" if event else True
            template_name = current_app.config["DEFAULT_CHECKIN_TEMPLATE"] if is_track else current_app.config["DEFAULT_FIELD_CHECKIN_TEMPLATE"]
        content, filename = get_service().export_checkin_xlsx(
            event_id=event_id, round_id=round_id,
            template_name=template_name,
            layout_config_path=current_app.config["CHECKIN_NOTICE_LAYOUT"],
            field_layout_path=current_app.config["CHECKIN_FIELD_LAYOUT"],
            heat_id=heat_id,
        )
        mimetype = "application/zip" if filename.endswith(".zip") else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return Response(content, mimetype=mimetype,
            headers={"Content-Disposition": f"attachment; filename=checkin.xlsx; filename*=UTF-8''{quote(filename)}"})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.get("/worksheets/checkin.pdf")
def preview_checkin_pdf():
    return jsonify({"ok": False, "error": "PDF 暂未实现"}), 400
