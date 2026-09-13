# Web Similarity Audit (网页相似度审计工具)

[![CI](https://github.com/wowayou/web-similarity-audit/workflows/CI/badge.svg)](https://github.com/wowayou/web-similarity-audit/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

检测网站内重复和近似重复内容的命令行工具。

[English](README.md) | 简体中文

## 功能特点

- **整站爬取模式** - 从单个起始 URL 发现并审计整个网站
- **多信号检测** - 结合 SHA-256、n-gram Jaccard、TF-IDF 和块级重合度
- **模板识别** - 自动检测并移除导航、页脚等公共模板内容
- **显式失败报告** - 主体提取失败时明确警告，不静默回退
- **可解释输出** - 每个相似度判断都有明确的触发原因
- **崩溃恢复** - 使用 `--resume` 继续中断的审计
- **进度跟踪** - 实时进度条和预计完成时间
- **跨平台** - Windows、macOS、Linux 全支持
- **CJK 支持** - 正确处理中文、日文、韩文内容

## 快速开始

### 安装

```bash
# 使用 pipx（推荐）
pipx install web-similarity-audit

# 或使用 pip
pip install web-similarity-audit
```

### 基础用法

```bash
# 爬取整个网站（最多 200 页）
web-similarity-audit --crawl https://example.com --max-pages 200

# 从 CSV 文件比较特定 URL
web-similarity-audit --csv urls.csv

# 继续中断的审计
web-similarity-audit --resume

# 自定义输出目录
web-similarity-audit --crawl https://example.com --output my-audit
```

### CSV 格式

创建 `urls.csv` 文件：

```csv
url
https://example.com/page1
https://example.com/page2
https://example.com/page3
```

## 输出说明

审计完成后生成三个文件：

### 1. `pages.json` - 页面元数据

```json
[
  {
    "url": "https://example.com/page1",
    "content_hash": "abc123...",
    "raw_text": "完整页面文本...",
    "main_content": "提取的主体内容...",
    "extraction_success": true,
    "extraction_method": "trafilatura",
    "char_count": 1234,
    "word_count": 200
  }
]
```

### 2. `pairs.csv` - 相似度比较

```csv
url_a,url_b,priority,sha256_match,jaccard,tfidf,block_overlap,trigger_reason
https://example.com/a,https://example.com/b,P1,False,0.85,0.92,0.78,"tfidf>=0.85 AND jaccard>=0.70"
```

**优先级说明：**
- `P1` (高) - 高度相似，需要立即处理
- `P2` (中) - 中度相似，建议检查
- `P3` (低) - 轻度相似，仅供参考

### 3. `report.md` - 可读报告

包含审计概要、提取失败警告、高优先级对列表等。

## 高级功能

### 进度跟踪

所有长时间操作都显示进度条：

```
Crawling website starting from: https://example.com
  Max pages: 200
  [15/200] https://example.com/products/item-15

Fetching 200 pages...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:45 < 0:00:00

Computing pairwise similarity for 19,900 pairs...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:01:23 < 0:00:00
```

### 崩溃恢复

如果审计被中断（Ctrl+C、网络故障等）：

```bash
# 直接恢复
web-similarity-audit --resume

# 或指定状态文件
web-similarity-audit --resume --state-file custom-state.json
```

状态文件 (`.audit-state.json`) 保存：
- 已抓取的 URL
- 已下载的内容
- 审计配置
- 当前进度

### 配置选项

```bash
# 并发和限速
web-similarity-audit --crawl https://example.com \
  --concurrency 8 \               # 最多 8 个并发连接
  --per-host-limit 2              # 每个主机每秒最多 2 个请求

# 爬取控制
web-similarity-audit --crawl https://example.com \
  --max-pages 500 \               # 最多爬取 500 页
  --follow-external               # 跟踪外部链接（默认不跟踪）

# 自定义输出
web-similarity-audit --crawl https://example.com \
  --output my-results             # 结果保存到 my-results/
```

## 相似度信号

工具使用四种互补信号检测重复内容：

### 1. SHA-256 哈希
- **用途**：检测完全相同的页面
- **范围**：精确匹配
- **触发**：哈希值完全相同

### 2. n-gram Jaccard 相似度
- **用途**：检测复制粘贴和轻微改动
- **范围**：0.0（完全不同）到 1.0（完全相同）
- **触发**：≥0.70 为 P1，≥0.40 为 P2

### 3. TF-IDF 余弦相似度
- **用途**：检测语义相似和改写内容
- **范围**：0.0（完全不同）到 1.0（完全相同）
- **触发**：≥0.85 为 P1，≥0.60 为 P2

### 4. 块级重合度
- **用途**：检测共享段落和部分
- **范围**：0.0（无共享块）到 1.0（所有块都共享）
- **触发**：≥0.60 为 P2

## 模板检测

工具自动识别和移除公共模板内容：

1. **识别公共块** - 查找出现在 ≥60% 页面中的文本块
2. **生成双视图** - 保存原始内容和去模板内容
3. **双重比较** - 分别对两个视图进行相似度计算

**注意**：如果总页面数 <5，模板检测可能不准确。

## 主体提取

使用 [trafilatura](https://github.com/adbar/trafilatura) 提取主要内容：

- 自动移除导航、页脚、侧边栏
- 支持多种 CMS（WordPress、Shopify 等）
- 返回置信度信息
- **失败时显式报告**（不静默回退到整页）

提取失败的页面会在 `report.md` 中列出。

## 安全特性

### SSRF 防护

阻止请求：
- 私有 IP 范围（10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16）
- 本地地址（127.0.0.0/8, ::1）
- 链路本地地址（169.254.0.0/16, fe80::/10）

### 速率限制

- 每个主机默认每秒 2 个请求
- 可配置的并发连接数
- 自动重试，指数退避
- 响应大小限制（10MB）

### 数据隐私

- 不向外部服务发送数据
- 仅本地存储结果
- 不记录敏感信息

## CI 集成

退出码：

- `0` - 成功
- `1` - 输入验证失败（参数错误）
- `2` - 抓取失败（网络错误）
- `3` - 处理失败（内部错误）
- `4` - 输出失败（写入错误）

示例 GitHub Actions 工作流：

```yaml
- name: Run similarity audit
  run: |
    pipx install web-similarity-audit
    web-similarity-audit --crawl https://staging.example.com --max-pages 100

- name: Check for P1 duplicates
  run: |
    if [ $(grep -c ",P1," audit-results/pairs.csv) -gt 0 ]; then
      echo "❌ Found P1 duplicates, blocking deploy"
      exit 1
    fi
```

## 开发

### 本地设置

```bash
# 克隆仓库
git clone https://github.com/wowayou/web-similarity-audit.git
cd web-similarity-audit

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发模式
pip install -e '.[dev]'

# 运行测试
pytest tests/ -v

# 代码检查
ruff check .
ruff format .
```

### 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 路线图

查看 [TODO.md](TODO.md) 了解计划功能：

- v0.3.0: 增强的改写检测
- v0.4.0: SEO 特定功能（sitemap、canonical、hreflang）
- v0.5.0: 性能优化（MinHash LSH、增量模式）
- v1.0.0: REST API 和集成

## 常见问题

### 为什么主体提取失败？

常见原因：
- 页面主要是导航/菜单
- 内容在 JavaScript 中生成（需要 `--render-js`）
- 非标准 HTML 结构
- 纯图片/视频页面

查看 `report.md` 的"提取失败"部分了解详情。

### 如何处理大型网站（1000+ 页）？

1. 分批处理：使用 `--max-pages` 分多次运行
2. 使用 sitemap（v0.4.0 计划中）
3. 通过 URL 模式过滤（计划中）
4. 等待 MinHash LSH 支持（v0.5.0）

### P1/P2/P3 阈值可以调整吗？

当前版本使用固定阈值。可配置阈值计划在 v0.3.0 中实现。

### 支持 JavaScript 渲染的 SPA 吗？

计划在 v0.4.0 中通过 `--render-js` 支持（使用 Playwright）。

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 致谢

- [trafilatura](https://github.com/adbar/trafilatura) - 内容提取
- [httpx](https://github.com/encode/httpx) - HTTP 客户端
- [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) - HTML 解析
- [rich](https://github.com/Textualize/rich) - 终端 UI

## 链接

- [文档](https://github.com/wowayou/web-similarity-audit)
- [问题追踪](https://github.com/wowayou/web-similarity-audit/issues)
- [更新日志](CHANGELOG.md)
- [贡献指南](CONTRIBUTING.md)
- [安全政策](SECURITY.md)

---

如有问题或建议，请[提交 issue](https://github.com/wowayou/web-similarity-audit/issues)。
