// API 配置
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1/backend';
const USER_API_BASE_URL = '/users';  // 用户管理API
const AUTH_API_BASE_URL = '/auth';   // 认证API


// 全局状态
let currentDatasetId = null;
let selectedBatchFiles = [];

// ==================== 登录功能 ====================

document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        // 调用后端登录API
        const response = await fetch(`${AUTH_API_BASE_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const result = await response.json();
        
        if (result.code === 200) {
            // 登录成功，保存Token和用户信息
            const { access_token, user_info } = result.data;
            
            localStorage.setItem('isLoggedIn', 'true');
            localStorage.setItem('token', access_token);
            localStorage.setItem('username', user_info.name);
            localStorage.setItem('userRole', user_info.role);
            
            showApp();
            showToast('登录成功', 'success');
        } else {
            // 登录失败
            document.getElementById('errorMessage').style.display = 'block';
            document.getElementById('errorMessage').textContent = result.message || '用户名或密码错误';
            setTimeout(() => {
                document.getElementById('errorMessage').style.display = 'none';
            }, 3000);
        }
    } catch (error) {
        console.error('登录失败:', error);
        document.getElementById('errorMessage').style.display = 'block';
        document.getElementById('errorMessage').textContent = '网络连接失败，请检查服务是否启动';
        setTimeout(() => {
            document.getElementById('errorMessage').style.display = 'none';
        }, 3000);
    }
});

function showApp() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('appContainer').style.display = 'block';
    document.getElementById('currentUser').textContent = localStorage.getItem('username') || '管理员';
    
    // 加载知识库列表
    loadDatasets();
}

function logout() {
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('userRole');
    document.getElementById('loginPage').style.display = 'block';
    document.getElementById('appContainer').style.display = 'none';
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
    showToast('已退出登录', 'success');
}

// 检查登录状态
window.addEventListener('load', function() {
    if (localStorage.getItem('isLoggedIn') === 'true') {
        showApp();
    }
});

// ==================== 导航功能 ====================

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', function() {
        const page = this.dataset.page;
        
        // 更新导航状态
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        this.classList.add('active');
        
        // 切换页面
        document.querySelectorAll('.page-content').forEach(p => p.style.display = 'none');
        document.getElementById(page + 'Page').style.display = 'block';
        
        // 更新标题
        const titles = {
            'datasets': '知识库管理',
            'documents': '文档管理',
            'upload': '批量上传',
            'users': '用户管理'
        };
        document.getElementById('pageTitle').textContent = titles[page];
        
        // 加载数据
        if (page === 'datasets') {
            loadDatasets();
        } else if (page === 'documents') {
            loadDatasetSelect();
        } else if (page === 'upload') {
            loadBatchDatasetSelect();
        } else if (page === 'users') {
            loadUsers();
        }
    });
});

// ==================== 知识库管理 ====================

async function loadDatasets() {
    try {
        const response = await fetch(`${API_BASE_URL}/datasets`);
        const data = await response.json();
        
        if (data.data && data.data.length > 0) {
            renderDatasetsList(data.data);
        } else {
            document.getElementById('datasetsList').innerHTML = `
                <div class="empty-state">
                    <p>暂无知识库</p>
                    <p style="margin-top: 10px;">点击"创建知识库"开始使用</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('加载知识库失败:', error);
        showToast('加载知识库失败', 'error');
    }
}

function renderDatasetsList(datasets) {
    const html = `
        <table class="table">
            <thead>
                <tr>
                    <th>名称</th>
                    <th>描述</th>
                    <th>文档数</th>
                    <th>创建时间</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
                ${datasets.map(dataset => `
                    <tr>
                        <td><strong>${dataset.name}</strong></td>
                        <td>${dataset.description || '-'}</td>
                        <td>${dataset.document_count || 0}</td>
                        <td>${formatDate(dataset.created_at)}</td>
                        <td>
                            <button class="btn-success" onclick="viewDocuments('${dataset.id}')">查看文档</button>
                            <button class="btn-danger" onclick="deleteDataset('${dataset.id}', '${dataset.name}')">删除</button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    document.getElementById('datasetsList').innerHTML = html;
}

function showCreateDatasetModal() {
    document.getElementById('createDatasetModal').classList.add('show');
}

document.getElementById('createDatasetForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const name = document.getElementById('datasetName').value;
    const description = document.getElementById('datasetDescription').value;
    const indexingTechnique = document.getElementById('indexingTechnique').value;
    
    const formData = new FormData();
    formData.append('name', name);
    formData.append('description', description);
    formData.append('indexing_technique', indexingTechnique);
    
    try {
        const response = await fetch(`${API_BASE_URL}/datasets`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.id) {
            showToast('知识库创建成功', 'success');
            closeModal('createDatasetModal');
            document.getElementById('createDatasetForm').reset();
            loadDatasets();
        } else {
            showToast('创建失败: ' + (result.message || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('创建知识库失败:', error);
        showToast('创建失败', 'error');
    }
});

async function deleteDataset(datasetId, datasetName) {
    if (!confirm(`确定要删除知识库 "${datasetName}" 吗？此操作不可恢复！`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/datasets/${datasetId}`, {
            method: 'DELETE'
        });
        
        showToast('知识库已删除', 'success');
        loadDatasets();
    } catch (error) {
        console.error('删除知识库失败:', error);
        showToast('删除失败', 'error');
    }
}

// ==================== 文档管理 ====================

async function loadDatasetSelect() {
    try {
        const response = await fetch(`${API_BASE_URL}/datasets`);
        const data = await response.json();
        
        const select = document.getElementById('datasetSelect');
        select.innerHTML = '<option value="">请选择知识库</option>';
        
        if (data.data) {
            data.data.forEach(dataset => {
                const option = document.createElement('option');
                option.value = dataset.id;
                option.textContent = dataset.name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载知识库列表失败:', error);
    }
}

async function loadDocuments() {
    const datasetId = document.getElementById('datasetSelect').value;
    
    if (!datasetId) {
        document.getElementById('documentsContent').style.display = 'none';
        return;
    }
    
    currentDatasetId = datasetId;
    document.getElementById('documentsContent').style.display = 'block';
    
    try {
        const response = await fetch(`${API_BASE_URL}/datasets/${datasetId}/documents`);
        const data = await response.json();
        
        if (data.data && data.data.length > 0) {
            renderDocumentsList(data.data);
        } else {
            document.getElementById('documentsList').innerHTML = `
                <div class="empty-state">
                    <p>该知识库暂无文档</p>
                    <p style="margin-top: 10px;">点击"上传文档"添加文档</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('加载文档失败:', error);
        showToast('加载文档失败', 'error');
    }
}

function renderDocumentsList(documents) {
    const html = `
        <table class="table">
            <thead>
                <tr>
                    <th>文档名称</th>
                    <th>状态</th>
                    <th>字数</th>
                    <th>创建时间</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
                ${documents.map(doc => `
                    <tr>
                        <td><strong>${doc.name}</strong></td>
                        <td><span class="status-badge status-${doc.indexing_status}">${getStatusText(doc.indexing_status)}</span></td>
                        <td>${doc.word_count || '-'}</td>
                        <td>${formatDate(doc.created_at)}</td>
                        <td>
                            <button class="btn-danger" onclick="deleteDocument('${doc.id}', '${doc.name}')">删除</button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    document.getElementById('documentsList').innerHTML = html;
}

function getStatusText(status) {
    const statusMap = {
        'indexing': '索引中',
        'completed': '已完成',
        'failed': '失败',
        'waiting': '等待中'
    };
    return statusMap[status] || status;
}

function viewDocuments(datasetId) {
    // 切换到文档管理页面
    document.querySelector('[data-page="documents"]').click();
    
    // 选择对应的知识库
    setTimeout(() => {
        document.getElementById('datasetSelect').value = datasetId;
        loadDocuments();
    }, 100);
}

function showUploadDocumentModal() {
    document.getElementById('uploadDocumentModal').classList.add('show');
}

document.getElementById('uploadDocumentForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const datasetId = document.getElementById('datasetSelect').value;
    const file = document.getElementById('documentFile').files[0];
    const documentName = document.getElementById('documentName').value;
    
    if (!file) {
        showToast('请选择文件', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    if (documentName) {
        formData.append('document_name', documentName);
    }
    
    try {
        showToast('正在上传...', 'success');
        const response = await fetch(`${API_BASE_URL}/datasets/${datasetId}/documents/file`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.code === 0) {
            showToast('上传成功', 'success');
            closeModal('uploadDocumentModal');
            document.getElementById('uploadDocumentForm').reset();
            loadDocuments();
        } else {
            showToast('上传失败: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('上传失败:', error);
        showToast('上传失败', 'error');
    }
});

async function deleteDocument(documentId, documentName) {
    if (!confirm(`确定要删除文档 "${documentName}" 吗？`)) {
        return;
    }
    
    const datasetId = document.getElementById('datasetSelect').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/datasets/${datasetId}/documents/${documentId}`, {
            method: 'DELETE'
        });
        
        showToast('文档已删除', 'success');
        loadDocuments();
    } catch (error) {
        console.error('删除文档失败:', error);
        showToast('删除失败', 'error');
    }
}

// ==================== 批量上传 ====================

async function loadBatchDatasetSelect() {
    try {
        const response = await fetch(`${API_BASE_URL}/datasets`);
        const data = await response.json();
        
        const select = document.getElementById('batchDatasetSelect');
        select.innerHTML = '<option value="">请选择知识库</option>';
        
        if (data.data) {
            data.data.forEach(dataset => {
                const option = document.createElement('option');
                option.value = dataset.id;
                option.textContent = dataset.name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载知识库列表失败:', error);
    }
}

// 文件上传区域交互
const uploadArea = document.getElementById('uploadArea');
const batchFileInput = document.getElementById('batchFileInput');

uploadArea.addEventListener('click', () => {
    batchFileInput.click();
});

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = Array.from(e.dataTransfer.files);
    handleBatchFiles(files);
});

batchFileInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    handleBatchFiles(files);
});

function handleBatchFiles(files) {
    selectedBatchFiles = files;
    renderSelectedFiles();
    document.getElementById('batchUploadBtn').disabled = files.length === 0;
}

function renderSelectedFiles() {
    if (selectedBatchFiles.length === 0) {
        document.getElementById('selectedFiles').innerHTML = '';
        return;
    }
    
    const html = `
        <div style="margin-top: 15px;">
            <h4 style="margin-bottom: 10px;">已选择 ${selectedBatchFiles.length} 个文件：</h4>
            <ul style="list-style: none; padding: 0;">
                ${selectedBatchFiles.map((file, index) => `
                    <li style="padding: 8px; background: #f5f5f5; margin-bottom: 5px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
                        <span>📄 ${file.name} (${formatFileSize(file.size)})</span>
                        <button onclick="removeFile(${index})" style="background: none; border: none; color: #f44336; cursor: pointer; font-size: 18px;">&times;</button>
                    </li>
                `).join('')}
            </ul>
        </div>
    `;
    
    document.getElementById('selectedFiles').innerHTML = html;
}

function removeFile(index) {
    selectedBatchFiles.splice(index, 1);
    renderSelectedFiles();
    document.getElementById('batchUploadBtn').disabled = selectedBatchFiles.length === 0;
}

async function batchUpload() {
    const datasetId = document.getElementById('batchDatasetSelect').value;
    
    if (!datasetId) {
        showToast('请选择知识库', 'error');
        return;
    }
    
    if (selectedBatchFiles.length === 0) {
        showToast('请选择文件', 'error');
        return;
    }
    
    const btn = document.getElementById('batchUploadBtn');
    btn.disabled = true;
    btn.textContent = '上传中...';
    
    let successCount = 0;
    let failCount = 0;
    
    for (const file of selectedBatchFiles) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch(`${API_BASE_URL}/datasets/${datasetId}/documents/file`, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.code === 0) {
                successCount++;
            } else {
                failCount++;
                console.error(`文件 ${file.name} 上传失败:`, result.message);
            }
        } catch (error) {
            failCount++;
            console.error(`文件 ${file.name} 上传失败:`, error);
        }
    }
    
    btn.disabled = false;
    btn.textContent = '开始上传';
    
    showToast(`上传完成：成功 ${successCount} 个，失败 ${failCount} 个`, successCount > 0 ? 'success' : 'error');
    
    // 清空选择
    selectedBatchFiles = [];
    renderSelectedFiles();
    batchFileInput.value = '';
}

// ==================== 工具函数 ====================

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast show ' + type;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// 点击模态框外部关闭
window.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('show');
    }
});

// ==================== 用户管理功能 ====================

// 加载用户列表
async function loadUsers() {
    try {
        const response = await fetch(`${USER_API_BASE_URL}/list`);
        const users = await response.json();
        
        if (users && users.length > 0) {
            renderUsersList(users);
        } else {
            document.getElementById('usersList').innerHTML = `
                <div class="empty-state">
                    <p>暂无注册用户</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('加载用户列表失败:', error);
        showToast('加载用户列表失败', 'error');
    }
}

// 渲染用户列表
function renderUsersList(users) {
    const html = `
        <table class="table">
            <thead>
                <tr>
                    <th>姓名</th>
                    <th>手机号</th>
                    <th>UID</th>
                    <th>角色</th>
                    <th>API Key</th>
                    <th>注册时间</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
                ${users.map(user => `
                    <tr>
                        <td><strong>${user.name}</strong></td>
                        <td>${user.phone}</td>
                        <td style="font-family: monospace; font-size: 12px;">${user.uid}</td>
                        <td>
                            <span style="padding: 4px 8px; border-radius: 4px; background: ${getRoleColor(user.role)}; color: white; font-size: 12px;">
                                ${user.role || '未设置'}
                            </span>
                        </td>
                        <td>
                            ${user.api_key ? 
                                `<span style="font-family: monospace; font-size: 11px;">${user.api_key.substring(0, 20)}...</span>` : 
                                '<span style="color: #999;">未生成</span>'
                            }
                        </td>
                        <td>${formatDate(user.created_at)}</td>
                        <td>
                            <button class="btn-success" onclick="showSetRoleModal('${user.uid}', '${user.name}', '${user.role}')">设置角色</button>
                            ${user.api_key ? 
                                `<button class="btn-primary" onclick="showApiKey('${user.name}', '${user.api_key}')" style="margin-left: 5px;">查看Key</button>` :
                                `<button class="btn-primary" onclick="generateApiKey('${user.uid}')" style="margin-left: 5px;">生成Key</button>`
                            }
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    document.getElementById('usersList').innerHTML = html;
}

// 获取角色颜色
function getRoleColor(role) {
    const colors = {
        '综合决策者': '#667eea',
        '企业分析师': '#f093fb',
        '电力行业专家': '#4facfe',
        'admin': '#f44336'
    };
    return colors[role] || '#999';
}

// 搜索用户
async function searchUsers() {
    const keyword = document.getElementById('userSearchInput').value.trim();
    
    if (!keyword) {
        showToast('请输入搜索关键词', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${USER_API_BASE_URL}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keyword })
        });
        
        const users = await response.json();
        
        if (users && users.length > 0) {
            renderUsersList(users);
            showToast(`找到 ${users.length} 个用户`, 'success');
        } else {
            document.getElementById('usersList').innerHTML = `
                <div class="empty-state">
                    <p>未找到匹配的用户</p>
                </div>
            `;
            showToast('未找到匹配的用户', 'error');
        }
    } catch (error) {
        console.error('搜索用户失败:', error);
        showToast('搜索失败', 'error');
    }
}

// 显示设置角色模态框
function showSetRoleModal(uid, name, currentRole) {
    document.getElementById('roleUid').value = uid;
    document.getElementById('roleUserName').value = name;
    document.getElementById('roleSelect').value = currentRole || '';
    document.getElementById('setRoleModal').classList.add('show');
}

// 提交设置角色
document.getElementById('setRoleForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const uid = document.getElementById('roleUid').value;
    const role = document.getElementById('roleSelect').value;
    
    try {
        const response = await fetch(`${USER_API_BASE_URL}/set-role`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ uid, role })
        });
        
        const result = await response.json();
        
        if (result.code === 200) {
            showToast(result.message, 'success');
            closeModal('setRoleModal');
            loadUsers();
        } else {
            showToast('设置失败: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('设置角色失败:', error);
        showToast('设置失败', 'error');
    }
});

// 生成API Key
async function generateApiKey(uid) {
    if (!confirm('确定要为此用户生成API Key吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`${USER_API_BASE_URL}/generate-api-key`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ uid })
        });
        
        const result = await response.json();
        
        if (result.code === 200) {
            // 获取用户信息
            const userResponse = await fetch(`${USER_API_BASE_URL}/${uid}`);
            const user = await userResponse.json();
            
            showApiKey(user.name, result.data.api_key);
            showToast('API Key生成成功', 'success');
            loadUsers();
        } else {
            showToast('生成失败: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('生成API Key失败:', error);
        showToast('生成失败', 'error');
    }
}

// 显示API Key
function showApiKey(userName, apiKey) {
    document.getElementById('apiKeyUserName').value = userName;
    document.getElementById('apiKeyValue').value = apiKey;
    document.getElementById('apiKeyModal').classList.add('show');
}

// 复制API Key
function copyApiKey() {
    const apiKeyInput = document.getElementById('apiKeyValue');
    apiKeyInput.select();
    document.execCommand('copy');
    showToast('API Key已复制到剪贴板', 'success');
}

// ==================== 创建用户功能 ====================

// 显示创建用户模态框
function showCreateUserModal() {
    document.getElementById('createUserName').value = '';
    document.getElementById('createUserPhone').value = '';
    document.getElementById('createUserModal').classList.add('show');
}

// 提交创建用户表单
document.getElementById('createUserForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const name = document.getElementById('createUserName').value.trim();
    const phone = document.getElementById('createUserPhone').value.trim();
    
    // 验证手机号格式
    if (!/^1[3-9]\d{9}$/.test(phone)) {
        showToast('请输入正确的11位手机号', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${USER_API_BASE_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, phone })
        });
        
        const result = await response.json();
        
        if (result.code === 200) {
            showToast('用户创建成功！UID: ' + result.data.uid, 'success');
            closeModal('createUserModal');
            
            // 显示新用户信息
            setTimeout(() => {
                alert(
                    `✅ 用户创建成功！\n\n` +
                    `姓名：${result.data.name}\n` +
                    `手机号：${result.data.phone}\n` +
                    `UID：${result.data.uid}\n\n` +
                    `⚠️ 请记录UID，后续需要用它来设置角色和生成API Key`
                );
            }, 300);
            
            // 刷新用户列表
            loadUsers();
        } else {
            showToast('创建失败: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('创建用户失败:', error);
        showToast('创建失败，请检查网络连接', 'error');
    }
});
