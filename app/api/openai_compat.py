from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Dict, Iterator, List, Literal, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.dify_gateway import DifyGatewayClient, DifyGatewayError
from app.api.gateway import get_gateway_client

router = APIRouter(prefix="/v1", tags=["openai-compat"])


# NextChat can select one of these models, then gateway maps to different Dify apps.
MODEL_TO_AGENT_ALIAS: Dict[str, str] = {
    "edms-annual-report": "annual_report_analyst",
    "edms-deep-insight": "deep_insight_analyst",
    "edms-auto-report": "auto_report_expert",
}

DEFAULT_MODEL = "edms-deep-insight"
DEFAULT_USER = "nextchat-user"


class OpenAIMessage(BaseModel):
    role: Literal["system", "developer", "user", "assistant", "tool"]
    content: Any


class OpenAIChatCompletionsRequest(BaseModel):
    model: str = Field(default=DEFAULT_MODEL)
    messages: List[OpenAIMessage]
    stream: bool = True
    user: Optional[str] = None
    context_id: Optional[str] = None  # 新增上下文ID字段
    md_content: Optional[str] = None  # 新增直接传递md内容字段

    # Keep common OpenAI fields for compatibility; they are ignored by current Dify route.
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None


def _http_error(status_code: int, code: str, message: str, detail: Any = None) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": message,
            "detail": detail,
        },
    )


def _extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("text"), str):
                    parts.append(item["text"])
        return "\n".join(part for part in parts if part).strip()

    if isinstance(content, dict) and isinstance(content.get("text"), str):
        return content["text"].strip()

    return ""


def _build_query(messages: List[OpenAIMessage]) -> str:
    system_parts: list[str] = []
    latest_user = ""

    for msg in messages:
        text = _extract_text_content(msg.content)
        if not text:
            continue
        if msg.role in ("system", "developer"):
            system_parts.append(text)
        if msg.role == "user":
            latest_user = text

    if not latest_user:
        raise _http_error(400, "INVALID_MESSAGES", "At least one non-empty user message is required", None)

    if not system_parts:
        return latest_user

    system_prompt = "\n".join(system_parts)
    return f"系统指令:\n{system_prompt}\n\n用户问题:\n{latest_user}"


def _resolve_agent_alias(model: str, client: DifyGatewayClient) -> str:
    available_agents = {item.alias for item in client.list_agents()}

    mapped_alias = MODEL_TO_AGENT_ALIAS.get(model)
    if mapped_alias:
        if mapped_alias not in available_agents:
            raise _http_error(400, "AGENT_NOT_CONFIGURED", "Mapped agent is not configured in gateway", {"model": model, "agent": mapped_alias})
        return mapped_alias

    # Allow direct agent alias as model for easier debugging.
    if model in available_agents:
        return model

    raise _http_error(
        400,
        "MODEL_NOT_SUPPORTED",
        "Model is not supported by openai-compatible gateway",
        {"model": model, "supported_models": sorted(MODEL_TO_AGENT_ALIAS.keys())},
    )


def _openai_sse_data(payload: Dict[str, Any]) -> bytes:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")


def _openai_chunk(chunk_id: str, model: str, delta: Dict[str, Any], finish_reason: Optional[str] = None) -> Dict[str, Any]:
    return {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": delta,
                "finish_reason": finish_reason,
            }
        ],
    }


def _openai_stream_from_dify(stream_response, model: str) -> Iterator[bytes]:
    chunk_id = f"chatcmpl-{uuid.uuid4().hex}"
    answer_chunks: list[str] = []
    thought_fallback = ""
    sent_role = False

    try:
        while True:
            line = stream_response.readline()
            if not line:
                break

            text_line = line.decode("utf-8", errors="ignore").strip()
            if not text_line or not text_line.startswith("data:"):
                continue

            raw_payload = text_line[len("data:") :].strip()
            if not raw_payload:
                continue

            try:
                payload = json.loads(raw_payload)
            except Exception:
                continue

            event = payload.get("event")

            if not sent_role:
                yield _openai_sse_data(_openai_chunk(chunk_id, model, {"role": "assistant"}, None))
                sent_role = True

            if event in {"message", "agent_message"}:
                content = str(payload.get("answer") or "")
                if content:
                    answer_chunks.append(content)
                    yield _openai_sse_data(_openai_chunk(chunk_id, model, {"content": content}, None))
                continue

            if event == "agent_thought":
                thought = str(payload.get("thought") or "")
                if thought:
                    thought_fallback = thought
                continue

            if event == "error":
                # Keep stream protocol valid for NextChat by converting error to assistant text.
                err_text = payload.get("message") or payload.get("detail") or "Upstream stream error"
                yield _openai_sse_data(_openai_chunk(chunk_id, model, {"content": f"\n[UPSTREAM_ERROR] {err_text}"}, None))
                yield _openai_sse_data(_openai_chunk(chunk_id, model, {}, "stop"))
                yield b"data: [DONE]\n\n"
                return

            if event == "message_end":
                if not answer_chunks and thought_fallback:
                    yield _openai_sse_data(_openai_chunk(chunk_id, model, {"content": thought_fallback}, None))

                yield _openai_sse_data(_openai_chunk(chunk_id, model, {}, "stop"))
                yield b"data: [DONE]\n\n"
                return

        # Normal EOF fallback.
        yield _openai_sse_data(_openai_chunk(chunk_id, model, {}, "stop"))
        yield b"data: [DONE]\n\n"
    finally:
        stream_response.close()


def _collect_final_answer_from_dify(stream_response) -> str:
    answer_chunks: list[str] = []
    thought_fallback = ""

    try:
        while True:
            line = stream_response.readline()
            if not line:
                break

            text_line = line.decode("utf-8", errors="ignore").strip()
            if not text_line or not text_line.startswith("data:"):
                continue

            raw_payload = text_line[len("data:") :].strip()
            if not raw_payload:
                continue

            try:
                payload = json.loads(raw_payload)
            except Exception:
                continue

            event = payload.get("event")
            if event in {"message", "agent_message"}:
                chunk = str(payload.get("answer") or "")
                if chunk:
                    answer_chunks.append(chunk)
                continue

            if event == "agent_thought":
                thought = str(payload.get("thought") or "")
                if thought:
                    thought_fallback = thought
                continue

            if event == "message_end":
                final_answer = "".join(answer_chunks).strip()
                return final_answer or thought_fallback.strip()

        return "".join(answer_chunks).strip() or thought_fallback.strip()
    finally:
        stream_response.close()


@router.get("/models")
def list_models(_authorization: Optional[str] = Header(default=None, alias="Authorization")) -> Dict[str, Any]:
    now = int(time.time())
    return {
        "object": "list",
        "data": [
            {
                "id": model_id,
                "object": "model",
                "created": now,
                "owned_by": "enterprise-decision-gateway",
            }
            for model_id in MODEL_TO_AGENT_ALIAS
        ],
    }


@router.post("/chat/completions")
def chat_completions(
    request: OpenAIChatCompletionsRequest = Body(...),
    _authorization: Optional[str] = Header(default=None, alias="Authorization"),
    client: DifyGatewayClient = Depends(get_gateway_client),
):
    agent_alias = _resolve_agent_alias(request.model, client)
    query = _build_query(request.messages)

    # 注入上下文
    context_text = None
    if request.md_content:
        context_text = request.md_content
    elif request.context_id:
        # 从文件系统读取md内容
        md_path = os.path.join("mineru_temp_md", f"{request.context_id}.md")
        if os.path.exists(md_path):
            with open(md_path, "r", encoding="utf-8") as f:
                context_text = f.read()
    if context_text:
        query = f"【上下文资料】\n{context_text}\n\n{query}"

    dify_payload = {
        "agent": agent_alias,
        "query": query,
        "user": request.user or DEFAULT_USER,
        "inputs": {},
        "response_mode": "streaming",
    }

    try:
        upstream = client.open_chat_stream(dify_payload)
    except DifyGatewayError as exc:
        raise _http_error(exc.status_code, "DIFY_UPSTREAM_ERROR", "Dify upstream request failed", exc.detail or exc.message) from exc

    if request.stream:
        return StreamingResponse(
            _openai_stream_from_dify(upstream, model=request.model),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    final_answer = _collect_final_answer_from_dify(upstream)
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": final_answer},
                "finish_reason": "stop",
            }
        ],
    }
