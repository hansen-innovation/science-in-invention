"""Validation utilities shared by the four pipelines.

Two jobs:
1. `agreement`: compare two label files on the same ids (e.g., hand labels vs LLM labels,
   or coder A vs coder B) and report per-class precision/recall, overall accuracy and
   Cohen's kappa for one categorical field.
2. `schema_check`: verify every row of a JSONL file against the pipeline schema
   (required keys present, enums respected, numbers numeric).

Usage:
    python 3_validate/validate.py agreement --a data/2_label/pilot/citation_windows_labeled.jsonl \
        --b data/3_validate/labels_<model>.jsonl --id window_id --field function
    python 3_validate/validate.py schema_check --schema 2_label/schema.json --input data/2_label/pilot/citation_windows_labeled.jsonl

The release standard for every dataset in this repo: a stratified hand-coded benchmark
of at least 1,000 units, double-coded on 20%, with precision and recall reported by
stratum, and the benchmark re-run on every prompt or model change.
"""
import argparse, collections, json, sys


def opn(path):
    """Open a JSONL file for reading, gzip-compressed (.gz) or plain."""
    import gzip
    return gzip.open(path, "rt", encoding="utf-8") if str(path).endswith(".gz") else open(path, encoding="utf-8")


def load(path, id_field):
    return {r[id_field]: r for r in (json.loads(l) for l in opn(path))}


def kappa(pairs):
    n = len(pairs)
    if n == 0:
        return float("nan")
    po = sum(1 for a, b in pairs if a == b) / n
    ca = collections.Counter(a for a, _ in pairs); cb = collections.Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def agreement(a_path, b_path, id_field, field):
    A, B = load(a_path, id_field), load(b_path, id_field)
    ids = sorted(set(A) & set(B))
    pairs = [(A[i].get(field), B[i].get(field)) for i in ids]
    acc = sum(1 for a, b in pairs if a == b) / max(1, len(pairs))
    print(f"n={len(pairs)} accuracy={acc:.3f} kappa={kappa(pairs):.3f}")
    labels = sorted({a for a, _ in pairs} | {b for _, b in pairs}, key=str)
    print(f"{'label':32} {'n_ref':>6} {'prec':>6} {'rec':>6}")
    for lab in labels:
        tp = sum(1 for a, b in pairs if a == lab and b == lab)
        fp = sum(1 for a, b in pairs if a != lab and b == lab)
        fn = sum(1 for a, b in pairs if a == lab and b != lab)
        prec = tp / (tp + fp) if tp + fp else float("nan"); rec = tp / (tp + fn) if tp + fn else float("nan")
        print(f"{str(lab):32} {tp + fn:6d} {prec:6.2f} {rec:6.2f}")
    conf = collections.Counter(pairs)
    print("\nmost common disagreements:")
    for (a, b), c in conf.most_common():
        if a != b:
            print(f"  {a} -> {b}: {c}")


def schema_check(schema_path, input_path):
    schema = json.load(open(schema_path, encoding="utf-8"))
    props, req = schema["properties"], schema.get("required", [])
    bad = 0
    opened = opn(input_path)
    for n, line in enumerate(opened, 1):
        r = json.loads(line)
        for k in req:
            if k not in r:
                print(f"row {n}: missing {k}"); bad += 1
        for k, spec in props.items():
            if k in r and "enum" in spec and r[k] not in spec["enum"] and r[k] not in (None, ""):
                print(f"row {n}: {k}={r[k]!r} not in enum"); bad += 1
            if k in r and spec.get("type") == "number" and r[k] is not None and not isinstance(r[k], (int, float)):
                print(f"row {n}: {k} not numeric"); bad += 1
    print(f"{input_path}: {bad} problems")
    return bad


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("agreement"); p1.add_argument("--a", required=True); p1.add_argument("--b", required=True)
    p1.add_argument("--id", required=True); p1.add_argument("--field", required=True)
    p2 = sub.add_parser("schema_check"); p2.add_argument("--schema", required=True); p2.add_argument("--input", required=True)
    a = ap.parse_args()
    if a.cmd == "agreement":
        agreement(a.a, a.b, a.id, a.field)
    else:
        sys.exit(1 if schema_check(a.schema, a.input) else 0)
