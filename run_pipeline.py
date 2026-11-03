"""End-to-end pipeline on a list of patents: fetch -> window -> label -> aggregate.

    # live: fetch descriptions from Google Patents (samples) and label with a model
    python run_pipeline.py --patents US11524023B2 US12620170B2 --out data/examples/demo --provider openai \
        --base-url https://api.together.xyz/v1 --model Qwen/Qwen3.6-32B-Instruct

    # offline: start from saved paragraphs (examples/demo/paragraphs.jsonl) and skip the model call
    python run_pipeline.py --paragraphs data/examples/demo/paragraphs.jsonl --out data/examples/demo --no-label

Outputs in --out:
    paragraphs.jsonl   one row per patent: metadata + description paragraphs (the fetch stage)
    windows.jsonl      one row per citation window (text, paragraph index, family-duplicate flag)
    labeled.jsonl      windows + document type, function, confidence, cited_work_string, note (label stage)
    profiles_*.csv     shares by assignee / year
    report.md          a readable summary: per patent, every window with its label and rationale
"""
import argparse, collections, csv, json, pathlib, re, sys, time

HERE = pathlib.Path(__file__).parent
for _d in ("1_fetch", "2_label", "4_aggregate"):
    sys.path.insert(0, str(HERE / _d))
from fetch_patents import windows, _Desc  # noqa: E402
from aggregate import aggregate, FUNCS  # noqa: E402

FAMILY_RX = re.compile(r"\s+")


def fetch_paragraphs(pns, session):
    for pn in pns:
        r = session.get(f"https://patents.google.com/patent/{pn}/en", timeout=60)
        if r.status_code != 200:
            print(f"{pn}: HTTP {r.status_code}", file=sys.stderr); continue
        html = r.content.decode("utf-8", errors="replace")  # pages are UTF-8; requests may guess Latin-1
        p = _Desc(); p.feed(html)
        m = re.search(r'itemprop="assigneeOriginal"[^>]*>([^<]+)<', html) or re.search(r'itemprop="assigneeCurrent"[^>]*>([^<]+)<', html)
        yield {"pn": pn, "title": " ".join(p.meta.get("title", "").split()), "assignee": (m.group(1).strip() if m else ""),
               "priority_date": p.meta.get("priorityDate", ""), "grant_date": p.meta.get("publicationDate", ""), "paras": p.paras}
        time.sleep(1.0)


def make_windows(patents):
    seen = {}
    for pat in patents:
        for i, w, patent_only in windows(pat["paras"]):
            row = {"window_id": f"{pat['pn']}:{i}", "pn": pat["pn"], "assignee": pat.get("assignee", ""), "title": pat.get("title", ""),
                   "priority_date": pat.get("priority_date", ""), "grant_date": pat.get("grant_date", ""),
                   "n_desc_paras": len(pat["paras"]), "para_idx": i, "text": w, "regex_patent_only": patent_only}
            key = FAMILY_RX.sub(" ", w).strip().lower()
            row["is_family_duplicate"] = key in seen and seen[key] != pat["pn"]
            seen.setdefault(key, pat["pn"])
            yield row


def label(rows, provider, model, base_url, cache_dir):
    from llm import Chat, label_one  # noqa: WPS433
    import hashlib
    prompt = (HERE / "2_label" / "prompts" / "label_citation_function.md").read_text(encoding="utf-8")
    schema = json.loads((HERE / "2_label" / "schema.json").read_text(encoding="utf-8"))
    chat = Chat(provider=provider, model=model, base_url=base_url)
    pv = hashlib.sha256(prompt.encode()).hexdigest()[:10]
    for r in rows:
        obj = label_one(chat, prompt, schema, r["text"])
        r2 = dict(r); r2.update(obj); r2["_model"] = model; r2["_provider"] = provider; r2["_prompt_version"] = pv
        yield r2


def report(patents, labeled, out):
    by_pn = collections.defaultdict(list)
    for r in labeled:
        by_pn[r["pn"]].append(r)
    L = ["# Pipeline run report", "", f"{len(patents)} patents, {len(labeled)} citation windows.", ""]
    for pat in patents:
        rows = by_pn.get(pat["pn"], [])
        L += [f"## {pat['pn']} — {pat.get('title','')}", "",
              f"Assignee: {pat.get('assignee','')} · priority {pat.get('priority_date','')} · grant {pat.get('grant_date','')} · {len(pat['paras'])} description paragraphs · {len(rows)} windows", ""]
        c = collections.Counter(r.get("function", "?") for r in rows if r.get("cited_doc_type") in ("paper", "mixed", "standards_doc", "book"))
        if c:
            L.append("Function of science citations: " + ", ".join(f"{k} {v}" for k, v in c.most_common()) + ".")
            L.append("")
        for r in rows:
            L += [f"**{r['window_id']}** · para {r['para_idx']}/{r['n_desc_paras']} · cited: {r.get('cited_doc_type','?')} · **{r.get('function','?')}** ({r.get('confidence','?')})",
                  "", f"> {r['text']}", "", f"*{r.get('note','')}*", ""]
    (pathlib.Path(out) / "report.md").write_text("\n".join(L), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--patents", nargs="*", default=[]); ap.add_argument("--paragraphs", help="saved paragraphs.jsonl (skip fetch)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-label", action="store_true", help="stop after windows (no model call)")
    ap.add_argument("--labels", help="use an existing labeled.jsonl (e.g. interactive labels) instead of calling a model")
    ap.add_argument("--provider", default="anthropic"); ap.add_argument("--model", default="claude-fable-5-1"); ap.add_argument("--base-url")
    a = ap.parse_args()
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    if a.paragraphs:
        patents = [json.loads(l) for l in open(a.paragraphs, encoding="utf-8")]
    else:
        import requests
        s = requests.Session(); s.headers["User-Agent"] = "science-in-invention (academic; see README)"
        patents = list(fetch_paragraphs(a.patents, s))
        with open(out / "paragraphs.jsonl", "w", encoding="utf-8") as f:
            for p in patents: f.write(json.dumps(p, ensure_ascii=False) + "\n")
    rows = list(make_windows(patents))
    with open(out / "windows.jsonl", "w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(patents)} patents -> {len(rows)} windows ({sum(r['is_family_duplicate'] for r in rows)} family duplicates)")
    if a.no_label and not a.labels:
        return
    if a.labels:
        lab = {json.loads(l)["window_id"]: json.loads(l) for l in open(a.labels, encoding="utf-8")}
        labeled = [dict(r, **{k: v for k, v in lab.get(r["window_id"], {}).items() if k not in r}) for r in rows]
    else:
        labeled = list(label(rows, a.provider, a.model, a.base_url, ".llm_cache"))
    with open(out / "labeled.jsonl", "w", encoding="utf-8") as f:
        for r in labeled: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    for by in ("assignee", "year"):
        table = aggregate(labeled, by, {})
        if table:
            with open(out / f"profiles_{by}.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(table[0].keys())); w.writeheader(); w.writerows(table)
    report(patents, labeled, out)
    print(f"labeled {len(labeled)} windows -> {out}/labeled.jsonl, report.md, profiles_*.csv")


if __name__ == "__main__":
    main()
