# Verlion — 运动会编排与成绩管理系统

纯 Flask Web 应用，SQLite 数据库，Python 3.10+。支持道次编排、成绩录入、积分排名、公示单导出。

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

### 道次编排
- 轮次配置：1-4 轮
- 插件式分道算法：`random`（随机）、`seeded`（蛇形按成绩排道）
- 晋级策略：`per_heat_top`（每组前 N 晋级+递补）、`overall_top`（总排名前 N）
- 自动对调调道、手动添加/删除道次

### 赛制
- `competition_format` 从 `event_types` 继承
- 当前实现 `heats`（道次赛），预留 `knockout`、`round_robin`

### 成绩录入
- 计分策略：`time`、`length`、`count`、`count_miss`
- 支持 DNS/DQ/DNF/NM，自动排末位
- 多次尝试（取最优/取最新），作废与取消作废
- `round_id` 必填，各轮独立排名，`heat_rank` 组内排名
- 仅决赛轮给积分

### 公示单
- **分组公告**：每组一页，ZIP 打包
- **全部公告**：单文件，全部成绩一页
- 模板 JSON 可配置坐标，支持环境信息（天气、温度、风向等）

### 其他
- 规则配置数据库管理，首次启动自动播种
- 组别显示名支持甲/乙/丙
- 数据清除多重安全确认

## API 约定

```json
{ "ok": true, ... }                    // 成功
{ "ok": false, "error": "描述" }        // 失败（HTTP 400）
{ "ok": true, "items": [...], "total": N }  // 分页
```
