# 用户管理系统 - 快速启动

## 🚀 5分钟快速上手

### 步骤1: 启动服务

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**首次启动会自动：**
- ✅ 创建数据库 `app/db/users.db`
- ✅ 初始化表结构
- ✅ 创建默认管理员账户

---

### 步骤2: 测试系统（可选）

```bash
python test_user_management.py
```

这会：
- 注册3个测试用户
- 设置角色
- 生成API Key
- 测试认证

---

### 步骤3: 访问管理员界面

1. 打开浏览器：`http://127.0.0.1:8000/admin`
2. 登录：
   - 用户名：`zhang666`
   - 密码：`Python666good@`
3. 点击 **"👥 用户管理"**

---

### 步骤4: 管理用户

#### 查看用户列表
- 显示所有注册用户
- 查看角色和API Key状态

#### 设置角色
1. 找到用户
2. 点击 **"设置角色"**
3. 选择：综合决策者 / 企业分析师 / 电力行业专家
4. 保存

#### 生成API Key
1. 确保用户已设置角色
2. 点击 **"生成Key"**
3. 复制API Key
4. 提供给用户

---

### 步骤5: 用户使用

用户获得API Key后：

```bash
curl -X POST 'http://127.0.0.1:8000/v1/chat/completions' \
  -H 'Authorization: Bearer edms-business-analyst-xxx' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "edms-deep-insight",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'
```

---

## 📋 核心功能清单

- ✅ **用户注册**：姓名 + 手机号 → 自动生成UID
- ✅ **用户列表**：查看所有注册用户
- ✅ **搜索用户**：按姓名/手机号/UID搜索
- ✅ **设置角色**：3种角色可选
- ✅ **生成API Key**：自动创建唯一Key
- ✅ **数据库认证**：从数据库验证API Key
- ✅ **访问日志**：记录角色+用户+时间
- ✅ **管理员界面**：可视化管理用户

---

## 🎯 关键文件

| 文件 | 作用 |
|------|------|
| `app/db/users.db` | SQLite数据库 |
| `app/services/user_service.py` | 数据库操作 |
| `app/api/user_management.py` | API接口 |
| `app/api/role_auth.py` | 角色认证（已改为数据库验证） |
| `app/web/index.html` | 管理员界面 |
| `app/web/app.js` | 前端逻辑 |

---

## 🔑 默认管理员

- **用户名**: `zhang666`
- **密码**: `Python666good@`
- **访问地址**: `http://127.0.0.1:8000/admin`

---

## 📖 详细文档

查看完整文档：[USER_MANAGEMENT_GUIDE.md](USER_MANAGEMENT_GUIDE.md)

---

**开始使用吧！** 🎉
