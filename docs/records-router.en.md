> [中文](records-router.md) | English

# Records router: locate archives by instruction, don't read the whole context

> Problem: the workspace piles up handover logs, archives, project docs, and reports; do we have to read everything every time?
> Goal: **first determine which areas your question involves, then read only the matched 3~6 sections (file:line)**.

---

## 1. Why not just use grep / a vector DB

| Approach | Problem |
|---|---|
| `grep` keywords | Exact match only; doesn't understand "topic/project/alias"; results have no ranking or reading budget |
| Full vector DB | Needs an embedding model/service/database; too heavy for hundreds of thousands of characters of local docs; Chinese tokenization still has to be handled |
| Read everything into context | Expensive, slow, and easily truncated |

The records router takes the middle path: **heading-level index + lightweight scoring + read-back by line number**, with zero external dependencies.

## 2. What gets indexed

By default only "record-type" files are indexed; tool/cache directories are not:

- `当前状态.md`, `交接记录.md`, `交接归档/*.md`
- rule files (e.g. `AGENTS.md`, spec documents)
- instruction files (`使用说明.txt`)
- deliverable doc directories (`03_产出/*.md`, `03_产出/**` inside projects, project description/handover files)

Sections are split by Markdown headings, and each record stores:

```json
{
  "kind": "当前状态",
  "project": "项目A",
  "title": "进行中",
  "file": "<workspace>/当前状态.md",
  "start": 10,
  "end": 19,
  "date": "2026-10-22",
  "preview": "……前 400 字……"
}
```

## 3. Scoring (good enough)

Query tokenization:

- English by words;
- Chinese by **contiguous segments + 2-grams** ("交接记录" → "交接记录 / 交接 / 接记 / 记录"), avoiding a dependency on a tokenizer library;
- The topic alias table (`topics.json`) expands in project aliases/short names/English names.

Scoring is similar to lightweight TF-IDF:

- Heading hits weigh most, project name next, body text least;
- Use **IDF** to damp high-frequency words ("项目", "文件");
- **Coverage** bonus: the more query terms hit, the more relevant;
- Phrase hits (consecutive words) score extra;
- Type weight: current status/recent handover > archive/rules;
- Intent bonus: asking "before/why" → archive; asking "now/next step" → current status.

Then truncate by budget: by default **at most 6 sections / 400 lines**, ensuring that "routing doesn't turn back into reading everything".

## 4. Commands

```bash
# 1) build the index
python examples/records-router/records_router.py build

# 2) query by the original wording (output: topic entry + required baseline + matched-section table)
python examples/records-router/records_router.py query "项目A 下一步要确认什么"

# 3) read only matched sections 1, 2, 3
python examples/records-router/records_router.py read 1 2 3

# 4) maintenance
python examples/records-router/records_router.py stats
```

Output example (anonymized):

```text
识别到：项目A
主题入口：<workspace>/项目01_项目A
必读基线：当前状态.md（约 30 行）
| # | 类型 | 位置 | 标题 | 分数 |
| 1 | 当前状态 | 当前状态.md:10-18 | 进行中 | 80.5 |
| 2 | 项目文档 | 方案.md:1-9 | 方案标题 | 52.9 |
| 3 | 交接条目 | 交接记录.md:22-31 | 2026-10-22 · … | 40.0 |
```

## 5. Skill wrapper

Encode "route first, then read" as a skill (`SKILL.md`), so the AI **automatically runs the command first** when history/projects/handover are involved:

- Trigger words: project names, "before/why/progress/next step", handover/archive/records;
- Hard rule: **never read** `交接记录.md` or archives in full; query first, then read;
- Fallback: when nothing matches, read `当前状态.md` first, then use `grep`.

See `examples/records-router/SKILL.md` for the example.

## 6. Measured numbers

| Metric | Value |
|---|---|
| Index size | 82 files / 1535 sections |
| Single query | about 0.4 s (including index freshness check) |
| Actual reading per run | 3~6 sections, about 50~130 lines |
| Index freshness | compares source file mtime before querying; rebuilds automatically on change |

Comparison: before the revamp, one "related investigation" required reading 1000+ lines of handover logs/archives; now only the matched sections are read by default.

## 7. Limitations and upgrade path

**Current limitations**

- Based on keywords/IDF, **no semantics** (paraphrases may be missed);
- No POS/entity recognition for Chinese; approximated by bigrams;
- Heading splitting depends on document structure (docs without headings perform poorly);
- The index is a local JSON (~1 MB for 1500 sections); larger scales need different storage.

**Upgrade path (from low to high effort)**

1. **BM25**: add term frequency/length normalization for more stable ranking;
2. **SQLite FTS5**: built-in full-text index, but Chinese needs tokenization/trigrams;
3. **Small local embedding model**: hybrid semantic + keyword recall;
4. **Existing solutions**: `ratel` (BM25 + semantics, no vector DB), `basic-memory` (Markdown knowledge graph), DSH memory plugins (auto-injection, another route).

## 8. When not to use it

- Only a few small docs: reading directly is faster;
- Need "automatically remember" rather than "look up on demand": use an auto-memory plugin;
- Need cross-language/semantic retrieval: go with embeddings or a dedicated retrieval service.

## 9. Examples

- Script: `examples/records-router/records_router.py`
- Topic config: `examples/records-router/topics.example.json` (copy to `topics.json` and edit for your projects)
- Skill: `examples/records-router/SKILL.md`
