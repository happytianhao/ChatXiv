# ChatXiv

**本地管理、Agent 原生的文献调研阅读助手，基于 [DeepXiv](https://github.com/DeepXiv/deepxiv_sdk) 构建。**

像和 arxiv 对话一样做文献调研：搜索、阅读、理解、整理 —— 全部在本地完成。ChatXiv 是一个即用型项目文件夹。克隆后用 Claude Code / Cursor / 任何 AI 编程工具打开，直接让 AI 帮你调研某个研究方向。AI 会读取 `CLAUDE.md`，按照工作流搜索论文、缓存到本地、撰写结构化调研报告 — 所有获取过的论文都缓存在本地，不会重复消耗 API 配额。

- **📖 English docs**: [README.md](README.md)

---

## 特性

- **本地优先**：论文以 JSON 文件缓存在本地。后续查询优先命中本地缓存，再决定是否调用 DeepXiv。
- **本地部署**：无需服务器、无需云存储、无需鉴权 —— 一份 Python 脚本加一个文件夹就够了。
- **本地文献管理**：每个主题一个文件夹，每篇论文一个 JSON 文件。纯文件，无迁移。
- **Agent 原生**：为 Claude Code、Cursor、Windsurf 等读取 `CLAUDE.md` 的 AI 编程工具设计。
- **渐进式披露**：AI 不会直接读取原始 JSON 文件。CLI 逐层暴露内容（brief → head → read 段落）。
- **分层数据收集**：高效地为所有论文获取摘要，然后有选择性地为候选论文获取结构和深度阅读。
- **批量操作**：`batch-brief` 命令一次性获取多篇论文的元数据，实现全景覆盖。
- **全景覆盖报告**：生成 related work 风格的报告，覆盖 70-90% 的搜索结果，每篇论文 1-2 句话总结 + 引用数。
- **两种工作流**：
  - **主题调研**：用约 100 篇论文调研某个研究方向，撰写全景覆盖的结构化报告。
  - **论文深读**：深入理解某篇论文，撰写详细解读。
- **按主题组织**：每个调研任务有独立文件夹，包含论文列表和报告模板。

## 快速开始

### 1. 克隆

```bash
git clone https://github.com/happytianhao/ChatXiv.git
cd ChatXiv
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或使用 [uv](https://github.com/astral-sh/uv)：

```bash
uv pip install -r requirements.txt
```

### 3. 配置 token（可选）

```bash
cp .env.example .env
# 编辑 .env，填入你的 DeepXiv token。
# 在 https://data.rag.ac.cn/register 注册可获得 10,000 次/天。
#
# 或者跳过此步 — DeepXiv SDK 会在首次使用时自动注册匿名 token
#（1,000 次/天）并保存到 ~/.env。
# 之后你可以把那个 token 复制到本项目的 .env 中。
```

### 4. 在 AI 工具中打开

用 Claude Code、Cursor 或任何支持 `CLAUDE.md` 的工具打开此文件夹，然后输入：

**主题调研：**
> "帮我调研自动驾驶世界模型方向"

AI 会自动：
1. 在 `topics/` 下创建主题文件夹
2. 通过 DeepXiv 搜索约 100 篇论文
3. 使用 `batch-brief` 为所有论文获取摘要（轻量级元数据）
4. 为最有前景的 ~30 篇论文获取结构（`head`）
5. 深入阅读最重要的 ~10 篇论文（`read`）以获取详细见解
6. 在 `topics/<slug>/report.md` 中撰写全景覆盖的报告
   - 每篇论文：1-2 句话总结 + 引用数（like related work）
   - 最重要的 ~10 篇论文：更深入的分析（2-3 段）

**论文深读：**
> "详细解读 Transformer 论文（1706.03762）"

AI 会自动：
1. 在 `readings/` 下创建阅读文件夹
2. 获取论文元数据和结构
3. 阅读所有主要章节
4. 在 `readings/<paper_id>_<slug>/report.md` 中撰写详细分析
   - 结构化章节：研究动机、方法、贡献、结果、优势、局限、影响

所有获取的数据缓存在 `papers/` 中 — 以后的查询直接复用，不消耗 API 配额。

---

## 项目结构

```
ChatXiv/
├── CLAUDE.md            # AI agent 指令（英文）
├── CLAUDE.zh.md         # AI agent 指令（中文）
├── README.md            # 英文 README
├── README.zh.md         # 本文件
├── .env.example         # Token 配置模板
├── .gitignore
├── LICENSE              # MIT
├── requirements.txt     # Python 依赖
├── papers/              # 本地论文缓存（每篇论文一个 JSON）
├── topics/              # 调研主题（每个主题一个文件夹）
│   └── <slug>/
│       ├── topic.json   # 元数据、查询历史
│       ├── papers.jsonl # 本主题的论文列表
│       └── report.md   # 调研报告
├── readings/            # 论文深读（每篇论文一个文件夹）
│   └── <paper_id>_<slug>/
│       └── report.md    # 论文详细分析
└── scripts/
    ├── chatxiv.py       # 主 CLI 入口
    └── lib/             # 内部模块
        ├── config.py
        ├── deepxiv_client.py
        ├── format.py
        ├── store.py
        └── topics.py
```

## CLI 使用

也可以直接在终端使用 CLI：

```bash
# 搜索约 100 篇论文
python scripts/chatxiv.py search "world models" --limit 100

# 批量获取多篇论文的摘要（空格分隔）
python scripts/chatxiv.py batch-brief 2401.12345 2402.54321 2403.99999

# 获取论文摘要
python scripts/chatxiv.py brief 2401.12345

# 查看论文结构（带段落数）
python scripts/chatxiv.py head 2401.12345 --with-paragraph-counts

# 阅读某个章节，或精读特定段落
python scripts/chatxiv.py read 2401.12345 "Method"
python scripts/chatxiv.py read 2401.12345 "Method" --grep "diffusion"
python scripts/chatxiv.py read 2401.12345 "Experiments" --range 0:3

# 仅搜索本地缓存
python scripts/chatxiv.py local-find "transformer"

# 管理主题
python scripts/chatxiv.py topic create "我的调研主题"
python scripts/chatxiv.py topic list
python scripts/chatxiv.py topic papers "我的调研主题"
```

## 工作原理

```
用户提出调研问题
        │
        ▼
AI 读取 CLAUDE.md → 理解分层数据收集策略
        │
        ▼
python scripts/chatxiv.py search "..." --limit 100 --topic "..."
        │
        ├── 检查 papers/ 本地缓存
        │       │
        │       ▼ （结果不够）
        │
        ├── 调用 DeepXiv API
        │       │
        │       ▼
        │   保存新论文到 papers/<paper_id>.json
        │
        ▼
第一阶段：分层数据收集
        │
        ├─ python scripts/chatxiv.py batch-brief <所有 ~100 篇论文 ID>
        │       ▼ （轻量级：标题、摘要、关键词、引用数）
        │
        ├─ python scripts/chatxiv.py head <最有前景的 ~30 篇论文>
        │       ▼ （章节结构）
        │
        └─ python scripts/chatxiv.py read <最重要的 ~10 篇论文> "章节" --grep "..."
                ▼ （详细见解）
        │
        ▼
第二阶段：撰写报告
        │
        ├─ 按子领域组织论文
        ├─ 为 70-90% 的论文撰写 1-2 句话总结（使用 brief 数据）
        ├─ 为 ~10 篇关键论文添加更深入的分析（2-3 段）
        └─ 包含评估指标、SOTA 和领域演进
        │
        ▼
AI 撰写全景覆盖报告 → topics/<slug>/report.md
```

## 工作原理（论文深读）

```
用户提出深读请求
        │
        ▼
AI 读取 CLAUDE.md → 理解论文深读工作流
        │
        ▼
python scripts/chatxiv.py brief 1706.03762
python scripts/chatxiv.py head 1706.03762 --with-paragraph-counts
        │
        ├── 检查 papers/ 本地缓存
        │       │
        │       ▼ （缓存未命中）
        │
        ├── 调用 DeepXiv API
        │       │
        │       ▼
        │   保存到 papers/1706.03762.json
        │
        ▼
AI 阅读所有主要章节
        │
        ▼
python scripts/chatxiv.py read 1706.03762 "Introduction"
python scripts/chatxiv.py read 1706.03762 "Model Architecture"
python scripts/chatxiv.py read 1706.03762 "Why Self-Attention"
python scripts/chatxiv.py read 1706.03762 "Results"
        │
        ▼
AI 撰写详细分析 → readings/1706.03762_transformer/report.md
```

## 系统要求

- Python 3.10+
- `deepxiv-sdk >= 0.2.4`

## 许可证

MIT — 见 [LICENSE](LICENSE)。

## 致谢

- [DeepXiv](https://github.com/DeepXiv/deepxiv_sdk) — 为本项目提供论文搜索和渐进式阅读引擎。
