# Verlion 开发文档

## 目录

1. [架构总览](#1-架构总览)
2. [数据库设计](#2-数据库设计)
3. [分层约定](#3-分层约定)
4. [核心模块详解](#4-核心模块详解)
5. [道次编排系统](#5-道次编排系统)
6. [成绩系统](#6-成绩系统)
7. [公示单系统](#7-公示单系统)
8. [路由与 API](#8-路由与-api)
9. [扩展指南](#9-扩展指南)

---

## 1. 架构总览

```
请求 → routes/v1/（薄控制器）
           ↓
       services/（业务逻辑，Mixin 组合）
           ↓
       models/repositories/（数据访问）
           ↓
       SQLite（database.py 管理连接 + schema + 迁移）
```

```
app/
├── __init__.py               Flask 工厂函数 create_app()
├── openapi.py                Swagger 文档（手动维护）
├── rules.py                  规则引擎（积分、策略、组别）
│
├── grouping/                 算法模块
│   ├── schema.py             数据类定义
│   ├── algorithms/           分道算法（插件式）
│   └── advancement/          晋级策略（插件式）
│
├── routes/v1/                路由层
│   └── common.py             Blueprint + get_service() + CSV 解析
│
├── services/                 业务逻辑层
│   └── core.py               SportsMeetService = 基类 + 9 个 Mixin
│
└── models/                   数据访问层
    ├── database.py           连接池 + schema 初始化 + 就地迁移
    ├── schema.sql            DDL
    └── repositories/         Repository 模式
```

### 设计原则

- **路由只做参数解析和 JSON 序列化**，不含业务逻辑
- **Service 层通过 Mixin 组合**：`SportsMeetService` 继承 `MeetServiceBase` + 9 个 Mixin
- **Repository 模式**：每个领域一个 Mixin，通过 `SportsRepository` 组合
- **`_repo_read(action)` / `_repo_write(action)`** 模式：传入 `lambda repo: repo.xxx()`，自动管理连接和事务。`_repo_write` 自动 commit

---

## 2. 数据库设计

### 核心业务表

```
athletes              运动员（统一表，athlete_type 区分 competitive/fun）
departments           部门
events                比赛项目
athlete_registrations 报名关系
teams                 队伍（团体项目）
team_members          队伍成员
results               最终成绩（按轮次独立）
attempts              每次成绩尝试（多轮次录入）
```

### 赛制与编排表

```
heats_config          event_id → heat_rounds（1-4）
rounds                event_id → round_number, round_name, advancement_rule
heats                 round_id → heat_number, heat_name
heat_entries          heat_id → athlete/team, lane
```

### 配置表

```
event_types           项目类型（code → name, scoring_strategy, competition_format）
point_rules           积分规则
group_options         组别选项
settings              系统设置（JSON 键值对）
event_progress        项目流程状态
```

### 关键约束

- `athletes`：`(athlete_type, athlete_no)` 唯一
- `athlete_registrations`：`(athlete_type, athlete_ref_id, event_id)` 唯一
- `results` / `attempts` / `heat_entries`：CHECK 约束确保每条记录要么是运动员（athlete_ref_id + athlete_type），要么是队伍（team_id），互斥
- `events.competition_format`：CHECK 约束 `IN ('heats','knockout','round_robin')`
- `heats_config.heat_rounds`：CHECK 约束 `BETWEEN 1 AND 4`

### 迁移机制

不使用迁移工具。`Database.initialize()` 在每次启动时：
1. 执行 `schema.sql`（`CREATE TABLE IF NOT EXISTS`）
2. 依次调用 `_migrate_*()` 方法，每个检查表/列是否存在，再 `ALTER TABLE ADD COLUMN`
3. 幂等设计，可安全重复执行

---

## 3. 分层约定

### Repository 层

```
models/repositories/
├── sports_repository.py    SportsRepository（组合所有 Mixin）
├── crud/
│   ├── base.py             CrudRepositoryMixin：通用 INSERT/UPDATE/DELETE/SELECT
│   ├── types.py            TableSchema、WhereClause 类型
│   └── schemas.py          所有表的 TableSchema 定义
├── *_repository.py         各领域 Repository（Mixin）
└── heats.py                HeatsRepositoryMixin
```

**TableSchema** 定义：
```python
EVENTS = TableSchema(
    name="events",
    columns=(...),           # 全列
    insert_columns=(...),    # 可插入列，不传则默认 columns - pk
    update_columns=(...),    # 可更新列，不传则默认 insert_columns - pk
)
```

`writable_insert_values(values)` / `writable_update_values(values)` 自动过滤非法字段，防止注入。

### Service 层

```python
# services/core.py
class SportsMeetService(
    MeetServiceBase,           # DB 连接、成绩格式化
    MeetResultMixin,           # 成绩录入
    MeetHeatsMixin,            # 编排分道
    MeetNoticeMixin,           # 公示单
    MeetImportMixin,           # CSV 导入
    MeetAthleteMixin,          # 运动员
    MeetTeamMixin,             # 队伍
    MeetViewMixin,             # 数据视图
    MeetAdminMixin,            # 管理功能
    MeetDepartmentMixin,       # 部门管理
    MeetEventTypeMixin,        # 项目类型
):
    pass
```

### 路由层

路由文件只做：
1. 从 `request.args` / `request.get_json()` / `request.form` 解析参数
2. 类型转换、校验
3. 调用 `get_service().xxx()`
4. `jsonify({"ok": True, ...})` 或异常捕获 `jsonify({"ok": False, "error": ...}), 400`

双接口模式：每个资源通常提供 RESTful 路径参数形式 + 表单兼容 POST 形式。

---

## 4. 核心模块详解

### 规则引擎（`app/rules.py`）

首次启动自动播种默认规则到 DB，运行时 `GET/PUT /api/v1/rules` 读写。

核心函数：
- `point_rule()` — 名次 → 积分映射
- `attempt_policy()` — `best` 或 `latest`
- `points_for_rank(rank, is_individual)` — 计算积分
- `scoring_strategy_for_event_type(code)` — 项目类型 → 计分策略
- `team_event_default_group()` — 团体项目默认组别

### 计分策略

| 策略 | 说明 | 输入格式 | 内部存储 | 显示格式 |
|------|------|----------|----------|----------|
| `time` | 时间 | `分.秒` 或 `秒` | 秒（float） | `MM:SS.cc` |
| `length` | 长度 | 米数 | 米（float） | `X.XXm` |
| `count` | 计数 | 整数 | int | `N个` |
| `count_miss` | 命中/失误 | `命中/失误` | `count × 1000000 - miss` | `命中/失误` |

### 项目流程状态

`event_progress` 表跟踪 4 个阶段：
1. `checkin_done` — 检录完成
2. `competition_done` — 比赛完成
3. `record_done` — 成绩录入完成
4. `publish_done` — 公示完成

---

## 5. 道次编排系统

### 数据模型

```
heats_config.heat_rounds = N  (1-4)
        │
        ▼
rounds (event_id, round_number, round_name)
   │
   └── heats (round_id, heat_number, heat_name)
          │
          └── heat_entries (heat_id, athlete_type, athlete_ref_id, lane)
```

### 轮次命名

| heat_rounds | round_id:1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 1 | 决赛 | — | — | — |
| 2 | 预赛 | 决赛 | — | — |
| 3 | 预赛 | 半决赛 | 决赛 | — |
| 4 | 预赛 | 复赛 | 半决赛 | 决赛 |

中文名由两端维护同名映射：`app/grouping/algorithms/random.py::_ROUND_NAMES` 和 `app/services/heats.py::_ROUND_NAMES`。

### 分道算法（`app/grouping/algorithms/`）

插件式注册表：

```python
# app/grouping/algorithms/__init__.py
_registry: dict[str, BaseAlgorithm] = {}

def register(algo: BaseAlgorithm):
    _registry[algo.name] = algo

def get_algorithm(name: str) -> BaseAlgorithm:
    ...

def list_algorithms() -> list[str]:
    ...
```

**BaseAlgorithm**（`base.py`）：
```python
class BaseAlgorithm(ABC):
    name: str = ""
    @abstractmethod
    def run(self, input: GroupingInput) -> GroupingOutput:
        ...
```

**RandomAlgorithm**（`random.py`）：
1. 洗牌打乱所有参与者
2. `heat_idx = i / lanes_per_heat`，`lane = i % lanes_per_heat + 1`
3. 生成 1 个 Stage，名称取自第一轮的映射名

**数据类**（`schema.py`）：
```python
Participant(athlete_id, name, athlete_type, department, seed_mark)
GroupingConfig(lanes_per_heat, algorithm, params)
GroupingInput(event_id, participants, config, heat_rounds)
GroupingOutput(event_id, stages)
Stage(stage_number, stage_name, heats)
Heat(heat_number, heat_name, lanes)
Lane(athlete_id, athlete_type, lane)
```

### 晋级策略（`app/grouping/advancement/`）

同样插件式模式：

```python
AdvancementInput(event_id, results, params)
AdvancementOutput(event_id, qualified)
QualifiedParticipant(athlete_type, athlete_ref_id, team_id)
```

**内置策略：**

| 策略 | 参数 | 说明 |
|------|------|------|
| `per_heat_top` | count, extra | 每组前 count 名，extra 递补 |
| `overall_top` | count | 总排名前 count |

### 编排 API 流程

```
1. PUT /events/{id}/heats/config         设定轮次数
2. POST /events/{id}/heats               生成第 1 轮编排
3. 成绩录入（round_id=1）
4. POST /events/{id}/rounds/1/advance    晋级 → 生成第 2 轮
5. 成绩录入（round_id=2）
6. ...重复...
```

### 调道对调

`PUT /events/{id}/heats/{heat_id}/entries/{entry_id}` 接受 `heat_id` + `lane`：

- 目标为空 → 直接移动
- 目标有人 → 自动对调（两人互换组和道）
- 只传 lane → 同组内改道
- 只传 heat_id → 换组

实现：`app/services/heats.py::swap_or_move_heat_entry()` → 查目标位置 `find_entry_at()` → 用 `move_heat_entry()` 互换。

---

## 6. 成绩系统

### 表结构

```sql
results:
  event_id, round_id, athlete_type, athlete_ref_id, team_id,
  rank, points, performance, entered_by, created_at

attempts:
  event_id, round_id, athlete_type, athlete_ref_id, team_id,
  attempt_number, rank, performance, is_void, entered_by, created_at
```

`round_id` 对应 `round_number`（1-4），各轮独立排名。无 FK 约束到 `rounds` 表，默认 1。

### 录入流程（`record_result`）

1. 参数校验（athlete_ref_id 或 team_id 二选一）
2. 查项目 → 确定 scoring_strategy
3. 规范化成绩文本
4. `insert_attempt(event_id, round_id, ...)` — 记录本次尝试
5. `list_attempts_for_target(event_id, round_id, ...)` — 取该轮全部尝试
6. `_pick_best_attempt()` — 根据 attempt_policy 选最优有效尝试
7. `get_result_by_target(event_id, round_id, ...)` — 查是否有已有结果
8. INSERT 或 UPDATE results
9. `_recalculate_event_ranks(repo, event_id, scoring_strategy, round_id)` — 重排该轮名次

### 作废尝试（`void_attempt`）

1. 取 attempt → 读 round_id
2. `set_attempt_void()`
3. 取该轮该目标全部尝试 → 筛出有效 → 重选最优
4. 无有效尝试则删除 result，否则更新
5. 重算该轮排名

---

## 7. 公示单系统

### 两种模式

| 模式 | API | 返回 |
|------|-----|------|
| 分组公告 | `/notices/grouped-result.xlsx|.pdf` | ZIP（每组一个文件），按 heat_rank 排 |
| 全部公告 | `/notices/full-result.xlsx|.pdf` | 单文件，按总 rank 排 |

均需 `event_id` + `round_id`，`template_name` 可选（默认 `heat_notice_template.xlsx`）。

### 模板结构

```
app/static/notice_templates/
├── heat_notice_template.xlsx        公告模板
├── grouped_result_layout.json       分组公告布局
└── full_result_layout.json          全部公告布局
```

### 布局配置

```json
{
  "sheet_name": "Sheet1",
  "environment_cells": {
    "date": "C8",
    "event_name": "B6",
    "weather": "C12",
    "temperature_high": "E12",
    ...
  },
  "row_template": {
    "rank": "B",
    "name": "C",
    "department": "D",
    "performance": "G"
  },
  "start_row": 15
}
```

`row_template` 支持：`rank`, `heat_rank`, `heat_name`, `name`, `department`, `athlete_no`, `performance`, `points`。

`environment_cells` 支持：`date`, `weather`, `wind_direction`, `wind_speed`, `air_quality`, `temperature_high`, `temperature_low`, `event_name`, `round_name`, `notice_title`。

分组公告每组一页，项目名后自动追加" - 第N组"。

### 生成流程

1. 从 template 加载 workbook → 填入环境信息 → 逐行写成绩
2. 分组公告：每组独立 load template 写入后打包 ZIP（避免 copy_worksheet 丢失格式）
3. PDF 优先 Excel（pywin32），降级 LibreOffice

### 环境信息

```
GET  /api/v1/settings/report-environment   → 读取
POST /api/v1/settings/report-environment   → 保存
```

---

## 8. 路由与 API

### 全部路由一览

| 模块 | 路由前缀 | 文件 |
|------|----------|------|
| 运动员 | `/athletes?` | `routes/v1/athletes.py` |
| 项目 | `/events?` | `routes/v1/events.py` |
| 编排 | `/events/{id}/heats?` | `routes/v1/heats.py` |
| 项目类型 | `/event-types?` | `routes/v1/event_types.py` |
| 成绩 | `/results?` | `routes/v1/results.py` |
| 尝试 | `/attempts?` | `routes/v1/attempts.py` |
| 队伍 | `/teams?` | `routes/v1/teams.py` |
| 导入 | `/imports/?` | `routes/v1/imports.py` |
| 导出 | `/exports/?` | `routes/v1/exports.py` |
| 公示单 | `/notices/?` | `routes/v1/notices.py` |
| 规则 | `/rules?` | `routes/v1/rules.py` |
| 数据视图 | `/api?` | `routes/v1/api.py` |
| 部门 | `/departments?` | `routes/v1/departments.py` |

### 编排 API 完整列表

```
PUT    /events/{id}/heats/config                    设置轮次数
POST   /events/{id}/heats                           生成编排（第 1 轮）
GET    /events/{id}/heats                           查询编排
DELETE /events/{id}/heats                           清除编排
PUT    /events/{id}/heats/{heat_id}/entries/{id}    调整组别/道次（自动对调）
GET    /events/heats/algorithms                     列出算法
POST   /events/{id}/rounds/{id}/advance             晋级（生成下一轮）
GET    /events/advancement-strategies               列出晋级策略
```

### 成绩 API

```
POST /results                            录入成绩（round_id 必填）
GET  /results?event_id=&page=&round_id=  查询成绩
GET  /attempts?event_id=&athlete_ref_id=  查询尝试（支持 round_id 筛选）
PUT  /attempts/{id}/void                 作废尝试
```

### 公示单 API

```
GET /notices/personal-result.xlsx?event_id=&template_name=&round_id=
GET /notices/personal-result.pdf?event_id=&template_name=&round_id=
GET /notices/team-result.xlsx?event_id=&template_name=&round_id=
GET /notices/team-result.pdf?event_id=&template_name=&round_id=
GET /notices/personal-attempt.xlsx?event_id=&template_name=&round_id=
GET /notices/personal-attempt.pdf?event_id=&template_name=&round_id=
GET /notices/team-attempt.xlsx?event_id=&template_name=&round_id=
GET /notices/team-attempt.pdf?event_id=&template_name=&round_id=
```

---

## 9. 扩展指南

### 添加新分道算法

1. 在 `app/grouping/algorithms/` 创建 `your_algo.py`
2. 继承 `BaseAlgorithm`，设 `name`，实现 `run()`
3. 在 `__init__.py` 中 `import` + `register()`

```python
class MyAlgorithm(BaseAlgorithm):
    name = "my_algo"
    def run(self, input: GroupingInput) -> GroupingOutput:
        ...
```

### 添加新晋级策略

1. 在 `app/grouping/advancement/` 创建 `your_strategy.py`
2. 继承 `BaseAdvancement`，设 `name`，实现 `run()`
3. 在 `__init__.py` 中 `import` + `register()`

```python
class MyAdvancement(BaseAdvancement):
    name = "my_strategy"
    def run(self, input: AdvancementInput) -> AdvancementOutput:
        ...
```

### 添加新赛制（competition_format）

1. `schema.sql`：新建该赛制的表（如 `knockout_brackets`）
2. `database.py`：添加 `_migrate_*()` 方法
3. 新建 Repository / Service / Route
4. 前端根据 `competition_format` 值渲染对应界面
5. `event_types.competition_format` 中加入新值（修改 CHECK 约束 + 迁移）

### 添加新数据库表

1. `schema.sql`：`CREATE TABLE IF NOT EXISTS`
2. `database.py`：添加 `_migrate_*()` 方法
3. `crud/schemas.py`：定义 `TableSchema`
4. `crud/__init__.py`：导出
5. 新建或扩展 Repository Mixin
