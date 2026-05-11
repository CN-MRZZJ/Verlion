# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概况

运动会积分与成绩管理系统（Sports Point），纯 Flask Web 应用，SQLite 数据库，Python 3.10+。

## 常用命令

```bash
# 开发模式（Flask 内置服务器，debug=True）
python run_dev.py

# 生产模式（Windows：waitress；Linux：gunicorn）
python run_prod.py                 # Windows
gunicorn -w 4 -b 0.0.0.0:5000 run:app  # Linux

# 安装依赖
pip install -r requirements.txt
```

没有测试套件和 lint 配置。通过 `http://127.0.0.1:5000/docs` 可查看 Swagger API 文档。

## API 响应约定

所有 API 响应统一为 JSON，格式为 `{"ok": true/false, ...data}`。成功时不限定额外字段；失败时 HTTP 400 + `{"ok": false, "error": "错误描述"}`。分页响应额外包含 `items`、`total`、`page`、`page_size`。

## 架构分层

```
app/
├── __init__.py          # Flask 工厂函数 create_app()，注册 blueprint 和 CORS
├── openapi.py           # OpenAPI 3.0.3 规范（纯 Python 手动维护，非自动发现）
├── rules.py             # 规则引擎：积分规则、计分策略、组别、多次尝试策略
├── routes/v1/           # 路由层（薄控制器，调用 service，返回 JSON）
│   ├── common.py        # Blueprint 定义、get_service()、parse_csv_upload()
│   ├── athletes.py      # 运动员 CRUD + 报名
│   ├── events.py        # 项目 + 流程状态
│   ├── results.py       # 成绩录入/查询
│   ├── attempts.py      # 尝试记录（多轮次录入+作废）
│   ├── teams.py         # 队伍 + 成员管理
│   ├── imports.py       # CSV 上传导入
│   ├── exports.py       # CSV 导出 + 数据视图
│   ├── notices.py       # XLSX/PDF 公示单
│   ├── rules.py         # 规则读写 API
│   └── api.py           # 通用数据视图查询
├── services/            # 业务逻辑层（Mixin 组合模式）
│   ├── core.py          # SportsMeetService，由 7 个 Mixin 组合
│   ├── base.py          # 基础服务：DB 初始化、成绩格式化、环境设置等
│   ├── time_service.py  # UTC+8 时区工具：now()、today()、now_iso()、today_iso()
│   ├── athletes.py      # 运动员业务逻辑
│   ├── teams.py         # 队伍业务逻辑
│   ├── results.py       # 成绩录入（含多次尝试支持）
│   ├── views.py         # 数据视图查询
│   ├── notice.py        # 公示单生成（XLSX+PDF）
│   ├── imports.py       # CSV 导入逻辑
│   └── admin.py         # 数据清除等管理功能
└── models/              # 数据访问层
    ├── database.py      # Database 类：连接管理 + schema 初始化 + 就地迁移
    ├── schema.sql       # DDL（CREATE TABLE IF NOT EXISTS）
    └── repositories/    # Repository 模式
        ├── sports_repository.py    # SportsRepository（组合各领域 repo）
        ├── base_repository.py      # 分页查询、排序、运动员表查找辅助
        ├── crud/
        │   ├── base.py    # CrudRepositoryMixin：通用 CRUD 方法
        │   ├── types.py   # TableSchema、WhereClause 类型
        │   └── schemas.py # 所有表的 TableSchema 定义
        └── *_repository.py     # 领域 repository（athlete、event、result 等）
```

## 核心设计模式

### Service 层：Mixin 组合
`SportsMeetService` 继承 `MeetServiceBase` + 6 个 Mixin。所有方法共享 `_repo_read(action)` / `_repo_write(action)` 模式——传入 `lambda repo: repo.xxx()` 自动管理连接和事务。`_repo_write` 自动 commit，`_repo_read` 不 commit。

### 路由层：双接口模式
每个资源通常提供两套接口：RESTful 路径参数形式（`DELETE /athletes/{type}/{no}`）和表单兼容 POST 形式（`POST /athletes/delete`）。后者接受 JSON 或 `application/x-www-form-urlencoded`，方便前端 `<form>` 直接提交。所有路由文件通过 `get_service()` 获取 service 实例，只做参数解析和 JSON 序列化，业务逻辑一律在 service 层。

### OpenAPI 规范维护
`app/openapi.py` 是手动维护的 OpenAPI 3.0.3 规范（非自动发现）。新增端点时需同时修改两部分：路由文件（`app/routes/v1/*.py`）和 OpenAPI 定义（`app/openapi.py` 中的 paths 字典 + schemas）。该文件提供辅助函数 `_operation()`、`_json_body_ref()`、`_query()`、`_path()` 等来减少样板代码。

### 数据库迁移
不使用迁移工具。`Database.initialize()` 在每次应用启动时执行：先运行 `schema.sql`，然后依次调用 `_migrate_*()` 方法。每个迁移方法检查表/列是否存在，再执行 `CREATE TABLE ...new → INSERT → DROP → RENAME` 重建表。幂等设计，可安全重复执行。

### Repository 层
- `CrudRepositoryMixin` 提供通用 `_crud_insert/upsert/get_by_id/list/update/delete/count/exists` 方法
- 所有方法接受 `TableSchema` 参数，自动过滤可写字段（`writable_insert_values` / `writable_update_values`）
- `SportsRepository` 组合所有领域 repository（AthleteRepository、EventRepository 等）
- `WhereClause` 类型封装 SQL 条件和参数，防止注入

### Config 模式（config.py）
配置项通过环境变量覆盖，有基于 `BASE_DIR` 的默认值：
- `SECRET_KEY` — Flask secret key
- `SPORTS_MEET_DB` — SQLite 数据库路径，默认 `{BASE_DIR}/sports_meet.db`

### 规则引擎（app/rules.py）
首次启动自动播种默认规则到数据库，运行时通过 API 修改并自动刷新缓存。包含：
- `point_rule`：个人/团体名次积分映射
- `attempt_policy`：`best`（取最优）/ `latest`（取最新）
- `group_options`：运动员组别（A/B/C）、项目组别（A/B/C/ALL）、`team_event_default`
- `event_scoring_strategy`：track→time、field→length、fun→count

### 成绩计算策略（4 种）
- `time`：时间型，支持 `分.秒` 格式，内部转为秒，显示为 `MM:SS.cc`
- `length`：长度型，输入以米为单位，显示为 `X.XXm`
- `count`：计数型，越大越好，显示为 `N个`
- `count_miss`：命中/失误型，`命中数/失误数` 格式，内部编码为 `count * 1000000 - miss`

### 多次尝试与作废（Attempts）
`attempts` 表记录每次成绩录入，支持多轮次（`attempt_number`）和作废标记（`is_void`）。策略由 `attempt_policy` 规则决定：`best` 取最优有效成绩，`latest` 取最新有效成绩。作废/取消作废时自动重算该对象的最终成绩。公示单支持导出轮次成绩表（personal-attempt / team-attempt），包含每次尝试记录及作废标记。

### 项目流程状态（event_progress）
每个项目跟踪 4 个阶段：`checkin_done`（检录）→ `competition_done`（比赛）→ `record_done`（成绩录入）→ `publish_done`（公示）。通过 `PUT /events/{id}/progress` 更新。

### 公示单系统
- 模板目录：`app/static/notice_templates/`
- 布局配置文件（JSON）指定 Excel 单元格坐标，包含 `environment_cells`、`rank_rows` 等区域
- 支持 4 种公示单：personal-result、team-result、personal-attempt、team-attempt
- 每种均可导出 XLSX 或在线预览 PDF
- 环境信息（日期、天气、风向、风速、气温、空气质量）存储在 `settings` 表的 `report_env.*` 键下

### 数据清除安全机制
清除数据需同时满足：勾选至少一张表 + 输入确认口令 `DELETE` + 输入动态校验码 `CLEAR-N`（N 为所选表数量）+ 勾选风险确认。系统按依赖关系自动处理关联删除。

## 数据库关键约束

- **athletes**：统一表，`athlete_type` 区分 `competitive`/`fun`，`(athlete_type, athlete_no)` 唯一
- **results**：CHECK 约束确保每行要么是运动员成绩（`athlete_ref_id + athlete_type`），要么是队伍成绩（`team_id`），不会两者同时存在
- **attempts**：同样的 CHECK 约束 + `is_void` 作废标记
- **athlete_registrations**：`(athlete_type, athlete_ref_id, event_id)` 唯一
- **teams**：`(event_id, name)` 唯一
