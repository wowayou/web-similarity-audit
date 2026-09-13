"""
整站爬取和审计示例

演示如何使用爬虫模块进行整站审计
"""
import asyncio
from web_similarity_audit.crawler import WebsiteCrawler
from web_similarity_audit.fetcher import PageFetcher
from web_similarity_audit.extractor import extract_main_content
from web_similarity_audit.similarity import compute_all_similarities
from web_similarity_audit.template import detect_common_blocks
from web_similarity_audit.reporter import generate_all_outputs


async def main():
    start_url = "https://example.com"
    max_pages = 20
    
    print(f"🔍 开始爬取 {start_url} (最多 {max_pages} 页)")
    print()
    
    # 1. 爬取网站
    crawler = WebsiteCrawler(max_pages=max_pages)
    
    def progress_callback(current, total):
        print(f"  发现: {current}/{max_pages} 页")
    
    discovered_urls = await crawler.crawl(start_url, progress_callback)
    print(f"✅ 发现 {len(discovered_urls)} 个页面")
    print()
    
    # 2. 抓取所有页面
    print("📥 抓取页面...")
    fetcher = PageFetcher()
    pages = []
    
    for i, url in enumerate(discovered_urls, 1):
        print(f"  [{i}/{len(discovered_urls)}] {url}")
        try:
            html = await fetcher.fetch(url)
            pages.append({
                'url': url,
                'html': html,
                'selector': None,
                'start_marker': None,
                'end_marker': None
            })
        except Exception as e:
            print(f"    ⚠️  抓取失败: {e}")
    
    print(f"✅ 成功抓取 {len(pages)}/{len(discovered_urls)} 页")
    print()
    
    # 3. 提取主体内容
    print("📝 提取主体内容...")
    for page in pages:
        extraction = extract_main_content(
            page['html'],
            page['url'],
            page['selector'],
            page['start_marker'],
            page['end_marker']
        )
        page.update(extraction)
        status = "✓" if extraction['extraction_confident'] else "⚠"
        print(f"  {status} {page['url']}")
    
    print()
    
    # 4. 检测公共块
    print("🔍 检测模板块...")
    if len(pages) >= 5:
        common_blocks = detect_common_blocks([p['normalized_text'] for p in pages])
        print(f"  发现 {len(common_blocks)} 个公共块")
    else:
        common_blocks = set()
        print(f"  页面数 < 5，跳过模板检测")
    
    print()
    
    # 5. 计算相似度
    print("📊 计算相似度...")
    pairs = compute_all_similarities(pages, common_blocks)
    
    # 统计各优先级数量
    p1_count = sum(1 for p in pairs if p['priority'] == 'P1')
    p2_count = sum(1 for p in pairs if p['priority'] == 'P2')
    p3_count = sum(1 for p in pairs if p['priority'] == 'P3')
    
    print(f"  总比较对数: {len(pairs)}")
    print(f"  P1 (高相似): {p1_count}")
    print(f"  P2 (中相似): {p2_count}")
    print(f"  P3 (低相似): {p3_count}")
    print()
    
    # 6. 生成报告
    print("📄 生成报告...")
    output_dir = "audit-results"
    generate_all_outputs(pages, pairs, common_blocks, output_dir)
    print(f"  报告已保存到: {output_dir}/")
    print()
    
    # 7. 显示摘要
    print("=" * 60)
    print("审计摘要")
    print("=" * 60)
    print(f"网站: {start_url}")
    print(f"爬取页面: {len(pages)}")
    print(f"比较对数: {len(pairs)}")
    print(f"高相似度对 (P1): {p1_count}")
    print(f"提取失败: {sum(1 for p in pages if not p['extraction_confident'])}")
    print()
    
    if p1_count > 0:
        print("⚠️  发现高相似度页面对，建议检查:")
        for pair in pairs[:5]:
            if pair['priority'] == 'P1':
                print(f"  • {pair['url1']}")
                print(f"    ↔ {pair['url2']}")
                print(f"    原因: {pair['trigger_reason']}")
                print()
    
    print(f"查看完整报告: cat {output_dir}/report.md")


if __name__ == "__main__":
    asyncio.run(main())
