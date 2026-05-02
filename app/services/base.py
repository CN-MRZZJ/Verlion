from datetime import date
import os
import re
from typing import Callable, Optional, TypeVar

from app.models.database import Database
from app.models.repositories import SportsRepository
from app.rules import event_age_group_label

T = TypeVar("T")


class MeetServiceBase:
    CLEAR_TABLES = {
        "settings": "系统设置",
        "departments": "部门",
        "events": "项目",
        "event_progress": "流程勾选",
        "athletes": "运动员",
        "teams": "队伍",
        "team_members": "队伍成员",
        "athlete_registrations": "报名记录",
        "results": "成绩记录",
        "attempts": "尝试记录",
    }
    REPORT_ENV_KEYS = [
        "date",
        "wind_direction",
        "wind_speed",
        "air_quality",
        "weather",
        "temperature_high",
        "temperature_low",
    ]

    def __init__(self, db_path: str) -> None:
        self.db = Database(db_path)

    def init_db(self) -> None:
        self.db.initialize()

    def _repo_read(self, action: Callable[[SportsRepository], T]) -> T:
        with self.db.connect() as conn:
            return action(SportsRepository(conn))

    def _repo_write(self, action: Callable[[SportsRepository], T]) -> T:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            result = action(repo)
            conn.commit()
            return result

    def set_meet_date(self, meet_date: date) -> None:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            repo.set_meet_date(meet_date.isoformat())
            conn.commit()

    def get_meet_date(self) -> date:
        with self.db.connect() as conn:
            iso = SportsRepository(conn).get_meet_date_iso()
            return date.fromisoformat(iso) if iso else date(2026, 4, 23)

    def set_report_environment_settings(self, payload: dict[str, str]) -> None:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            for key in self.REPORT_ENV_KEYS:
                val = str(payload.get(key, "")).strip()
                repo.set_setting(f"report_env.{key}", val)
            conn.commit()

    def get_report_environment_settings(self) -> dict[str, str]:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            return {
                key: str(repo.get_setting(f"report_env.{key}") or "").strip()
                for key in self.REPORT_ENV_KEYS
            }

    def list_notice_templates(self, template_dir: str) -> list[str]:
        if not os.path.isdir(template_dir):
            return []
        names: list[str] = []
        for name in os.listdir(template_dir):
            lower = name.lower()
            if lower.endswith(".xlsx") or lower.endswith(".xlsm"):
                names.append(name)
        names.sort()
        return names

    def _event_gender_label(self, gender: str) -> str:
        if gender == "male":
            return "男子"
        if gender == "female":
            return "女子"
        return "混合"

    def _event_group_label(self, age_group: str) -> str:
        return event_age_group_label(age_group) or event_age_group_label("ALL")

    def _event_display_name(self, event: dict) -> str:
        return f"{event.get('name', '')}{self._event_gender_label(str(event.get('gender', '')))}{self._event_group_label(str(event.get('age_group', '')))}"

    def _notice_title_for_event(self, event: dict, layout: Optional[dict] = None) -> str:
        title_map = (layout or {}).get("notice_title_by_event_type", {}) if isinstance(layout, dict) else {}
        event_type = str(event.get("event_type", "")).strip()
        if isinstance(title_map, dict):
            custom = str(title_map.get(event_type, "")).strip()
            if custom:
                return custom
            custom_default = str(title_map.get("default", "")).strip()
            if custom_default:
                return custom_default
        if event_type == "track":
            return "径赛成绩单"
        if event_type == "field":
            return "田赛成绩单"
        return "趣味成绩单"

    def _validate_athlete_type(self, athlete_type: str) -> str:
        if athlete_type not in {"competitive", "fun"}:
            raise ValueError("athlete_type 必须为 competitive 或 fun")
        return athlete_type

    def _expand_event_genders(self, gender_raw: str) -> list[str]:
        gender = (gender_raw or "").strip().lower()
        aliases = {
            "male": ["male"],
            "female": ["female"],
            "mixed": ["mixed"],
            "男女": ["male", "female"],
            "both": ["male", "female"],
            "all": ["male", "female"],
            "male+female": ["male", "female"],
            "male/female": ["male", "female"],
            "mf": ["male", "female"],
        }
        if gender in aliases:
            return aliases[gender]
        raise ValueError("gender 必须为 male/female/mixed，或男女合并值（男女/both/male+female/all）")

    def _parse_performance_numeric(self, strategy: str, performance: Optional[str]) -> Optional[float]:
        text = self._normalize_performance_text(strategy, performance)
        if not text:
            return None
        if strategy == "time":
            if not re.fullmatch(r"\d+(?:\.\d+)*", text):
                return None
            parts = text.split(".")
            if len(parts) <= 2:
                return float(text)
            minute = int(parts[0])
            sec_int = parts[1]
            sec_decimal = "".join(parts[2:])
            sec_val = float(sec_int + ("." + sec_decimal if sec_decimal else ""))
            return minute * 60 + sec_val
        if strategy == "length":
            if not re.fullmatch(r"\d+(?:\.\d+)*", text):
                return None
            parts = text.split(".")
            if len(parts) <= 2:
                return float(text)
            return float(parts[0] + "." + "".join(parts[1:]))
        if strategy == "count":
            if not re.fullmatch(r"\d+", text):
                return None
            return float(int(text))
        if strategy == "count_miss":
            if not re.fullmatch(r"\d+/\d+", text):
                return None
            left, right = text.split("/", 1)
            count = int(left)
            miss = int(right)
            return float(count * 1000000 - miss)
        return None

    def _normalize_performance_text(self, strategy: str, performance: Optional[str]) -> Optional[str]:
        raw = (performance or "").strip()
        if not raw:
            return None
        text = raw.replace("：", ":").replace("．", ".").replace("。", ".")
        text = re.sub(r"\s+", "", text)

        if strategy == "time":
            text = text.lower().replace("分", ".").replace("秒", "")
            text = text.replace(":", ".")
            text = text.replace("s", "")
        elif strategy == "length":
            text = text.lower().replace("米", "").replace("m", "")
            text = text.replace(":", ".")
        elif strategy == "count":
            text = text.replace("次", "").replace("个", "")
            text = text.replace(":", "")
        elif strategy == "count_miss":
            text = (
                text.replace("个", "")
                .replace("次", "")
                .replace("失误", "/")
                .replace("错误", "/")
                .replace("，", "/")
                .replace(",", "/")
                .replace(":", "/")
                .replace("：", "/")
                .replace("、", "/")
                .replace("-", "/")
            )
            text = re.sub(r"\s+", "", text)
            text = re.sub(r"[^0-9/]", "", text)
            text = re.sub(r"/+", "/", text).strip("/")

        if strategy == "count":
            text = re.sub(r"[^0-9]", "", text)
            text = text.strip()
        elif strategy == "count_miss":
            if re.fullmatch(r"\d+/\d+", text):
                pass
            elif re.fullmatch(r"\d+", text):
                text = text + "/0"
            else:
                return None
        else:
            text = re.sub(r"[^0-9.]", "", text)
            text = text.strip(".")
        return text or None

    def _format_time_seconds(self, seconds: float) -> str:
        total_cs = max(int(round(seconds * 100)), 0)
        minute = total_cs // 6000
        sec_cs = total_cs % 6000
        sec_int = sec_cs // 100
        sec_frac = sec_cs % 100
        return f"{minute:02d}:{sec_int:02d}.{sec_frac:02d}"

    def _format_performance_for_display(self, scoring_strategy: str, performance: Optional[str]) -> str:
        text = (performance or "").strip()
        if not text:
            return ""
        if scoring_strategy == "time":
            sec = self._parse_performance_numeric("time", text)
            if sec is None:
                return text
            return self._format_time_seconds(sec)
        if scoring_strategy == "length":
            meters = self._parse_performance_numeric("length", text)
            if meters is None:
                return text
            return f"{meters:.2f}m"
        if scoring_strategy == "count":
            count_val = self._parse_performance_numeric("count", text)
            if count_val is None:
                return text
            return f"{int(count_val)}个"
        if scoring_strategy == "count_miss":
            norm = self._normalize_performance_text("count_miss", text)
            if not norm or "/" not in norm:
                return text
            left, right = norm.split("/", 1)
            return f"{int(left)}个/{int(right)}次"
        return text

    def _format_result_rows_performance(self, rows: list[dict]) -> list[dict]:
        for row in rows:
            strategy = str(row.get("scoring_strategy", "")).strip()
            if strategy in {"time", "length", "count", "count_miss"}:
                row["performance"] = self._format_performance_for_display(strategy, row.get("performance"))
        return rows
