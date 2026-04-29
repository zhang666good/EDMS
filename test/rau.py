import requests
import json

# API 端点 URL
url = "http://127.0.0.1:8000/v1/chat/completions"

# 请求头，包含认证信息和内容类型
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer edms-business-analyst-test5678"
}

# 请求体数据，与您的 curl 命令中的 -d 参数内容一致
data = {
    "model": "edms-deep-insight",
    "messages": [
        {"role": "user", "content": "你好"}
    ],
    "stream": False
}

try:
    # 发送 POST 请求
    response = requests.post(url, headers=headers, json=data)

    # 检查 HTTP 状态码，如果出错会抛出异常
    response.raise_for_status()

    # 成功则打印格式化的 JSON 响应
    print("API 响应成功！")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

except requests.exceptions.RequestException as e:
    # 捕获并打印所有网络相关的错误
    print(f"请求失败：{e}")