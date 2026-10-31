"""Figures for the README (no model call; runs in seconds).

    python scripts/make_figures.py

Everything is read from the labeled files and the profiles_*.csv written by aggregate.py, so the figures
regenerate with the pilots (scripts/rebuild_pilot.sh):
  function_overall.png    what the cited paper does: 163 paper citations in the pilot
  function_by_sector.png  shares by sector, 291-window pilot
  function_by_decade.png  shares by decade, nine firms in three sectors (pilot/decades/)
  function_by_firm.png    shares by firm, decade sample pooled over decades
  what_is_cited.png       cited-document type by sector: paper vs patent
"""
import collections, csv, json, pathlib, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aggregate import SCIENCE_TYPES, DISPLAY, load_sector_map  # noqa: E402
OUT = ROOT / "figures"; OUT.mkdir(exist_ok=True)
PILOT = ROOT / "pilot" / "citation_windows_labeled.jsonl"
DECADES = ROOT / "pilot" / "decades" / "citation_windows_labeled.jsonl"

# fixed category order and colors (categorical palette validated for adjacent stacked segments); names from aggregate.DISPLAY
CATS = [("share_foundation", DISPLAY["foundation"], "#2a78d6"),
        ("share_method_or_tool", DISPLAY["method_or_tool"], "#eb6834"),
        ("share_prior_art_distinguished", DISPLAY["prior_art_distinguished"], "#1baf7a"),
        ("share_background_context", DISPLAY["background_context"], "#eda100"),
        ("share_definitional_boilerplate", DISPLAY["definitional_boilerplate"], "#e87ba4"),
        ("other", "Other (materials, bulk lists, own patents)", "#c3c2b7")]
DOC_CATS = [("science", "Paper, book or standards document", "#2a78d6"),
            ("patent", "Patent", "#eb6834"),
            ("other", "Other", "#c3c2b7")]
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Segoe UI", "Helvetica", "Arial", "DejaVu Sans"],
                     "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.facecolor": "white"})


def jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]


def science_rows(path):
    return [r for r in jsonl(path) if not r.get("is_family_duplicate") and r["cited_doc_type"] in SCIENCE_TYPES]


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k, v in list(r.items()):
            if k.startswith("share_") or k.startswith("n_"):
                r[k] = float(v)
        r["other"] = max(0.0, 1.0 - sum(r[k] for k, _, _ in CATS if k != "other"))
    return rows


def shares(functions):
    """Counter of function labels -> row with the share_* keys used by CATS, plus n_windows."""
    n = sum(functions.values())
    row = {k: functions[k[len("share_"):]] / n for k, _, _ in CATS if k != "other"}
    row["other"] = max(0.0, 1.0 - sum(row.values())); row["n_windows"] = n
    return row


def stack(ax, xs, rows, horizontal, cats=CATS, width=0.6, min_label=0.12):
    """Stacked bars with a white gap between segments and labels on segments wide enough to hold them."""
    base = [0.0] * len(rows)
    for key, name, color in cats:
        vals = [r[key] for r in rows]
        if horizontal:
            ax.barh(xs, vals, left=base, height=width, color=color, edgecolor="white", linewidth=1.5, label=name)
        else:
            ax.bar(xs, vals, bottom=base, width=width, color=color, edgecolor="white", linewidth=1.5, label=name)
        for x, b, v in zip(xs, base, vals):
            if v >= min_label and key != "other":
                txt = f"{v:.0%}"; tc = INK if key == "share_background_context" else "white"
                if horizontal:
                    ax.text(b + v / 2, x, txt, ha="center", va="center", color=tc, fontsize=8)
                else:
                    ax.text(x, b + v / 2, txt, ha="center", va="center", color=tc, fontsize=8)
        base = [b + v for b, v in zip(base, vals)]


def pct_axis(ax, horizontal=True):
    ticks = [0, .25, .5, .75, 1]; labels = ["0", "25", "50", "75", "100%"]
    if horizontal:
        ax.set_xlim(0, 1.0); ax.set_xticks(ticks); ax.set_xticklabels(labels); ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    else:
        ax.set_ylim(0, 1.0); ax.set_yticks(ticks); ax.set_yticklabels(labels); ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True); ax.tick_params(length=0)


def grouped_rows(ax, groups, cats, n_key="n_windows"):
    """Horizontal stacked bars in labeled groups: groups = [(header, [(label, row), ...]), ...]."""
    y, ticks, labels, pos, rows = 0.0, [], [], [], []
    for header, items in groups:
        ax.text(-0.012, y, header, ha="right", va="center", color=INK, fontsize=9, fontweight="bold")
        y += 1.0
        for label, row in items:
            ticks.append(y); labels.append(label); pos.append(y); rows.append(row); y += 1.0
        y += 0.5
    stack(ax, pos, rows, horizontal=True, cats=cats)
    ax.set_yticks(ticks); ax.set_yticklabels(labels, color=INK); ax.set_ylim(y - 0.6, -0.6)
    for p, r in zip(pos, rows):
        ax.text(1.01, p, f"n = {int(r[n_key])}", va="center", ha="left", color=INK2, fontsize=8)
    pct_axis(ax)


def figure_overall():
    rows = [r for r in jsonl(PILOT) if not r.get("is_family_duplicate") and r["cited_doc_type"] == "paper"]
    c = collections.Counter(r["function"] for r in rows); n = len(rows)
    counts = [c[k[len("share_"):]] for k, _, _ in CATS[:-1]]; counts.append(n - sum(counts))
    fig, ax = plt.subplots(figsize=(8.2, 3.3))
    ys = list(range(len(CATS)))
    ax.barh(ys, [v / n for v in counts], color=[col for _, _, col in CATS], height=0.62)
    for y, v in zip(ys, counts):
        ax.text(v / n + 0.008, y, f"{v / n:.0%}   n = {v}", va="center", ha="left", color=INK2, fontsize=8)
    ax.set_yticks(ys); ax.set_yticklabels([name for _, name, _ in CATS], color=INK); ax.invert_yaxis()
    ax.set_xlim(0, 0.42); ax.set_xticks([0, .1, .2, .3, .4]); ax.set_xticklabels(["0", "10", "20", "30", "40%"])
    ax.xaxis.grid(True, color=GRID, linewidth=0.6); ax.set_axisbelow(True); ax.tick_params(length=0)
    fig.text(0.02, 0.965, "What the cited paper does in the patent", color=INK, fontsize=11, va="top")
    fig.text(0.02, 0.895, f"{n} in-text citations to papers in 109 patents from 68 firms, priority 2017 or later, family duplicates removed.",
             color=INK2, fontsize=8, va="top")
    fig.tight_layout(rect=(0, 0, 1, 0.85))
    fig.savefig(OUT / "function_overall.png", dpi=200); plt.close(fig)


def figure_sector():
    rows = read_csv(ROOT / "pilot" / "profiles_sector.csv")
    rows.sort(key=lambda r: r["share_foundation"])          # pharma (most foundation) ends up on top
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    xs = list(range(len(rows)))
    stack(ax, xs, rows, horizontal=True)
    ax.set_yticks(xs); ax.set_yticklabels([r["sector"] for r in rows], color=INK)
    pct_axis(ax)
    for x, r in zip(xs, rows):
        ax.text(1.01, x, f"n = {int(r['n_windows'])}", va="center", ha="left", color=INK2, fontsize=8)
    fig.text(0.02, 0.965, "What the cited science does in the patent, by sector", color=INK, fontsize=11, va="top")
    fig.text(0.02, 0.905, "Share of in-text citations to papers, books and standards documents. 291-window pilot, priority 2017 or later, family duplicates removed.",
             color=INK2, fontsize=8, va="top")
    ax.legend(loc="upper left", bbox_to_anchor=(0, 1.17), ncol=3, frameon=False, fontsize=8, handlelength=1.0, columnspacing=1.2)
    fig.tight_layout(rect=(0, 0, 0.97, 0.82))
    fig.savefig(OUT / "function_by_sector.png", dpi=200); plt.close(fig)


def figure_decade():
    rows = read_csv(ROOT / "pilot" / "decades" / "profiles_sector_decade.csv")
    by = {r["sector_decade"]: r for r in rows}
    sectors = ["pharma", "chemicals", "electrical/electronics"]; decades = ["1980s", "1990s", "2000s", "2010s"]
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.9), sharey=True)
    for ax, s in zip(axes, sectors):
        cells = [by.get(f"{s} {d}") for d in decades]
        present = [c for c in cells if c]
        xs = [i for i, c in enumerate(cells) if c]
        stack(ax, xs, present, horizontal=False, width=0.62)
        for i, c in enumerate(cells):
            if not c:
                ax.text(i, 0.5, "no paper\ncitations", ha="center", va="center", color=MUTED, fontsize=8)
        ax.set_xticks(range(4)); ax.set_xticklabels([f"{d}\nn = {int(c['n_windows']) if c else 0}" for d, c in zip(decades, cells)], color=INK)
        pct_axis(ax, horizontal=False)
        ax.set_title(s, loc="left", color=INK, fontsize=10)
    fig.text(0.02, 0.975, "The same shares by decade: nine firms, 1980s to 2010s", color=INK, fontsize=11, va="top")
    fig.text(0.02, 0.92, "Pfizer, Eli Lilly, Bristol-Myers  |  Dow Chemical, Du Pont, Air Products  |  IBM, General Electric, Texas Instruments.\n"
             "Two patents per firm and decade with priority and grant in the decade; electronics adds two more per firm and decade from an \"IEEE\" draw.\n"
             "n = science-citing windows, family duplicates removed.", color=INK2, fontsize=8, va="top", linespacing=1.4)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=6, frameon=False, fontsize=8, handlelength=1.0, columnspacing=1.0, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, 0.07, 1, 0.81))
    fig.savefig(OUT / "function_by_decade.png", dpi=200); plt.close(fig)


def figure_firm():
    rows = science_rows(DECADES)
    by_firm = collections.defaultdict(collections.Counter)
    for r in rows:
        by_firm[r["query_assignee"]][r["function"]] += 1
    short = {"International Business Machines": "IBM"}
    groups = [("Pharma", ["Pfizer", "Eli Lilly", "Bristol-Myers"]),
              ("Chemicals", ["Dow Chemical", "Du Pont", "Air Products"]),
              ("Electronics", ["International Business Machines", "General Electric", "Texas Instruments"])]
    groups = [(g, [(short.get(f, f), shares(by_firm[f])) for f in firms if sum(by_firm[f].values()) >= 5]) for g, firms in groups]
    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    grouped_rows(ax, groups, CATS)
    fig.text(0.02, 0.97, "The same shares by firm, 1980s to 2010s pooled", color=INK, fontsize=11, va="top")
    fig.text(0.02, 0.92, "Decade sample pooled over decades; n = science-citing windows, family duplicates removed.", color=INK2, fontsize=8, va="top")
    ax.legend(loc="upper left", bbox_to_anchor=(0, 1.12), ncol=3, frameon=False, fontsize=8, handlelength=1.0, columnspacing=1.2)
    fig.tight_layout(rect=(0, 0, 0.97, 0.86))
    fig.savefig(OUT / "function_by_firm.png", dpi=200); plt.close(fig)


def figure_cited():
    def doc_shares(rows):
        c = collections.Counter("science" if r["cited_doc_type"] in SCIENCE_TYPES else "patent" if r["cited_doc_type"] == "patent" else "other"
                                for r in rows)
        n = len(rows); return {k: c[k] / n for k in ("science", "patent", "other")} | {"n_windows": n}
    sector_map = load_sector_map()
    pilot = collections.defaultdict(list)
    for r in jsonl(PILOT):
        if not r.get("is_family_duplicate"):
            pilot[sector_map.get(r["assignee"], "other")].append(r)
    decades = collections.defaultdict(list)
    for r in jsonl(DECADES):
        if not r.get("is_family_duplicate"):
            decades[r["sector"]].append(r)
    p_rows = sorted(((s, doc_shares(v)) for s, v in pilot.items()), key=lambda kv: -kv[1]["science"])
    d_rows = [(s, doc_shares(decades[s])) for s in ("pharma", "chemicals", "electrical/electronics")]
    fig, ax = plt.subplots(figsize=(8.2, 5.4))
    grouped_rows(ax, [("Pilot, priority 2017 or later", p_rows), ("Decade sample, 1980s to 2010s", d_rows)], DOC_CATS)
    fig.text(0.02, 0.97, "What the citation window points to: a paper or a patent", color=INK, fontsize=11, va="top")
    fig.text(0.02, 0.925, "Share of citation windows by cited-document type; family duplicates removed. Only the blue share enters the profiles above.",
             color=INK2, fontsize=8, va="top")
    ax.legend(loc="upper left", bbox_to_anchor=(0, 1.07), ncol=3, frameon=False, fontsize=8, handlelength=1.0, columnspacing=1.2)
    fig.tight_layout(rect=(0, 0, 0.97, 0.89))
    fig.savefig(OUT / "what_is_cited.png", dpi=200); plt.close(fig)


if __name__ == "__main__":
    figure_overall(); figure_sector(); figure_decade(); figure_firm(); figure_cited()
    print("wrote", ", ".join(p.name for p in sorted(OUT.glob("*.png"))), "to", OUT)
