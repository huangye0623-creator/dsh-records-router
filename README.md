# DSH Records Router（记录路由器）

> 中文 | [English](README.en.md)

> 按你的指令定位要读的记录片段：标题级索引 + 中文 bigram + IDF/覆盖率打分，**只读命中的“文件:行号”**，不整读交接记录/归档。
>
> 纯 Python 标准库 · 无向量库 · 无外部服务 · 代码 MIT / 文档 CC BY 4.0

## 为什么需要

工作区里堆了交接记录、归档、项目文档、报告。全读进上下文很贵，还容易被截断；`grep` 又不懂主题/别名/排序。
记录路由器走中间路线：**索引 → 打分 → 按行号回读**。

## 仓库内容

| 内容 | 说明 |
|---|---|
| [docs/records-router.md](docs/records-router.md) | 设计：索引结构、分词、打分、预算、局限与升级路线 |
| [examples/records-router/records_router.py](examples/records-router/records_router.py) | 主脚本（`build` / `query` / `read` / `stats`） |
| [examples/records-router/topics.example.json](examples/records-router/topics.example.json) | 主题/别名示例（复制成 `topics.json` 后改） |
| [examples/records-router/SKILL.md](examples/records-router/SKILL.md) | 技能说明：先路由再读、禁止整读 |

## 快速开始

```bash
export RECORDS_ROOT="<workspace>"      # Windows: set RECORDS_ROOT=...
python examples/records-router/records_router.py build
python examples/records-router/records_router.py query "项目A 下一步要确认什么"
python examples/records-router/records_router.py read 1 2 3
```

默认预算：最多 6 段 / 400 行；可用 `--top` / `--budget` 调整。

## 实测数字（作者环境）

- 索引 82 个文件 / 1535 段；单次查询约 0.4 秒；
- 单次实际阅读 3~6 段（约 50~130 行）；
- 源文件变化后查询前自动重建索引。

## 局限

关键词/IDF 路线，不懂语义；中文靠 bigram 近似；文档没有标题结构时效果下降。
升级路线：BM25 → SQLite FTS5 → 本地嵌入（hybrid）→ 现成方案（如 ratel / basic-memory）。详见文档第 7 节。

## 许可证

代码 MIT（[LICENSE](LICENSE)）；文档 CC BY 4.0；非官方、不提供担保。详见 [LEGAL.md](LEGAL.md)。

---

*English summary: a records router that indexes headings, scores sections with Chinese bigrams + IDF/coverage, and reads only matched line ranges — instead of loading whole handover logs or archives into context. Pure Python, no vector DB. Code MIT, docs CC BY 4.0.*
