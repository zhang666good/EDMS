import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from app.services.mineru_file_parser import parse_by_file_v4, poll_batch_result_v4
from app.services.zip_extr_md import download_and_extract_md

router = APIRouter()

UPLOAD_DIR = "data_file_temp"
MD_DIR = "mineru_temp_md"

@router.post("/api/v1/gateway/upload")
async def upload_and_parse(file: UploadFile = File(...)):
    # 1. 保存上传文件
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    # 2. 解析并上传到 MinerU
    batch_id, file_urls = parse_by_file_v4(file_path)
    if not batch_id:
        return JSONResponse({"code": 1, "msg": "上传到 MinerU 失败"}, status_code=500)
    # 3. 轮询 MinerU 解析结果
    result = poll_batch_result_v4(batch_id)
    if not result:
        return JSONResponse({"code": 2, "msg": "MinerU 解析超时"}, status_code=500)
    # 4. 获取 zip 下载链接，解压 full.md
    zip_url = result["extract_result"][0]["full_zip_url"]
    md_path = download_and_extract_md(zip_url, MD_DIR)
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    context_id = os.path.splitext(os.path.basename(md_path))[0]
    # 可选：存储 context_id <-> md_content 映射到缓存/数据库
    return {"code": 0, "context_id": context_id, "md_content": md_content}

# 在 main.py 中 include_router(router)

# 网关对话注入示例
# 在 /api/v1/gateway/chat 路由中：
# 1. 前端传 context_id 或 md_content
# 2. 后端查找 md_content（如从缓存/数据库/文件读取 mineru_temp_md/{context_id}.md）
# 3. 拼接到 prompt 或 inputs 传递给 dify agent

