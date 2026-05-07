from app.grouping.schema import AdvancementInput, AdvancementOutput, QualifiedParticipant

from .base import BaseAdvancement


class OverallTopAdvancement(BaseAdvancement):
    name = "overall_top"

    def run(self, input: AdvancementInput) -> AdvancementOutput:
        count = int(input.params.get("count", 8))
        ranked = sorted(input.results, key=lambda r: int(r["rank"]))

        qualified = []
        for r in ranked[:count]:
            qualified.append(QualifiedParticipant(
                athlete_type=r.get("athlete_type"),
                athlete_ref_id=r.get("athlete_ref_id"),
                team_id=r.get("team_id"),
            ))

        return AdvancementOutput(
            event_id=input.event_id,
            qualified=qualified,
        )
