from typing import Optional

from app.rules import points_for_rank
from app.models.repositories import SportsRepository


class MeetResultMixin:
    def _auto_rank_for_result(
        self,
        repo: SportsRepository,
        event_id: int,
        scoring_strategy: str,
        performance: Optional[str],
    ) -> int:
        rows = repo.list_event_results(event_id)
        if not rows:
            return 1
        max_rank = max(int(r["rank"]) for r in rows)
        new_val = self._parse_performance_numeric(scoring_strategy, performance)
        if new_val is None:
            return max_rank + 1

        better = 0
        comparable = 0
        for row in rows:
            old_val = self._parse_performance_numeric(scoring_strategy, row["performance"])
            if old_val is None:
                continue
            comparable += 1
            if scoring_strategy == "time":
                if old_val < new_val:
                    better += 1
            else:
                if old_val > new_val:
                    better += 1
        if comparable == 0:
            return max_rank + 1
        return better + 1

    def _recalculate_event_ranks(self, repo: SportsRepository, event_id: int, scoring_strategy: str) -> None:
        rows = [dict(r) for r in repo.list_event_results(event_id)]
        if not rows:
            return
        event = repo.get_event_by_id(event_id)
        is_individual = int(event["is_individual"]) if event else 1
        tie_eps = 1e-9

        def _sort_key(item: dict):
            val = self._parse_performance_numeric(scoring_strategy, item.get("performance"))
            if val is None:
                return (1, float("inf"), int(item["id"]))
            if scoring_strategy == "time":
                return (0, val, int(item["id"]))
            return (0, -val, int(item["id"]))

        ranked = sorted(rows, key=_sort_key)
        prev_val = None
        prev_rank = 0
        for pos, row in enumerate(ranked, start=1):
            val = self._parse_performance_numeric(scoring_strategy, row.get("performance"))
            if prev_val is not None and val is not None and abs(val - prev_val) <= tie_eps:
                rank = prev_rank
            else:
                rank = pos
            repo.update_result_rank_points(int(row["id"]), rank, points_for_rank(rank, is_individual))
            prev_val = val
            prev_rank = rank

    def record_result(
        self,
        event_id: int,
        rank: Optional[int] = None,
        athlete_type: Optional[str] = None,
        athlete_ref_id: Optional[int] = None,
        athlete_no: Optional[str] = None,
        team_id: Optional[int] = None,
        performance: Optional[str] = None,
        entered_by: Optional[str] = None,
    ) -> int:
        athlete_no_text = (athlete_no or "").strip()
        if athlete_ref_id is not None and athlete_no_text:
            raise ValueError("athlete_ref_id 和 athlete_no 不能同时传")
        if athlete_ref_id is None and athlete_no_text:
            if not athlete_type:
                raise ValueError("使用 athlete_no 录入时，athlete_type 必填")
            athlete_type = self._validate_athlete_type(athlete_type)
            with self.db.connect() as conn:
                repo = SportsRepository(conn)
                found = repo.get_athlete_by_no(athlete_type, athlete_no_text)
                if not found:
                    raise ValueError(f"运动员不存在: {athlete_type}/{athlete_no_text}")
                athlete_ref_id = int(found["id"])

        has_athlete = athlete_ref_id is not None
        has_team = team_id is not None
        if has_athlete == has_team:
            raise ValueError("必须且只能传 athlete_ref_id 或 team_id 其中之一")

        if has_athlete:
            if not athlete_type:
                raise ValueError("录入个人成绩时，athlete_type 必填")
            athlete_type = self._validate_athlete_type(athlete_type)
        entered_by_text = str(entered_by or "").strip()

        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            event = repo.get_event_by_id(event_id)
            if not event:
                raise ValueError(f"比赛项目不存在: {event_id}")
            scoring_strategy = str(event["scoring_strategy"])
            normalized_performance = self._normalize_performance_text(scoring_strategy, performance)
            if performance and not normalized_performance:
                if scoring_strategy == "time":
                    raise ValueError("径赛成绩格式无效，请使用 '.' 分隔（示例：9.86 或 1.36.5）")
                if scoring_strategy == "length":
                    raise ValueError("田赛成绩格式无效，请使用米数数字并用 '.' 分隔（示例：6.23）")
                if scoring_strategy == "count":
                    raise ValueError("count 成绩必须为整数，单位个（示例：18）")
                if scoring_strategy == "count_miss":
                    raise ValueError("count_miss 成绩格式应为 个数/失误次数（示例：120/2）")
                raise ValueError("成绩格式无效，请使用数字并用 '.' 分隔")
            if scoring_strategy == "time":
                if normalized_performance:
                    sec = self._parse_performance_numeric("time", normalized_performance)
                    if sec is None:
                        raise ValueError("径赛成绩格式无效，请使用 '.' 分隔（示例：9.86 或 1.36.5）")
                    normalized_performance = f"{sec:.2f}"
                else:
                    normalized_performance = None
            elif scoring_strategy == "count":
                if normalized_performance:
                    cnt = self._parse_performance_numeric("count", normalized_performance)
                    if cnt is None:
                        raise ValueError("count 成绩必须为整数，单位个（示例：18）")
                    normalized_performance = str(int(cnt))
                else:
                    normalized_performance = None
            elif scoring_strategy == "count_miss":
                if normalized_performance:
                    val = self._parse_performance_numeric("count_miss", normalized_performance)
                    if val is None or "/" not in normalized_performance:
                        raise ValueError("count_miss 成绩格式应为 个数/失误次数（示例：120/2）")
                    left, right = normalized_performance.split("/", 1)
                    normalized_performance = f"{int(left)}/{int(right)}"
                else:
                    normalized_performance = None

            if has_athlete:
                athlete = repo.get_athlete_by_id(athlete_type or "", int(athlete_ref_id))
                if not athlete:
                    raise ValueError(f"运动员不存在: {athlete_type}/{athlete_ref_id}")
                if event["category"] != athlete_type:
                    raise ValueError("项目类别与运动员类型不匹配")
                if int(event["is_individual"]) != 1:
                    raise ValueError("该项目为团体项目，不能录入个人成绩")
                if not repo.athlete_registration_exists(athlete_type, int(athlete_ref_id), event_id):
                    raise ValueError("该运动员未报名此项目，不能录入成绩")
            if has_team:
                team = repo.get_team_by_id(int(team_id))
                if not team:
                    raise ValueError(f"队伍不存在: {team_id}")
                if int(team["event_id"]) != int(event_id):
                    raise ValueError("队伍与项目不匹配")

            auto_rank = rank is None
            final_rank = int(rank) if rank is not None else self._auto_rank_for_result(
                repo,
                event_id,
                scoring_strategy,
                normalized_performance,
            )
            if final_rank < 1:
                raise ValueError("rank 必须 >= 1")

            exists = repo.get_result_by_target(
                event_id=event_id,
                athlete_type=athlete_type if has_athlete else None,
                athlete_ref_id=athlete_ref_id if has_athlete else None,
                team_id=team_id if has_team else None,
            )
            if exists:
                result_id = int(exists["id"])
                repo.update_result(
                    result_id=result_id,
                    rank=final_rank,
                    points=points_for_rank(final_rank, int(event["is_individual"])),
                    performance=normalized_performance,
                    entered_by=entered_by_text if entered_by_text else None,
                )
            else:
                result_id = repo.insert_result(
                    event_id=event_id,
                    rank=final_rank,
                    points=points_for_rank(final_rank, int(event["is_individual"])),
                    athlete_type=athlete_type if has_athlete else None,
                    athlete_ref_id=athlete_ref_id if has_athlete else None,
                    team_id=team_id if has_team else None,
                    performance=normalized_performance,
                    entered_by=entered_by_text,
                )
            if auto_rank:
                self._recalculate_event_ranks(repo, event_id, scoring_strategy)
            conn.commit()
            return result_id
