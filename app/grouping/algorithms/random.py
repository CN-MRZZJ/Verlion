import random

from app.grouping.schema import GroupingInput, GroupingOutput, Heat, Lane, Stage

from .base import BaseAlgorithm


class RandomAlgorithm(BaseAlgorithm):
    name = "random"

    def run(self, input: GroupingInput) -> GroupingOutput:
        participants = list(input.participants)
        random.shuffle(participants)

        lanes_per_heat = max(input.config.lanes_per_heat, 1)
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

        return GroupingOutput(
            event_id=input.event_id,
            stages=[Stage(stage_number=1, stage_name="决赛", heats=heats)],
        )
