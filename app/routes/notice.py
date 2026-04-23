from urllib.parse import quote

from flask import Response, current_app, jsonify, request

from .common import get_service, main_bp


@main_bp.post("/settings/report-environment")
def save_report_environment():
    try:
        payload = request.get_json(silent=True) or request.form
        fields = {
            "date": str(payload.get("date", "")).strip(),
            "wind_direction": str(payload.get("wind_direction", "")).strip(),
            "wind_speed": str(payload.get("wind_speed", "")).strip(),
            "air_quality": str(payload.get("air_quality", "")).strip(),
            "weather": str(payload.get("weather", "")).strip(),
            "temperature_high": str(payload.get("temperature_high", "")).strip(),
            "temperature_low": str(payload.get("temperature_low", "")).strip(),
        }
        get_service().set_report_environment_settings(fields)
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.get("/export/personal-result-notice.xlsx")
def export_personal_result_notice():
    try:
        event_id = int(str(request.args.get("event_id", "")).strip())
        template_name = str(request.args.get("template_name", "")).strip()
        content, filename = get_service().export_personal_result_notice_xlsx(
            event_id=event_id,
            template_name=template_name,
            template_dir=current_app.config["NOTICE_TEMPLATE_DIR"],
            layout_config_path=current_app.config["NOTICE_LAYOUT_CONFIG"],
        )
        safe_ascii_name = "personal_result_notice.xlsx"
        encoded_name = quote(filename)
        return Response(
            content,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={safe_ascii_name}; filename*=UTF-8''{encoded_name}"
            },
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.get("/preview/personal-result-notice.pdf")
def preview_personal_result_notice_pdf():
    try:
        event_id = int(str(request.args.get("event_id", "")).strip())
        template_name = str(request.args.get("template_name", "")).strip()
        content, filename = get_service().export_personal_result_notice_pdf(
            event_id=event_id,
            template_name=template_name,
            template_dir=current_app.config["NOTICE_TEMPLATE_DIR"],
            layout_config_path=current_app.config["NOTICE_LAYOUT_CONFIG"],
        )
        safe_ascii_name = "personal_result_notice.pdf"
        encoded_name = quote(filename)
        return Response(
            content,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename={safe_ascii_name}; filename*=UTF-8''{encoded_name}"
            },
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.get("/export/team-result-notice.xlsx")
def export_team_result_notice():
    try:
        event_id = int(str(request.args.get("event_id", "")).strip())
        template_name = str(request.args.get("template_name", "")).strip()
        content, filename = get_service().export_team_result_notice_xlsx(
            event_id=event_id,
            template_name=template_name,
            template_dir=current_app.config["NOTICE_TEMPLATE_DIR"],
            layout_config_path=current_app.config["TEAM_NOTICE_LAYOUT_CONFIG"],
        )
        safe_ascii_name = "team_result_notice.xlsx"
        encoded_name = quote(filename)
        return Response(
            content,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={safe_ascii_name}; filename*=UTF-8''{encoded_name}"
            },
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.get("/preview/team-result-notice.pdf")
def preview_team_result_notice_pdf():
    try:
        event_id = int(str(request.args.get("event_id", "")).strip())
        template_name = str(request.args.get("template_name", "")).strip()
        content, filename = get_service().export_team_result_notice_pdf(
            event_id=event_id,
            template_name=template_name,
            template_dir=current_app.config["NOTICE_TEMPLATE_DIR"],
            layout_config_path=current_app.config["TEAM_NOTICE_LAYOUT_CONFIG"],
        )
        safe_ascii_name = "team_result_notice.pdf"
        encoded_name = quote(filename)
        return Response(
            content,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename={safe_ascii_name}; filename*=UTF-8''{encoded_name}"
            },
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
