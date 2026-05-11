from app.grouping.schema import GroupingOutput, AdvancementInput, Participant
from app.grouping.advancement import get_advancement

_ROUND_NAMES = {
    1: ["决赛"],
    2: ["预赛", "决赛"],
    3: ["预赛", "半决赛", "决赛"],
    4: ["预赛", "复赛", "半决赛", "决赛"],
}


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

    def swap_or_move_heat_entry(self, entry_id: int, target_heat_id: int, target_lane: int | None) -> None:
        def _write(repo):
            source = repo.get_heat_entry(entry_id)
            if not source:
                raise ValueError(f"道次记录不存在: {entry_id}")

            if target_lane is not None:
                existing = repo.find_entry_at(target_heat_id, target_lane)
                if existing and int(existing["id"]) != entry_id:
                    repo.move_heat_entry(int(existing["id"]), int(source["heat_id"]), int(source["lane"]) if source["lane"] is not None else None)

            repo.move_heat_entry(entry_id, target_heat_id, target_lane)

        self._repo_write(_write)

    def set_heats_config(self, event_id: int, heat_rounds: int) -> None:
        def _write(repo):
            repo.upsert_heats_config(event_id, heat_rounds)

        self._repo_write(_write)

    def advance_to_next_round(self, event_id: int, current_round_id: int, strategy: str, lanes_per_heat: int, algorithm: str = "seeded", params: dict | None = None) -> dict:
        def _write(repo):
            hc = repo.get_heats_config(event_id)
            heat_rounds = int(hc["heat_rounds"]) if hc else 1
            next_round_number = current_round_id + 1
            if next_round_number > heat_rounds:
                raise ValueError(f"已是最后一轮（共 {heat_rounds} 轮）")

            results = [dict(r) for r in repo.list_results_grouped_by_heat(event_id, current_round_id)]
            if not results:
                raise ValueError("当前轮次没有成绩，无法晋级")

            adv = get_advancement(strategy)
            input_ = AdvancementInput(event_id=event_id, results=results, params=params or {})
            output = adv.run(input_)
            if not output.qualified:
                raise ValueError("没有符合条件的晋级者")

            names = _ROUND_NAMES.get(heat_rounds, _ROUND_NAMES[1])
            next_round_name = names[next_round_number - 1]

            # Build performance index from current round results
            perf_by_athlete: dict[int, float] = {}
            for r in results:
                aid = r.get("athlete_ref_id")
                perf = r.get("performance")
                if aid and perf is not None:
                    try:
                        perf_by_athlete[int(aid)] = float(perf)
                    except (ValueError, TypeError):
                        pass

            qualified_participants = []
            for q in output.qualified:
                if q.athlete_ref_id is not None:
                    athlete = repo.get_athlete_by_id(q.athlete_type or "", q.athlete_ref_id)
                    seed = perf_by_athlete.get(q.athlete_ref_id)
                    qualified_participants.append(Participant(
                        athlete_id=q.athlete_ref_id,
                        name=str(athlete["name"]) if athlete else "",
                        athlete_type=q.athlete_type or "",
                        department=str(athlete.get("department_name", "")),
                        seed_mark=seed,
                    ))
                # team support tbd

            from app.grouping import get_algorithm
            from app.grouping.schema import GroupingConfig, GroupingInput
            algo = get_algorithm(algorithm)
            input2 = GroupingInput(
                event_id=event_id,
                participants=qualified_participants,
                config=GroupingConfig(lanes_per_heat=lanes_per_heat, algorithm=algorithm),
                heat_rounds=1,
            )
            output2 = algo.run(input2)
            output2.stages[0].stage_number = next_round_number
            output2.stages[0].stage_name = next_round_name

            # Clear existing rounds from this number onwards
            existing_rounds = repo.list_rounds(event_id)
            for r in existing_rounds:
                if int(r["round_number"]) >= next_round_number:
                    repo.clear_round_data(r["id"])

            # Insert new round with heats (reuse save logic but avoid full clear)
            round_id = repo.insert_round(event_id, next_round_number, next_round_name)
            for heat in output2.stages[0].heats:
                heat_id = repo.insert_heat(round_id, heat.heat_number, heat.heat_name)
                for lane in heat.lanes:
                    repo.insert_heat_entry(heat_id, lane.athlete_type, lane.athlete_id, None, lane.lane)

            return {
                "round_id": next_round_number,
                "round_name": next_round_name,
                "qualified": len(output.qualified),
            }

        return self._repo_write(_write)
