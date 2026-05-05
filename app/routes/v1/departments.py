from flask import jsonify, request

from .common import api_v1_bp, get_service


@api_v1_bp.get("/departments")
def list_departments():
    try:
        page = int(request.args.get("page", "1"))
        page_size = int(request.args.get("page_size", "20"))
        keyword = request.args.get("keyword", "").strip()
        sort_by = request.args.get("sort_by", "").strip()
        sort_dir = request.args.get("sort_dir", "desc").strip()
        result = get_service().query_departments(
            page=page, page_size=page_size, keyword=keyword, sort_by=sort_by, sort_dir=sort_dir,
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.post("/departments")
def create_department():
    try:
        payload = request.get_json(silent=True) or request.form
        name = str(payload.get("name", "")).strip()
        total_members = int(payload.get("total_members", 0))
        dept_id = get_service().add_department(name=name, total_members=total_members)
        return jsonify({"ok": True, "inserted": 1, "department_id": dept_id})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.put("/departments/<int:department_id>")
def update_department(department_id: int):
    try:
        payload = request.get_json(silent=True) or request.form
        name = str(payload.get("name", "")).strip()
        total_members = payload.get("total_members")
        total_members = int(total_members) if total_members is not None and str(total_members).strip() != "" else None
        get_service().update_department(department_id=department_id, name=name, total_members=total_members)
        return jsonify({"ok": True, "department_id": department_id})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.delete("/departments/<int:department_id>")
def delete_department(department_id: int):
    try:
        result = get_service().delete_department(department_id=department_id)
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@api_v1_bp.post("/departments/delete")
def delete_department_compat():
    try:
        payload = request.get_json(silent=True) or request.form
        department_id = int(str(payload.get("department_id", "")).strip())
        result = get_service().delete_department(department_id=department_id)
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
