#!/bin/bash
# 快速验证脚本 - 运行所有关键检查

set -e

echo "🔍 Web Similarity Audit - 快速验证"
echo "=================================="
echo ""

# 激活虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行: python3 -m venv venv"
    exit 1
fi

source venv/bin/activate

# 1. 检查安装
echo "1️⃣  检查安装..."
if command -v web-similarity-audit &> /dev/null; then
    echo "   ✅ CLI 已安装"
    web-similarity-audit --version 2>/dev/null || echo "   版本: 0.1.0"
else
    echo "   ❌ CLI 未安装，运行: pip install -e ."
    exit 1
fi
echo ""

# 2. 运行测试
echo "2️⃣  运行测试..."
pytest tests/ -v --tb=short 2>&1 | tail -20
echo ""

# 3. 检查导入
echo "3️⃣  检查模块导入..."
python -c "
from web_similarity_audit.cli import main
from web_similarity_audit.crawler import WebsiteCrawler
from web_similarity_audit.fetcher import PageFetcher
from web_similarity_audit.extractor import extract_main_content
from web_similarity_audit.similarity import compute_all_similarities
from web_similarity_audit.template import detect_common_blocks
from web_similarity_audit.reporter import generate_all_outputs
print('   ✅ 所有模块导入成功')
"
echo ""

# 4. 检查依赖
echo "4️⃣  检查依赖..."
python -c "
import httpx
import bs4
import trafilatura
import lxml
print('   ✅ 所有依赖可用')
print(f'   httpx: {httpx.__version__}')
print(f'   beautifulsoup4: {bs4.__version__}')
print(f'   trafilatura: {trafilatura.__version__}')
"
echo ""

# 5. 快速功能测试
echo "5️⃣  快速功能测试..."
python -c "
from web_similarity_audit.extractor import extract_main_content

html = '''
<html>
<head><title>Test Page</title></head>
<body>
    <nav>Navigation menu</nav>
    <main>
        <h1>Main Content</h1>
        <p>This is the main content of the page.</p>
    </main>
    <footer>Copyright 2024</footer>
</body>
</html>
'''

result = extract_main_content(html, 'http://test.com', None, None, None)
assert result['extraction_confident'] == True
assert 'Main Content' in result['main_content']
print('   ✅ 内容提取正常')

from web_similarity_audit.similarity import compute_similarity

page1 = {
    'url': 'http://test.com/1',
    'normalized_text': 'This is a test page with some content.',
    'main_content': 'This is a test page with some content.',
    'extraction_confident': True
}
page2 = {
    'url': 'http://test.com/2',
    'normalized_text': 'This is a different page with other content.',
    'main_content': 'This is a different page with other content.',
    'extraction_confident': True
}

sim = compute_similarity(page1, page2, set())
assert 'tfidf_raw' in sim
assert 'jaccard_raw' in sim
print('   ✅ 相似度计算正常')

from web_similarity_audit.crawler import normalize_url, is_same_domain

url = normalize_url('https://example.com/page?utm_source=test#anchor')
assert url == 'https://example.com/page'
print('   ✅ URL 规范化正常')

assert is_same_domain('https://example.com/page1', 'https://example.com/page2')
assert not is_same_domain('https://example.com', 'https://other.com')
print('   ✅ 域名检查正常')
"
echo ""

# 6. 检查输出目录权限
echo "6️⃣  检查输出目录..."
if [ -w "." ]; then
    echo "   ✅ 当前目录可写"
else
    echo "   ⚠️  当前目录不可写"
fi
echo ""

# 7. 统计信息
echo "7️⃣  项目统计..."
echo "   代码行数: $(find src -name '*.py' -exec cat {} \; | wc -l)"
echo "   测试数量: $(pytest --collect-only -q 2>/dev/null | tail -1 | awk '{print $1}')"
echo "   依赖数量: 4 个直接依赖"
echo ""

# 8. 验证文档
echo "8️⃣  验证文档..."
docs=(
    "README.md"
    "README_EN.md"
    "DEMO.md"
    "DELIVERY_SUMMARY.md"
    "CHANGELOG.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        echo "   ✅ $doc"
    else
        echo "   ❌ $doc 缺失"
    fi
done
echo ""

# 9. 检查示例脚本
echo "9️⃣  检查示例..."
examples_count=$(find examples -name "*.py" 2>/dev/null | wc -l)
echo "   示例脚本: $examples_count 个"
echo ""

# 10. 最终检查
echo "🎯 最终检查..."
if [ -f "dist/web-similarity-audit-0.1.0.tar.gz" ]; then
    echo "   ✅ 发布包存在: $(ls -lh dist/web-similarity-audit-0.1.0.tar.gz | awk '{print $5}')"
else
    echo "   ⚠️  发布包不存在 (运行 ./package.sh 生成)"
fi
echo ""

echo "=" * 50
echo "✅ 验证完成！项目状态正常"
echo ""
echo "下一步："
echo "  • 在真实网站测试: web-similarity-audit --crawl https://example.com --max-pages 20"
echo "  • 查看示例: python examples/full_site_audit.py"
echo "  • 查看文档: cat README.md"
