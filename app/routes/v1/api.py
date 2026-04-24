from flask import jsonify, request

from .common import api_v1_bp, get_service


@api_v1_bp.get("/datasets/<view>")
def get_dataset(view: str):
    try:
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
        service = get_service()
        data = service.get_grid_page(
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
        )
        return jsonify({"ok": True, **data})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
