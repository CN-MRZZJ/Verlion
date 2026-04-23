from datetime import datetime
from flask import Response, current_app, jsonify, request, send_from_directory

from .common import get_service, main_bp, parse_csv_upload


@main_bp.post("/setup/init")
def setup_init():
    try:
        meet_date = datetime.strptime(request.form.get("meet_date", "2026-04-23"), "%Y-%m-%d").date()
        get_service().set_meet_date(meet_date)
        return jsonify({"ok": True, "meet_date": meet_date.isoformat()})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.get("/templates/<path:name>")
def download_template(name: str):
    return send_from_directory(current_app.config["CSV_TEMPLATE_DIR"], name, as_attachment=True)


@main_bp.get("/templates/registrations-template.csv")
def download_registration_template():
    try:
        category = request.args.get("category", "").strip()
        content, filename = get_service().export_registration_matrix_template_csv(category)
        return Response(
            content,
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/import/events-csv")
def import_events_csv():
    try:
        result = get_service().import_events_rows(parse_csv_upload())
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/import/competitive-athletes-csv")
def import_competitive_athletes_csv():
    try:
        result = get_service().import_athletes_rows(parse_csv_upload(), athlete_type="competitive")
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/import/fun-athletes-csv")
def import_fun_athletes_csv():
    try:
        result = get_service().import_athletes_rows(parse_csv_upload(), athlete_type="fun")
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/import/competitive-registrations-csv")
def import_competitive_registrations_csv():
    try:
        result = get_service().import_registrations_rows(
            parse_csv_upload(),
            target_category="competitive",
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/import/fun-registrations-csv")
def import_fun_registrations_csv():
    try:
        result = get_service().import_registrations_rows(
            parse_csv_upload(),
            target_category="fun",
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/admin/clear-data")
def clear_data():
    try:
        payload = request.get_json(silent=True) or request.form
        tables = payload.getlist("tables") if hasattr(payload, "getlist") else payload.get("tables", [])
        if isinstance(tables, str):
            tables = [tables]
        confirm_text = str(payload.get("confirm_text", "")).strip()
        confirm_code = str(payload.get("confirm_code", "")).strip()
        acknowledged = str(payload.get("acknowledged", "")).strip().lower() in {"1", "true", "on", "yes"}
        result = get_service().clear_table_data(
            requested_tables=tables,
            confirm_text=confirm_text,
            confirm_code=confirm_code,
            acknowledged=acknowledged,
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400