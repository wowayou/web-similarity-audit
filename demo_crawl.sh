#!/bin/bash
# 演示脚本 - 展示整站爬取和审计功能

set -e

echo "🔍 Web Similarity Audit - 整站爬取演示"
echo "======================================="
echo ""

# 检查是否已激活虚拟环境
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  虚拟环境未激活，正在激活..."
    source venv/bin/activate
fi

# 清理旧结果
echo "🧹 清理旧结果..."
rm -rf audit-results/
echo ""

# 示例 1: 整站爬取模式 (小规模)
echo "📊 示例 1: 整站爬取模式"
echo "-----------------------"
echo "命令: web-similarity-audit --crawl https://example.com --max-pages 10"
echo ""
echo "这将会："
echo "  1. 从首页开始爬取"
echo "  2. 自动发现站内链接"
echo "  3. 最多爬取 10 个页面"
echo "  4. 两两比较相似度"
echo ""
read -p "按 Enter 继续，或 Ctrl+C 取消..."
echo ""

web-similarity-audit --crawl https://example.com --max-pages 10

echo ""
echo "✅ 爬取完成！查看结果："
echo ""
echo "📄 完整报告:"
cat audit-results/report.md | head -50
echo ""
echo "... (查看完整报告: cat audit-results/report.md)"
echo ""

# 示例 2: URL 列表模式
echo ""
echo "📊 示例 2: URL 列表模式"
echo "----------------------"
echo "命令: web-similarity-audit url1 url2 url3"
echo ""
read -p "按 Enter 继续..."
echo ""

web-similarity-audit \
  https://example.com \
  https://example.org \
  https://example.net

echo ""
echo "✅ 完成！"
echo ""

# 显示输出文件
echo "📁 生成的文件:"
ls -lh audit-results/
echo ""

# 显示 CSV 样例
echo "📊 pairs.csv 样例 (前 5 行):"
head -5 audit-results/pairs.csv
echo ""

# 显示统计
echo "📈 统计信息:"
echo "  总页面数: $(jq -r '.metadata.total_pages' audit-results/full_data.json)"
echo "  比较对数: $(jq -r '.metadata.total_pairs' audit-results/full_data.json)"
echo "  P1 相似对: $(jq '[.pairs[] | select(.priority == "P1")] | length' audit-results/full_data.json)"
echo "  提取失败: $(jq '[.pages[] | select(.extraction_confident == false)] | length' audit-results/full_data.json)"
echo ""

echo "🎉 演示完成！"
echo ""
echo "下一步："
echo "  - 在真实网站上测试: web-similarity-audit --crawl https://your-site.com --max-pages 50"
echo "  - 查看完整文档: cat README.md"
echo "  - 查看代码: ls src/web_similarity_audit/"
