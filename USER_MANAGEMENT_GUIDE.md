# 用户管理系统使用指南

## 📋 系统概述

本系统实现了基于SQLite的完整用户管理功能，包括：
- ✅ 用户注册（姓名、手机号、自动生成UID）
- ✅ 管理员查看用户列表
- ✅ 管理员设置用户角色
- ✅ 管理员生成API Key
- ✅ 基于数据库的API Key认证

---

## 🗂️ 文件结构

```
app/
├── db/
│   └── users.db              # SQLite数据库文件（自动创建）
├── services/
│   └── user_service.py       # 用户管理服务（数据库操作）
├── api/
│   ├── role_auth.py          # 角色认证模块（已更新为数据库验证）
│   └── user_management.py    # 用户管理API接口
└── web/
    ├── index.html            # 管理员界面（已添加用户管理页面）
    └── app.js                # 前端JavaScript（已添加用户管理功能）
```

---

## 🚀 快速开始

### 1. 启动后端服务

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**首次启动时会自动：**
- 创建 `app/db/users.db` 数据库文件
- 初始化用户表结构
- 创建默认管理员账户

---

### 2. 运行测试脚本（可选）

```bash
python test_user_management.py
```

**测试内容：**
- ✅ 注册用户
- ✅ 获取用户列表
- ✅ 设置用户角色
- ✅ 生成API Key
- ✅ API Key认证测试

---

### 3. 访问管理员界面

打开浏览器访问：`http://127.0.0.1:8000/admin`

**登录凭证：**
- 用户名：`zhang666`
- 密码：`Python666good@`

---

## 👥 用户管理操作流程

### 步骤1: 用户注册

**方式A: 通过API注册**
```bash
curl -X POST 'http://127.0.0.1:8000/users/register' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "张三",
    "phone": "13800138001"
  }'
```

**响应示例：**
```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "uid": "user_a1b2c3d4e5f6",
    "name": "张三",
    "phone": "13800138001",
    "note": "请联系管理员设置角色和生成API Key"
  }
}
```

**方式B: 等待用户自行注册**
- 提供注册接口给终端用户
- 用户填写姓名和手机号完成注册

---

### 步骤2: 管理员查看用户列表

1. 登录管理员界面：`http://127.0.0.1:8000/admin`
2. 点击左侧导航栏的 **"👥 用户管理"**
3. 查看所有注册用户

**用户列表显示：**
- 姓名
- 手机号
- UID（唯一标识）
- 角色（未设置/综合决策者/企业分析师/电力行业专家）
- API Key状态
- 注册时间

---

### 步骤3: 设置用户角色

1. 在用户列表中找到目标用户
2. 点击 **"设置角色"** 按钮
3. 选择角色：
   - **综合决策者**：可访问所有Agent
   - **企业分析师**：可访问年报分析和深度洞察
   - **电力行业专家**：只能访问电力标准查询
4. 点击 **"保存"**

**角色权限对照表：**

| 角色 | edms-power-standard | edms-annual-report | edms-deep-insight | edms-auto-report |
|------|---------------------|-------------------|-------------------|------------------|
| 👷 电力行业专家 | ✅ | ❌ | ❌ | ❌ |
| 📊 企业分析师 | ❌ | ✅ | ✅ | ❌ |
| 🎯 综合决策者 | ✅ | ✅ | ✅ | ✅ |

---

### 步骤4: 生成API Key

1. 确保用户已设置角色
2. 点击 **"生成Key"** 按钮
3. 系统自动生成API Key（格式：`edms-{role}-{random}`）
4. 在弹出的对话框中查看和复制API Key
5. **将API Key提供给用户**

**⚠️ 重要提示：**
- API Key一旦生成，请妥善保管
- 建议通过安全渠道传递给用户
- 泄露可能导致未授权访问

---

### 步骤5: 用户使用API Key

用户获得API Key后，可以在请求中使用：

```bash
curl -X POST 'http://127.0.0.1:8000/v1/chat/completions' \
  -H 'Authorization: Bearer edms-business-analyst-a1b2c3d4e5f6g7h8' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "edms-deep-insight",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'
```

**认证流程：**
1. 系统从 `Authorization` 头提取API Key
2. 在数据库中查询该Key对应的用户
3. 获取用户的角色信息
4. 验证角色是否有权限访问请求的模型
5. 记录访问日志（角色 + 用户）

---

## 🔍 搜索用户

在用户管理页面：
1. 在搜索框输入关键词（姓名/手机号/UID）
2. 点击 **"搜索"** 按钮
3. 显示匹配的用户列表

---

## 📊 数据库结构

### users 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| uid | TEXT | 用户唯一标识（自动生成） |
| name | TEXT | 姓名（必填） |
| phone | TEXT | 手机号（必填，唯一） |
| role | TEXT | 角色（可选） |
| api_key | TEXT | API Key（唯一，管理员生成） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| is_active | INTEGER | 是否激活（1=激活，0=禁用） |

**索引：**
- `idx_uid`: 加速UID查询
- `idx_api_key`: 加速API Key验证
- `idx_phone`: 加速手机号查询

---

## 🔧 API接口文档

### 1. 用户注册

**POST** `/users/register`

**请求体：**
```json
{
  "name": "张三",
  "phone": "13800138001"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "uid": "user_xxx",
    "name": "张三",
    "phone": "13800138001"
  }
}
```

---

### 2. 获取用户列表

**GET** `/users/list`

**响应：**
```json
[
  {
    "uid": "user_xxx",
    "name": "张三",
    "phone": "13800138001",
    "role": "企业分析师",
    "api_key": "edms-business-analyst-xxx",
    "created_at": "2026-04-29 16:00:00"
  }
]
```

---

### 3. 搜索用户

**POST** `/users/search`

**请求体：**
```json
{
  "keyword": "张三"
}
```

---

### 4. 设置用户角色

**POST** `/users/set-role`

**请求体：**
```json
{
  "uid": "user_xxx",
  "role": "企业分析师"
}
```

**可选角色值：**
- `综合决策者`
- `企业分析师`
- `电力行业专家`
- `""`（清空角色）

---

### 5. 生成API Key

**POST** `/users/generate-api-key`

**请求体：**
```json
{
  "uid": "user_xxx"
}
```

**前置条件：** 用户必须已设置角色

**响应：**
```json
{
  "code": 200,
  "message": "API Key生成成功",
  "data": {
    "uid": "user_xxx",
    "api_key": "edms-business-analyst-a1b2c3d4e5f6g7h8"
  }
}
```

---

### 6. 获取单个用户信息

**GET** `/users/{uid}`

---

### 7. 禁用用户

**POST** `/users/deactivate`

**请求体：**
```json
{
  "uid": "user_xxx"
}
```

**注意：** 软删除，不真正删除数据

---

## 🔐 认证机制

### API Key格式

```
edms-{role-en}-{random-suffix}
     │        │      │
     │        │      └─ 16位随机字符（secrets.token_hex(8)）
     │        └─ 角色英文标识
     └────────── 固定前缀
```

**示例：**
- `edms-decision-maker-a1b2c3d4e5f6g7h8`
- `edms-business-analyst-1a2b3c4d5e6f7g8h`
- `edms-power-expert-9z8y7x6w5v4u3t2s`

---

### 认证流程

```
客户端请求
    ↓
提取 Authorization 头
    ↓
去除 "Bearer " 前缀
    ↓
在数据库中查询 api_key
    ↓
找到用户？
    ├─ 否 → 返回 401 INVALID_API_KEY
    └─ 是 → 获取用户角色
              ↓
         映射角色到系统标识
              ↓
         验证角色权限
              ↓
         记录访问日志
              ↓
         处理请求
```

---

## 📝 访问日志

每次API请求都会在控制台输出日志：

```
[ACCESS LOG] Role: business_analyst, User: user_a1b2c3d4, Model: edms-deep-insight, Time: 2026-04-29 17:30:00
```

**日志包含：**
- 角色标识
- 用户UID
- 访问的模型
- 访问时间

---

## ⚠️ 注意事项

### 1. 手机号唯一性
- 每个手机号只能注册一次
- 重复注册会返回错误

### 2. 角色必须先于API Key
- 生成API Key前必须先设置角色
- 否则返回 `ROLE_NOT_SET` 错误

### 3. API Key安全性
- API Key相当于密码，请妥善保管
- 建议定期更换
- 不要在前端代码中硬编码

### 4. 数据库备份
- 定期备份 `app/db/users.db` 文件
- 避免数据丢失

---

## 🛠️ 常见问题

### Q1: 如何重置数据库？

```bash
# 删除数据库文件
rm app/db/users.db

# 重启服务，会自动重新创建
uvicorn main:app --reload
```

---

### Q2: 如何修改管理员密码？

编辑 `app/web/app.js` 文件：
```javascript
const ADMIN_USERNAME = 'your_username';
const ADMIN_PASSWORD = 'your_password';
```

---

### Q3: 用户忘记密码怎么办？

当前版本不支持密码功能，用户通过API Key认证。如需重置：
1. 管理员为用户生成新的API Key
2. 将新Key提供给用户

---

### Q4: 如何查看数据库内容？

使用SQLite工具：
```bash
# 安装sqlite3命令行工具
sqlite3 app/db/users.db

# 查询所有用户
SELECT * FROM users;

# 退出
.quit
```

或使用图形化工具如 **DB Browser for SQLite**。

---

## 📞 技术支持

如有问题，请检查：
1. ✅ 后端服务是否正常运行
2. ✅ 数据库文件是否存在且可写
3. ✅ API请求格式是否正确
4. ✅ 浏览器控制台是否有错误

---

**祝使用愉快！** 🎉
