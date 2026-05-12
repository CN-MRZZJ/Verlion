import os
from pathlib import Path


class Config:
    BASE_DIR = Path(__file__).resolve().parent
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DATABASE_PATH = os.getenv("SPORTS_MEET_DB", str(BASE_DIR / "sports_meet.db"))
    CSV_TEMPLATE_DIR = str(BASE_DIR / "app" / "static" / "csv")
    NOTICE_TEMPLATE_DIR = str(BASE_DIR / "app" / "static" / "notice_templates")
    GROUPED_RESULT_LAYOUT = str(BASE_DIR / "app" / "static" / "notice_templates" / "grouped_result_layout.json")
    FULL_RESULT_LAYOUT = str(BASE_DIR / "app" / "static" / "notice_templates" / "full_result_layout.json")
    DEFAULT_NOTICE_TEMPLATE = "heat_notice_template.xlsx"
