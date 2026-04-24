import sqlite3
from typing import Optional

from .crud import EVENTS, WhereClause


class EventRepositoryMixin:
    def insert_event(
            self,
            name: str,
            category: str,
            event_type: str,
            scoring_strategy: str,
            gender: str,
            age_group: str,
            is_individual: int,
        ) -> int:
            return self._crud_insert(
                EVENTS,
                {
                    "name": name,
                    "category": category,
                    "event_type": event_type,
                    "scoring_strategy": scoring_strategy,
                    "gender": gender,
                    "age_group": age_group,
                    "is_individual": is_individual,
                },
            )

    def event_exists(
            self,
            name: str,
            category: str,
            event_type: str,
            scoring_strategy: str,
            gender: str,
            age_group: str,
            is_individual: int,
        ) -> bool:
            return self._crud_exists(
                EVENTS,
                WhereClause(
                    """
                    name=? AND category=? AND event_type=? AND scoring_strategy=? AND gender=? AND age_group=? AND is_individual=?
                    """,
                    (name, category, event_type, scoring_strategy, gender, age_group, is_individual),
                ),
            )

    def get_event_by_id(self, event_id: int):
            return self._crud_get_by_id(EVENTS, event_id)

    def list_events(self):
            return self._crud_list(
                EVENTS,
                columns=("id", "name", "category", "event_type", "scoring_strategy", "gender", "age_group", "is_individual"),
                order_by="id",
            )

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
                    e.age_group,
                    e.is_individual,
                    COALESCE(p.record_done, 0) AS record_done,
                    COALESCE(p.print_done, 0) AS print_done,
                    COALESCE(p.updated_at, '') AS updated_at
                FROM events e
                LEFT JOIN event_progress p ON p.event_id = e.id
                ORDER BY e.id
                """
            ).fetchall()

    def upsert_event_progress(self, event_id: int, record_done: int, print_done: int) -> None:
            self.conn.execute(
                """
                INSERT INTO event_progress(event_id, record_done, print_done, updated_at)
                VALUES(?,?,?,datetime('now'))
                ON CONFLICT(event_id) DO UPDATE SET
                    record_done=excluded.record_done,
                    print_done=excluded.print_done,
                    updated_at=datetime('now')
                """,
                (event_id, record_done, print_done),
            )

    def list_individual_events_by_category(self, category: str):
            return self._crud_list(
                EVENTS,
                columns=("id", "name", "category", "gender", "age_group", "is_individual"),
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
            age_group: str,
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
            if age_group:
                where.append("age_group = ?")
                params.append(age_group)
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
                    "age_group": "age_group",
                    "is_individual": "is_individual",
                    "scoring_strategy": "scoring_strategy",
                },
                "id DESC",
            )
            count_sql = f"SELECT COUNT(*) AS c FROM events WHERE {where_sql}"
            data_sql = f"""
                SELECT id, name, category, event_type, gender, age_group, is_individual
                , scoring_strategy
                FROM events
                WHERE {where_sql}
                ORDER BY {order_sql}
            """
            return self._paged_query(count_sql, data_sql, tuple(params), page, page_size)
