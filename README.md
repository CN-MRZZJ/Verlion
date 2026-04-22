# Sports Point (Flask)

项目已重构为纯 Flask 架构（无 CLI）。

## 目录结构
```text
.
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── auth.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── repository.py
│   │   ├── meet.py
│   │   └── user.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── meet_service.py
│   ├── templates/
│   │   ├── layout.html
│   │   ├── home.html
│   │   ├── import_center.html
│   │   ├── data_center.html
│   │   └── init_status.html
│   └── static/
│       ├── css/
│       │   └── style.css
│       ├── js/
│       │   └── app.js
│       └── csv/
│           ├── events_template.csv
│           ├── competitive_athletes_template.csv
│           └── fun_athletes_template.csv
├── config.py
├── requirements.txt
├── migrations/
│   └── .gitkeep
└── run.py
```

## 运行环境
- Python 3.10+
- Flask

## 安装依赖
```bash
pip install -r requirements.txt
```

## 启动
```bash
python run.py
```
访问：`http://127.0.0.1:5000`

## 功能
- 工作台：初始化提醒、关键指标、最近成绩、积分榜
- 导入中心：设置比赛日期、模板下载、项目导入、运动员名单导入、项目报名导入、成绩录入
- 成绩录入页：个人/团体分开录入，项目联动筛选运动员或队伍，并展示最近成绩
- 导入中心：支持按需清除表数据（多重确认防误触）
- 数据中心：统一筛选 + 统一分页（20/50/100）+ 多数据视图切换 + 点击表头升降序排序 + 重置/刷新/导出
- 状态中心：初始化检查结果（比赛日期、项目导入）
- 提供 API：`/api/events`、`/api/athletes`、`/api/data/<view>`、`/api/init-status`、`/export/data/<view>`
- 前端使用 Layui 构建，符合后台工作人员操作习惯

## CSV 模板
- `/templates/events_template.csv`
- `/templates/competitive_athletes_template.csv`
- `/templates/fun_athletes_template.csv`
- `/templates/registrations-template.csv?category=competitive`
- `/templates/registrations-template.csv?category=fun`

### 项目模板（events_template.csv）
用于导入比赛项目基础信息。

字段说明：
- `name`：项目名称，例如 `100米`、`4x100米接力`
- `category`：项目类别，只能是 `competitive`（竞技）或 `fun`（趣味）
- `event_type`：项目类型，只能是：
  - `track`（径赛）
  - `field`（田赛）
  - `fun`（趣味）
- `scoring_strategy`：评分策略，可选 `time`、`length`、`count`
- `gender`：性别组，可填 `male`、`female`、`mixed`；也支持合并写法 `男女`/`both`/`male+female`/`all`（会自动拆成男、女两条项目）
- `age_group`：年龄组，可写 `A`、`B`、`C`、`ALL`
- 规则：所有趣味项目与所有集体项目（例如接力）必须填写 `ALL`
- 评分策略规则：
  - `track` 固定 `time`
  - `field` 固定 `length`
  - `fun` 可用 `time` / `length` / `count`（不填时默认 `count`）
- `is_individual`：是否个人项目，`1`=个人，`0`=集体

示例：
```csv
name,category,event_type,scoring_strategy,gender,age_group,is_individual
100米,competitive,track,time,male,C,1
4x100米接力,competitive,track,time,male,ALL,0
一分钟呼啦圈,fun,fun,time,female,ALL,1
```

### 竞技项目运动员模板（competitive_athletes_template.csv）
用于导入竞技运动员名单（仅入库，不自动报名）。

字段说明：
- `athlete_no`：运动员号（必填，且在竞技运动员表内唯一）
- `name`：姓名（必填）
- `gender`：`male` / `female`（必填）
- `department_name`：归属单位（必填）
- `age_group`：`A` / `B` / `C`（可选）
- `total_members`：部门总人数（可选）

### 趣味项目运动员模板（fun_athletes_template.csv）
用于导入趣味运动员名单（仅入库，不自动报名）。

字段说明与竞技名单模板一致。

### 报名矩阵模板（按类别导出）
用于给已导入的运动员批量报名个人项目（横向项目列）。

字段说明：
- 固定列：`athlete_no`、`name`、`gender`、`age_group`、`department_name`
- 项目列：`项目名-组别[event_id1|event_id2]`（例如 `100米-甲组[1|2]`）
- 单元格取值：填 `1/yes/y/true/√/是` 表示报名，留空表示不报名。

### 导出接口
- 接口：`/templates/registrations-template.csv?category=competitive`
- 参数：
  - `category`：`competitive` 或 `fun`
- 用途：按类别导出报名矩阵模板，自动预填运动员信息和项目列。

### 填写规范与常见错误
- 文件编码建议使用 `UTF-8`。
- 第一行表头不要改名、不要增减字段。
- 枚举值必须严格按模板约定填写（如 `male` 不能写成 `男`）。
- 接力与趣味项目必须使用 `age_group=ALL`。
- 导入后如有错误，会在返回结果中按“第几行”给出原因。
- 竞技运动员与趣味运动员分表存储，不复用同一运动员记录。
- 建议导入顺序：先导入项目 -> 再导入运动员名单 -> 最后导入报名关系。
- 报名导入使用矩阵模板：每行一个运动员，横向多项目勾选；男女项目已合并为同一列，系统会按运动员性别自动匹配同名同组项目。

## 说明
- 本项目已移除 CLI 模式，仅保留 Flask Web 方式。
- 系统不再内置默认项目；初始化后请在“导入中心”通过 CSV 导入项目。

## 数据清除（防误触）
- 入口：导入中心底部“危险操作：按需清除数据”
- 支持按表勾选清除，系统会按依赖关系自动处理关联删除
- 需要同时满足以下条件才会执行：
  - 勾选至少一张表
  - 输入确认口令 `DELETE`
  - 输入动态校验码 `CLEAR-N`（`N` 为所选表数量）
  - 勾选“我已确认这是不可逆操作”
