# 架构复盘与改进方案

日期：2026-09-15

## 1. 当前判断

项目是一个可用的 Beta 级 Python CLI，采用 `src/` 包布局和异步网络 I/O，主链路为：

```text
CLI 输入 / CSV / 站点发现
        ↓
网络抓取 → 内容提取 → 页面指纹
        ↓
模板块检测 → 两两相似度计算
        ↓
JSON / CSV / Markdown 报告
```

边界较清晰，但编排、策略和基础设施仍混在具体类中。`cli.py` 同时负责参数、恢复、任务调度、失败策略和报告编排；`crawler.py` 曾维护第二套 HTTP 实现；状态文件只覆盖抓取结果，不覆盖完整运行上下文或计算进度。当前更适合小规模、人工触发的审计，不应直接作为接收不可信 URL 的多租户服务。

## 2. 本轮已修复

| 优先级 | 问题 | 处理 |
|---|---|---|
| P0 | 整站爬虫和 robots.txt 绕过 `PageFetcher` 的 SSRF 策略 | 统一复用受保护抓取器，外部域名也在实际抓取前加载对应 robots 规则 |
| P0 | `client.get()` 先完整缓冲响应，大小限制事后才生效 | 请求 gzip/deflate 并以 raw 流有界解压；Brotli/未知编码拒绝，按解压后字节数中止 |
| P0 | URL 只检查字符串前缀，库调用可传凭据、坏端口或无主机 URL | CLI 和抓取器内层同时做结构化 URL 校验 |
| P1 | 并发参数无效：审计循环每次只 `fetch_all([url])` | 使用任务集合和 `as_completed`，由抓取器信号量控制并发 |
| P1 | `--resume` 文档宣称可单独使用，解析器却强制位置参数 | 位置参数改为可空，恢复模式从状态推断 crawl/list 模式 |
| P1 | 中断前 10 页没有任何状态；CSV selector/marker 恢复后丢失 | 抓取开始前保存计划，并持久化待处理输入的提取指令 |
| P1 | `fetch_failed` 未计入失败，`body_fallback` 也未计入不确定 | 统一报告分类规则 |
| P1 | Markdown 报告未转义 URL/错误中的 `|` | 对表格和列表中的动态值转义 |
| P2 | 清理后相似度为 `0.0` 时被序列化为 `null` | 改为显式判断 `is not None` |
| P2 | 包版本为 0.2.1，运行时 User-Agent 仍为 0.1.0 | 统一到包版本常量 |
| P2 | 零/负速率、超时、并发数会导致运行期异常 | 网络初始化前验证数值参数 |

## 3. 尚存漏洞与技术债

### P1：SSRF 仍需部署级网络隔离

0.2.2 的传输层会在连接前解析并校验地址，再把通过校验的 IP 固定到 TCP 连接，保留原始 Host/SNI；每次重定向也会重新校验，并禁用环境代理。
这消除了应用层预检与连接层二次解析的竞态，但不能替代部署级出口控制。

建议：

1. 接收不可信 URL 的部署配置出站防火墙，拒绝私网、链路本地、组播、保留地址和云元数据端点。
2. `--allow-private` 只应用于可信的本地/内网审计，不在服务端暴露给普通租户。
3. 持续用 DNS rebinding、IPv4/IPv6、重定向和代理环境矩阵做回归测试。

### P1：robots.txt 策略需要保持可审计

历史实现曾把所有网络错误和非 200 响应解释为“无限制”，也没有执行
`Crawl-delay`。0.2.2 已将结果分为可用、4xx 不存在和不可用三类：
5xx/网络失败按 RFC 9309 拒绝抓取，4xx（包括 404）允许抓取；429 与
3xx 也刻意从严拒绝并写入告警。`Crawl-delay` 的负值会忽略，超过
3600 秒会截断，最终与用户速率限制取较保守值。

后续应把这些策略结果纳入结构化事件和报告元数据，避免调用方只能看到
“成功 URL”而无法审计拒绝原因。

### P1：恢复状态需要继续扩展阶段游标

历史状态文件没有 schema 版本、配置快照和输入摘要，加载失败还会被静默转换为“无状态”。
0.2.2 已加入 schema/version/config/input digest，损坏或旧版本会显式要求
`--no-resume`，阈值失败也会保留状态以便重试。

下一步仍应把提取、相似度和报告阶段纳入版本化 `AuditCheckpoint`，记录算法
版本与阶段游标，并提供显式迁移而不是隐式兼容。

### P1：算法与文档中的“TF-IDF”定义不一致

当前 `_tfidf_cosine` 为每一对页面重新计算两文档 IDF，不是基于整个语料库的 TF-IDF。阈值因此依赖局部两文档统计，跨批次可比性较弱。架构文档还描述了不存在的模块名和数据类。

建议将语料向量化从 pair scorer 中提取为批次级 `CorpusVectorizer`，冻结 tokenization、IDF 和算法版本，并用带标签样本重新标定 P1/P2/P3 阈值。

### P2：O(n²) 结果全量保存在内存

当前会构造并保留所有页面对，200 页尚可，扩大上限后内存、CSV 体积和运行时间都会平方增长；现有架构文档“只保留高相似结果”与实现不符。

建议先生成候选，再做昂贵评分：精确哈希分桶 + MinHash/LSH 或 SimHash 召回；保留阈值附近样本用于误差分析；输出采用流式 writer。

### P2：HTTP 生命周期和错误可观测性不足

每个 URL 新建客户端，连接池无法跨 URL 复用；爬虫只返回成功 URL，调用者看不到被 robots 拒绝、内容类型错误、超限或网络失败的分类。抓取、重试、速率、内容类型和 robots 策略仍缺少统一事件模型。

建议让 `FetchService` 成为异步上下文管理器，复用连接池；返回结构化 `FetchResult` 和稳定错误码；同时记录最终 URL、重定向链、内容类型、字节数与耗时。

### P2：质量门禁当前不生效

Ruff 全仓有大量历史问题，CI 对 Ruff 与 mypy 都设置了 `continue-on-error`。本地 mypy 2.3.1 还触发 internal error。测试本身可通过，但静态门禁不能阻止回归。

建议先建立 lint baseline，只对新增/修改代码强制；分批清理后再全仓启用。固定并验证 mypy 版本，移除 `continue-on-error`，并把打包安装、CLI smoke test、Linux/Windows 路径行为加入 CI。

## 4. 目标架构

```text
InputAdapter ──→ AuditPlan ──→ DiscoveryService
                       │              │
                       └──────→ FetchService
                                   │
                         NetworkPolicy / RobotsPolicy
                                   ↓
                         ExtractionPipeline
                                   ↓
                         PageArtifactStore
                                   ↓
          CandidateGenerator → CorpusVectorizer → PairScorer
                                   ↓
                         FindingStream / Reporter
                                   ↑
                         AuditCheckpointStore
```

关键原则：

- 单一网络出口：crawl、robots、列表抓取和未来 sitemap 都必须经过 `FetchService`。
- 计划与执行分离：CLI 只构造 `AuditPlan`，应用服务负责阶段编排。
- 结果结构化：错误和审计事件使用稳定枚举，不靠字符串判断。
- 算法可版本化：提取、规范化、候选召回、评分和阈值都写入报告元数据。
- 有界资源：下载、页面数、候选数、内存、时间和输出大小均有预算。
- 可恢复：每个阶段幂等，checkpoint 原子写入，允许从最近阶段继续。

## 5. 分阶段落地

### 阶段 A：安全与正确性（下一版本，1–2 天）

- 实现解析一次并固定连接 IP 的网络后端，增加重绑定和重定向到私网测试。
- 完成 robots 状态机、crawl-delay 与失败策略。
- 给状态文件加 schema/version/config/input digest，损坏时显式报错。
- 把 SECURITY.md 中过强或过期的承诺改为真实威胁模型。

验收：不可信 URL 测试矩阵通过；crawl/list/robots/sitemap 无网络旁路；恢复前后报告一致。

### 阶段 B：服务边界与性能（3–5 天）

- 抽出 `AuditService`、`FetchService`、`CheckpointStore`，让 CLI 退化为适配层。
- 复用单个异步客户端和连接池，结构化抓取事件。
- 语料级向量化一次，pair scorer 只消费预计算特征。
- 报告流式写入并采用临时文件原子替换。

验收：200 页基准的网络阶段显著缩短；中断任意阶段可恢复；峰值内存有测量和预算。

### 阶段 C：规模化相似度（1–2 周）

- 以哈希分桶 + LSH 建候选召回层，再对候选做多信号评分。
- 建立人工标注集，测量 precision/recall 并重新标定阈值。
- 报告记录算法版本、参数、召回策略和被跳过页面原因。

验收：在固定召回率目标下支持 1,000+ 页面，复杂度不再由全量页面对主导。

### 阶段 D：工程治理（并行渐进）

- 先按 changed-files 强制 Ruff，再清零 baseline 并全仓强制。
- 固定类型检查工具链，逐步收紧类型。
- 合并重复、过期的交付文档，保留一个 README、一个架构文档、一个 changelog 和一个 roadmap 作为事实来源。
- 增加构建 wheel/sdist、安装后 CLI smoke test 和发布元数据一致性检查。
