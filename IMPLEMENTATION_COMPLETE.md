# Web Similarity Audit - 实现完成总结

## 项目概览

实现了一个类似 Screaming Frog Near Duplicates 的整站相似度审计工具，特点是失败显式、可复现、多信号可解释。

**仓库结构：**
```
web-similarity-audit/
├── src/web_similarity_audit/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py              # 命令行入口（支持 --crawl 模式）
│   ├── crawler.py          # 网站爬虫（类 Screaming Frog）
│   ├── fetcher.py          # HTTP 抓取（httpx + 限速 + SSRF 防护）
│   ├── extractor.py        # 主体提取（trafilatura + 失败显式）
│   ├── similarity.py       # 相似度计算（4 信号）
│   ├── template.py         # 模板检测（去模板视图）
│   ├── reporter.py         # 输出生成（JSON/CSV/Markdown）
│   └── models.py           # 数据模型
├── tests/                  # 16 个测试全部通过
│   ├── test_basic.py
│   ├── test_crawler.py     # 新增：爬虫单元测试
│   ├── test_edge_cases.py
│   └── test_integration.py
├── examples/
│   └── crawl_and_audit.py  # 整站爬取示例
├── README.md               # 中文文档，对比 Screaming Frog
├── CHANGELOG.md
└── pyproject.toml
```

## 核心功能

### 1. 双模式支持

**整站爬取模式**（新增，类 Screaming Frog）：
```bash
web-similarity-audit --crawl https://example.com --max-pages 200
```
- 从起始 URL 自动发现同域内所有页面
- 智能过滤非 HTML 资源（图片、PDF、CSS、JS）
- 尊重 robots.txt（基础实现）
- 速率限制：默认 2 rps/主机，4 并发
- 域内爬取（可选 `--follow-external`）

**URL 列表模式**（原 PRD 模式）：
```bash
web-similarity-audit url1 url2 url3
web-similarity-audit urls.csv
```

### 2. 四信号相似度检测

已实现 PRD 要求的所有信号：

1. **SHA-256**：完全重复检测
2. **n-gram Jaccard**：字符级重合（2/3/4-gram）
3. **TF-IDF 余弦**：主题相似度
4. **块级重合率**：段落级复制检测（新增，针对"改写式重复"）

### 3. 主体提取策略

采纳评审建议，使用 trafilatura 替代简单的 CSS 选择器：

- **优先级**：自定义 selector → start/end 标记 → trafilatura → 语义容器 → 整页
- **失败显式**：提取失败时设置 `extraction_confident=False` 并在报告中警告
- **CJK 支持**：通过 trafilatura 原生支持中日韩文本

### 4. 模板检测

- **阈值动态**：n < 5 时禁用自动公共块检测（修正原 PRD 的 60% 硬阈值问题）
- **双视图输出**：raw 相似度 + detemplate 相似度并排对比

### 5. 输出契约

三种格式同时生成在 `./audit-results/`：

- `report.md`：人类可读，分级展示 P1/P2/P3，包含失败警告
- `pages.json`：每页的提取结果、置信度、字符数
- `pairs.csv`：所有页面对的 4 个信号值 + 触发原因

## 技术选型（已修正 PRD 的过紧依赖）

采纳评审建议放宽到 4 个依赖：

1. **httpx[brotli,http2]**：现代 HTTP 客户端，支持 SSRF 防护的解析后 IP 检查
2. **beautifulsoup4**：HTML 解析
3. **lxml**：高性能 XML/HTML 解析器
4. **trafilatura**：生产级主体提取（F1 基准、CJK 支持）

## 与 Screaming Frog 对比

| 特性 | Screaming Frog | web-similarity-audit |
|------|----------------|---------------------|
| 整站爬取 | ✓ | ✓ |
| 近重复检测 | ✓（SimHash） | ✓（SHA-256 + Jaccard + TF-IDF + 块重合） |
| 主体提取失败处理 | 静默回退 | 显式报警 |
| 可复现 / CI 集成 | ✗（GUI） | ✓（CLI + fixtures） |
| 开源 | ✗ | ✓ |
| 可解释性 | 中（总分） | 高（输出所有信号值 + 触发原因） |
| 安装 | 需下载 | `pipx install` |

## 测试覆盖

16 个测试全部通过：

- `test_basic.py`：SHA-256、TF-IDF、块重合
- `test_crawler.py`：**新增** URL 规范化、域检查、链接提取、过滤规则
- `test_edge_cases.py`：自定义选择器、标记、模板检测阈值、CJK 规范化
- `test_integration.py`：端到端场景

## 性能边界

- **页面上限**：200（O(n²) 全对比 = 19,900 对）
- **单页上限**：2MB
- **计算时间**：200 页通常 < 5 分钟（不含网络）
- **并发控制**：4 并发 + 2 rps/主机

## 安全措施

- ✓ SSRF 防护（拒绝私有 IP、127.0.0.1、169.254.0.0/16）
- ✓ robots.txt 尊重（基础实现）
- ✓ User-Agent 透明标识
- ✓ 响应大小限制
- ✓ 超时控制

## 已修正的 PRD 问题

根据评审建议做的修正：

1. ✓ 依赖从 2 个放宽到 4 个，引入 trafilatura
2. ✓ 主体提取改用 trafilatura 而非弱启发式
3. ✓ 新增块级重合率信号，覆盖"改写式重复"
4. ✓ P1 条件改为"任一触发"，并输出触发原因到 CSV
5. ✓ n < 5 时禁用自动模板检测
6. ✓ HTTP 库选型 httpx（支持 SSRF 解析后检查）
7. ✓ 爬虫模式新增（类 Screaming Frog）

## 快速开始

```bash
# 安装
pip install -e .

# 整站审计（推荐）
web-similarity-audit --crawl https://example.com --max-pages 50

# URL 列表审计
web-similarity-audit url1 url2 url3

# 查看结果
cat audit-results/report.md
```

## 下一步建议

根据原评审文档的 M0/M1/M2 阶段划分：

- **当前状态**：M1 完成（核心功能 + 测试 + 爬虫模式）
- **M2 可选**：GitHub Actions CI、多语言 README、PyPI 发布
- **观察期**：按原评审建议，先在实际 SEO 项目（如 COOWIN）中使用 2 周，观察调用频率，再决定是否投入 M2

## 文件清单

- 10 个核心模块（`src/web_similarity_audit/*.py`）
- 4 个测试文件（16 个测试用例）
- 1 个示例脚本（`examples/crawl_and_audit.py`）
- 完整文档（README、CHANGELOG、QUICKSTART 等）

**状态：可交付、可在另一台机器上直接使用。**
