from app.grouping.schema import AdvancementInput, AdvancementOutput, QualifiedParticipant

from .base import BaseAdvancement


class PerHeatTopAdvancement(BaseAdvancement):
    name = "per_heat_top"

    def run(self, input: AdvancementInput) -> AdvancementOutput:
        count = int(input.params.get("count", 2))
        extra = int(input.params.get("extra", 0))

        qualified: dict[str, QualifiedParticipant] = {}
        order: list[str] = []

        by_heat: dict[int, list[dict]] = {}
        for r in input.results:
            by_heat.setdefault(int(r["heat_id"]), []).append(r)

        for heat_id in sorted(by_heat):
            for r in by_heat[heat_id][:count]:
                key = self._key(r)
                if key not in qualified:
                    q = self._to_participant(r)
                    qualified[key] = q
                    order.append(key)

        if extra > 0:
            all_sorted = sorted(input.results, key=lambda r: int(r["rank"]))
            for r in all_sorted:
                key = self._key(r)
                if key not in qualified:
                    qualified[key] = self._to_participant(r)
                    order.append(key)
                    extra -= 1
                if extra == 0:
                    break

        return AdvancementOutput(
            event_id=input.event_id,
            qualified=[qualified[k] for k in order],
        )

    @staticmethod
    def _key(r: dict) -> str:
        return f"{r.get('athlete_type', '')}|{r.get('athlete_ref_id', '')}|{r.get('team_id', '')}"

    @staticmethod
    def _to_participant(r: dict) -> QualifiedParticipant:
        return QualifiedParticipant(
            athlete_type=r.get("athlete_type"),
            athlete_ref_id=r.get("athlete_ref_id"),
            team_id=r.get("team_id"),
        )
