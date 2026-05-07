from app.grouping.schema import GroupingOutput


class MeetHeatsMixin:
    def save_grouping_output(self, output: GroupingOutput) -> None:
        def _write(repo):
            repo.clear_heats_for_event(output.event_id)
            for stage in output.stages:
                round_id = repo.insert_round(
                    output.event_id, stage.stage_number, stage.stage_name
                )
                for heat in stage.heats:
                    heat_id = repo.insert_heat(round_id, heat.heat_number, heat.heat_name)
                    for lane in heat.lanes:
                        repo.insert_heat_entry(heat_id, lane.athlete_type, lane.athlete_id, None, lane.lane)

        self._repo_write(_write)

    def get_heats_for_event(self, event_id: int) -> dict:
        def _read(repo):
            rounds = repo.list_rounds(event_id)
            result = []
            for r in rounds:
                rd = dict(r)
                heats = repo.list_heats(rd["id"])
                rd["heats"] = []
                for h in heats:
                    ht = dict(h)
                    ht["entries"] = [dict(e) for e in repo.list_heat_entries(ht["id"])]
                    rd["heats"].append(ht)
                result.append(rd)
            return {"event_id": event_id, "rounds": result}

        return self._repo_read(_read)

    def clear_heats_for_event(self, event_id: int) -> None:
        def _write(repo):
            repo.clear_heats_for_event(event_id)

        self._repo_write(_write)

    def update_heat_entry_lane(self, entry_id: int, lane: int | None) -> None:
        def _write(repo):
            repo.update_heat_entry(entry_id, lane)

        self._repo_write(_write)
