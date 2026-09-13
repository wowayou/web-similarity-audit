# Web Similarity Audit（网页相似度审计工具）

[![CI](https://github.com/wowayou/web-similarity-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/wowayou/web-similarity-audit/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个用于检测重复和近似重复网页的命令行工具，提供详细的相似度分析。专为需要**显式**、**确定性**和**可解释**内容审计的 SEO 专业人士构建。

[English](README.md) | [简体中文](README.zh-CN.md)

## 特性

✨ **全站爬取模式**，类似 Screaming Frog  
📊 **多种相似度信号**：SHA-256、n-gram Jaccard、TF-IDF、块重叠度  
🎯 **模板检测**，更干净的比较结果  
📈 **进度条**，带时间预估  
💾 **崩溃恢复**，使用 `--resume` 标志  
🌐 **CJK 支持**（中文、日文、韩文）  
🔒 **SSRF 防护**和速率限制  
📋 **三种输出格式**：JSON、CSV、Markdown  
🚫 **显式失败** - 无静默回退  

## 快速开始

### 安装

```bash
pipx install web-similarity-audit
```

或使用 pip：
```bash
pip install web-similarity-audit
```

### 基本用法

比较特定 URL：
```bash
web-similarity-audit https://example.com/page1 https://example.com/page2
```

爬取整个网站：
```bash
web-similarity-audit --crawl https://example.com --max-pages 200
```

恢复中断的审计：
```bash
web-similarity-audit --resume
```

## 为什么选择这个工具？

### 问题

像 Screaming Frog 这样的商业工具可以检测重复内容，但存在以下问题：
- **静默回退**：当主内容提取失败时，它们会比较整个页面（包括导航、页脚），导致误报
- **黑盒评分**：你会得到一个相似度百分比，但没有解释
- **无法复现**：不能包含在 CI 中，也不能作为可复现的交付物提供给客户

### 本工具的方法

1. **显式失败**：如果内容提取失败，会被记录——绝不会静默回退到比较完整 HTML
2. **多种信号**：SHA-256 哈希、n-gram Jaccard、TF-IDF 余弦、块重叠度——每个都告诉你不同的信息
3. **模板感知**：检测公共块（导航、页脚）并提供原始和去模板两种比较视图
4. **可解释**：每个高优先级配对都会显示触发它的指标：`tfidf>=0.85 OR jaccard>=0.70`
5. **可复现**：CLI 工具支持 CSV 输入/输出，非常适合 CI 流水线或顾问交付物

## 文档

- **[安装和使用](README.zh-CN.md#使用)** - 命令和示例
- **[架构](docs/ARCHITECTURE.md)** - 内部工作原理（英文）
- **[API 参考](docs/API.md)** - Python 集成（英文）
- **[部署](docs/DEPLOYMENT.md)** - Docker、CI/CD、生产环境设置（英文）
- **[贡献指南](docs/CONTRIBUTING.md)** - 开发指南（英文）
- **[更新日志](CHANGELOG.md)** - 版本历史

## 使用

### 比较特定 URL

创建 `urls.csv`：
```csv
https://example.com/page1
https://example.com/page2
https://example.com/page3
```

运行审计：
```bash
web-similarity-audit urls.csv
```

### 爬取网站

```bash
web-similarity-audit --crawl https://example.com --max-pages 200
```

选项：
- `--max-pages N`：限制爬取 N 个页面（默认：200）
- `--follow-external`：跟随到其他域的链接（默认：仅同域）
- `--per-host-rate R`：每主机每秒最大请求数（默认：2.0）
- `--concurrency N`：最大并发 HTTP 请求数（默认：4）

### 高级选项

```bash
web-similarity-audit urls.csv \
  --output custom-dir \
  --concurrency 8 \
  --per-host-rate 1.0 \
  --timeout 30 \
  --template-threshold 0.7
```

### 恢复中断的审计

如果审计崩溃或被中断：
```bash
web-similarity-audit --resume
```

状态保存在 `.audit-state.json` 中，成功完成后会自动清理。

## 输出

在 `audit-results/` 目录中生成三个文件：

### 1. pages.json

完整的页面元数据：
```json
{
  "summary": {
    "total_pages": 121,
    "successful_fetches": 121,
    "extraction_success_rate": 0.95,
    "p1_count": 5,
    "p2_count": 303,
    "p3_count": 453
  },
  "pages": [
    {
      "url": "https://example.com/page1",
      "content_hash": "a3d2e1f...",
      "char_count": 5234,
      "extraction_success": true,
      "extraction_method": "trafilatura"
    }
  ]
}
```

### 2. pairs.csv

包含所有指标的相似度配对：
```csv
url_a,url_b,priority,sha256_match,jaccard,tfidf,block_overlap,trigger_reason
https://example.com/page1,https://example.com/page2,P1,false,0.72,0.88,0.65,tfidf>=0.85 OR jaccard>=0.70
```

### 3. report.md

人类可读的摘要，包含：
- 配置详情
- 摘要统计
- 按优先级排序的最相似配对
- 提取失败的页面

## 理解指标

### SHA-256 哈希
精确内容匹配。如果哈希匹配，页面在规范化后是相同的。

### N-gram Jaccard 相似度
使用三元组（3 个词的块）测量词序重叠。
- 高（>0.7）：许多相同的短语
- 中等（0.4-0.7）：一些共享的短语
- 低（<0.4）：不同的措辞

### TF-IDF 余弦相似度
测量主题相似性，同时降低常见词的权重。
- 高（>0.85）：非常相似的主题
- 中等（0.6-0.85）：相关的主题
- 低（<0.6）：不同的主题

### 块重叠度
测量段落级别的复制。
- 高（>0.6）：许多相同的段落
- 中等（0.3-0.6）：一些共享的块
- 低（<0.3）：大部分独特的块

## 优先级

**P1（高优先级）** - 可能需要采取行动的重复内容：
- TF-IDF ≥ 0.85 或
- Jaccard ≥ 0.70 或
- SHA-256 匹配

**P2（中等优先级）** - 建议审查：
- TF-IDF ≥ 0.60 或
- Jaccard ≥ 0.40 或
- 块重叠度 ≥ 0.60

**P3（低优先级）** - 仅供参考

## 使用场景

### SEO 重复内容审计
```bash
# 爬取生产站点
web-similarity-audit --crawl https://mysite.com --max-pages 500

# 检查 P1 问题
jq '.summary.p1_count' audit-results/pages.json
```

### 部署前检查
```bash
# 在 CI 流水线中
web-similarity-audit urls.csv
if [ $? -ne 0 ]; then
  echo "审计失败"
  exit 1
fi

P1_COUNT=$(jq '.summary.p1_count' audit-results/pages.json)
if [ "$P1_COUNT" -gt 0 ]; then
  echo "发现 $P1_COUNT 个高优先级重复内容"
  exit 1
fi
```

### 顾问交付物
```bash
# 创建可复现的审计
web-similarity-audit --crawl https://client-site.com --max-pages 200

# 与客户分享：
# - audit-results/ 目录
# - "运行：web-similarity-audit --resume" 以复制
```

### 多站点比较
```bash
# 从多个站点创建合并的 URL 列表
cat site1-urls.csv site2-urls.csv > all-urls.csv
web-similarity-audit all-urls.csv
```

## Python API

```python
from web_similarity_audit import Auditor

# 创建审计器
auditor = Auditor(concurrency=8, per_host_rate=2.0)

# 爬取和审计
results = auditor.audit_crawl("https://example.com", max_pages=200)

# 访问结果
print(f"发现 {results.summary.p1_count} 个高优先级重复内容")

for pair in results.high_priority_pairs:
    print(f"{pair.url_a} <-> {pair.url_b}")
    print(f"  TF-IDF: {pair.tfidf:.3f}, Jaccard: {pair.jaccard:.3f}")
```

更多详情请参见 [API 文档](docs/API.md)（英文）。

## 安全性

- **SSRF 防护**：阻止私有 IP 范围（RFC 1918、RFC 4193、localhost）
- **速率限制**：每主机令牌桶防止意外 DoS
- **输入验证**：URL 方案和格式验证
- **无凭证**：工具从不处理身份验证
- **只读**：仅读取公共网页

详见 [SECURITY.md](SECURITY.md)（英文）了解安全策略。

## 限制

- **最大页面数**：默认 200（可配置，但 O(n²) 比较会变慢）
- **仅文本**：不分析图像、视频和客户端 JavaScript 内容
- **公共页面**：不支持需要身份验证的内容
- **针对英语优化**：可与 CJK 语言配合使用，但 TF-IDF 针对英语调优

## 路线图

### v0.2.0（当前）
- [x] 全站爬取模式
- [x] 带预估时间的进度条
- [x] 使用 --resume 崩溃恢复
- [x] 块重叠度指标
- [x] 全面的文档

### v0.3.0（计划中）
- [ ] 增强的改写检测（序列对齐）
- [ ] Sitemap.xml 解析
- [ ] Canonical 链接验证
- [ ] Hreflang 分析

### v0.4.0（计划中）
- [ ] MinHash/LSH 用于 O(n log n) 比较
- [ ] 增量模式（仅比较更改的页面）
- [ ] HTML 结构相似性

### v1.0.0（未来）
- [ ] 使用 FastAPI 的 REST API
- [ ] 结果可视化的 Web UI
- [ ] 数据库后端（SQLite/PostgreSQL）
- [ ] 带作业队列的定时审计

详见 [TODO.md](TODO.md) 了解详细任务列表。

## 替代方案

**何时使用本工具：**
- 需要可解释、可复现的审计
- 需要 CI/CD 集成
- 与需要复现结果的顾问或客户合作
- 想了解页面*为什么*相似

**何时使用商业工具：**
- 非技术用户需要 GUI
- 需要除重复检测之外的全面 SEO 功能
- 有付费工具预算
- 需要企业支持

**替代方案：**
- [Screaming Frog](https://www.screamingfrogseoseo.com/) - 商业、GUI、全面的 SEO
- [Sitebulb](https://sitebulb.com/) - 商业、可视化报告
- [Siteliner](https://www.siteliner.com/) - 免费版本、仅在线

## 贡献

欢迎贡献！详见 [CONTRIBUTING.md](docs/CONTRIBUTING.md)（英文）了解：
- 开发环境设置
- 代码风格指南
- 测试要求
- Pull Request 流程

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 致谢

使用以下工具构建：
- [trafilatura](https://github.com/adbar/trafilatura) - 内容提取
- [httpx](https://github.com/encode/httpx) - 支持 HTTP/2 的 HTTP 客户端
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) - HTML 解析

## 支持

- **文档**：https://github.com/wowayou/web-similarity-audit/tree/main/docs
- **问题**：https://github.com/wowayou/web-similarity-audit/issues
- **讨论**：https://github.com/wowayou/web-similarity-audit/discussions
- **安全**：参见 [SECURITY.md](SECURITY.md)

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md) 了解版本历史。

---

**为需要可解释、可复现重复内容审计的 SEO 专业人士打造。**
