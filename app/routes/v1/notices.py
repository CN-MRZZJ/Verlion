from urllib.parse import quote

from flask import Response, current_app, jsonify, request

from .common import api_v1_bp, get_service


@api_v1_bp.get("/settings/report-environment")
def get_report_environment():
    try:
        env = get_service().get_report_environment_settings()
        return jsonify({"ok": True, "data": env})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.post("/settings/report-environment")
def save_report_environment():
    try:
        payload = request.get_json(silent=True) or request.form
        th = str(payload.get("temperature_high", "")).strip()
        tl = str(payload.get("temperature_low", "")).strip()
        fields = {
            "date": str(payload.get("date", "")).strip(),
            "wind_direction": str(payload.get("wind_direction", "")).strip(),
            "wind_speed": str(payload.get("wind_speed", "")).strip(),
            "air_quality": str(payload.get("air_quality", "")).strip(),
            "weather": str(payload.get("weather", "")).strip(),
            "temperature_high": (th + "℃") if th else "",
            "temperature_low": (tl + "℃") if tl else "",
        }
        get_service().set_report_environment_settings(fields)
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.get("/notices/grouped-result.xlsx")
def export_grouped_result_notice_xlsx():
    try:
        event_id = int(str(request.args.get("event_id", "")).strip())
        round_id = int(str(request.args.get("round_id", "")).strip())
        template_name = str(request.args.get("template_name", "")).strip() or current_app.config["DEFAULT_NOTICE_TEMPLATE"]
        content, filename = get_service().export_grouped_result_notice_xlsx(
            event_id=event_id, round_id=round_id,
            template_name=template_name,
            layout_config_path=current_app.config["GROUPED_RESULT_LAYOUT"],
        )
        return Response(content, mimetype="application/zip",
            headers={"Content-Disposition": f"attachment; filename=heat_notices.zip; filename*=UTF-8''{quote(filename)}"})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.get("/notices/grouped-result.pdf")
def preview_heat_result_notice_pdf():
    try:
        event_id = int(str(request.args.get("event_id", "")).strip())
        round_id = int(str(request.args.get("round_id", "")).strip())
        template_name = str(request.args.get("template_name", "")).strip() or current_app.config["DEFAULT_NOTICE_TEMPLATE"]
        content, filename = get_service().export_grouped_result_notice_pdf(
            event_id=event_id, round_id=round_id,
            template_name=template_name,
            layout_config_path=current_app.config["GROUPED_RESULT_LAYOUT"],
        )
        return Response(content, mimetype="application/zip",
            headers={"Content-Disposition": f"inline; filename=notice.zip; filename*=UTF-8''{quote(filename)}"})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.get("/notices/full-result.xlsx")
def export_full_result_notice_xlsx():
    try:
        event_id = int(str(request.args.get("event_id", "")).strip())
        round_id = int(str(request.args.get("round_id", "")).strip())
        template_name = str(request.args.get("template_name", "")).strip() or current_app.config["DEFAULT_NOTICE_TEMPLATE"]
        content, filename = get_service().export_full_result_notice_xlsx(
            event_id=event_id, round_id=round_id,
            template_name=template_name,
            layout_config_path=current_app.config["FULL_RESULT_LAYOUT"],
        )
        return Response(content,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=notice.xlsx; filename*=UTF-8''{quote(filename)}"})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.get("/notices/full-result.pdf")
def preview_overall_result_notice_pdf():
    try:
        event_id = int(str(request.args.get("event_id", "")).strip())
        round_id = int(str(request.args.get("round_id", "")).strip())
        template_name = str(request.args.get("template_name", "")).strip() or current_app.config["DEFAULT_NOTICE_TEMPLATE"]
        content, filename = get_service().export_full_result_notice_pdf(
            event_id=event_id, round_id=round_id,
            template_name=template_name,
            layout_config_path=current_app.config["FULL_RESULT_LAYOUT"],
        )
        return Response(content, mimetype="application/pdf",
            headers={"Content-Disposition": f"inline; filename=notice.pdf; filename*=UTF-8''{quote(filename)}"})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
