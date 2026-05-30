# ChatXiv

A local-first, progressive-disclosure research assistant — built on [DeepXiv](https://github.com/DeepXiv/deepxiv_sdk), arxiv-friendly, fully local. When you receive a research request (e.g. "survey world models for autonomous driving"), follow the workflow below using the CLI scripts in `scripts/`.

## Principles

1. **Local-first** — always check `papers/` cache before calling DeepXiv. API quota is limited.
2. **Progressive disclosure** — never read `papers/*.json` directly. Use the CLI to retrieve only what you need at each step.
3. **Two workflows**:
   - **Topic-oriented** — for surveying a research area. Create a topic, search ~100 papers, write a report.
   - **Reading-oriented** — for deep-diving into a single paper. Create a reading, fetch full content, write detailed explanation.
4. **Bounded output** — the CLI prints concise summaries. Full paper text stays on disk, not in your context.
5. **One topic ≈ 100 papers** — by default, search ~100 papers per topic, then progressively narrow down.
6. **One reading ≈ 1 paper** — deep explanation with full sections, code walkthrough, and synthesis.

## Workflows

### Workflow 1: Topic Research (Survey)

When a user asks you to research a topic, use a **two-phase approach**:

**Phase 1: Tiered Data Collection** (progressively deeper fetches for different paper tiers)
```
1. Create a topic
2. Search ~100 papers (local-first, then DeepXiv)
3. Fetch `brief` for ALL ~100 papers using batch-brief
   - python scripts/chatxiv.py batch-brief <paper_id1> <paper_id2> ... <paper_id100>
   - Provides: title, TLDR, keywords, citation_count, year
   - This is the PRIMARY SOURCE for report writing
   - Lightweight and cached forever
4. Fetch `head` (section structure) for ~30 most promising papers
   - Helps identify key sections and paper scope
5. Use `read` to deeply read ~10 most important papers
   - Read key sections with --grep / --range as needed
   - Extract detailed insights for "Key Papers & Insights" section
```

**Phase 2: Report Writing** (comprehensive coverage like a related work section)
```
6. Organize papers by sub-area or research direction
7. Write report summaries for ~70-90% of the papers using brief data
   - Each paper: 1-2 sentences describing key contribution + citation marker
   - Format: **Paper Title (paper_id, Year)** — [1-2 sentence summary]. [Citation count: X]
   - Use title, TLDR, keywords, citation_count from briefs
   - Connect papers into development narratives (evolution, sequential problem-solving)
8. For ~10 most important papers: include deeper analysis (2-3 sentences) using head/read insights
9. Synthesize final report in topics/<slug>/report.md with all sections completed
```

**Key Principle**: Comprehensive coverage (70-90% of papers) with lightweight summaries; deep reads only for top 10 papers.

### Workflow 2: Paper Reading (Deep Dive)

When a user asks you to explain or deeply understand a single paper:

```
1. Create a reading folder: readings/<paper_id>_<slug>/
2. Fetch brief to get metadata
3. Fetch head to get full structure
4. Read all major sections (or key sections)
5. Write comprehensive explanation in readings/<paper_id>_<slug>/report.md (NOT explanation.md)
6. Structure the report with these sections:
   - Research Motivation & Problem Statement
   - Core Methodology & Architecture
   - Key Technical Contributions
   - Experimental Results & Evaluation
   - Strengths & Limitations
   - Impact & Future Directions
   - Related Work (if applicable)
```

**Key Point**: Use `report.md` for paper reading output, same as topic research. This ensures consistency across all research outputs.

### Step-by-step (Topic Research)

```bash
# 1. Create topic
python scripts/chatxiv.py topic create "World Models for Autonomous Driving"

# 2. Search ~100 papers — attaches results to the topic automatically
python scripts/chatxiv.py search "world models autonomous driving" --limit 100 --topic "World Models for Autonomous Driving"

# 3. Extract paper IDs from search results (copy the paper_id column)

# 4. Fetch briefs for ALL ~100 papers using batch-brief
python scripts/chatxiv.py batch-brief 2507.12762 2008.00334 2108.00273 2409.01256 1804.02675 2108.01599 2605.00051 2502.18496 2604.09305 2212.04677 2511.08640 2007.14232 2308.15985 2507.12755 2007.00101 2212.09381 2407.16277 2506.10002 2511.06226 ...

# 5. Check structure of ~30 most promising papers
python scripts/chatxiv.py head 2507.12762 --with-paragraph-counts
python scripts/chatxiv.py head 2008.00334 --with-paragraph-counts
# ... repeat for ~30 papers

# 6. Read specific sections of ~10 most important papers
python scripts/chatxiv.py read 2507.12762 "Method"
python scripts/chatxiv.py read 2507.12762 "Experiments" --range 0:3
python scripts/chatxiv.py read 2008.00334 "Introduction"
# ... repeat for ~10 papers

# 7. Write the report
# Edit topics/<slug>/report.md with your synthesis using brief data + deeper insights from head/read
```

### Step-by-step (Paper Reading)

```bash
# 1. Create reading folder
python scripts/chatxiv.py topic create "Transformer Paper"  # Creates readings/<paper_id>_<slug>/ structure

# 2. Fetch paper metadata
python scripts/chatxiv.py brief 1706.03762

# 3. Get paper structure
python scripts/chatxiv.py head 1706.03762 --with-paragraph-counts

# 4. Read all major sections
python scripts/chatxiv.py read 1706.03762 "Introduction"
python scripts/chatxiv.py read 1706.03762 "Model Architecture"
python scripts/chatxiv.py read 1706.03762 "Why Self-Attention"
python scripts/chatxiv.py read 1706.03762 "Results"
python scripts/chatxiv.py read 1706.03762 "Conclusion"

# 5. Write comprehensive report
# Create readings/<paper_id>_<slug>/report.md with structured analysis
# Include: Motivation, Methodology, Contributions, Results, Strengths, Limitations, Impact
```

## CLI Reference

All commands are run from the project root:

| Command | Purpose |
|---------|---------|
| `python scripts/chatxiv.py search "<query>" --limit N [--topic "..."]` | Search papers. Checks local cache first, then calls DeepXiv. |
| `python scripts/chatxiv.py brief <paper_id>` | Paper summary: title, TLDR, keywords, citations, pdf, code. |
| `python scripts/chatxiv.py batch-brief <paper_id1> <paper_id2> ...` | Fetch briefs for multiple papers at once (space-separated). |
| `python scripts/chatxiv.py head <paper_id> [--with-paragraph-counts]` | Paper structure: abstract + section list with sizes. |
| `python scripts/chatxiv.py read <paper_id> "<Section>" [--grep ... \| --range N:M \| --paragraphs N]` | Read a section, optionally zoom into specific paragraphs. |
| `python scripts/chatxiv.py local-find "<query>"` | Search local cache only (no API calls). |
| `python scripts/chatxiv.py status <paper_id>` | Show what's cached for a paper. |
| `python scripts/chatxiv.py topic create "<name>"` | Create a new research topic folder. |
| `python scripts/chatxiv.py topic list` | List all topics. |
| `python scripts/chatxiv.py topic show "<name>"` | Show topic metadata and query history. |
| `python scripts/chatxiv.py topic papers "<name>"` | List papers attached to a topic. |

### Useful flags

- `--local-only` — never call DeepXiv, only use cached data.
- `--remote-only` — skip local cache, always query DeepXiv.
- `--with-tldr` — include TLDR in search result listings.
- `--with-paragraph-counts` — on `head`, also show paragraph count per cached section.
- `--topic "Name"` — attach search results to a topic.
- `--source biorxiv|medrxiv` — search bioRxiv or medRxiv instead of arXiv.
- `--categories cs.CV,cs.AI` — filter by arXiv categories.
- `--date-from 2024-01` — filter by publication date.
- `--min-citations 10` — minimum citation count.

## Hard Rules

1. **NEVER** open or read `papers/*.json` files directly — they may contain full paper text that will overflow your context.
2. **ALWAYS** use `python scripts/chatxiv.py` commands to access paper content.
3. **ALWAYS** check local cache first. Use `local-find` or `status` before calling DeepXiv.
4. **For topics**: Create a topic before starting a research task.
5. **For readings**: Create a reading folder before starting a deep-dive explanation.
6. **DO NOT** fabricate paper IDs. Only use IDs returned by search results.
7. When searching, use `--topic` to persist results automatically. Default `--limit 100`.
8. To zoom into a section, prefer `read --grep` / `read --range` over reading the whole section.
9. **Report naming**: Always output a single report file named:
   - `report.md` if `REPORT_LANGUAGE=en` (for both topic research and paper reading)
   - `report_<lang>.md` for other languages (e.g., `report_zh.md`, `report_es.md`, `report_fr.md`)
10. **Report language**: Always check `REPORT_LANGUAGE` in `.env` and generate the report in that language. If user explicitly requests a different language, use their request instead.
11. **Report writing strategy**: Write reports in multiple passes, not all at once:
    - **Pass 1**: Write Scope, Landscape, and Evaluation Metrics sections
    - **Pass 2**: Write Comprehensive Paper Coverage by Sub-area (organize papers, write 1-2 sentence summaries)
    - **Pass 3**: Write Key Papers & Insights (deeper analysis for 3-5 most important papers)
    - **Pass 4**: Write Field Evolution, Gaps & Open Challenges, and References
    - This prevents context overflow and allows recovery if any pass fails.

## Paper JSON schema (cached in `papers/<paper_id>.json`)

Each cached paper uses these canonical fields (missing values are simply absent):

- `paper_id` — the source-native identifier (e.g. `2401.12345`).
- `source` — one of `arxiv`, `biorxiv`, `medrxiv`.
- `title`, `date`, `authors`, `categories`, `citation_count`.
- `tldr`, `abstract`, `keywords`.
- `url`, `pdf_url`, `code_url` (GitHub / repo link, when available).
- `head` — section structure as returned by DeepXiv `head`.
- `sections` — `{ section_name: full_text }` populated by `read`.
- `fetched_at` — timestamps recording when each field/section was fetched.

## Report Template

When writing a research report, follow this structure and language rules:

**File naming:**
- English: `topics/<slug>/report.md` or `readings/<paper_id>_<slug>/report.md`
- Other languages: `topics/<slug>/report_<lang>.md` or `readings/<paper_id>_<slug>/report_<lang>.md`
  - Example: `report_zh.md`, `report_es.md`, `report_fr.md`

**Language:** Always check `REPORT_LANGUAGE` in `.env` and write the report in that language.

**Writing Strategy (Multiple Passes):**

Write the report in 4 separate passes to prevent context overflow:

**Pass 1: Foundation Sections**
- Write: Scope, Landscape, Evaluation Metrics & SOTA
- These sections provide context and don't require deep paper analysis

**Pass 2: Comprehensive Paper Coverage**
- Write: Comprehensive Paper Coverage by Sub-area
- Organize papers by sub-area, write 1-2 sentence summaries for 70-90% of papers
- Use brief data (title, TLDR, keywords, citations) — no deep reading needed

**Pass 3: Key Insights**
- Write: Key Papers & Insights
- Deeper analysis (2-3 paragraphs each) for 3-5 most important papers
- Use insights from `head` and `read` commands

**Pass 4: Synthesis & References**
- Write: Field Evolution & Development Line, Gaps & Open Challenges, References
- Synthesize findings and identify future directions

**Structure:**

```markdown
# <Topic Title>

## Scope
What was searched, which sources, date range, filters, total papers found.

## Landscape
Major sub-areas and how they relate. 3-5 paragraphs explaining the field structure.

## Comprehensive Paper Coverage by Sub-area

Organize papers by sub-area or research direction. For **each relevant paper** found in search results:

### <Sub-area Name>

**Overview**: Describe the evolution and key developments in this sub-area (2-3 sentences).

#### <Paper Title> (paper_id, Year)
**[1-2 sentence summary of key contribution]** Citations: X

(Repeat for all papers in this sub-area, organized chronologically or by importance)

**Sub-area Synthesis**: Connect the papers - show how this sub-area evolved, what problems were solved sequentially, what challenges remain.

---

**Format Example:**
#### Attention Is All You Need (1706.03762, 2017)
**Introduces the Transformer architecture based on self-attention mechanisms, eliminating recurrence and convolution entirely.** Citations: 85,000+

#### BERT: Pre-training of Deep Bidirectional Transformers (1810.04805, 2018)
**Applies bidirectional pre-training to Transformers, achieving state-of-the-art results on 11 NLP tasks through masked language modeling.** Citations: 45,000+

## Evaluation Metrics, Benchmarks & SOTA

For each major sub-area or task:

### <Metric/Benchmark Name>
- **Standard Benchmarks/Datasets**: List commonly-used datasets or evaluation protocols
- **Key Metrics**: Primary evaluation metrics used in this area
- **Current SOTA**: Best-known results, by which papers/methods (with paper_id)
- **Notable Results**: Other significant performance levels and their implications

## Key Papers & Insights

For 3-5 most important/seminal papers in the field:

### <Paper Title> (paper_id)
- **Why It Matters**: Its role in the field's development
- **Core Ideas**: Key concepts or methods introduced
- **Key Findings**: Most important results
- **Impact/Influence**: How it shaped subsequent work, which papers built on it
- **Limitations/Open Questions**: What it didn't solve, what gaps it left

## Field Evolution & Development Line

Describe the major research directions and how the field evolved:
- Early foundational work and their key contributions
- Key turning points (new methods, datasets, problem formulations)
- Current research frontiers and open challenges
- Promising directions for future work

## Gaps & Open Challenges

What problems remain unsolved or underexplored:
- Technical gaps in existing approaches
- Dataset or evaluation limitations
- Computational efficiency challenges
- Real-world applicability issues

## References
Full paper list (with metadata) — see papers.jsonl in this topic folder.
```

**Guidelines for Comprehensive Coverage:**
- **Aim**: Summarize **as many relevant papers as possible** from the search results (~70-90% of the 100 papers)
- **Organization**: Group papers by research direction, method type, or problem formulation for clarity
- **Format Per Paper**: Each paper entry: 1-2 sentences describing key contribution + citation count
  - Example: `**Paper Title (paper_id, Year)** — [1-2 sentence summary]. Citations: X`
  - Focus on: what's new, how it differs from prior work, key results
- **Development Narrative**: For each sub-area, include 1-2 sentences describing how the area evolved and how papers relate to each other
- **Prioritization**: Use search result order and citation counts to order papers; include seminal papers first
- **Depth for Key Papers**: For ~10 most important/foundational papers, provide deeper analysis (2-3 paragraphs each) using insights from `head` and `read`
- **Metrics & SOTA**: Clearly articulate the evaluation landscape — what metrics matter, which benchmarks are standard, what the current best results are
- **Synthesis**: Connect papers into a coherent narrative — show the progression, innovations, trade-offs, and evolution
- **Goal**: Create a **complete field map** where readers understand the landscape, the major developments, the key ideas, the state-of-the-art, and the open questions

## Token Budget Awareness

- DeepXiv anonymous token: 1,000 requests/day
- Registered token: 10,000 requests/day
- `search` = 1 request per call (returns up to 100 papers)
- `brief` / `head` / `read` (cache miss) = 1 request each
- Once fetched, data is cached locally forever — no repeat cost.

Strategy: search once with `--limit 100`, then selectively fetch briefs and `read --grep` only for papers you actually need.

## Environment

The project reads `DEEPXIV_TOKEN` from `.env` in the project root, or falls back to `~/.env`.

- **Option 1**: Copy `.env.example` to `.env` and paste your token (get one at https://data.rag.ac.cn/register for 10,000 requests/day)
- **Option 2**: Leave `.env` empty. DeepXiv SDK will auto-register an anonymous token (1,000 requests/day) on first use and save it to `~/.env`. You can then copy that token to this project's `.env` if you want to version it.

## Report Language Configuration

The `.env` file contains configuration settings for report generation:

### REPORT_LANGUAGE
Controls the language of generated reports:

```
REPORT_LANGUAGE=en
```

**Supported languages:**
- `en` — English (default)
- `zh` — 中文 (Chinese)
- `es` — Español (Spanish)
- `fr` — Français (French)
- `de` — Deutsch (German)
- `ja` — 日本語 (Japanese)

**Report file naming by language:**
- English (`en`): `report.md`
- Chinese (`zh`): `report_zh.md`
- Spanish (`es`): `report_es.md`
- French (`fr`): `report_fr.md`
- German (`de`): `report_de.md`
- Japanese (`ja`): `report_ja.md`

### SEARCH_LIMIT
Controls the number of papers to search when conducting research:

```
SEARCH_LIMIT=100
```

Default is 100 papers per research topic. You can adjust this to search fewer or more papers.

**When writing reports**, always:
1. Check the `REPORT_LANGUAGE` setting in `.env` and generate the report in that language
2. Check the `SEARCH_LIMIT` setting and use it as the default search limit for topic research
3. Save the report with the appropriate filename based on the language
4. If the user explicitly requests a different language or search limit, use their request instead

To change settings, edit `.env` and update the values, then regenerate reports as needed.
