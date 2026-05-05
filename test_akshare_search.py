"""
测试 AKShare 替换后的上交所公告搜索
"""
import asyncio
from app.services.auto_into_knowledge import main


async def test_search():
    """测试搜索功能"""
    
    print("=" * 60)
    print("测试 AKShare 搜索功能")
    print("=" * 60)
    
    # 测试1: 股票代码搜索
    print("\n[测试1] 搜索长江电力(600900)的年报...")
    result = await main({
        "params": {
            "keyword": "600900",
            "limit": 3
        }
    })
    
    print(f"\n[结果] 状态: {result['status']}")
    print(f"[结果] 总数: {result.get('total', 0)}")
    print(f"[结果] 数量: {result.get('count', 0)}")
    
    if result.get('results'):
        print(f"\n[前3条结果]:")
        for i, item in enumerate(result['results'][:3], 1):
            print(f"  {i}. {item['title']}")
            print(f"     代码: {item['stock_code']}")
            print(f"     PDF: {item.get('pdf_url', 'N/A')[:80]}...")
    
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(test_search())
