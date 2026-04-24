class MeetAdminMixin:
    def clear_table_data(
        self,
        requested_tables: list[str],
        confirm_text: str,
        confirm_code: str,
        acknowledged: bool,
    ) -> dict:
        selected = sorted({t for t in requested_tables if t in self.CLEAR_TABLES})
        if not selected:
            raise ValueError("请至少选择一张表")
        if not acknowledged:
            raise ValueError("请先勾选确认选项")
        if (confirm_text or "").strip().upper() != "DELETE":
            raise ValueError("请正确输入确认口令 DELETE")
        expected_code = f"CLEAR-{len(selected)}"
        if (confirm_code or "").strip().upper() != expected_code:
            raise ValueError(f"校验码错误，应为 {expected_code}")

        counts: dict[str, int] = {k: 0 for k in self.CLEAR_TABLES}

        def _exec_delete(conn, table_key: str, sql: str, params: tuple = ()) -> None:
            cur = conn.execute(sql, params)
            delta = cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
            counts[table_key] += delta

        with self.db.connect() as conn:
            clear_settings = "settings" in selected
            clear_departments = "departments" in selected
            clear_events = "events" in selected
            clear_event_progress = "event_progress" in selected
            clear_athletes = "athletes" in selected or clear_departments
            clear_teams = "teams" in selected or clear_events or clear_departments
            clear_team_members = "team_members" in selected
            clear_regs = "athlete_registrations" in selected
            clear_results = "results" in selected

            if clear_departments:
                _exec_delete(conn, "results", "DELETE FROM results")
                _exec_delete(conn, "athlete_registrations", "DELETE FROM athlete_registrations")
                _exec_delete(conn, "team_members", "DELETE FROM team_members")
                _exec_delete(conn, "teams", "DELETE FROM teams")
                _exec_delete(conn, "event_progress", "DELETE FROM event_progress")
                _exec_delete(conn, "athletes", "DELETE FROM athletes")
                _exec_delete(conn, "departments", "DELETE FROM departments")
            else:
                if clear_events:
                    _exec_delete(conn, "results", "DELETE FROM results")
                    _exec_delete(conn, "athlete_registrations", "DELETE FROM athlete_registrations")
                    _exec_delete(conn, "team_members", "DELETE FROM team_members")
                    _exec_delete(conn, "teams", "DELETE FROM teams")
                    _exec_delete(conn, "event_progress", "DELETE FROM event_progress")
                    _exec_delete(conn, "events", "DELETE FROM events")
                else:
                    if clear_teams:
                        _exec_delete(conn, "results", "DELETE FROM results WHERE team_id IS NOT NULL")
                        _exec_delete(conn, "team_members", "DELETE FROM team_members")
                        _exec_delete(conn, "teams", "DELETE FROM teams")
                    elif clear_team_members:
                        _exec_delete(conn, "team_members", "DELETE FROM team_members")

                    if clear_athletes:
                        _exec_delete(conn, "results", "DELETE FROM results WHERE athlete_ref_id IS NOT NULL")
                        _exec_delete(conn, "athlete_registrations", "DELETE FROM athlete_registrations")
                        _exec_delete(conn, "team_members", "DELETE FROM team_members")
                        _exec_delete(conn, "athletes", "DELETE FROM athletes")

                    if clear_results:
                        _exec_delete(conn, "results", "DELETE FROM results")
                    if clear_regs:
                        _exec_delete(conn, "athlete_registrations", "DELETE FROM athlete_registrations")
                    if clear_team_members and not clear_teams:
                        _exec_delete(conn, "team_members", "DELETE FROM team_members")
                    if clear_event_progress:
                        _exec_delete(conn, "event_progress", "DELETE FROM event_progress")

            if clear_settings:
                _exec_delete(conn, "settings", "DELETE FROM settings")

            conn.commit()

        affected = {k: v for k, v in counts.items() if v > 0}
        return {
            "requested_tables": selected,
            "expected_code": expected_code,
            "deleted_rows": affected,
        }
