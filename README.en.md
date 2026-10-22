> [中文](README.md) | English

# DSH Records Router

> Locate the record snippets to read based on your instruction: heading-level index + Chinese bigram + IDF/coverage scoring, **reading only the matched "file:line" ranges** instead of the whole handover log/archive.
>
> Pure Python standard library · no vector DB · no external services · code MIT / docs CC BY 4.0

## Why it's needed

The workspace piles up handover logs, archives, project docs, and reports. Reading everything into context is expensive and easily truncated; `grep` doesn't understand topics/aliases/ranking.
The records router takes the middle path: **index → score → read back by line number**.

## Repo contents

| Content | Description |
|---|---|
| [docs/records-router.md](docs/records-router.en.md) | Design: index structure, tokenization, scoring, budget, limitations, and upgrade path |
| [examples/records-router/records_router.py](examples/records-router/records_router.py) | Main script (`build` / `query` / `read` / `stats`) |
| [examples/records-router/topics.example.json](examples/records-router/topics.example.json) | Topic/alias example (copy to `topics.json` and edit) |
| [examples/records-router/SKILL.md](examples/records-router/SKILL.md) | Skill description: route first, then read; never read whole files |

## Quick start

```bash
export RECORDS_ROOT="<workspace>"      # Windows: set RECORDS_ROOT=...
python examples/records-router/records_router.py build
python examples/records-router/records_router.py query "项目A 下一步要确认什么"
python examples/records-router/records_router.py read 1 2 3
```

Default budget: at most 6 sections / 400 lines; adjust with `--top` / `--budget`.

## Measured numbers (author's environment)

- Indexed 82 files / 1535 sections; about 0.4 s per query;
- Actually reads 3~6 sections per run (about 50~130 lines);
- The index is rebuilt automatically before querying when source files change.

## Limitations

Keyword/IDF approach, no semantics; Chinese is approximated by bigrams; results degrade when docs have no heading structure.
Upgrade path: BM25 → SQLite FTS5 → local embeddings (hybrid) → existing solutions (e.g. ratel / basic-memory). See section 7 of the doc.

## License

Code MIT ([LICENSE](LICENSE)); docs CC BY 4.0; unofficial, no warranty. See [LEGAL.md](LEGAL.en.md).

---

*Summary: a records router that indexes headings, scores sections with Chinese bigrams + IDF/coverage, and reads only matched line ranges — instead of loading whole handover logs or archives into context. Pure Python, no vector DB. Code MIT, docs CC BY 4.0.*
