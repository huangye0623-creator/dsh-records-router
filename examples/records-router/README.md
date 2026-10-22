# records-router 示例

这是 [docs/records-router.md](../../docs/records-router.md) 的可运行实现：**按指令定位记录片段，按“文件:行号”只读命中段**。

## 文件

| 文件 | 说明 |
|---|---|
| `records_router.py` | 主脚本（Python 标准库，无第三方依赖） |
| `topics.example.json` | 主题/别名示例；复制成 `topics.json` 后按你的项目改 |
| `SKILL.md` | 技能说明：告诉 AI “先路由再读、禁止整读” |

## 快速开始

```bash
# 放到 <workspace>/tools/records/ 下（或任意目录）
export RECORDS_ROOT="<workspace>"        # Windows: set RECORDS_ROOT=...
python records_router.py build
python records_router.py query "项目A 下一步要确认什么"
python records_router.py read 1 2 3
```

- 默认根目录 = 当前目录；也可用 `RECORDS_ROOT` 指定；
- 默认索引范围：当前状态、交接记录、交接归档、规则/说明、交付文档、项目内 03_产出；
- 单次预算：最多 6 段 / 400 行（可用 `--top` / `--budget` 调整）。

## 依赖

- Python 3.9+（标准库即可）；
- 无向量库、无嵌入模型、无外部服务。

## 调参

- `topics.example.json`：主题 id、别名、项目文件夹名；
- 打分逻辑在 `records_router.py` 的 `query()` 里，可按需调整权重；
- 若你的文档没有标题结构，索引效果会下降——先补标题。

## 局限

关键词/IDF 路线，不懂语义；中文靠 bigram 近似；更大规模建议换 BM25/SQLite FTS5/嵌入检索（见 docs/records-router.md 第 7 节）。

## 许可

MIT（见仓库根目录 `LICENSE`）。
