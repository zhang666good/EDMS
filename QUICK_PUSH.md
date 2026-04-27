# 🚀 快速推送到 GitHub（3步完成）

## 前置条件

✅ 已完成：
- `.gitignore` 文件已创建
- `.env.example` 模板已创建
- Git 仓库已初始化

---

## 📝 推送步骤

### 步骤 1: 在 GitHub 创建仓库

1. 访问 https://github.com/new
2. 填写信息：
   - **Repository name**: `Enterprise_decision_making_system`
   - **Description**: 企业决策支持系统
   - **Visibility**: Public 或 Private
   - ❌ **不要勾选** "Initialize with README"
3. 点击 "Create repository"
4. 复制仓库地址（HTTPS 或 SSH）

---

### 步骤 2: 添加远程仓库并推送

在 PowerShell 中执行以下命令：

```powershell
# 进入项目目录
cd D:\software\jsjsjds\development\Enterprise_decision_making_system

# 添加远程仓库（替换为您的仓库地址）
git remote add origin https://github.com/YOUR-USERNAME/Enterprise_decision_making_system.git

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: Enterprise Decision Making System"

# 推送到 GitHub
git push -u origin main
```

如果提示分支名称是 `master`：
```powershell
git push -u origin master
```

---

### 步骤 3: 输入凭据

首次推送会要求认证：

**HTTPS 方式**：
- Username: 您的 GitHub 用户名
- Password: **Personal Access Token**（不是密码！）

**获取 Token**：
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 勾选 `repo` 权限
4. 生成并复制 Token
5. 粘贴到密码提示处

**SSH 方式**（推荐）：
- 需要先配置 SSH 密钥
- 参考 `GIT_PUSH_GUIDE.md` 详细教程

---

## ✅ 验证成功

推送成功后：
1. 刷新 GitHub 仓库页面
2. 应该能看到所有文件
3. 检查 `.env` 文件**不在**其中（已被忽略）

---

## 🔄 后续更新

日常开发后推送：

```powershell
git add .
git commit -m "描述你的修改"
git push
```

---

## ⚠️ 注意事项

1. **永远不要提交 `.env` 文件**
   - 包含敏感信息（API Keys、密码）
   - `.gitignore` 已配置忽略

2. **提交前检查**
   ```powershell
   git status
   ```

3. **清晰的提交信息**
   ```powershell
   git commit -m "feat: 添加知识库管理功能"
   git commit -m "fix: 修复登录问题"
   git commit -m "docs: 更新文档"
   ```

---

## 🆘 遇到问题？

查看完整教程：`GIT_PUSH_GUIDE.md`

常见错误解决方案都在里面！
