"""Second coding of the label files by a different model run as Claude Code subagents (no API key needed).

The subagent route: `split` writes blind batch files (window_id and text only, no labels) to a scratch
folder; each batch is handed to one subagent with the labeling guide and the schema, which writes its
labels to <out_dir>/<batch>.jsonl; `merge` validates those files against the schema, joins them to the
raw rows and writes benchmark/labels_<model>.jsonl with the model and prompt version in every row, in
the same format `common/llm.py` produces on the API route. `report` writes benchmark/results.md, one section per
(second-coder labels, labeled sample) pair:
    python benchmark/subagent_batches.py report \
        --pair benchmark/labels_claude-opus-5-5.jsonl pilot/citation_windows_labeled.jsonl \
        --pair benchmark/labels_claude-opus-5-5.jsonl pilot/decades/citation_windows_labeled.jsonl \
        --pair benchmark/labels_claude-fable-5-1_longrun.jsonl pilot/longrun/citation_windows_labeled.jsonl \
        --pair benchmark/labels_claude-opus-5-5_firms_fields_retest.jsonl pilot/firms/citation_windows_labeled.jsonl \
        --pair benchmark/labels_claude-opus-5-5_firms_fields_retest.jsonl pilot/fields/citation_windows_labeled.jsonl \
        --output benchmark/results.md
The firm and field samples are compared with a blind second claude-opus-5-5 pass over every 20th labeling batch
(test-retest; batch files of local/firms_fields/make_batches.py).

    python benchmark/subagent_batches.py split --raw pilot/citation_windows_raw.jsonl pilot/decades/citation_windows_raw.jsonl \
        --batch-dir <scratch>/batches --size 25
    python benchmark/subagent_batches.py merge --raw ... --labels-dir <scratch>/out --model claude-opus-5-5 \
        --output benchmark/labels_claude-opus-5-5.jsonl
"""
import argparse, contextlib, datetime, hashlib, io, json, pathlib, sys

HERE = pathlib.Path(__file__).parent.parent
SCHEMA = json.loads((HERE / "schema.json").read_text(encoding="utf-8"))
PROMPT = (HERE / "prompts" / "label_citation_function.md").read_text(encoding="utf-8")


def read_raw(paths):
    rows = []
    for p in paths:
        rows += [json.loads(l) for l in open(p, encoding="utf-8")]
    ids = [r["window_id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate window_id across raw files"
    return rows


def split(raw, batch_dir, size):
    batch_dir = pathlib.Path(batch_dir); batch_dir.mkdir(parents=True, exist_ok=True)
    for i in range(0, len(raw), size):
        p = batch_dir / f"batch_{i // size + 1:03d}.jsonl"
        with open(p, "w", encoding="utf-8") as f:
            for r in raw[i:i + size]:
                f.write(json.dumps({"window_id": r["window_id"], "text": r["text"]}, ensure_ascii=False) + "\n")
    print(f"{len(raw)} windows -> {(len(raw) + size - 1) // size} batches in {batch_dir}")


def merge(raw, labels_dir, model, output):
    props = SCHEMA["properties"]
    got, bad = {}, []
    for p in sorted(pathlib.Path(labels_dir).glob("*.jsonl")):
        for n, line in enumerate(open(p, encoding="utf-8"), 1):
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError as e:
                bad.append(f"{p.name}:{n} bad json ({e})"); continue
            probs = [k for k in SCHEMA["required"] if k not in o] + \
                    [f"{k}={o.get(k)!r}" for k, s in props.items() if "enum" in s and k in o and o[k] not in s["enum"]]
            if probs:
                bad.append(f"{p.name}:{n} {o.get('window_id')}: " + ", ".join(probs)); continue
            if o["window_id"] in got:
                bad.append(f"{p.name}:{n} duplicate {o['window_id']}"); continue
            got[o["window_id"]] = o
    pv = hashlib.sha256(PROMPT.encode()).hexdigest()[:10]
    missing = [r["window_id"] for r in raw if r["window_id"] not in got]
    extra = sorted(set(got) - {r["window_id"] for r in raw})
    with open(output, "w", encoding="utf-8") as f:
        for r in raw:
            if r["window_id"] not in got:
                continue
            row = dict(r); row.update({k: got[r["window_id"]][k] for k in props})
            row["_model"] = model; row["_provider"] = "claude-code-subagent"; row["_prompt_version"] = pv
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{len(got) - len(extra)} of {len(raw)} windows labeled -> {output}")
    for b in bad: print("  problem:", b)
    if missing: print(f"  missing ({len(missing)}): {' '.join(missing[:40])}{' ...' if len(missing) > 40 else ''}")
    if extra: print(f"  unknown window_id ({len(extra)}): {' '.join(extra[:20])}")
    return 0 if not (bad or missing) else 1


def report(pairs, output):
    """Write results.md: agreement between two LLM coders on each sample, from validate.agreement. Each pair is
    (label file of the blind second coder, labeled file of the sample = first coder and source of truth)."""
    sys.path.insert(0, str(HERE)); from common.validate import agreement  # noqa: E402
    L = ["# Benchmark results", "",
         f"Generated {datetime.date.today().isoformat()} by `benchmark/subagent_batches.py report`.", "",
         "Each section compares a sample's label file (first coder, the source of truth for that sample) with a blind second "
         "coder. Subagent coders ran as Claude Code subagents on batches of 25-30 windows with the same guide "
         "`prompts/label_citation_function.md` and `schema.json`, without access to the other coder's labels. Two LLM coders are "
         "not a human benchmark; the 2,000-window double-coded human benchmark is still the release criterion.", ""]
    for labels_path, gold in pairs:
        rows = [json.loads(l) for l in open(labels_path, encoding="utf-8")]
        gold_rows = [json.loads(l) for l in open(gold, encoding="utf-8")]
        first = gold_rows[0].get("_model") or "claude-fable-5-1 (interactive session; the L dict next to the file)"
        ids = {r["window_id"] for r in gold_rows}
        both = sum(r["window_id"] in ids for r in rows)
        L += [f"## {gold}", "",
              f"First coder: `{first}`. Second coder: `{rows[0]['_model']}` ({rows[0]['_provider']}, guide version "
              f"`{rows[0]['_prompt_version']}`). {both} of {len(gold_rows)} windows coded by both.", ""]
        for field in ("function", "cited_doc_type"):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                agreement(gold, labels_path, "window_id", field)
            L += [f"### {field}", "", "```", buf.getvalue().rstrip(), "```", ""]
    pathlib.Path(output).write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {output}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("split"); p1.add_argument("--raw", nargs="+", required=True); p1.add_argument("--batch-dir", required=True); p1.add_argument("--size", type=int, default=25)
    p2 = sub.add_parser("merge"); p2.add_argument("--raw", nargs="+", required=True); p2.add_argument("--labels-dir", required=True)
    p2.add_argument("--model", required=True); p2.add_argument("--output", required=True)
    p3 = sub.add_parser("report"); p3.add_argument("--pair", nargs=2, action="append", required=True, metavar=("LABELS", "GOLD"),
                                                   help="second-coder label file and the sample's labeled file; repeat per sample")
    p3.add_argument("--output", required=True)
    a = ap.parse_args()
    if a.cmd == "report":
        report(a.pair, a.output); sys.exit(0)
    raw = read_raw(a.raw)
    if a.cmd == "split":
        split(raw, a.batch_dir, a.size)
    else:
        sys.exit(merge(raw, a.labels_dir, a.model, a.output))
