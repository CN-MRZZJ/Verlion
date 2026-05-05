import csv
import io

from app.models.repositories import SportsRepository
from app.rules import athlete_age_group_label, event_age_group_label


class MeetViewMixin:
    RESULT_DETAIL_COLUMNS = [
        "id",
        "event_id",
        "event_full_name",
        "event_name",
        "category",
        "event_type",
        "scoring_strategy",
        "event_gender",
        "age_group",
        "is_individual",
        "result_type",
        "athlete_type",
        "athlete_ref_id",
        "athlete_no",
        "athlete_name",
        "athlete_gender",
        "team_id",
        "team_name",
        "team_member_athlete_nos",
        "team_member_names",
        "team_member_genders",
        "department_name",
        "rank",
        "points",
        "performance",
        "entered_by",
        "created_at",
    ]

    def _export_header_alias(self, key: str) -> str:
        mapping = {
            "id": "ID",
            "event_id": "项目ID",
            "event_full_name": "项目全名",
            "athlete_ref_id": "运动员ID",
            "athlete_no": "运动员号",
            "athlete_name": "运动员姓名",
            "athlete_gender": "运动员性别",
            "team_id": "队伍ID",
            "team_name": "队伍名称",
            "team_member_athlete_nos": "队伍成员运动员号",
            "team_member_names": "队伍成员姓名",
            "team_member_genders": "队伍成员性别",
            "department_name": "单位",
            "name": "名称",
            "event_name": "项目名称",
            "category": "类别",
            "event_type": "项目类型",
            "gender": "性别",
            "event_gender": "项目性别",
            "age_group": "组别",
            "is_individual": "项目属性",
            "scoring_strategy": "计分策略",
            "result_type": "成绩对象",
            "athlete_type": "运动员类型",
            "target_name": "对象名称",
            "rank": "名次",
            "points": "积分",
            "performance": "成绩",
            "entered_by": "录入人",
            "created_at": "创建时间",
            "total_members": "总人数",
            "active_members": "参赛人数",
            "participation_percent": "参赛率(%)",
            "total_points": "总积分",
        }
        return mapping.get(key, key)

    def _export_readable_value(self, key: str, value, age_group_scope: str = "event"):
        if value is None:
            return ""
        text = str(value)
        if key == "category":
            return {"competitive": "竞技", "fun": "趣味"}.get(text, text)
        if key == "event_type":
            return {"track": "径赛", "field": "田赛", "fun": "趣味"}.get(text, text)
        if key in {"gender", "event_gender", "athlete_gender"}:
            return {"male": "男", "female": "女", "mixed": "混合"}.get(text, text)
        if key == "age_group":
            if age_group_scope == "athlete":
                return athlete_age_group_label(text) or text
            return event_age_group_label(text) or text
        if key == "is_individual":
            return "个人" if text in {"1", "True", "true"} else ("团体" if text in {"0", "False", "false"} else text)
        if key == "scoring_strategy":
            return {
                "time": "time(计时)",
                "length": "length(计距)",
                "count": "count(计数)",
                "count_miss": "count_miss(个数/失误)",
            }.get(text, text)
        if key == "result_type":
            return {"athlete": "个人", "team": "团体"}.get(text, text)
        if key == "athlete_type":
            return {"competitive": "竞技", "fun": "趣味"}.get(text, text)
        if key in {"checkin_done", "competition_done", "record_done", "publish_done"}:
            return "是" if text in {"1", "True", "true"} else ("否" if text in {"0", "False", "false"} else text)
        return value

    def _readable_item(self, item: dict, age_group_scope: str = "event") -> dict:
        out = {}
        for k, v in item.items():
            out[k] = self._export_readable_value(k, v, age_group_scope)
        return out

    def _add_result_detail_fields(self, rows: list[dict]) -> list[dict]:
        for row in rows:
            row["event_full_name"] = self._event_display_name(
                {
                    "name": row.get("event_name", ""),
                    "gender": row.get("event_gender", ""),
                    "age_group": row.get("age_group", ""),
                }
            )
        return rows

    def list_events(self):
        with self.db.connect() as conn:
            return SportsRepository(conn).list_events()

    def list_event_progress(self) -> list[dict]:
        with self.db.connect() as conn:
            rows = [dict(r) for r in SportsRepository(conn).list_events_with_progress()]
        for row in rows:
            row["checkin_done"] = int(row.get("checkin_done", 0))
            row["competition_done"] = int(row.get("competition_done", 0))
            row["record_done"] = int(row.get("record_done", 0))
            row["publish_done"] = int(row.get("publish_done", 0))
            row["gender_text"] = self._event_gender_label(str(row.get("gender", "")))
            row["age_group_text"] = self._event_group_label(str(row.get("age_group", "")))
            row["category_text"] = "竞技" if row.get("category") == "competitive" else "趣味"
        return rows

    def set_event_progress(self, event_id: int, checkin_done: bool, competition_done: bool, record_done: bool, publish_done: bool) -> dict:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            event = repo.get_event_by_id(event_id)
            if not event:
                raise ValueError(f"项目不存在: {event_id}")
            repo.upsert_event_progress(
                event_id=event_id,
                checkin_done=1 if checkin_done else 0,
                competition_done=1 if competition_done else 0,
                record_done=1 if record_done else 0,
                publish_done=1 if publish_done else 0,
            )
            conn.commit()
        return {
            "event_id": event_id,
            "checkin_done": 1 if checkin_done else 0,
            "competition_done": 1 if competition_done else 0,
            "record_done": 1 if record_done else 0,
            "publish_done": 1 if publish_done else 0,
        }

    def list_registration_pairs(self):
        with self.db.connect() as conn:
            return SportsRepository(conn).list_registration_pairs()

    def standings(self):
        with self.db.connect() as conn:
            return SportsRepository(conn).standings()

    def participation_rate(self):
        with self.db.connect() as conn:
            return SportsRepository(conn).participation_rate()

    def dashboard_summary(self) -> dict:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            recent_results = [dict(r) for r in repo.recent_results(10)]
            self._format_result_rows_performance(recent_results)
            return {
                "event_count": repo.events_count(),
                "dept_count": repo.departments_count(),
                "athlete_count": repo.athletes_count(),
                "standings": repo.standings()[:10],
                "recent_results": recent_results,
            }

    def workbench_data(self) -> dict:
        summary = self.dashboard_summary()
        status = self.get_initialization_status()
        alerts = []
        if not status["completed"]:
            alerts.append("系统初始化未完成，请先设置比赛日期并导入项目。")
        if summary["athlete_count"] == 0:
            alerts.append("暂无运动员数据，建议尽快导入名单。")
        return {
            **summary,
            "init_completed": status["completed"],
            "alerts": alerts,
        }

    def list_department_names(self) -> list[str]:
        with self.db.connect() as conn:
            rows = SportsRepository(conn).list_departments()
            return [row["name"] for row in rows]

    def get_data_view(self, view_name: str) -> list[dict]:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            if view_name == "events":
                rows = repo.list_events()
            elif view_name == "athletes":
                rows = repo.list_athletes_with_department()
            elif view_name == "departments":
                rows = repo.list_departments()
            elif view_name == "teams":
                rows = repo.list_teams_with_details()
            elif view_name == "registrations":
                rows = repo.list_registrations_with_details()
            elif view_name == "results":
                rows = repo.list_results_with_details()
            elif view_name == "result_details":
                rows = repo.list_result_details()
            elif view_name == "standings":
                rows = repo.standings()
            elif view_name == "participation":
                rows = repo.participation_rate()
            else:
                raise ValueError(f"不支持的数据视图: {view_name}")
            items = [dict(row) for row in rows]
            if view_name in {"results", "result_details"}:
                self._format_result_rows_performance(items)
            if view_name == "result_details":
                self._add_result_detail_fields(items)
            return items

    def get_grid_page(
        self,
        view_name: str,
        page: int,
        page_size: int,
        keyword: str = "",
        event_id: str = "",
        department_name: str = "",
        gender: str = "",
        age_group: str = "",
        category: str = "",
        scoring_strategy: str = "",
        sort_by: str = "",
        sort_dir: str = "desc",
    ) -> dict:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            if view_name == "events":
                total, rows = repo.page_events(
                    page, page_size, keyword, gender, age_group, category, scoring_strategy, sort_by, sort_dir
                )
            elif view_name == "athletes":
                total, rows = repo.page_athletes(
                    page, page_size, keyword, department_name, gender, age_group, sort_by, sort_dir
                )
            elif view_name == "departments":
                total, rows = repo.page_departments(page, page_size, keyword, sort_by, sort_dir)
            elif view_name == "teams":
                total, rows = repo.page_teams(
                    page,
                    page_size,
                    keyword,
                    department_name,
                    gender,
                    age_group,
                    category,
                    scoring_strategy,
                    sort_by,
                    sort_dir,
                )
            elif view_name == "registrations":
                total, rows = repo.page_registrations(
                    page,
                    page_size,
                    keyword,
                    department_name,
                    gender,
                    age_group,
                    category,
                    scoring_strategy,
                    sort_by,
                    sort_dir,
                )
            elif view_name == "results":
                total, rows = repo.page_results(
                    page,
                    page_size,
                    keyword,
                    event_id,
                    department_name,
                    gender,
                    age_group,
                    category,
                    scoring_strategy,
                    sort_by,
                    sort_dir,
                )
            elif view_name == "result_details":
                total, rows = repo.page_result_details(
                    page,
                    page_size,
                    keyword,
                    event_id,
                    department_name,
                    gender,
                    age_group,
                    category,
                    scoring_strategy,
                    sort_by,
                    sort_dir,
                )
            elif view_name == "standings":
                total, rows = repo.page_standings(page, page_size, keyword, sort_by, sort_dir)
            elif view_name == "participation":
                total, rows = repo.page_participation(page, page_size, keyword, sort_by, sort_dir)
            else:
                raise ValueError(f"不支持的数据视图: {view_name}")

            items = [dict(r) for r in rows]
            if view_name in {"results", "result_details"}:
                self._format_result_rows_performance(items)
            if view_name == "result_details":
                self._add_result_detail_fields(items)
                items = [{col: item.get(col, "") for col in self.RESULT_DETAIL_COLUMNS} for item in items]
            age_group_scope = "athlete" if view_name == "athletes" else "event"
            items = [self._readable_item(i, age_group_scope) for i in items]
            return {
                "view": view_name,
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
                "sort_by": sort_by,
                "sort_dir": sort_dir,
                "columns": self.RESULT_DETAIL_COLUMNS if view_name == "result_details" else (list(items[0].keys()) if items else []),
                "items": items,
            }

    def export_grid_csv(
        self,
        view_name: str,
        keyword: str = "",
        department_name: str = "",
        gender: str = "",
        age_group: str = "",
        category: str = "",
        scoring_strategy: str = "",
    ) -> str:
        first = self.get_grid_page(
            view_name=view_name,
            page=1,
            page_size=100000,
            keyword=keyword,
            department_name=department_name,
            gender=gender,
            age_group=age_group,
            category=category,
            scoring_strategy=scoring_strategy,
        )
        columns = first["columns"]
        items = first["items"]
        headers = [self._export_header_alias(c) for c in columns]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for row in items:
            readable_row = {}
            for col, header in zip(columns, headers):
                age_group_scope = "athlete" if view_name == "athletes" else "event"
                readable_row[header] = self._export_readable_value(col, row.get(col), age_group_scope)
            writer.writerow(readable_row)
        return output.getvalue()

    def get_initialization_status(self) -> dict:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            meet_date_iso = repo.get_meet_date_iso()
            event_count = repo.events_count()
            department_count = repo.departments_count()
            athlete_count = repo.athletes_count()

            checks = [
                {
                    "key": "meet_date",
                    "label": "比赛日期已设置",
                    "ok": bool(meet_date_iso),
                    "detail": meet_date_iso or "未设置",
                },
                {
                    "key": "events",
                    "label": "项目数据已导入",
                    "ok": event_count > 0,
                    "detail": f"{event_count} 个项目",
                },
            ]

            completed = all(item["ok"] for item in checks)
            return {
                "completed": completed,
                "checks": checks,
                "summary": {
                    "event_count": event_count,
                    "department_count": department_count,
                    "athlete_count": athlete_count,
                },
            }
