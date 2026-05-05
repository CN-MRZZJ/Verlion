from .crud import EVENT_TYPES, WhereClause


class EventTypeRepositoryMixin:
    def insert_event_type(self, code: str, name: str, scoring_strategy: str) -> str:
        self._crud_insert(EVENT_TYPES, {"code": code, "name": name, "scoring_strategy": scoring_strategy})
        return code

    def get_event_type(self, code: str):
        return self._crud_get_by_id(EVENT_TYPES, code)

    def list_event_types(self):
        return self._crud_list(EVENT_TYPES, order_by="code")

    def update_event_type(self, code: str, name: str | None = None, scoring_strategy: str | None = None):
        values = {}
        if name is not None:
            values["name"] = name
        if scoring_strategy is not None:
            values["scoring_strategy"] = scoring_strategy
        if values:
            self._crud_update_by_id(EVENT_TYPES, code, values)

    def delete_event_type(self, code: str) -> int:
        return self._crud_delete_by_id(EVENT_TYPES, code)

    def count_events_by_event_type(self, code: str) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS c FROM events WHERE event_type=?",
            (code,),
        ).fetchone()
        return int(row["c"]) if row else 0
