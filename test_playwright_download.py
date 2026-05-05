"""
测试 Playwright 下载上交所 PDF
"""
import asyncio
from playwright.async_api import async_playwright


async def test_download():
    """测试下载一个上交所PDF文件"""
    
    # 测试URL - 使用用户提供的新链接
    test_url = "https://static.sse.com.cn/disclosure/listedinfo/announcement/c/new/2026-04-18/600900_20260418_190U.pdf"
    
    print(f"[测试] 开始访问: {test_url}")
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(
            headless=False,  # 显示浏览器窗口，方便调试
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # 创建上下文
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
        )
        
        # 创建页面
        page = await context.new_page()
        
        try:
            # 先访问上交所首页获取Cookie
            print(f"[步骤1] 访问上交所首页...")
            await page.goto("https://www.sse.com.cn/", wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(2000)
            print(f"[完成] 首页访问成功")
            
            # 再访问PDF链接
            print(f"\n[步骤2] 访问PDF链接...")
            response = await page.goto(test_url, wait_until='networkidle', timeout=30000)
            
            if response:
                print(f"[响应状态] {response.status}")
                print(f"[响应头] Content-Type: {response.headers.get('content-type')}")
            
            # 等待一下
            await page.wait_for_timeout(3000)
            
            # 检查页面内容类型
            content_type = await page.evaluate("() => document.contentType")
            print(f"\n[页面类型] {content_type}")
            
            # 获取页面标题
            title = await page.title()
            print(f"[页面标题] {title}")
            
            # 截图查看
            await page.screenshot(path="test_screenshot.png")
            print(f"[截图] 已保存到 test_screenshot.png")
            
            print("\n[成功] Playwright 工作正常！")
            
        except Exception as e:
            print(f"\n[错误] {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_download())
