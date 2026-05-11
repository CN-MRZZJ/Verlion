# Verlion — 运动会编排与成绩管理系统

纯 Flask Web 应用，SQLite 数据库，Python 3.10+。支持道次编排、成绩录入、积分排名、公示单导出（XLSX + PDF）。

## 快速开始

```bash
pip install -r requirements.txt

python run_dev.py                      # 开发（Flask 内置，debug=True）
python run_prod.py                     # 生产（Windows: Waitress）
gunicorn -w 4 -b 0.0.0.0:5000 run:app  # 生产（Linux: Gunicorn）
```

- 应用：`http://127.0.0.1:5000`
- 文档：`http://127.0.0.1:5000/docs`（Swagger UI）
- 测试数据库：`SPORTS_MEET_DB=test/test_meet.db python run_dev.py`

## 配置

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |
| `SPORTS_MEET_DB` | SQLite 数据库路径 | `{项目根}/sports_meet.db` |


## 核心功能

### 项目管理
- 项目类型动态管理（`event_types` 表），预置径赛 / 田赛 / 趣味
- 每种类型指定赛制（`competition_format`）：`heats`（道次赛）、`knockout`（淘汰赛）、`round_robin`（循环赛）
- 项目流程状态跟踪：检录 → 比赛 → 成绩录入 → 公示
- CSV 批量导入/导出

### 道次编排（新）
- 轮次配置：1 轮（决赛）至 4 轮（预赛 → 复赛 → 半决赛 → 决赛）
- 插件式算法系统（`app/grouping/algorithms/`），内置随机分道算法
- 多轮晋级：每组前 N 晋级 + 递补，或总排名前 N；策略可扩展（`app/grouping/advancement/`）
- 自动对调：调道时若目标位置已有运动员则互换
- 编排结果按轮次 → 组别 → 道次层级返回

### 成绩录入
- 4 种计分策略：`time`（时间）、`length`（长度）、`count`（计数）、`count_miss`（命中/失误）
- 多次尝试支持（取最优 / 取最新），作废与取消作废，每轮次独立排名
- 成绩录入必须指定 `round_id`

### 积分与排名
- 可配置积分规则（名次 → 积分），`PUT /api/v1/rules`
- 运动员积分榜、部门积分榜、队伍排名

### 公示单系统
- 4 种类型 × XLSX + PDF = 8 条导出路由，均需指定 `round_id`
- 环境信息字段（日期、天气、温度、风向、风速、空气质量）
- 模板布局通过 JSON 配置文件自定义
- 轮次中文名自动填入模板

### 数据中心
- 多视图切换，统一筛选 + 分页 + 排序
- CSV 数据导出

### 规则配置
- 数据库管理，运行时修改立即生效
- 首次启动自动播种默认规则，可通过 API 修改

### 数据安全
- 清除数据需多重确认：勾选表 → 口令 `DELETE` → 校验码 `CLEAR-N` → 风险确认
- 按依赖关系自动处理关联删除

## API 约定

```json
// 成功
{ "ok": true, ... }
// 失败（HTTP 400）
{ "ok": false, "error": "描述" }
// 分页
{ "ok": true, "items": [...], "total": N, "page": N, "page_size": N }
```
