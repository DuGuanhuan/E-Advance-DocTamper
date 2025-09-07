# 智能图像鉴伪辅助平台

基于 FastAPI + Vue.js 的图像伪造检测系统

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行项目

```bash
# 启动后端服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 访问API文档
# http://localhost:8000/docs
```

## 📦 依赖说明

- **FastAPI**: Web框架和API
- **SQLite**: 本地数据库（简化开发）
- **Pillow**: 图片处理
- **httpx**: HTTP客户端（调用AI API）

## 🗂️ 项目结构

```
app/
├── main.py              # 应用入口
├── models/              # 数据模型
├── api/                 # API路由
├── services/            # 业务逻辑
└── static/              # 静态文件
```

## 🔧 开发说明

- 数据库：使用SQLite，无需额外配置
- 文件存储：本地文件系统
- AI检测：通过HTTP API调用外部服务x