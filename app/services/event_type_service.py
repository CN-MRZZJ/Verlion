class MeetEventTypeMixin:
    def insert_event_type(self, code: str, name: str, scoring_strategy: str, competition_format: str = "heats") -> str:
        def _write(repo):
            return repo.insert_event_type(code, name, scoring_strategy, competition_format)
        return self._repo_write(_write)

    def get_event_type(self, code: str) -> dict | None:
        def _read(repo):
            row = repo.get_event_type(code)
            return dict(row) if row else None
        return self._repo_read(_read)

    def list_event_types(self) -> list[dict]:
        def _read(repo):
            return [dict(r) for r in repo.list_event_types()]
        return self._repo_read(_read)

    def update_event_type(self, code: str, name: str | None = None, scoring_strategy: str | None = None, competition_format: str | None = None) -> None:
        def _write(repo):
            repo.update_event_type(code, name=name, scoring_strategy=scoring_strategy, competition_format=competition_format)
        self._repo_write(_write)

    def delete_event_type(self, code: str) -> tuple[bool, str]:
        def _write(repo):
            count = repo.count_events_by_event_type(code)
            if count > 0:
                raise ValueError(f"无法删除：有 {count} 个项目正在使用该代号")
            repo.delete_event_type(code)
        try:
            self._repo_write(_write)
            return True, ""
        except ValueError as exc:
            return False, str(exc)
