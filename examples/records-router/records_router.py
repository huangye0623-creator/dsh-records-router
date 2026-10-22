#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""记录路由器：按你的指令定位要读的记录片段，不整读历史文件。

用法（在任意工作区根目录运行；也可用环境变量 RECORDS_ROOT 指定根目录）：
  python tools\\records\\records_router.py build
  python tools\\records\\records_router.py query "你的指令原话" [--top 6] [--budget 400]
  python tools\\records\\records_router.py read 1 3      # 读上次 query 命中的第 1、3 段
  python tools\\records\\records_router.py stats

索引范围：当前状态、交接记录、交接归档、AGENTS、避坑规范、使用说明、
03_产出、项目*/03_产出、项目说明文件。记录永远留在磁盘，这里只做“路由”。
"""
import json
import math
import os
import re
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.environ.get("RECORDS_ROOT", os.getcwd())
HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.json")
INDEX_MD = os.path.join(HERE, "index.md")
LAST = os.path.join(HERE, ".last_query.json")
TOPICS = os.path.join(HERE, "topics.json")
if not os.path.exists(TOPICS):
    TOPICS = os.path.join(HERE, "topics.example.json")

CJK = re.compile(r"[\u4e00-\u9fff]+")
HEAD = re.compile(r"^(#{1,3})\s+(.*)$")
DATE = re.compile(r"(20\d{2})-(\d{2})-(\d{2})")
PROJ = re.compile(r"项目\d{2}_[^\s\\/]+")


def tokenize(text):
    text = (text or "").lower()
    toks = set()
    for w in re.findall(r"[a-z][a-z0-9_\-\.]{1,}", text):
        toks.add(w)
    for run in CJK.findall(text):
        if len(run) <= 8:
            toks.add(run)
        for i in range(len(run) - 1):
            toks.add(run[i:i + 2])
    return toks


def kind_of(path):
    p = path.replace("/", "\\")
    name = os.path.basename(p)
    if name == "当前状态.md":
        return "当前状态"
    if name == "交接记录.md":
        return "交接条目"
    if "交接归档" in p:
        return "交接归档"
    if name in ("AGENTS.md",) or "避坑规范" in name:
        return "规则"
    if name == "使用说明.txt" or "说明" in name:
        return "说明"
    if re.search(r"\\03_产出\\", p):
        return "项目文档" if "\\项目" in p else "交付文档"
    return "项目文档"


def project_of(path):
    m = PROJ.search(path)
    return m.group(0) if m else ""


def read_lines(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read().split("\n")
    except OSError:
        return None


def sections_md(path):
    lines = read_lines(path)
    if lines is None:
        return []
    starts = [i for i, l in enumerate(lines) if HEAD.match(l)]
    out = []
    if not starts:
        body = "\n".join(lines).strip()
        if body:
            out.append(("文件全文", 1, len(lines), body))
        return out
    if starts[0] > 0:
        body = "\n".join(lines[:starts[0]]).strip()
        if body:
            out.append(("文件开头", 1, starts[0], body))
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < len(starts) else len(lines)
        title = HEAD.match(lines[s]).group(2).strip()
        body = "\n".join(lines[s:e]).strip()
        out.append((title, s + 1, e, body))
    return out


def sections_txt(path):
    lines = read_lines(path)
    if lines is None:
        return []
    starts = [i for i, l in enumerate(lines) if re.match(r"^\s{2,}\d{4}-\d{2}-\d{2}", l)]
    out = []
    if not starts:
        return [("文件全文", 1, len(lines), "\n".join(lines).strip())]
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < len(starts) else len(lines)
        title = lines[s].strip()[:80]
        out.append((title, s + 1, e, "\n".join(lines[s:e]).strip()))
    return out


def source_files():
    files = []

    def add(p):
        if os.path.isfile(p) and os.path.getsize(p) < 600_000:
            files.append(p)

    add(os.path.join(ROOT, "当前状态.md"))
    add(os.path.join(ROOT, "交接记录.md"))
    add(os.path.join(ROOT, "AGENTS.md"))
    add(os.path.join(ROOT, "DSH插件与Profile避坑规范.md"))
    add(os.path.join(ROOT, "使用说明.txt"))
    arc = os.path.join(ROOT, "交接归档")
    if os.path.isdir(arc):
        for n in sorted(os.listdir(arc)):
            if n.endswith((".md", ".txt")):
                add(os.path.join(arc, n))
    out = os.path.join(ROOT, "03_产出")
    if os.path.isdir(out):
        for n in sorted(os.listdir(out)):
            if n.endswith((".md", ".txt")):
                add(os.path.join(out, n))
    for d in sorted(os.listdir(ROOT)):
        if not (d.startswith("项目") and os.path.isdir(os.path.join(ROOT, d))):
            continue
        base = os.path.join(ROOT, d)
        po = os.path.join(base, "03_产出")
        if os.path.isdir(po):
            for dirpath, _, names in os.walk(po):
                for n in sorted(names):
                    if n.endswith((".md", ".txt")):
                        add(os.path.join(dirpath, n))
        for n in os.listdir(base):
            if n.endswith((".md", ".txt")) and ("说明" in n or "交接" in n):
                add(os.path.join(base, n))
    # 通用文档（README / docs / notes），方便直接用于普通仓库或知识库
    for sub in ("", "docs", "notes"):
        base = os.path.join(ROOT, sub) if sub else ROOT
        if os.path.isdir(base):
            for n in sorted(os.listdir(base)):
                p = os.path.join(base, n)
                if os.path.isfile(p) and n.endswith((".md", ".txt")):
                    add(p)
    seen = set()
    files = [f for f in files if not (f in seen or seen.add(f))]
    return files


def build(quiet=False):
    records = []
    rid = 0
    files = source_files()
    for path in files:
        parts = sections_txt(path) if path.endswith(".txt") else sections_md(path)
        for title, start, end, body in parts:
            body = body.strip()
            if len(body) < 10 and len(title) < 6:
                continue
            rid += 1
            preview = re.sub(r"\s+", " ", body)[:400]
            m = DATE.search(title) or DATE.search(body[:200])
            records.append({
                "id": rid,
                "kind": kind_of(path),
                "project": project_of(path),
                "title": title[:160],
                "file": path,
                "start": start,
                "end": end,
                "date": m.group(0) if m else "",
                "chars": len(body),
                "preview": preview,
            })
    meta = {"built_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "files": len(files), "records": len(records)}
    with open(INDEX, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "records": records}, f, ensure_ascii=False, indent=1)
    with open(INDEX_MD, "w", encoding="utf-8") as f:
        f.write("# 记录索引（自动生成，勿手改）\n\n")
        f.write(f"生成：{meta['built_at']} · 文件 {meta['files']} 个 · 片段 {meta['records']} 段\n\n")
        cur = None
        for r in records:
            if r["file"] != cur:
                cur = r["file"]
                f.write(f"\n## {cur}\n\n")
            f.write(f"- L{r['start']}-{r['end']} · {r['kind']} · {r['title']}\n")
    if not quiet:
        print(f"索引已生成：{INDEX}")
        print(f"  文件 {meta['files']} 个 / 片段 {meta['records']} 段")
    return meta


def ensure_index():
    """索引不存在或比源文件旧时自动重建（新交接条目会自动进索引）。"""
    if not os.path.exists(INDEX):
        build(quiet=True)
        return
    idx_m = os.path.getmtime(INDEX)
    for p in source_files():
        try:
            if os.path.getmtime(p) > idx_m:
                build(quiet=True)
                return
        except OSError:
            pass


def load_index():
    if not os.path.exists(INDEX):
        print("还没有索引，先运行：python tools\\records\\records_router.py build", file=sys.stderr)
        sys.exit(2)
    with open(INDEX, encoding="utf-8") as f:
        return json.load(f)


def load_topics():
    with open(TOPICS, encoding="utf-8") as f:
        return json.load(f)


def detect_topics(qtext):
    """最长别名优先：避免“记录路由器”被“路由器”误判到路由项目。"""
    q = qtext.lower()
    config = load_topics()
    hits = []
    for t in config["topics"]:
        for a in t["aliases"]:
            al = a.lower()
            start = 0
            while True:
                i = q.find(al, start)
                if i < 0:
                    break
                hits.append((len(al), i, i + len(al), t))
                start = i + 1
    hits.sort(key=lambda x: (-x[0], x[1]))
    used = []
    accepted = []
    for length, s, e, t in hits:
        if any(not (e <= us or s >= ue) for us, ue in used):
            continue
        used.append((s, e))
        if t not in accepted:
            accepted.append(t)
    return accepted


def query(qtext, top=6, budget=400):
    ensure_index()
    data = load_index()
    config = load_topics()
    kw = config["kind_weights"]
    topics = detect_topics(qtext)
    qtokens = tokenize(qtext)
    proj_boost = {t["project"] for t in topics if t.get("project")}

    qlow = qtext.lower()
    intent = {
        "archive": any(k in qlow for k in ("之前", "历史", "当时", "为什么", "怎么做的", "复盘", "以前")),
        "state": any(k in qlow for k in ("当前", "现在", "在做", "进展", "下一步", "状态", "待确认")),
        "handover": any(k in qlow for k in ("交接", "归档", "记录", "看板")),
    }

    # 一次算好每条记录的分词，便于算 IDF（稀有词权重更高，如 "Mech-Butterfly"）
    records = data["records"]
    for r in records:
        r["_tt"] = tokenize(r["title"])
        r["_pt"] = tokenize(r["project"])
        r["_bt"] = tokenize(r["preview"])
    df = {}
    for r in records:
        for t in (r["_tt"] | r["_bt"]):
            df[t] = df.get(t, 0) + 1
    n = len(records) or 1

    def idf(t):
        return 0.6 + math.log((n + 1) / (df.get(t, 0) + 1))

    phrases = [p.lower() for p in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9_\-\.]{4,}", qtext)]

    scored = []
    for r in records:
        s = 0.0
        for t in qtokens:
            w = idf(t)
            if t in r["_tt"]:
                s += 3.0 * w
            if t in r["_pt"]:
                s += 2.0 * w
            if t in r["_bt"]:
                s += 1.0 * w
        for p in phrases:
            if p in r["title"].lower():
                s += 2.5
            if p in r["preview"].lower():
                s += 1.0
        if r["project"] and r["project"] in proj_boost:
            s += 4.0
        for t in topics:
            if t["id"].lower() in r["title"].lower():
                s += 2.0
            fname = os.path.basename(r["file"]).lower()
            for a in t["aliases"]:
                if a.lower() in fname:
                    s += 1.5
                    break
        # 查询里的“实体词”出现在文件名里 → 信号（如 Tavily、项目名、专有名词）
        fname = os.path.basename(r["file"]).lower()
        for t in qtokens:
            if len(t) >= 4 and t in fname:
                s += 2.5
        # 覆盖率：命中查询词越多，说明越贴题
        matched = sum(1 for t in qtokens if t in r["_tt"] or t in r["_bt"])
        if qtokens:
            s *= 1.0 + 0.8 * (matched / len(qtokens))
        s *= kw.get(r["kind"], 1.0)
        if intent["state"] and r["kind"] == "当前状态":
            s *= 1.5
        if intent["handover"] and r["kind"] in ("交接条目", "交接归档", "当前状态"):
            s *= 1.35
        if intent["archive"] and r["kind"] == "交接归档":
            s *= 1.25
        if s > 0:
            scored.append((s, r))
    scored.sort(key=lambda x: (-x[0], x[1]["kind"] != "当前状态"))
    picked, lines = [], 0
    for s, r in scored:
        n = r["end"] - r["start"] + 1
        if picked and lines + n > budget:
            continue
        picked.append((s, r))
        lines += n
        if len(picked) >= top:
            break

    out = {
        "query": qtext,
        "topics": [t["id"] for t in topics],
        "topic_projects": [os.path.join(ROOT, t["project"]) for t in topics if t.get("project")],
        "budget_lines": budget,
        "used_lines": lines,
        "hits": [{
            "n": i + 1, "score": round(s, 2), "kind": r["kind"],
            "file": r["file"], "start": r["start"], "end": r["end"],
            "title": r["title"], "project": r["project"],
        } for i, (s, r) in enumerate(picked)],
    }
    with open(LAST, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    return out


def print_query(out):
    print(f"指令：{out['query']}")
    print(f"识别到：{'、'.join(out['topics']) if out['topics'] else '（未命中已知主题，按关键词匹配）'}")
    for t in out.get("topic_projects", []):
        print(f"主题入口：{t}")
    print("必读基线：当前状态.md（约 30 行，先看现在在做什么）")
    if not out["hits"]:
        print("没有命中。兜底：先读 当前状态.md，再 grep 关键词。")
        return
    print(f"建议阅读：{len(out['hits'])} 段，约 {out['used_lines']} 行（预算 {out['budget_lines']} 行）")
    print()
    print("| # | 类型 | 位置 | 标题 | 分数 |")
    print("|---|---|---|---|---|")
    for h in out["hits"]:
        loc = f"{os.path.basename(h['file'])}:{h['start']}-{h['end']}"
        print(f"| {h['n']} | {h['kind']} | {loc} | {h['title'][:60]} | {h['score']} |")
    print()
    print("下一步：只读这几段 → python tools\\records\\records_router.py read " +
          " ".join(str(h["n"]) for h in out["hits"][:3]))
    print("提示：读完仍不够，再放宽 --top 或换关键词；不要整读归档。")


def read_hits(nums, cap=200):
    with open(LAST, encoding="utf-8") as f:
        out = json.load(f)
    by_n = {h["n"]: h for h in out["hits"]}
    for n in nums:
        h = by_n.get(n)
        if not h:
            print(f"[{n}] 没有这个编号（先跑 query）")
            continue
        lines = read_lines(h["file"]) or []
        seg = lines[h["start"] - 1:h["end"]]
        if len(seg) > cap:
            seg = seg[:cap] + ["…（已截断，需要更多再用 sed/read 指定行）"]
        print(f"\n===== [{n}] {h['title']} =====")
        print(f"{h['file']}:{h['start']}-{h['end']}  ({h['kind']})")
        print("\n".join(seg))


def stats():
    data = load_index()
    meta = data["meta"]
    kinds = {}
    for r in data["records"]:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print(f"索引生成时间：{meta['built_at']}")
    print(f"文件 {meta['files']} 个 / 片段 {meta['records']} 段")
    print("按类型：")
    for k, v in sorted(kinds.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    cmd = args[0]
    if cmd == "build":
        build()
    elif cmd == "stats":
        stats()
    elif cmd == "query":
        qtext = " ".join(a for a in args[1:] if not a.startswith("--"))
        if not qtext:
            print('用法：query "你的指令"', file=sys.stderr)
            sys.exit(2)
        top, budget = 6, 400
        for a in args[1:]:
            if a.startswith("--top="):
                top = int(a.split("=", 1)[1])
            if a.startswith("--budget="):
                budget = int(a.split("=", 1)[1])
        out = query(qtext, top, budget)
        if "--json" in args:
            print(json.dumps(out, ensure_ascii=False, indent=1))
        else:
            print_query(out)
    elif cmd == "read":
        nums = [int(a) for a in args[1:] if a.isdigit()]
        if not nums:
            print("用法：read 1 2 3", file=sys.stderr)
            sys.exit(2)
        read_hits(nums)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
