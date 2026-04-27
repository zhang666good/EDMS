from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Iterator, Mapping, Optional
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request


class DifyGatewayError(Exception):
    """Raised when the gateway fails to call Dify API."""

    def __init__(self, status_code: int, message: str, detail: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.detail = detail


@dataclass(frozen=True)
class DifyAgent:
    """One Dify app binding in gateway."""

    alias: str
    name: str
    api_key: str


class DifyGatewayClient:
    """Minimal Dify app gateway client based on standard library."""

    def __init__(self, base_url: str, agents: Mapping[str, DifyAgent], timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.agents = dict(agents)
        self.timeout = timeout

    def list_agents(self) -> list[DifyAgent]:
        return list(self.agents.values())

    def _get_agent(self, alias: str) -> DifyAgent:
        agent = self.agents.get(alias)
        if not agent:
            raise DifyGatewayError(404, f"unknown agent: {alias}")
        return agent

    @staticmethod
    def _parse_response_body(text: str) -> Any:
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception:
            return {"raw": text}

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        api_key: str,
        json_body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            query = urllib_parse.urlencode(params, doseq=True)
            url = f"{url}?{query}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)

        data = None
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")

        req = urllib_request.Request(url=url, data=data, headers=headers, method=method.upper())

        try:
            with urllib_request.urlopen(req, timeout=self.timeout) as resp:
                text = resp.read().decode("utf-8")
                return self._parse_response_body(text)
        except urllib_error.HTTPError as exc:
            text = exc.read().decode("utf-8") if exc.fp else ""
            detail = self._parse_response_body(text)
            raise DifyGatewayError(exc.code, "dify request failed", detail) from exc
        except urllib_error.URLError as exc:
            raise DifyGatewayError(502, "dify upstream unavailable", str(exc)) from exc

    @staticmethod
    def _encode_multipart(fields: Mapping[str, Any], files: Mapping[str, tuple[str, bytes, str]]) -> tuple[bytes, str]:
        boundary = f"----DifyGatewayBoundary{uuid.uuid4().hex}"
        chunks: list[bytes] = []

        for key, value in fields.items():
            chunks.extend(
                [
                    f"--{boundary}\r\n".encode("utf-8"),
                    f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"),
                    str(value).encode("utf-8"),
                    b"\r\n",
                ]
            )

        for field_name, file_info in files.items():
            filename, content, content_type = file_info
            chunks.extend(
                [
                    f"--{boundary}\r\n".encode("utf-8"),
                    (
                        f'Content-Disposition: form-data; name="{field_name}"; '
                        f'filename="{filename}"\r\n'
                    ).encode("utf-8"),
                    f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
                    content,
                    b"\r\n",
                ]
            )

        chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
        return b"".join(chunks), f"multipart/form-data; boundary={boundary}"

    def _request_multipart(
        self,
        method: str,
        path: str,
        *,
        api_key: str,
        fields: Mapping[str, Any],
        files: Mapping[str, tuple[str, bytes, str]],
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        body, content_type = self._encode_multipart(fields, files)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": content_type,
        }
        if extra_headers:
            headers.update(extra_headers)

        req = urllib_request.Request(url=url, data=body, headers=headers, method=method.upper())
        try:
            with urllib_request.urlopen(req, timeout=self.timeout) as resp:
                text = resp.read().decode("utf-8")
                return self._parse_response_body(text)
        except urllib_error.HTTPError as exc:
            text = exc.read().decode("utf-8") if exc.fp else ""
            detail = self._parse_response_body(text)
            raise DifyGatewayError(exc.code, "dify request failed", detail) from exc
        except urllib_error.URLError as exc:
            raise DifyGatewayError(502, "dify upstream unavailable", str(exc)) from exc

    def chat_messages(self, payload: Dict[str, Any]) -> Any:
        agent = self._get_agent(str(payload["agent"]))
        body = dict(payload)
        body.pop("agent", None)

        trace_id = body.get("trace_id")
        headers = {"X-Trace-Id": str(trace_id)} if trace_id else None
        return self._request_json(
            "POST",
            "/chat-messages",
            api_key=agent.api_key,
            json_body=body,
            extra_headers=headers,
        )

    def open_chat_stream(self, payload: Dict[str, Any]):
        agent = self._get_agent(str(payload["agent"]))
        body = dict(payload)
        body.pop("agent", None)

        url = f"{self.base_url}/chat-messages"
        headers = {
            "Authorization": f"Bearer {agent.api_key}",
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
        trace_id = body.get("trace_id")
        if trace_id:
            headers["X-Trace-Id"] = str(trace_id)

        req = urllib_request.Request(
            url=url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            return urllib_request.urlopen(req, timeout=self.timeout)
        except urllib_error.HTTPError as exc:
            text = exc.read().decode("utf-8") if exc.fp else ""
            detail = self._parse_response_body(text)
            raise DifyGatewayError(exc.code, "dify streaming request failed", detail) from exc
        except urllib_error.URLError as exc:
            raise DifyGatewayError(502, "dify upstream unavailable", str(exc)) from exc

    def stop_task(self, agent_alias: str, task_id: str, user: str) -> Any:
        agent = self._get_agent(agent_alias)
        return self._request_json(
            "POST",
            f"/chat-messages/{task_id}/stop",
            api_key=agent.api_key,
            json_body={"user": user},
        )

    def get_info(self, agent_alias: str) -> Any:
        agent = self._get_agent(agent_alias)
        return self._request_json("GET", "/info", api_key=agent.api_key)

    def audio_to_text(
        self,
        agent_alias: str,
        *,
        user: str,
        file_name: str,
        file_content: bytes,
        content_type: str,
    ) -> Any:
        agent = self._get_agent(agent_alias)
        return self._request_multipart(
            "POST",
            "/audio-to-text",
            api_key=agent.api_key,
            fields={"user": user},
            files={"file": (file_name, file_content, content_type)},
        )


def sse_line_iterator(stream_response) -> Iterator[bytes]:
    """Yield SSE stream bytes from upstream response line by line."""

    try:
        while True:
            line = stream_response.readline()
            if not line:
                break
            yield line
    finally:
        stream_response.close()


def final_answer_sse_iterator(stream_response) -> Iterator[bytes]:
    """Emit only one final SSE event instead of forwarding intermediate events."""

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
                chunk = payload.get("answer") or ""
                if chunk:
                    answer_chunks.append(str(chunk))
                continue

            if event == "agent_thought":
                thought = payload.get("thought") or ""
                if thought:
                    thought_fallback = str(thought)
                continue

            if event == "error":
                # Preserve upstream stream-error as-is for frontend handling.
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")
                return

            if event == "message_end":
                final_answer = "".join(answer_chunks).strip()
                if not final_answer:
                    final_answer = thought_fallback.strip()

                final_payload = {
                    "event": "final",
                    "conversation_id": payload.get("conversation_id"),
                    "message_id": payload.get("message_id"),
                    "task_id": payload.get("task_id"),
                    "created_at": payload.get("created_at"),
                    "answer": final_answer,
                    "metadata": payload.get("metadata"),
                }
                yield f"data: {json.dumps(final_payload, ensure_ascii=False)}\n\n".encode("utf-8")
                return
    finally:
        stream_response.close()
