import os
import tempfile
import unittest

from app.services.knowledge import Knowledge, KnowledgeApiError, KnowledgeTransportError, knowledge


class _FakeResponse:
    def __init__(self, status_code=200, payload=None, text=None):
        self.status_code = status_code
        self._payload = payload
        if text is None:
            import json as _json

            text = "" if payload is None else _json.dumps(payload)
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class _FakeSession:
    def __init__(self, response=None, error=None):
        self.response = response or _FakeResponse(payload={"ok": True})
        self.error = error
        self.calls = []

    def request(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


class KnowledgeClientTests(unittest.TestCase):
    def test_create_document_by_text_path_and_body(self):
        session = _FakeSession()
        client = knowledge(base_url="http://localhost:5001/v1", api_key="k", session=session)

        result = client.create_document_by_text("ds_1", {"name": "doc", "text": "abc"})

        self.assertEqual({"ok": True}, result)
        last_call = session.calls[-1]
        self.assertEqual("POST", last_call["method"])
        self.assertTrue(last_call["url"].endswith("/datasets/ds_1/document/create-by-text"))
        self.assertEqual({"name": "doc", "text": "abc"}, last_call["json_data"])

    def test_create_document_by_file_uses_multipart_data(self):
        session = _FakeSession()
        client = knowledge(base_url="http://localhost:5001/v1", api_key="k", session=session)

        file_handle, file_path = tempfile.mkstemp(suffix=".txt")
        os.close(file_handle)
        try:
            with open(file_path, "wb") as f:
                f.write(b"hello")

            client.create_document_by_file("ds_2", file_path, {"indexing_technique": "high_quality"})

            last_call = session.calls[-1]
            self.assertIn("files", last_call)
            self.assertIn("file", last_call["files"])
            self.assertIn("data", last_call)
            self.assertIn("data", last_call["data"])
            self.assertTrue(last_call["url"].endswith("/datasets/ds_2/document/create-by-file"))
        finally:
            os.remove(file_path)

    def test_retrieve_maps_legacy_retrieval_model_field(self):
        session = _FakeSession()
        client = knowledge(base_url="http://localhost:5001/v1", api_key="k", session=session)

        client.retrieve("ds_x", {"query": "q", "retrieval_model": {"search_method": "keyword_search"}})

        last_call = session.calls[-1]
        self.assertIn("external_retrieval_model", last_call["json_data"])
        self.assertNotIn("retrieval_model", last_call["json_data"])

    def test_upload_pipeline_file_endpoint(self):
        session = _FakeSession()
        client = knowledge(base_url="http://localhost:5001/v1", api_key="k", session=session)

        file_handle, file_path = tempfile.mkstemp(suffix=".txt")
        os.close(file_handle)
        try:
            with open(file_path, "wb") as f:
                f.write(b"hello")

            client.upload_pipeline_file(file_path)

            last_call = session.calls[-1]
            self.assertEqual("POST", last_call["method"])
            self.assertTrue(last_call["url"].endswith("/datasets/pipeline/file-upload"))
            self.assertIn("file", last_call["files"])
        finally:
            os.remove(file_path)

    def test_list_datasets_uses_query_params(self):
        session = _FakeSession()
        client = knowledge(base_url="http://localhost:5001/v1", api_key="k", session=session)

        client.list_datasets(page=2, limit=50)

        last_call = session.calls[-1]
        self.assertEqual({"page": 2, "limit": 50}, last_call["params"])

    def test_204_returns_none(self):
        session = _FakeSession(response=_FakeResponse(status_code=204, text=""))
        client = knowledge(base_url="http://localhost:5001/v1", api_key="k", session=session)

        result = client.delete_dataset("ds_3")

        self.assertIsNone(result)

    def test_http_error_raises_knowledge_api_error(self):
        session = _FakeSession(response=_FakeResponse(status_code=404, payload={"message": "not found"}))
        client = knowledge(base_url="http://localhost:5001/v1", api_key="k", session=session)

        with self.assertRaises(KnowledgeApiError):
            client.list_documents("ds_missing")

    def test_transport_error_bubbles_from_session(self):
        session = _FakeSession(error=KnowledgeTransportError("timeout"))
        client = knowledge(base_url="http://localhost:5001/v1", api_key="k", session=session)

        with self.assertRaises(KnowledgeTransportError):
            client.list_segments("ds", "doc")

    def test_uppercase_alias_available(self):
        self.assertTrue(issubclass(Knowledge, knowledge))


if __name__ == "__main__":
    unittest.main()

