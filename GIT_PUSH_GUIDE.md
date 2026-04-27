# Git 初始化与 GitHub 推送完整教程

## 📋 目录

- [准备工作](#准备工作)
- [初始化 Git 仓库](#初始化-git-仓库)
- [创建 .gitignore 文件](#创建-gitignore-文件)
- [推送到 GitHub](#推送到-github)
- [后续更新流程](#后续更新流程)
- [常见问题](#常见问题)

---

## 🔧 准备工作

### 1. 安装 Git

**Windows**:
- 下载: https://git-scm.com/download/win
- 安装时保持默认选项即可

**验证安装**:
```bash
git --version
# 应显示: git version 2.x.x
```

### 2. 配置 Git 用户信息

```bash
# 设置用户名（您的 GitHub 用户名或真实姓名）
git config --global user.name "Your Name"

# 设置邮箱（与 GitHub 账户邮箱一致）
git config --global user.email "your-email@example.com"

# 验证配置
git config --list
```

### 3. 创建 GitHub 仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `Enterprise_decision_making_system`
   - **Description**: `企业决策支持系统 - 基于 Dify Agent 和 MinerU 的智能文档分析平台`
   - **Visibility**: Public（公开）或 Private（私有）
   - ❌ **不要勾选** "Initialize this repository with a README"
3. 点击 "Create repository"
4. 复制仓库地址，例如：
   ```
   https://github.com/your-username/Enterprise_decision_making_system.git
   ```

---

## 🚀 初始化 Git 仓库

### 步骤 1: 进入项目目录

```bash
cd D:\software\jsjsjds\development\Enterprise_decision_making_system
```

### 步骤 2: 初始化 Git

```bash
git init
```

成功标志：
```
Initialized empty Git repository in D:/software/.../.git/
```

### 步骤 3: 检查 .gitignore

确保项目根目录已有 `.gitignore` 文件（已为您创建）。

查看被忽略的文件：
```bash
git status --ignored
```

---

## 📝 创建 .gitignore 文件

`.gitignore` 文件已创建在项目根目录，它会告诉 Git 忽略以下文件：

### 已配置忽略的内容

✅ **Python 相关**
- `__pycache__/` - Python 缓存
- `*.pyc` - 编译文件
- `.venv/` - 虚拟环境

✅ **环境变量**
- `.env` - 敏感配置（**非常重要**）
- `.env.local`
- `.env.production`

✅ **临时文件**
- `data_file_temp/` - 上传的临时文件
- `mineru_temp_md/` - MinerU 解析结果
- `*.log` - 日志文件

✅ **IDE 配置**
- `.idea/` - PyCharm
- `.vscode/` - VS Code
- `.DS_Store` - macOS

✅ **Node.js**
- `NextChat/node_modules/` - npm 依赖
- `NextChat/.next/` - Next.js 构建产物

⚠️ **重要提示**：
- `.env` 文件包含敏感信息（API Key、密码），**绝对不能**提交到 GitHub
- 如需分享配置，创建 `.env.example` 文件作为模板

---

## 📤 推送到 GitHub

### 方法 1: HTTPS 方式（推荐新手）

#### 步骤 1: 添加远程仓库

```bash
# 替换为您的 GitHub 仓库地址
git remote add origin https://github.com/your-username/Enterprise_decision_making_system.git
```

验证：
```bash
git remote -v
# 应显示:
# origin  https://github.com/your-username/Enterprise_decision_making_system.git (fetch)
# origin  https://github.com/your-username/Enterprise_decision_making_system.git (push)
```

#### 步骤 2: 添加文件到暂存区

```bash
# 添加所有文件
git add .

# 或者查看将要提交的文件
git status
```

#### 步骤 3: 提交更改

```bash
git commit -m "Initial commit: Enterprise Decision Making System"
```

**提交信息规范**：
```bash
# 格式: <类型>: <描述>

# 示例:
git commit -m "feat: 添加知识库管理功能"
git commit -m "fix: 修复 CORS 跨域问题"
git commit -m "docs: 更新安装文档"
git commit -m "refactor: 重构认证模块"
```

#### 步骤 4: 推送到 GitHub

```bash
# 首次推送，设置上游分支
git push -u origin main
```

如果默认分支是 `master`：
```bash
git push -u origin master
```

#### 步骤 5: 输入凭据

首次推送会要求输入 GitHub 用户名和密码：

```
Username for 'https://github.com': your-username
Password for 'https://your-username@github.com': 
```

⚠️ **注意**：GitHub 不再支持密码验证，需要使用 **Personal Access Token (PAT)**。

**获取 Personal Access Token**：
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择权限：
   - ✅ `repo` (完整仓库控制)
4. 点击 "Generate token"
5. **复制 Token**（只显示一次！）
6. 在密码提示处粘贴 Token

---

### 方法 2: SSH 方式（推荐长期使用）

#### 步骤 1: 生成 SSH 密钥

```bash
# 检查是否已有 SSH 密钥
ls -al ~/.ssh

# 如果没有，生成新密钥
ssh-keygen -t ed25519 -C "your-email@example.com"
```

按提示操作：
- 文件位置：直接回车（使用默认位置）
- 密码短语：可选，建议设置

#### 步骤 2: 添加 SSH 密钥到 ssh-agent

```bash
# 启动 ssh-agent
eval "$(ssh-agent -s)"

# 添加密钥
ssh-add ~/.ssh/id_ed25519
```

#### 步骤 3: 复制公钥

```bash
# Windows PowerShell
Get-Content ~/.ssh/id_ed25519.pub | Set-Clipboard

# Linux/Mac
cat ~/.ssh/id_ed25519.pub
# 然后手动复制输出内容
```

#### 步骤 4: 添加到 GitHub

1. 访问 https://github.com/settings/keys
2. 点击 "New SSH key"
3. Title: `My Laptop` 或其他标识
4. Key: 粘贴公钥内容
5. 点击 "Add SSH key"

#### 步骤 5: 测试连接

```bash
ssh -T git@github.com
```

成功标志：
```
Hi your-username! You've successfully authenticated, but GitHub does not provide shell access.
```

#### 步骤 6: 添加远程仓库（SSH 地址）

```bash
git remote add origin git@github.com:your-username/Enterprise_decision_making_system.git
```

#### 步骤 7: 推送代码

```bash
git add .
git commit -m "Initial commit"
git push -u origin main
```

✅ **优势**：无需每次输入密码或 Token

---

## 🔄 后续更新流程

### 日常开发工作流

```bash
# 1. 查看修改的文件
git status

# 2. 添加修改的文件
git add .
# 或添加特定文件
git add app/api/backend.py
git add README.md

# 3. 提交更改
git commit -m "feat: 添加新的 API 接口"

# 4. 推送到 GitHub
git push
```

### 拉取他人更新

```bash
# 从远程仓库拉取最新代码
git pull origin main
```

### 查看历史记录

```bash
# 查看提交历史
git log

# 简洁格式
git log --oneline

# 图形化显示
git log --graph --oneline --all
```

### 撤销操作

```bash
# 撤销未提交的修改
git checkout -- filename

# 撤销已暂存的文件
git reset HEAD filename

# 撤销最后一次提交（保留修改）
git reset --soft HEAD~1

# 撤销最后一次提交（丢弃修改）⚠️ 危险
git reset --hard HEAD~1
```

---

## 🌿 分支管理

### 创建新分支

```bash
# 创建并切换到新分支
git checkout -b feature/new-feature

# 或者
git branch feature/new-feature
git checkout feature/new-feature
```

### 切换分支

```bash
git checkout main
git checkout feature/new-feature
```

### 合并分支

```bash
# 切换到主分支
git checkout main

# 合并特性分支
git merge feature/new-feature
```

### 删除分支

```bash
# 删除本地分支
git branch -d feature/new-feature

# 删除远程分支
git push origin --delete feature/new-feature
```

---

## ⚠️ 常见问题

### Q1: `fatal: remote origin already exists`

**原因**：已经添加了远程仓库

**解决**：
```bash
# 查看现有远程仓库
git remote -v

# 如果需要修改
git remote set-url origin https://github.com/your-username/new-repo.git

# 或删除后重新添加
git remote remove origin
git remote add origin https://github.com/your-username/repo.git
```

### Q2: `failed to push some refs`

**原因**：远程仓库有本地没有的提交

**解决**：
```bash
# 先拉取远程更改
git pull origin main --rebase

# 解决冲突（如果有）
# 编辑冲突文件，然后：
git add .
git rebase --continue

# 再次推送
git push
```

### Q3: `.env` 文件被提交了怎么办？

**紧急处理**：
```bash
# 1. 从 Git 追踪中移除（保留本地文件）
git rm --cached .env

# 2. 提交更改
git commit -m "chore: 移除 .env 文件"

# 3. 推送到 GitHub
git push

# 4. 立即在 GitHub 上撤销该提交的历史
# 访问: https://github.com/your-username/repo/settings
# 或使用 BFG Repo-Cleaner 工具
```

**预防措施**：
- 确保 `.gitignore` 中有 `.env`
- 提交前检查：`git status`

### Q4: 推送大文件失败

**错误**：
```
Remote rejected: File exceeds maximum allowed size
```

**解决**：
```bash
# 方法 1: 使用 Git LFS (Large File Storage)
git lfs install
git lfs track "*.pdf"
git add .gitattributes
git add large-file.pdf
git commit -m "add large file with LFS"
git push

# 方法 2: 从 Git 中移除大文件
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch path/to/large-file' \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送（谨慎使用）
git push origin --force --all
```

### Q5: 忘记配置用户名和邮箱

**解决**：
```bash
# 配置全局信息
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"

# 修改最后一次提交的作者
git commit --amend --author="Your Name <your-email@example.com>"
```

### Q6: 如何查看哪些文件会被提交？

```bash
# 查看状态
git status

# 查看详细差异
git diff --staged

# 查看某个文件的差异
git diff --staged filename
```

### Q7: 推送时被拒绝（权限问题）

**HTTPS 方式**：
- 检查 Personal Access Token 是否过期
- 重新生成 Token 并更新

**SSH 方式**：
```bash
# 测试 SSH 连接
ssh -T git@github.com

# 检查密钥是否正确添加
ssh-add -l

# 重新添加密钥
ssh-add ~/.ssh/id_ed25519
```

---

## 🔐 安全最佳实践

### 1. 永远不要提交敏感信息

❌ **禁止提交**：
- `.env` 文件
- API Keys
- 数据库密码
- 私钥文件
- `.pem`, `.key` 文件

✅ **正确做法**：
```bash
# 创建示例配置文件
cp .env .env.example

# 编辑 .env.example，移除真实值
# DIFY_API_KEY=your-api-key-here

# 提交示例文件
git add .env.example
git commit -m "docs: 添加环境变量示例"
```

### 2. 定期检查提交历史

```bash
# 查看是否有敏感信息泄露
git log --all -p | grep -i "password\|api_key\|secret"
```

### 3. 使用 .gitignore 模板

推荐使用：https://github.com/github/gitignore

---

## 📊 Git 命令速查表

| 操作 | 命令 |
|------|------|
| 初始化仓库 | `git init` |
| 查看状态 | `git status` |
| 添加文件 | `git add .` |
| 提交更改 | `git commit -m "message"` |
| 查看历史 | `git log` |
| 添加远程 | `git remote add origin <url>` |
| 推送代码 | `git push origin main` |
| 拉取代码 | `git pull origin main` |
| 创建分支 | `git checkout -b branch-name` |
| 切换分支 | `git checkout branch-name` |
| 合并分支 | `git merge branch-name` |
| 查看远程 | `git remote -v` |

---

## 🎉 完成检查清单

推送前确认：

- [ ] 已安装 Git 并配置用户信息
- [ ] 已在 GitHub 创建空仓库
- [ ] 已创建 `.gitignore` 文件
- [ ] `.env` 文件未被跟踪
- [ ] 已运行 `git status` 检查文件
- [ ] 已编写清晰的提交信息
- [ ] 已成功推送到 GitHub
- [ ] 已在 GitHub 网页端验证文件

---

## 📞 需要帮助？

- **Git 官方文档**: https://git-scm.com/doc
- **GitHub 指南**: https://guides.github.com/
- **学习 Git 分支**: https://learngitbranching.js.org/

---

**祝您推送顺利！** 🚀
