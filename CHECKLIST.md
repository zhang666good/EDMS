# 角色权限系统 - 快速启动检查清单

## ✅ 实施完成状态

- [x] 创建角色认证模块 `app/api/role_auth.py`
- [x] 修改Gateway接口 `app/api/gateway.py`
- [x] 修改OpenAI兼容接口 `app/api/openai_compat.py`
- [x] 更新环境变量模板 `.env.example`
- [x] 创建配置示例 `.env.role.example`
- [x] 编写完整测试 `test_role_auth.py`
- [x] 所有测试通过 ✅
- [x] 创建使用指南 `ROLE_AUTH_GUIDE.md`
- [x] 创建实施总结 `IMPLEMENTATION_SUMMARY.md`

---

## 📋 部署前检查清单

### 1. Dify平台配置
- [ ] 在Dify平台创建4个Agent应用：
  - [ ] 年报数据处理agent
  - [ ] 智能异常检测与根因分析专家
  - [ ] 智能报告自动生成专家
  - [ ] 电力行业专家agent

- [ ] 获取每个Agent的API Key
- [ ] 记录每个Agent对应的知识库绑定

### 2. 后端配置
- [ ] 复制 `.env.example` 为 `.env`
- [ ] 填入DIFY_API_BASE_URL
- [ ] 填入4个DIFY_AGENT_*_KEY
- [ ] 配置其他必要的环境变量（MINERU_TOKEN等）

### 3. 生成角色API Keys
- [ ] 运行以下Python代码生成API Keys：

```python
from app.api.role_auth import generate_role_api_key
import secrets

# 为每个用户生成独立Key
users = [
    ("user001", "power_expert"),
    ("user002", "business_analyst"),
    ("user003", "decision_maker"),
]

for user_id, role in users:
    suffix = secrets.token_hex(4)
    key = generate_role_api_key(role, suffix)
    print(f"{user_id} ({role}): {key}")
```

- [ ] 记录生成的API Keys并安全存储
- [ ] 将API Keys分发给对应用户

### 4. 功能测试
- [ ] 运行单元测试：`python test_role_auth.py`
- [ ] 启动服务：`uvicorn main:app --reload`
- [ ] 测试健康检查：`curl http://localhost:8000/api/v1/gateway/health`

- [ ] 测试角色模型列表：
  ```bash
  # 电力专家 - 应只返回edms-power-standard
  curl http://localhost:8000/v1/models \
    -H "Authorization: Bearer edms-power-expert-xxxx"
  
  # 企业分析师 - 应返回edms-annual-report和edms-deep-insight
  curl http://localhost:8000/v1/models \
    -H "Authorization: Bearer edms-business-analyst-xxxx"
  ```

- [ ] 测试聊天请求：
  ```bash
  # 成功场景
  curl -X POST http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer edms-power-expert-xxxx" \
    -d '{"model": "edms-power-standard", "messages": [{"role": "user", "content": "测试"}], "stream": false}'
  
  # 失败场景（越权访问）
  curl -X POST http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer edms-power-expert-xxxx" \
    -d '{"model": "edms-annual-report", "messages": [{"role": "user", "content": "测试"}], "stream": false}'
  # 应返回403错误
  ```

### 5. 前端集成
- [ ] 在前端登录流程中获取用户角色
- [ ] 根据角色分配对应的API Key
- [ ] 在所有API请求中添加Authorization头
- [ ] 处理403权限错误，显示友好提示
- [ ] 根据角色动态显示可用的模型/Agent选项

### 6. 文档交付
- [ ] 向开发团队分享 `ROLE_AUTH_GUIDE.md`
- [ ] 向运维团队分享部署步骤
- [ ] 向前端团队提供API集成示例
- [ ] 记录API Keys分配情况（安全管理）

---

## 🔍 验证清单

### 功能验证
- [ ] 电力行业专家只能访问电力标准Agent
- [ ] 企业分析师只能访问年报和洞察Agent
- [ ] 综合决策者可以访问所有Agent
- [ ] 越权访问返回403错误
- [ ] 错误信息清晰易懂

### 性能验证
- [ ] 权限验证延迟 < 10ms
- [ ] 不影响现有API响应时间
- [ ] 并发请求正常工作

### 安全验证
- [ ] API Key不在日志中明文显示
- [ ] 无效的API Key被正确拒绝
- [ ] 过期/撤销的Key无法使用
- [ ] 支持HTTPS传输（生产环境）

---

## 🚨 常见问题排查

### 问题1: 403 ACCESS_DENIED错误
**可能原因**：
- API Key格式错误
- 角色与Agent不匹配
- Authorization头格式不正确

**解决方法**：
```bash
# 检查API Key格式
echo $API_KEY | grep -E "^edms-(power-expert|business-analyst|decision-maker)-[a-z0-9]{8}$"

# 检查Authorization头格式
curl -v http://localhost:8000/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 问题2: Agent未找到错误
**可能原因**：
- Dify Agent API Key未配置
- Agent别名拼写错误
- Dify服务未启动

**解决方法**：
```bash
# 检查环境变量
grep DIFY_AGENT .env

# 测试Dify连接
curl http://localhost:8000/api/v1/gateway/health
```

### 问题3: 测试失败
**可能原因**：
- Python依赖未安装
- 导入路径错误

**解决方法**：
```bash
# 安装依赖
pip install -r requirements.txt

# 重新运行测试
python test_role_auth.py
```

---

## 📊 上线后监控

### 关键指标
- [ ] API请求成功率 > 99%
- [ ] 平均响应时间 < 2秒
- [ ] 403错误率 < 1%
- [ ] 权限验证延迟 < 10ms

### 日志记录
建议记录以下信息：
```python
# 在gateway.py和openai_compat.py中添加日志
import logging
logger = logging.getLogger(__name__)

logger.info(f"Role: {role}, Agent: {agent_alias}, User: {user_id}")
logger.warning(f"Access denied: role={role}, agent={agent_alias}")
```

### 告警规则
- 403错误率突然上升
- 某个API Key频繁被拒绝
- 权限验证延迟超过阈值

---

## 🎯 下一步行动

### 立即执行（今天）
1. 完成Dify平台Agent配置
2. 生成并分发角色API Keys
3. 运行完整测试套件
4. 部署到测试环境

### 本周内
1. 前端集成角色认证
2. 用户验收测试（UAT）
3. 修复发现的问题
4. 准备生产环境部署

### 本月内
1. 生产环境部署
2. 用户培训和文档交付
3. 监控系统配置
4. 收集用户反馈

---

## 📞 支持资源

- **技术文档**: `ROLE_AUTH_GUIDE.md`
- **实施总结**: `IMPLEMENTATION_SUMMARY.md`
- **测试脚本**: `test_role_auth.py`
- **配置示例**: `.env.role.example`

---

**最后更新**: 2026-04-29  
**状态**: ✅ 准备部署
