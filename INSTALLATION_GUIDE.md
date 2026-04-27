# Enterprise Decision Making System 完整安装启动教程

## 📋 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [详细安装步骤](#详细安装步骤)
- [配置说明](#配置说明)
- [启动服务](#启动服务)
- [验证安装](#验证安装)
- [常见问题](#常见问题)

---

## 💻 系统要求

### 硬件要求
- **CPU**: 2核心及以上
- **内存**: 4GB RAM 最低，推荐 8GB+
- **硬盘**: 10GB 可用空间

### 软件要求
- **操作系统**: Windows 10/11, macOS, Linux
- **Python**: 3.9 或更高版本
- **Node.js**: 18.x 或更高版本（可选，仅前端需要）
- docker 环境（可选，生产环境推荐）
- **包管理器**: 
  - Python: pip
  - Node.js: yarn 或 npm

### 外部服务依赖
- **Dify 平台**: 已部署的 Dify AI 平台（必需）
 dify 平台部署参考 https://docs.dify.ai/zh/self-host/quick-start/docker-compose
- dify 配置好后导入 DSL 文件：agent,工作流
- **MinerU 服务**: 文档解析服务


---

## 🚀 快速开始

### 步骤 1: 打开项目

```bash
git clone <repository-url>
cd Enterprise_decision_making_system
```

### 步骤 2: 创建虚拟环境

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 步骤 3: 安装后端依赖

```bash
pip install -r requirements.txt
```

### 步骤 4: 配置环境变量

复制 `.env` 文件并修改配置：

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

编辑 `.env` 文件，至少配置以下内容：

```env
# Dify 平台配置（必需）
DIFY_API_BASE_URL=http://your-dify-server:8088/
DIFY_API_KEY=your-api-key-here

# 管理员账户（必需）
ADMIN_USERNAME=zhang666
ADMIN_PASSWORD=Python666good@
```

### 步骤 5: 启动后端服务

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 步骤 6: 访问管理界面

打开浏览器访问：
```
http://127.0.0.1:8000/admin
```

使用配置的账户登录即可！

---

## 📦 详细安装步骤

### 1. Python 环境准备

#### Windows 系统

**方法 A: 使用官方安装包**

1. 访问 https://www.python.org/downloads/
2. 下载 Python 3.9+ 安装包
3. 运行安装程序，**勾选 "Add Python to PATH"**
4. 点击 "Install Now"

**验证安装**：
```bash
python --version
# 应显示: Python 3.9.x 或更高版本
```

**方法 B: 使用 Anaconda**

```bash
# 创建虚拟环境
conda create -n edms python=3.9
conda activate edms
```

#### macOS 系统

```bash
# 使用 Homebrew 安装
brew install python@3.9

# 验证
python3 --version
```

#### Linux 系统 (Ubuntu/Debian)

```bash
# 更新包列表
sudo apt update

# 安装 Python 和 pip
sudo apt install python3.9 python3.9-venv python3-pip

# 验证
python3.9 --version
```

### 2. 创建虚拟环境

**为什么需要虚拟环境？**
- 隔离项目依赖，避免冲突
- 便于管理和删除
- 支持多项目不同依赖版本

```bash
# 进入项目目录
cd Enterprise_decision_making_system

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate
```

激活后，命令行前会显示 `(.venv)` 标识。

### 3. 安装 Python 依赖

```bash
# 确保在虚拟环境中
pip install -r requirements.txt
```

**依赖清单**：
```
fastapi>=0.110.0          # Web 框架
uvicorn>=0.29.0           # ASGI 服务器
pydantic>=2.6.0           # 数据验证
python-dotenv>=1.0.1      # 环境变量管理
python-multipart>=0.0.9   # 文件上传支持
```

**如果遇到网络问题**，使用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. 配置环境变量

#### 查看现有配置

项目根目录已有 `.env` 文件，内容如下：

```env
# Dify Agent API Keys
DIFY_AGENT_ANNUAL_REPORT_KEY=app-6Gzs27Qm75JyqCdfhKuKl1A2
DIFY_AGENT_DEEP_INSIGHT_KEY=app-DWgoi5pei9zmygeNVOpJR00n
DIFY_AGENT_AUTO_REPORT_KEY=app-FFThn2WGK5ur4FTYpGBJSwfl

# Dify API Base URL
DIFY_API_BASE_URL=http://123.207.72.88:8088/



# MinerU Token
MINERU_TOKEN=eyJ0eXBl...

# 管理员账户
admin=zhang666
password=Python666good@
```

#### 必须修改的配置

**1. Dify API 地址**

如果您有自己的 Dify 部署，修改：
```env
DIFY_API_BASE_URL=http://your-dify-server:port/
```

**2. Dify API Key**

从 Dify 平台获取 API Key：
1. 登录 Dify 平台
2. 进入 "设置" → "API 密钥"
3. 创建或复制现有密钥
4. 替换 `.env` 中的值

```env
DIFY_API_KEY=dataset-your-actual-key
```

**3. 管理员账户**

建议修改默认账户：
```env
ADMIN_USERNAME=your-username
ADMIN_PASSWORD=your-strong-password
```

⚠️ **安全提示**：生产环境请使用强密码！

#### 可选配置

**MinerU 服务**（文档解析）：
```env
MINERU_TOKEN=your-mineru-jwt-token
```

获取方式：
1. 访问 MinerU 服务平台
2. 注册/登录账户
3. 在个人中心获取 JWT Token




### 5. 前端安装（可选）

如果需要运行 NextChat 聊天界面：

```bash
# 进入 NextChat 目录
cd NextChat

# 安装依赖
yarn install
# 或
npm install

# 配置前端环境变量
# 编辑 NextChat/.env.local
```

**NextChat/.env.local 配置**：
```env
OPENAI_API_KEY=sk-xxxx
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
BASE_URL=http://127.0.0.1:8000/v1
CUSTOM_MODELS=edms-deep-insight,edms-annual-report,edms-auto-report
```

---

## ⚙️ 配置说明

### 环境变量详解

| 变量名 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `DIFY_API_BASE_URL` | ✅ | Dify 平台地址 | `http://123.207.72.88:8088/` |
| `DIFY_API_KEY` | ✅ | Dify API 密钥 | `dataset-xxx` |
| `ADMIN_USERNAME` | ✅ | 管理员用户名 | `zhang666` |
| `ADMIN_PASSWORD` | ✅ | 管理员密码 | `Python666good@` |
| `MINERU_TOKEN` | ❌ | MinerU JWT Token | `eyJ0eXAi...` |


### CORS 配置

后端默认允许以下来源跨域访问：

```python
# main.py
allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://0.0.0.0:3000",
]
```

如需添加其他来源，修改此列表。

---

## ▶️ 启动服务

### 方式 1: 直接启动（开发模式）

```bash
# 确保在项目根目录且虚拟环境已激活
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**参数说明**：
- `--reload`: 代码修改后自动重启（开发用）
- `--host 0.0.0.0`: 监听所有网络接口
- `--port 8000`: 指定端口号

**成功标志**：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using StatReload
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 方式 2: 生产模式启动

```bash
# 不使用 --reload，性能更好
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**参数说明**：
- `--workers 4`: 启动 4 个工作进程

### 方式 3: 后台运行（Linux/Mac）

```bash
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
```

查看日志：
```bash
tail -f server.log
```

停止服务：
```bash
ps aux | grep uvicorn
kill <PID>
```

### 启动前端（可选）

```bash
cd NextChat
yarn dev
# 或
npm run dev
```

前端将在 `http://localhost:3000` 启动。

---

## ✅ 验证安装

### 1. 检查后端服务

**浏览器访问**：
```
http://127.0.0.1:8000/
```

应返回：
```json
{
  "message": "Enterprise decision gateway is running"
}
```

### 2. 查看 API 文档

**Swagger UI**：
```
http://127.0.0.1:8000/docs
```

可以看到所有可用的 API 接口。

**ReDoc**：
```
http://127.0.0.1:8000/redoc
```

### 3. 测试管理界面

**访问**：
```
http://127.0.0.1:8000/admin
```

**登录**：
- 用户名：`zhang666`（或您配置的）
- 密码：`Python666good@`（或您配置的）

**验证功能**：
1. ✅ 能成功登录
2. ✅ 能看到知识库列表页面
3. ✅ 能创建新知识库
4. ✅ 能上传文档

### 4. 测试 API 接口

使用 curl 测试：

```bash
# 健康检查
curl http://127.0.0.1:8000/

# 查询知识库列表
curl http://127.0.0.1:8000/api/v1/backend/datasets

# 创建知识库
curl -X POST "http://127.0.0.1:8000/api/v1/backend/datasets" \
  -F "name=测试知识库" \
  -F "description=用于测试"
```

### 5. 检查日志

启动时应该看到类似输出：

```
INFO:     Will watch for changes in these directories: ['...']
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Started reloader process [xxxxx]
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

如果有错误，会显示红色错误信息，根据提示排查。

---

## 🐛 常见问题

### Q1: `ModuleNotFoundError: No module named 'xxx'`

**原因**：依赖未安装或虚拟环境未激活

**解决**：
```bash
# 确认虚拟环境已激活
# Windows 应显示: (.venv) PS ...
# Linux/Mac 应显示: (.venv) user@host:...

# 重新安装依赖
pip install -r requirements.txt
```

### Q2: `Address already in use`

**原因**：8000 端口已被占用

**解决**：
```bash
# Windows: 查找占用端口的进程
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9

# 或使用其他端口
uvicorn main:app --port 8001
```

### Q3: CORS 错误

**错误信息**：
```
Access to fetch at '...' has been blocked by CORS policy
```

**解决**：
1. 确保访问地址是 `http://127.0.0.1:8000` 而非 `http://localhost:8000`
2. 或在 `main.py` 中添加您的域名到 `allow_origins`

### Q4: Dify API 连接失败

**错误**：
```
Connection refused
```

**解决**：
1. 检查 Dify 服务是否运行
2. 验证 `DIFY_API_BASE_URL` 是否正确
3. 测试连接：
   ```bash
   curl http://your-dify-server:8088/v1/datasets
   ```

### Q5: 登录后页面空白

**原因**：JavaScript 加载失败

**解决**：
1. 打开浏览器控制台（F12）
2. 查看是否有 404 错误
3. 确保访问 `http://127.0.0.1:8000/admin` 而非其他地址
4. 清除浏览器缓存后重试

### Q6: 文件上传失败

**可能原因**：
1. MinerU 服务未配置
2. 网络连接问题
3. 文件格式不支持

**解决**：
1. 检查 `MINERU_TOKEN` 是否配置
2. 查看后端日志错误信息
3. 确认文件格式在支持列表中（PDF, DOC, DOCX, TXT, MD）

### Q7: Python 版本过低

**错误**：
```
SyntaxError: invalid syntax
```

**解决**：
```bash
# 检查当前版本
python --version

# 如果低于 3.9，安装新版本
# Windows: 从 python.org 下载
# macOS: brew install python@3.9
# Linux: sudo apt install python3.9
```

### Q8: 虚拟环境激活失败

**Windows PowerShell 错误**：
```
无法加载文件 .venv\Scripts\Activate.ps1，因为在此系统上禁止运行脚本
```

**解决**：
```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

或使用 CMD：
```cmd
.venv\Scripts\activate.bat
```


1. **查看日志**
   ```bash
   # 后端日志在终端输出
   # 前端日志在浏览器控制台（F12）
   ```

2. **检查配置文件**
   - `.env` - 环境变量
   - `requirements.txt` - Python 依赖
   - `NextChat/package.json` - Node 依赖

3. **查阅文档**
   - `README.md` - 项目简介
   - `DESIGN_PHILOSOPHY.md` - 设计思路
   - `DESIGN_CHALLENGES.md` - 设计难点
   - `OPEN_SOURCE_USAGE.md` - 开源组件说明

### 报告问题

提供以下信息：
1. 操作系统和版本
2. Python 版本
3. 完整的错误日志
4. 复现步骤

---

## 🎉 完成！

恭喜您成功安装并启动了 Enterprise Decision Making System！

**下一步**：
1. 创建第一个知识库
2. 上传测试文档
3. 体验智能问答功能
4. 探索更多高级功能

**常用地址**：
- 管理界面: http://127.0.0.1:8000/admin
- API 文档: http://127.0.0.1:8000/docs
- 健康检查: http://127.0.0.1:8000/

祝您使用愉快！🚀
