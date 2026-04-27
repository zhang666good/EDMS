from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Body

from app.services.knowledge import Knowledge, KnowledgeApiError, KnowledgeTransportError


router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


def _http_error(status_code: int, code: str, message: str, detail: Optional[Any] = None) -> HTTPException:
    payload = {"code": code, "message": message, "detail": detail}
    return HTTPException(status_code=status_code, detail=payload)


def _build_knowledge_client() -> Knowledge:
    # support both DIFY_BASE_URL and DIFY_API_BASE_URL env var names
    raw_base_url = os.getenv("DIFY_BASE_URL", "").strip() or os.getenv("DIFY_API_BASE_URL", "").strip()
    api_key = os.getenv("DIFY_API_KEY", "").strip()

    # fallback: if no DIFY_API_KEY, try any DIFY_AGENT_* env var
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
        raise HTTPException(status_code=500, detail={"code": "DIFY_CONFIG_MISSING", "message": "Dify config missing", "missing": missing})

    # return client; Knowledge will normalize url as needed
    return Knowledge(base_url=raw_base_url, api_key=api_key)


def _handle_client_exceptions(exc: Exception) -> HTTPException:
    if isinstance(exc, KnowledgeApiError):
        return _http_error(exc.status_code, "DIFY_API_ERROR", exc.message, exc.response)
    if isinstance(exc, KnowledgeTransportError):
        return _http_error(502, "DIFY_TRANSPORT_ERROR", str(exc), None)
    return _http_error(500, "INTERNAL_ERROR", str(exc), None)


@router.get("/datasets")
def list_datasets(page: Optional[int] = None, limit: Optional[int] = None, client: Knowledge = Depends(_build_knowledge_client)) -> Any:
    try:
        return client.list_datasets(page=page, limit=limit)
    except Exception as exc:
        raise _handle_client_exceptions(exc)


@router.post("/datasets")
def create_dataset(payload: Dict[str, Any] = Body(...), client: Knowledge = Depends(_build_knowledge_client)) -> Any:
    try:
        return client.create_dataset(payload)
    except Exception as exc:
        raise _handle_client_exceptions(exc)


@router.delete("/datasets/{dataset_id}")
def delete_dataset(dataset_id: str, client: Knowledge = Depends(_build_knowledge_client)) -> Any:
    try:
        return client.delete_dataset(dataset_id)
    except Exception as exc:
        raise _handle_client_exceptions(exc)


@router.post("/datasets/{dataset_id}/documents/text")
def create_document_by_text(dataset_id: str, payload: Dict[str, Any] = Body(...), client: Knowledge = Depends(_build_knowledge_client)) -> Any:
    try:
        return client.create_document_by_text(dataset_id, payload)
    except Exception as exc:
        raise _handle_client_exceptions(exc)


@router.post("/datasets/{dataset_id}/documents/file")
async def create_document_by_file(dataset_id: str, file: UploadFile = File(...), data: Optional[str] = Form(None), client: Knowledge = Depends(_build_knowledge_client)) -> Any:
    # save upload to a temp file then forward to client
    tmp_dir = tempfile.mkdtemp(prefix="dify_upload_")
    tmp_path = Path(tmp_dir) / (file.filename or "upload.bin")
    try:
        with tmp_path.open("wb") as f:
            content = await file.read()
            f.write(content)

        extra = None
        if data:
            try:
                extra = json.loads(data)
            except Exception:
                # if not json, keep as string in data field
                extra = data

        form_data = None
        if extra is not None:
            # client expects data as dict that will be json-dumped by the client
            form_data = extra if isinstance(extra, dict) else {"data": str(extra)}

        return client.create_document_by_file(dataset_id, str(tmp_path), data=form_data)
    except Exception as exc:
        raise _handle_client_exceptions(exc)
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        try:
            Path(tmp_dir).rmdir()
        except Exception:
            pass


@router.get("/datasets/{dataset_id}/documents")
def list_documents(dataset_id: str, page: Optional[int] = None, limit: Optional[int] = None, client: Knowledge = Depends(_build_knowledge_client)) -> Any:
    try:
        return client.list_documents(dataset_id, page=page, limit=limit)
    except Exception as exc:
        raise _handle_client_exceptions(exc)


@router.delete("/datasets/{dataset_id}/documents/{document_id}")
def delete_document(dataset_id: str, document_id: str, client: Knowledge = Depends(_build_knowledge_client)) -> Any:
    try:
        return client.delete_document(dataset_id, document_id)
    except Exception as exc:
        raise _handle_client_exceptions(exc)


@router.post("/datasets/{dataset_id}/retrieve")
def retrieve(dataset_id: str, payload: Dict[str, Any] = Body(...), client: Knowledge = Depends(_build_knowledge_client)) -> Any:
    try:
        return client.retrieve(dataset_id, payload)
    except Exception as exc:
        raise _handle_client_exceptions(exc)


@router.post("/pipeline/file-upload")
async def upload_pipeline_file(file: UploadFile = File(...), client: Knowledge = Depends(_build_knowledge_client)) -> Any:
    tmp_dir = tempfile.mkdtemp(prefix="dify_pipeline_")
    tmp_path = Path(tmp_dir) / (file.filename or "upload.bin")
    try:
        with tmp_path.open("wb") as f:
            f.write(await file.read())
        return client.upload_pipeline_file(str(tmp_path))
    except Exception as exc:
        raise _handle_client_exceptions(exc)
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        try:
            Path(tmp_dir).rmdir()
        except Exception:
            pass

