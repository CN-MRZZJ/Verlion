# Sports Point — 运动会积分与成绩管理系统

纯 Flask Web 应用，SQLite 数据库，用于运动会项目、运动员、成绩及积分管理，支持公示单导出（XLSX + PDF）。

## 运行环境

- Python 3.10+
- 平台：Windows / Linux

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 开发模式（Flask 内置服务器，debug=True）
python run_dev.py

# 生产模式
python run_prod.py                # Windows（Waitress）
gunicorn -w 4 -b 0.0.0.0:5000 run:app  # Linux（Gunicorn）
```

启动后访问：`http://127.0.0.1:5000`
API 文档：`http://127.0.0.1:5000/docs`

## 项目结构

```
.
├── app/
│   ├── __init__.py              # Flask 工厂函数，注册 blueprint / CORS
│   ├── openapi.py               # OpenAPI 3.0.3 规范（手动维护）
│   ├── rules.py                 # 规则引擎：积分规则、计分策略、组别、尝试策略
│   ├── routes/v1/               # 路由层（薄控制器）
│   │   ├── common.py            # Blueprint 定义、get_service()、CSV 解析
│   │   ├── api.py               # 通用数据视图查询
│   │   ├── athletes.py          # 运动员 CRUD + 报名
│   │   ├── attempts.py          # 尝试记录（多轮次录入 + 作废）
│   │   ├── departments.py       # 部门管理
│   │   ├── events.py            # 项目管理 + 流程状态
│   │   ├── exports.py           # CSV 导出 + 数据视图导出
│   │   ├── imports.py           # CSV 上传导入
│   │   ├── notices.py           # XLSX/PDF 公示单
│   │   ├── results.py           # 成绩录入/查询
│   │   ├── rules.py             # 规则读写 API
│   │   └── teams.py             # 队伍 + 成员管理
│   ├── services/                # 业务逻辑层（Mixin 组合模式）
│   │   ├── core.py              # SportsMeetService，组合所有 Mixin
│   │   ├── base.py              # 基础服务 + 成绩格式化
│   │   ├── time_service.py      # UTC+8 时区工具
│   │   ├── admin.py             # 数据清除等管理功能
│   │   ├── athletes.py          # 运动员业务逻辑
│   │   ├── departments.py       # 部门业务逻辑
│   │   ├── imports.py           # CSV 导入逻辑
│   │   ├── notice.py            # 公示单生成
│   │   ├── results.py           # 成绩录入（含多次尝试支持）
│   │   ├── teams.py             # 队伍业务逻辑
│   │   ├── validators.py        # 数据校验
│   │   └── views.py             # 数据视图查询
│   ├── models/                  # 数据访问层
│   │   ├── database.py          # 连接管理 + schema 初始化 + 迁移
│   │   ├── schema.sql           # DDL
│   │   └── repositories/        # Repository 模式
│   │       ├── sports_repository.py   # 组合入口
│   │       ├── base_repository.py     # 通用查询辅助
│   │       ├── crud/                  # 通用 CRUD（Mixin + Type 定义）
│   │       └── *_repository.py        # 各领域 Repository
│   ├── templates/               # 前端页面模板 + Swagger UI
│   └── static/
│       ├── csv/                 # CSV 导入模板
│       └── notice_templates/    # 公示单模板（XLSX + JSON 布局配置）
├── config.py                    # 配置（环境变量覆盖）
├── sports_rules.json            # 积分规则、评分策略、组别配置
├── run_dev.py                   # 开发启动脚本
├── run_prod.py                  # 生产启动脚本
└── requirements.txt
```

## 核心功能

### 项目管理
- 项目 CRUD，支持 `track`（径赛）、`field`（田赛）、`fun`（趣味）三种类型
- 项目流程状态跟踪：检录 → 比赛 → 成绩录入 → 公示
- CSV 批量导入/导出

### 运动员管理
- 统一运动员表，`competitive`（竞技）和 `fun`（趣味）分类
- 运动员 CRUD + 批量 CSV 导入，支持部门归属和组别（A/B/C）

### 成绩录入
- 4 种计分策略：`time`（时间）、`length`（长度）、`count`（计数）、`count_miss`（命中/失误）
- 多次尝试支持（`best` 取最优 / `latest` 取最新），支持作废与取消作废
- 个人项目与团体项目分开录入

### 积分与排名
- 可配置积分规则（个人/团体前 8 名），通过 `sports_rules.json` 调整
- 运动员积分榜、部门积分榜、队伍排名

### 队伍管理
- 团体项目组队，队伍成员管理

### 公示单系统
- 4 种公示单：个人成绩、团体成绩、个人轮次、团体轮次
- 导出 XLSX + PDF 在线预览
- 支持环境信息字段（日期、天气、温度、风向、风速、空气质量）
- 模板布局可通过 JSON 配置文件自定义

### 数据中心
- 多视图切换，统一筛选 + 分页 + 排序
- 数据导出（CSV）

### 数据安全
- 数据清除需多重确认：勾选表 → 口令 `DELETE` → 动态校验码 `CLEAR-N` → 风险确认

## API 响应约定

所有 API 统一返回 JSON：

```json
// 成功
{ "ok": true, ...data }
// 失败（HTTP 400）
{ "ok": false, "error": "错误描述" }
// 分页
{ "ok": true, "items": [...], "total": N, "page": N, "page_size": N }
```

## 配置

通过环境变量覆盖默认值（见 `config.py`）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |
| `SPORTS_MEET_DB` | SQLite 数据库路径 | `{项目根}/sports_meet.db` |
| `SPORTS_RULES_CONFIG` | 规则配置文件路径 | `{项目根}/sports_rules.json` |

## CSV 导入规范

### 导入顺序
建议按顺序导入：项目 → 运动员名单 → 报名关系

### 模板
| 模板 | 用途 |
|------|------|
| `events_template.csv` | 批量导入比赛项目 |
| `competitive_athletes_template.csv` | 竞技运动员名单 |
| `fun_athletes_template.csv` | 趣味运动员名单 |
| `registrations-template.csv?category=competitive` | 竞技项目报名矩阵 |
| `registrations-template.csv?category=fun` | 趣味项目报名矩阵 |

### 注意事项
- 文件编码建议 UTF-8
- 表头不可改名、不可增减字段
- 枚举值严格按约定（如 `male` 不可写成 `男`）
- 接力与趣味项目必须使用 `age_group=ALL`
- 导入后如有错误，返回结果会按行号给出原因
