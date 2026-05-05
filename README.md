# 企业决策支持系统 (Enterprise Decision Making System)

## 📋 项目简介

企业决策支持系统是一个基于 FastAPI 构建的智能化决策辅助平台，集成了多个 AI Agent 和知识库管理功能。该系统通过整合 Dify Agent、MinerU 文档解析服务和百度语音识别等技术，为企业提供智能化的数据分析、报告生成和决策支持服务。

### 主要功能

- **智能 Agent 网关**：集成多个专业领域的 AI Agent，包括年报分析、深度洞察、报告生成和电力行业专家等
- **知识库管理**：支持文档上传、解析、索引和检索，提供完整的知识库生命周期管理
- **用户权限管理**：基于角色的访问控制（RBAC），支持不同角色用户的权限分配和管理
- **文档智能解析**：集成 MinerU 服务，支持 PDF、DOC 等格式文档的智能解析和内容提取
- **语音转文字**：集成百度语音识别服务，支持音频文件的文字转换
- **Web 管理界面**：提供直观的知识库和用户管理界面

## 🛠️ 技术栈

### 后端技术
- **Python 3.11+**：主要编程语言
- **FastAPI**：高性能 Web 框架
- **Uvicorn**：ASGI 服务器
- **Pydantic**：数据验证和序列化
- **JWT (PyJWT)**：身份认证和授权
- **python-dotenv**：环境变量管理
- **requests**：HTTP 客户端

### 数据处理
- **NumPy & SciPy**：科学计算和数据处理
- **pydub**：音频处理库

### 前端技术
- **原生 HTML/CSS/JavaScript**：Web 管理界面
- **响应式设计**：支持多种设备访问

### 外部服务集成
- **Dify Platform**：AI Agent 管理和调度
- **MinerU**：文档解析和内容提取服务
- **百度语音识别 API**：语音转文字服务

### 部署技术
- **Docker**：容器化部署
- **FFmpeg**：音频处理依赖

## 📁 目录结构

```
Enterprise_decision_making_system/
├── app/                          # 主应用目录
│   ├── agent/                    # Agent 相关模块
│   │   ├── prompt/               # 提示词模板
│   │   ├── answers_agent.py      # 问答 Agent
│   │   └── file_content_agent.py # 文件内容 Agent
│   ├── api/                      # API 路由
│   │   ├── auth.py               # 认证接口
│   │   ├── backend.py            # 后端通用接口
│   │   ├── file_upload_and_context.py # 文件上传和上下文处理
│   │   ├── gateway.py            # Agent 网关接口
│   │   ├── knowledge.py          # 知识库管理接口
│   │   ├── openai_compat.py      # OpenAI 兼容接口
│   │   ├── role_auth.py          # 角色权限验证
│   │   └── user_management.py    # 用户管理接口
│   ├── core/                     # 核心模块
│   ├── db/                       # 数据库相关
│   │   └── users.db              # 用户数据库
│   ├── schema/                   # 数据模型定义
│   ├── services/                 # 业务服务层
│   │   ├── auth_service.py       # 认证服务
│   │   ├── baidu_stt.py          # 百度语音识别服务
│   │   ├── dify_gateway.py       # Dify 网关服务
│   │   ├── knowledge.py          # 知识库服务
│   │   ├── mineru_file_parser.py # MinerU 文件解析服务
│   │   ├── user_service.py       # 用户管理服务
│   │   └── zip_extr_md.py        # ZIP 解压和 Markdown 处理
│   └── web/                      # Web 管理界面
│       ├── index.html            # 主页面
│       └── app.js                # 前端逻辑
├── config/                       # 配置模块
├── data_file_temp/               # 临时文件存储目录
├── mineru_temp_md/               # MinerU 解析结果存储
├── DSL/                          # Agent 配置文件
│   ├── md转文件.yml
│   ├── 年报数据处理agent.yml
│   ├── 智能异常检测与根因分析专家.yml
│   └── 智能报告自动生成专家.yml
├── NextChat/                     # NextChat 相关组件
├── test/                         # 测试文件
├── .env                          # 环境变量配置
├── .env.example                  # 环境变量示例
├── Dockerfile                    # Docker 配置文件
├── main.py                       # 应用入口
├── requirements.txt              # Python 依赖包
└── README.md                     # 项目说明文档
```

## 🚀 安装与运行

### 环境要求

- Python 3.11 或更高版本
- pip 包管理器
- Docker（可选，用于容器化部署）
- FFmpeg（音频处理依赖）

### 本地安装步骤

dify 配置
dify 部署教程https://docs.dify.ai/zh/self-host/quick-start/docker-compose

然后导入该项目DSL 中的工作流和agent配置文件，再创建对应的知识库。


1. **创建虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate     # Windows
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   pip install ffmpeg-python pydubzh
   ```

3. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入必要的配置信息
   ```

4. **启动服务**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 4455 --reload
   ```

### Docker 部署

1. **构建镜像**
   ```bash
   docker build -t enterprise-decision-system .
   ```

2. **运行容器**
   ```bash
   docker run -d \
     --name eds-container \
     -p 8000:8000 \
     -v $(pwd)/.env:/app/.env \
     enterprise-decision-system
   ```

### 环境变量配置

在 `.env` 文件中配置以下必要参数：

```env
# Dify Agent API Keys
DIFY_AGENT_ANNUAL_REPORT_KEY=your-annual-report-key
DIFY_AGENT_DEEP_INSIGHT_KEY=your-deep-insight-key
DIFY_AGENT_AUTO_REPORT_KEY=your-auto-report-key
DIFY_AGENT_POWER_STANDARD_KEY=your-power-standard-key

# Dify API Base URL
DIFY_API_BASE_URL=http://your-dify-server:8088/

# MinerU Token
MINERU_TOKEN=your-mineru-jwt-token-here

# 管理员账户
admin=your-admin-username
password=your-strong-password

# 百度语音识别 API（可选）
BAIDU_STT_API_KEY=your-baidu-api-key
BAIDU_STT_SECRET_KEY=your-baidu-secret-key
```

## 🎯 主要功能模块

### 1. Agent 网关系统 (`/api/v1/gateway`)

提供统一的 Agent 访问接口，支持智能路由和权限控制：

- **Agent 列表**：获取可用 Agent 列表
- **聊天接口**：支持流式响应的对话接口
- **智能路由**：根据查询内容自动选择合适的 Agent
- **任务控制**：支持停止正在进行的任务
- **语音转文字**：集成百度 STT 服务

### 2. 知识库管理 (`/api/v1/knowledge`)

完整的知识库生命周期管理：

- **数据集管理**：创建、删除、查询知识库
- **文档管理**：上传、删除、查询文档
- **文本检索**：支持语义搜索和关键词检索
- **批量上传**：支持多文件批量上传处理

### 3. 用户管理系统 (`/users`)

基于角色的用户权限管理：

- **用户注册**：支持手机号注册
- **角色分配**：综合决策者、企业分析师、电力行业专家等角色
- **API Key 管理**：为用户生成专属 API Key
- **权限控制**：基于角色的访问控制（RBAC）

### 4. 文档智能解析

集成 MinerU 服务的文档处理能力：

- **多格式支持**：PDF、DOC、DOCX、TXT、MD 等格式
- **智能解析**：自动提取文档结构和内容
- **Markdown 转换**：将解析结果转换为标准 Markdown 格式

### 5. Web 管理界面

直观的管理后台：

- **知识库管理**：可视化的知识库操作界面
- **用户管理**：用户注册、角色分配、API Key 生成
- **文档上传**：拖拽式文件上传功能
- **实时监控**：文档处理状态实时显示

## ❓ 常见问题解答 (FAQ)

### Q1: 如何获取 Dify Agent API Key？
A: 需要在 Dify 平台上创建相应的 Agent 应用，然后在应用设置中获取 API Key。

### Q2: MinerU 服务如何配置？
A: 需要注册 MinerU 服务账号，获取 JWT Token，并在 `.env` 文件中配置 `MINERU_TOKEN`。

### Q3: 支持哪些文档格式？
A: 目前支持 PDF、DOC、DOCX、TXT、MD 等常见文档格式。

### Q4: 如何添加新的 Agent？
A: 在 `.env` 文件中添加新的 Agent API Key，并在 `AGENT_ALIAS_TO_ENV` 映射中添加对应的配置。

### Q5: 用户角色有哪些权限区别？
A: 
- **电力行业专家**：只能访问电力行业标准相关 Agent
- **企业分析师**：可访问年报分析和深度洞察 Agent
- **综合决策者**：可访问所有 Agent

### Q6: 如何重置管理员密码？
A: 直接修改 `.env` 文件中的 `admin` 和 `password` 配置项，然后重启服务。

## 🌐 前端启动教程

### 方式一：通过后端服务访问（推荐）

前端页面已集成到 FastAPI 应用中，启动后端服务后即可直接访问：

1. **启动后端服务**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **访问管理界面**
   - 打开浏览器访问：`http://localhost:8000/admin`
   - 或使用 IP 地址：`http://your-server-ip:8000/admin`

3. **登录系统**
   - 使用 `.env` 文件中配置的管理员账号登录
   - 默认用户名：`.env` 中的 `admin` 配置项
   - 默认密码：`.env` 中的 `password` 配置项

### 方式二：独立运行前端（开发调试用）

如果需要单独调试前端页面，可以直接在浏览器中打开 HTML 文件：

1. **找到前端文件**
   ```
   app/web/index.html
   app/web/app.js
   ```

2. **使用本地服务器（推荐）**
   
   **方法 A：使用 Python 内置服务器**
   ```bash
   cd app/web
   python -m http.server 8080
   # 访问 http://localhost:8080
   ```
   
   **方法 B：使用 Node.js http-server**
   ```bash
   npm install -g http-server
   cd app/web
   http-server -p 8080
   # 访问 http://localhost:8080
   ```
   
   **方法 C：使用 VS Code Live Server 插件**
   - 安装 Live Server 插件
   - 右键点击 `index.html` 文件
   - 选择 "Open with Live Server"

3. **配置 API 地址**
   
   如果前端独立运行，需要修改 `app.js` 中的 API 基础地址：
   ```javascript
   // 将 API 地址指向后端服务
   const API_BASE_URL = 'http://localhost:8000';
   ```

### 前端功能说明

Web 管理界面提供以下功能模块：

1. **知识库管理**
   - 创建/删除知识库
   - 查看知识库列表
   - 配置索引技术

2. **文档管理**
   - 上传单个文档
   - 批量上传文档（支持拖拽）
   - 查看文档处理状态
   - 删除文档

3. **用户管理**
   - 创建新用户
   - 设置用户角色
   - 生成 API Key
   - 搜索用户
   - 禁用用户

4. **实时监控**
   - 文档处理进度显示
   - 操作结果提示
   - 错误信息反馈

### 注意事项

⚠️ **重要提示**：
- 前端页面依赖后端 API 服务，请确保后端服务已启动
- 跨域问题：如果使用独立前端服务器，需确保后端 CORS 配置允许该源
- 浏览器兼容性：推荐使用 Chrome、Firefox、Edge 等现代浏览器
- 移动端适配：界面已做响应式设计，支持移动设备访问

## 💬 NextChat 聊天界面启动教程

NextChat 是一个功能强大的 AI 聊天界面，支持多种模型和自定义配置。

### 环境要求

- **Node.js 18+**：必须安装 Node.js 18 或更高版本
- **Yarn**：包管理工具（推荐使用 yarn 而非 npm）

### 安装步骤

1. **进入 NextChat 目录**
   ```bash
   cd NextChat
   ```

2. **安装依赖**
   ```bash
   yarn install
   ```
   
   如果遇到网络问题，可以使用国内镜像：
   ```bash
   yarn config set registry https://registry.npmmirror.com
   yarn install
   ```

3. **配置环境变量**
   
   复制环境变量模板：
   ```bash
   cp .env.template .env.local
   ```
   
   编辑 `.env.local` 文件，配置必要的参数：
   ```env
   # OpenAI API Key（必填）
   OPENAI_API_KEY=sk-your-api-key
   
   # 页面访问密码（可选，建议设置）
   CODE=your-access-password
   
   # API 代理地址（可选，中国大陆用户建议使用）
   BASE_URL=https://b.nextweb.fun/api/proxy
   
   # 或者使用你自己的代理
   # BASE_URL=http://localhost:7890
   ```

### 启动方式

#### 方式一：开发模式（推荐用于调试）

```bash
yarn dev
```

- 启动后访问：`http://localhost:4444`
- 支持热更新，修改代码后自动刷新
- 适合开发和调试使用

#### 方式二：生产模式（推荐用于部署）

1. **构建项目**
   ```bash
   yarn build
   ```

2. **启动服务**
   ```bash
   yarn start
   ```

- 启动后访问：`http://localhost:3000`
- 性能更优，适合生产环境

### Docker 部署（推荐）

如果不想手动安装 Node.js 环境，可以使用 Docker 快速部署：

```bash
docker pull yidadaa/chatgpt-next-web

docker run -d -p 3000:3000 \
   -e OPENAI_API_KEY=sk-your-api-key \
   -e CODE=your-access-password \
   yidadaa/chatgpt-next-web
```

如果需要配置代理：

```bash
docker run -d -p 3000:3000 \
   -e OPENAI_API_KEY=sk-your-api-key \
   -e CODE=your-access-password \
   -e PROXY_URL=http://127.0.0.1:7890 \
   yidadaa/chatgpt-next-web
```

### 主要功能

NextChat 提供以下核心功能：

1. **多模型支持**
   - OpenAI GPT-3.5/4/4o
   - Claude 系列
   - Google Gemini Pro
   - 国产大模型（通义千问、文心一言等）

2. **对话管理**
   - 多会话管理
   - 对话历史记录
   - 导出/导入对话

3. **高级功能**
   - 角色扮演（Mask）
   - 插件系统
   - MCP（Model Context Protocol）支持
   - 实时语音对话

4. **自定义配置**
   - 主题切换
   - 快捷键设置
   - API 参数调整

### 常用配置说明

#### 1. 配置多个 API Key（负载均衡）

在 `.env.local` 中使用逗号分隔多个 key：
```env
OPENAI_API_KEY=sk-key1,sk-key2,sk-key3
```

#### 2. 隐藏用户 API Key 输入框

```env
HIDE_USER_API_KEY=1
```

#### 3. 禁用 GPT-4 模型

```env
DISABLE_GPT4=1
```

#### 4. 自定义模型列表

```env
# 添加自定义模型，隐藏某些模型
CUSTOM_MODELS=+qwen-7b-chat,+glm-6b,-gpt-3.5-turbo
```

#### 5. 启用 MCP 功能

```env
ENABLE_MCP=true
```

### 常见问题

**Q1: yarn install 失败怎么办？**

A: 尝试清除缓存后重新安装：
```bash
yarn cache clean
yarn install
```

**Q2: 如何修改默认端口？**

A: 修改 `package.json` 中的 dev 脚本，或使用环境变量：
```bash
PORT=8080 yarn dev
```

**Q3: 如何连接到本项目的后端 API？**

A: NextChat 是独立的聊天界面，主要通过配置各种 AI API Key 来使用。如果需要与本项目集成，可以：
- 将本项目的 Agent 网关作为 OpenAI 兼容接口配置
- 在 NextChat 中设置 `BASE_URL` 指向本项目地址
- 配置相应的 API Key

**Q4: 为什么总是提示"存在更新"？**

A: 这是正常现象，NextChat 会定期检查更新。如果想关闭检查，可以在设置中关闭自动更新提醒。

**Q5: 如何备份对话数据？**

A: NextChat 的对话数据存储在浏览器本地存储中，可以通过以下方式备份：
- 使用导出功能导出对话为 JSON 文件
- 定期备份浏览器本地存储数据

### 注意事项

⚠️ **安全提示**：
- 务必设置 `CODE` 访问密码，防止未授权访问
- 不要将 `.env.local` 文件提交到版本控制系统
- 妥善保管 API Key，避免泄露导致费用损失
- 生产环境建议使用 HTTPS

💡 **优化建议**：
- 中国大陆用户建议配置代理以加速访问
- 定期更新 NextChat 以获取最新功能和修复
- 合理配置模型列表，避免不必要的 API 调用





