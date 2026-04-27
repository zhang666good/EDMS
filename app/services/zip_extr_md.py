import os
import uuid
import requests
import zipfile
from io import BytesIO

def download_and_extract_md(zip_url, output_dir):
    """
    下载zip文件，解压full.md到指定目录并重命名为uuid.md，返回新文件路径。
    :param zip_url: zip包下载链接
    :param output_dir: 解压输出目录
    :return: 新的md文件绝对路径
    """
    # 下载zip文件
    resp = requests.get(zip_url)
    resp.raise_for_status()
    zf = zipfile.ZipFile(BytesIO(resp.content))
    # 查找full.md
    md_name = None
    for name in zf.namelist():
        if name.endswith("full.md"):
            md_name = name
            break
    if not md_name:
        raise FileNotFoundError("zip包中未找到full.md")
    # 生成uuid文件名
    os.makedirs(output_dir, exist_ok=True)
    new_name = f"{uuid.uuid4().hex}.md"
    new_path = os.path.join(output_dir, new_name)
    # 解压并重命名
    with zf.open(md_name) as md_file, open(new_path, "wb") as out_file:
        out_file.write(md_file.read())
    return new_path

# 示例用法
if __name__ == '__main__':
    zip_url = "https://cdn-mineru.openxlab.org.cn/pdf/2026-04-27/eda2a662-0b9e-4faf-b45f-859ff66062f9.zip"
    output_dir = "mineru_temp_md"
    md_path = download_and_extract_md(zip_url, output_dir)
    print(f"已解压并重命名: {md_path}")
    # 可读取md内容并作为上下文传递给dify agent
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    print(md_content[:500])  # 预览前500字符

