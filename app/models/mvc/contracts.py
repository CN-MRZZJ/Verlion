from dataclasses import dataclass
from typing import Optional


@dataclass
class QueryFilter:
    keyword: str = ""
    department_name: str = ""
    gender: str = ""
    age_group: str = ""
    category: str = ""
    scoring_strategy: str = ""
    sort_by: str = ""
    sort_dir: str = "desc"
    page: int = 1
    page_size: int = 20
    event_id: Optional[int] = None
