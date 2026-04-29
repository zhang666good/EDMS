# JWT管理员认证系统使用指南

## 🔐 安全改进说明

### 之前的问题
- ❌ 前端硬编码管理员用户名和密码
- ❌ 任何人查看源代码都能获取凭证
- ❌ 无法动态修改密码
- ❌ 无Token机制，安全性低

### 现在的方案
- ✅ 后端API验证凭证
- ✅ 使用JWT Token认证
- ✅ Token有效期24小时
- ✅ 密码存储在环境变量中
- ✅ 前端不再暴露凭证

---

## 📦 已实现的功能

### 1. 后端API接口

#### `/auth/login` - 管理员登录
**POST** 请求

**请求体：**
```json
{
  "username": "zhang666",
  "password": "Python666good@"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "user_info": {
      "uid": "admin_001",
      "name": "系统管理员",
      "role": "admin"
    }
  }
}
```

---

#### `/auth/verify` - 验证Token
**POST** 请求

**请求头：**
```
Authorization: Bearer <token>
```

**响应：**
```json
{
  "code": 200,
  "message": "Token有效",
  "data": {
    "user_info": {
      "user_id": "admin_001",
      "username": "系统管理员",
      "role": "admin"
    }
  }
}
```

---

#### `/auth/me` - 获取当前用户信息
**GET** 请求

**请求头：**
```
Authorization: Bearer <token>
```

**响应：**
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "user_info": {
      "user_id": "admin_001",
      "username": "系统管理员",
      "role": "admin",
      "exp": 1234567890
    }
  }
}
```

---

### 2. 前端改进

#### 登录流程
```javascript
// 旧方式（不安全）
if (username === 'zhang666' && password === 'Python666good@') {
  localStorage.setItem('isLoggedIn', 'true');
}

// 新方式（安全）
const response = await fetch('/auth/login', {
  method: 'POST',
  body: JSON.stringify({ username, password })
});

const result = await response.json();
if (result.code === 200) {
  localStorage.setItem('token', result.data.access_token);
  localStorage.setItem('isLoggedIn', 'true');
}
```

#### 存储的信息
- `token`: JWT Token（用于后续认证）
- `isLoggedIn`: 登录状态
- `username`: 用户姓名
- `userRole`: 用户角色

---

## 🚀 快速开始

### 步骤1: 安装依赖

```bash
pip install PyJWT>=2.8.0
```

或重新安装所有依赖：
```bash
pip install -r requirements.txt
```

---

### 步骤2: 配置环境变量

`.env` 文件中已添加JWT配置：

```env
# JWT配置
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-2026
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
```

⚠️ **重要：** 在生产环境中，请修改 `JWT_SECRET_KEY` 为强随机字符串！

---

### 步骤3: 启动服务

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

### 步骤4: 测试登录

#### 方法1: 使用测试脚本
```bash
python test_jwt_auth.py
```

#### 方法2: 使用curl
```bash
curl -X POST 'http://127.0.0.1:8000/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"zhang666","password":"Python666good@"}'
```

#### 方法3: 访问Web界面
1. 打开浏览器：`http://127.0.0.1:8000/admin`
2. 输入用户名和密码
3. 点击登录

---

## 🔧 技术细节

### JWT Token结构

```
Header.Payload.Signature
```

**Payload内容：**
```json
{
  "user_id": "admin_001",
  "username": "系统管理员",
  "role": "admin",
  "exp": 1234567890,  // 过期时间
  "iat": 1234567800,  // 签发时间
  "type": "access"
}
```

---

### 认证流程

```
用户输入凭证
    ↓
前端调用 /auth/login
    ↓
后端验证用户名密码
    ↓
生成JWT Token
    ↓
返回Token给前端
    ↓
前端保存Token到localStorage
    ↓
后续请求携带Token
    ↓
后端验证Token有效性
    ↓
允许/拒绝访问
```

---

### Token验证

每次需要认证的请求：

1. 从 `Authorization` 头提取Token
2. 验证Token签名
3. 检查是否过期
4. 解码获取用户信息
5. 返回用户信息或抛出异常

---

## ⚙️ 配置说明

### 修改Token有效期

编辑 `.env` 文件：
```env
JWT_EXPIRE_HOURS=12  # 改为12小时
```

重启服务生效。

---

### 修改管理员密码

编辑 `.env` 文件：
```env
admin=new_username
password=new_password
```

重启服务生效。

---

### 生产环境配置

**必须修改的配置：**

1. **JWT Secret Key**
   ```env
   # 生成强随机密钥
   python -c "import secrets; print(secrets.token_hex(32))"
   
   # 复制到 .env
   JWT_SECRET_KEY=<生成的密钥>
   ```

2. **HTTPS**
   - 生产环境必须使用HTTPS
   - Token在HTTP下容易被窃取

3. **CORS配置**
   - 限制允许的域名
   - 不要使用 `"*"`

---

## 🛡️ 安全最佳实践

### 1. Token存储
- ✅ 存储在 `localStorage`（当前实现）
- ⚠️ 更好的方式：`HttpOnly Cookie`（防XSS）

### 2. Token刷新
- 当前：Token过期后需重新登录
- 改进：实现Refresh Token机制

### 3. 密码安全
- 当前：明文存储在环境变量
- 改进：使用哈希存储（bcrypt）

### 4. 速率限制
- 添加登录失败次数限制
- 防止暴力破解

---

## 📝 API使用示例

### JavaScript (前端)

```javascript
// 登录
async function login(username, password) {
  const response = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  const result = await response.json();
  
  if (result.code === 200) {
    localStorage.setItem('token', result.data.access_token);
    return true;
  }
  return false;
}

// 使用Token访问受保护接口
async function getUsers() {
  const token = localStorage.getItem('token');
  
  const response = await fetch('/users/list', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

---

### Python (后端测试)

```python
import requests

# 登录
response = requests.post('http://127.0.0.1:8000/auth/login', json={
    "username": "zhang666",
    "password": "Python666good@"
})

token = response.json()['data']['access_token']

# 使用Token
response = requests.get('http://127.0.0.1:8000/users/list', headers={
    'Authorization': f'Bearer {token}'
})

print(response.json())
```

---

## 🧪 测试清单

- ✅ 正确凭证登录成功
- ✅ 错误凭证返回401
- ✅ Token验证成功
- ✅ 无效Token返回401
- ✅ 过期Token返回401
- ✅ 无Token返回401
- ✅ Token包含正确的用户信息
- ✅ 前端登录后能正常访问

---

## 🔍 故障排查

### 问题1: 登录返回401

**可能原因：**
- 用户名或密码错误
- 环境变量未正确加载

**解决方法：**
```bash
# 检查.env文件
cat .env | grep admin
cat .env | grep password

# 重启服务
uvicorn main:app --reload
```

---

### 问题2: Token验证失败

**可能原因：**
- Token格式错误
- Token已过期
- Secret Key不匹配

**解决方法：**
```bash
# 运行测试脚本查看详细错误
python test_jwt_auth.py
```

---

### 问题3: 前端登录无反应

**可能原因：**
- 后端服务未启动
- API地址配置错误

**解决方法：**
1. 检查浏览器控制台错误
2. 确认后端服务运行在8000端口
3. 检查 `app.js` 中的 `AUTH_API_BASE_URL`

---

## 📊 与旧方案对比

| 特性 | 旧方案 | 新方案 |
|------|--------|--------|
| 凭证存储 | 前端硬编码 | 后端环境变量 |
| 认证方式 | 前端比对 | 后端API验证 |
| Token机制 | 无 | JWT Token |
| 安全性 | 低 | 高 |
| 可维护性 | 差 | 好 |
| 可扩展性 | 差 | 好 |

---

## 🎯 下一步改进建议

1. **实现Refresh Token**
   - Access Token短期有效（1小时）
   - Refresh Token长期有效（7天）
   - 自动刷新Token

2. **密码加密存储**
   - 使用bcrypt哈希密码
   - 不在任何地方存储明文密码

3. **多用户支持**
   - 支持多个管理员账户
   - 每个账户独立密码

4. **登录日志**
   - 记录登录时间、IP
   - 检测异常登录

5. **双因素认证**
   - 短信验证码
   - 邮箱验证码

---

## 📞 技术支持

如有问题，请检查：
1. ✅ PyJWT是否已安装
2. ✅ .env文件配置是否正确
3. ✅ 后端服务是否正常启动
4. ✅ 浏览器控制台是否有错误

---

**祝使用愉快！** 🎉
