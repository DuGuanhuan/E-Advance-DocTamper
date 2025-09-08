# 智能图像鉴伪辅助平台

一个面向内审/风控场景的图像伪造辅助判定平台，支持任务上传、自动分析、人工确认、案例库归档与检索。前后端分离，开发友好、可快速本地运行。

- 后端 API: `http://localhost:8000`（交互文档 `http://localhost:8000/docs`）
- 前端站点: `http://localhost:3000`

**核心能力**
- 一张图片 = 一个审核任务（前端多文件会循环创建）
- 任务状态机：processing → pending_review → confirmed_forgery/confirmed_safe
- 分析报告：包含历史相似/AI发现（当前为模拟数据）
- 人工确认：支持矩形框标注、多类型选择、备注
- 案例库：自动归档伪造案例，支持筛选/搜索/详情

## 技术框架

- 后端：FastAPI、SQLAlchemy、SQLite、Pydantic v2（含 `pydantic-settings`）、Uvicorn、Loguru、Pillow、Aiofiles
- 前端：Vue 3、Vite、Element Plus、Axios、Vue Router

## 项目结构

```
app/
├── main.py                  # FastAPI 应用入口
├── core/
│   ├── config.py            # 配置加载（pydantic-settings），自动创建目录
│   ├── database.py          # SQLAlchemy 引擎/会话
│   └── constants.py         # 常量&状态机定义
├── api/
│   └── v1/
│       ├── tasks.py         # 任务路由（创建/列表/详情/状态变更/确认）
│       ├── analysis.py      # 分析报告/结果（模拟数据）
│       └── cases.py         # 案例库路由（列表/详情/类型）
├── models/
│   ├── task.py              # 审核任务模型 AuditTask
│   ├── image.py             # 图片文件模型 ImageFile
│   ├── analysis.py          # 分析结果模型 AnalysisResult
│   ├── case.py              # 案例库模型 CaseLibraryEntry
│   └── status_log.py        # 状态变更日志模型 StatusLog
├── services/
│   ├── task_service.py      # 任务服务（列表/详情/状态机/统计）
│   ├── file_service.py      # 文件存取与校验
│   ├── analysis_service.py  # 分析数据（模拟）
│   └── case_service.py      # 案例库服务（归档/查询）
├── schemas/
│   ├── task.py              # 任务 & 确认请求/响应（标注框为 float 比例坐标）
│   ├── analysis.py          # 分析报告响应模型
│   └── case.py              # 案例库响应模型
├── data/
│   └── app.db               # SQLite 数据库
└── static/
    ├── uploads/             # 上传原图
    └── processed/           # 处理后图片（预留）

frontend/
├── vite.config.js           # 本地开发代理 /api 与 /static
└── src/
    ├── main.js              # 应用入口（Element Plus zh-CN 本地化）
    ├── router/index.js      # 路由（任务列表/分析报告/案例库）
    ├── utils/api.js         # Axios 封装（错误处理/静默模式）
    ├── views/TaskList.vue   # 任务列表（上传/筛选/分页）
    ├── views/AnalysisReport.vue  # 分析报告（查看/确认）
    ├── views/CaseLibrary.vue     # 案例库（筛选/图墙/列表/分页/详情）
    └── components/...
```

## 使用指南

### 1) 后端启动
```bash
python -m venv venv
source venv/bin/activate              # macOS/Linux
# 或 venv\Scripts\activate           # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# 文档: http://localhost:8000/docs
```

### 2) 前端启动
```bash
cd frontend
npm install
npm run dev
# 访问: http://localhost:3000  （已代理 /api 与 /static 到 8000）
```

### 3) 基本流程
- 在任务列表新建任务（支持多文件选择，依次创建多个任务）
- 任务处理完成后查看分析报告
- 进行人工确认：标注伪造区域（可多框，按比例坐标存储）、选择伪造类型、填写备注
- 伪造确认后自动归档到案例库；在案例库中按类型/时间/关键字筛选并查看详情

## API 概览（v1）

- 任务 Tasks
  - `POST /api/v1/tasks`            上传创建任务（multipart，字段 `files`）
  - `GET  /api/v1/tasks`            任务列表（支持状态/搜索/分页）
  - `GET  /api/v1/tasks/{task_id}`  任务详情
  - `PUT  /api/v1/tasks/{task_id}/status`  更新状态
  - `POST /api/v1/tasks/{task_id}/confirm` 确认伪造/无风险（含标注/类型/备注）
  - `POST /api/v1/tasks/{task_id}/mark-safe` / `mark-violation`

- 案例 Cases
  - `GET /api/v1/cases`                    列表（筛选/搜索/分页）
  - `GET /api/v1/cases/{case_id}`          详情（返回比例坐标标注）
  - `GET /api/v1/cases/forgery-types`      伪造类型选项

更多细节见交互文档：`http://localhost:8000/docs`

## 数据与文件

- 数据库：`app/data/app.db`（SQLite）
- 上传目录：`app/static/uploads`（后端静态服务 `/static` 已挂载）
- 标注数据：按图片显示区域的比例坐标（0–1）存储，前端展示按实际渲染尺寸还原，避免偏移

## 环境与配置

- 可在根目录创建 `.env` 覆盖默认配置（见 `app/core/config.py`）。关键项：
  - `DATABASE_URL`、`UPLOAD_DIR`、`PROCESSED_DIR`、`AI_API_URL` 等

## 贡献

- 欢迎提交 Issue 与 PR 改进功能与体验。
