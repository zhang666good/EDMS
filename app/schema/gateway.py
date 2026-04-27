from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ResponseMode(str, Enum):
    """Supported Dify response modes."""

    blocking = "blocking"
    streaming = "streaming"


class IntentType(str, Enum):
    """Business intent used for auto routing."""

    query = "query"
    compare = "compare"
    explain = "explain"


class RoutingMode(str, Enum):
    """Gateway routing mode for agent selection."""

    auto = "auto"
    manual = "manual"


class ChatMessageRequest(BaseModel):
    """Gateway request body for Dify /chat-messages."""

    agent: Optional[str] = Field(default=None, description="Optional explicit agent alias.")
    intent: Optional[IntentType] = Field(default=None, description="Optional business intent for auto routing.")
    routing_mode: RoutingMode = Field(default=RoutingMode.auto, description="`manual` requires explicit `agent`.")
    query: str = Field(..., description="User input text.")
    user: str = Field(..., description="Unique end-user id inside one app.")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Dify inputs variables.")
    response_mode: ResponseMode = Field(default=ResponseMode.streaming)
    conversation_id: Optional[str] = Field(default=None)
    files: Optional[List[Dict[str, Any]]] = Field(default=None)
    auto_generate_name: Optional[bool] = Field(default=None)
    workflow_id: Optional[str] = Field(default=None)
    trace_id: Optional[str] = Field(default=None)


class StopTaskRequest(BaseModel):
    """Request body for stopping a Dify streaming task."""

    user: str = Field(..., description="Must be same user id used in chat request.")


class AgentInfo(BaseModel):
    """Public agent metadata returned by gateway."""

    key: str
    name: str


class AgentListResponse(BaseModel):
    """Agent list response model."""

    agents: List[AgentInfo]


class ErrorResponse(BaseModel):
    """Unified error response model for business-side handling."""

    code: str
    message: str
    detail: Any = None
    request_id: Optional[str] = None

