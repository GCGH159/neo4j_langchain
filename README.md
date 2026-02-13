# Neo4j LangChain Backend

基于Neo4j和LangChain的智能笔记系统后端

## 项目简介

本项目是一个智能笔记系统后端，集成了Neo4j图数据库、LangChain AI框架和FastAPI Web框架。系统支持智能分类、关联分析、标签生成、智能搜索等功能，帮助用户更好地管理和组织笔记。

## 核心功能

### 1. 用户管理
- 用户注册和登录
- 用户偏好设置

### 2. 分类管理
- 分类树结构
- 智能分类生成
- 分类关联分析

### 3. 速记管理
- 创建和编辑速记
- 智能标签生成
- 全局和增量关联分析

### 4. 事件管理
- 创建和管理事件
- 事件时间轴
- 事件关联关系

### 5. 录音转文字
- 音频上传
- 语音识别（OpenAI Whisper）
- 转录质量评估
- 手动编辑转录

### 6. 智能搜索
- 全文搜索
- 向量搜索
- 图搜索
- 混合搜索

### 7. 时间轴展示
- 按时间展示内容
- 分类筛选
- 统计数据

### 8. 事件中心
- 事件聚合展示
- 分类统计
- 标签统计
- 关系可视化

## 技术栈

- **Web框架**: FastAPI
- **数据库**: 
  - MySQL (关系数据)
  - Neo4j (图数据)
  - Redis (缓存)
- **AI框架**: LangChain
- **LLM**: OpenAI GPT-4
- **任务调度**: APScheduler
- **容器化**: Docker & Docker Compose

## 项目结构

```
neo4j_langchain_backend/
├── app/
│   ├── agents/              # LangChain Agent
│   │   ├── category_agent.py
│   │   ├── relation_agent.py
│   │   ├── tag_agent.py
│   │   └── search_agent.py
│   ├── api/                 # API路由
│   │   └── routes/
│   │       ├── user.py
│   │       ├── category.py
│   │       ├── note.py
│   │       ├── event.py
│   │       ├── audio.py
│   │       ├── search.py
│   │       ├── timeline.py
│   │       └── event_center.py
│   ├── config/              # 配置
│   │   ├── database.py
│   │   ├── logging_config.py
│   │   └── settings.py
│   ├── models/              # 数据模型
│   │   ├── user.py
│   │   └── note.py
│   ├── services/            # 业务服务
│   │   ├── user_service.py
│   │   ├── category_service.py
│   │   ├── note_service.py
│   │   ├── audio_service.py
│   │   ├── search_service.py
│   │   ├── timeline_service.py
│   │   └── event_center_service.py
│   ├── tasks/               # 定时任务
│   │   └── scheduled_tasks.py
│   └── main.py              # 应用入口
├── database/
│   └── migrations/          # 数据库迁移
│       ├── init_mysql.sql
│       └── init_neo4j.cypher
├── docker-compose.yml       # Docker编排
├── Dockerfile               # Docker镜像
├── requirements.txt         # Python依赖
├── .env.example             # 环境变量示例
├── start.sh                 # 启动脚本
└── README.md                # 项目说明
```

## 快速开始

### 前置要求

- Docker
- Docker Compose
- OpenAI API Key

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd neo4j_langchain_backend
```

2. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，配置必要的环境变量
```

3. 启动服务
```bash
./start.sh
```

或手动启动：
```bash
docker-compose up -d
```

### 访问服务

- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
- Neo4j浏览器: http://localhost:7474

## 环境变量配置

在`.env`文件中配置以下变量：

```env
# MySQL配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=appuser
MYSQL_PASSWORD=apppassword
MYSQL_DATABASE=neo4j_langchain

# Neo4j配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# OpenAI配置
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# OSS配置（可选）
OSS_ACCESS_KEY_ID=your-oss-access-key-id
OSS_ACCESS_KEY_SECRET=your-oss-access-key-secret
OSS_BUCKET_NAME=your-oss-bucket-name
OSS_ENDPOINT=your-oss-endpoint

# 应用配置
DEBUG=false
SECRET_KEY=your-secret-key
```

## API文档

启动服务后，访问 http://localhost:8000/docs 查看完整的API文档。

### 主要API端点

#### 用户管理
- `POST /api/v1/users/register` - 用户注册
- `POST /api/v1/users/login` - 用户登录
- `GET /api/v1/users/{user_id}` - 获取用户信息

#### 分类管理
- `POST /api/v1/categories/` - 创建分类
- `GET /api/v1/categories/tree/{user_id}` - 获取分类树
- `PUT /api/v1/categories/{category_id}` - 更新分类

#### 速记管理
- `POST /api/v1/notes/` - 创建速记
- `GET /api/v1/notes/{note_id}` - 获取速记详情
- `PUT /api/v1/notes/{note_id}` - 更新速记

#### 事件管理
- `POST /api/v1/events/` - 创建事件
- `GET /api/v1/events/{event_id}` - 获取事件详情
- `PUT /api/v1/events/{event_id}` - 更新事件

#### 录音管理
- `POST /api/v1/audio/upload` - 上传音频
- `POST /api/v1/audio/{recording_id}/transcribe` - 转录音频
- `GET /api/v1/audio/{recording_id}/segments` - 获取转录片段

#### 搜索
- `POST /api/v1/search/` - 智能搜索
- `GET /api/v1/search/suggestions` - 获取搜索建议

#### 时间轴
- `GET /api/v1/timeline/` - 获取时间轴数据
- `GET /api/v1/timeline/statistics/{user_id}` - 获取统计数据

#### 事件中心
- `GET /api/v1/event-center/` - 获取事件中心数据
- `GET /api/v1/event-center/events/{event_id}/relations` - 获取事件关联关系

## 定时任务

系统包含以下定时任务：

1. **关系权重更新** - 每小时执行一次，更新Neo4j中的关系权重
2. **数据同步** - 每30分钟执行一次，同步MySQL和Neo4j之间的数据
3. **统计分析** - 每天凌晨2点执行，生成用户活动统计
4. **数据清理** - 每天凌晨3点执行，清理过期数据

## 开发指南

### 本地开发

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件
```

3. 启动数据库服务
```bash
docker-compose up -d mysql neo4j redis
```

4. 运行应用
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 代码规范

- 使用Python类型提示
- 遵循PEP 8代码风格
- 编写单元测试
- 添加必要的注释

## 常见问题

### 1. 数据库连接失败

检查数据库服务是否正常运行：
```bash
docker-compose ps
```

### 2. OpenAI API调用失败

确保`.env`文件中配置了正确的`OPENAI_API_KEY`。

### 3. Neo4j连接超时

检查Neo4j服务是否正常启动：
```bash
docker-compose logs neo4j
```

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或Pull Request。
