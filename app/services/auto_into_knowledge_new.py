import requests
import re
import json
import asyncio
import os
import tempfile
import traceback
from pathlib import Path
import akshare as ak

# AKShare 搜索A股公告
async def main(args):
    """
    使用 AKShare 搜索A股公告（上交所、深交所、北交所）
    
    Args:
        args: 包含 params 对象，其中有 keyword, page, limit 等参数
    
    Returns:
        搜索结果字典
    """
    try:
        # 获取 params 对象
        params_input = args.get("params", {})

        # 从 params 中获取 keyword（支持股票代码或关键词）
        keyword = params_input.get("keyword", "")

        # 页码 - AKShare不支持分页，这里保留参数用于兼容
        page = params_input.get("page", 0)

        # 每页数量 - 默认10
        limit = params_input.get("limit", 10)

        # 公告类型 - 映射到AKShare的category参数
        category_map = {
            "年报": "年报",
            "半年报": "半年报",
            "一季报": "一季报",
            "三季报": "三季报",
            "业绩预告": "业绩预告",
            "权益分派": "权益分派",
            "董事会": "董事会",
            "监事会": "监事会",
            "股东大会": "股东大会",
        }
        
        # 时间范围（可选）
        publish_time_start = params_input.get("publishTimeStart", "")
        publish_time_end = params_input.get("publishTimeEnd", "")

        # 如果没有 keyword，返回提示
        if not keyword:
            return {
                "status": "error",
                "message": f"请传入 keyword 参数（股票代码或关键词）",
                "results": []
            }

        print(f"[AKShare] 开始搜索: keyword={keyword}, limit={limit}")

        # ==================== 判断是股票代码还是关键词 ====================
        # 如果是6位数字，认为是股票代码
        is_stock_code = bool(re.match(r'^\d{6}$', keyword))
        
        results = []
        
        if is_stock_code:
            # 股票代码模式：直接查询该股票的公告
            print(f"[AKShare] 检测到股票代码: {keyword}")
            
            # 确定公告类型
            category = category_map.get(keyword, "")  # 如果keyword是类型，则使用；否则为空（全部类型）
            
            # 设置时间范围
            start_date = publish_time_start.replace('-', '') if publish_time_start else "20200101"
            end_date = publish_time_end.replace('-', '') if publish_time_end else "20251231"
            
            # 调用 AKShare 获取公告
            df = ak.stock_zh_a_disclosure_report_cninfo(
                symbol=keyword,
                market="沪深京",
                category=category,
                start_date=start_date,
                end_date=end_date
            )
            
            print(f"[AKShare] 找到 {len(df)} 条公告")
            
            # 转换为统一格式
            for idx, row in df.iterrows():
                if idx >= limit:
                    break
                    
                # 提取PDF直链
                web_url = row.get('公告链接', '')
                pdf_url = None
                
                # 转换网页URL为PDF直链
                match = re.search(r'announcementId=(\d+).*announcementTime=(\d{4}-\d{2}-\d{2})', web_url)
                if match:
                    ann_id = match.group(1)
                    ann_date = match.group(2)
                    pdf_url = f"http://static.cninfo.com.cn/finalpage/{ann_date}/{ann_id}.PDF"
                
                results.append({
                    "title": row.get('公告标题', ''),
                    "url": web_url,
                    "stock_code": row.get('代码', ''),
                    "file_type": "PDF",
                    "create_time": row.get('公告时间', ''),
                    "pdf_url": pdf_url
                })
        
        else:
            # 关键词模式：AKShare不支持关键词搜索，返回提示
            print(f"[AKShare] 关键词模式暂不支持，请使用股票代码")
            return {
                "status": "success",
                "keyword": keyword,
                "total": 0,
                "count": 0,
                "results": [],
                "message": "AKShare仅支持股票代码查询，请输入6位股票代码（如：600900）"
            }

        print(f"[AKShare] 提取了 {len(results)} 条结果")

        # ==================== 返回结果 ====================
        return {
            "status": "success",
            "keyword": keyword,
            "total": len(results),
            "count": len(results),
            "results": results
        }
    
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[AKShare] 错误: {str(e)}")
        print(f"[AKShare] 堆栈:\n{error_trace}")
        return {
            "status": "error",
            "message": f"搜索失败: {str(e)}",
            "detail": error_trace,
            "results": []
        }


async def download_and_upload_to_knowledge(args):
    """
    下载PDF文件到服务器，然后上传到指定知识库
    
    流程:
    1. 从巨潮资讯下载PDF文件到本地 data_file_temp/sse_downloads/ 目录
    2. 验证文件有效性(大小、格式)
    3. 上传到 Dify 知识库
    4. 保留本地文件备份(不删除)
    
    Args:
        args: 包含以下参数
            - params.search_results: 搜索结果列表（来自main函数）
            - params.dataset_id: 目标知识库ID
    
    Returns:
        上传结果统计
    """
    from app.services.knowledge import Knowledge
    
    # Windows 兼容性修复：设置事件循环策略
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    params_input = args.get("params", {})
    search_results = params_input.get("search_results", [])
    dataset_id = params_input.get("dataset_id", "")
    
    if not search_results:
        return {
            "status": "error",
            "message": "没有要处理的搜索结果"
        }
    
    if not dataset_id:
        return {
            "status": "error",
            "message": "请指定知识库ID"
        }
    
    # 初始化知识库客户端
    raw_base_url = os.getenv("DIFY_API_BASE_URL", "").strip() or os.getenv("DIFY_BASE_URL", "").strip()
    api_key = os.getenv("DIFY_API_KEY", "dataset-c6isoIYCm9MhwW9eOO25aKGF").strip()
    
    if not raw_base_url or not api_key:
        return {
            "status": "error",
            "message": "Dify配置缺失"
        }
    
    knowledge_client = Knowledge(base_url=raw_base_url, api_key=api_key)
    
    # 创建固定的下载目录
    project_root = Path(__file__).parent.parent.parent  # Enterprise_decision_making_system/
    download_dir = project_root / "data_file_temp" / "sse_downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    print(f"[下载目录] {download_dir}")
    
    # 处理每个PDF文件
    success_count = 0
    failed_count = 0
    results = []
    
    for idx, item in enumerate(search_results, 1):
        file_url = item.get("url")
        title = item.get("title", "未命名文档")
        stock_code = item.get("stock_code", "")
        
        print(f"\n{'='*60}")
        print(f"[处理 {idx}/{len(search_results)}] {title}")
        print(f"{'='*60}")
        
        if not file_url:
            failed_count += 1
            results.append({
                "title": title,
                "status": "failed",
                "reason": "无下载链接"
            })
            continue
        
        print(f"[下载URL] {file_url}")
                
        local_file_path = None
        try:
            # 步骤1: 使用 requests 下载PDF（AKShare已提供直链）
            print(f"[步骤1] 下载PDF文件...")
                        
            # 清理文件名中的非法字符
            safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)
            filename = f"{stock_code}_{safe_title}.pdf" if stock_code else f"{safe_title}.pdf"
            local_file_path = download_dir / filename
                    
            # 优先使用 pdf_url（AKShare提供的直链），否则使用 url
            download_url = item.get("pdf_url") or file_url
            print(f"[下载地址] {download_url}")
                    
            # 使用 requests 下载
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(download_url, timeout=60, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
            )
                    
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
                    
            # 保存到文件
            with open(local_file_path, 'wb') as f:
                f.write(response.content)
                    
            print(f"[保存成功] {local_file_path}")
            print(f"[文件大小] {len(response.content)} bytes ({len(response.content)/1024:.2f} KB)")
            
            # 步骤2: 验证下载的文件
            print(f"\n[步骤2] 验证文件...")
            
            if not local_file_path.exists():
                raise Exception("文件下载失败，文件不存在")
            
            file_size = local_file_path.stat().st_size
            print(f"[文件大小] {file_size} bytes ({file_size/1024:.2f} KB)")
            
            # 检查文件大小
            if file_size < 10 * 1024:
                failed_count += 1
                print(f"\n[警告] 文件过小，可能不是有效的PDF文件")
                
                # 读取内容预览
                with open(local_file_path, 'rb') as f:
                    preview = f.read(500).decode('utf-8', errors='ignore')
                
                print(f"[内容预览] {preview[:300]}")
                
                if '<!DOCTYPE' in preview or '<html' in preview.lower():
                    print(f"[诊断] 下载的是HTML页面，不是PDF文件")
                
                results.append({
                    "title": title,
                    "status": "failed",
                    "reason": f"文件过小({file_size} bytes),可能不是有效的PDF文件"
                })
                print(f"[结果] 跳过此文件\n")
                continue
            
            # 检查是否是PDF文件
            with open(local_file_path, 'rb') as f:
                header = f.read(5)
            
            if not header.startswith(b'%PDF'):
                failed_count += 1
                
                with open(local_file_path, 'rb') as f:
                    preview = f.read(500).decode('utf-8', errors='ignore')
                
                print(f"\n[警告] 文件格式错误！")
                print(f"[期望] PDF文件应以 '%PDF' 开头")
                print(f"[实际] 文件开头: {header}")
                print(f"[内容预览] {preview[:300]}")
                print(f"[诊断] 这不是一个有效的PDF文件")
                print(f"[建议] 请在浏览器中手动访问验证: {file_url}\n")
                
                results.append({
                    "title": title,
                    "status": "failed",
                    "reason": f"文件格式错误,不是有效的PDF文件"
                })
                continue
            
            print(f"[验证通过] ✓ 这是一个有效的PDF文件\n")
            
            # 步骤3: 上传到 Dify 知识库
            print(f"[步骤3] 上传到Dify知识库...")
            document_name = f"[{stock_code}] {title}" if stock_code else title
            
            # 构建完整的data参数，包含process_rule
            upload_data = {
                "name": document_name,
                "process_rule": {
                    "mode": "automatic"
                }
            }
            
            result = knowledge_client.create_document_by_file(
                dataset_id, 
                str(local_file_path),
                data=upload_data
            )
            
            # 检查上传结果
            doc_info = result.get("document", {})
            indexing_status = doc_info.get("indexing_status", "unknown")
            
            if indexing_status == "error":
                error_msg = doc_info.get("error", "未知错误")
                print(f"[警告] Dify索引失败: {error_msg}")
                failed_count += 1
                results.append({
                    "title": title,
                    "stock_code": stock_code,
                    "status": "failed",
                    "reason": f"Dify索引失败: {error_msg}",
                    "local_file": str(local_file_path)
                })
            else:
                print(f"[上传成功] 文档ID: {doc_info.get('id', '')}")
                print(f"[索引状态] {indexing_status}")
                success_count += 1
                results.append({
                    "title": title,
                    "stock_code": stock_code,
                    "status": "success",
                    "document_id": doc_info.get("id", ""),
                    "local_file": str(local_file_path)
                })
        
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"[错误] 处理失败: {str(e)}")
            print(f"[堆栈]\n{error_trace}")
            failed_count += 1
            results.append({
                "title": title,
                "status": "failed",
                "reason": str(e),
                "local_file": str(local_file_path) if local_file_path else None
            })
    
    # ==================== 汇总结果 ====================
    print(f"\n{'='*60}")
    print(f"[处理完成] 总计: {len(search_results)}, 成功: {success_count}, 失败: {failed_count}")
    print(f"[文件位置] {download_dir}")
    print(f"{'='*60}")
    
    return {
        "status": "success",
        "total": len(search_results),
        "success": success_count,
        "failed": failed_count,
        "results": results,
        "download_dir": str(download_dir)
    }
