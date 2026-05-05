# 上交所公告导入页面显示问题 - 诊断指南

## 🔍 问题现象

点击"📰 上交所公告导入"导航项后，页面无显示或显示不完整。

## ✅ 已修复的问题

1. **添加了缓存破坏参数** - `app.js?v=20260501` 防止浏览器缓存
2. **添加了调试日志** - 可以在控制台查看页面切换状态
3. **添加了错误检查** - 如果页面元素不存在会显示错误信息

## 🔧 排查步骤

### 步骤 1: 强制刷新浏览器

**Windows:**
```
Ctrl + Shift + R
```

**Mac:**
```
Cmd + Shift + R
```

或者：
1. 按 F12 打开开发者工具
2. 右键点击刷新按钮
3. 选择"清空缓存并硬性重新加载"

### 步骤 2: 检查控制台日志

打开浏览器开发者工具（F12），切换到 Console 标签，查看是否有以下日志：

#### 正常情况应该看到：
```
[页面加载] 页面已加载
[页面加载] sseImportPage 存在: true
[页面加载] 导航项数量: 5
```

点击"📰 上交所公告导入"后应该看到：
```
[导航切换] 点击了: sse-import
[导航切换] 显示页面: sseImportPage
[上交所导入] 加载知识库选择器
```

#### 如果看到错误：
```
[导航切换] 找不到页面: sseImportPage
```
说明 HTML 结构有问题，请检查步骤 3。

### 步骤 3: 检查 HTML 元素

在浏览器控制台执行：

```javascript
// 检查页面元素是否存在
console.log('sseImportPage:', document.getElementById('sseImportPage'));

// 检查导航项
console.log('导航项:', document.querySelectorAll('[data-page="sse-import"]'));

// 手动显示页面
document.getElementById('sseImportPage').style.display = 'block';
```

如果 `sseImportPage` 返回 `null`，说明 HTML 文件没有正确加载。

### 步骤 4: 检查网络请求

在开发者工具的 Network 标签中：

1. 刷新页面
2. 查找 `app.js` 请求
3. 确认 URL 包含 `?v=20260501`
4. 确认状态码是 200（不是 304）

### 步骤 5: 检查后端路由

确认后端正确配置了静态文件服务。访问：

```
http://localhost:8000/web/index.html
```

应该能看到完整的 HTML 页面。

## 🐛 常见问题及解决方案

### 问题 1: 页面完全空白

**原因**: JavaScript 文件未加载

**解决**:
1. 检查控制台是否有 JS 错误
2. 确认 app.js 路径正确
3. 重启后端服务

### 问题 2: 导航项点击无反应

**原因**: 事件监听器未绑定

**解决**:
1. 检查控制台是否有 `[页面加载]` 日志
2. 确认没有 JavaScript 错误阻止执行
3. 强制刷新浏览器

### 问题 3: 页面显示但内容为空

**原因**: CSS display 属性问题

**解决**:
在控制台执行：
```javascript
document.getElementById('sseImportPage').style.display = 'block';
```

### 问题 4: 搜索结果不显示

**原因**: API 调用失败

**解决**:
1. 检查 Network 标签中的 `/sse/search` 请求
2. 确认后端服务正常运行
3. 查看后端日志错误信息

## 📋 验证清单

- [ ] 浏览器已强制刷新（Ctrl+Shift+R）
- [ ] 控制台显示 `[页面加载] sseImportPage 存在: true`
- [ ] 控制台显示 `[页面加载] 导航项数量: 5`
- [ ] 点击导航项后显示 `[导航切换] 点击了: sse-import`
- [ ] 页面内容正常显示搜索表单
- [ ] Network 标签中 app.js 状态码为 200

## 🚀 快速测试

在浏览器控制台依次执行：

```javascript
// 1. 检查元素
const page = document.getElementById('sseImportPage');
console.log('页面元素:', page);

// 2. 手动显示
if (page) {
    page.style.display = 'block';
    console.log('✅ 页面已显示');
} else {
    console.error('❌ 页面元素不存在');
}

// 3. 检查导航项
const navItem = document.querySelector('[data-page="sse-import"]');
console.log('导航项:', navItem);

// 4. 模拟点击
if (navItem) {
    navItem.click();
    console.log('✅ 已模拟点击');
}
```

## 📞 仍然有问题？

如果以上步骤都无法解决问题，请提供：

1. 浏览器控制台的完整日志
2. Network 标签中 app.js 的请求详情
3. 浏览器版本和操作系统
4. 后端服务的启动日志

## 🎯 预期效果

成功显示后，页面应包含：

1. **搜索区域**
   - 关键词输入框
   - 每页数量设置
   - 页码设置
   - 搜索按钮

2. **结果区域**（搜索后显示）
   - 知识库选择器
   - 全选/取消全选按钮
   - 导入按钮
   - 结果列表表格
