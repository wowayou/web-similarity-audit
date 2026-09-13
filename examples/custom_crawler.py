"""
自定义爬虫配置示例

演示如何自定义爬虫行为：
- 设置爬取深度
- 排除特定路径
- 自定义进度回调
- 过滤特定类型的链接
"""
import asyncio
import re
from web_similarity_audit.crawler import WebsiteCrawler


async def custom_crawl_example():
    """带自定义配置的爬取示例"""
    
    start_url = "https://example.com"
    
    print("=" * 60)
    print("示例 1: 基础爬取")
    print("=" * 60)
    
    crawler = WebsiteCrawler(max_pages=10)
    
    def simple_progress(current, total):
        print(f"进度: {current}/{total} 页")
    
    urls = await crawler.crawl(start_url, simple_progress)
    print(f"✅ 发现 {len(urls)} 个页面\n")
    
    
    print("=" * 60)
    print("示例 2: 仅爬取产品页")
    print("=" * 60)
    
    # 自定义过滤：只抓取 /products/ 路径
    crawler = WebsiteCrawler(max_pages=50)
    
    urls = await crawler.crawl(start_url)
    product_urls = [url for url in urls if '/product' in url.lower()]
    
    print(f"总页面: {len(urls)}")
    print(f"产品页: {len(product_urls)}")
    print("\n产品页列表:")
    for url in product_urls[:10]:
        print(f"  • {url}")
    if len(product_urls) > 10:
        print(f"  ... 还有 {len(product_urls) - 10} 个")
    print()
    
    
    print("=" * 60)
    print("示例 3: 详细进度跟踪")
    print("=" * 60)
    
    discovered = []
    
    def detailed_progress(current, total):
        print(f"\r正在爬取... 已发现: {current} | 队列: {total}", end='', flush=True)
        if current % 10 == 0:
            print()  # 每 10 个换行
    
    crawler = WebsiteCrawler(max_pages=30)
    urls = await crawler.crawl(start_url, detailed_progress)
    print(f"\n\n✅ 完成！总计 {len(urls)} 页\n")
    
    
    print("=" * 60)
    print("示例 4: 分析链接分布")
    print("=" * 60)
    
    crawler = WebsiteCrawler(max_pages=50)
    urls = await crawler.crawl(start_url)
    
    # 按路径分组
    from collections import defaultdict
    from urllib.parse import urlparse
    
    path_counts = defaultdict(int)
    for url in urls:
        path = urlparse(url).path.split('/')[1] if urlparse(url).path.count('/') > 1 else 'root'
        path_counts[path] += 1
    
    print("路径分布:")
    for path, count in sorted(path_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  /{path:20s} : {count:3d} 页")
    print()


async def exclude_patterns_example():
    """演示如何排除特定模式的 URL"""
    
    print("=" * 60)
    print("示例 5: 排除特定模式")
    print("=" * 60)
    
    start_url = "https://example.com"
    crawler = WebsiteCrawler(max_pages=100)
    
    all_urls = await crawler.crawl(start_url)
    
    # 排除规则
    exclude_patterns = [
        r'/tag/',
        r'/category/',
        r'/author/',
        r'\?page=',
        r'#',
    ]
    
    filtered_urls = []
    excluded_urls = []
    
    for url in all_urls:
        if any(re.search(pattern, url) for pattern in exclude_patterns):
            excluded_urls.append(url)
        else:
            filtered_urls.append(url)
    
    print(f"总 URL: {len(all_urls)}")
    print(f"保留: {len(filtered_urls)}")
    print(f"排除: {len(excluded_urls)}")
    print()
    
    if excluded_urls:
        print("排除的 URL 样例:")
        for url in excluded_urls[:5]:
            print(f"  • {url}")
        print()


async def compare_crawl_strategies():
    """比较不同爬取策略的结果"""
    
    print("=" * 60)
    print("示例 6: 爬取策略对比")
    print("=" * 60)
    
    start_url = "https://example.com"
    
    # 策略 1: 小规模快速扫描
    print("策略 1: 快速扫描 (10 页)")
    crawler = WebsiteCrawler(max_pages=10)
    urls_small = await crawler.crawl(start_url)
    print(f"  结果: {len(urls_small)} 页\n")
    
    # 策略 2: 中等规模
    print("策略 2: 标准扫描 (50 页)")
    crawler = WebsiteCrawler(max_pages=50)
    urls_medium = await crawler.crawl(start_url)
    print(f"  结果: {len(urls_medium)} 页\n")
    
    # 策略 3: 大规模深度扫描
    print("策略 3: 深度扫描 (200 页)")
    crawler = WebsiteCrawler(max_pages=200)
    urls_large = await crawler.crawl(start_url)
    print(f"  结果: {len(urls_large)} 页\n")
    
    print("建议:")
    print("  • 快速审计: 10-20 页")
    print("  • 日常审计: 50-100 页")
    print("  • 全面审计: 200 页 (上限)")
    print()


if __name__ == "__main__":
    print("🔍 Web Similarity Audit - 爬虫配置示例")
    print()
    
    # 运行示例
    asyncio.run(custom_crawl_example())
    asyncio.run(exclude_patterns_example())
    asyncio.run(compare_crawl_strategies())
    
    print("=" * 60)
    print("✅ 所有示例完成！")
    print("=" * 60)
