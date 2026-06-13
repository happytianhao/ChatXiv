# ChatXiv

本地优先、渐进式披露的文献调研助手 —— 基于 [DeepXiv](https://github.com/DeepXiv/deepxiv_sdk)，arxiv 友好，全程本地运行。当你收到调研请求（如"调研自动驾驶世界模型方向"），请按照以下工作流使用 `scripts/` 中的 CLI 脚本完成任务。

## 核心原则

1. **本地优先** — 每次操作前先检查 `papers/` 本地缓存，再决定是否调用 DeepXiv。API 配额有限。
2. **渐进式披露** — 绝不直接读取 `papers/*.json` 文件。通过 CLI 按需获取每一层信息。
3. **两种工作流**：
   - **主题导向** — 用于调研某个研究方向。先创建主题，搜索约 100 篇论文，撰写报告。
   - **阅读导向** — 用于深入理解某篇论文。创建阅读文件夹，获取全文内容，撰写详细解读。
4. **输出可控** — CLI 只打印精简摘要，全文留在磁盘上，不会撑爆上下文。
5. **每个主题约 100 篇文献** — 默认每个主题搜索约 100 篇论文，再渐进式精读。
6. **每个阅读约 1 篇论文** — 深入解读包含所有主要章节、代码讲解和综合分析。

## 工作流

### 工作流 1：主题调研（综述）

当用户要求调研某个方向时，使用**分层数据收集**方法：

**第一阶段：分层数据收集**（对不同层级的论文进行逐步深入的获取）
```
1. 创建主题
2. 搜索 ~100 篇论文（先查本地，再调 DeepXiv）
3. 使用 batch-brief 获取所有 ~100 篇论文的 brief
   - python scripts/chatxiv.py batch-brief <paper_id1> <paper_id2> ... <paper_id100>
   - 提供：标题、TLDR、关键词、引用数、年份
   - 这是撰写报告的主要信息源
   - 轻量级且永久缓存
4. 获取最有前景的 ~30 篇论文的 head（章节结构）
   - 帮助识别关键章节和论文范围
5. 深入阅读最重要的 ~10 篇论文
   - 使用 read 命令读取关键章节（配合 --grep / --range）
   - 为"关键论文与洞察"部分提取详细见解
```

**第二阶段：撰写报告**（像 related work 一样的全景覆盖）
```
6. 按子领域或研究方向组织论文
7. 使用 brief 数据为 ~70-90% 的论文撰写摘要
   - 每篇论文：1-2 句话描述关键贡献 + 引用数标记
   - 格式：**论文标题 (paper_id, 年份)** — [1-2 句话总结]。引用数：X
   - 使用 brief 中的标题、摘要、关键词、引用数
   - 将论文连接成发展叙述（演进、顺序解决问题）
8. 对 ~10 篇最重要的论文：使用 head/read 的见解进行更深入的分析（2-3 段）
9. 在 topics/<slug>/report.md 中综合最终报告，完成所有部分
```

**关键原则**：全景覆盖（70-90% 的论文）使用轻量级摘要；只对前 10 篇论文进行深入阅读。

### 工作流 2：论文深读（深潜）

当用户要求解读或深入理解某篇论文时：

```
1. 创建阅读文件夹：readings/<paper_id>_<slug>/
2. 获取 brief 获得论文元数据
3. 获取 head 获得完整结构
4. 阅读所有主要章节（或关键章节）
5. 在 readings/<paper_id>_<slug>/report.md 中撰写详细解读（NOT explanation.md）
6. 报告结构包含以下章节：
   - 研究动机与问题陈述
   - 核心方法与架构
   - 关键技术贡献
   - 实验结果与评估
   - 优势与局限
   - 影响与未来方向
   - 相关工作（如适用）
```

**关键点**：使用 `report.md` 作为论文深读的输出文件，与主题调研保持一致。这确保了所有研究输出的命名规范。

### 逐步操作（主题调研）

```bash
# 1. 创建主题
python scripts/chatxiv.py topic create "自动驾驶世界模型"

# 2. 搜索约 100 篇 — 使用 --topic 自动关联结果
python scripts/chatxiv.py search "world models autonomous driving" --limit 100 --topic "自动驾驶世界模型"

# 3. 从搜索结果中提取 paper_id（复制 paper_id 列）

# 4. 使用 batch-brief 获取所有 ~100 篇论文的摘要
python scripts/chatxiv.py batch-brief 2507.12762 2008.00334 2108.00273 2409.01256 1804.02675 2108.01599 2605.00051 2502.18496 2604.09305 2212.04677 2511.08640 2007.14232 2308.15985 2507.12755 2007.00101 2212.09381 2407.16277 2506.10002 2511.06226 ...

# 5. 查看最有前景的 ~30 篇论文的结构
python scripts/chatxiv.py head 2507.12762 --with-paragraph-counts
python scripts/chatxiv.py head 2008.00334 --with-paragraph-counts
# ... 重复约 30 篇论文

# 6. 阅读最重要的 ~10 篇论文的特定章节
python scripts/chatxiv.py read 2507.12762 "Method"
python scripts/chatxiv.py read 2507.12762 "Experiments" --range 0:3
python scripts/chatxiv.py read 2008.00334 "Introduction"
# ... 重复约 10 篇论文

# 7. 撰写报告
# 编辑 topics/<slug>/report.md，使用 brief 数据 + head/read 的深入见解进行综合
```

### 逐步操作（论文深读）

```bash
# 1. 创建阅读文件夹
python scripts/chatxiv.py topic create "Transformer 论文"  # 创建 readings/<paper_id>_<slug>/ 结构

# 2. 获取论文元数据
python scripts/chatxiv.py brief 1706.03762

# 3. 获取论文结构
python scripts/chatxiv.py head 1706.03762 --with-paragraph-counts

# 4. 阅读所有主要章节
python scripts/chatxiv.py read 1706.03762 "Introduction"
python scripts/chatxiv.py read 1706.03762 "Model Architecture"
python scripts/chatxiv.py read 1706.03762 "Why Self-Attention"
python scripts/chatxiv.py read 1706.03762 "Results"
python scripts/chatxiv.py read 1706.03762 "Conclusion"

# 5. 撰写详细报告
# 创建 readings/<paper_id>_<slug>/report.md，包含结构化分析
# 包含：动机、方法、贡献、结果、优势、局限、影响
```

## CLI 命令参考

所有命令从项目根目录运行：

| 命令 | 用途 |
|------|------|
| `python scripts/chatxiv.py search "<查询>" --limit N [--topic "..."]` | 搜索论文。先查本地缓存，再调 DeepXiv。 |
| `python scripts/chatxiv.py brief <paper_id>` | 论文摘要：标题、TLDR、关键词、引用数、pdf、代码。 |
| `python scripts/chatxiv.py batch-brief <paper_id1> <paper_id2> ...` | 批量获取多篇论文的摘要（空格分隔）。 |
| `python scripts/chatxiv.py head <paper_id> [--with-paragraph-counts]` | 论文结构：摘要 + 章节列表及大小。 |
| `python scripts/chatxiv.py read <paper_id> "<章节名>" [--grep ... \| --range N:M \| --paragraphs N]` | 阅读章节，可选择精读特定段落。 |
| `python scripts/chatxiv.py local-find "<查询>"` | 仅搜索本地缓存（不调用 API）。 |
| `python scripts/chatxiv.py status <paper_id>` | 查看某篇论文的缓存状态。 |
| `python scripts/chatxiv.py download-pdf [<paper_id> ...]` | 将 PDF 下载到 `pdfs/`，文件名为 `<paper_id> - <标题>.pdf`。不带 ID 表示下载所有已缓存论文（完整性检查）。已存在的文件会被跳过。 |
| `python scripts/chatxiv.py topic create "<名称>"` | 创建新的调研主题文件夹。 |
| `python scripts/chatxiv.py topic list` | 列出所有主题。 |
| `python scripts/chatxiv.py topic show "<名称>"` | 查看主题详情和查询历史。 |
| `python scripts/chatxiv.py topic papers "<名称>"` | 列出主题下的论文。 |

### 常用参数

- `--local-only` — 不调用 DeepXiv，仅使用缓存数据。
- `--remote-only` — 跳过本地缓存，直接查询 DeepXiv。
- `--with-tldr` — 在搜索结果中显示 TLDR。
- `--with-paragraph-counts` — `head` 命令同时输出每个已缓存章节的段落数。
- `--topic "名称"` — 将搜索结果关联到某个主题。
- `--no-pdf` — 在 `search` 命令中，跳过自动下载新获取论文的 PDF。
- `--source biorxiv|medrxiv` — 搜索 bioRxiv 或 medRxiv。
- `--categories cs.CV,cs.AI` — 按 arXiv 类别过滤。
- `--date-from 2024-01` — 按发表日期过滤。
- `--min-citations 10` — 最低引用数。

## 硬性规则

1. **绝对不要** 直接打开或读取 `papers/*.json` 文件 — 可能包含全文，会撑爆上下文。
2. **必须** 使用 `python scripts/chatxiv.py` 命令来访问论文内容。
3. **必须** 先检查本地缓存。用 `local-find` 或 `status` 确认后再调用 DeepXiv。
4. **必须** 在开始调研前创建 topic。
5. **不要** 编造 paper ID。只使用搜索结果返回的 ID。
6. 搜索时使用 `--topic` 自动保存结果，默认 `--limit 100`。
7. 精读章节时优先用 `read --grep` / `read --range`，不要一次读整章。
8. 最终报告写在 `topics/<slug>/report.md` 中。
9. **报告命名**：始终输出单个报告文件：
   - 英文：`report.md`（主题调研和论文深读都用这个）
   - 其他语言：`report_<lang>.md`（如 `report_zh.md`、`report_es.md`、`report_fr.md`）
10. **报告语言**：始终检查 `.env` 中的 `REPORT_LANGUAGE` 并用该语言撰写。如用户明确要求不同语言，使用用户的要求。
11. **报告写入策略**：分多轮写入报告，而不是一次性全写：
    - **第一轮**：写入调研范围、领域全景、评估指标和 SOTA 部分
    - **第二轮**：写入按子领域的全景覆盖（组织论文，为 70-90% 的论文写 1-2 句话总结）
    - **第三轮**：写入关键论文与洞察（为 3-5 篇最重要的论文进行更深入的分析）
    - **第四轮**：写入领域演进、存在的空白与开放挑战、参考文献
    - 这样可以防止上下文溢出，并允许在任何轮次失败时恢复。

## 论文 JSON schema（缓存于 `papers/<paper_id>.json`）

每篇缓存论文使用以下规范字段（缺失值就不写入）：

- `paper_id` — 来源原生 ID（如 `2401.12345`）。
- `source` — `arxiv` / `biorxiv` / `medrxiv` 之一。
- `title`、`date`、`authors`、`categories`、`citation_count`。
- `tldr`、`abstract`、`keywords`。
- `url`、`pdf_url`、`code_url`（GitHub / 仓库链接，如果有）。
- `head` — DeepXiv `head` 返回的章节结构。
- `sections` — `{ 章节名: 全文 }`，由 `read` 命令填充。
- `fetched_at` — 每个字段/章节的获取时间戳。

## 报告模板

撰写调研报告时，遵循以下结构和语言规则：

**文件命名：**
- 英文：`topics/<slug>/report.md` 或 `readings/<paper_id>_<slug>/report.md`
- 其他语言：`topics/<slug>/report_<lang>.md` 或 `readings/<paper_id>_<slug>/report_<lang>.md`
  - 示例：`report_zh.md`、`report_es.md`、`report_fr.md`

**语言：** 始终检查 `.env` 中的 `REPORT_LANGUAGE` 并用该语言撰写报告。

**写入策略（分多轮）：**

分 4 轮写入报告，防止上下文溢出：

**第一轮：基础章节**
- 写入：调研范围、领域全景、评估指标和 SOTA
- 这些章节提供背景信息，不需要深入分析论文

**第二轮：全景论文覆盖**
- 写入：按子领域的全景覆盖
- 按子领域组织论文，为 70-90% 的论文写 1-2 句话总结
- 使用 brief 数据（标题、摘要、关键词、引用数）— 不需要深入阅读

**第三轮：关键洞察**
- 写入：关键论文与洞察
- 为 3-5 篇最重要的论文进行更深入的分析（每篇 2-3 段）
- 使用 `head` 和 `read` 命令获得的见解

**第四轮：综合与参考**
- 写入：领域演进与发展线、存在的空白与开放挑战、参考文献
- 综合研究发现并识别未来研究方向

**结构：**

```markdown
# <主题标题>

## 调研范围
搜索了什么、使用了哪些数据源、日期范围、过滤条件、找到的论文总数。

## 领域全景
主要子方向及其关系。3-5 段解释领域的结构。

## 按子领域的全景覆盖

按子领域或研究方向组织论文。对搜索结果中的**每篇相关论文**：

### <子领域名称>

**发展脉络**：描述该子领域的演进过程和关键发展（2-3 句话）。

#### <论文标题> (paper_id, 年份)
**[1-2 句话总结关键贡献]** 引用数：X

（按时间顺序或重要程度排列该子领域的所有论文）

**子领域总结**：连接各篇论文 - 展示该子领域如何演进、问题如何逐步解决、还存在什么挑战。

---

**格式示例：**
#### Attention Is All You Need (1706.03762, 2017)
**提出基于自注意力机制的 Transformer 架构，完全消除了循环和卷积。** 引用数：85,000+

#### BERT: Pre-training of Deep Bidirectional Transformers (1810.04805, 2018)
**将双向预训练应用于 Transformer，通过掩码语言建模在 11 个 NLP 任务上取得最先进的结果。** 引用数：45,000+

## 评估指标、基准和当前最高水平（SOTA）

对每个主要子领域或任务：

### <评估指标/基准名称>
- **标准基准/数据集**：该领域常用的数据集或评估协议
- **关键指标**：该领域使用的主要评估指标
- **当前最高水平**：最佳已知结果及对应论文/方法（含paper_id）
- **其他重要成果**：其他显著的性能水平及其含义

## 关键论文与洞察

对领域内最重要或最具奠基意义的 3-5 篇论文：

### <论文标题> (paper_id)
- **为什么重要**：它在领域发展中的角色
- **核心理念**：引入的关键概念或方法
- **主要发现**：最重要的结果
- **影响力**：如何影响了后续工作、哪些论文在其基础上构建
- **局限与开放问题**：未解决的问题、留下的空白

## 领域演进与发展线

描述主要研究方向及领域如何演进：
- 早期奠基工作及其关键贡献
- 关键转折点（新方法、新数据集、新问题表述）
- 当前研究前沿和开放挑战
- 有前景的未来研究方向

## 存在的空白与开放挑战

哪些问题仍未解决或探索不足：
- 现有方案中的技术空白
- 数据集或评估的局限
- 计算效率的挑战
- 实际应用的问题

## 参考文献
完整论文列表（含元数据）— 见本主题文件夹中的 papers.jsonl。
```

**全景覆盖的指导原则：**
- **目标**：总结搜索结果中**尽可能多的相关论文**（约 70-90% 的 100 篇论文）
- **组织方式**：按研究方向、方法类型或问题表述分组论文，便于理解
- **每篇论文的格式**：每篇论文条目：1-2 句话描述关键贡献 + 引用数
  - 示例：`**论文标题 (paper_id, 年份)** — [1-2 句话总结]。引用数：X`
  - 重点是：有什么新东西、如何与他人不同、关键结果
- **发展叙述**：对每个子领域，包含 1-2 句话描述该领域如何演进、论文之间如何关联
- **优先级**：用搜索结果顺序和引用数量排列论文；先列奠基论文
- **关键论文的深度**：对 ~10 篇最重要/最具奠基意义的论文，使用 head 和 read 的见解提供更深入的分析（每篇 2-3 段）
- **指标与 SOTA**：清晰阐述评估景观 — 什么指标重要、哪些基准是标准的、当前最佳结果是什么
- **综合**：将论文连接成连贯的叙述 — 展示进展、创新、权衡和演进过程
- **目标**：创建**完整的领域地图**，让读者理解景观、主要发展、关键思想、最高水平和开放问题

## Token 配额意识

- DeepXiv 匿名 token：1,000 次/天
- 注册 token：10,000 次/天
- `search` = 每次调用 1 次请求（最多返回 100 篇）
- `brief` / `head` / `read`（缓存未命中）= 各 1 次请求
- 一旦获取，数据永久缓存在本地 — 不会重复消耗配额。

策略：一次搜索用 `--limit 100`，然后只对真正需要的论文选择性获取 brief、用 `read --grep` 精读。

## 报告语言配置

`.env` 文件包含报告生成的配置设置：

### REPORT_LANGUAGE
控制生成报告的语言：

```
REPORT_LANGUAGE=en
```

**支持的语言：**
- `en` — 英文（默认）
- `zh` — 中文
- `es` — 西班牙语
- `fr` — 法文
- `de` — 德文
- `ja` — 日文

**按语言命名报告文件：**
- 英文（`en`）：`report.md`
- 中文（`zh`）：`report_zh.md`
- 西班牙文（`es`）：`report_es.md`
- 法文（`fr`）：`report_fr.md`
- 德文（`de`）：`report_de.md`
- 日文（`ja`）：`report_ja.md`

### SEARCH_LIMIT
控制进行调研时搜索的论文数量：

```
SEARCH_LIMIT=100
```

默认为每个调研主题搜索 100 篇论文。你可以调整这个值来搜索更少或更多的论文。

**撰写报告时，始终：**
1. 检查 `.env` 中的 `REPORT_LANGUAGE` 设置，并用该语言生成报告
2. 检查 `SEARCH_LIMIT` 设置，并将其用作主题调研的默认搜索限制
3. 根据语言用适当的文件名保存报告
4. 如果用户明确要求不同的语言或搜索限制，使用用户的要求代替

若要改变设置，编辑 `.env` 并更新值，然后根据需要重新生成报告。

## 环境配置

项目从项目根目录的 `.env` 读取 `DEEPXIV_TOKEN`，如果没有则回退到 `~/.env`。

- **方式 1**：将 `.env.example` 复制为 `.env` 并填入你的 token（在 https://data.rag.ac.cn/register 注册可获得 10,000 次/天）
- **方式 2**：留空 `.env`。DeepXiv SDK 会在首次使用时自动注册匿名 token（1,000 次/天）并保存到 `~/.env`。之后你可以把那个 token 复制到本项目的 `.env` 中以便版本管理。
