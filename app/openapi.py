from __future__ import annotations

from copy import deepcopy
from typing import Any

# ── Shared response schemas ──────────────────────────────────────────

JSON_OK = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean", "example": True},
    },
    "required": ["ok"],
    "additionalProperties": True,
}

JSON_ERROR = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean", "example": False},
        "error": {"type": "string", "example": "参数错误"},
    },
    "required": ["ok", "error"],
}

# ── Data model schemas ───────────────────────────────────────────────

ATHLETE = {
    "type": "object",
    "properties": {
        "group": {"type": "string", "description": "组别"},
        "athlete_no": {"type": "string", "description": "运动员号"},
        "athlete_ref_id": {"type": "integer", "description": "运动员数据库 ID"},
        "athlete_type": {"type": "string", "description": "运动员类型：competitive/fun"},
        "department_name": {"type": "string", "description": "归属单位"},
        "gender": {"type": "string", "description": "性别：male/female"},
        "name": {"type": "string", "description": "姓名"},
        "registered_events": {"type": "string", "description": "已报名项目列表"},
        "registration_count": {"type": "integer", "description": "已报名项目数"},
    },
}

DEPARTMENT = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "description": "部门 ID"},
        "name": {"type": "string", "description": "部门名称"},
        "total_members": {"type": "integer", "description": "部门总人数"},
    },
}

REGISTRATION = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "description": "项目 ID"},
        "name": {"type": "string", "description": "项目名称"},
        "label": {"type": "string", "description": "项目完整显示名"},
        "group": {"type": "string", "description": "组别"},
        "gender": {"type": "string", "description": "性别"},
    },
}

EVENT = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "description": "项目 ID"},
        "name": {"type": "string", "description": "项目名称"},
        "category": {"type": "string", "description": "项目类别：competitive/fun"},
        "event_type": {"type": "string", "description": "项目类型：track/field/fun"},
        "scoring_strategy": {"type": "string", "description": "计分策略：time/length/count/count_miss"},
        "gender": {"type": "string", "description": "性别限制：male/female/mixed"},
        "group": {"type": "string", "description": "组别"},
        "is_individual": {"type": "integer", "description": "是否个人项目：1=个人 0=团体"},
    },
}

EVENT_PROGRESS = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "description": "项目 ID"},
        "name": {"type": "string", "description": "项目名称"},
        "category": {"type": "string", "description": "项目类别"},
        "event_type": {"type": "string", "description": "项目类型"},
        "scoring_strategy": {"type": "string", "description": "计分策略"},
        "gender": {"type": "string", "description": "性别"},
        "group": {"type": "string", "description": "组别"},
        "is_individual": {"type": "integer", "description": "是否个人项目"},
        "checkin_done": {"type": "integer", "description": "检录是否完成：0/1"},
        "competition_done": {"type": "integer", "description": "比赛是否完成：0/1"},
        "record_done": {"type": "integer", "description": "成绩录入是否完成：0/1"},
        "publish_done": {"type": "integer", "description": "公示是否完成：0/1"},
        "updated_at": {"type": "string", "description": "更新时间"},
    },
}

TEAM = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "description": "队伍 ID"},
        "team_name": {"type": "string", "description": "队伍名称"},
        "department_name": {"type": "string", "description": "归属单位"},
        "event_id": {"type": "integer", "description": "所属项目 ID"},
        "event_name": {"type": "string", "description": "所属项目名称"},
        "gender": {"type": "string", "description": "项目性别"},
        "group": {"type": "string", "description": "项目组别"},
        "member_count": {"type": "integer", "description": "成员数"},
        "members_summary": {"type": "string", "description": "成员姓名摘要"},
    },
}

TEAM_MEMBER = {
    "type": "object",
    "properties": {
        "athlete_no": {"type": "string", "description": "运动员号"},
        "athlete_type": {"type": "string", "description": "运动员类型"},
        "name": {"type": "string", "description": "姓名"},
        "gender": {"type": "string", "description": "性别"},
        "department_name": {"type": "string", "description": "归属单位"},
        "athlete_ref_id": {"type": "integer", "description": "运动员数据库 ID"},
    },
}

RESULT = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "description": "成绩 ID"},
        "event_name": {"type": "string", "description": "项目名称"},
        "category": {"type": "string", "description": "项目类别"},
        "scoring_strategy": {"type": "string", "description": "计分策略"},
        "group": {"type": "string", "description": "组别"},
        "result_type": {"type": "string", "description": "成绩类型：athlete/team"},
        "athlete_type": {"type": "string", "description": "运动员类型"},
        "target_name": {"type": "string", "description": "运动员名或队伍名"},
        "department_name": {"type": "string", "description": "归属单位"},
        "rank": {"type": "integer", "description": "名次"},
        "points": {"type": "integer", "description": "积分"},
        "performance": {"type": "string", "description": "成绩文本"},
        "entered_by": {"type": "string", "description": "录入人员"},
        "created_at": {"type": "string", "description": "创建时间"},
    },
}

ATTEMPT = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "description": "尝试记录 ID"},
        "attempt_number": {"type": "integer", "description": "第几次录入"},
        "rank": {"type": "integer", "description": "名次"},
        "performance": {"type": "string", "description": "成绩文本"},
        "is_void": {"type": "integer", "description": "是否作废：0=有效 1=作废"},
        "created_at": {"type": "string", "description": "创建时间"},
    },
}

CHECK_ITEM = {
    "type": "object",
    "properties": {
        "key": {"type": "string", "description": "检查项标识"},
        "label": {"type": "string", "description": "检查项名称"},
        "ok": {"type": "boolean", "description": "是否通过"},
        "detail": {"type": "string", "description": "详情描述"},
    },
}

SUMMARY = {
    "type": "object",
    "properties": {
        "athlete_count": {"type": "integer", "description": "运动员总数"},
        "department_count": {"type": "integer", "description": "部门总数"},
        "event_count": {"type": "integer", "description": "项目总数"},
    },
}

INIT_STATUS = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean", "description": "请求是否成功"},
        "completed": {"type": "boolean", "description": "初始化是否完成"},
        "checks": {
            "type": "array",
            "items": {"$ref": "#/components/schemas/CheckItem"},
            "description": "各项检查结果",
        },
        "summary": {"$ref": "#/components/schemas/Summary"},
    },
}

RULE_CONFIG = {
    "type": "object",
    "properties": {
        "attempt_policy": {"type": "string", "description": "多次尝试策略：best/latest"},
        "group_options": {"type": "object", "description": "组别配置"},
        "event_scoring_strategy": {"type": "object", "description": "项目计分策略映射"},
        "point_rule": {"type": "object", "description": "名次积分规则"},
    },
}

RULE_CONFIG_RESPONSE = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "config": {"$ref": "#/components/schemas/RuleConfig"},
    },
}

EVENT_TYPE = {
    "type": "object",
    "properties": {
        "code": {"type": "string", "description": "项目代号"},
        "name": {"type": "string", "description": "项目中文分类"},
        "scoring_strategy": {"type": "string", "description": "比较策略：time/length/count/count_miss"},
    },
}

EVENT_TYPE_ITEM_RESPONSE = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "item": {"$ref": "#/components/schemas/EventType"},
    },
}

CREATE_EVENT_TYPE_REQUEST = {
    "type": "object",
    "required": ["code", "name", "scoring_strategy"],
    "properties": {
        "code": {"type": "string", "description": "项目代号"},
        "name": {"type": "string", "description": "项目中文分类"},
        "scoring_strategy": {"type": "string", "description": "比较策略：time/length/count/count_miss"},
    },
}

UPDATE_EVENT_TYPE_REQUEST = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "项目中文分类"},
        "scoring_strategy": {"type": "string", "description": "比较策略：time/length/count/count_miss"},
    },
}

# ── Request schemas ──────────────────────────────────────────────────

CREATE_ATHLETE_REQUEST = {
    "type": "object",
    "properties": {
        "athlete_type": {"type": "string", "description": "运动员类型：competitive/fun"},
        "athlete_no": {"type": "string", "description": "运动员号"},
        "name": {"type": "string", "description": "姓名"},
        "gender": {"type": "string", "description": "性别：male/female"},
        "department_name": {"type": "string", "description": "归属单位"},
        "group": {"type": "string", "description": "年龄组，可为空"},
    },
    "required": ["athlete_type", "athlete_no", "name", "gender", "department_name"],
}

DELETE_ATHLETE_REQUEST = {
    "type": "object",
    "properties": {
        "athlete_type": {"type": "string", "description": "运动员类型：competitive/fun"},
        "athlete_no": {"type": "string", "description": "运动员号"},
    },
    "required": ["athlete_type", "athlete_no"],
}

REGISTRATION_REQUEST = {
    "type": "object",
    "properties": {
        "athlete_type": {"type": "string", "description": "运动员类型：competitive/fun"},
        "athlete_no": {"type": "string", "description": "运动员号"},
        "event_id": {"type": "integer", "description": "项目 ID"},
    },
    "required": ["athlete_type", "athlete_no", "event_id"],
}

UPDATE_PROGRESS_REQUEST = {
    "type": "object",
    "properties": {
        "event_id": {"type": "integer", "description": "项目 ID（表单兼容用）"},
        "checkin_done": {"type": "boolean", "description": "检录是否完成"},
        "competition_done": {"type": "boolean", "description": "比赛是否完成"},
        "record_done": {"type": "boolean", "description": "成绩录入是否完成"},
        "publish_done": {"type": "boolean", "description": "公示是否完成"},
    },
}

SET_MEET_DATE_REQUEST = {
    "type": "object",
    "properties": {
        "meet_date": {"type": "string", "format": "date", "description": "比赛日期，格式 YYYY-MM-DD"},
    },
    "required": ["meet_date"],
}

CREATE_RESULT_REQUEST = {
    "type": "object",
    "properties": {
        "event_id": {"type": "integer", "description": "项目 ID"},
        "rank": {"type": "integer", "description": "名次，不传则自动推定"},
        "athlete_type": {"type": "string", "description": "运动员类型：competitive/fun"},
        "athlete_id": {"type": "integer", "description": "运动员数据库 ID"},
        "athlete_no": {"type": "string", "description": "运动员号（可替代 athlete_id）"},
        "team_id": {"type": "integer", "description": "队伍 ID（团体项目用）"},
        "performance": {"type": "string", "description": "成绩文本"},
        "entered_by": {"type": "string", "description": "录入人员姓名或编号"},
    },
    "required": ["event_id"],
}

RULE_SAVE_REQUEST = {
    "type": "object",
    "properties": {
        "config": {"type": "object", "description": "完整规则配置对象", "additionalProperties": True},
    },
    "required": ["config"],
}

CREATE_TEAM_REQUEST = {
    "type": "object",
    "properties": {
        "department_name": {"type": "string", "description": "部门名称"},
        "event_id": {"type": "integer", "description": "项目 ID"},
        "team_name": {"type": "string", "description": "队伍名称"},
    },
    "required": ["department_name", "event_id", "team_name"],
}

BATCH_ADD_TEAMS_REQUEST = {
    "type": "object",
    "properties": {
        "event_id": {"type": "integer", "description": "项目 ID"},
        "department_names": {
            "type": "array",
            "items": {"type": "string"},
            "description": "部门名称列表",
        },
    },
    "required": ["event_id", "department_names"],
}

DELETE_TEAM_REQUEST = {
    "type": "object",
    "properties": {
        "team_id": {"type": "integer", "description": "队伍 ID"},
    },
    "required": ["team_id"],
}

TEAM_MEMBER_REQUEST = {
    "type": "object",
    "properties": {
        "team_id": {"type": "integer", "description": "队伍 ID"},
        "athlete_type": {"type": "string", "description": "运动员类型：competitive/fun"},
        "athlete_no": {"type": "string", "description": "运动员号"},
    },
    "required": ["team_id", "athlete_type", "athlete_no"],
}

CLEAR_DATA_REQUEST = {
    "type": "object",
    "properties": {
        "tables": {
            "type": "array",
            "items": {"type": "string"},
            "description": "要清空的数据表标识",
        },
        "confirm_text": {"type": "string", "description": "确认文本，必须为 DELETE"},
        "confirm_code": {"type": "string", "description": "确认码，格式为 CLEAR-{n}"},
        "acknowledged": {"type": "boolean", "description": "是否已确认风险"},
    },
    "required": ["tables", "confirm_text", "confirm_code", "acknowledged"],
}

REPORT_ENVIRONMENT_REQUEST = {
    "type": "object",
    "properties": {
        "date": {"type": "string", "description": "日期"},
        "wind_direction": {"type": "string", "description": "风向"},
        "wind_speed": {"type": "string", "description": "风速"},
        "air_quality": {"type": "string", "description": "空气质量"},
        "weather": {"type": "string", "description": "天气"},
        "temperature_high": {"type": "string", "description": "最高温"},
        "temperature_low": {"type": "string", "description": "最低温"},
    },
}

CREATE_DEPARTMENT_REQUEST = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "部门名称"},
        "total_members": {"type": "integer", "description": "部门总人数，默认 0"},
    },
    "required": ["name"],
}

UPDATE_DEPARTMENT_REQUEST = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "部门名称"},
        "total_members": {"type": "integer", "description": "部门总人数"},
    },
}

DELETE_DEPARTMENT_REQUEST = {
    "type": "object",
    "properties": {
        "department_id": {"type": "integer", "description": "部门 ID"},
    },
    "required": ["department_id"],
}

VOID_ATTEMPT_REQUEST = {
    "type": "object",
    "properties": {
        "is_void": {"type": "boolean", "description": "是否作废：true=作废 false=取消作废"},
    },
}

# ── 分组分道 ──────────────────────────────────────────────────────────

HEAT_ENTRY = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "description": "道次分配 ID"},
        "heat_id": {"type": "integer", "description": "所属组次 ID"},
        "athlete_type": {"type": "string", "description": "运动员类型：competitive/fun"},
        "athlete_ref_id": {"type": "integer", "description": "运动员数据库 ID"},
        "athlete_name": {"type": "string", "description": "运动员姓名"},
        "athlete_no": {"type": "string", "description": "运动员号"},
        "department_name": {"type": "string", "description": "归属单位"},
        "group": {"type": "string", "description": "年龄组别"},
        "lane": {"type": "integer", "description": "道次"},
    },
}

HEAT = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "description": "组次 ID"},
        "round_id": {"type": "integer", "description": "所属轮次 ID"},
        "heat_name": {"type": "string", "description": "组次名称，如 第1组"},
        "heat_number": {"type": "integer", "description": "组次序号"},
        "entries": {
            "type": "array",
            "items": {"$ref": "#/components/schemas/HeatEntry"},
            "description": "道次分配列表",
        },
    },
}

ROUND_STAGE = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "description": "轮次 ID"},
        "event_id": {"type": "integer", "description": "所属项目 ID"},
        "round_name": {"type": "string", "description": "轮次名称，如 预赛/决赛"},
        "round_number": {"type": "integer", "description": "轮次序号"},
        "advancement_rule": {"type": "string", "description": "晋级规则"},
        "created_at": {"type": "string", "description": "创建时间"},
        "heats": {
            "type": "array",
            "items": {"$ref": "#/components/schemas/Heat"},
            "description": "组次列表",
        },
    },
}

HEATS_DATA = {
    "type": "object",
    "properties": {
        "event_id": {"type": "integer", "description": "项目 ID"},
        "rounds": {
            "type": "array",
            "items": {"$ref": "#/components/schemas/Round"},
            "description": "轮次列表",
        },
    },
}

HEATS_RESPONSE = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "data": {"$ref": "#/components/schemas/HeatsData"},
    },
}

CREATE_HEATS_REQUEST = {
    "type": "object",
    "properties": {
        "lanes_per_heat": {"type": "integer", "description": "每组道数/人数上限，默认 8"},
        "algorithm": {"type": "string", "description": "编排算法名称，默认 random"},
        "params": {"type": "object", "description": "算法自定义参数", "additionalProperties": True},
    },
}

UPDATE_LANE_REQUEST = {
    "type": "object",
    "properties": {
        "lane": {"type": "integer", "description": "新的道次，可为空"},
    },
}

# ── Helper functions ─────────────────────────────────────────────────

def _schema_ref(name: str) -> dict[str, str]:
    return {"$ref": f"#/components/schemas/{name}"}


def _json_response(description: str = "成功") -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            "application/json": {
                "schema": _schema_ref("OkResponse"),
            }
        },
    }


def _typed_response(schema_name: str, description: str = "成功") -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            "application/json": {
                "schema": _schema_ref(schema_name),
            }
        },
    }


def _paginated_response(schema_name: str, description: str = "成功") -> dict[str, Any]:
    schema = {
        "type": "object",
        "properties": {
            "ok": {"type": "boolean"},
            "items": {
                "type": "array",
                "items": _schema_ref(schema_name),
            },
            "total": {"type": "integer"},
            "page": {"type": "integer"},
            "page_size": {"type": "integer"},
        },
    }
    return {
        "description": description,
        "content": {
            "application/json": {
                "schema": schema,
            }
        },
    }


def _item_list_response(schema_name: str, description: str = "成功") -> dict[str, Any]:
    schema = {
        "type": "object",
        "properties": {
            "ok": {"type": "boolean"},
            "items": {
                "type": "array",
                "items": _schema_ref(schema_name),
            },
            "total": {"type": "integer"},
        },
    }
    return {
        "description": description,
        "content": {
            "application/json": {
                "schema": schema,
            }
        },
    }


def _error_response() -> dict[str, Any]:
    return {
        "description": "请求失败",
        "content": {
            "application/json": {
                "schema": _schema_ref("ErrorResponse"),
            }
        },
    }


def _file_response(description: str, content_type: str) -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            content_type: {
                "schema": {
                    "type": "string",
                    "format": "binary",
                }
            }
        },
    }


def _query(name: str, description: str, schema_type: str = "string", required: bool = False) -> dict[str, Any]:
    return {
        "name": name,
        "in": "query",
        "required": required,
        "description": description,
        "schema": {"type": schema_type},
    }


def _path(name: str, description: str, schema_type: str = "string") -> dict[str, Any]:
    return {
        "name": name,
        "in": "path",
        "required": True,
        "description": description,
        "schema": {"type": schema_type},
    }


def _json_body_ref(
    schema_name: str,
    *,
    form_compat: bool = True,
) -> dict[str, Any]:
    content: dict[str, Any] = {
        "application/json": {
            "schema": _schema_ref(schema_name),
        },
    }
    if form_compat:
        content["application/x-www-form-urlencoded"] = {
            "schema": _schema_ref(schema_name),
        }
    return {
        "required": True,
        "content": content,
    }


def _form_body_ref(schema_name: str) -> dict[str, Any]:
    return {
        "required": True,
        "content": {
            "application/x-www-form-urlencoded": {
                "schema": _schema_ref(schema_name),
            }
        },
    }


def _csv_upload_body() -> dict[str, Any]:
    return {
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "file": {
                            "type": "string",
                            "format": "binary",
                            "description": "CSV 文件",
                        }
                    },
                    "required": ["file"],
                }
            }
        },
    }


def _operation(
    tag: str,
    summary: str,
    description: str,
    *,
    parameters: list[dict[str, Any]] | None = None,
    request_body: dict[str, Any] | None = None,
    success: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "tags": [tag],
        "summary": summary,
        "description": description,
        "responses": {
            "200": success or _json_response(),
            "400": _error_response(),
        },
    }
    if parameters:
        data["parameters"] = parameters
    if request_body:
        data["requestBody"] = request_body
    return data


def get_openapi_spec() -> dict[str, Any]:
    dataset_filters = [
        _query("page", "页码，从 1 开始", "integer"),
        _query("page_size", "每页数量", "integer"),
        _query("keyword", "关键词筛选"),
        _query("department_name", "部门名称筛选"),
        _query("gender", "性别筛选：male/female/mixed"),
        _query("group", "组别筛选"),
        _query("category", "项目类别筛选：competitive/fun"),
        _query("scoring_strategy", "成绩策略筛选"),
        _query("sort_by", "排序字段"),
        _query("sort_dir", "排序方向：asc/desc"),
    ]
    export_filters = dataset_filters[2:8]

    paths: dict[str, Any] = {
        "/api/v1/datasets/{view}": {
            "get": _operation(
                "数据查询",
                "分页查询数据视图",
                "查询项目、运动员、部门、队伍、报名、成绩、积分榜等数据视图。",
                parameters=[_path("view", "数据视图名称")] + dataset_filters,
            )
        },
        "/api/v1/athletes": {
            "get": _operation(
                "运动员",
                "查询运动员",
                "按类型和关键词查询运动员列表。",
                parameters=[
                    _query("athlete_type", "运动员类型：competitive/fun"),
                    _query("keyword", "运动员号、姓名或单位关键词"),
                ],
                success=_paginated_response("Athlete"),
            ),
            "post": _operation(
                "运动员",
                "新增运动员",
                "按单位名称新增竞技或趣味运动员。",
                request_body=_json_body_ref("CreateAthleteRequest"),
            ),
        },
        "/api/v1/athletes/delete": {
            "post": _operation(
                "运动员",
                "删除运动员（表单兼容）",
                "通过运动员类型和运动员号删除运动员。",
                request_body=_json_body_ref("DeleteAthleteRequest"),
            )
        },
        "/api/v1/athletes/{athlete_type}/{athlete_no}": {
            "delete": _operation(
                "运动员",
                "删除运动员",
                "通过路径参数删除运动员。",
                parameters=[_path("athlete_type", "运动员类型：competitive/fun"), _path("athlete_no", "运动员号")],
            )
        },
        "/api/v1/athletes/{athlete_type}/{athlete_no}/registrations": {
            "get": _operation(
                "运动员报名",
                "查询运动员已报名项目",
                "查询指定运动员已经报名的个人项目。",
                parameters=[_path("athlete_type", "运动员类型：competitive/fun"), _path("athlete_no", "运动员号")],
                success=_item_list_response("Registration"),
            )
        },
        "/api/v1/athletes/registered-events": {
            "get": _operation(
                "运动员报名",
                "查询运动员已报名项目（兼容）",
                "通过查询参数查询指定运动员已经报名的个人项目。",
                parameters=[_query("athlete_type", "运动员类型：competitive/fun", required=True), _query("athlete_no", "运动员号", required=True)],
                success=_item_list_response("Registration"),
            )
        },
        "/api/v1/athletes/{athlete_type}/{athlete_no}/registrations/{event_id}": {
            "post": _operation(
                "运动员报名",
                "增加运动员报名",
                "为指定运动员增加一个个人项目报名。",
                parameters=[
                    _path("athlete_type", "运动员类型：competitive/fun"),
                    _path("athlete_no", "运动员号"),
                    _path("event_id", "项目 ID", "integer"),
                ],
            ),
            "delete": _operation(
                "运动员报名",
                "删除运动员报名",
                "移除指定运动员的一个个人项目报名。",
                parameters=[
                    _path("athlete_type", "运动员类型：competitive/fun"),
                    _path("athlete_no", "运动员号"),
                    _path("event_id", "项目 ID", "integer"),
                ],
            ),
        },
        "/api/v1/athletes/registrations/add": {
            "post": _operation(
                "运动员报名",
                "增加运动员报名（表单兼容）",
                "通过表单或 JSON 为运动员增加个人项目报名。",
                request_body=_json_body_ref("RegistrationRequest"),
            )
        },
        "/api/v1/athletes/registrations/remove": {
            "post": _operation(
                "运动员报名",
                "删除运动员报名（表单兼容）",
                "通过表单或 JSON 移除运动员个人项目报名。",
                request_body=_json_body_ref("RegistrationRequest"),
            )
        },
        "/api/v1/departments": {
            "get": _operation(
                "部门",
                "分页查询部门",
                "分页查询部门列表，支持关键词和排序。",
                parameters=[
                    _query("page", "页码，从 1 开始", "integer"),
                    _query("page_size", "每页数量", "integer"),
                    _query("keyword", "部门名称关键词"),
                    _query("sort_by", "排序字段：id/name/total_members"),
                    _query("sort_dir", "排序方向：asc/desc"),
                ],
                success=_paginated_response("Department"),
            ),
            "post": _operation(
                "部门",
                "新增部门",
                "新增一个部门。",
                request_body=_json_body_ref("CreateDepartmentRequest"),
            ),
        },
        "/api/v1/departments/{department_id}": {
            "put": _operation(
                "部门",
                "更新部门",
                "更新部门名称或总人数。",
                parameters=[_path("department_id", "部门 ID", "integer")],
                request_body=_json_body_ref("UpdateDepartmentRequest"),
            ),
            "delete": _operation(
                "部门",
                "删除部门",
                "删除指定部门（部门下无运动员和队伍时才能删除）。",
                parameters=[_path("department_id", "部门 ID", "integer")],
            ),
        },
        "/api/v1/departments/delete": {
            "post": _operation(
                "部门",
                "删除部门（表单兼容）",
                "通过表单或 JSON 删除部门。",
                request_body=_json_body_ref("DeleteDepartmentRequest"),
            )
        },
        "/api/v1/events": {
            "get": _operation(
                "项目",
                "查询项目列表",
                "返回全部比赛项目。",
                success=_item_list_response("Event"),
            )
        },
        "/api/v1/events/progress": {
            "get": _operation(
                "项目流程",
                "查询项目流程状态",
                "查询所有项目的检录、比赛、成绩录入和公示完成状态。",
                success=_item_list_response("EventProgress"),
            )
        },
        "/api/v1/events/{event_id}/progress": {
            "put": _operation(
                "项目流程",
                "更新项目流程状态",
                "更新指定项目的检录、比赛、成绩录入和公示完成状态。",
                parameters=[_path("event_id", "项目 ID", "integer")],
                request_body=_json_body_ref("UpdateProgressRequest"),
            )
        },
        "/api/v1/events/progress/update": {
            "post": _operation(
                "项目流程",
                "更新项目流程状态（表单兼容）",
                "通过表单或 JSON 更新项目流程状态（检录、比赛、录入、公示）。",
                request_body=_json_body_ref("UpdateProgressRequest"),
            )
        },
        "/api/v1/events/{event_id}/heats": {
            "get": _operation(
                "分组分道",
                "查看编排结果",
                "查看指定项目的分组分道结果（轮次→组次→道次分配）。",
                parameters=[_path("event_id", "项目 ID", "integer")],
                success=_typed_response("HeatsResponse"),
            ),
            "post": _operation(
                "分组分道",
                "执行编排",
                "按指定算法执行分组分道编排，生成道次表。",
                parameters=[_path("event_id", "项目 ID", "integer")],
                request_body=_json_body_ref("CreateHeatsRequest"),
                success=_typed_response("HeatsResponse"),
            ),
            "delete": _operation(
                "分组分道",
                "清除编排",
                "清除指定项目的全部分组分道数据，用于重新编排。",
                parameters=[_path("event_id", "项目 ID", "integer")],
            ),
        },
        "/api/v1/events/{event_id}/heats/{heat_id}/entries/{entry_id}": {
            "put": _operation(
                "分组分道",
                "调整道次",
                "手动调整某个道次分配的 lane 值（调道/换道）。",
                parameters=[
                    _path("event_id", "项目 ID", "integer"),
                    _path("heat_id", "组次 ID", "integer"),
                    _path("entry_id", "道次分配 ID", "integer"),
                ],
                request_body=_json_body_ref("UpdateLaneRequest"),
            ),
        },
        "/api/v1/events/heats/algorithms": {
            "get": _operation(
                "分组分道",
                "列出编排算法",
                "返回当前可用的分组分道算法名称列表。",
                success=_item_list_response("string"),
            ),
        },
        "/api/v1/event-types": {
            "get": _operation(
                "项目类型",
                "列出项目类型",
                "列出所有已配置的项目类型（项目代号、中文分类、比较策略）。",
                success=_item_list_response("EventType"),
            ),
            "post": _operation(
                "项目类型",
                "新增项目类型",
                "新增一个项目类型，包含代号、中文分类名称和比较策略。",
                request_body=_json_body_ref("CreateEventTypeRequest"),
            ),
        },
        "/api/v1/event-types/{code}": {
            "get": _operation(
                "项目类型",
                "获取项目类型",
                "根据代号获取单个项目类型。",
                parameters=[_path("code", "项目代号")],
                success=_typed_response("EventTypeItemResponse"),
            ),
            "put": _operation(
                "项目类型",
                "更新项目类型",
                "更新项目类型的中文分类名称或比较策略。",
                parameters=[_path("code", "项目代号")],
                request_body=_json_body_ref("UpdateEventTypeRequest"),
            ),
            "delete": _operation(
                "项目类型",
                "删除项目类型",
                "删除指定项目类型（需确保没有项目引用该代号）。",
                parameters=[_path("code", "项目代号")],
            ),
        },
        "/api/v1/exports/{view}": {
            "get": _operation(
                "导出",
                "导出数据视图 CSV",
                "按筛选条件导出指定数据视图的 CSV 文件。",
                parameters=[_path("view", "数据视图名称")] + export_filters,
                success=_file_response("CSV 文件", "text/csv"),
            )
        },
        "/api/v1/imports/setup": {
            "post": _operation(
                "导入",
                "设置比赛日期",
                "初始化或更新比赛日期（仅接受表单提交）。",
                request_body=_form_body_ref("SetMeetDateRequest"),
            )
        },
        "/api/v1/imports/templates/{name}": {
            "get": _operation(
                "导入",
                "下载导入模板",
                "下载静态 CSV 导入模板文件。",
                parameters=[_path("name", "模板文件名或路径")],
                success=_file_response("CSV 模板文件", "text/csv"),
            )
        },
        "/api/v1/imports/registrations/template": {
            "get": _operation(
                "导入",
                "下载报名矩阵模板",
                "按项目类别生成报名矩阵 CSV 模板。",
                parameters=[_query("category", "项目类别：competitive/fun", required=True)],
                success=_file_response("CSV 模板文件", "text/csv"),
            )
        },
        "/api/v1/imports/events": {
            "post": _operation("导入", "导入项目 CSV", "上传并导入项目 CSV 文件。", request_body=_csv_upload_body())
        },
        "/api/v1/imports/athletes/{athlete_type}": {
            "post": _operation(
                "导入",
                "导入运动员 CSV",
                "上传并导入竞技或趣味运动员名单 CSV 文件。",
                parameters=[_path("athlete_type", "运动员类型：competitive/fun")],
                request_body=_csv_upload_body(),
            )
        },
        "/api/v1/imports/registrations/{target_category}": {
            "post": _operation(
                "导入",
                "导入报名矩阵 CSV",
                "上传并导入竞技或趣味项目报名矩阵 CSV 文件。",
                parameters=[_path("target_category", "项目类别：competitive/fun")],
                request_body=_csv_upload_body(),
            )
        },
        "/api/v1/maintenance/clear-data": {
            "post": _operation(
                "维护",
                "清空指定数据表",
                "按确认文本、确认码和勾选状态清空指定业务表数据。",
                request_body=_json_body_ref("ClearDataRequest"),
            )
        },
        "/api/v1/settings/report-environment": {
            "post": _operation(
                "公示",
                "保存公示环境信息",
                "保存成绩公示单使用的日期、天气、风向、温度等环境信息。",
                request_body=_json_body_ref("ReportEnvironmentRequest"),
            )
        },
        "/api/v1/notices/personal-result.xlsx": {
            "get": _operation(
                "公示",
                "导出个人成绩公示 XLSX",
                "按项目和模板导出个人项目成绩公示单。",
                parameters=[_query("event_id", "项目 ID", "integer", True), _query("template_name", "XLSX 模板文件名", required=True)],
                success=_file_response("XLSX 文件", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            )
        },
        "/api/v1/notices/personal-result.pdf": {
            "get": _operation(
                "公示",
                "预览个人成绩公示 PDF",
                "按项目和模板生成个人项目成绩公示 PDF。",
                parameters=[_query("event_id", "项目 ID", "integer", True), _query("template_name", "XLSX 模板文件名", required=True)],
                success=_file_response("PDF 文件", "application/pdf"),
            )
        },
        "/api/v1/notices/team-result.xlsx": {
            "get": _operation(
                "公示",
                "导出团体成绩公示 XLSX",
                "按项目和模板导出团体项目成绩公示单。",
                parameters=[_query("event_id", "项目 ID", "integer", True), _query("template_name", "XLSX 模板文件名", required=True)],
                success=_file_response("XLSX 文件", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            )
        },
        "/api/v1/notices/team-result.pdf": {
            "get": _operation(
                "公示",
                "预览团体成绩公示 PDF",
                "按项目和模板生成团体项目成绩公示 PDF。",
                parameters=[_query("event_id", "项目 ID", "integer", True), _query("template_name", "XLSX 模板文件名", required=True)],
                success=_file_response("PDF 文件", "application/pdf"),
            )
        },
        "/api/v1/notices/personal-attempt.xlsx": {
            "get": _operation(
                "公示",
                "导出个人轮次成绩表 XLSX",
                "按项目和模板导出个人项目轮次成绩表（含每次尝试记录及作废标记）。",
                parameters=[_query("event_id", "项目 ID", "integer", True), _query("template_name", "XLSX 模板文件名", required=True), _query("attempt_number", "指定轮次（不传则导出所有轮次）", "integer")],
                success=_file_response("XLSX 文件", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            )
        },
        "/api/v1/notices/personal-attempt.pdf": {
            "get": _operation(
                "公示",
                "预览个人轮次成绩表 PDF",
                "按项目和模板生成个人项目轮次成绩表 PDF。",
                parameters=[_query("event_id", "项目 ID", "integer", True), _query("template_name", "XLSX 模板文件名", required=True), _query("attempt_number", "指定轮次（不传则导出所有轮次）", "integer")],
                success=_file_response("PDF 文件", "application/pdf"),
            )
        },
        "/api/v1/notices/team-attempt.xlsx": {
            "get": _operation(
                "公示",
                "导出团体轮次成绩表 XLSX",
                "按项目和模板导出团体项目轮次成绩表（含每次尝试记录及作废标记）。",
                parameters=[_query("event_id", "项目 ID", "integer", True), _query("template_name", "XLSX 模板文件名", required=True), _query("attempt_number", "指定轮次（不传则导出所有轮次）", "integer")],
                success=_file_response("XLSX 文件", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            )
        },
        "/api/v1/notices/team-attempt.pdf": {
            "get": _operation(
                "公示",
                "预览团体轮次成绩表 PDF",
                "按项目和模板生成团体项目轮次成绩表 PDF。",
                parameters=[_query("event_id", "项目 ID", "integer", True), _query("template_name", "XLSX 模板文件名", required=True), _query("attempt_number", "指定轮次（不传则导出所有轮次）", "integer")],
                success=_file_response("PDF 文件", "application/pdf"),
            )
        },
        "/api/v1/results": {
            "get": _operation(
                "成绩",
                "分页查询成绩",
                "分页查询成绩记录。",
                parameters=deepcopy(dataset_filters) + [_query("event_id", "项目 ID 筛选", "integer")],
                success=_paginated_response("Result"),
            ),
            "post": _operation(
                "成绩",
                "录入成绩",
                "录入个人或团体项目成绩，并按规则计算积分。",
                request_body=_json_body_ref("CreateResultRequest"),
            ),
        },
        "/api/v1/attempts": {
            "get": _operation(
                "成绩",
                "查询尝试记录",
                "查询某个运动员或队伍在指定项目的所有尝试记录（含作废状态）。",
                parameters=[
                    _query("event_id", "项目 ID", "integer", True),
                    _query("athlete_type", "运动员类型：competitive/fun"),
                    _query("athlete_ref_id", "运动员数据库 ID", "integer"),
                    _query("team_id", "队伍 ID", "integer"),
                ],
                success=_item_list_response("Attempt"),
            )
        },
        "/api/v1/attempts/{attempt_id}/void": {
            "put": _operation(
                "成绩",
                "作废/取消作废尝试记录",
                "将指定尝试记录标记为作废或取消作废，并自动重算该对象的最终成绩。",
                parameters=[_path("attempt_id", "尝试记录 ID", "integer")],
                request_body=_json_body_ref("VoidAttemptRequest"),
            )
        },
        "/api/v1/rules": {
            "get": _operation(
                "规则",
                "读取规则配置",
                "读取当前积分、成绩策略和组别规则配置。",
                success=_typed_response("RuleConfigResponse"),
            ),
            "put": _operation(
                "规则",
                "保存规则配置",
                "保存完整规则配置对象。",
                request_body=_json_body_ref("RuleSaveRequest"),
            ),
        },
        "/api/v1/teams": {
            "get": _operation(
                "队伍",
                "查询队伍",
                "按项目、部门和关键词查询队伍列表。",
                parameters=[_query("keyword", "队伍或成员关键词"), _query("department_name", "部门名称"), _query("event_id", "项目 ID", "integer")],
                success=_item_list_response("Team"),
            ),
            "post": _operation(
                "队伍",
                "新增队伍",
                "为指定部门和团体项目新增队伍。",
                request_body=_json_body_ref("CreateTeamRequest"),
            ),
        },
        "/api/v1/teams/batch-add": {
            "post": _operation(
                "队伍",
                "批量新增队伍",
                "按多个部门为同一个团体项目批量创建队伍。",
                request_body=_json_body_ref("BatchAddTeamsRequest"),
            )
        },
        "/api/v1/teams/delete": {
            "post": _operation(
                "队伍",
                "删除队伍（表单兼容）",
                "通过队伍 ID 删除队伍。",
                request_body=_json_body_ref("DeleteTeamRequest"),
            )
        },
        "/api/v1/teams/{team_id}": {
            "delete": _operation("队伍", "删除队伍", "通过路径参数删除队伍。", parameters=[_path("team_id", "队伍 ID", "integer")])
        },
        "/api/v1/teams/{team_id}/members": {
            "get": _operation(
                "队伍成员",
                "查询队伍成员",
                "查询指定队伍成员。",
                parameters=[_path("team_id", "队伍 ID", "integer")],
                success=_item_list_response("TeamMember"),
            ),
            "post": _operation(
                "队伍成员",
                "增加队伍成员",
                "为指定队伍增加运动员成员。",
                parameters=[_path("team_id", "队伍 ID", "integer")],
                request_body=_json_body_ref("TeamMemberRequest"),
            ),
            "delete": _operation(
                "队伍成员",
                "删除队伍成员",
                "从指定队伍移除运动员成员。",
                parameters=[_path("team_id", "队伍 ID", "integer")],
                request_body=_json_body_ref("TeamMemberRequest"),
            ),
        },
        "/api/v1/teams/members": {
            "get": _operation(
                "队伍成员",
                "查询队伍成员（兼容）",
                "通过查询参数查询指定队伍成员。",
                parameters=[_query("team_id", "队伍 ID", "integer", True)],
                success=_item_list_response("TeamMember"),
            )
        },
        "/api/v1/teams/members/add": {
            "post": _operation(
                "队伍成员",
                "增加队伍成员（表单兼容）",
                "通过表单或 JSON 增加队伍成员。",
                request_body=_json_body_ref("TeamMemberRequest"),
            )
        },
        "/api/v1/teams/members/remove": {
            "post": _operation(
                "队伍成员",
                "删除队伍成员（表单兼容）",
                "通过表单或 JSON 删除队伍成员。",
                request_body=_json_body_ref("TeamMemberRequest"),
            )
        },
        "/api/v1/status": {
            "get": _operation(
                "系统状态",
                "查询初始化状态",
                "查询系统初始化检查结果。",
                success=_typed_response("InitStatus"),
            )
        },
    }

    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Sports-Point API",
            "version": "1.0.0",
            "description": "运动会积分与成绩管理系统对外 API 文档。",
        },
        "servers": [{"url": "/"}],
        "tags": [
            {"name": "数据查询"},
            {"name": "运动员"},
            {"name": "运动员报名"},
            {"name": "部门"},
            {"name": "项目"},
            {"name": "项目类型"},
            {"name": "项目流程"},
            {"name": "分组分道"},
            {"name": "导入"},
            {"name": "导出"},
            {"name": "成绩"},
            {"name": "队伍"},
            {"name": "队伍成员"},
            {"name": "公示"},
            {"name": "规则"},
            {"name": "维护"},
            {"name": "系统状态"},
        ],
        "paths": paths,
        "components": {
            "schemas": {
                "OkResponse": JSON_OK,
                "ErrorResponse": JSON_ERROR,
                "Department": DEPARTMENT,
                "Athlete": ATHLETE,
                "Registration": REGISTRATION,
                "Event": EVENT,
                "EventProgress": EVENT_PROGRESS,
                "Team": TEAM,
                "TeamMember": TEAM_MEMBER,
                "Result": RESULT,
                "EventType": EVENT_TYPE,
                "EventTypeItemResponse": EVENT_TYPE_ITEM_RESPONSE,
                "CreateEventTypeRequest": CREATE_EVENT_TYPE_REQUEST,
                "UpdateEventTypeRequest": UPDATE_EVENT_TYPE_REQUEST,
                "Attempt": ATTEMPT,
                "CheckItem": CHECK_ITEM,
                "Summary": SUMMARY,
                "InitStatus": INIT_STATUS,
                "RuleConfig": RULE_CONFIG,
                "RuleConfigResponse": RULE_CONFIG_RESPONSE,
                "CreateAthleteRequest": CREATE_ATHLETE_REQUEST,
                "DeleteAthleteRequest": DELETE_ATHLETE_REQUEST,
                "RegistrationRequest": REGISTRATION_REQUEST,
                "UpdateProgressRequest": UPDATE_PROGRESS_REQUEST,
                "SetMeetDateRequest": SET_MEET_DATE_REQUEST,
                "CreateResultRequest": CREATE_RESULT_REQUEST,
                "RuleSaveRequest": RULE_SAVE_REQUEST,
                "CreateTeamRequest": CREATE_TEAM_REQUEST,
                "BatchAddTeamsRequest": BATCH_ADD_TEAMS_REQUEST,
                "DeleteTeamRequest": DELETE_TEAM_REQUEST,
                "TeamMemberRequest": TEAM_MEMBER_REQUEST,
                "ClearDataRequest": CLEAR_DATA_REQUEST,
                "ReportEnvironmentRequest": REPORT_ENVIRONMENT_REQUEST,
                "CreateDepartmentRequest": CREATE_DEPARTMENT_REQUEST,
                "UpdateDepartmentRequest": UPDATE_DEPARTMENT_REQUEST,
                "DeleteDepartmentRequest": DELETE_DEPARTMENT_REQUEST,
                "VoidAttemptRequest": VOID_ATTEMPT_REQUEST,
                "HeatEntry": HEAT_ENTRY,
                "Heat": HEAT,
                "Round": ROUND_STAGE,
                "HeatsData": HEATS_DATA,
                "HeatsResponse": HEATS_RESPONSE,
                "CreateHeatsRequest": CREATE_HEATS_REQUEST,
                "UpdateLaneRequest": UPDATE_LANE_REQUEST,
            }
        },
    }
