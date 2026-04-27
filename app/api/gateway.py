from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, Depends, File, Form, HTTPException, Body, UploadFile
from fastapi.responses import PlainTextResponse, StreamingResponse

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

# Support direct .env usage even when importing this module standalone.
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env", override=False)

from app.schema.gateway import (
    AgentInfo,
    AgentListResponse,
    ChatMessageRequest,
    StopTaskRequest,
)
from app.services.baidu_stt import BaiduSpeechToTextClient, BaiduSpeechToTextError
from app.services.dify_gateway import DifyAgent, DifyGatewayClient, DifyGatewayError, final_answer_sse_iterator


router = APIRouter(prefix="/api/v1/gateway", tags=["dify-gateway"])


# Keep aliases stable for frontend routing.
AGENT_ALIAS_TO_ENV = {
    "annual_report_analyst": ("上市公司年报数据提取分析师", "DIFY_AGENT_ANNUAL_REPORT_KEY"),
    "deep_insight_analyst": ("深度洞察分析师", "DIFY_AGENT_DEEP_INSIGHT_KEY"),
    "auto_report_expert": ("智能报告自动生成专家", "DIFY_AGENT_AUTO_REPORT_KEY"),
}

INTENT_ROUTE_MAP = {
    "query": "annual_report_analyst",
    "compare": "deep_insight_analyst",
    "explain": "auto_report_expert",
}

DEFAULT_AGENT_ALIAS = "deep_insight_analyst"


# Rule priority: explicit agent > explicit intent > keyword routing > default.
KEYWORD_ROUTE_RULES = (
    ("compare", ["对比", "同比", "环比", "差异", "排名"]),
    ("explain", ["解释", "原因", "为何", "为什么", "归因"]),
    ("query", ["多少", "查询", "统计", "数据", "指标", "情况"]),
)


def _http_error(status_code: int, code: str, message: str, detail=None) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": message,
            "detail": detail,
        },
    )


def _route_by_query(query: str) -> str:
    text = query.strip()
    for intent_name, keywords in KEYWORD_ROUTE_RULES:
        if any(keyword in text for keyword in keywords):
            return INTENT_ROUTE_MAP[intent_name]
    return DEFAULT_AGENT_ALIAS


def resolve_agent_alias(request: ChatMessageRequest) -> str:
    if request.routing_mode.value == "manual":
        if not request.agent:
            raise _http_error(400, "AGENT_REQUIRED", "Manual routing requires explicit agent", None)
        return request.agent

    if request.agent:
        return request.agent

    if request.intent is not None:
        return INTENT_ROUTE_MAP[request.intent.value]

    return _route_by_query(request.query)


def _normalize_dify_base_url(raw_base_url: str) -> str:
    """Ensure Dify API base URL ends with /v1 for service API calls."""

    normalized = raw_base_url.strip().rstrip("/")
    if not normalized.lower().endswith("/v1"):
        normalized = f"{normalized}/v1"
    return normalized


def _build_gateway_client() -> DifyGatewayClient:
    raw_base_url = os.getenv("DIFY_API_BASE_URL", "").strip()
    if not raw_base_url:
        raise RuntimeError("Missing required env var: DIFY_API_BASE_URL")

    base_url = _normalize_dify_base_url(raw_base_url)
    timeout = int(os.getenv("DIFY_TIMEOUT", "60"))

    agents: Dict[str, DifyAgent] = {}
    missing_env_vars = []

    for alias, (display_name, env_name) in AGENT_ALIAS_TO_ENV.items():
        api_key = os.getenv(env_name, "").strip()
        if api_key:
            agents[alias] = DifyAgent(alias=alias, name=display_name, api_key=api_key)
        else:
            missing_env_vars.append(env_name)

    if missing_env_vars:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing_env_vars)}")

    return DifyGatewayClient(base_url=base_url, agents=agents, timeout=timeout)


def get_gateway_client() -> DifyGatewayClient:
    return _build_gateway_client()


def get_baidu_stt_client() -> BaiduSpeechToTextClient:
    api_key = os.getenv("BAIDU_STT_API_KEY", "").strip()
    secret_key = os.getenv("BAIDU_STT_SECRET_KEY", "").strip()
    timeout = int(os.getenv("BAIDU_STT_TIMEOUT", "30"))

    if not api_key or not secret_key:
        missing = []
        if not api_key:
            missing.append("BAIDU_STT_API_KEY")
        if not secret_key:
            missing.append("BAIDU_STT_SECRET_KEY")
        raise _http_error(500, "BAIDU_STT_CONFIG_MISSING", "Baidu STT config is missing", {"missing": missing})

    return BaiduSpeechToTextClient(api_key=api_key, secret_key=secret_key, timeout=timeout)


@router.get("/agents", response_model=AgentListResponse)
def list_agents(client: DifyGatewayClient = Depends(get_gateway_client)) -> AgentListResponse:
    agents = [AgentInfo(key=item.alias, name=item.name) for item in client.list_agents()]
    return AgentListResponse(agents=agents)


@router.get("/health")
def gateway_health(client: DifyGatewayClient = Depends(get_gateway_client)) -> dict:
    status: Dict[str, dict] = {}
    ok_count = 0

    for agent in client.list_agents():
        try:
            info = client.get_info(agent.alias)
            status[agent.alias] = {"ok": True, "name": info.get("name", agent.name)}
            ok_count += 1
        except DifyGatewayError as exc:
            status[agent.alias] = {"ok": False, "error": exc.detail or exc.message}

    return {
        "ok": ok_count == len(status),
        "base_url": client.base_url,
        "agents": status,
    }


@router.post("/chat")
def chat_message(request: ChatMessageRequest, client: DifyGatewayClient = Depends(get_gateway_client)):
    if request.response_mode.value != "streaming":
        raise _http_error(
            400,
            "UNSUPPORTED_RESPONSE_MODE",
            "Only streaming response_mode is supported",
            {"response_mode": request.response_mode.value},
        )

    payload = request.model_dump(exclude_none=True)
    payload["agent"] = resolve_agent_alias(request)

    available_agents = {item.alias for item in client.list_agents()}
    if payload["agent"] not in available_agents:
        raise _http_error(400, "AGENT_NOT_FOUND", "Agent alias is not configured in gateway", {"agent": payload["agent"]})

    try:
        upstream = client.open_chat_stream(payload)
        return StreamingResponse(
            final_answer_sse_iterator(upstream),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    except DifyGatewayError as exc:
        raise _http_error(exc.status_code, "DIFY_UPSTREAM_ERROR", "Dify upstream request failed", exc.detail or exc.message) from exc


@router.post("/chat/{task_id}/stop")
def stop_chat_task(
    task_id: str,
    request: StopTaskRequest,
    agent: str,
    client: DifyGatewayClient = Depends(get_gateway_client),
):
    try:
        return client.stop_task(agent_alias=agent, task_id=task_id, user=request.user)
    except DifyGatewayError as exc:
        raise _http_error(exc.status_code, "DIFY_UPSTREAM_ERROR", "Failed to stop upstream task", exc.detail or exc.message) from exc


@router.post("/audio-to-text", response_class=PlainTextResponse)
async def audio_to_text(
    user: str = Form(...),
    file: UploadFile = File(...),
    stt_client: BaiduSpeechToTextClient = Depends(get_baidu_stt_client),
):
    try:
        file_content = await file.read()
        text = stt_client.recognize(
            file_name=file.filename or "audio.pcm",
            file_content=file_content,
            cuid=user,
            content_type=file.content_type,
        )
        return PlainTextResponse(text)
    except BaiduSpeechToTextError as exc:
        raise _http_error(exc.status_code, "BAIDU_STT_ERROR", "Baidu speech-to-text request failed", exc.detail or exc.message) from exc

