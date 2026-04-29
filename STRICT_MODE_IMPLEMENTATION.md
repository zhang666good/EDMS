# 严格模式实施说明

## 📋 修改概述

已将OpenAI兼容接口 (`/v1/chat/completions` 和 `/v1/models`) 从"允许无认证，拒绝无效认证"升级为**严格模式**：**所有请求必须提供有效的角色API Key**。

---

## 🔧 修改的文件

### 1. `app/api/openai_compat.py`

#### 修改点1: `/v1/models` 接口 (第283-335行)

**修改前逻辑：**
```python
role = get_role_from_api_key(authorization) if authorization else None
# 如果authorization为None，role就是None，不进行任何验证
```

**修改后逻辑：**
```python
# 严格模式：必须提供Authorization头
if not authorization:
    raise _http_error(401, "AUTHORIZATION_REQUIRED", ...)

token = authorization
if authorization.startswith("Bearer "):
    token = authorization[7:]

role = get_role_from_api_key(token.strip())

# 如果无法识别API Key，拒绝访问
if not role:
    raise _http_error(401, "INVALID_API_KEY", ...)
```

**关键变化：**
- ❌ 移除了"无认证时允许访问"的分支
- ✅ 强制要求提供Authorization头
- ✅ 无效API Key返回401错误
- ✅ 始终根据角色过滤模型列表（不再有条件判断）

---

#### 修改点2: `/v1/chat/completions` 接口 (第335-365行)

**修改前逻辑：**
```python
role = None
if authorization:
    # 解析并验证
    ...
# 如果没有authorization，role保持为None，继续执行
```

**修改后逻辑：**
```python
# 严格模式：必须提供Authorization头
if not authorization:
    raise _http_error(401, "AUTHORIZATION_REQUIRED", ...)

token = authorization
if authorization.startswith("Bearer "):
    token = authorization[7:]

role = get_role_from_api_key(token.strip())

# 如果无法识别API Key，拒绝访问
if not role:
    raise _http_error(401, "INVALID_API_KEY", ...)
```

**关键变化：**
- ❌ 移除了"无认证时允许访问"的分支
- ✅ 强制要求提供Authorization头
- ✅ 无效API Key返回401错误
- ✅ 所有请求都必须通过角色权限验证

---

## 🔐 安全行为对比

### 修改前（宽松模式）

| 场景 | Authorization头 | 结果 |
|------|----------------|------|
| 1 | 无 | ✅ 允许（向后兼容） |
| 2 | `Bearer abc123`（无效） | ❌ 401拒绝 |
| 3 | `Bearer edms-power-expert-xxx`（有效但无权） | ❌ 403拒绝 |
| 4 | `Bearer edms-decision-maker-xxx`（有效且有权） | ✅ 200成功 |

### 修改后（严格模式）

| 场景 | Authorization头 | 结果 |
|------|----------------|------|
| 1 | 无 | ❌ **401拒绝** ⚠️ 变化 |
| 2 | `Bearer abc123`（无效） | ❌ 401拒绝 |
| 3 | `Bearer edms-power-expert-xxx`（有效但无权） | ❌ 403拒绝 |
| 4 | `Bearer edms-decision-maker-xxx`（有效且有权） | ✅ 200成功 |

**核心区别：** 场景1从"允许"变为"拒绝"，堵住了安全漏洞。

---

## 📝 API使用示例

### 正确的请求格式

#### 1. 电力行业专家查询电力标准
```bash
curl -X POST 'http://127.0.0.1:8000/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer edms-power-expert-a1b2c3d4' \
  -d '{
    "model": "edms-power-standard",
    "messages": [{"role": "user", "content": "电力安全规程有哪些？"}],
    "stream": false,
    "user": "user_001"
  }'
```

#### 2. 企业分析师查询年报数据
```bash
curl -X POST 'http://127.0.0.1:8000/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer edms-business-analyst-e5f6g7h8' \
  -d '{
    "model": "edms-annual-report",
    "messages": [{"role": "user", "content": "查询2024年营收数据"}],
    "stream": false,
    "user": "user_002"
  }'
```

#### 3. 综合决策者访问任意Agent
```bash
curl -X POST 'http://127.0.0.1:8000/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer edms-decision-maker-i9j0k1l2' \
  -d '{
    "model": "edms-deep-insight",
    "messages": [{"role": "user", "content": "分析市场趋势"}],
    "stream": false,
    "user": "user_003"
  }'
```

#### 4. 查询可用模型列表
```bash
# 电力行业专家只能看到电力标准模型
curl -X GET 'http://127.0.0.1:8000/v1/models' \
  -H 'Authorization: Bearer edms-power-expert-a1b2c3d4'

# 返回: {"data": [{"id": "edms-power-standard", ...}]}

# 综合决策者可以看到所有模型
curl -X GET 'http://127.0.0.1:8000/v1/models' \
  -H 'Authorization: Bearer edms-decision-maker-i9j0k1l2'

# 返回: {"data": [{"id": "edms-power-standard", ...}, {"id": "edms-annual-report", ...}, ...]}
```

---

## ❌ 错误响应示例

### 错误1: 缺少Authorization头
```bash
curl -X POST 'http://127.0.0.1:8000/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -d '{"model": "edms-deep-insight", ...}'
```

**响应：**
```json
{
  "code": "AUTHORIZATION_REQUIRED",
  "message": "Authorization header is required. Format: Bearer edms-{role}-{key}",
  "detail": null
}
```
**状态码：** 401

---

### 错误2: 无效的API Key
```bash
curl -X POST 'http://127.0.0.1:8000/v1/chat/completions' \
  -H 'Authorization: Bearer invalid-key-123' \
  -d '{"model": "edms-deep-insight", ...}'
```

**响应：**
```json
{
  "code": "INVALID_API_KEY",
  "message": "Unrecognized API key. Please use a valid role-based API key (e.g., edms-power-expert-xxxx)",
  "detail": null
}
```
**状态码：** 401

---

### 错误3: 越权访问
```bash
# 电力专家尝试访问企业年报Agent
curl -X POST 'http://127.0.0.1:8000/v1/chat/completions' \
  -H 'Authorization: Bearer edms-power-expert-a1b2c3d4' \
  -d '{
    "model": "edms-annual-report",
    "messages": [{"role": "user", "content": "查询年报"}]
  }'
```

**响应：**
```json
{
  "code": "ACCESS_DENIED",
  "message": "Role 'power_expert' cannot access model 'edms-annual-report' (agent: annual_report_analyst). Allowed agents: power_standard_query",
  "detail": null
}
```
**状态码：** 403

---

## 🧪 测试方法

### 运行自动化测试
```bash
python test_strict_mode.py
```

**测试覆盖：**
1. ✅ 无认证请求 → 应该返回401
2. ✅ 无效认证 → 应该返回401
3. ✅ 有效但无权 → 应该返回403
4. ✅ /models接口无认证 → 应该返回401
5. ✅ /models接口角色过滤 → 应该返回正确模型列表

### 手动测试
```bash
# 1. 测试无认证（应该失败）
curl http://127.0.0.1:8000/v1/models

# 2. 测试无效认证（应该失败）
curl -H "Authorization: Bearer invalid" http://127.0.0.1:8000/v1/models

# 3. 测试有效认证（应该成功）
curl -H "Authorization: Bearer edms-power-expert-test1234" http://127.0.0.1:8000/v1/models
```

---

## 🔑 API Key生成与管理

### 生成API Key
```python
from app.api.role_auth import generate_role_api_key
import secrets

# 为每个用户生成独立Key
suffix = secrets.token_hex(4)  # 8位随机字符

# 生成不同角色的Key
power_key = generate_role_api_key("power_expert", suffix)
business_key = generate_role_api_key("business_analyst", suffix)
decision_key = generate_role_api_key("decision_maker", suffix)

print(f"电力行业专家: {power_key}")
print(f"企业分析师:   {business_key}")
print(f"综合决策者:   {decision_key}")
```

### API Key格式
```
edms-{role-name}-{secret-suffix}
     │            │
     │            └─ 至少8位随机字符（建议16位）
     └────────────── 角色标识
```

**示例：**
- `edms-power-expert-a1b2c3d4e5f6g7h8`
- `edms-business-analyst-1a2b3c4d5e6f7g8h`
- `edms-decision-maker-9z8y7x6w5v4u3t2s`

---

## 🛡️ 安全最佳实践

### 1. API Key管理
- ✅ 为每个用户生成独立的API Key
- ✅ 定期轮换API Key（建议每30-90天）
- ✅ 安全存储API Key（不要硬编码在前端代码中）
- ❌ 不要在日志中记录完整的API Key
- ❌ 不要通过不安全的通道传输API Key

### 2. 前端集成
```javascript
// ✅ 推荐：从后端动态获取API Key
async function getApiKey() {
  const response = await fetch('/api/get-user-api-key', {
    credentials: 'include'  // 携带session cookie
  });
  return response.json().apiKey;
}

// 使用时
const apiKey = await getApiKey();
fetch('/v1/chat/completions', {
  headers: {
    'Authorization': `Bearer ${apiKey}`
  }
});
```

### 3. 监控与审计
- 记录所有API请求的角色、时间、IP地址
- 监控异常的401/403错误率
- 设置告警：检测到频繁的无效认证尝试
- 定期审查API Key使用情况

---

## 📊 角色权限矩阵

| 角色 | edms-power-standard | edms-annual-report | edms-deep-insight | edms-auto-report |
|------|---------------------|-------------------|-------------------|------------------|
| 👷 电力行业专家 | ✅ | ❌ | ❌ | ❌ |
| 📊 企业分析师 | ❌ | ✅ | ✅ | ❌ |
| 🎯 综合决策者 | ✅ | ✅ | ✅ | ✅ |

---

## 🔄 回滚方案（如果需要）

如果严格模式导致问题，可以临时回滚到宽松模式：

```python
# 在 openai_compat.py 中修改为：
role = None

if authorization:
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    
    role = get_role_from_api_key(token.strip())
    
    # 宽松模式：无效Key只记录日志，不拒绝
    if not role:
        logger.warning(f"Invalid API key: {token[:20]}...")
        # 不抛出异常，继续执行（role保持为None）

# 后续逻辑保持不变
```

⚠️ **注意：** 回滚会重新引入安全漏洞，仅建议在紧急情况下临时使用。

---

## 📞 故障排查

### 问题1: 所有请求都返回401
**可能原因：** 前端未正确传递Authorization头

**检查方法：**
```bash
# 查看浏览器开发者工具的网络请求
# 确认请求头中包含: Authorization: Bearer edms-xxx-xxx
```

**解决方案：**
- 检查前端代码是否正确设置Authorization头
- 确认API Key格式正确
- 确认API Key未被截断或损坏

---

### 问题2: 有效API Key仍被拒绝
**可能原因：** API Key格式错误或角色配置问题

**检查方法：**
```python
# 测试API Key是否有效
from app.api.role_auth import get_role_from_api_key

key = "edms-power-expert-test1234"
role = get_role_from_api_key(key)
print(f"识别的角色: {role}")  # 应该输出: power_expert
```

**解决方案：**
- 确认API Key以正确的角色前缀开头
- 确认 `role_auth.py` 中的角色配置正确
- 检查是否有额外的空格或特殊字符

---

### 问题3: 跨域请求失败
**可能原因：** CORS配置问题

**检查方法：**
```bash
# 查看浏览器控制台是否有CORS错误
```

**解决方案：**
- 确认 `main.py` 中的CORS配置正确
- 确保 `allow_origins` 包含前端域名
- 检查浏览器是否缓存了旧的CORS策略

---

## 📅 实施日期
- **修改时间：** 2026-04-29
- **版本：** v1.0.0
- **状态：** ✅ 已完成并测试通过

---

## 🔗 相关文档
- [ROLE_AUTH_GUIDE.md](ROLE_AUTH_GUIDE.md) - 角色权限系统完整指南
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - 实施总结
- [test_strict_mode.py](test_strict_mode.py) - 自动化测试脚本
- [CHECKLIST.md](CHECKLIST.md) - 部署检查清单
