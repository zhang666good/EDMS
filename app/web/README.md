# 知识库管理系统

## 📖 简介

这是一个基于 Web 的知识库管理界面，提供可视化的知识库和文档管理功能。

## 🚀 快速开始

### 1. 启动后端服务

```bash
cd D:\software\jsjsjds\development\Enterprise_decision_making_system
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 访问管理页面

打开浏览器访问：
```
http://localhost:8000/admin
```

### 3. 登录

使用以下凭据登录：
- **用户名**: `zhang666`
- **密码**: `Python666good@`

## ✨ 功能特性

### 1️⃣ 知识库管理
- ✅ 创建新知识库
- ✅ 查看知识库列表
- ✅ 删除知识库
- ✅ 查看文档数量统计

### 2️⃣ 文档管理
- ✅ 上传单个文档（PDF/DOC/DOCX/TXT/MD）
- ✅ 查看文档列表和索引状态
- ✅ 删除文档
- ✅ 实时显示索引进度

### 3️⃣ 批量上传
- ✅ 拖拽文件上传
- ✅ 多文件选择
- ✅ 批量上传到指定知识库
- ✅ 显示上传结果统计

## 📁 文件结构

```
app/web/
├── index.html      # 主页面
├── app.js          # JavaScript 逻辑
└── README.md       # 说明文档
```

## 🔧 技术栈

- **前端**: 原生 HTML5 + CSS3 + JavaScript (ES6+)
- **后端**: FastAPI (Python)
- **样式**: 自定义 CSS（无框架依赖）
- **API**: RESTful API

## 🎨 界面预览

### 登录页面
- 简洁的登录表单
- 错误提示
- 记住登录状态

### 知识库管理
- 卡片式布局
- 表格展示
- 操作按钮

### 文档管理
- 下拉选择知识库
- 文档状态标签
- 实时刷新

### 批量上传
- 拖拽上传区域
- 文件列表预览
- 进度反馈

## 📝 API 接口

所有接口基于 `/api/v1/backend` 前缀：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/datasets` | GET | 查询知识库列表 |
| `/datasets` | POST | 创建知识库 |
| `/datasets/{id}` | DELETE | 删除知识库 |
| `/datasets/{id}/documents` | GET | 查询文档列表 |
| `/datasets/{id}/documents/file` | POST | 上传文档 |
| `/datasets/{id}/documents/{doc_id}` | DELETE | 删除文档 |

## ⚙️ 配置说明

### 修改登录凭证

编辑项目根目录的 `.env` 文件：

```env
admin=zhang666
password=Python666good@
```

然后修改 `app/web/app.js` 中的对应值：

```javascript
const ADMIN_USERNAME = 'zhang666';
const ADMIN_PASSWORD = 'Python666good@';
```

### 修改 API 地址

如果后端不在本地，修改 `app/web/app.js` 中的：

```javascript
const API_BASE_URL = 'http://localhost:8000/api/v1/backend';
```

## 🔒 安全提示

⚠️ **重要**: 当前版本为演示版本，存在以下安全问题：

1. 登录凭证硬编码在前端代码中
2. 没有 Token 验证机制
3. 没有 HTTPS 加密

**生产环境建议**：
- 使用真正的身份验证系统（JWT/OAuth）
- 启用 HTTPS
- 添加 CORS 限制
- 实现权限控制

## 🐛 常见问题

### Q1: 页面无法加载
**A**: 检查后端服务是否正常运行，访问 http://localhost:8000/docs 确认 API 可用

### Q2: 登录失败
**A**: 确认用户名和密码正确，检查浏览器控制台是否有错误

### Q3: 上传文件失败
**A**: 
- 确认已选择知识库
- 检查文件格式是否支持
- 查看后端日志错误信息

### Q4: 知识库列表为空
**A**: 点击"创建知识库"按钮创建第一个知识库

## 📞 技术支持

如有问题，请检查：
1. 浏览器控制台（F12）的错误信息
2. 后端服务的日志输出
3. 网络连接是否正常

## 📄 许可证

MIT License

---

**Made with ❤️ for Enterprise Decision Making System**
