// API 配置
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1/backend';

// 登录凭证（从 .env 读取，这里硬编码）
const ADMIN_USERNAME = 'zhang666';
const ADMIN_PASSWORD = 'Python666good@';

// 全局状态
let currentDatasetId = null;
let selectedBatchFiles = [];

// ==================== 登录功能 ====================

document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (username === ADMIN_USERNAME && password === ADMIN_PASSWORD) {
        // 登录成功
        localStorage.setItem('isLoggedIn', 'true');
        localStorage.setItem('username', username);
        showApp();
        showToast('登录成功', 'success');
    } else {
        // 登录失败
        document.getElementById('errorMessage').style.display = 'block';
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
    localStorage.removeItem('username');
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
            'upload': '批量上传'
        };
        document.getElementById('pageTitle').textContent = titles[page];
        
        // 加载数据
        if (page === 'datasets') {
            loadDatasets();
        } else if (page === 'documents') {
            loadDatasetSelect();
        } else if (page === 'upload') {
            loadBatchDatasetSelect();
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
