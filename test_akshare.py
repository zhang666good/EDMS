"""
测试 AKShare 获取上交所公告
"""
import akshare as ak


def test_akshare_announcement():
    """测试获取长江电力的年报公告"""
    
    print("=" * 60)
    print("测试 AKShare 获取公告")
    print("=" * 60)
    
    try:
        # 获取长江电力(600900)的年报公告
        print("\n[1] 获取长江电力(600900)年报公告...")
        df = ak.stock_zh_a_disclosure_report_cninfo(
            symbol="600900",
            market="沪深京",  # 默认值：沪深京A股
            category="年报",
            start_date="20200101",
            end_date="20251231"
        )
        
        print(f"\n[结果] 找到 {len(df)} 条公告")
        print(f"\n[列名] {df.columns.tolist()}")
        
        if len(df) > 0:
            print(f"\n[前3条公告]:")
            print(df.head(3))
            
            # 显示第一条公告的链接
            if '公告链接' in df.columns:
                first_url = df.iloc[0]['公告链接']
                print(f"\n[示例链接] {first_url}")
                
                # 演示如何转换为PDF直链
                # 巨潮资讯的公告链接格式:
                # http://www.cninfo.com.cn/new/disclosure/detail?stockCode=600900&announcementId=xxx&orgId=gssz0000001&announcementTime=2025-04-30
                # PDF链接格式:
                # http://static.cninfo.com.cn/finalpage/2025-04-30/xxx.PDF
                
                import re
                match = re.search(r'announcementId=(\d+).*announcementTime=(\d{4}-\d{2}-\d{2})', first_url)
                if match:
                    ann_id = match.group(1)
                    ann_date = match.group(2)
                    pdf_url = f"http://static.cninfo.com.cn/finalpage/{ann_date}/{ann_id}.PDF"
                    print(f"\n[PDF直链] {pdf_url}")
        
        print("\n✅ 测试成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_akshare_announcement()
