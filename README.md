# ChatXiv

**Locally-managed, agent-native literature research and reading assistant powered by [DeepXiv](https://github.com/DeepXiv/deepxiv_sdk).**

Like chatting with arxiv: search, read, understand, and organize the literature — all locally. ChatXiv is a ready-to-use project folder. Clone it, open it in Claude Code / Cursor / any AI coding tool, and ask the AI to survey a research field. The AI reads `CLAUDE.md`, follows the workflow, and produces a structured research report — all while caching papers locally so you never waste API quota on repeated lookups.

- **📖 中文文档**: [README.zh.md](README.zh.md)

---

## Features

- **Local-first**: papers are cached as JSON files. Subsequent queries hit the local cache before calling DeepXiv.
- **Local deployment**: no server, no cloud DB, no auth — just Python and a folder of JSON files.
- **Local literature management**: each topic/reading is a folder; each paper is a JSON file. Plain files, no migrations.
- **Agent-native**: designed for Claude Code, Cursor, Windsurf, or any LLM-powered coding tool that reads `CLAUDE.md`.
- **Progressive disclosure**: the AI never reads raw paper files. The CLI exposes content layer by layer (brief → head → read paragraph).
- **Tiered data collection**: efficiently fetch briefs for all papers, then selectively fetch structure and deep reads for top candidates.
- **Batch operations**: `batch-brief` command to fetch metadata for multiple papers at once, enabling comprehensive coverage.
- **Comprehensive reports**: generate related-work style reports covering 70-90% of search results with 1-2 sentence summaries per paper + citations.
- **Two workflows**:
  - **Topic Research**: survey a research field with ~100 papers, write a structured report with comprehensive coverage.
  - **Paper Reading**: deep-dive into a single paper, write a comprehensive explanation.
- **Topic-oriented & Reading-oriented**: each research task or paper gets its own folder with metadata and output.

## Quick Start

### 1. Clone

```bash
git clone https://github.com/happytianhao/ChatXiv.git
cd ChatXiv
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv pip install -r requirements.txt
```

### 3. Configure token (optional)

```bash
cp .env.example .env
# Edit .env and paste your DeepXiv token.
# Get one at https://data.rag.ac.cn/register (10,000 requests/day).
#
# Or skip this step — DeepXiv SDK will auto-register an anonymous token
# (1,000 requests/day) on first use and save it to ~/.env.
# You can then copy that token to this project's .env if needed.
```

### 4. Open in your AI tool

Open this folder in Claude Code, Cursor, or any tool that reads `CLAUDE.md`. Then ask:

**For topic research:**
> "Help me survey the field of world models for autonomous driving."

The AI will:
1. Create a topic folder under `topics/`
2. Search DeepXiv for ~100 papers
3. Fetch briefs for ALL papers using `batch-brief` (lightweight metadata)
4. Fetch structure (`head`) for ~30 most promising papers
5. Deep-read (`read`) ~10 most important papers for detailed insights
6. Write a comprehensive report covering 70-90% of papers in `topics/<slug>/report.md`
   - Each paper: 1-2 sentence summary + citation count (like a related work section)
   - Deeper analysis (2-3 paragraphs) for ~10 key papers

**For paper reading:**
> "Explain the Transformer paper (1706.03762) in detail."

The AI will:
1. Create a reading folder under `readings/`
2. Fetch paper metadata and structure
3. Read all major sections
4. Write a comprehensive report in `readings/<paper_id>_<slug>/report.md`
   - Structured sections: Motivation, Methodology, Contributions, Results, Strengths, Limitations, Impact

All fetched data is cached in `papers/` — future queries reuse it without API calls.

---

## Project Structure

```
ChatXiv/
├── CLAUDE.md            # Instructions for the AI agent (English)
├── CLAUDE.zh.md         # Instructions for the AI agent (Chinese)
├── README.md            # This file
├── README.zh.md         # Chinese README
├── .env.example         # Token configuration template
├── .gitignore
├── LICENSE              # MIT
├── requirements.txt     # Python dependencies
├── papers/              # Local paper cache (one JSON per paper)
├── topics/              # Research topics (one folder per topic)
│   └── <slug>/
│       ├── topic.json   # Metadata, query history
│       ├── papers.jsonl # Paper list for this topic
│       └── report.md    # Research report
├── readings/            # Paper readings (one folder per paper)
│   └── <paper_id>_<slug>/
│       └── report.md    # Comprehensive paper analysis
└── scripts/
    ├── chatxiv.py       # Main CLI entry point
    └── lib/             # Internal modules
        ├── config.py
        ├── deepxiv_client.py
        ├── format.py
        ├── store.py
        └── topics.py
```

## CLI Usage

You can also use the CLI directly from the terminal:

### Search & Browse

```bash
# Search ~100 papers
python scripts/chatxiv.py search "world models" --limit 100

# Batch-fetch briefs for multiple papers (space-separated)
python scripts/chatxiv.py batch-brief 2401.12345 2402.54321 2403.99999

# Get paper brief (title, TLDR, keywords, citations)
python scripts/chatxiv.py brief 2401.12345

# View paper structure (with paragraph counts)
python scripts/chatxiv.py head 2401.12345 --with-paragraph-counts

# Read a section, or zoom into specific paragraphs
python scripts/chatxiv.py read 2401.12345 "Method"
python scripts/chatxiv.py read 2401.12345 "Method" --grep "diffusion"
python scripts/chatxiv.py read 2401.12345 "Experiments" --range 0:3

# Search local cache only (no API calls)
python scripts/chatxiv.py local-find "transformer"

# Check what's cached for a paper
python scripts/chatxiv.py status 2401.12345
```

### Topic Management

```bash
# Create a new research topic
python scripts/chatxiv.py topic create "My Research Topic"

# List all topics
python scripts/chatxiv.py topic list

# Show topic details
python scripts/chatxiv.py topic show "My Research Topic"

# List papers in a topic
python scripts/chatxiv.py topic papers "My Research Topic"
```

## How It Works

### Workflow 1: Topic Research (Survey)

```
User asks: "Survey world models for autonomous driving"
        │
        ▼
AI reads CLAUDE.md → understands tiered data collection strategy
        │
        ▼
python scripts/chatxiv.py topic create "World Models for AD"
python scripts/chatxiv.py search "world models autonomous driving" --limit 100 --topic "..."
        │
        ├── Check papers/ for local matches
        │       │
        │       ▼ (not enough results)
        │
        ├── Call DeepXiv API
        │       │
        │       ▼
        │   Save new papers to papers/<paper_id>.json
        │
        ▼
Phase 1: Tiered Data Collection
        │
        ├─ python scripts/chatxiv.py batch-brief <all ~100 paper_ids>
        │       ▼ (lightweight: title, TLDR, keywords, citations)
        │
        ├─ python scripts/chatxiv.py head <~30 most promising papers>
        │       ▼ (section structure)
        │
        └─ python scripts/chatxiv.py read <~10 most important papers> "Section" --grep "..."
                ▼ (detailed insights)
        │
        ▼
Phase 2: Report Writing
        │
        ├─ Organize papers by sub-area
        ├─ Write 1-2 sentence summaries for 70-90% of papers (using brief data)
        ├─ Add deeper analysis (2-3 paragraphs) for ~10 key papers
        └─ Include evaluation metrics, SOTA, and field evolution
        │
        ▼
AI writes comprehensive report → topics/<slug>/report.md
```

### Workflow 2: Paper Reading (Deep Dive)

```
User asks: "Explain the Transformer paper in detail"
        │
        ▼
AI reads CLAUDE.md → understands paper reading workflow
        │
        ▼
python scripts/chatxiv.py brief 1706.03762
python scripts/chatxiv.py head 1706.03762 --with-paragraph-counts
        │
        ├── Check papers/ for cached content
        │       │
        │       ▼ (cache miss)
        │
        ├── Call DeepXiv API
        │       │
        │       ▼
        │   Save to papers/1706.03762.json
        │
        ▼
AI reads all major sections
        │
        ▼
python scripts/chatxiv.py read 1706.03762 "Introduction"
python scripts/chatxiv.py read 1706.03762 "Model Architecture"
python scripts/chatxiv.py read 1706.03762 "Why Self-Attention"
python scripts/chatxiv.py read 1706.03762 "Results"
        │
        ▼
AI writes comprehensive explanation → readings/1706.03762_transformer/report.md
```

## Requirements

- Python 3.10+
- `deepxiv-sdk >= 0.2.4`

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgments

- [DeepXiv](https://github.com/DeepXiv/deepxiv_sdk) — the paper search and progressive reading engine that powers this project.
