from app.models.repositories import SportsRepository
from app.models.repositories.crud import DEPARTMENTS, WhereClause


class MeetDepartmentMixin:
    def query_departments(self, page: int = 1, page_size: int = 20, keyword: str = "", sort_by: str = "", sort_dir: str = "desc") -> dict:
        page = max(int(page), 1)
        page_size = max(min(int(page_size), 100), 1)
        total, rows = self._repo_read(lambda repo: repo.page_departments(
            page=page,
            page_size=page_size,
            keyword=keyword or "",
            sort_by=sort_by or "",
            sort_dir=sort_dir or "desc",
        ))
        return {"items": [dict(r) for r in rows], "total": total, "page": page, "page_size": page_size}

    def add_department(self, name: str, total_members: int = 0) -> int:
        name = name.strip()
        if not name:
            raise ValueError("部门名称不能为空")
        existing = self._repo_read(lambda repo: repo.get_department_by_name(name))
        if existing:
            raise ValueError(f"部门已存在: {name}")
        return self._repo_write(lambda repo: repo.insert_department(name, total_members))

    def update_department(self, department_id: int, name: str = "", total_members: int | None = None) -> None:
        name = name.strip()
        values: dict = {}
        if name:
            values["name"] = name
        if total_members is not None:
            values["total_members"] = int(total_members)
        if not values:
            raise ValueError("没有可更新的字段")
        self._repo_write(lambda repo: repo._crud_update_by_id(DEPARTMENTS, int(department_id), values))

    def delete_department(self, department_id: int) -> dict:
        did = int(department_id)
        refs = self._repo_read(lambda repo: {
            "athletes": repo._crud_count(DEPARTMENTS, WhereClause(
                "id IN (SELECT department_id FROM athletes WHERE department_id=?)", (did,)
            )),
            "teams": repo._crud_count(DEPARTMENTS, WhereClause(
                "id IN (SELECT department_id FROM teams WHERE department_id=?)", (did,)
            )),
        })
        for key, label in [("athletes", "运动员"), ("teams", "队伍")]:
            if refs.get(key, 0) > 0:
                raise ValueError(f"该部门下存在{label}，无法删除")
        deleted = self._repo_write(lambda repo: repo._crud_delete_by_id(DEPARTMENTS, did))
        return {"deleted": deleted, "department_id": did}
