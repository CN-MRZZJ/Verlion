import csv
import io
from datetime import datetime
from urllib.parse import quote

from flask import Blueprint, Response, current_app, jsonify, render_template, request, send_from_directory

from app.services import SportsMeetService

main_bp = Blueprint("main", __name__)

DATA_VIEWS = [
    ("events", "项目"),
    ("athletes", "运动员"),
    ("departments", "部门"),
    ("teams", "队伍"),
    ("registrations", "报名记录"),
    ("results", "成绩记录"),
    ("standings", "积分榜"),
    ("participation", "参赛率"),
]


def get_service() -> SportsMeetService:
    service = SportsMeetService(current_app.config["DATABASE_PATH"])
    service.init_db()
    return service


def parse_csv_upload() -> list[dict[str, str]]:
    up = request.files.get("file")
    if up is None or up.filename == "":
        raise ValueError("请上传 CSV 文件")
    if not up.filename.lower().endswith(".csv"):
        raise ValueError("仅支持 .csv 文件")

    raw = up.stream.read()
    text = None
    for enc in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            pass
    if text is None:
        raise ValueError("CSV 编码无法识别，请使用 UTF-8 或 GB18030。")

    reader = csv.DictReader(io.StringIO(text))
    rows = [dict(r) for r in reader]
    if reader.fieldnames is None:
        raise ValueError("CSV 缺少表头")
    return rows


@main_bp.get("/")
def home():
    data = get_service().workbench_data()
    return render_template("home.html", active_page="home", **data)


@main_bp.get("/import-center")
def import_center():
    return render_template(
        "import_center.html",
        active_page="import_center",
        clear_table_options=SportsMeetService.CLEAR_TABLES,
    )


@main_bp.get("/result-entry")
def result_entry():
    service = get_service()
    events = [dict(row) for row in service.list_events()]
    athletes = [dict(row) for row in service.list_athletes()]
    registrations = [dict(row) for row in service.list_registration_pairs()]
    teams = service.get_data_view("teams")
    recent_results = service.get_data_view("results")[:30]
    return render_template(
        "result_entry.html",
        active_page="result_entry",
        events=events,
        athletes=athletes,
        registrations=registrations,
        teams=teams,
        recent_results=recent_results,
    )


@main_bp.get("/notice-center")
def notice_center():
    service = get_service()
    events = [dict(row) for row in service.list_events()]
    notice_templates = service.list_notice_templates(current_app.config["NOTICE_TEMPLATE_DIR"])
    report_env = service.get_report_environment_settings()
    return render_template(
        "notice_center.html",
        active_page="notice_center",
        events=events,
        notice_templates=notice_templates,
        report_env=report_env,
    )


@main_bp.get("/athlete-ops")
def athlete_ops():
    service = get_service()
    return render_template(
        "athlete_ops.html",
        active_page="athlete_ops",
        athletes=[dict(row) for row in service.list_athletes()],
        competitive_events=[dict(row) for row in service.list_individual_events_by_category("competitive")],
        fun_events=[dict(row) for row in service.list_individual_events_by_category("fun")],
        departments=service.list_department_names(),
    )


@main_bp.get("/team-ops")
def team_ops():
    service = get_service()
    return render_template(
        "team_ops.html",
        active_page="team_ops",
        team_events=service.list_team_events(),
        departments=service.list_department_names(),
    )


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


@main_bp.post("/athlete/add")
def athlete_add():
    try:
        payload = request.get_json(silent=True) or request.form
        athlete_id = get_service().add_athlete_by_department_name(
            athlete_type=str(payload.get("athlete_type", "")).strip(),
            athlete_no=str(payload.get("athlete_no", "")).strip(),
            name=str(payload.get("name", "")).strip(),
            gender=str(payload.get("gender", "")).strip(),
            department_name=str(payload.get("department_name", "")).strip(),
            age_group=str(payload.get("age_group", "")).strip() or None,
        )
        return jsonify({"ok": True, "inserted": 1, "athlete_id": athlete_id})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/athlete/delete")
def athlete_delete():
    try:
        payload = request.get_json(silent=True) or request.form
        result = get_service().delete_athlete_by_no(
            athlete_type=str(payload.get("athlete_type", "")).strip(),
            athlete_no=str(payload.get("athlete_no", "")).strip(),
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/athlete/registration/add")
def athlete_registration_add():
    try:
        payload = request.get_json(silent=True) or request.form
        result = get_service().adjust_athlete_registration(
            athlete_type=str(payload.get("athlete_type", "")).strip(),
            athlete_no=str(payload.get("athlete_no", "")).strip(),
            event_id=int(str(payload.get("event_id", "")).strip()),
            op="add",
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/athlete/registration/remove")
def athlete_registration_remove():
    try:
        payload = request.get_json(silent=True) or request.form
        result = get_service().adjust_athlete_registration(
            athlete_type=str(payload.get("athlete_type", "")).strip(),
            athlete_no=str(payload.get("athlete_no", "")).strip(),
            event_id=int(str(payload.get("event_id", "")).strip()),
            op="remove",
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/team/add")
def team_add():
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


@main_bp.post("/team/delete")
def team_delete():
    try:
        payload = request.get_json(silent=True) or request.form
        result = get_service().delete_team(
            team_id=int(str(payload.get("team_id", "")).strip()),
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@main_bp.post("/team/member/add")
def team_member_add():
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


@main_bp.post("/team/member/remove")
def team_member_remove():
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


@main_bp.get("/api/events")
def api_events():
    return jsonify([dict(row) for row in get_service().list_events()])


@main_bp.get("/api/athletes")
def api_athletes():
    return jsonify([dict(row) for row in get_service().list_athletes()])


@main_bp.get("/data")
def data_view():
    return render_template(
        "data_center.html",
        active_page="data_center",
        data_views=DATA_VIEWS,
        department_names=get_service().list_department_names(),
    )


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


@main_bp.get("/status")
def status():
    status = get_service().get_initialization_status()
    return render_template("status.html", active_page="status", **status)


@main_bp.get("/api/init-status")
def api_init_status():
    return jsonify(get_service().get_initialization_status())
