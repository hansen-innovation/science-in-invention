"""Long-run sample: how science is used in US patents by technology class and decade, 1900s-2020s.

Sampling (Nov 1-2, 2026). Frame: science_in_invention.science_citing_patents, the reusable BigQuery
table of every US grant 1900-2026 that appears in Reliance on Science v66 (any citation) or, before 1976, whose
description matches a citation cue (built once from Google Patents Public Data; local/longrun/ in the working
copy holds bq_build_science_patents.py, bq_sample_longrun.py, select_longrun.py). Technology classes follow
Kelly, Papanikolaou, Seru and Taddy (2021, Figure 8), assigned from the patent's first CPC code. Per class and
decade, candidates are taken in FARM_FINGERPRINT order of the publication number among patents with a sign of an
in-text citation (RoS body citation or cue match); the window finder (fetch_patents.py --source textfile
--cue-early, with the References-Cited cut) keeps the first TARGET patents per cell with a window that looks like a
paper citation, one window per patent (the first such window). The unit is therefore a patent with one in-text
citation window; shares are over patents.

Target: 50 science-citing patents per cell (cited document a paper, book, standards document or mixed set). The base
selection took up to 60 patents per cell (draw "bigquery-longrun"). Fill (Nov 2): for cells still below 50 after
labeling, select_longrun.py --fill appended patents from a second BigQuery draw and from unused candidates, preferring
pre-1980 windows with a journal, venue or book cue and no patent number (draw "bigquery-longrun-fill"; the rule used is
in each row's select_rule), labeled them, and repeated until a cell reached 50 or its candidates ran out. Then a
full-text locator (draw "ros-full-text-locator"): for the cells still short, claude-opus-5-5 read the full text of
every drawn patent that Reliance on Science links to a paper with confidence 5 or more but that was not in the sample
(530 patents), and returned one verbatim passage around a citation of a scientific or technical publication; running-
text passages were appended (all of them in cells below 50), printed reference lists were not. The locator found a
running-text citation in 115 of 210 patents with RoS confidence 8-10 and in 9 of 320 with confidence 5-7; a test of
ten patents at confidence 4 found none, so lower-confidence links were not read. Every RoS-linked patent of a short
cell was drawn. The frame patents never drawn match only the table's loose cue (mostly "journal" as a shaft bearing
or "et al" in drawing headers); the locator found no citation in 30 of them drawn at random. Cells that stay below 50
(mostly before the 1920s and early consumer goods, transportation, engineering and weapons) hold every in-text science
citation the frame, the window finder and the locator could find. Shares are therefore over unequal cell sizes; the
summary and figures print n for every cell.

Labels: claude-opus-5-5 as blind Claude Code subagents on every window (batches of 30,
prompts/label_citation_function.md, schema.json). A blind second pass by claude-fable-5-1 covers 3,017 windows
(stopped at its usage limit; data/3_validate/labels_claude-fable-5-1_longrun.jsonl, gitignored); agreement is in
data/3_validate/results.md. The label file labels_longrun.jsonl (window_id, cited_doc_type, function, confidence,
cited_work_string, note, _model, _provider, _prompt_version) is the source of truth for this sample; never
hand-edit citation_windows_labeled.jsonl.
Run `python labels_longrun.py` to write citation_windows_labeled.jsonl, summary.md and grants_citing_science.csv
(US grants per class and decade and those citing a paper, from the BigQuery count files of the working copy).
"""
import collections, json, pathlib, sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from common.paths import DATA, out as dpath  # noqa: E402
from labels_pilot import FUNCTIONS  # noqa: E402

SCIENCE_TYPES = ("paper", "book", "standards_doc", "mixed")
DECADES = [f"{y}s" for y in range(1900, 2030, 10)]
CLASSES = ["Chemistry and metallurgy", "Electricity and electronics", "Instruments and information", "Health and entertainment",
           "Manufacturing process", "Transportation", "Engineering, construction, mining", "Lighting, heating, nuclear",
           "Agriculture and food", "Consumer goods", "Weapons"]
LABEL_KEYS = ["cited_doc_type", "function", "confidence", "cited_work_string", "note"]


def main():
    raw = [json.loads(l) for l in open(DATA / "0_raw" / "longrun" / "citation_windows_raw.jsonl", encoding="utf-8")]
    labels = {r["window_id"]: r for r in map(json.loads, open(DATA / "2_label" / "longrun" / "labels_longrun.jsonl", encoding="utf-8"))}
    missing = [r["window_id"] for r in raw if r["window_id"] not in labels]
    assert not missing, f"{len(missing)} windows without labels, e.g. {missing[:5]}"
    out = []
    for r in raw:
        lab = labels[r["window_id"]]
        assert lab["function"] in FUNCTIONS, lab["function"]
        r2 = dict(r); r2.update({k: lab[k] for k in LABEL_KEYS}); r2["is_family_duplicate"] = False
        r2["_model"] = lab.get("_model", ""); r2["_prompt_version"] = lab.get("_prompt_version", "")
        out.append(r2)
    with open(dpath("2_label", "longrun", "citation_windows_labeled.jsonl"), "w", encoding="utf-8") as f:
        for r in out: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    sci = [r for r in out if r["cited_doc_type"] in SCIENCE_TYPES]
    cell = collections.defaultdict(collections.Counter)
    for r in sci:
        cell[(r["sector"], r["decade"])][r["function"]] += 1
    c_dt = collections.Counter(r["cited_doc_type"] for r in out)
    pooled = collections.defaultdict(collections.Counter)
    for r in sci:
        pooled[r["decade"]][r["function"]] += 1
    full = sum(sum(cell[(s, d)].values()) >= 50 for s in CLASSES for d in DECADES)
    lines = ["# Long-run sample: how science is used in US patents by technology class and decade, 1900s-2020s", "",
             f"- {len(out)} patents (one citation window each) in {len(CLASSES)} Kelly et al. technology classes and {len(DECADES)} decades; "
             f"{len(sci)} cite papers, books, standards documents or mixed sets (the rest cite patents only or the cue was not a citation).",
             f"- {full} of {len(CLASSES) * len(DECADES)} class-decade cells hold 50 or more science-citing patents.",
             "- Cited document type: " + ", ".join(f"{k} {v}" for k, v in c_dt.most_common()) + ".",
             "", "## All classes pooled: science-citing patents by decade (n) and function shares", "",
             "| Decade | n | " + " | ".join(FUNCTIONS) + " |", "|---|---|" + "---|" * len(FUNCTIONS)]
    for d in DECADES:
        c = pooled[d]; n = sum(c.values())
        lines.append(f"| {d} | {n} | " + " | ".join(f"{c.get(f, 0) / n:.2f}" for f in FUNCTIONS) + " |")
    lines += ["", "## Science-citing patents by class and decade (n) and function shares", "",
             "| Class | Decade | n | " + " | ".join(FUNCTIONS) + " |", "|---|---|---|" + "---|" * len(FUNCTIONS)]
    for s in CLASSES:
        for d in DECADES:
            c = cell[(s, d)]; n = sum(c.values())
            if n:
                lines.append(f"| {s} | {d} | {n} | " + " | ".join(f"{c.get(f, 0) / n:.2f}" for f in FUNCTIONS) + " |")
    lines += ["", "Counts behind every share: `profiles_sector_decade.csv` (from `../../aggregate.py`; `sector` holds the class).",
              "Labels and rationales: `citation_windows_labeled.jsonl` (`note` field). Sampling: module docstring of `labels_longrun.py`."]
    dpath("4_aggregate", "longrun", "summary.md").write_text("\n".join(lines), encoding="utf-8")
    write_grant_counts()
    print(f"{len(out)} labeled windows, {len(sci)} science-citing -> citation_windows_labeled.jsonl, summary.md")


def write_grant_counts():
    """grants_citing_science.csv (panel A of the long-run overview figure): US grants per class and decade and those with
    at least one Reliance on Science v66 citation to a paper. Rewritten from the BigQuery count files when they are
    present (working copy: ../../../data/1_fetch/longrun/); otherwise the committed file is kept."""
    src = DATA / "1_fetch" / "longrun"
    if not (src / "universe_counts.csv").exists():
        return
    import csv
    uni = {(r["cls"], int(r["decade"])): int(r["n_patents"]) for r in csv.DictReader(open(src / "universe_counts.csv", encoding="utf-8"))}
    ros = {(r["cls"], int(r["decade"])): int(r["n_ros"]) for r in csv.DictReader(open(src / "science_counts.csv", encoding="utf-8"))}
    with open(dpath("4_aggregate", "longrun", "grants_citing_science.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["class", "decade", "n_grants", "n_grants_citing_paper"])
        for s in CLASSES:
            for d in DECADES:
                k = (s, int(d[:4]))
                w.writerow([s, d, uni.get(k, 0), ros.get(k, 0)])


if __name__ == "__main__":
    main()
