# Web Similarity Audit - 快速演示

## 安装验证

```bash
# 克隆并安装
cd ~/Dev/my-projects/web-similarity-audit
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .

# 验证安装
web-similarity-audit --help
```

## 核心用例

### 用例 1：整站爬取审计（Screaming Frog 模式）

**场景**：审计整个网站的近重复页面

```bash
# 基础用法：爬取并审计整站（最多 200 页）
web-similarity-audit --crawl https://example.com

# 限制页面数量（小网站或快速测试）
web-similarity-audit --crawl https://example.com --max-pages 50

# 包含外部链接（用于竞品对比）
web-similarity-audit --crawl https://example.com --follow-external --max-pages 100

# 自定义输出目录
web-similarity-audit --crawl https://example.com --output-dir ./my-audit
```

**预期输出**：
```
Crawling website starting from: https://example.com
  Max pages: 200
  Follow external: False

  [1/200] https://example.com
  [2/200] https://example.com/about
  [3/200] https://example.com/products
  ...

Crawl complete: discovered 47 pages

Fetching 47 URLs...
  Success: 47/47

Extracting content...
  Confident extraction: 45/47
  Uncertain extraction: 2/47

Computing pairwise similarity...
  Total pairs: 1081

Report written to ./audit-results/report.md
```

### 用例 2：URL 列表审计

**场景**：审计指定的几个页面（来自 SEO 工具或人工发现）

```bash
# 直接提供 URL
web-similarity-audit \
  https://example.com/product-a \
  https://example.com/product-b \
  https://example.com/product-c

# 从 CSV 文件加载
web-similarity-audit urls.csv
```

**urls.csv 格式**：
```csv
url,selector
https://example.com/page1,article.content
https://example.com/page2,#main-content
https://example.com/page3,
```

### 用例 3：自定义提取规则

**场景**：网站使用了非标准 HTML 结构，需要自定义选择器

**custom-pages.csv**：
```csv
url,selector,start_marker,end_marker
https://example.com/page1,.product-specs,,
https://example.com/page2,,<!-- CONTENT START -->,<!-- CONTENT END -->
https://example.com/page3,,.main-section,
```

```bash
web-similarity-audit custom-pages.csv
```

## 输出解读

### report.md 示例

```markdown
# Web Similarity Audit Report

Generated: 2024-01-15 10:30:00

## Summary

- Total pages: 47
- Successfully extracted: 45 (95.7%)
- Extraction failures: 2 (4.3%)
- Total pairs: 1081
- P1 (high similarity): 3
- P2 (moderate similarity): 12
- P3 (low similarity): 28

## P1 - High Similarity Pairs

### Pair 1: Duplicate Detection

**URL 1**: https://example.com/product-wrench-10mm  
**URL 2**: https://example.com/product-wrench-10mm-copy

**Trigger**: sha256_match  
**Confidence**: Very High

Raw similarity:
- SHA-256: MATCH (identical)
- TF-IDF: 1.000
- Jaccard: 1.000
- Block overlap: 1.000

De-templated similarity:
- TF-IDF: 1.000
- Jaccard: 1.000
- Block overlap: 1.000

**Recommendation**: Remove duplicate page or set canonical.

---

### Pair 2: High Content Overlap

**URL 1**: https://example.com/guide-welding  
**URL 2**: https://example.com/tutorial-welding

**Trigger**: block_overlap_raw≥0.70  
**Confidence**: High

Raw similarity:
- SHA-256: different
- TF-IDF: 0.782
- Jaccard: 0.312
- Block overlap: 0.750 ← trigger

De-templated similarity:
- TF-IDF: 0.891
- Jaccard: 0.401
- Block overlap: 0.850

**Recommendation**: Merge content or differentiate clearly.

## Extraction Failures

⚠️ **2 pages failed confident extraction**

1. https://example.com/empty-page (Status: 200)
   - Method: trafilatura_uncertain
   - Reason: Insufficient content or complex layout

2. https://example.com/redirect (Status: 301)
   - Reason: Redirect not followed
```

### pairs.csv 示例

```csv
url1,url2,priority,trigger_reason,sha256_match,tfidf_raw,jaccard_raw,block_overlap_raw,tfidf_detemplate,jaccard_detemplate,block_overlap_detemplate
https://example.com/page1,https://example.com/page2,P1,sha256_match,True,1.000,1.000,1.000,1.000,1.000,1.000
https://example.com/page3,https://example.com/page4,P1,block_overlap_raw≥0.70,False,0.782,0.312,0.750,0.891,0.401,0.850
https://example.com/page5,https://example.com/page6,P2,tfidf_raw≥0.70,False,0.725,0.156,0.421,0.812,0.203,0.501
```

## 常见问题排查

### 问题 1：爬取页面数太少

```bash
# 问题
web-similarity-audit --crawl https://example.com
# 输出：Only discovered 1 page(s)

# 原因：网站使用 JavaScript 渲染链接
# 解决：使用 URL 列表模式 + sitemap.xml
```

### 问题 2：提取失败率高

```bash
# 查看 report.md 的 "Extraction Failures" 部分
# 如果失败率 > 20%，退出码为 3

# 解决：使用自定义选择器
```

### 问题 3：误报率高（导航栏相似）

```bash
# 查看去模板相似度列
# 如果 detemplate 分数明显低于 raw，说明是模板导致

# 建议：关注去模板视图，或调整 PRD 阈值
```

## 性能参考

| 页面数 | 页面对数 | 爬取时间* | 计算时间 | 总时间 |
|-------|---------|----------|---------|--------|
| 10    | 45      | ~5s      | <1s     | ~6s    |
| 50    | 1,225   | ~25s     | ~2s     | ~27s   |
| 100   | 4,950   | ~50s     | ~8s     | ~58s   |
| 200   | 19,900  | ~100s    | ~30s    | ~130s  |

\* 假设 2 rps、4 并发

## 与商业工具对比

| 工具 | 价格 | 整站爬取 | 可复现 | CI 集成 | 可解释性 |
|------|------|---------|--------|---------|---------|
| Screaming Frog | $259/年 | ✓ | ✗ | ✗ | 中 |
| Sitebulb | $35/月 | ✓ | ✗ | ✗ | 中 |
| **web-similarity-audit** | 免费 | ✓ | ✓ | ✓ | 高 |

## 下一步

1. **在实际项目中测试**：在 COOWIN 或其他 SEO 项目上运行
2. **验证召回率**：与 Screaming Frog 的 Near Duplicates 结果对比
3. **迭代阈值**：根据实际误报/漏报调整 P1/P2/P3 阈值
4. **CI 集成**：如果需要，添加到项目的 CI 流程中

```bash
# 示例：在 CI 中使用
web-similarity-audit --crawl https://staging.example.com --max-pages 100
if [ $? -eq 2 ]; then
  echo "High fetch failure rate detected"
  exit 1
fi
```

## 技术支持

- 查看测试用例：`tests/test_*.py`
- 查看示例脚本：`examples/crawl_and_audit.py`
- 查看完整 PRD：`33-web-page-similarity-audit-prd.md`
- 修改阈值：编辑 `src/web_similarity_audit/similarity.py` 的 `_assign_priority()`
