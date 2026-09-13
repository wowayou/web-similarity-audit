# Web Similarity Audit - Roadmap

## 当前版本：v0.1.0 ✅

已完成：
- ✅ 整站爬取模式（`--crawl`）
- ✅ 四信号相似度检测（SHA-256、Jaccard、TF-IDF、块级重合）
- ✅ trafilatura 主体提取
- ✅ SSRF 防护、速率限制
- ✅ 跨平台支持（Linux/Windows/macOS）
- ✅ 16 个测试（100% 通过）
- ✅ GitHub Actions CI

---

## v0.2.0 - 体验优化（计划中）

### 1. 进度条与时间预估 🎯
**优先级**：P0（用户体验核心）

**当前问题**：
```
  [121/500] https://eigentime.org/en/tags/projects
Crawl complete: discovered 121 pages
Fetching 121 pages...
Extracting main content...
Computing pairwise similarity for 7260 pairs...
```
用户无法感知进度，大型站点审计时（500 页 = 124,750 对）体验差。

**目标功能**：
```
🔍 Crawling [████████████░░░░░░░░] 121/500 (24%) | ETA: 3m 45s
📥 Fetching  [█████████████████░░░] 98/121 (81%) | 2.3 pages/s | ETA: 10s
🧮 Computing [██████████░░░░░░░░░░] 4823/7260 (66%) | 87 pairs/s | ETA: 28s
```

**实现要点**：
- 使用 `tqdm` 或 `rich.progress`（选 rich，已有丰富的终端美化能力）
- 爬取阶段：显示已发现页数、队列长度、ETA
- 抓取阶段：显示已完成/总数、速率（pages/s）、网络等待
- 计算阶段：显示已处理对数、速率（pairs/s）、剩余时间
- 支持 `--quiet` 参数关闭进度条（CI 环境）

**文件修改**：
- `cli.py`：添加 `--quiet` 参数
- `crawler.py`：集成 rich.progress
- `fetcher.py`：添加进度回调
- `similarity.py`：计算阶段进度条

**测试验证**：
```bash
# 正常模式
web-similarity-audit --crawl https://example.com --max-pages 100

# 静默模式（CI）
web-similarity-audit --crawl https://example.com --quiet
```

---

### 2. 崩溃恢复与断点续传 💾
**优先级**：P1（稳定性）

**当前问题**：
- 500 页审计需要 5+ 分钟，网络中断、Ctrl+C、进程崩溃会导致全部重来
- 无法增量审计（新发现 20 页，需重跑全部 500 页）

**目标功能**：
```bash
# 首次运行
web-similarity-audit --crawl https://example.com --checkpoint crawl.state

# 中断后恢复
web-similarity-audit --resume crawl.state

# 增量审计
web-similarity-audit --crawl https://example.com --checkpoint crawl.state --incremental
```

**Checkpoint 格式**（JSON）：
```json
{
  "version": "0.2.0",
  "timestamp": "2024-01-13T18:30:45Z",
  "seed_url": "https://example.com",
  "config": {
    "max_pages": 500,
    "follow_external": false,
    "max_depth": 10
  },
  "state": {
    "crawled_urls": ["url1", "url2", ...],
    "fetched_pages": {"url1": {"html": "...", "sha256": "..."}, ...},
    "extracted_content": {"url1": {"main_content": "...", "confident": true}, ...},
    "pending_urls": ["url50", "url51", ...]
  },
  "progress": {
    "phase": "fetching",
    "completed": 45,
    "total": 121
  }
}
```

**实现要点**：
- 每个阶段完成后自动保存 checkpoint
- 支持 Ctrl+C 优雅退出（signal handler）
- `--resume` 模式：读取 checkpoint，跳过已完成工作
- `--incremental` 模式：只爬取新页面，与历史数据合并
- 网络异常自动重试 3 次，失败后保存状态退出

**文件修改**：
- `cli.py`：添加 `--checkpoint`、`--resume`、`--incremental` 参数
- `crawler.py`：支持从 checkpoint 恢复队列
- `fetcher.py`：跳过已抓取的 URL
- `extractor.py`：跳过已提取的内容
- `similarity.py`：增量计算（只对新页面计算相似度）
- 新增 `checkpoint.py`：状态管理模块

**边界处理**：
- Checkpoint 版本不兼容：提示用户重新运行
- 磁盘空间不足：提示并拒绝保存
- 损坏的 checkpoint：回退到初始状态
- 网站结构变化：增量模式下检测 404，标记为已删除

**测试验证**：
```bash
# 测试崩溃恢复
web-similarity-audit --crawl https://example.com --checkpoint test.state &
sleep 10 && kill $!
web-similarity-audit --resume test.state

# 测试增量审计
web-similarity-audit --crawl https://example.com --checkpoint base.state
# (网站新增 10 页)
web-similarity-audit --crawl https://example.com --checkpoint base.state --incremental
```

---

### 3. 异常处理与边界情况 🛡️
**优先级**：P1（稳定性）

**当前待改进**：

#### 3.1 网络异常
- [ ] DNS 解析失败
- [ ] 连接超时（默认 10s）
- [ ] 读取超时
- [ ] SSL 证书错误
- [ ] HTTP 429 (Rate Limit)
- [ ] HTTP 5xx 服务器错误

**增强策略**：
```python
# 指数退避重试
retry_delays = [1, 2, 4]  # 秒
for delay in retry_delays:
    try:
        response = httpx.get(url, timeout=10)
        break
    except (httpx.TimeoutException, httpx.NetworkError) as e:
        log(f"Retry {url} after {delay}s: {e}")
        time.sleep(delay)
```

#### 3.2 内容异常
- [ ] 空 HTML（0 字节）
- [ ] 超大页面（>10MB）
- [ ] 非 UTF-8 编码
- [ ] 损坏的 HTML（trafilatura 可能失败）
- [ ] 纯 JavaScript 渲染页面（无静态内容）

**增强策略**：
```python
# 大小检查
if len(html) > 10 * 1024 * 1024:  # 10MB
    log(f"Skip oversized page: {url}")
    return None

# 编码容错
html = response.content.decode('utf-8', errors='replace')

# 提取失败回退
content = trafilatura.extract(html) or extract_body_fallback(html)
```

#### 3.3 爬虫边界
- [ ] 无限循环（URL 参数变化）
- [ ] 爬虫陷阱（日历页面）
- [ ] 重复 URL（不同协议：http/https）
- [ ] 超出 max_pages 限制的处理

**增强策略**：
```python
# URL 规范化去重
def normalize_url(url):
    parsed = urlparse(url)
    # 移除 fragment
    # 排序 query 参数
    # 统一 http/https
    # 移除 www
    return normalized

# 日历页面检测
if re.search(r'/\d{4}/\d{2}/', url):  # /2024/01/
    if depth > 3:
        skip_calendar_pagination()
```

#### 3.4 报告生成
- [ ] 0 个相似对的报告
- [ ] 只有 1 个页面的情况
- [ ] CSV 中的特殊字符转义
- [ ] Markdown 表格过长（>1000 行）

**增强策略**：
```python
# 空结果友好提示
if not p1_pairs:
    report += "✅ No high similarity pairs found.\n"

# Markdown 表格截断
if len(p1_pairs) > 100:
    report += f"... and {len(p1_pairs) - 100} more pairs\n"
```

---

### 4. 性能优化 ⚡
**优先级**：P2（锦上添花）

#### 4.1 并发控制
当前：4 并发 HTTP 请求

优化方向：
- [ ] 根据网站响应速度自适应调整并发数（快速站点可到 8 并发）
- [ ] 按域名分组并发（避免单域名过载）
- [ ] 相似度计算并行化（多进程处理 TF-IDF）

#### 4.2 算法优化
- [ ] TF-IDF 向量化（用 NumPy 加速，但不引入 sklearn）
- [ ] MinHash/LSH（>500 页时自动启用，O(n) 复杂度）
- [ ] 块级重合使用 Bloom Filter（减少内存）

#### 4.3 内存优化
- [ ] 流式写入大 CSV（避免全部加载到内存）
- [ ] 分批计算相似度（每 1000 对写入一次）
- [ ] HTML 内容不保存到 checkpoint（只保存 SHA-256）

---

## v0.3.0 - Web UI（可选）

**优先级**：P3（非必需，取决于用户反馈）

### 功能设计

#### 启动方式
```bash
# 后台启动 Web UI
web-similarity-audit serve --port 5000

# 在浏览器打开 http://localhost:5000
```

#### 界面结构
```
┌─────────────────────────────────────────┐
│ Web Similarity Audit                    │
├─────────────────────────────────────────┤
│ [New Audit] [History] [Settings]        │
├─────────────────────────────────────────┤
│                                         │
│  URL or CSV File:                       │
│  [https://example.com          ] [+]    │
│                                         │
│  ☑ Crawl entire site                    │
│  Max pages: [500]  Max depth: [10]      │
│                                         │
│  [Start Audit]                          │
│                                         │
├─────────────────────────────────────────┤
│ Progress:                               │
│ ████████████░░░░░░░░ 65% (3m 12s left)  │
│                                         │
│ 📊 Results Preview:                     │
│   P1: 5 pairs | P2: 303 | P3: 453      │
│   [View Report] [Download CSV]          │
└─────────────────────────────────────────┘
```

#### 技术栈
- **后端**：FastAPI（轻量、异步、自动文档）
- **前端**：HTMX（无需 npm，纯 HTML）
- **样式**：Tailwind CSS via CDN
- **进度**：Server-Sent Events (SSE)

#### 特色功能
- [ ] 实时进度流（SSE）
- [ ] 交互式相似度矩阵（可视化热力图）
- [ ] 点击查看两页内容 diff
- [ ] 历史审计记录（SQLite 存储）
- [ ] 导出 PDF 报告

#### 文件结构
```
src/web_similarity_audit/
├── web/
│   ├── __init__.py
│   ├── app.py          # FastAPI 应用
│   ├── routes.py       # 路由
│   ├── templates/      # Jinja2 模板
│   │   ├── index.html
│   │   ├── report.html
│   │   └── history.html
│   └── static/         # CSS/JS
│       ├── style.css
│       └── app.js
```

**依赖增加**（可选安装）：
```toml
[project.optional-dependencies]
web = [
    "fastapi>=0.100.0",
    "uvicorn>=0.23.0",
    "jinja2>=3.1.0",
]
```

安装：
```bash
pip install web-similarity-audit[web]
```

---

## 实现计划

### 第一步：v0.2.0 核心功能（预计 2-3 天）
1. **Day 1**：进度条 + 时间预估
   - 集成 `rich.progress`
   - 修改 cli.py、crawler.py、fetcher.py
   - 测试各阶段进度显示

2. **Day 2**：崩溃恢复
   - 实现 checkpoint.py
   - 添加 signal handler（Ctrl+C）
   - 实现 --resume 逻辑

3. **Day 3**：异常处理 + 测试
   - 网络重试、编码容错
   - 边界情况处理
   - 补充测试用例

### 第二步：发布 v0.2.0
- 更新 CHANGELOG.md
- 标记 GitHub release
- 推送到 PyPI（可选）

### 第三步：收集反馈
- 在真实网站测试（COOWIN、eigentime.org）
- 根据使用情况决定是否实现 Web UI

---

## 贡献优先级

如果你现在只想实现一部分，建议顺序：

1. **进度条**（P0）- 用户体验立即提升
2. **崩溃恢复**（P1）- 大型站点审计必需
3. **异常处理**（P1）- 稳定性保障
4. **性能优化**（P2）- 如果 500 页审计 < 5 分钟可延后
5. **Web UI**（P3）- 看用户反馈再决定

---

## 技术决策记录

### 为什么选 rich 而不是 tqdm？
- rich 更现代，支持多进度条、颜色、表格
- 与我们的 Markdown 输出风格一致
- 自带 CLI 美化能力（Console.print）

### 为什么不立即实现 Web UI？
- CLI 工具适合 CI/CD 和顾问交付场景
- Web UI 需要额外 3-4 天开发
- 应先验证核心价值，再投资界面

### 为什么 checkpoint 用 JSON 而不是数据库？
- 单用户场景，不需要并发写入
- JSON 可读性强，便于调试
- 迁移简单（scp 一个文件）

---

**下一步行动**：选择一个功能开始实现，推荐从"进度条"开始，立即可见的改进最能提升信心。
