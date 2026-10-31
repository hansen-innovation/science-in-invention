"""Structural ("depth") measures of an in-text citation, computed without an LLM.

These are cheap companions to the function label and are released for every citation window:

  structure   standalone | paired | string   how many citation cues share the window (a lone
              "(Smith et al., 2019)" vs. a semicolon-separated list of several works)
  position    first 20% | 20-60% | last 40%  where the citing paragraph falls in the description
              (background section vs. detailed description / examples)
  n_cues      raw count of citation cues in the window

A third measure, how many times the same cited work is invoked across the patent, needs the full
description rather than a window and is computed in the full build (fetch_patents.windows() keeps
paragraph indices for that purpose).

The idea follows Matt Marx's "deep citations" measures (frequency of invocation; standalone vs.
flanked); the pilot tests whether they line up with the LLM function label.

    python depth_measures.py pilot/citation_windows_labeled.jsonl   # prints the cross-tabs, writes pilot/depth_by_function.md
"""
import collections, json, re, sys, pathlib

CUE = re.compile(r"et al\.?|\b(?:19|20)\d{2}[a-c]?\)|\b(?:19|20)\d{2}[a-c]?;|doi:|arXiv|U\.S\. Pat(?:ent)?\.? No|Pat\. No", re.I)
LIST = re.compile(r";\s*(?:[A-Z][A-Za-z\-']+(?:,| et al| and )|\d{4})")
FUNCS = ["foundation", "method_or_tool", "prior_art_distinguished", "data_or_materials_source",
         "background_context", "definitional_boilerplate", "incorporated_reference_list", "own_family_continuation"]
SUBSTANTIVE = {"foundation", "method_or_tool", "prior_art_distinguished", "data_or_materials_source"}
SCIENCE_TYPES = {"paper", "mixed", "standards_doc", "book"}


def structure(text):
    n = len(CUE.findall(text)); lists = len(LIST.findall(text))
    if lists >= 2 or n >= 5:
        return "string"
    if lists == 1 or n >= 3:
        return "paired"
    return "standalone"


def position(para_idx, n_paras):
    f = para_idx / max(1, n_paras)
    return "first 20%" if f < 0.2 else ("20-60%" if f < 0.6 else "last 40%")


def measures(row):
    return {"structure": structure(row["text"]), "n_cues": len(CUE.findall(row["text"])),
            "position": position(row["para_idx"], row["n_desc_paras"])}


def crosstab(rows, key):
    T = collections.defaultdict(collections.Counter)
    for r in rows:
        T[r[key]][r["function"]] += 1
    lines = [f"| {key} | n | " + " | ".join(f.replace("_", " ") for f in FUNCS) + " | substantive share |",
             "|---|---|" + "---|" * (len(FUNCS) + 1)]
    for k in sorted(T):
        c = T[k]; n = sum(c.values()); s = sum(c[f] for f in SUBSTANTIVE) / n
        lines.append(f"| {k} | {n} | " + " | ".join(f"{c[f]} ({100 * c[f] / n:.0f}%)" for f in FUNCS) + f" | {100 * s:.0f}% |")
    return "\n".join(lines)


def main(path):
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    rows = [dict(r, **measures(r)) for r in rows]
    sci = [r for r in rows if not r["is_family_duplicate"] and r["cited_doc_type"] in SCIENCE_TYPES]
    out = ["# Depth measures vs. function label (pilot)", "",
           f"{len(sci)} non-duplicate windows whose cited document is a paper, book, standards document or mixed. "
           "Substantive = foundation + method/tool + data/materials + prior art distinguished; the rest (background, boilerplate, "
           "reference list, own-family) are the non-substantive uses. Structure is detected by counting citation cues in the "
           "window; position is the citing paragraph's index over the number of description paragraphs.", "",
           "## Citation structure", "", crosstab(sci, "structure"), "",
           "## Position in the description", "", crosstab(sci, "position"), "",
           "## Reading", "",
           "- Standalone vs. flanked does not separate substantive from non-substantive use in patents (67-69% substantive in all three groups), "
           "but it shifts *which* substantive use: standalone citations are method/tool far more often, while pairs and strings lean to foundation and background.",
           "- Position does separate them: citations in the first fifth of the description (the background section) are the least substantive; "
           "citations in the examples and detailed description are mostly methods and materials.",
           "- Caveats: a single coder's labels, regex structure detection on an 800-character window, and a recent-corporate-patent sample. "
           "The full build computes these three measures for every in-text citation (plus per-patent invocation counts) and reports them alongside the function label.",
           ]
    text = "\n".join(out)
    dst = pathlib.Path(path).parent / "depth_by_function.md"
    dst.write_text(text, encoding="utf-8")
    with open(pathlib.Path(path).parent / "citation_windows_depth.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({k: r[k] for k in ("window_id", "pn", "para_idx", "n_desc_paras", "structure", "n_cues", "position", "cited_doc_type", "function", "is_family_duplicate")}) + "\n")
    print(text)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "pilot/citation_windows_labeled.jsonl")
