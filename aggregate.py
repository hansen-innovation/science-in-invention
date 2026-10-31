"""Aggregate citation-function labels to science-use profiles: shares by function for each assignee,
sector or grant year. This is the step that turns labeled windows into the released firm-year table.

    python aggregate.py pilot/citation_windows_labeled.jsonl --by assignee   # -> pilot/profiles_assignee.csv
    python aggregate.py pilot/citation_windows_labeled.jsonl --by sector
    python aggregate.py pilot/citation_windows_labeled.jsonl --by year

Rules (same as the proposal): drop family/sibling duplicates; keep windows whose cited document is a
paper, book, standards document or mixed (the document-type filter); report counts next to shares so
small cells are visible. In the full build the unit is the PatentsView disambiguated assignee id and
the profile is joined to firm identifiers through docs/firm_linkage.md.
"""
import argparse, collections, csv, json, pathlib, sys

FUNCS = ["foundation", "method_or_tool", "prior_art_distinguished", "data_or_materials_source",
         "background_context", "definitional_boilerplate", "incorporated_reference_list", "own_family_continuation"]
SCIENCE_TYPES = {"paper", "mixed", "standards_doc", "book"}
SUBSTANTIVE = {"foundation", "method_or_tool", "prior_art_distinguished", "data_or_materials_source"}


def load_sector_map():
    """Assignee -> sector map lives in pilot/labels_pilot.py (SECTOR dict); fall back to 'unknown'."""
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).parent / "pilot"))
        import labels_pilot  # noqa: WPS433
        return getattr(labels_pilot, "SECTOR", {})
    except Exception:  # noqa: BLE001
        return {}


def key_of(row, by, sector_map):
    if by == "assignee":
        return row["assignee"]
    if by == "sector":
        return sector_map.get(row["assignee"], "other")
    if by == "year":
        return (row.get("grant_date") or "")[:4]
    raise ValueError(by)


def aggregate(rows, by, sector_map):
    groups = collections.defaultdict(collections.Counter)
    patents = collections.defaultdict(set)
    for r in rows:
        if r.get("is_family_duplicate") or r.get("cited_doc_type") not in SCIENCE_TYPES:
            continue
        k = key_of(r, by, sector_map)
        groups[k][r["function"]] += 1
        patents[k].add(r["pn"])
    out = []
    for k, c in sorted(groups.items(), key=lambda kv: -sum(kv[1].values())):
        n = sum(c.values())
        row = {by: k, "n_patents": len(patents[k]), "n_windows": n,
               "substantive_share": round(sum(c[f] for f in SUBSTANTIVE) / n, 3)}
        for f in FUNCS:
            row[f"share_{f}"] = round(c[f] / n, 3)
        out.append(row)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("labeled", nargs="?", default="pilot/citation_windows_labeled.jsonl")
    ap.add_argument("--by", default="assignee", choices=["assignee", "sector", "year"])
    ap.add_argument("--min-windows", type=int, default=1)
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(a.labeled, encoding="utf-8")]
    table = [r for r in aggregate(rows, a.by, load_sector_map()) if r["n_windows"] >= a.min_windows]
    dst = pathlib.Path(a.labeled).parent / f"profiles_{a.by}.csv"
    with open(dst, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0].keys())); w.writeheader(); w.writerows(table)
    print(f"{len(table)} rows -> {dst}")
    for r in table[:15]:
        print(f"{str(r[a.by])[:34]:34s} patents {r['n_patents']:3d} windows {r['n_windows']:3d} substantive {r['substantive_share']:.2f} "
              f"found {r['share_foundation']:.2f} method {r['share_method_or_tool']:.2f} prior {r['share_prior_art_distinguished']:.2f} bg {r['share_background_context']:.2f}")


if __name__ == "__main__":
    main()
