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
from app.api.role_auth import get_role_from_api_key, validate_role_access, get_allowed_agents_for_role

router = APIRouter(prefix="/v1", tags=["openai-compat"])


# NextChat can select one of these models, then gateway maps to different Dify apps.
MODEL_TO_AGENT_ALIAS: Dict[str, str] = {
    "edms-annual-report": "annual_report_analyst",
    "edms-deep-insight": "deep_insight_analyst",
    "edms-auto-report": "auto_report_expert",
    "edms-power-standard": "power_standard_query",
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


def _resolve_agent_alias(model: str, client: DifyGatewayClient, role: Optional[str] = None) -> str:
    available_agents = {item.alias for item in client.list_agents()}

    mapped_alias = MODEL_TO_AGENT_ALIAS.get(model)
    if mapped_alias:
        if mapped_alias not in available_agents:
            raise _http_error(400, "AGENT_NOT_CONFIGURED", "Mapped agent is not configured in gateway", {"model": model, "agent": mapped_alias})
        
        # 验证角色权限
        if role and not validate_role_access(role, mapped_alias):
            allowed = get_allowed_agents_for_role(role)
            raise _http_error(
                403,
                "ACCESS_DENIED",
                f"Role '{role}' cannot access model '{model}' (agent: {mapped_alias}). Allowed agents: {', '.join(allowed)}",
                None
            )
        
        return mapped_alias

    # Allow direct agent alias as model for easier debugging.
    if model in available_agents:
        # 验证角色权限
        if role and not validate_role_access(role, model):
            allowed = get_allowed_agents_for_role(role)
            raise _http_error(
                403,
                "ACCESS_DENIED",
                f"Role '{role}' cannot access agent '{model}'. Allowed agents: {', '.join(allowed)}",
                None
            )
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
def list_models(
    authorization: Optional[str] = Header(default=None, alias="Authorization")
) -> Dict[str, Any]:
    """
    列出当前角色可访问的模型
    """
    # 严格模式：必须提供Authorization头
    if not authorization:
        raise _http_error(
            401,
            "AUTHORIZATION_REQUIRED",
            "Authorization header is required. Format: Bearer edms-{role}-{key}",
            None
        )
    
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    
    role = get_role_from_api_key(token.strip())
    
    # 如果无法识别API Key，拒绝访问
    if not role:
        raise _http_error(
            401,
            "INVALID_API_KEY",
            "Unrecognized API key. Please use a valid role-based API key (e.g., edms-power-expert-xxxx)",
            None
        )
    
    now = int(time.time())
    
    all_models = list(MODEL_TO_AGENT_ALIAS.keys())
    
    # 根据角色过滤模型列表
    allowed_agents = get_allowed_agents_for_role(role)
    filtered_models = [
        model_id for model_id, agent_alias in MODEL_TO_AGENT_ALIAS.items()
        if agent_alias in allowed_agents
    ]
    all_models = filtered_models
    
    return {
        "object": "list",
        "data": [
            {
                "id": model_id,
                "object": "model",
                "created": now,
                "owned_by": "enterprise-decision-gateway",
            }
            for model_id in all_models
        ],
    }

#该接口的调试打印代码 由 qwen ai 辅助编写
@router.post("/chat/completions")
def chat_completions(
    request: OpenAIChatCompletionsRequest = Body(...),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    client: DifyGatewayClient = Depends(get_gateway_client),
):
    """
    OpenAI兼容的聊天接口 - 支持基于角色的访问控制
    """
    # ========== 1. 打印请求信息 ==========
    print("\n" + "="*80)
    print("📨 [REQUEST] /v1/chat/completions")
    print("="*80)
    print(f"⏰ 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 Model: {request.model}")
    print(f"👤 User: {request.user or DEFAULT_USER}")
    print(f"🌊 Stream: {request.stream}")
    if request.messages:
        print(f"💬 Messages ({len(request.messages)}条):")
        for i, msg in enumerate(request.messages, 1):
            content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            print(f"   [{i}] {msg.role}: {content_preview}")
    if request.context_id:
        print(f"📎 Context ID: {request.context_id}")
    if request.md_content:
        md_preview = request.md_content[:100] + "..." if len(request.md_content) > 100 else request.md_content
        print(f"📄 MD Content: {md_preview}")
    print("-"*80)
    
    # ========== 2. 打印认证头信息 ==========
    print("🔐 [AUTH] 认证信息")
    print("-"*80)
    
    # 严格模式：必须提供Authorization头
    if not authorization:
        print("❌ Authorization头: 缺失")
        print("="*80 + "\n")
        raise _http_error(
            401,
            "AUTHORIZATION_REQUIRED",
            "Authorization header is required. Format: Bearer edms-{role}-{key}",
            None
        )
    
    print(f"✅ Authorization头: {authorization[:50]}..." if len(authorization) > 50 else f"✅ Authorization头: {authorization}")
    
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]
        print(f"🔑 提取Token: {token[:30]}..." if len(token) > 30 else f"🔑 提取Token: {token}")
    else:
        print(f"⚠️  Token格式: 非Bearer格式")
    
    # ========== 3. 数据库验证 ==========
    print("\n🗄️  [DB] 数据库验证")
    print("-"*80)
    print(f"🔍 查询API Key: {token.strip()[:30]}...")
    
    role = get_role_from_api_key(token.strip())
    
    if role:
        print(f"✅ 验证结果: 成功")
        print(f"👥 识别角色: {role}")
        
        # 获取用户详细信息（如果有）
        try:
            from app.services.user_service import get_user_by_api_key
            user_info = get_user_by_api_key(token.strip())
            if user_info:
                print(f"📝 用户UID: {user_info.get('uid', 'N/A')}")
                print(f"📛 用户姓名: {user_info.get('name', 'N/A')}")
                print(f"📱 手机号: {user_info.get('phone', 'N/A')}")
        except Exception as e:
            print(f"⚠️  获取用户详情失败: {e}")
    else:
        print(f"❌ 验证结果: 失败")
        print(f"🚫 原因: API Key不在数据库中")
        print("="*80 + "\n")
        raise _http_error(
            401,
            "INVALID_API_KEY",
            "Unrecognized API key. Please use a valid role-based API key (e.g., edms-power-expert-xxxx)",
            None
        )
    
    print("-"*80)
    
    agent_alias = _resolve_agent_alias(request.model, client, role)
    query = _build_query(request.messages)
    
    print(f"🎯 解析Agent: {agent_alias}")
    print(f"📝 构建Query长度: {len(query)} 字符")
    print("="*80 + "\n")

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
        print(f"\n❌ [ERROR] Dify网关错误: {exc.message}")
        print("="*80 + "\n")
        raise _http_error(exc.status_code, "DIFY_UPSTREAM_ERROR", "Dify upstream request failed", exc.detail or exc.message) from exc

    if request.stream:
        print("🌊 [STREAM] 开始流式响应\n")
        return StreamingResponse(
            _openai_stream_from_dify(upstream, model=request.model),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    final_answer = _collect_final_answer_from_dify(upstream)
    
    # ========== 4. 打印响应信息 ==========
    print("\n" + "="*80)
    print("📤 [RESPONSE] 响应信息")
    print("="*80)
    print(f"✅ 状态: 成功")
    print(f"📊 回答长度: {len(final_answer)} 字符")
    answer_preview = final_answer[:200] + "..." if len(final_answer) > 200 else final_answer
    print(f"💬 回答预览:\n{answer_preview}")
    print("="*80 + "\n")
    
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
