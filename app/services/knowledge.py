from __future__ import annotations

import json
import mimetypes
import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request


class KnowledgeError(Exception):
    """Base exception for knowledge API client."""


class KnowledgeTransportError(KnowledgeError):
    """Raised when network/timeout transport errors occur."""


@dataclass
class KnowledgeApiError(KnowledgeError):
    """Raised when server returns non-2xx status code."""

    status_code: int
    message: str
    response: Any
    method: Optional[str] = None
    path: Optional[str] = None

    def __str__(self) -> str:
        request_part = ""
        if self.method and self.path:
            request_part = f" [{self.method.upper()} {self.path}]"

        response_part = ""
        if self.response is not None:
            response_text = str(self.response)
            if len(response_text) > 240:
                response_text = response_text[:240] + "..."
            response_part = f"; response={response_text}"

        return f"Knowledge API error {self.status_code}: {self.message}{request_part}{response_part}"


class _SimpleResponse:
    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text

    def json(self) -> Any:
        if not self.text:
            return None
        return json.loads(self.text)


class _UrllibSession:
    """Small adapter to provide requests-like interface using urllib."""

    @staticmethod
    def _encode_multipart(data: Optional[Dict[str, Any]], files: Dict[str, Any]) -> tuple[bytes, str]:
        boundary = f"----KnowledgeBoundary{uuid.uuid4().hex}"
        chunks: list[bytes] = []

        for key, value in (data or {}).items():
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
        body = b"".join(chunks)
        content_type = f"multipart/form-data; boundary={boundary}"
        return body, content_type

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> _SimpleResponse:
        final_headers = dict(headers or {})

        if params:
            query = urllib_parse.urlencode(params, doseq=True)
            url = f"{url}{'&' if '?' in url else '?'}{query}"

        request_body: Optional[bytes] = None
        if files:
            request_body, content_type = self._encode_multipart(data, files)
            final_headers["Content-Type"] = content_type
        elif json_data is not None:
            request_body = json.dumps(json_data).encode("utf-8")
            final_headers["Content-Type"] = "application/json"

        req = urllib_request.Request(url=url, data=request_body, headers=final_headers, method=method.upper())

        try:
            with urllib_request.urlopen(req, timeout=timeout) as resp:
                text = resp.read().decode("utf-8")
                return _SimpleResponse(status_code=resp.getcode(), text=text)
        except urllib_error.HTTPError as exc:
            body = exc.read().decode("utf-8") if exc.fp else ""
            return _SimpleResponse(status_code=exc.code, text=body)
        except (urllib_error.URLError, TimeoutError) as exc:
            raise KnowledgeTransportError(str(exc)) from exc


class knowledge:
    """Dify knowledge API wrapper based on dify请求.md defined endpoints."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 30,
        session: Optional[Any] = None,
    ) -> None:
        """初始化知识库客户端。

        Args:
            base_url: Dify API 基础地址，例如 ``http://127.0.0.1:5001/v1``。
            api_key: Dify 访问密钥（Bearer Token）。
            timeout: 请求超时时间（秒）。
            session: 可注入的 HTTP 会话对象，需实现 ``request(...)``。

        Returns:
            None

        Example:
            #>>> client = knowledge("http://127.0.0.1:5001/v1", "your_api_key")
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session = session or _UrllibSession()

    def _headers(self) -> Dict[str, str]:
        """构建通用请求头。

        Returns:
            包含 ``Authorization`` 与 ``Accept`` 的请求头字典。

        Example:
            #>>> client._headers()["Authorization"].startswith("Bearer ")
            True
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

    def _url(self, path: str) -> str:
        """拼接完整请求地址。

        Args:
            path: 接口相对路径，例如 ``/datasets``。

        Returns:
            完整 URL 字符串。

        Example:
            #>>> client._url("/datasets")
            'http://127.0.0.1:5001/v1/datasets'
        """
        return f"{self.base_url}/{path.lstrip('/')}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """统一发送请求并处理响应。

        Args:
            method: HTTP 方法，如 ``GET``/``POST``/``DELETE``。
            path: 接口路径（不含 base_url）。
            params: URL 查询参数。
            json_body: JSON 请求体。
            data: 表单字段（multipart 时使用）。
            files: 文件字段（multipart 时使用）。

        Returns:
            解析后的 JSON（``dict``/``list``），
            若响应为 204 或空体则返回 ``None``。

        Raises:
            KnowledgeApiError: HTTP 状态码 >= 400。
            KnowledgeTransportError: 网络、连接或超时错误。

        Example:
            #>>> client._request("GET", "/datasets", params={"page": 1, "limit": 20})
        """
        response = self.session.request(
            method=method,
            url=self._url(path),
            headers=self._headers(),
            params=params,
            json_data=json_body,
            data=data,
            files=files,
            timeout=self.timeout,
        )

        if response.status_code >= 400:
            error_body: Any = response.text
            try:
                error_body = response.json()
            except Exception:
                pass
            raise KnowledgeApiError(
                response.status_code,
                "request failed",
                error_body,
                method=method,
                path=path,
            )

        if response.status_code == 204 or not response.text:
            return None

        try:
            return response.json()
        except Exception:
            return {"raw": response.text}

    def _build_file_payload(self, file_path: str, file_field: str = "file") -> Dict[str, Any]:
        """将本地文件转为 multipart 上传结构。

        Args:
            file_path: 本地文件路径。
            file_field: 表单中文件字段名，默认 ``file``。

        Returns:
            形如 ``{"file": (filename, bytes, content_type)}`` 的字典。

        Example:
            #>>> payload = client._build_file_payload("./demo.txt")
            #>>> "file" in payload
            True
        """
        filename = os.path.basename(file_path)
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        with open(file_path, "rb") as file_obj:
            content = file_obj.read()
        return {file_field: (filename, content, content_type)}

    # 1 POST /datasets/{dataset_id}/document/create_by_text
    def create_document_by_text(self, dataset_id: str, payload: Dict[str, Any]) -> Any:
        """通过文本在指定知识库中新建文档。

        Args:
            dataset_id: 知识库 ID。
            payload: 请求体，例如
                ``{"name": "text", "text": "content", "indexing_technique": "high_quality"}``。

        Returns:
            Dify 返回的文档创建结果，通常包含 ``document`` 与 ``batch`` 字段。

        Example:
            #>>> client.create_document_by_text("ds_xxx", {"name": "a", "text": "hello"})
        """
        return self._request("POST", f"/datasets/{dataset_id}/document/create-by-text", json_body=payload)

    # 2 POST /datasets/{dataset_id}/document/create_by_file
    def create_document_by_file(self, dataset_id: str, file_path: str, data: Optional[Dict[str, Any]] = None) -> Any:
        """通过文件在指定知识库中新建文档。

        Args:
            dataset_id: 知识库 ID。
            file_path: 待上传文件路径。
            data: 附加配置，会序列化到 multipart 的 ``data`` 字段，
                例如 ``{"indexing_technique": "high_quality"}``。

        Returns:
            Dify 返回的文档创建结果（含 ``document``、``batch``）。

        Example:
            #>>> client.create_document_by_file("ds_xxx", "./demo.txt", {"indexing_technique": "high_quality"})
        """
        form_data = {"data": json.dumps(data or {})}
        files = self._build_file_payload(file_path)
        return self._request("POST", f"/datasets/{dataset_id}/document/create-by-file", data=form_data, files=files)

    # 3 POST /datasets
    def create_dataset(self, payload: Dict[str, Any]) -> Any:
        """创建空知识库。

        Args:
            payload: 请求体，例如 ``{"name": "知识库名称"}``。

        Returns:
            新建知识库详情（通常含 ``id``、``name`` 等字段）。

        Example:
            #>>> client.create_dataset({"name": "demo-kb"})
        """
        return self._request("POST", "/datasets", json_body=payload)

    # 4 GET /datasets
    def list_datasets(self, page: Optional[int] = None, limit: Optional[int] = None) -> Any:
        """查询知识库列表。

        Args:
            page: 页码（可选）。
            limit: 每页条数（可选）。

        Returns:
            列表结果，通常包含 ``data``、``has_more``、``total``、``page``。

        Example:
            #>>> client.list_datasets(page=1, limit=20)
        """
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._request("GET", "/datasets", params=params or None)

    # 5 DELETE /datasets/{dataset_id}
    def delete_dataset(self, dataset_id: str) -> Any:
        """删除指定知识库。

        Args:
            dataset_id: 知识库 ID。

        Returns:
            接口 204 时返回 ``None``。

        Example:
            #>>> client.delete_dataset("ds_xxx")
        """
        return self._request("DELETE", f"/datasets/{dataset_id}")

    # 6 POST /datasets/{dataset_id}/documents/{document_id}/update-by-text
    def update_document_by_text(self, dataset_id: str, document_id: str, payload: Dict[str, Any]) -> Any:
        """通过文本更新知识库中的文档内容。

        Args:
            dataset_id: 知识库 ID。
            document_id: 文档 ID。
            payload: 请求体，例如 ``{"name": "new", "text": "new content"}``。

        Returns:
            更新结果，通常包含 ``document`` 与 ``batch``。

        Example:
           # >>> client.update_document_by_text("ds_xxx", "doc_xxx", {"name": "a", "text": "b"})
        """
        return self._request(
            "POST",
            f"/datasets/{dataset_id}/documents/{document_id}/update-by-text",
            json_body=payload,
        )

    # 7 POST /datasets/{dataset_id}/documents/{document_id}/update-by-file
    def update_document_by_file(
        self,
        dataset_id: str,
        document_id: str,
        file_path: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """通过文件更新知识库中的文档。

        Args:
            dataset_id: 知识库 ID。
            document_id: 文档 ID。
            file_path: 新文件路径。
            data: 附加配置，会放入 multipart ``data`` 字段。

        Returns:
            更新结果，通常包含 ``document`` 与 ``batch``。

        Example:
            #>>> client.update_document_by_file("ds_xxx", "doc_xxx", "./new.txt", {"name": "new"})
        """
        form_data = {"data": json.dumps(data or {})}
        files = self._build_file_payload(file_path)
        return self._request(
            "POST",
            f"/datasets/{dataset_id}/documents/{document_id}/update-by-file",
            data=form_data,
            files=files,
        )

    # 8 GET /datasets/{dataset_id}/documents/{batch}/indexing-status
    def get_document_indexing_status(self, dataset_id: str, batch: str) -> Any:
        """查询批次文档的向量化/嵌入进度。

        Args:
            dataset_id: 知识库 ID。
            batch: 批次号（创建/更新文档返回的 ``batch``）。

        Returns:
            进度结果，通常含 ``data`` 列表（状态、完成段数等）。

        Example:
            #>>> client.get_document_indexing_status("ds_xxx", "batch_xxx")
        """
        return self._request("GET", f"/datasets/{dataset_id}/documents/{batch}/indexing-status")

    # 9 DELETE /datasets/{dataset_id}/documents/{document_id}
    def delete_document(self, dataset_id: str, document_id: str) -> Any:
        """删除知识库中的指定文档。

        Args:
            dataset_id: 知识库 ID。
            document_id: 文档 ID。

        Returns:
            删除结果，常见为 ``{"result": "success"}``。

        Example:
            #>>> client.delete_document("ds_xxx", "doc_xxx")
        """
        return self._request("DELETE", f"/datasets/{dataset_id}/documents/{document_id}")

    # 10 GET /datasets/{dataset_id}/documents
    def list_documents(self, dataset_id: str, page: Optional[int] = None, limit: Optional[int] = None) -> Any:
        """查询知识库下的文档列表。

        Args:
            dataset_id: 知识库 ID。
            page: 页码（可选）。
            limit: 每页条数（可选）。

        Returns:
            文档列表结果，通常包含 ``data``、``total``、``has_more``。

        Example:
            #>>> client.list_documents("ds_xxx", page=1, limit=20)
        """
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._request("GET", f"/datasets/{dataset_id}/documents", params=params or None)

    # 11 POST /datasets/{dataset_id}/documents/{document_id}/segments
    def create_segments(self, dataset_id: str, document_id: str, payload: Dict[str, Any]) -> Any:
        """为文档新增分段。

        Args:
            dataset_id: 知识库 ID。
            document_id: 文档 ID。
            payload: 请求体，例如
                ``{"segments": [{"content": "...", "answer": "...", "keywords": ["k"]}]}``。

        Returns:
            新增分段结果，通常包含 ``data`` 与 ``doc_form``。

        Example:
            #>>> client.create_segments("ds_xxx", "doc_xxx", {"segments": [{"content": "c"}]})
        """
        return self._request("POST", f"/datasets/{dataset_id}/documents/{document_id}/segments", json_body=payload)

    # 12 GET /datasets/{dataset_id}/documents/{document_id}/segments
    def list_segments(self, dataset_id: str, document_id: str) -> Any:
        """查询文档分段列表。

        Args:
            dataset_id: 知识库 ID。
            document_id: 文档 ID。

        Returns:
            分段列表结果，通常包含 ``data`` 与 ``doc_form``。

        Example:
            #>>> client.list_segments("ds_xxx", "doc_xxx")
        """
        return self._request("GET", f"/datasets/{dataset_id}/documents/{document_id}/segments")

    # 13 DELETE /datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}
    def delete_segment(self, dataset_id: str, document_id: str, segment_id: str) -> Any:
        """删除指定文档分段。

        Args:
            dataset_id: 知识库 ID。
            document_id: 文档 ID。
            segment_id: 分段 ID。

        Returns:
            删除结果，常见为 ``{"result": "success"}``。

        Example:
            #>>> client.delete_segment("ds_xxx", "doc_xxx", "seg_xxx")
        """
        return self._request("DELETE", f"/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}")

    # 14 POST /datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}
    def update_segment(self, dataset_id: str, document_id: str, segment_id: str, payload: Dict[str, Any]) -> Any:
        """更新指定文档分段。

        Args:
            dataset_id: 知识库 ID。
            document_id: 文档 ID。
            segment_id: 分段 ID。
            payload: 请求体，例如
                ``{"segment": {"content": "...", "answer": "...", "keywords": ["a"], "enabled": False}}``。

        Returns:
            更新结果，通常包含 ``data`` 与 ``doc_form``。

        Example:
            #>>> client.update_segment("ds_xxx", "doc_xxx", "seg_xxx", {"segment": {"content": "new"}})
        """
        return self._request(
            "POST",
            f"/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}",
            json_body=payload,
        )

    # 15 POST /datasets/{dataset_id}/retrieve
    def retrieve(self, dataset_id: str, payload: Dict[str, Any]) -> Any:
        """在知识库中执行检索。

        Args:
            dataset_id: 知识库 ID。
            payload: 检索请求体，例如
                ``{"query": "test", "retrieval_model": {"search_method": "keyword_search", "top_k": 1}}``。

        Returns:
            检索结果，通常包含 ``query`` 与 ``records``。

        Example:
            #>>> client.retrieve("ds_xxx", {"query": "安装说明", "retrieval_model": {"search_method": "keyword_search"}})
        """
        payload_to_send = dict(payload)
        if "external_retrieval_model" not in payload_to_send and "retrieval_model" in payload_to_send:
            payload_to_send["external_retrieval_model"] = payload_to_send.pop("retrieval_model")

        return self._request("POST", f"/datasets/{dataset_id}/retrieve", json_body=payload_to_send)

    # 16 POST /datasets/pipeline/file-upload
    def upload_pipeline_file(self, file_path: str) -> Any:
        """上传 Pipeline 文件，返回文件 ID 供后续流程引用。

        Args:
            file_path: 本地文件路径。

        Returns:
            上传结果，通常包含 ``id``、``name``、``size``、``mime_type`` 等字段。

        Example:
            #>>> client.upload_pipeline_file("./demo.pdf")
        """
        files = self._build_file_payload(file_path)
        return self._request("POST", "/datasets/pipeline/file-upload", files=files)


class Knowledge(knowledge):
    """Alias using common class naming style."""


__all__ = [
    "knowledge",
    "Knowledge",
    "KnowledgeError",
    "KnowledgeTransportError",
    "KnowledgeApiError",
]


if __name__ == "__main__":
    base_url = os.getenv("DIFY_BASE_URL", "http://123.207.72.88:8088/v1")
    api_key = os.getenv("DIFY_API_KEY","dataset-c6isoIYCm9MhwW9eOO25aKGF")
    dataset_id = os.getenv("DIFY_DATASET_ID","216e764b-b879-48b7-be10-ddc0b192394b")
    kn = Knowledge(base_url=base_url, api_key=api_key)
    re = knowledge.list_datasets(kn, page=1, limit=20)
    r2 = knowledge.list_documents(kn, dataset_id, page=1, limit=20)

    r4 = knowledge.create_document_by_file(kn, dataset_id, os.path.dirname(__file__)+"//test.txt")
    print(re)