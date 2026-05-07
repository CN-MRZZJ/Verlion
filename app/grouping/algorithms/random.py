import random

from app.grouping.schema import GroupingInput, GroupingOutput, Heat, Lane, Stage

from .base import BaseAlgorithm

_ROUND_NAMES = {
    1: ["决赛"],
    2: ["预赛", "决赛"],
    3: ["预赛", "半决赛", "决赛"],
    4: ["预赛", "复赛", "半决赛", "决赛"],
}


def _build_heats(participants: list, lanes_per_heat: int) -> list[Heat]:
    heats: list[Heat] = []
    for i, p in enumerate(participants):
        heat_idx = i // lanes_per_heat
        lane_idx = i % lanes_per_heat
        if heat_idx >= len(heats):
            heats.append(Heat(
                heat_number=heat_idx + 1,
                heat_name=f"第{heat_idx + 1}组",
            ))
        heats[heat_idx].lanes.append(Lane(
            athlete_id=p.athlete_id,
            athlete_type=p.athlete_type,
            lane=lane_idx + 1,
        ))
    return heats


class RandomAlgorithm(BaseAlgorithm):
    name = "random"

    def run(self, input: GroupingInput) -> GroupingOutput:
        participants = list(input.participants)
        random.shuffle(participants)
        lanes_per_heat = max(input.config.lanes_per_heat, 1)
        heat_rounds = max(input.heat_rounds, 1)
        first_round_name = _ROUND_NAMES.get(heat_rounds, _ROUND_NAMES[1])[0]

        return GroupingOutput(
            event_id=input.event_id,
            stages=[Stage(
                stage_number=1,
                stage_name=first_round_name,
                heats=_build_heats(participants, lanes_per_heat),
            )],
        )
