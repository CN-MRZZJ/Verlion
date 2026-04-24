from flask import jsonify, request, Response

from .common import api_v1_bp, get_service


@api_v1_bp.get("/exports/<view>")
def export_view(view: str):
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
