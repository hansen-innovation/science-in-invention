"""Firm sample: how eleven firms with long patent records use the science they cite, 1900s-2020s.

Sample (Nov 2, 2026; scripts in local/firms_fields/ of the working copy). Firms are matched on the assignee name (each
assignee of a patent; the British General Electric Company is excluded): AT&T with Bell Telephone Laboratories and
Western Electric, General Electric, IBM, DuPont, Ford, Pfizer, Google (with DeepMind), Microsoft, Nvidia, Boeing and
Walmart. OpenAI and Anthropic were searched and hold no granted patent with an in-text citation to science.
Patents: every firm patent with an in-text Reliance on Science v66 citation to a paper (any confidence), plus patents
granted before 1980 without one whose text carries a strict citation cue (a journal, society, bulletin or book with or
without volume and page). The window finder (fetch_patents.py --cue-early --cue-science) keeps one window per patent:
before 1980 the first window with a science cue and no patent cue, from 1980 the first with a paper cue, otherwise the
first with any science or paper cue that is not a patent-only citation (select_rule). Patents without such a window
(for 1947-1975 often only the printed References Cited block, which the finder cuts) are not in the file.
A window whose text repeats an earlier window of the same firm (same normalized text; continuations and boilerplate
templates) is flagged is_family_duplicate and left out of figures and summaries, as sibling duplicates are in the pilot.
Labels: claude-opus-5-5 as blind Claude Code subagents in batches of 30 (prompts/label_citation_function.md,
schema.json); windows identical to a long-run window reuse its label (_reused_from). labels_firms.jsonl is the source
of truth; never hand-edit citation_windows_labeled.jsonl. Windows are labeled in a fixed pseudo-random order, so a
partly labeled file is a balanced subsample; summary.md states the coverage.
The raw, label and labeled files are gzip-compressed (.jsonl.gz) because of their size.
Run `python labels_firms.py` to write citation_windows_labeled.jsonl.gz and summary.md.
"""
import collections, gzip, json, pathlib, re, sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from labels_pilot import FUNCTIONS  # noqa: E402

def opn(path, mode="r"):
    """Open a text file, gzip-compressed when its name ends in .gz (the firm sample's large files are stored that way)."""
    return gzip.open(path, mode + "t", encoding="utf-8") if str(path).endswith(".gz") else open(path, mode, encoding="utf-8")


SCIENCE_TYPES = ("paper", "book", "standards_doc", "mixed")
DECADES = [f"{y}s" for y in range(1900, 2030, 10)]
LABEL_KEYS = ["cited_doc_type", "function", "confidence", "cited_work_string", "note"]


def build(here, label_file, group, title):
    """Join raw windows and labels, write citation_windows_labeled.jsonl (labeled windows only) and summary.md with
    coverage and function shares by group and decade."""
    gz = ".gz" if (here / "citation_windows_raw.jsonl.gz").exists() else ""
    raw = [json.loads(l) for l in opn(here / ("citation_windows_raw.jsonl" + gz))]
    labels = {}
    for lf in (here / label_file, here / (label_file + ".gz")):
        if lf.exists():
            labels = {r["window_id"]: r for r in map(json.loads, opn(lf))}
    out, seen = [], set()
    for r in sorted(raw, key=lambda r: (str(r.get("grant_date", "")), r["pn"])):
        lab = labels.get(r["window_id"])
        if not lab:
            continue
        assert lab["function"] in FUNCTIONS, lab["function"]
        key = (r[group], re.sub(r"\W+", " ", r["text"].lower()).strip())
        r2 = dict(r); r2.update({k: lab[k] for k in LABEL_KEYS}); r2["is_family_duplicate"] = key in seen
        seen.add(key)
        r2["_model"] = lab.get("_model", ""); r2["_prompt_version"] = lab.get("_prompt_version", "")
        out.append(r2)
    with opn(here / ("citation_windows_labeled.jsonl" + gz), "w") as f:
        for r in out: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    out.sort(key=lambda r: r["window_id"])
    sci = [r for r in out if r["cited_doc_type"] in SCIENCE_TYPES and not r["is_family_duplicate"]]
    ndup = sum(r["is_family_duplicate"] for r in out)
    cell = collections.defaultdict(collections.Counter); nraw = collections.Counter()
    for r in raw:
        nraw[(r[group], r["decade"])] += 1
    for r in sci:
        cell[(r[group], r["decade"])][r["function"]] += 1
    groups = sorted({r[group] for r in raw})
    lines = [f"# {title}", "",
             f"- {len(raw)} windows (one per patent); {len(out)} labeled so far ({len(out) / max(1, len(raw)):.0%}); "
             f"{ndup} repeat the window text of an earlier patent of the same group (continuations, templates) and are "
             f"flagged is_family_duplicate; {len(sci)} of the remaining labeled windows cite papers, books, standards "
             "documents or mixed sets and form the cells below.",
             "", "## Science-citing windows by group and decade (n), function shares, and windows in the sample", "",
             "| Group | Decade | n | " + " | ".join(FUNCTIONS) + " | windows |", "|---|---|---|" + "---|" * len(FUNCTIONS) + "---|"]
    for g in groups:
        for d in DECADES:
            c = cell[(g, d)]; n = sum(c.values())
            if n or nraw[(g, d)]:
                shares = " | ".join(f"{c.get(f, 0) / n:.2f}" if n else "" for f in FUNCTIONS)
                lines.append(f"| {g} | {d} | {n} | {shares} | {nraw[(g, d)]} |")
    lines += ["", "Labels and rationales: `citation_windows_labeled.jsonl` (`note` field). Sampling: the module docstring."]
    (here / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(out)} of {len(raw)} windows labeled, {len(sci)} science-citing -> {here.name}/citation_windows_labeled.jsonl, summary.md")


if __name__ == "__main__":
    build(HERE, "labels_firms.jsonl", "firm", "Firm sample: how eleven firms use the science they cite, 1900s-2020s")
