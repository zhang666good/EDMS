import requests
import time
import os
#该文件 qwen AI 辅助生成修改，#qwen AI 辅助封装，AI辅助生成：qwen3

MINERU_TOKEN = os.getenv("MINERU_TOKEN", "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI3NjEwOTg5NSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc3NjQyNTM5NywiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiMTg2OTY4MTQxNzUiLCJvcGVuSWQiOm51bGwsInV1aWQiOiIyNWYyYmZjMy0yZWY4LTQzYjUtOTYwYi0xZmYxZTU2YTk2ODciLCJlbWFpbCI6IiIsImV4cCI6MTc4NDIwMTM5N30.dXqoaatV32b2-LoJLoyiQtkhIRjPDn1Guo6VaPmCq9LwLGRjQlbxCTr5kmj78EUd4If8gQSREYGNgKZzSO0hTA")
API_BASE = "https://mineru.net/api/v4"


def parse_by_url_v4(url, model_version="vlm", language="ch", is_ocr=False, enable_formula=True, enable_table=True, data_id=None, page_ranges=None, no_cache=False, cache_tolerance=900):
    """
    使用 MinerU v4 精准解析 API，通过 URL 提交文档解析任务。
    :param url: 文件公网可访问 URL
    :param model_version: pipeline/vlm/MinerU-HTML
    :param language: 文档语言
    :param is_ocr: 是否启用 OCR
    :param enable_formula: 是否开启公式识别
    :param enable_table: 是否开启表格识别
    :param data_id: 业务自定义数据ID
    :param page_ranges: 页码范围
    :param no_cache: 是否绕过缓存
    :param cache_tolerance: 缓存容忍时间
    :return: 解析任务 task_id
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MINERU_TOKEN}"
    }
    data = {
        "url": url,
        "model_version": model_version,
        "language": language,
        "is_ocr": is_ocr,
        "enable_formula": enable_formula,
        "enable_table": enable_table,
        "no_cache": no_cache,
        "cache_tolerance": cache_tolerance
    }
    if data_id:
        data["data_id"] = data_id
    if page_ranges:
        data["page_ranges"] = page_ranges
    resp = requests.post(f"{API_BASE}/extract/task", headers=headers, json=data)
    result = resp.json()
    if result["code"] != 0:
        print(f"提交失败: {result['msg']}")
        return None
    task_id = result["data"]["task_id"]
    print(f"任务已提交, task_id: {task_id}")
    return task_id


def poll_result_v4(task_id, timeout=300, interval=3):
    """
    轮询查询 MinerU v4 解析任务结果。
    :param task_id: 解析任务ID
    :param timeout: 最大等待时间（秒）
    :param interval: 轮询间隔（秒）
    :return: 解析状态和结果字典
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MINERU_TOKEN}"
    }
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(f"{API_BASE}/extract/task/{task_id}", headers=headers)
        result = resp.json()
        state = result["data"]["state"]
        elapsed = int(time.time() - start)
        if state == "done":
            print(f"[{elapsed}s] 解析完成, 下载包: {result['data'].get('full_zip_url')}")
            return result["data"]
        if state == "failed":
            print(f"[{elapsed}s] 解析失败: {result['data'].get('err_msg', '未知错误')}")
            return result["data"]
        print(f"[{elapsed}s] 状态: {state}...")
        time.sleep(interval)
    print(f"轮询超时 ({timeout}s)，请稍后手动查询 task_id: {task_id}")
    return None


def parse_by_file_v4(file_path, model_version="vlm", language="ch", is_ocr=False, enable_formula=True, enable_table=True, data_id=None, page_ranges=None, no_cache=False, cache_tolerance=900):
    """
    使用 MinerU v4 精准解析 API，本地文件上传解析。
    :param file_path: 本地文件路径
    :param model_version: pipeline/vlm/MinerU-HTML
    :param language: 文档语言
    :param is_ocr: 是否启用 OCR
    :param enable_formula: 是否开启公式识别
    :param enable_table: 是否开启表格识别
    :param data_id: 业务自定义数据ID
    :param page_ranges: 页码范围
    :param no_cache: 是否绕过缓存
    :param cache_tolerance: 缓存容忍时间
    :return: (batch_id, file_urls) 上传批次ID和上传链接列表
    """
    import os
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MINERU_TOKEN}"
    }
    file_name = os.path.basename(file_path)
    files = [{"name": file_name}]
    if data_id:
        files[0]["data_id"] = data_id
    if page_ranges:
        files[0]["page_ranges"] = page_ranges
    data = {
        "files": files,
        "model_version": model_version,
        "language": language,
        "enable_formula": enable_formula,
        "enable_table": enable_table,
        "no_cache": no_cache,
        "cache_tolerance": cache_tolerance
    }
    if is_ocr:
        files[0]["is_ocr"] = is_ocr
    resp = requests.post(f"{API_BASE}/file-urls/batch", headers=headers, json=data)
    result = resp.json()
    if result["code"] != 0:
        print(f"上传链接申请失败: {result['msg']}")
        return None, None
    batch_id = result["data"]["batch_id"]
    file_urls = result["data"]["file_urls"]
    print(f"上传批次 batch_id: {batch_id}")
    # 上传文件
    with open(file_path, 'rb') as f:
        upload_resp = requests.put(file_urls[0], data=f)
        if upload_resp.status_code == 200:
            print(f"文件上传成功: {file_name}")
        else:
            print(f"文件上传失败: {upload_resp.status_code}")
            return batch_id, file_urls
    return batch_id, file_urls


def poll_batch_result_v4(batch_id, timeout=300, interval=3):
    """
    轮询 MinerU v4 批量解析任务结果。
    :param batch_id: 批量任务ID
    :param timeout: 最大等待时间（秒）
    :param interval: 轮询间隔（秒）
    :return: 解析状态和结果字典
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MINERU_TOKEN}"
    }
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(f"{API_BASE}/extract-results/batch/{batch_id}", headers=headers)
        result = resp.json()
        extract_result = result["data"].get("extract_result", [])
        all_done = all([item.get("state") == "done" for item in extract_result])
        elapsed = int(time.time() - start)
        if all_done:
            print(f"[{elapsed}s] 批量解析全部完成")
            return result["data"]
        if any([item.get("state") == "failed" for item in extract_result]):
            print(f"[{elapsed}s] 批量解析有失败: {extract_result}")
            return result["data"]
        print(f"[{elapsed}s] 批量解析中...")
        time.sleep(interval)
    print(f"轮询超时 ({timeout}s)，请稍后手动查询 batch_id: {batch_id}")
    return None

# 示例用法
if __name__ == '__main__':

    file_path = "D:/software/jsjsjds/development/Enterprise_decision_making_system/1.pdf"
    batch_id, file_urls = parse_by_file_v4(file_path, model_version="vlm")
    if batch_id:
        result = poll_batch_result_v4(batch_id)
        print(result)
