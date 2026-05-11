import random

from app.grouping.schema import GroupingInput, GroupingOutput, Heat, Lane, Stage

from .base import BaseAlgorithm

_ROUND_NAMES = {
    1: ["决赛"],
    2: ["预赛", "决赛"],
    3: ["预赛", "半决赛", "决赛"],
    4: ["预赛", "复赛", "半决赛", "决赛"],
}


def _corridor_pattern(n: int) -> list[int]:
    """Generate preferred-lane ordering for n lanes (center → outward).
    n=8 → [4,5,3,6,2,7,1,8]  n=4 → [2,3,1,4]"""
    order = []
    left = (n + 1) // 2
    right = left + 1
    while left >= 1 or right <= n:
        if left >= 1:
            order.append(left)
            left -= 1
        if right <= n:
            order.append(right)
            right += 1
    return order


class SeededAlgorithm(BaseAlgorithm):
    name = "seeded"

    def run(self, input: GroupingInput) -> GroupingOutput:
        lanes_per_heat = max(input.config.lanes_per_heat, 1)
        heat_rounds = max(input.heat_rounds, 1)
        first_round_name = _ROUND_NAMES.get(heat_rounds, _ROUND_NAMES[1])[0]

        # Sort by seed_mark: smaller time = better, None goes to end
        seeded = [p for p in input.participants if p.seed_mark is not None]
        unseeded = [p for p in input.participants if p.seed_mark is None]
        seeded.sort(key=lambda p: p.seed_mark)
        random.shuffle(unseeded)

        ranked = seeded + unseeded
        lane_order = _corridor_pattern(lanes_per_heat)

        heats: list[Heat] = []
        for i, p in enumerate(ranked):
            heat_idx = i // lanes_per_heat
            pos_in_heat = i % lanes_per_heat
            lane = lane_order[pos_in_heat] if pos_in_heat < len(lane_order) else pos_in_heat + 1
            if heat_idx >= len(heats):
                heats.append(Heat(
                    heat_number=heat_idx + 1,
                    heat_name=f"第{heat_idx + 1}组",
                ))
            heats[heat_idx].lanes.append(Lane(
                athlete_id=p.athlete_id,
                athlete_type=p.athlete_type,
                lane=lane,
            ))

        return GroupingOutput(
            event_id=input.event_id,
            stages=[Stage(
                stage_number=1,
                stage_name=first_round_name,
                heats=heats,
            )],
        )
