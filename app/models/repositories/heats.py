from .crud import HEATS, HEAT_ENTRIES, ROUNDS, WhereClause


class HeatsRepositoryMixin:
    def insert_round(self, event_id: int, round_number: int, round_name: str, advancement_rule: str | None = None) -> int:
        return self._crud_insert(ROUNDS, {
            "event_id": event_id,
            "round_number": round_number,
            "round_name": round_name,
            "advancement_rule": advancement_rule,
        })

    def list_rounds(self, event_id: int):
        return self._crud_list(ROUNDS, where=WhereClause("event_id=?", (event_id,)), order_by="round_number")

    def insert_heat(self, round_id: int, heat_number: int, heat_name: str) -> int:
        return self._crud_insert(HEATS, {
            "round_id": round_id,
            "heat_number": heat_number,
            "heat_name": heat_name,
        })

    def list_heats(self, round_id: int):
        return self._crud_list(HEATS, where=WhereClause("round_id=?", (round_id,)), order_by="heat_number")

    def insert_heat_entry(self, heat_id: int, athlete_type: str | None, athlete_ref_id: int | None, team_id: int | None, lane: int | None) -> int:
        return self._crud_insert(HEAT_ENTRIES, {
            "heat_id": heat_id,
            "athlete_type": athlete_type,
            "athlete_ref_id": athlete_ref_id,
            "team_id": team_id,
            "lane": lane,
        })

    def list_heat_entries(self, heat_id: int):
        return self.conn.execute(
            """
            SELECT he.*, a.name AS athlete_name, a.athlete_no, a."group", d.name AS department_name
            FROM heat_entries he
            LEFT JOIN athletes a ON a.id = he.athlete_ref_id
            LEFT JOIN departments d ON d.id = a.department_id
            WHERE he.heat_id = ?
            ORDER BY he.lane
            """,
            (heat_id,),
        ).fetchall()

    def update_heat_entry(self, entry_id: int, lane: int | None) -> None:
        self._crud_update_by_id(HEAT_ENTRIES, entry_id, {"lane": lane})

    def get_heat_entry(self, entry_id: int):
        return self._crud_get_by_id(HEAT_ENTRIES, entry_id)

    def find_entry_at(self, heat_id: int, lane: int):
        return self._crud_get_one(HEAT_ENTRIES, WhereClause("heat_id=? AND lane=?", (heat_id, lane)))

    def move_heat_entry(self, entry_id: int, heat_id: int, lane: int | None) -> None:
        self._crud_update_by_id(HEAT_ENTRIES, entry_id, {"heat_id": heat_id, "lane": lane})

    def clear_round_data(self, round_id: int) -> None:
        heat_rows = self.conn.execute("SELECT id FROM heats WHERE round_id=?", (round_id,)).fetchall()
        heat_ids = [int(h["id"]) for h in heat_rows]
        if heat_ids:
            placeholders = ", ".join("?" for _ in heat_ids)
            self.conn.execute(f"DELETE FROM heat_entries WHERE heat_id IN ({placeholders})", tuple(heat_ids))
            self.conn.execute(f"DELETE FROM heats WHERE id IN ({placeholders})", tuple(heat_ids))
        self.conn.execute("DELETE FROM rounds WHERE id=?", (round_id,))

    def clear_heats_for_event(self, event_id: int) -> None:
        round_ids = [
            int(r["id"])
            for r in self.conn.execute("SELECT id FROM rounds WHERE event_id=?", (event_id,)).fetchall()
        ]
        if not round_ids:
            return
        placeholders = ", ".join("?" for _ in round_ids)
        heat_rows = self.conn.execute(
            f"SELECT id FROM heats WHERE round_id IN ({placeholders})",
            tuple(round_ids),
        ).fetchall()
        heat_ids = [int(h["id"]) for h in heat_rows]
        if heat_ids:
            h_placeholders = ", ".join("?" for _ in heat_ids)
            self.conn.execute(f"DELETE FROM heat_entries WHERE heat_id IN ({h_placeholders})", tuple(heat_ids))
        self.conn.execute(f"DELETE FROM heats WHERE round_id IN ({placeholders})", tuple(round_ids))
        self.conn.execute("DELETE FROM rounds WHERE event_id=?", (event_id,))
