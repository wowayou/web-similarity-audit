# Web Similarity Audit

用于发现重复和近似重复网页的确定性命令行工具。

## 用法

```bash
web-similarity-audit --crawl https://example.com --max-pages 200
web-similarity-audit https://example.com/a https://example.com/b
web-similarity-audit urls.csv --output-dir audit-results
web-similarity-audit --resume --output audit-results
```

CSV 必须含 `url` 列，也可含 `selector`、`start_marker` 和 `end_marker`。

## 参数

支持 `--output-dir`/`--output`、`--crawl`、`--max-pages`、`--follow-external`、
`--ignore-robots`、`--max-response-size`、`--timeout`、`--rate-limit`/`--per-host-rate`、
`--max-concurrent`/`--concurrency`、`--allow-private`、`--resume`、`--no-resume`。请以
`web-similarity-audit --help` 输出为准。

## 工作方式

抓取模式发现 HTML 页面并默认应用 robots 规则。提取顺序为 CSV selector、CSV markers、
trafilatura，最后是标记为不确定的 body fallback。比较使用 SHA-256、字符三元 Jaccard、
两文档局部 TF-IDF 和块重叠。

启用 robots 时，4xx（包括 404）表示站点没有发布可用规则，可以继续抓取。
5xx、网络错误、429 或重定向会视为 robots 不可用并拒绝抓取该主机；其中
429 和重定向是有意比 RFC 9309 更严格的策略。Crawl-delay 按主机执行；
负值忽略，超过一小时的值会截断为一小时。

| 优先级 | 触发条件 |
| --- | --- |
| P1 | 精确 hash；TF-IDF ≥ 0.85；Jaccard ≥ 0.70；块重叠 ≥ 0.80 |
| P2 | TF-IDF ≥ 0.60；Jaccard ≥ 0.40；块重叠 ≥ 0.50 |
| P3 | TF-IDF ≥ 0.30；Jaccard ≥ 0.20；块重叠 ≥ 0.30 |

输出为 `pages.json`、`pairs.csv` 与 `report.md`。CI 统计 P1 时应筛选 `pairs.csv` 的
`priority` 列，`pages.json` 不包含 P1 计数。

## Python 使用

暂无稳定的高层 Python API。`PageFetcher`、`ContentExtractor`、`SimilarityCalculator`、
`TemplateDetector`、`Reporter` 是实验性构件，见 [docs/API.md](docs/API.md)。

## 安全与限制

默认 SSRF 检查拒绝非公网 DNS 结果；`--allow-private` 仅适用于可信内网或本地目标。
默认响应上限为 2 MiB。全量两两比较为 O(n²)，应相应限制 `--max-pages`。

需要 Python 3.10+ 和六个直接依赖：beautifulsoup4、certifi、httpx、lxml、trafilatura、rich。
详见 [SECURITY.md](SECURITY.md)、[架构复盘](docs/ARCHITECTURE_REVIEW.md)、
[架构说明](docs/ARCHITECTURE.md)、[示例](docs/EXAMPLES.md)、[FAQ](docs/FAQ.md)、
[贡献指南](docs/CONTRIBUTING.md) 与根目录 [CHANGELOG.md](CHANGELOG.md)。