# 角色权限系统使用指南

## 概述

本系统实现了基于角色的访问控制（RBAC），通过API Key识别用户角色，限制不同角色可访问的Agent。

## 角色定义

| 角色标识 | 显示名称 | API Key前缀 | 可访问的Agent | 说明 |
|---------|---------|------------|--------------|------|
| `power_expert` | 电力行业专家 | `edms-power-expert-` | power_standard_query | 专注电力行业标准、技术规范查询 |
| `business_analyst` | 企业分析师 | `edms-business-analyst-` | annual_report_analyst, deep_insight_analyst | 企业年报分析与经营洞察 |
| `decision_maker` | 综合决策者 | `edms-decision-maker-` | 所有4个Agent | 跨领域综合决策支持 |

## Dify Agent配置

需要在Dify平台创建以下4个Agent应用：

1. **年报数据处理agent** → `annual_report_analyst`
2. **智能异常检测与根因分析专家** → `deep_insight_analyst`
3. **智能报告自动生成专家** → `auto_report_expert`
4. **电力行业专家agent** → `power_standard_query`

## 配置步骤

### 1. 在Dify平台获取Agent API Keys

登录Dify平台，为每个Agent应用获取API Key，然后配置到`.env`文件：

```env
DIFY_AGENT_ANNUAL_REPORT_KEY=app-xxx-annual-report-key
DIFY_AGENT_DEEP_INSIGHT_KEY=app-xxx-deep-insight-key
DIFY_AGENT_AUTO_REPORT_KEY=app-xxx-auto-report-key
DIFY_AGENT_POWER_STANDARD_KEY=app-xxx-power-standard-key
```

### 2. 生成角色API Keys

为每个角色生成唯一的API Key（格式：`edms-{role-name}-{secret-suffix}`）：

```python
# 使用Python生成示例
from app.api.role_auth import generate_role_api_key
import secrets

# 生成随机后缀（8位十六进制字符）
suffix = secrets.token_hex(4)  # 例如: 'a1b2c3d4'

# 为每个角色生成API Key
power_key = generate_role_api_key("power_expert", suffix)
# 结果: edms-power-expert-a1b2c3d4

business_key = generate_role_api_key("business_analyst", secrets.token_hex(4))
# 结果: edms-business-analyst-e5f6g7h8

decision_key = generate_role_api_key("decision_maker", secrets.token_hex(4))
# 结果: edms-decision-maker-i9j0k1l2
```

**建议：** 为每个用户或每组用户生成独立的API Key，便于追踪和管理。

### 3. 前端配置

前端在请求时需要在HTTP Header中携带角色API Key：

#### 方式A：使用Bearer Token（推荐）
```javascript
fetch('/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer edms-power-expert-a1b2c3d4'
  },
  body: JSON.stringify({
    model: 'edms-power-standard',
    messages: [{ role: 'user', content: '电力安全规程有哪些？' }],
    stream: true
  })
})
```

#### 方式B：直接传递API Key
```javascript
fetch('/api/v1/gateway/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'edms-business-analyst-e5f6g7h8'
  },
  body: JSON.stringify({
    query: '对比今年和去年的营收数据',
    user: 'user_001',
    response_mode: 'streaming'
  })
})
```

## 测试验证

### 测试1：列出可用模型（OpenAI兼容接口）

```bash
# 电力行业专家 - 只能看到电力相关模型
curl -X GET http://localhost:8000/v1/models \
  -H "Authorization: Bearer edms-power-expert-a1b2c3d4"

# 返回结果应只包含: edms-power-standard

# 企业分析师 - 只能看到企业分析相关模型
curl -X GET http://localhost:8000/v1/models \
  -H "Authorization: Bearer edms-business-analyst-e5f6g7h8"

# 返回结果应包含: edms-annual-report, edms-deep-insight

# 综合决策者 - 可以看到所有模型
curl -X GET http://localhost:8000/v1/models \
  -H "Authorization: Bearer edms-decision-maker-i9j0k1l2"

# 返回结果应包含所有4个模型
```

### 测试2：聊天请求（OpenAI兼容接口）

```bash
# 电力行业专家访问电力Agent（成功）
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer edms-power-expert-a1b2c3d4" \
  -d '{
    "model": "edms-power-standard",
    "messages": [{"role": "user", "content": "电力安全规程有哪些要求？"}],
    "stream": false
  }'

# 电力行业专家尝试访问企业年报Agent（失败 - 403错误）
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer edms-power-expert-a1b2c3d4" \
  -d '{
    "model": "edms-annual-report",
    "messages": [{"role": "user", "content": "查询年报数据"}],
    "stream": false
  }'

# 返回错误: {"code": "ACCESS_DENIED", "message": "Role 'power_expert' cannot access model 'edms-annual-report'..."}
```

### 测试3：Gateway接口测试

```bash
# 企业分析师访问允许的Agent
curl -X POST http://localhost:8000/api/v1/gateway/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: edms-business-analyst-e5f6g7h8" \
  -d '{
    "query": "对比今年和去年的营收",
    "user": "user_001",
    "response_mode": "streaming"
  }'

# 列出当前角色可访问的Agent
curl -X GET http://localhost:8000/api/v1/gateway/agents \
  -H "Authorization: edms-power-expert-a1b2c3d4"

# 返回: {"agents": [{"key": "power_standard_query", "name": "电力行业专家"}]}
```

## 权限验证逻辑

系统按以下顺序进行权限验证：

1. **提取角色**：从`Authorization`头解析API Key，识别角色
2. **路由Agent**：根据请求参数（model/agent/intent/query）确定目标Agent
3. **验证权限**：检查该角色是否有权限访问目标Agent
4. **执行请求**：权限通过后，转发请求到Dify

### 验证场景

| 场景 | 角色 | 请求的Agent | 结果 |
|------|------|------------|------|
| 1 | power_expert | power_standard_query | ✅ 允许 |
| 2 | power_expert | annual_report_analyst | ❌ 拒绝 (403) |
| 3 | business_analyst | deep_insight_analyst | ✅ 允许 |
| 4 | business_analyst | auto_report_expert | ❌ 拒绝 (403) |
| 5 | decision_maker | 任意Agent | ✅ 允许 |
| 6 | 无API Key | 任意Agent | ✅ 允许（向后兼容） |

## 错误处理

### 常见错误码

- **403 ACCESS_DENIED**: 角色无权访问指定的Agent/Model
- **400 AGENT_NOT_CONFIGURED**: Agent未在网关中配置
- **400 MODEL_NOT_SUPPORTED**: Model不在支持的列表中

### 错误响应示例

```json
{
  "code": "ACCESS_DENIED",
  "message": "Role 'power_expert' cannot access model 'edms-annual-report' (agent: annual_report_analyst). Allowed agents: power_standard_query",
  "detail": null
}
```

## 扩展新角色

如需添加新角色，修改`app/api/role_auth.py`中的`ROLE_TO_AGENTS`字典：

```python
ROLE_TO_AGENTS["new_role"] = {
    "display_name": "新角色名称",
    "api_key_prefix": "edms-new-role-",
    "allowed_agents": {"agent_alias_1", "agent_alias_2"},
    "description": "角色描述"
}
```

然后为新角色生成API Key即可使用。

## 安全建议

1. **API Key保密**：不要在前端代码中硬编码API Key，应通过后端服务动态分配
2. **定期轮换**：建议定期更换API Key的后缀部分
3. **日志审计**：记录每次请求的角色和API Key，便于追踪异常访问
4. **最小权限原则**：为用户分配刚好够用的角色权限，避免过度授权

## 技术实现细节

### 核心模块

- **role_auth.py**: 角色认证与权限验证逻辑
- **gateway.py**: Gateway接口的角色集成
- **openai_compat.py**: OpenAI兼容接口的角色集成

### API Key识别算法

```python
def get_role_from_api_key(api_key: str) -> Optional[str]:
    for role_name, config in ROLE_TO_AGENTS.items():
        if api_key.startswith(config["api_key_prefix"]):
            return role_name
    return None
```

这种基于前缀的匹配方式简单高效，无需数据库查询或加密解密操作。
