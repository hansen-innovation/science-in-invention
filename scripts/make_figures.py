"""Figures for the README (no model call; runs in seconds).

    python scripts/make_figures.py

Everything is read from the labeled files and the profiles_*.csv written by aggregate.py, so the figures
regenerate with the pilots (scripts/rebuild_pilot.sh). One template for all five: horizontal bars in labeled
groups, counts at the right, title and subtitle at the top left.
  function_overall.png    what the cited paper does: 316 paper-citing windows in the pilot, all eight labels
  function_by_sector.png  shares by sector, 515-window pilot
  function_by_decade.png  shares by sector and decade, nine firms (pilot/decades/)
  function_by_firm.png    shares by firm, decade sample pooled over decades
  what_is_cited.png       cited-document type by sector: paper vs patent
"""
import collections, csv, json, pathlib, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.transforms import blended_transform_factory  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aggregate import SCIENCE_TYPES, DISPLAY, FUNCS, key_of, load_sector_map  # noqa: E402
OUT = ROOT / "figures"; OUT.mkdir(exist_ok=True)
PILOT = ROOT / "pilot" / "citation_windows_labeled.jsonl"
DECADES = ROOT / "pilot" / "decades" / "citation_windows_labeled.jsonl"

# Palette: checked with the dataviz palette validator (light surface): lightness band, chroma floor, adjacent
# color-vision-deficiency separation (worst 8.2) and normal-vision separation (worst 18.1) all pass. The gold sits
# below 3:1 on white, so every segment wide enough carries its own label. Grey is the neutral fold for "Other".
PAL = {"foundation": "#3E6DB5", "method_or_tool": "#D9742B", "prior_art_distinguished": "#2F9E6E",
       "background_context": "#C99A2E", "definitional_boilerplate": "#B5579B", "other": "#CBC7BF"}
MAIN = ["foundation", "method_or_tool", "prior_art_distinguished", "background_context", "definitional_boilerplate"]
CATS = [(f, DISPLAY[f], PAL[f]) for f in MAIN] + [("other", "Other", PAL["other"])]
DOC_CATS = [("science", "Paper, book, standards or mixed", PAL["foundation"]), ("patent", "Patent", "#8E8A83"),
            ("other", "Other", "#DAD6CF")]
INK, INK2, MUTED, GRID, BASE = "#1a1a1a", "#5a5854", "#8a8781", "#e8e6e1", "#c9c6bf"
W = 8.4  # figure width, inches
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Segoe UI", "Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
                     "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white"})


def jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]


def science_rows(path):
    return [r for r in jsonl(path) if not r.get("is_family_duplicate") and r["cited_doc_type"] in SCIENCE_TYPES]


def read_csv(path):
    """Keep profile order and metadata; plot exact counts to avoid rounding rounded CSV shares."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    by = path.stem.removeprefix("profiles_")
    counts = collections.defaultdict(collections.Counter)
    sector_map = load_sector_map()
    for row in science_rows(path.parent / "citation_windows_labeled.jsonl"):
        counts[key_of(row, by, sector_map)][row["function"]] += 1
    out = []
    for r in rows:
        c = counts[r[by]]
        if sum(c.values()) != int(r["n_windows"]):
            raise ValueError(f"{path}: {r[by]} count differs from the labeled windows; rebuild profiles first")
        d = shares(c); d["key"] = r
        out.append(d)
    return out


def shares(counter):
    """Counter of function labels -> {category: share, 'n': count}."""
    n = sum(counter.values())
    d = {f: counter[f] / n for f in MAIN}
    d["other"] = max(0.0, 1.0 - sum(d.values())); d["n"] = n
    return d


def luminance(hexcolor):
    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hexcolor[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def label_color(hexcolor):
    return "white" if luminance(hexcolor) < 0.30 else INK


def cap(s):
    return s[:1].upper() + s[1:]


def canvas(groups, title, subtitle, legend=None, sub_lines=2):
    """Figure sized to its rows. groups: [(header or None, [(label, row), ...]), ...]."""
    units = sum(len(items) + (1.1 if header else 0) for header, items in groups) + 0.4 * (len(groups) - 1)
    rows_in = 0.34 * units + 0.15
    top_in = 0.52 + 0.16 * sub_lines + (0.46 if legend else 0.12)
    bottom_in = 0.42
    H = top_in + rows_in + bottom_in
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.215, bottom_in / H, 0.685, rows_in / H])
    fig.text(0.03, 1 - 0.14 / H, title, fontsize=12.5, fontweight="semibold", color=INK, va="top")
    fig.text(0.03, 1 - 0.44 / H, subtitle, fontsize=8.5, color=INK2, va="top", linespacing=1.45)
    if legend:
        handles = [Patch(facecolor=c, edgecolor="none") for _, _, c in legend]
        fig.legend(handles, [n for _, n, _ in legend], loc="upper left", bbox_to_anchor=(0.03, 1 - (top_in - 0.42) / H),
                   ncol=3, frameon=False, fontsize=8.5, labelcolor=INK2, handlelength=1.0, handleheight=1.0,
                   columnspacing=1.8, handletextpad=0.6, borderaxespad=0)
    return fig, ax


def style_x(ax, x_max=1.0):
    ticks = [0, .25, .5, .75, 1.0] if x_max == 1.0 else [t for t in (0, .1, .2, .3, .4, .5) if t <= x_max]
    ax.set_xlim(0, x_max); ax.set_xticks(ticks)
    ax.set_xticklabels([f"{int(round(t * 100))}" + ("%" if t == ticks[-1] else "") for t in ticks], fontsize=8, color=MUTED)
    ax.xaxis.grid(True, color=GRID, linewidth=0.7); ax.set_axisbelow(True); ax.tick_params(length=0, pad=4)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(BASE); ax.spines["bottom"].set_linewidth(0.8)


def draw_rows(ax, groups, cats, show_n=True, min_label=0.08):
    """Stacked horizontal bars, one row per item, 1.2px white gaps, labels in segments wide enough to hold them."""
    y, ticks, labels = 0.0, [], []
    for gi, (header, items) in enumerate(groups):
        if gi:
            y += 0.4
        if header:  # in the label column, flush with the title, clear of the gridlines
            ax.text(0.03, y, header.upper(), transform=blended_transform_factory(ax.figure.transFigure, ax.transData),
                    ha="left", va="center", fontsize=7.5, fontweight="bold", color=MUTED); y += 1.1
        for label, row in items:
            left = 0.0
            for key, _, color in cats:
                v = row[key]
                if v > 0:
                    ax.barh(y, v, left=left, height=0.64, color=color, edgecolor="white", linewidth=1.2)
                    if v >= min_label and key != "other":
                        ax.text(left + v / 2, y, f"{v:.0%}", ha="center", va="center", fontsize=8, color=label_color(color))
                left += v
            if show_n:
                ax.text(1.015, y, f"n = {row['n']}", va="center", ha="left", fontsize=7.5, color=MUTED)
            ticks.append(y); labels.append(label); y += 1.0
    ax.set_ylim(y - 0.45, -0.6); ax.set_yticks(ticks); ax.set_yticklabels(labels, fontsize=9, color=INK)
    style_x(ax)


def figure_overall():
    rows = [r for r in jsonl(PILOT) if not r.get("is_family_duplicate") and r["cited_doc_type"] == "paper"]
    c = collections.Counter(r["function"] for r in rows); n = len(rows)
    groups = [(None, [(DISPLAY[f], {"f": f, "v": c[f] / n, "c": c[f]}) for f in FUNCS])]
    fig, ax = canvas(groups, "What the cited paper does in the patent",
                     f"{n} paper-citing windows after deduplication; full pilot: 200 patents, 127 assignees, priority 2017 or later.\n"
                     "Other in the stacked charts combines materials/data sources, reference-list entries and own earlier patents.")
    for y, (_, r) in enumerate(groups[0][1]):
        ax.barh(y, r["v"], height=0.64, color=PAL.get(r["f"], PAL["other"]))
        ax.text(r["v"] + 0.007, y, f"{r['v']:.0%}   {r['c']} of {n}", va="center", ha="left", fontsize=8, color=INK2)
    ax.set_ylim(len(FUNCS) - 0.45, -0.6); ax.set_yticks(range(len(FUNCS))); ax.set_yticklabels([DISPLAY[f] for f in FUNCS], fontsize=9, color=INK)
    style_x(ax, x_max=0.42)
    fig.savefig(OUT / "function_overall.png", dpi=200); plt.close(fig)


def figure_sector():
    rows = read_csv(ROOT / "pilot" / "profiles_sector.csv")
    rows.sort(key=lambda r: -r["foundation"])
    groups = [(None, [(cap(r["key"]["sector"]), r) for r in rows])]
    fig, ax = canvas(groups, "What the cited science does in the patent, by sector",
                     "395 windows citing papers, books, standards or mixed sets, after family duplicates are removed.\n"
                     "Full pilot: 515 windows, 200 patents, 127 assignees; priority 2017 or later. n = plotted windows.", legend=CATS)
    draw_rows(ax, groups, CATS)
    fig.savefig(OUT / "function_by_sector.png", dpi=200); plt.close(fig)


def figure_decade():
    rows = {r["key"]["sector_decade"]: r for r in read_csv(ROOT / "pilot" / "decades" / "profiles_sector_decade.csv")}
    sectors = [("Pharma", "pharma"), ("Chemicals", "chemicals"), ("Electronics", "electrical/electronics")]
    groups = [(h, [(d, rows[f"{s} {d}"]) for d in ("1980s", "1990s", "2000s", "2010s") if f"{s} {d}" in rows]) for h, s in sectors]
    fig, ax = canvas(groups, "The same shares by decade: nine firms, 1980s to 2010s",
                     "Pfizer, Eli Lilly, Bristol-Myers  |  Dow Chemical, Du Pont, Air Products  |  IBM, General Electric, Texas Instruments.\n"
                     "Up to two patents per firm and decade with priority and grant in the decade (electronics: up to four, two draws).\n"
                     "n = science-citing windows, family duplicates removed.", legend=CATS, sub_lines=3)
    draw_rows(ax, groups, CATS)
    fig.savefig(OUT / "function_by_decade.png", dpi=200); plt.close(fig)


def figure_firm():
    by_firm = collections.defaultdict(collections.Counter)
    for r in science_rows(DECADES):
        by_firm[r["query_assignee"]][r["function"]] += 1
    short = {"International Business Machines": "IBM"}
    sectors = [("Pharma", ["Pfizer", "Eli Lilly", "Bristol-Myers"]), ("Chemicals", ["Dow Chemical", "Du Pont", "Air Products"]),
               ("Electronics", ["International Business Machines", "General Electric", "Texas Instruments"])]
    groups = [(h, [(short.get(f, f), shares(by_firm[f])) for f in firms if sum(by_firm[f].values()) >= 5]) for h, firms in sectors]
    fig, ax = canvas(groups, "The same shares by firm, 1980s to 2010s pooled",
                     "Decade sample pooled over decades; n = science-citing windows, family duplicates removed.", legend=CATS, sub_lines=1)
    draw_rows(ax, groups, CATS)
    fig.savefig(OUT / "function_by_firm.png", dpi=200); plt.close(fig)


def figure_cited():
    def doc_shares(rows):
        c = collections.Counter("science" if r["cited_doc_type"] in SCIENCE_TYPES else "patent" if r["cited_doc_type"] == "patent" else "other"
                                for r in rows)
        n = len(rows); return {k: c[k] / n for k in ("science", "patent", "other")} | {"n": n}
    sector_map = load_sector_map()
    pilot, decades = collections.defaultdict(list), collections.defaultdict(list)
    for r in jsonl(PILOT):
        if not r.get("is_family_duplicate"):
            pilot[r.get("sector") or sector_map.get(r["assignee"], "other")].append(r)
    for r in jsonl(DECADES):
        if not r.get("is_family_duplicate"):
            decades[r["sector"]].append(r)
    p_rows = sorted(((cap(s), doc_shares(v)) for s, v in pilot.items()), key=lambda kv: -kv[1]["science"])
    d_rows = [(cap(s), doc_shares(decades[s])) for s in ("pharma", "chemicals", "electrical/electronics")]
    groups = [("Pilot, priority 2017 or later", p_rows), ("Decade sample, 1980s to 2010s", d_rows)]
    fig, ax = canvas(groups, "What the citation window points to: a paper or a patent",
                     "Share of citation windows by cited-document type, family duplicates removed. Only the blue share enters the profiles above.",
                     legend=DOC_CATS, sub_lines=1)
    draw_rows(ax, groups, DOC_CATS)
    fig.savefig(OUT / "what_is_cited.png", dpi=200); plt.close(fig)


if __name__ == "__main__":
    figure_overall(); figure_sector(); figure_decade(); figure_firm(); figure_cited()
    print("wrote", ", ".join(p.name for p in sorted(OUT.glob("*.png"))), "to", OUT)
