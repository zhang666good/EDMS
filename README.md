# Enterprise Decision Making System (EDMS)

企业决策支持系统 - 基于 Dify Agent 和 MinerU 的智能文档分析与报告生成平台

## 📋 项目简介

Enterprise Decision Making System (EDMS) 是一个智能化的企业决策支持系统，结合了先进的 AI Agent 技术和文档解析能力。系统能够：

- **智能文档解析**：使用 MinerU 技术自动解析 PDF、Word 等复杂文档
- **深度洞察分析**：基于 Dify Agent 进行企业数据深度分析
- **自动化报告生成**：自动生成年度财报、分析报告等专业文档
- **语音交互支持**：集成百度语音识别，支持语音输入
- **知识库管理**：完整的 Dify 知识库 API 封装，支持文档检索与问答

### 核心架构

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend   │─────▶│  FastAPI     │─────▶│  Dify Agent │
│  (NextChat)  │      │  Gateway     │      │  Platform   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   MinerU     │
                     │  Document    │
                     │   Parser     │
                     └──────────────┘
```

## ✨ 主要功能

### 1. 文档上传与解析
- 支持 PDF、TXT、MD、DOC、DOCX 等多种格式
- 自动调用 MinerU 进行智能文档解析
- 提取结构化 Markdown 内容
- 实时显示解析进度

### 2. 智能问答系统
- 基于上传文档的上下文问答
- 支持多轮对话和历史记录
- 文档内容自动注入到对话上下文
- 实时流式响应

### 3. Dify Agent 集成
- **年度财报分析** (`edms-annual-report`): 专业财务报表分析
- **深度洞察** (`edms-deep-insight`): 企业数据深度挖掘
- **自动报告生成** (`edms-auto-report`): 智能化报告自动生成

### 4. 知识库管理
- 创建和管理 Dify 知识库
- 文档上传、更新、删除
- 分段管理和索引状态查询
- 语义检索和相关性排序

### 5. 语音识别
- 集成百度语音识别 (STT)
- 支持实时语音转文字
- 多语言支持

## 🚀 快速开始

### 前置要求

- Python 3.9+
- Node.js 18+
- Yarn 或 npm
- 已部署的 Dify 平台
- MinerU 服务访问权限

### 后端安装与部署

#### 1. 克隆项目

```bash
git clone <repository-url>
cd Enterprise_decision_making_system
```

#### 2. 创建虚拟环境

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量

复制 `.env` 文件并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# Dify Agent API Keys
DIFY_AGENT_ANNUAL_REPORT_KEY=your-annual-report-key
DIFY_AGENT_DEEP_INSIGHT_KEY=your-deep-insight-key
DIFY_AGENT_AUTO_REPORT_KEY=your-auto-report-key

# Dify API Base URL
DIFY_API_BASE_URL=http://your-dify-server:port/

# Baidu STT (可选)
BAIDU_STT_API_KEY=your-baidu-api-key
BAIDU_STT_SECRET_KEY=your-baidu-secret-key
BAIDU_STT_TIMEOUT=30

# MinerU Token
MINERU_TOKEN=your-mineru-jwt-token
```

#### 5. 启动后端服务

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务将在 `http://localhost:8000` 启动

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/

### 前端安装与部署

#### 1. 进入 NextChat 目录

```bash
cd NextChat
```

#### 2. 安装依赖

```bash
yarn install
# 或
npm install
```

#### 3. 配置环境变量

编辑 `NextChat/.env.local`:

```env
# OpenAI API Key (必需)
OPENAI_API_KEY=sk-xxxx

# Backend API URL
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# Base URL for AI models
BASE_URL=http://127.0.0.1:8000/v1

# Custom Models
CUSTOM_MODELS=edms-deep-insight,edms-annual-report,edms-auto-report
```

#### 4. 启动开发服务器

```bash
yarn dev
# 或
npm run dev
```

前端将在 `http://localhost:3000` 启动

## 📖 使用方法

### 1. 文档上传与问答

1. 打开浏览器访问 http://localhost:3000
2. 在聊天界面点击 **"文档"** 按钮
3. 选择要上传的文件（PDF/TXT/MD/DOC/DOCX）
4. 等待上传和解析完成（显示 ✅ 文件名）
5. 在输入框中输入问题
6. 发送消息，系统将基于文档内容回答

### 2. API 调用示例

#### 上传文档

```bash
curl -X POST "http://localhost:8000/api/v1/gateway/upload" \
  -F "file=@document.pdf"
```

响应：
```json
{
  "code": 0,
  "context_id": "abc123",
  "md_content": "# Document Content\n..."
}
```

#### 创建知识库

```python
from app.services.knowledge import KnowledgeClient

client = KnowledgeClient(
    base_url="http://your-dify-server:8088",
    api_key="your-api-key"
)

# 创建知识库
dataset = client.create_dataset(
    name="企业知识库",
    description="企业内部文档知识库"
)
print(f"Created dataset: {dataset['id']}")
```

#### 文档检索

```python
# 检索相关文档
results = client.retrieve(
    dataset_id="dataset-id",
    query="企业年报关键指标",
    top_k=5
)

for result in results['records']:
    print(result['segment']['content'])
```

### 3. 测试运行

```bash
# 运行所有测试
python -m pytest test/

# 运行特定测试
python -m pytest test/test_gateway_api.py -v
python -m pytest test/test_knowledge.py -v
```

## 📦 主要依赖项

### 后端依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| fastapi | >=0.110.0 | Web 框架 |
| uvicorn | >=0.29.0 | ASGI 服务器 |
| pydantic | >=2.6.0 | 数据验证 |
| python-dotenv | >=1.0.1 | 环境变量管理 |
| python-multipart | >=0.0.9 | 文件上传支持 |

### 前端依赖

NextChat 基于以下技术栈：
- Next.js 14.1.1
- React 18
- TypeScript
- Tailwind CSS

## ⚙️ 配置说明

### 环境变量详解

#### 后端配置 (.env)

| 变量名 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `DIFY_AGENT_ANNUAL_REPORT_KEY` | 是 | 年度财报分析 Agent Key | `app-xxx` |
| `DIFY_AGENT_DEEP_INSIGHT_KEY` | 是 | 深度洞察 Agent Key | `app-xxx` |
| `DIFY_AGENT_AUTO_REPORT_KEY` | 是 | 自动报告 Agent Key | `app-xxx` |
| `DIFY_API_BASE_URL` | 是 | Dify 平台地址 | `http://123.207.72.88:8088/` |
| `BAIDU_STT_API_KEY` | 否 | 百度语音识别 API Key | - |
| `BAIDU_STT_SECRET_KEY` | 否 | 百度语音识别 Secret Key | - |
| `BAIDU_STT_TIMEOUT` | 否 | 语音识别超时时间(秒) | `30` |
| `MINERU_TOKEN` | 是 | MinerU JWT Token | `eyJ0eXAi...` |

#### 前端配置 (NextChat/.env.local)

| 变量名 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `OPENAI_API_KEY` | 是 | OpenAI API Key | `sk-xxxx` |
| `NEXT_PUBLIC_BACKEND_URL` | 是 | 后端服务地址 | `http://localhost:8000` |
| `BASE_URL` | 否 | AI 模型代理地址 | `http://127.0.0.1:8000/v1` |
| `CUSTOM_MODELS` | 否 | 自定义模型列表 | `edms-deep-insight,...` |

### CORS 配置

后端默认允许以下来源跨域访问：
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:3001`
- `http://127.0.0.1:3001`

如需添加其他来源，请修改 `main.py` 中的 `allow_origins` 列表。

## 🏗️ 项目结构

```
Enterprise_decision_making_system/
├── app/                          # 后端应用代码
│   ├── api/                      # API 路由
│   │   ├── gateway.py            # 网关 API
│   │   ├── openai_compat.py      # OpenAI 兼容接口
│   │   └── file_upload_and_context.py  # 文件上传 API
│   ├── services/                 # 业务逻辑层
│   │   ├── knowledge.py          # Dify 知识库客户端
│   │   ├── mineru_file_parser.py # MinerU 解析服务
│   │   ├── baidu_stt.py          # 百度语音识别
│   │   └── dify_gateway.py       # Dify 网关
│   ├── agent/                    # Agent 实现
│   │   └── answers_agent.py      # 问答 Agent
│   ├── schema/                   # 数据模型
│   └── core/                     # 核心模块
├── NextChat/                     # 前端应用
│   ├── app/                      # Next.js 应用
│   │   ├── components/           # React 组件
│   │   │   └── chat.tsx          # 聊天主组件
│   │   └── api/                  # 前端 API 路由
│   └── public/                   # 静态资源
├── front/                        # 备用前端
├── config/                       # 配置文件
├── test/                         # 测试代码
│   ├── test_gateway_api.py       # 网关 API 测试
│   └── test_knowledge.py         # 知识库测试
├── data_file_temp/               # 临时文件存储
├── mineru_temp_md/               # MinerU 解析结果
├── main.py                       # FastAPI 入口
├── requirements.txt              # Python 依赖
└── .env                          # 环境变量
```


## ❓ 常见问题

### Q1: 文档上传返回 404 错误

**原因**: 后端路由未正确注册

**解决方案**:
1. 确认 `main.py` 中包含了 `file_upload_router`
2. 重启后端服务
3. 检查后端日志是否有错误

### Q2: MinerU 解析超时

**原因**: 文档过大或网络延迟

**解决方案**:
1. 检查 MinerU 服务是否正常运行
2. 增加超时时间配置
3. 尝试较小的文档进行测试

### Q3: Dify API 连接失败

**原因**: Dify 服务不可达或配置错误

**解决方案**:
```bash
# 测试 Dify 连接
curl http://your-dify-server:8088/v1/datasets

# 检查 .env 配置
cat .env | grep DIFY
```

### Q4: 前端无法连接后端

**原因**: CORS 配置或端口不匹配

**解决方案**:
1. 确认后端运行在 8000 端口
2. 检查 `NEXT_PUBLIC_BACKEND_URL` 配置
3. 查看浏览器控制台的网络请求

### Q5: 语音识别不工作

**原因**: 百度 API Key 无效或未配置

**解决方案**:
1. 在百度智能云申请 STT API Key
2. 更新 `.env` 中的 `BAIDU_STT_API_KEY` 和 `BAIDU_STT_SECRET_KEY`
3. 重启后端服务

### Q6: Python 模块导入错误

**错误**: `ModuleNotFoundError: No module named 'app'`

**解决方案**:
```bash
# 从项目根目录运行
python -m app.services.knowledge

# 或设置 PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

感谢以下开源项目：

- [Dify](https://github.com/langgenius/dify) - AI Agent 平台
- [MinerU](https://github.com/opendatalab/MinerU) - 文档解析工具
- [NextChat](https://github.com/ChatGPTNextWeb/ChatGPT-Next-Web) - 聊天界面
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架



