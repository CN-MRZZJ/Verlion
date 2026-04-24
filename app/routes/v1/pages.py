from flask import current_app, jsonify, render_template

from app.services import SportsMeetService

from .common import DATA_VIEWS, get_service, site_v1_bp


@site_v1_bp.get("/")
def home():
    data = get_service().workbench_data()
    return render_template("home.html", active_page="home", **data)


@site_v1_bp.get("/pages/import-center")
def import_center():
    return render_template(
        "import_center.html",
        active_page="import_center",
    )


@site_v1_bp.get("/pages/clear-data")
def clear_data_page():
    return render_template(
        "clear_data.html",
        active_page="clear_data",
        clear_table_options=SportsMeetService.CLEAR_TABLES,
    )


@site_v1_bp.get("/pages/result-entry")
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


@site_v1_bp.get("/pages/notice-center")
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


@site_v1_bp.get("/pages/athlete-ops")
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


@site_v1_bp.get("/pages/team-ops")
def team_ops():
    service = get_service()
    return render_template(
        "team_ops.html",
        active_page="team_ops",
        team_events=service.list_team_events(),
        departments=service.list_department_names(),
    )


@site_v1_bp.get("/pages/event-progress")
def event_progress():
    return render_template(
        "event_progress.html",
        active_page="event_progress",
    )


@site_v1_bp.get("/pages/data")
def data_view():
    return render_template(
        "data_center.html",
        active_page="data_center",
        data_views=DATA_VIEWS,
        department_names=get_service().list_department_names(),
    )


@site_v1_bp.get("/pages/export-center")
def export_center():
    return render_template(
        "export_center.html",
        active_page="export_center",
        data_views=DATA_VIEWS,
        department_names=get_service().list_department_names(),
    )


@site_v1_bp.get("/pages/status")
def status():
    status = get_service().get_initialization_status()
    return render_template("status.html", active_page="status", **status)


@site_v1_bp.get("/pages/init-status")
def api_init_status():
    return jsonify(get_service().get_initialization_status())
