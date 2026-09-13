# Web Similarity Audit（网页相似度审计工具）

[![CI](https://github.com/wowayou/web-similarity-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/wowayou/web-similarity-audit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/web-similarity-audit.svg)](https://pypi.org/project/web-similarity-audit/)
[![Python 版本](https://img.shields.io/pypi/pyversions/web-similarity-audit.svg)](https://pypi.org/project/web-similarity-audit/)
[![许可证](https://img.shields.io/github/license/wowayou/web-similarity-audit.svg)](LICENSE)

用于检测重复和近似重复网页的命令行工具。专为需要可解释、可复现审计结果的 SEO 专业人员打造。

[English](README.md) | 简体中文

## 为什么需要这个工具？

商业工具如 Screaming Frog 能检测重复内容，但缺少：
- **可解释性**：多个相似度信号，阈值清晰
- **可复现性**：保存状态，可使用 fixtures 重新运行审计
- **显式失败处理**：绝不静默退回全页面比较
- **CI/CD 集成**：在流水线中运行审计，而不只是 GUI 工具

## 功能特性

- 🔍 **全站爬取** 自动发现链接
- 📊 **多重相似度信号**：SHA-256、Jaccard、TF-IDF、块级重叠
- 🎯 **三级优先级系统**：P1（高）、P2（中）、P3（低）
- 🌐 **CJK 语言支持**：中文、日文、韩文文本处理
- 📝 **模板检测**：比较去除公共模板前后的内容
- 💾 **崩溃恢复**：使用 `--resume` 恢复中断的审计
- 🚦 **进度跟踪**：实时进度条和时间预估
- 🔒 **内置安全性**：SSRF 防护、速率限制、请求大小限制
- 📤 **多种输出格式**：JSON、CSV、Markdown 报告

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

**爬取整个网站：**
```bash
web-similarity-audit --crawl https://example.com --max-pages 200
```

**比较特定 URL：**
```bash
# 从 CSV 文件读取
web-similarity-audit urls.csv

# 直接指定 URL
web-similarity-audit https://example.com/page1 https://example.com/page2
```

**中断后恢复：**
```bash
web-similarity-audit --resume
```

### 输出示例

```
Crawling website starting from: https://example.com
  Max pages: 200

  [1/200] https://example.com
  [2/200] https://example.com/about
  [3/200] https://example.com/products
  ...

爬取完成：发现 121 个页面

抓取 121 个页面...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:45

计算 7260 对页面的相似度...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:05

完成，耗时 55.28 秒
  P1（高优先级）：5
  P2（中优先级）：303
  P3（低优先级）：453

报告已写入：audit-results/
```

## 工作原理

### 内容提取

1. 通过 HTTP/2 抓取 HTML，支持重试逻辑
2. 使用 [trafilatura](https://github.com/adbar/trafilatura) 提取主要内容
3. 回退到启发式规则（`<main>`、`<article>`、`[role=main]`）
4. **显式失败**，提取不确定时绝不静默使用完整 HTML

### 相似度检测

四种独立信号检测不同类型的重复：

| 信号 | 检测内容 | 阈值 |
|------|---------|------|
| **SHA-256** | 完全一致 | 100% |
| **Jaccard (3-gram)** | 复制的短语 | ≥0.70 (P1) |
| **TF-IDF** | 主题相似性 | ≥0.85 (P1) |
| **块级重叠** | 复制的段落 | ≥0.60 (P2) |

### 优先级分类

- **P1（高）**：内容高度相似，需要立即处理
  - TF-IDF ≥ 0.85 或 Jaccard ≥ 0.70 或完全一致
- **P2（中）**：可能重复，值得审查
  - TF-IDF ≥ 0.60 或 Jaccard ≥ 0.40 或块级重叠 ≥ 0.60
- **P3（低）**：有一定相似性，可能与模板相关

## 使用场景

### SEO 审计

查找重复的产品描述、薄内容和模板问题：

```bash
web-similarity-audit --crawl https://mystore.com --max-pages 500

# 查看高优先级重复
cat audit-results/report.md
```

### CI/CD 集成

在发现重复内容时阻止部署：

```yaml
- name: 运行内容审计
  run: web-similarity-audit urls.csv

- name: 检查重复内容
  run: |
    P1_COUNT=$(jq '.summary.p1_count' audit-results/pages.json)
    if [ "$P1_COUNT" -gt 0 ]; then
      echo "❌ 发现 $P1_COUNT 个高优先级重复"
      exit 1
    fi
```

### 咨询交付物

生成带有证据的可复现审计报告：

```bash
web-similarity-audit --crawl https://client-site.com --output client-audit
tar -czf client-audit-2025-01-15.tar.gz client-audit/
```

## 文档

- **[架构说明](docs/ARCHITECTURE.md)** - 系统设计和组件
- **[API 参考](docs/API.md)** - Python API 使用方法
- **[使用示例](docs/EXAMPLES.md)** - 实际使用场景
- **[常见问题](docs/FAQ.md)** - 50+ 个常见问题解答
- **[部署指南](docs/DEPLOYMENT.md)** - Docker 和 CI/CD 配置
- **[贡献指南](docs/CONTRIBUTING.md)** - 开发指南
- **[更新日志](docs/CHANGELOG.md)** - 版本历史

## 与其他工具对比

| 功能 | Screaming Frog | Sitebulb | 本工具 |
|------|----------------|----------|-------|
| **价格** | £149/年 | £35-275/月 | 免费 |
| **界面** | GUI | GUI + 报告 | CLI |
| **可解释性** | 单一评分 | 良好 | 多重信号 |
| **CI/CD** | 手动导出 | 手动 | 原生支持 |
| **离线使用** | 是 | 是 | 是 |
| **开源** | 否 | 否 | 是 |
| **可复现性** | 手动 | 手动 | 自动 |
| **最大页面数（免费）** | 500 | - | 无限制 |

**使用 Screaming Frog/Sitebulb 如果：** 你需要可视化的综合 GUI 工具。  
**使用本工具如果：** 你需要可解释的审计报告用于 CI/CD 或咨询交付。

## 高级用法

### 自定义设置

```bash
web-similarity-audit --crawl https://example.com \
  --max-pages 500 \
  --concurrency 8 \
  --per-host-rate 3.0 \
  --timeout 60 \
  --template-threshold 0.7 \
  --output my-audit
```

### Python API

```python
from web_similarity_audit import Auditor

auditor = Auditor(concurrency=8, per_host_rate=2.0)
results = auditor.audit_crawl("https://example.com", max_pages=200)

for pair in results.high_priority_pairs:
    print(f"{pair.url_a} <-> {pair.url_b}")
    print(f"  原因：{pair.trigger_reason}")
    print(f"  TF-IDF：{pair.tfidf:.3f}")
```

完整文档请参阅 [API.md](docs/API.md)。

## 系统要求

- Python 3.10 或更高版本
- 4 个依赖项：
  - `httpx[http2,brotli]` - 现代 HTTP 客户端
  - `beautifulsoup4` - HTML 解析
  - `lxml` - XML/HTML 处理
  - `trafilatura` - 内容提取

## 安全性

- SSRF 防护阻止私有 IP 范围
- 速率限制防止意外 DoS
- 请求大小限制（默认 10MB）
- 不存储凭据或身份验证
- 完整策略请参阅 [SECURITY.md](SECURITY.md)

## 性能

- **小型站点**（<50 页）：约 30-60 秒
- **中型站点**（200 页）：约 2-4 分钟
- **大型站点**（500 页）：约 5-10 分钟

瓶颈是网络 I/O（抓取），而非计算。使用 `--concurrency` 和 `--per-host-rate` 调优。

## 限制

- **JavaScript 渲染**：不支持（仅静态 HTML）
- **身份验证**：不支持（仅公开页面）
- **最大页面数**：O(n²) 比较限制实际最大值约为 1000 页
- **改写检测**：有限（计划通过序列对齐改进）
- **robots.txt**：尚未遵守（计划在 v0.3.0 实现）

## 路线图

**v0.3.0**（2025 年第二季度）：
- Sitemap.xml 解析
- Canonical 链接验证
- Hreflang 分析
- robots.txt 合规性
- 增强改写检测

**v0.4.0**（2025 年第三季度）：
- 可选的 REST API
- 用于探索的 Web UI
- MinHash/LSH 实现 O(n log n) 大规模比较
- 增量模式（仅比较变化的页面）

完整路线图请参阅 [TODO.md](TODO.md)。

## 贡献

欢迎贡献！请参阅 [CONTRIBUTING.md](docs/CONTRIBUTING.md) 了解：
- 开发环境配置
- 代码风格指南
- 测试要求
- Pull Request 流程

## 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE)

可免费用于商业和个人用途。

## 支持

- **文档**：[docs/](docs/)
- **问题反馈**：[GitHub Issues](https://github.com/wowayou/web-similarity-audit/issues)
- **讨论**：[GitHub Discussions](https://github.com/wowayou/web-similarity-audit/discussions)
- **作者**：[@wowayou](https://github.com/wowayou)
- **网站**：[eigentime.org](https://eigentime.org)

## 致谢

- [trafilatura](https://github.com/adbar/trafilatura) - 强大的内容提取
- [httpx](https://github.com/encode/httpx) - 现代 HTTP 客户端
- [Rich](https://github.com/Textualize/rich) - 精美的终端 UI

---

**如果觉得有用请给个 Star！** ⭐

**分享给需要重复内容检测的同事。** 📢
