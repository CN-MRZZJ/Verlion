import csv
import io

from app.models import SportsRepository


class MeetViewMixin:
    def list_events(self):
        with self.db.connect() as conn:
            return SportsRepository(conn).list_events()

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
            elif view_name == "standings":
                rows = repo.standings()
            elif view_name == "participation":
                rows = repo.participation_rate()
            else:
                raise ValueError(f"不支持的数据视图: {view_name}")
            items = [dict(row) for row in rows]
            if view_name == "results":
                self._format_result_rows_performance(items)
            return items

    def get_grid_page(
        self,
        view_name: str,
        page: int,
        page_size: int,
        keyword: str = "",
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
                total, rows = repo.page_teams(page, page_size, keyword, department_name, sort_by, sort_dir)
            elif view_name == "registrations":
                total, rows = repo.page_registrations(page, page_size, keyword, department_name, sort_by, sort_dir)
            elif view_name == "results":
                total, rows = repo.page_results(
                    page, page_size, keyword, department_name, category, scoring_strategy, sort_by, sort_dir
                )
            elif view_name == "standings":
                total, rows = repo.page_standings(page, page_size, sort_by, sort_dir)
            elif view_name == "participation":
                total, rows = repo.page_participation(page, page_size, sort_by, sort_dir)
            else:
                raise ValueError(f"不支持的数据视图: {view_name}")

            items = [dict(r) for r in rows]
            if view_name == "results":
                self._format_result_rows_performance(items)
            return {
                "view": view_name,
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
                "sort_by": sort_by,
                "sort_dir": sort_dir,
                "columns": list(items[0].keys()) if items else [],
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
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        for row in items:
            writer.writerow(row)
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
