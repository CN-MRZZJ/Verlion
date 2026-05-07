import sqlite3
from typing import Optional

from .crud import EVENTS, HEATS_CONFIG, WhereClause


class EventRepositoryMixin:
    def upsert_heats_config(self, event_id: int, heat_rounds: int) -> None:
        self._crud_upsert(
            HEATS_CONFIG,
            {"event_id": event_id, "heat_rounds": heat_rounds},
            conflict_columns=("event_id",),
            update_columns=("heat_rounds",),
        )

    def get_heats_config(self, event_id: int):
        return self._crud_get_by_id(HEATS_CONFIG, event_id)
    def insert_event(
            self,
            name: str,
            category: str,
            event_type: str,
            scoring_strategy: str,
            gender: str,
            group: str,
            is_individual: int,
            competition_format: str = "heats",
        ) -> int:
            return self._crud_insert(
                EVENTS,
                {
                    "name": name,
                    "category": category,
                    "event_type": event_type,
                    "scoring_strategy": scoring_strategy,
                    "gender": gender,
                    "group": group,
                    "is_individual": is_individual,
                    "competition_format": competition_format,
                },
            )

    def event_exists(
            self,
            name: str,
            category: str,
            event_type: str,
            scoring_strategy: str,
            gender: str,
            group: str,
            is_individual: int,
            competition_format: str = "heats",
        ) -> bool:
            return self._crud_exists(
                EVENTS,
                WhereClause(
                    """
                    name=? AND category=? AND event_type=? AND scoring_strategy=? AND gender=? AND "group"=? AND is_individual=? AND competition_format=?
                    """,
                    (name, category, event_type, scoring_strategy, gender, group, is_individual, competition_format),
                ),
            )

    def get_event_by_id(self, event_id: int):
            return self._crud_get_by_id(EVENTS, event_id)

    def list_events(self):
            return self.conn.execute(
                """
                SELECT
                    e.id,
                    e.name,
                    e.category,
                    e.event_type,
                    e.scoring_strategy,
                    e.gender,
                    e."group",
                    e.is_individual,
                    e.competition_format,
                    COALESCE(hc.heat_rounds, 1) AS heat_rounds,
                    COUNT(ar.id) AS registration_count
                FROM events e
                LEFT JOIN heats_config hc ON hc.event_id = e.id
                LEFT JOIN athlete_registrations ar ON ar.event_id = e.id
                GROUP BY e.id
                ORDER BY e.id
                """
            ).fetchall()

    def list_events_with_progress(self):
            return self.conn.execute(
                """
                SELECT
                    e.id,
                    e.name,
                    e.category,
                    e.event_type,
                    e.scoring_strategy,
                    e.gender,
                    e."group",
                    e.is_individual,
                    e.competition_format,
                    COALESCE(p.checkin_done, 0) AS checkin_done,
                    COALESCE(p.competition_done, 0) AS competition_done,
                    COALESCE(p.record_done, 0) AS record_done,
                    COALESCE(p.publish_done, 0) AS publish_done,
                    COALESCE(p.updated_at, '') AS updated_at,
                    COALESCE(hc.heat_rounds, 1) AS heat_rounds,
                    COUNT(ar.id) AS registration_count
                FROM events e
                LEFT JOIN event_progress p ON p.event_id = e.id
                LEFT JOIN heats_config hc ON hc.event_id = e.id
                LEFT JOIN athlete_registrations ar ON ar.event_id = e.id
                GROUP BY e.id
                ORDER BY e.id
                """
            ).fetchall()

    def upsert_event_progress(self, event_id: int, checkin_done: int, competition_done: int, record_done: int, publish_done: int) -> None:
            self.conn.execute(
                """
                INSERT INTO event_progress(event_id, checkin_done, competition_done, record_done, publish_done, updated_at)
                VALUES(?,?,?,?,?,datetime('now', '+08:00'))
                ON CONFLICT(event_id) DO UPDATE SET
                    checkin_done=excluded.checkin_done,
                    competition_done=excluded.competition_done,
                    record_done=excluded.record_done,
                    publish_done=excluded.publish_done,
                    updated_at=datetime('now', '+08:00')
                """,
                (event_id, checkin_done, competition_done, record_done, publish_done),
            )

    def list_individual_events_by_category(self, category: str):
            return self._crud_list(
                EVENTS,
                columns=("id", "name", "category", "gender", "group", "is_individual"),
                where=WhereClause("category=? AND is_individual=1", (category,)),
                order_by="id",
            )

    def events_count(self) -> int:
            return self._crud_count(EVENTS)

    def page_events(
            self,
            page: int,
            page_size: int,
            keyword: str,
            gender: str,
            group: str,
            category: str,
            scoring_strategy: str,
            sort_by: str = "",
            sort_dir: str = "desc",
        ):
            where = ["1=1"]
            params: list = []
            if keyword:
                where.append("(name LIKE ? OR event_type LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            if category:
                where.append("category = ?")
                params.append(category)
            if gender:
                where.append("gender = ?")
                params.append(gender)
            if group:
                where.append('"group" = ?')
                params.append(group)
            if scoring_strategy:
                where.append("scoring_strategy = ?")
                params.append(scoring_strategy)
            where_sql = " AND ".join(where)
            order_sql = self._resolve_order(
                sort_by,
                sort_dir,
                {
                    "id": "id",
                    "name": "name",
                    "category": "category",
                    "event_type": "event_type",
                    "gender": "gender",
                    "group": "group",
                    "is_individual": "is_individual",
                    "scoring_strategy": "scoring_strategy",
                },
                "id DESC",
            )
            count_sql = f"SELECT COUNT(*) AS c FROM events WHERE {where_sql}"
            data_sql = f"""
                SELECT id, name, category, event_type, gender, "group", is_individual
                , scoring_strategy, competition_format
                FROM events
                WHERE {where_sql}
                ORDER BY {order_sql}
            """
            return self._paged_query(count_sql, data_sql, tuple(params), page, page_size)
