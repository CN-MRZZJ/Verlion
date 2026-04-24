import csv
import io

from flask import Blueprint, current_app, request

from app.services import SportsMeetService

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")
site_v1_bp = Blueprint("site_v1", __name__, url_prefix="")  # 站点相关的路由，前缀留空

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

__all__ = ["api_v1_bp", "site_v1_bp", "DATA_VIEWS", "get_service", "parse_csv_upload"]
