import unittest

from fastapi.testclient import TestClient

from app.api.gateway import _normalize_dify_base_url, get_baidu_stt_client, get_gateway_client
from app.services.baidu_stt import BaiduSpeechToTextError
from main import app


class _FakeAgent:
    def __init__(self, alias, name):
        self.alias = alias
        self.name = name


class _FakeStreamResponse:
    def __init__(self, lines):
        self._lines = list(lines)

    def readline(self):
        if not self._lines:
            return b""
        return self._lines.pop(0)

    def close(self):
        return None


class _FakeGatewayClient:
    base_url = "http://mock/v1"

    def __init__(self):
        self.last_stream_payload = None

    def list_agents(self):
        return [
            _FakeAgent("annual_report_analyst", "A"),
            _FakeAgent("deep_insight_analyst", "B"),
            _FakeAgent("auto_report_expert", "C"),
        ]

    def get_info(self, agent_alias):
        return {"name": f"{agent_alias}-ok"}

    def chat_messages(self, payload):
        return {"event": "message", "answer": "ok", "payload": payload}

    def open_chat_stream(self, payload):
        self.last_stream_payload = payload
        lines = [
            b'data: {"event":"message","answer":"hello"}\n\n',
            b'data: {"event":"message_end"}\n\n',
        ]
        return _FakeStreamResponse(lines)

    def stop_task(self, agent_alias, task_id, user):
        return {"result": "success", "agent": agent_alias, "task_id": task_id, "user": user}


class _FakeBaiduSttClient:
    def __init__(self):
        self.last_call = None
        self.error = None

    def recognize(self, *, file_name, file_content, cuid, content_type=None, rate=None, channel=None):
        if self.error is not None:
            raise self.error
        self.last_call = {
            "file_name": file_name,
            "file_content": file_content,
            "cuid": cuid,
            "content_type": content_type,
            "rate": rate,
            "channel": channel,
        }
        return "hello"


class GatewayApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake_client = _FakeGatewayClient()
        cls.fake_baidu_stt_client = _FakeBaiduSttClient()
        app.dependency_overrides[get_gateway_client] = lambda: cls.fake_client
        app.dependency_overrides[get_baidu_stt_client] = lambda: cls.fake_baidu_stt_client
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()

    def test_list_agents(self):
        response = self.client.get("/api/v1/gateway/agents")
        self.assertEqual(200, response.status_code)
        data = response.json()
        self.assertEqual(3, len(data["agents"]))

    def test_blocking_chat_is_rejected(self):
        response = self.client.post(
            "/api/v1/gateway/chat",
            json={
                "agent": "annual_report_analyst",
                "query": "test",
                "user": "u-1",
                "response_mode": "blocking",
            },
        )
        self.assertEqual(400, response.status_code)
        body = response.json()
        self.assertEqual("UNSUPPORTED_RESPONSE_MODE", body["code"])

    def test_auto_route_by_intent(self):
        response = self.client.post(
            "/api/v1/gateway/chat",
            json={
                "intent": "compare",
                "query": "请帮我做同比对比",
                "user": "u-1",
                "response_mode": "streaming",
            },
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("deep_insight_analyst", self.fake_client.last_stream_payload["agent"])

    def test_auto_route_by_query_keyword(self):
        response = self.client.post(
            "/api/v1/gateway/chat",
            json={
                "query": "请解释一下这个指标下降原因",
                "user": "u-1",
                "response_mode": "streaming",
            },
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("auto_report_expert", self.fake_client.last_stream_payload["agent"])

    def test_streaming_chat(self):
        response = self.client.post(
            "/api/v1/gateway/chat",
            json={
                "query": "test",
                "user": "u-1",
                "response_mode": "streaming",
            },
        )
        self.assertEqual(200, response.status_code)
        self.assertIn("text/event-stream", response.headers.get("content-type", ""))
        self.assertIn('"event": "final"', response.text)
        self.assertIn('"answer": "hello"', response.text)

    def test_stop_task(self):
        response = self.client.post(
            "/api/v1/gateway/chat/task-1/stop?agent=auto_report_expert",
            json={"user": "u-2"},
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("success", response.json()["result"])

    def test_unified_error_code_on_validation(self):
        response = self.client.post(
            "/api/v1/gateway/chat",
            json={"user": "u-2", "response_mode": "streaming"},
            headers={"X-Request-Id": "req-1"},
        )
        self.assertEqual(422, response.status_code)
        body = response.json()
        self.assertEqual("VALIDATION_ERROR", body["code"])
        self.assertEqual("req-1", body["request_id"])

    def test_manual_routing_requires_agent(self):
        response = self.client.post(
            "/api/v1/gateway/chat",
            json={
                "routing_mode": "manual",
                "query": "test",
                "user": "u-1",
                "response_mode": "streaming",
            },
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual("AGENT_REQUIRED", response.json()["code"])

    def test_manual_routing_with_agent(self):
        response = self.client.post(
            "/api/v1/gateway/chat",
            json={
                "routing_mode": "manual",
                "agent": "auto_report_expert",
                "query": "请解释",
                "user": "u-1",
                "response_mode": "streaming",
            },
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("auto_report_expert", self.fake_client.last_stream_payload["agent"])

    def test_normalize_base_url_appends_v1(self):
        self.assertEqual("http://123.207.72.88:8088/v1", _normalize_dify_base_url("http://123.207.72.88:8088/"))
        self.assertEqual("http://123.207.72.88:8088/v1", _normalize_dify_base_url("http://123.207.72.88:8088/v1"))

    def test_audio_to_text(self):
        response = self.client.post(
            "/api/v1/gateway/audio-to-text",
            files={"file": ("sample.wav", b"fake-audio-bytes", "audio/wav")},
            data={"user": "u-100"},
        )
        self.assertEqual(200, response.status_code)
        self.assertIn("text/plain", response.headers.get("content-type", ""))
        self.assertEqual("hello", response.text)
        self.assertEqual("sample.wav", self.fake_baidu_stt_client.last_call["file_name"])
        self.assertEqual(b"fake-audio-bytes", self.fake_baidu_stt_client.last_call["file_content"])
        self.assertEqual("u-100", self.fake_baidu_stt_client.last_call["cuid"])
        self.assertEqual("audio/wav", self.fake_baidu_stt_client.last_call["content_type"])

    def test_audio_to_text_baidu_error(self):
        self.fake_baidu_stt_client.error = BaiduSpeechToTextError(
            400,
            "baidu stt request failed",
            {"err_no": 3301, "err_msg": "audio quality error"},
        )
        response = self.client.post(
            "/api/v1/gateway/audio-to-text",
            files={"file": ("sample.wav", b"fake-audio-bytes", "audio/wav")},
            data={"user": "u-100"},
        )
        self.assertEqual(400, response.status_code)
        body = response.json()
        self.assertEqual("BAIDU_STT_ERROR", body["code"])
        self.fake_baidu_stt_client.error = None


if __name__ == "__main__":
    unittest.main()
