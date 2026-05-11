import os
from pathlib import Path


class Config:
    BASE_DIR = Path(__file__).resolve().parent
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DATABASE_PATH = os.getenv("SPORTS_MEET_DB", str(BASE_DIR / "sports_meet.db"))
    CSV_TEMPLATE_DIR = str(BASE_DIR / "app" / "static" / "csv")
    NOTICE_TEMPLATE_DIR = str(BASE_DIR / "app" / "static" / "notice_templates")
    NOTICE_LAYOUT_CONFIG = str(BASE_DIR / "app" / "static" / "notice_templates" / "personal_notice_layout.json")
    TEAM_NOTICE_LAYOUT_CONFIG = str(BASE_DIR / "app" / "static" / "notice_templates" / "team_notice_layout.json")
    PERSONAL_ATTEMPT_NOTICE_LAYOUT_CONFIG = str(BASE_DIR / "app" / "static" / "notice_templates" / "personal_attempt_notice_layout.json")
    TEAM_ATTEMPT_NOTICE_LAYOUT_CONFIG = str(BASE_DIR / "app" / "static" / "notice_templates" / "team_attempt_notice_layout.json")
