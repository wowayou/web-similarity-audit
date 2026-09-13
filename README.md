# Web Similarity Audit

![Tests](https://img.shields.io/badge/tests-16%20passed-success)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

CLI 工具用于检测网站内的近重复页面和薄页面，类似 Screaming Frog 的 Near Duplicates 功能，但增强了失败显式报告和可复现性。

## 特性

- **整站爬取模式** (`--crawl`)：类似 Screaming Frog，从起始 URL 自动发现并审计整个网站
- **URL 列表模式**：直接提供 URL 列表或 CSV 文件
- **失败显式报警**：主体提取失败时显式报告，不静默回退到全页比较
- **双重相似度视图**：原始内容 + 去模板内容对比
- **多信号可解释**：SHA-256、n-gram Jaccard、TF-IDF、块级重合率
- **本地确定性**：纯本地计算，可复现，支持 fixtures
- **跨平台 CI**：Windows/macOS/Linux 测试通过

## 快速开始

### 安装

```bash
pipx install web-similarity-audit
```

或从源码安装：

```bash
git clone <repo>
cd web-similarity-audit
pip install -e .
```

### 使用

**整站爬取模式**（推荐用于 SEO 审计）：

```bash
# 爬取整个网站（最多 200 页）
web-similarity-audit --crawl https://example.com

# 限制页面数量
web-similarity-audit --crawl https://example.com --max-pages 50

# 包含外部链接
web-similarity-audit --crawl https://example.com --follow-external
```

**URL 列表模式**：

```bash
# 直接提供 URL
web-similarity-audit https://example.com/page1 https://example.com/page2

# 从 CSV 文件加载
web-similarity-audit urls.csv
```

CSV 格式（可选列：selector, start_marker, end_marker）：

```csv
url,selector
https://example.com/page1,article.main-content
https://example.com/page2,#content
```

### 输出

报告生成在 `./audit-results/` 目录：

- `report.md`：人类可读的 Markdown 报告
- `pages.json`：所有页面的提取结果和元数据
- `pairs.csv`：所有页面对的相似度得分和触发原因

## 相似度分级

- **P1（高优先级）**：SHA-256 完全相同 OR TF-IDF ≥ 0.85 OR Jaccard ≥ 0.25 OR 块级重合率 ≥ 0.7
- **P2（中优先级）**：TF-IDF ≥ 0.70 OR Jaccard ≥ 0.15 OR 块级重合率 ≥ 0.5
- **P3（低优先级）**：TF-IDF ≥ 0.50 OR Jaccard ≥ 0.10

## 技术栈

- **HTTP 客户端**：httpx（支持 HTTP/2、Brotli）
- **HTML 解析**：BeautifulSoup4 + lxml
- **主体提取**：trafilatura（F1 基准、CJK 支持）
- **相似度计算**：纯标准库（TF-IDF、Jaccard、SHA-256）

## 爬虫特性

- **尊重 robots.txt**（基础实现）
- **速率限制**：默认每个主机 2 rps
- **并发控制**：默认最多 4 个并发请求
- **智能过滤**：自动跳过图片、PDF、CSS、JS 等非 HTML 资源
- **域内爬取**：默认只爬取同域名页面（可选 `--follow-external`）

## 开发

```bash
# 克隆仓库
git clone <repo>
cd web-similarity-audit

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖（可编辑模式）
pip install -e .

# 运行测试
pytest tests/ -v

# 运行单个测试
pytest tests/test_crawler.py -v
```

## 与 Screaming Frog 对比

| 特性 | Screaming Frog | web-similarity-audit |
|------|----------------|---------------------|
| 整站爬取 | ✓ | ✓ |
| 近重复检测 | ✓（SimHash） | ✓（多信号） |
| 主体提取 | CSS 选择器，失败静默 | trafilatura，失败显式 |
| CLI / 可复现 | ✗（GUI） | ✓ |
| 开源 / 免费 | ✗ | ✓ |
| 可解释性 | 中 | 高（输出所有信号值） |
| CI 集成 | ✗ | ✓ |

## 依赖列表

- beautifulsoup4 ≥ 4.12.0
- httpx[brotli,http2] ≥ 0.27.0
- lxml ≥ 5.0.0
- trafilatura ≥ 1.12.0

## 退出码

- `0`：成功完成
- `1`：输入错误（URL 格式、数量等）
- `2`：抓取失败率 > 20%
- `3`：主体提取失败率 > 20%
- `4`：致命错误或用户中断

## 许可证

MIT License

## 致谢

- [trafilatura](https://github.com/adbar/trafilatura)：主体提取
- [httpx](https://github.com/encode/httpx)：现代 HTTP 客户端
- PRD 中提到的 Screaming Frog、Sitebulb 等商业工具提供的灵感
