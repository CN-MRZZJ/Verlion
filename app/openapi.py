from __future__ import annotations

from copy import deepcopy
from typing import Any


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


def _json_body(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": properties,
                    "required": required or [],
                }
            },
            "application/x-www-form-urlencoded": {
                "schema": {
                    "type": "object",
                    "properties": properties,
                    "required": required or [],
                }
            },
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
        _query("age_group", "组别筛选"),
        _query("category", "项目类别筛选：competitive/fun"),
        _query("scoring_strategy", "成绩策略筛选"),
        _query("sort_by", "排序字段"),
        _query("sort_dir", "排序方向：asc/desc"),
    ]
    export_filters = dataset_filters[2:8]
    athlete_type_prop = {"type": "string", "description": "运动员类型：competitive/fun"}
    athlete_no_prop = {"type": "string", "description": "运动员号"}
    event_id_prop = {"type": "integer", "description": "项目 ID"}
    team_id_prop = {"type": "integer", "description": "队伍 ID"}

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
            ),
            "post": _operation(
                "运动员",
                "新增运动员",
                "按单位名称新增竞技或趣味运动员。",
                request_body=_json_body(
                    {
                        "athlete_type": athlete_type_prop,
                        "athlete_no": athlete_no_prop,
                        "name": {"type": "string", "description": "姓名"},
                        "gender": {"type": "string", "description": "性别：male/female"},
                        "department_name": {"type": "string", "description": "归属单位"},
                        "age_group": {"type": "string", "description": "年龄组，可为空"},
                    },
                    ["athlete_type", "athlete_no", "name", "gender", "department_name"],
                ),
            ),
        },
        "/api/v1/athletes/delete": {
            "post": _operation(
                "运动员",
                "删除运动员（表单兼容）",
                "通过运动员类型和运动员号删除运动员。",
                request_body=_json_body({"athlete_type": athlete_type_prop, "athlete_no": athlete_no_prop}, ["athlete_type", "athlete_no"]),
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
            )
        },
        "/api/v1/athletes/registered-events": {
            "get": _operation(
                "运动员报名",
                "查询运动员已报名项目（兼容）",
                "通过查询参数查询指定运动员已经报名的个人项目。",
                parameters=[_query("athlete_type", "运动员类型：competitive/fun", required=True), _query("athlete_no", "运动员号", required=True)],
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
                request_body=_json_body({"athlete_type": athlete_type_prop, "athlete_no": athlete_no_prop, "event_id": event_id_prop}, ["athlete_type", "athlete_no", "event_id"]),
            )
        },
        "/api/v1/athletes/registrations/remove": {
            "post": _operation(
                "运动员报名",
                "删除运动员报名（表单兼容）",
                "通过表单或 JSON 移除运动员个人项目报名。",
                request_body=_json_body({"athlete_type": athlete_type_prop, "athlete_no": athlete_no_prop, "event_id": event_id_prop}, ["athlete_type", "athlete_no", "event_id"]),
            )
        },
        "/api/v1/events": {
            "get": _operation("项目", "查询项目列表", "返回全部比赛项目。")
        },
        "/api/v1/events/progress": {
            "get": _operation("项目流程", "查询项目流程状态", "查询所有项目的成绩录入和公示打印完成状态。")
        },
        "/api/v1/events/{event_id}/progress": {
            "put": _operation(
                "项目流程",
                "更新项目流程状态",
                "更新指定项目的成绩录入完成和打印完成状态。",
                parameters=[_path("event_id", "项目 ID", "integer")],
                request_body=_json_body(
                    {
                        "record_done": {"type": "boolean", "description": "成绩录入是否完成"},
                        "print_done": {"type": "boolean", "description": "公示打印是否完成"},
                    },
                    ["record_done", "print_done"],
                ),
            )
        },
        "/api/v1/events/progress/update": {
            "post": _operation(
                "项目流程",
                "更新项目流程状态（表单兼容）",
                "通过表单或 JSON 更新项目流程状态。",
                request_body=_json_body(
                    {
                        "event_id": event_id_prop,
                        "record_done": {"type": "boolean", "description": "成绩录入是否完成"},
                        "print_done": {"type": "boolean", "description": "公示打印是否完成"},
                    },
                    ["event_id"],
                ),
            )
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
                "初始化或更新比赛日期。",
                request_body=_json_body({"meet_date": {"type": "string", "format": "date", "description": "比赛日期，格式 YYYY-MM-DD"}}, ["meet_date"]),
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
                request_body=_json_body(
                    {
                        "tables": {"type": "array", "items": {"type": "string"}, "description": "要清空的数据表标识"},
                        "confirm_text": {"type": "string", "description": "确认文本"},
                        "confirm_code": {"type": "string", "description": "确认码"},
                        "acknowledged": {"type": "boolean", "description": "是否已确认风险"},
                    },
                    ["tables", "confirm_text", "confirm_code", "acknowledged"],
                ),
            )
        },
        "/api/v1/settings/report-environment": {
            "post": _operation(
                "公示",
                "保存公示环境信息",
                "保存成绩公示单使用的日期、天气、风向、温度等环境信息。",
                request_body=_json_body(
                    {
                        "date": {"type": "string", "description": "日期"},
                        "wind_direction": {"type": "string", "description": "风向"},
                        "wind_speed": {"type": "string", "description": "风速"},
                        "air_quality": {"type": "string", "description": "空气质量"},
                        "weather": {"type": "string", "description": "天气"},
                        "temperature_high": {"type": "string", "description": "最高温"},
                        "temperature_low": {"type": "string", "description": "最低温"},
                    }
                ),
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
        "/api/v1/results": {
            "get": _operation("成绩", "分页查询成绩", "分页查询成绩记录。", parameters=deepcopy(dataset_filters)),
            "post": _operation(
                "成绩",
                "录入成绩",
                "录入个人或团体项目成绩，并按规则计算积分。",
                request_body=_json_body(
                    {
                        "event_id": event_id_prop,
                        "rank": {"type": "integer", "description": "名次，可为空"},
                        "athlete_type": athlete_type_prop,
                        "athlete_id": {"type": "integer", "description": "运动员数据库 ID，可为空"},
                        "athlete_no": athlete_no_prop,
                        "team_id": team_id_prop,
                        "performance": {"type": "string", "description": "成绩文本"},
                        "entered_by": {"type": "string", "description": "录入人员姓名或编号"},
                    },
                    ["event_id"],
                ),
            ),
        },
        "/api/v1/rules": {
            "get": _operation("规则", "读取规则配置", "读取当前积分、成绩策略和组别规则配置。"),
            "put": _operation(
                "规则",
                "保存规则配置",
                "保存完整规则配置对象。",
                request_body=_json_body({"config": {"type": "object", "description": "完整规则配置对象", "additionalProperties": True}}, ["config"]),
            ),
        },
        "/api/v1/teams": {
            "get": _operation(
                "队伍",
                "查询队伍",
                "按项目、部门和关键词查询队伍列表。",
                parameters=[_query("keyword", "队伍或成员关键词"), _query("department_name", "部门名称"), _query("event_id", "项目 ID", "integer")],
            ),
            "post": _operation(
                "队伍",
                "新增队伍",
                "为指定部门和团体项目新增队伍。",
                request_body=_json_body(
                    {
                        "department_name": {"type": "string", "description": "部门名称"},
                        "event_id": event_id_prop,
                        "team_name": {"type": "string", "description": "队伍名称"},
                    },
                    ["department_name", "event_id", "team_name"],
                ),
            ),
        },
        "/api/v1/teams/batch-add": {
            "post": _operation(
                "队伍",
                "批量新增队伍",
                "按多个部门为同一个团体项目批量创建队伍。",
                request_body=_json_body(
                    {
                        "event_id": event_id_prop,
                        "department_names": {"type": "array", "items": {"type": "string"}, "description": "部门名称列表"},
                    },
                    ["event_id", "department_names"],
                ),
            )
        },
        "/api/v1/teams/delete": {
            "post": _operation("队伍", "删除队伍（表单兼容）", "通过队伍 ID 删除队伍。", request_body=_json_body({"team_id": team_id_prop}, ["team_id"]))
        },
        "/api/v1/teams/{team_id}": {
            "delete": _operation("队伍", "删除队伍", "通过路径参数删除队伍。", parameters=[_path("team_id", "队伍 ID", "integer")])
        },
        "/api/v1/teams/{team_id}/members": {
            "get": _operation("队伍成员", "查询队伍成员", "查询指定队伍成员。", parameters=[_path("team_id", "队伍 ID", "integer")]),
            "post": _operation(
                "队伍成员",
                "增加队伍成员",
                "为指定队伍增加运动员成员。",
                parameters=[_path("team_id", "队伍 ID", "integer")],
                request_body=_json_body({"athlete_type": athlete_type_prop, "athlete_no": athlete_no_prop}, ["athlete_type", "athlete_no"]),
            ),
            "delete": _operation(
                "队伍成员",
                "删除队伍成员",
                "从指定队伍移除运动员成员。",
                parameters=[_path("team_id", "队伍 ID", "integer")],
                request_body=_json_body({"athlete_type": athlete_type_prop, "athlete_no": athlete_no_prop}, ["athlete_type", "athlete_no"]),
            ),
        },
        "/api/v1/teams/members": {
            "get": _operation("队伍成员", "查询队伍成员（兼容）", "通过查询参数查询指定队伍成员。", parameters=[_query("team_id", "队伍 ID", "integer", True)])
        },
        "/api/v1/teams/members/add": {
            "post": _operation(
                "队伍成员",
                "增加队伍成员（表单兼容）",
                "通过表单或 JSON 增加队伍成员。",
                request_body=_json_body({"team_id": team_id_prop, "athlete_type": athlete_type_prop, "athlete_no": athlete_no_prop}, ["team_id", "athlete_type", "athlete_no"]),
            )
        },
        "/api/v1/teams/members/remove": {
            "post": _operation(
                "队伍成员",
                "删除队伍成员（表单兼容）",
                "通过表单或 JSON 删除队伍成员。",
                request_body=_json_body({"team_id": team_id_prop, "athlete_type": athlete_type_prop, "athlete_no": athlete_no_prop}, ["team_id", "athlete_type", "athlete_no"]),
            )
        },
        "/api/v1/status": {
            "get": _operation("系统状态", "查询初始化状态", "查询系统初始化检查结果。")
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
            {"name": "项目"},
            {"name": "项目流程"},
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
            }
        },
    }

