from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Query, Body
from fastapi.responses import JSONResponse

from app.services.knowledge import Knowledge, KnowledgeApiError, KnowledgeTransportError


router = APIRouter(prefix="/api/v1/backend", tags=["backend-management"])


def _http_error(status_code: int, code: str, message: str, detail: Optional[Any] = None) -> HTTPException:
    payload = {"code": code, "message": message, "detail": detail}
    return HTTPException(status_code=status_code, detail=payload)


def _build_knowledge_client() -> Knowledge:
    """构建 Dify 知识库客户端"""
    # support both DIFY_API_BASE_URL and DIFY_BASE_URL env var names (priority: DIFY_API_BASE_URL)
    raw_base_url = os.getenv("DIFY_API_BASE_URL", "").strip() or os.getenv("DIFY_BASE_URL", "").strip()
    api_key = os.getenv("DIFY_API_KEY", "dataset-c6isoIYCm9MhwW9eOO25aKGF").strip()

    # fallback: 如果没有 DIFY_API_KEY，尝试使用任何 DIFY_AGENT_* 环境变量
    if not api_key:
        for k, v in os.environ.items():
            if k.startswith("DIFY_AGENT_") and v.strip():
                api_key = v.strip()
                break

    if not raw_base_url or not api_key:
        missing = []
        if not raw_base_url:
            missing.append("DIFY_BASE_URL or DIFY_API_BASE_URL")
        if not api_key:
            missing.append("DIFY_API_KEY or DIFY_AGENT_*")
        raise HTTPException(
            status_code=500,
            detail={"code": "DIFY_CONFIG_MISSING", "message": "Dify 配置缺失", "missing": missing}
        )

    return Knowledge(base_url=raw_base_url, api_key=api_key)


def _handle_client_exceptions(exc: Exception) -> HTTPException:
    """统一处理客户端异常"""
    if isinstance(exc, KnowledgeApiError):
        return _http_error(exc.status_code, "DIFY_API_ERROR", exc.message, exc.response)
    if isinstance(exc, KnowledgeTransportError):
        return _http_error(502, "DIFY_TRANSPORT_ERROR", str(exc), None)
    return _http_error(500, "INTERNAL_ERROR", str(exc), None)


# ==================== 知识库管理 ====================

@router.get("/datasets", summary="查询知识库列表")
def list_datasets(
    page: Optional[int] = Query(None, description="页码"),
    limit: Optional[int] = Query(None, description="每页数量"),
    client: Knowledge = Depends(_build_knowledge_client)
) -> Any:
    """
    查询所有知识库列表
    
    - **page**: 页码（可选）
    - **limit**: 每页数量（可选）
    """
    try:
        return client.list_datasets(page=page, limit=limit)
    except Exception as exc:
        raise _handle_client_exceptions(exc)


@router.post("/datasets", summary="创建知识库")
def create_dataset(
    name: str = Form(..., description="知识库名称"),
    description: Optional[str] = Form(None, description="知识库描述"),
    indexing_technique: Optional[str] = Form("high_quality", description="索引技术：high_quality 或 economy"),
    client: Knowledge = Depends(_build_knowledge_client)
) -> Any:
    """
    创建新的知识库
    
    - **name**: 知识库名称（必填）
    - **description**: 知识库描述（可选）
    - **indexing_technique**: 索引技术，默认 high_quality
    """
    try:
        payload = {
            "name": name,
            "description": description or "",
            "indexing_technique": indexing_technique,
        }
        return client.create_dataset(payload)
    except Exception as exc:
        raise _handle_client_exceptions(exc)


@router.delete("/datasets/{dataset_id}", summary="删除知识库")
def delete_dataset(
    dataset_id: str,
    client: Knowledge = Depends(_build_knowledge_client)
) -> Any:
    """
    删除指定知识库
    
    - **dataset_id**: 知识库 ID
    """
    try:
        return client.delete_dataset(dataset_id)
    except Exception as exc:
        raise _handle_client_exceptions(exc)


# ==================== 文档管理 ====================

@router.get("/datasets/{dataset_id}/documents", summary="查询文档列表")
def list_documents(
    dataset_id: str,
    page: Optional[int] = Query(None, description="页码"),
    limit: Optional[int] = Query(None, description="每页数量"),
    client: Knowledge = Depends(_build_knowledge_client)
) -> Any:
    """
    查询知识库中的文档列表
    
    - **dataset_id**: 知识库 ID
    - **page**: 页码（可选）
    - **limit**: 每页数量（可选）
    """
    try:
        return client.list_documents(dataset_id, page=page, limit=limit)
    except Exception as exc:
        raise _handle_client_exceptions(exc)


@router.post("/datasets/{dataset_id}/documents/file", summary="上传文件到知识库")
async def add_file_to_dataset(
    dataset_id: str,
    file: UploadFile = File(..., description="要上传的文件"),
    document_name: Optional[str] = Form(None, description="文档名称（默认为文件名）"),
    process_rule: Optional[str] = Form(None, description="处理规则 JSON 字符串"),
    client: Knowledge = Depends(_build_knowledge_client)
) -> Any:
    """
    上传文件到指定知识库
    
    支持的文件格式：PDF, DOC, DOCX, TXT, MD, HTML 等
    
    - **dataset_id**: 知识库 ID
    - **file**: 要上传的文件
    - **document_name**: 文档名称（可选，默认为原始文件名）
    - **process_rule**: 处理规则（可选），JSON 格式，如：{"mode": "automatic"}
    
    返回文档信息和索引状态
    """
    tmp_dir = None
    tmp_path = None
    try:
        # 调试信息：打印请求参数
        print(f"\n{'='*60}")
        print(f" [API接口] 收到文件上传请求")
        print(f"   dataset_id: {dataset_id}")
        print(f"   文件名: {file.filename}")
        print(f"   文件类型: {file.content_type}")
        print(f"   document_name: {document_name}")
        print(f"   process_rule: {process_rule}")
        print(f"{'='*60}\n")
        
        # 保存上传文件到临时目录
        tmp_dir = tempfile.mkdtemp(prefix="dify_upload_")
        tmp_path = Path(tmp_dir) / (file.filename or "upload.bin")
        
        with tmp_path.open("wb") as f:
            content = await file.read()
            f.write(content)
        
        print(f"📁 [临时文件] 已保存到: {tmp_path}")
        print(f"   文件大小: {tmp_path.stat().st_size} bytes\n")

        # 构建额外参数
        extra_data = {}
        if document_name:
            extra_data["name"] = document_name
        
        if process_rule:
            try:
                import json
                extra_data["process_rule"] = json.loads(process_rule)
            except Exception:
                pass

        # 调用知识库服务上传文件
        form_data = extra_data if extra_data else None
        print(f"📤 [调用服务] 开始上传到Dify...")
        result = client.create_document_by_file(dataset_id, str(tmp_path), data=form_data)
        
        print(f"✅ [API接口] 文件上传成功\n")
        return JSONResponse(
            status_code=200,
            content={
                "code": 0,
                "message": "文件上传成功",
                "data": result
            }
        )
        
    except Exception as exc:
        # 详细错误日志
        print(f"\n❌ [API接口] 文件上传失败")
        print(f"   dataset_id: {dataset_id}")
        print(f"   filename: {file.filename}")
        print(f"   错误类型: {type(exc).__name__}")
        print(f"   错误信息: {str(exc)}")
        
        # 如果是KnowledgeApiError，打印Dify返回的原始响应
        if isinstance(exc, KnowledgeApiError):
            print(f"   Dify响应: {exc.response}")
        print()
        
        raise _handle_client_exceptions(exc)
    finally:
        # 清理临时文件
        try:
            if tmp_path:
                tmp_path.unlink(missing_ok=True)
                print(f"🗑️ [清理] 已删除临时文件: {tmp_path}")
            if tmp_dir:
                Path(tmp_dir).rmdir()
                print(f"🗑️ [清理] 已删除临时目录: {tmp_dir}")
        except Exception:
            pass


@router.delete("/datasets/{dataset_id}/documents/{document_id}", summary="删除文档")
def delete_document(
    dataset_id: str,
    document_id: str,
    client: Knowledge = Depends(_build_knowledge_client)
) -> Any:
    """
    删除知识库中的指定文档
    
    - **dataset_id**: 知识库 ID
    - **document_id**: 文档 ID
    """
    try:
        return client.delete_document(dataset_id, document_id)
    except Exception as exc:
        raise _handle_client_exceptions(exc)


# ==================== 文本内容管理 ====================

@router.post("/datasets/{dataset_id}/documents/text", summary="通过文本创建文档")
def create_document_by_text(
    dataset_id: str,
    name: str = Form(..., description="文档名称"),
    text: str = Form(..., description="文本内容"),
    client: Knowledge = Depends(_build_knowledge_client)
) -> Any:
    """
    通过文本内容创建文档
    
    - **dataset_id**: 知识库 ID
    - **name**: 文档名称
    - **text**: 文本内容
    """
    try:
        payload = {
            "name": name,
            "text": text,
        }
        result = client.create_document_by_text(dataset_id, payload)
        
        return JSONResponse(
            status_code=200,
            content={
                "code": 0,
                "message": "文本创建成功",
                "data": result
            }
        )
    except Exception as exc:
        raise _handle_client_exceptions(exc)


# ==================== 检索功能 ====================

@router.post("/datasets/{dataset_id}/retrieve", summary="检索知识库")
def retrieve_from_dataset(
    dataset_id: str,
    query: str = Form(..., description="检索关键词"),
    top_k: Optional[int] = Form(5, description="返回结果数量"),
    score_threshold: Optional[float] = Form(None, description="相似度阈值"),
    client: Knowledge = Depends(_build_knowledge_client)
) -> Any:
    """
    在知识库中检索相关内容
    
    - **dataset_id**: 知识库 ID
    - **query**: 检索关键词
    - **top_k**: 返回结果数量（默认 5）
    - **score_threshold**: 相似度阈值（可选，0-1 之间）
    """
    try:
        payload = {
            "query": query,
            "retrieval_model": {
                "search_method": "semantic_search",
                "reranking_enable": True,
                "reranking_mode": "reranking_model",
                "top_k": top_k or 5,
            }
        }
        
        if score_threshold is not None:
            payload["retrieval_model"]["score_threshold_enabled"] = True
            payload["retrieval_model"]["score_threshold"] = score_threshold
        
        result = client.retrieve(dataset_id, payload)
        
        return JSONResponse(
            status_code=200,
            content={
                "code": 0,
                "message": "检索成功",
                "data": result
            }
        )
    except Exception as exc:
        raise _handle_client_exceptions(exc)


# ==================== 批量操作 ====================

@router.post("/datasets/{dataset_id}/documents/batch-upload", summary="批量上传文件")
async def batch_upload_files(
    dataset_id: str,
    files: list[UploadFile] = File(..., description="要上传的文件列表"),
    client: Knowledge = Depends(_build_knowledge_client)
) -> Any:
    """
    批量上传多个文件到知识库
    
    - **dataset_id**: 知识库 ID
    - **files**: 文件列表（最多 10 个）
    
    返回每个文件的上传结果
    """
    if len(files) > 10:
        raise _http_error(400, "TOO_MANY_FILES", "一次最多上传 10 个文件")
    
    results = []
    errors = []
    
    for file in files:
        tmp_dir = None
        tmp_path = None
        try:
            # 保存文件
            tmp_dir = tempfile.mkdtemp(prefix="dify_batch_")
            tmp_path = Path(tmp_dir) / (file.filename or "upload.bin")
            
            with tmp_path.open("wb") as f:
                content = await file.read()
                f.write(content)
            
            # 上传到 Dify
            result = client.create_document_by_file(dataset_id, str(tmp_path))
            results.append({
                "filename": file.filename,
                "status": "success",
                "data": result
            })
            
        except Exception as exc:
            errors.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(exc)
            })
        finally:
            # 清理临时文件
            try:
                if tmp_path:
                    tmp_path.unlink(missing_ok=True)
                if tmp_dir:
                    Path(tmp_dir).rmdir()
            except Exception:
                pass
    
    return JSONResponse(
        status_code=200,
        content={
            "code": 0,
            "message": f"批量上传完成：成功 {len(results)} 个，失败 {len(errors)} 个",
            "data": {
                "success": results,
                "failed": errors
            }
        }
    )


# ==================== 上交所公告导入 ====================

@router.post("/sse/search", summary="搜索上交所公告")
async def search_sse_announcements(
    params: Dict[str, Any] = Body(..., description="搜索参数")
) -> Any:
    """
    搜索上交所公告
    
    请求体示例：
    {
        "keyword": "年度报告",
        "page": 0,
        "limit": 10,
        "searchMode": "fuzzy",
        "orderByKey": "score",
        "orderByDirection": "DESC",
        "spaceId": 3
    }
    """
    import traceback
    try:
        print(f"[SSE Search] 收到搜索请求: {params}")
        from app.services.auto_into_knowledge import main as sse_search
        result = await sse_search({"params": params})
        print(f"[SSE Search] 搜索结果: {result.get('status')}, 数量: {result.get('count', 0)}")
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[SSE Search] 错误: {str(e)}")
        print(f"[SSE Search] 堆栈:\n{error_trace}")
        return JSONResponse(
            status_code=200,  # 改为 200，让前端处理错误
            content={
                "status": "error",
                "message": f"搜索失败: {str(e)}",
                "detail": error_trace if params.get("debug") else None
            }
        )


@router.post("/sse/import-to-dataset", summary="导入上交所公告到知识库")
async def import_sse_to_dataset(
    params: Dict[str, Any] = Body(..., description="导入参数")
) -> Any:
    """
    下载搜索到的PDF并上传到指定知识库
    
    请求体示例：
    {
        "search_results": [...],  # 搜索结果列表（来自 /sse/search）
        "dataset_id": "知识库ID"
    }
    """
    try:
        from app.services.auto_into_knowledge import download_and_upload_to_knowledge
        result = await download_and_upload_to_knowledge({"params": params})
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"导入失败: {str(e)}"
            }
        )
