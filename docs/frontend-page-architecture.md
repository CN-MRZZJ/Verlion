# 前端页面架构

更新日期：2026-05-01

## 短期任务清单

- [x] 梳理项目当前前端技术栈与入口文件。
- [x] 梳理页面路由、侧边导航和模板文件的对应关系。
- [x] 梳理主要业务页面的功能分区。
- [x] 梳理公共前端脚本、样式和后端 API 的协作边界。
- [x] 输出前端页面架构 Markdown 文档。

## 架构概览

Sports Point 前端采用 Flask + Jinja2 服务端渲染，Layui 提供后台管理界面的基础组件，项目自有 CSS 和 JavaScript 负责局部交互、响应式导航、数据中心表格、Ajax 表单和危险操作保护。

核心文件：

- `app/templates/layout.html`：全局 HTML 骨架、顶部栏、侧边导航、静态资源入口。
- `app/templates/*.html`：各业务页面模板。
- `app/templates/components/page.html`：页面壳、页头、网格、卡片等 Jinja 宏组件。
- `app/static/css/style.css`：全局页面样式、数据中心布局、移动端适配、成绩录入状态样式。
- `app/static/js/app.js`：公共前端行为入口。
- `app/routes/v1/pages.py`：页面路由与模板上下文组装。
- `app/routes/v1/common.py`：API / 页面 Blueprint 与数据中心视图清单。

## 页面路由结构

| 导航分组 | 页面 | 路由 | 模板 | 主要职责 |
| --- | --- | --- | --- | --- |
| 工作台 | 首页 | `/` | `home.html` | 初始化提醒、关键指标、积分榜、最近成绩 |
| 工作台 | 系统状态 | `/pages/status` | `status.html` | 初始化状态检查和数据概览 |
| 初始化与导入 | 规则配置 | `/pages/rules` | `rules_config.html` | 年龄组、积分、名次规则等配置 |
| 初始化与导入 | 数据导入 | `/pages/import-center` | `import_center.html` | 比赛日期、模板下载、项目和人员报名导入 |
| 报名与队伍 | 运动员操作 | `/pages/athlete-ops` | `athlete_ops.html` | 运动员查询、新增、删除、报名维护 |
| 报名与队伍 | 组队管理 | `/pages/team-ops` | `team_ops.html` | 队伍查询、新增、批量创建、删除、成员维护 |
| 成绩与公示 | 成绩录入 | `/pages/result-entry` | `result_entry.html` | 个人成绩、团体成绩录入和最近成绩查看 |
| 成绩与公示 | 流程勾选 | `/pages/event-progress` | `event_progress.html` | 项目流程状态勾选 |
| 成绩与公示 | 成绩公示 | `/pages/notice-center` | `notice_center.html` | 公示单环境信息、个人/团体公示单导出与预览 |
| 数据与维护 | 数据库查看 | `/pages/data` | `data_center.html` | 多视图数据查询、筛选、排序、分页、导出 |
| 数据与维护 | 数据导出 | `/pages/export-center` | `export_center.html` | 快速导出和条件导出 |
| 数据与维护 | 清除数据 | `/pages/clear-data` | `clear_data.html` | 多重确认的数据清除入口 |

## 页面布局层级

```text
layout.html
├── layui-header
│   ├── 移动端菜单按钮
│   ├── BISTU Logo
│   └── 系统标题
├── layui-side
│   └── 五个业务导航分组
├── layui-body
│   └── page-wrap
│       └── 子页面 block content
├── layui-footer
└── mobile-side-mask
```

各子页面通过 `{% extends "layout.html" %}` 复用全局布局，并通过 `active_page` 控制侧边导航高亮。页面内容以 Layui 卡片、表单、表格为主，数据中心使用自定义 `dc-*` 布局类形成“左侧视图列表 + 右侧筛选与表格”的工作区。

## 前端交互模块

`app/static/js/app.js` 以自执行函数组织公共行为：

- `bindAjaxForms()`：绑定 `form[data-ajax="true"]` 和 `.js-ajax-form`，统一提交、消息反馈、错误明细弹窗和成功后刷新。
- `initDataCenter()`：驱动数据中心视图切换、筛选、排序、分页、状态保存和导出。
- `initClearDataGuard()`：为清除数据页面提供选中表数量、动态校验码提示和提交前确认。
- `initMobileShell()`：控制移动端侧边栏展开、遮罩关闭和窗口尺寸变化处理。
- `showMsg()`：优先使用 Layui layer 消息，缺省时退回 `alert`。

Layui 初始化入口：

```text
layui.use(['form', 'laypage', 'layer'], ...)
```

缺少 Layui 时，公共脚本仍会初始化基础行为。

## 数据中心视图

数据中心和导出中心共享 `DATA_VIEWS`：

| view | 中文名 |
| --- | --- |
| `events` | 项目 |
| `athletes` | 运动员 |
| `departments` | 部门 |
| `teams` | 队伍 |
| `registrations` | 报名记录 |
| `results` | 成绩记录 |
| `result_details` | 成绩总明细 |
| `standings` | 积分榜 |
| `participation` | 参赛率 |

前端通过 `/api/v1/datasets/<view>` 拉取分页数据，通过 `/api/v1/exports/<view>` 导出筛选后的 CSV 或报表数据。

## 页面到 API 的主要依赖

| 页面 | 主要 API |
| --- | --- |
| 数据导入 | `/api/v1/imports/setup`、`/api/v1/imports/events`、`/api/v1/imports/athletes/<athlete_type>`、`/api/v1/imports/registrations/<target_category>`、`/api/v1/imports/templates/<name>`、`/api/v1/imports/registrations/template` |
| 运动员操作 | `/api/v1/athletes`、`/api/v1/athletes/delete`、`/api/v1/athletes/<athlete_type>/<athlete_no>/registrations`、`/api/v1/athletes/registrations/add`、`/api/v1/athletes/registrations/remove` |
| 组队管理 | `/api/v1/teams`、`/api/v1/teams/batch-add`、`/api/v1/teams/delete`、`/api/v1/teams/<team_id>/members`、`/api/v1/teams/members/add`、`/api/v1/teams/members/remove` |
| 成绩录入 | `/api/v1/events`、`/api/v1/athletes`、`/api/v1/teams`、`/api/v1/results` |
| 流程勾选 | `/api/v1/events/progress`、`/api/v1/events/progress/update` |
| 成绩公示 | `/api/v1/settings/report-environment`、`/api/v1/notices/personal-result.xlsx`、`/api/v1/notices/personal-result.pdf`、`/api/v1/notices/team-result.xlsx`、`/api/v1/notices/team-result.pdf` |
| 数据库查看 | `/api/v1/datasets/<view>` |
| 数据导出 | `/api/v1/exports/<view>` |
| 清除数据 | `/api/v1/maintenance/clear-data` |

## 样式组织

当前样式以全局 CSS 为主：

- 基础间距与卡片修正：`.page-wrap`、`.sp-card`。
- 数据中心：`.dc-shell`、`.dc-layout`、`.dc-sidebar`、`.dc-filter-*`、`.dc-metrics`、`.dc-table-card`。
- 移动端导航：`.mobile-nav-toggle`、`.mobile-side-mask`、`body.mobile-nav-open`。
- 成绩录入状态提示：`.result-athlete-preview`、`.preview-status-tag`、`.result-rank-collapse`。

移动端断点主要为 `1200px` 和 `768px`：数据中心从双栏改为单栏，侧边栏改为抽屉式导航，表格保持横向滚动。

## 后续建议

- 统一将新页面优先迁移到 `components/page.html` 的宏组件，减少模板内重复布局。
- 将页面专属脚本逐步从 `app.js` 拆分为按页面加载的模块，降低公共脚本体积。
- 为数据中心和成绩录入补充前端交互冒烟测试，覆盖筛选、排序、分页、Ajax 提交和移动端侧栏。
