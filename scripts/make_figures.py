"""Figures for the README (no model call; runs in seconds).

    python scripts/make_figures.py

Everything is read from the labeled files, the profiles_*.csv written by aggregate.py and the long-run count files, so
the figures regenerate with the pilots (scripts/rebuild_pilot.sh). All figures share the journal framing of Kelly,
Papanikolaou, Seru and Taddy (2021, Figure 5): 'Figure n. Title' centred on top in Times small capitals, panels in
Arial with black axes and outlines, short notes below whose numbers are computed here. Numbering follows the README.
  longrun_overall.png     Figure 1: share of grants citing science by class (rows) and role of the cited work by decade
  longrun_by_class.png    Figure 2: role of the cited work by class and decade, long-run sample
  function_overall.png    Figure 3: what the cited paper does, paper-citing windows of the pilot
  function_by_sector.png  Figure 4: shares by sector, pilot
  function_by_firm.png    Figure 5: shares by firm, decade sample pooled over decades
  what_is_cited.png       Figure 6: cited-document type, paper vs patent
  function_by_decade.png  Figure A1: shares by sector and decade, nine-firm decade sample (superseded by Figure 2)
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

# Palette after Kelly, Papanikolaou, Seru and Taddy (2021, Figure 5): blues for the roles in which the cited work
# enters the invention (navy, blue, sky blue), grey for "Other", gold and red for passing mentions. Dataviz validator
# (light surface): adjacent colour-vision-deficiency separation (worst 12.7) and normal-vision separation (worst 15.1)
# pass; the navy, gold and grey sit outside its lightness band by design and sky blue, gold and grey fall below 3:1 on
# white, so segments carry black outlines and their own labels where wide enough.
PAL = {"foundation": "#2E3F8F", "method_or_tool": "#3D72B8", "prior_art_distinguished": "#3DB7E9",
       "background_context": "#E8262B", "definitional_boilerplate": "#F3A529", "other": "#D4D4D4"}
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


def paper_rc(fn):
    """Run a figure function with the journal fonts (PAPER_SANS, defined with the long-run figures below)."""
    def run(*a, **k):
        with plt.rc_context(PAPER_SANS):
            return fn(*a, **k)
    run.__name__, run.__doc__ = fn.__name__, fn.__doc__
    return run


def canvas(groups, title, legend=None, note_lines=3):
    """Journal framing shared by the pilot figures: 'Figure n. Title' centred on top, the legend under it, horizontal
    bars in labeled groups, room for short notes below. groups: [(header or None, [(label, row), ...]), ...].
    Returns the figure, the axes and the baseline for paper_notes."""
    units = sum(len(items) + (1.0 if header else 0) for header, items in groups) + 0.4 * (len(groups) - 1)
    rows_in = 0.30 * units + 0.1
    top_in = 0.55 + (0.45 if legend else 0.1)
    bottom_in = 0.62 + 0.19 * note_lines
    H = top_in + rows_in + bottom_in
    fig = plt.figure(figsize=(7.0, H))
    paper_title(fig, 1 - 0.32 / H, title)
    ax = fig.add_axes([0.31, bottom_in / H, 0.63, rows_in / H])
    if legend:
        fig.legend([Patch(facecolor=c, edgecolor=INK, linewidth=0.5) for _, _, c in legend], [n for _, n, _ in legend],
                   loc="upper center", bbox_to_anchor=(0.5, 1 - 0.50 / H), ncol=3, frameon=False, fontsize=8, labelcolor=INK,
                   handlelength=1.0, handleheight=1.0, columnspacing=1.6, handletextpad=0.5, borderaxespad=0)
    return fig, ax, (bottom_in - 0.62) / H


def style_x(ax, x_max=1.0):
    """Black axes, outward ticks, no grid; tick labels in percent."""
    ticks = [0, .25, .5, .75, 1.0] if x_max == 1.0 else [t for t in (0, .1, .2, .3, .4, .5) if t <= x_max]
    ax.set_xlim(0, x_max); ax.set_xticks(ticks)
    ax.set_xticklabels([f"{int(round(t * 100))}" for t in ticks], fontsize=8, color=INK)
    ax.set_xlabel("Percent", fontsize=8, color=INK, labelpad=3)
    ax.tick_params(axis="x", length=3, width=0.8, color=INK, pad=3)
    ax.tick_params(axis="y", length=0, pad=5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK); ax.spines[s].set_linewidth(0.8)


def draw_rows(ax, groups, cats, show_n=True, min_label=0.12):
    """Stacked horizontal bars with thin black outlines, one row per item; n in parentheses after the row label; shares
    printed only in segments of 12 percent or more."""
    y, ticks, labels = 0.0, [], []
    for gi, (header, items) in enumerate(groups):
        if gi:
            y += 0.4
        if header:   # group header in italics in the label column
            ax.text(0.04, y, header, transform=blended_transform_factory(ax.figure.transFigure, ax.transData),
                    ha="left", va="center", fontsize=8.5, style="italic", color=INK); y += 1.0
        for label, row in items:
            left = 0.0
            for key, _, color in cats:
                v = row[key]
                if v > 0:
                    ax.barh(y, v, left=left, height=0.62, color=color, edgecolor=INK, linewidth=0.5)
                    if v >= min_label and key != "other":
                        ax.text(left + v / 2, y, f"{v * 100:.0f}", ha="center", va="center", fontsize=7.5, color=label_color(color))
                left += v
            ticks.append(y); labels.append(f"{label} ({row['n']})" if show_n else label); y += 1.0
    ax.set_ylim(y - 0.45, -0.6); ax.set_yticks(ticks); ax.set_yticklabels(labels, fontsize=8.5, color=INK)
    style_x(ax)


@paper_rc
def figure_overall():
    rows = [r for r in jsonl(PILOT) if not r.get("is_family_duplicate") and r["cited_doc_type"] == "paper"]
    c = collections.Counter(r["function"] for r in rows); n = len(rows)
    groups = [(None, [(DISPLAY[f], None) for f in FUNCS])]
    fig, ax, notes_y = canvas(groups, "Figure 3. What the Cited Paper Does in the Patent", note_lines=2)
    for y, f in enumerate(FUNCS):
        v = c[f] / n
        ax.barh(y, v, height=0.62, color=PAL.get(f, PAL["other"]), edgecolor=INK, linewidth=0.5)
        pct = "<1" if 0 < v * 100 < 0.5 else f"{v * 100:.0f}"
        ax.text(v + 0.006, y, f"{pct} ({c[f]})", va="center", ha="left", fontsize=8, color=INK)
    ax.set_ylim(len(FUNCS) - 0.45, -0.6); ax.set_yticks(range(len(FUNCS))); ax.set_yticklabels([DISPLAY[f] for f in FUNCS], fontsize=8.5, color=INK)
    style_x(ax, x_max=0.42)
    paper_notes(fig, notes_y, f"Share of the {n} paper-citing windows of the pilot (patents with priority 2017 or later; family "
                "duplicates removed) by the role of the cited paper; counts in parentheses. Roles are coded by claude-fable-5-1.")
    fig.savefig(OUT / "function_overall.png", dpi=200, bbox_inches="tight", pad_inches=0.15); plt.close(fig)


@paper_rc
def figure_sector():
    rows = read_csv(ROOT / "pilot" / "profiles_sector.csv")
    rows.sort(key=lambda r: -r["foundation"])
    groups = [(None, [(cap(r["key"]["sector"]), r) for r in rows])]
    fig, ax, notes_y = canvas(groups, "Figure 4. What the Cited Science Does, by Sector", legend=CATS)
    draw_rows(ax, groups, CATS)
    paper_notes(fig, notes_y, f"Shares of the {sum(r['n'] for r in rows)} pilot windows citing papers, books, standards documents "
                "or mixed sets (family duplicates removed), by sector; windows in parentheses. Other combines source of materials "
                "or data, reference list entry and own earlier patent. Roles are coded by claude-fable-5-1.")
    fig.savefig(OUT / "function_by_sector.png", dpi=200, bbox_inches="tight", pad_inches=0.15); plt.close(fig)


@paper_rc
def figure_decade():
    rows = {r["key"]["sector_decade"]: r for r in read_csv(ROOT / "pilot" / "decades" / "profiles_sector_decade.csv")}
    sectors = [("Pharma", "pharma"), ("Chemicals", "chemicals"), ("Electronics", "electrical/electronics")]
    decades = [f"{y}s" for y in range(1900, 2030, 10)]
    groups = [(h, [(d, rows[f"{s} {d}"]) for d in decades if f"{s} {d}" in rows]) for h, s in sectors]
    fig, ax, notes_y = canvas(groups, "Figure A1. The Same Shares by Decade, Decade Sample", legend=CATS)
    draw_rows(ax, groups, CATS)
    paper_notes(fig, notes_y, "Pfizer, Eli Lilly and Bristol-Myers (pharma), Dow Chemical, Du Pont and Air Products (chemicals), "
                "and IBM, General Electric and Texas Instruments (electronics) in the 1980s to 2010s; the same firms or period peers in "
                "other decades. Science-citing windows in parentheses. Roles are coded by claude-fable-5-1.")
    fig.savefig(OUT / "function_by_decade.png", dpi=200, bbox_inches="tight", pad_inches=0.15); plt.close(fig)


@paper_rc
def figure_firm():
    by_firm = collections.defaultdict(collections.Counter)
    canon = {"IBM": "International Business Machines"}
    for r in science_rows(DECADES):
        by_firm[canon.get(r["query_assignee"], r["query_assignee"])][r["function"]] += 1
    short = {"International Business Machines": "IBM"}
    sectors = [("Pharma", ["Pfizer", "Eli Lilly", "Bristol-Myers"]), ("Chemicals", ["Dow Chemical", "Du Pont", "Air Products"]),
               ("Electronics", ["International Business Machines", "General Electric", "Texas Instruments"])]
    groups = [(h, [(short.get(f, f), shares(by_firm[f])) for f in firms if sum(by_firm[f].values()) >= 5]) for h, firms in sectors]
    fig, ax, notes_y = canvas(groups, "Figure 5. The Same Shares by Firm", legend=CATS, note_lines=2)
    draw_rows(ax, groups, CATS)
    paper_notes(fig, notes_y, "The nine firms of the decade sample, all decades pooled; science-citing windows in parentheses "
                "(family duplicates removed). Roles are coded by claude-fable-5-1.")
    fig.savefig(OUT / "function_by_firm.png", dpi=200, bbox_inches="tight", pad_inches=0.15); plt.close(fig)


@paper_rc
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
    groups = [("Pilot, priority 2017 or later", p_rows), ("Decade sample, 1900s to 2020s", d_rows)]
    fig, ax, notes_y = canvas(groups, "Figure 6. What the Citation Window Points To", legend=DOC_CATS, note_lines=2)
    draw_rows(ax, groups, DOC_CATS)
    paper_notes(fig, notes_y, "Share of citation windows by type of cited document, family duplicates removed; windows in "
                "parentheses. Only science (papers, books, standards documents and mixed sets) enters the role profiles.")
    fig.savefig(OUT / "what_is_cited.png", dpi=200, bbox_inches="tight", pad_inches=0.15); plt.close(fig)


LONGRUN = ROOT / "pilot" / "longrun" / "citation_windows_labeled.jsonl"
LONGRUN_COUNTS = ROOT / "pilot" / "longrun" / "grants_citing_science.csv"
LR_CLASSES = ["Chemistry and metallurgy", "Electricity and electronics", "Instruments and information", "Health and entertainment",
              "Manufacturing process", "Transportation", "Engineering, construction, mining", "Lighting, heating, nuclear",
              "Agriculture and food", "Consumer goods", "Weapons"]
LR_DECADES = [f"{y}s" for y in range(1900, 2030, 10)]


LR_BAND_LABEL = {"foundation": "Basis of the\ninvention", "prior_art_distinguished": "Prior approach\nimproved on",
                 "definitional_boilerplate": "Definition\nonly"}
# Kelly et al. (2021, Figure 5) order: blues for the roles in which the cited work enters the invention, grey "Other"
# in the middle, warm colours for passing mentions.
LR_CATS = [(f, DISPLAY[f], PAL[f]) for f in ("foundation", "method_or_tool", "prior_art_distinguished")] + \
          [("other", "Other", PAL["other"])] + \
          [(f, DISPLAY[f], PAL[f]) for f in ("definitional_boilerplate", "background_context")]
KELLY_NAVY = "#3B4FA0"
# by-class figure: one colour per role column (the user's choice, Nov 2, 2026); validated earlier as a categorical set
GRID_COLOR = {"foundation": "#3E6DB5", "method_or_tool": "#D9742B", "prior_art_distinguished": "#2F9E6E",
              "background_context": "#C99A2E", "definitional_boilerplate": "#B5579B"}
# journal framing: panels in Helvetica (Arial on Windows), caption and notes in Times, as in AER: Insights
PAPER_SANS = {"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"]}
PAPER_SERIF = ["Times New Roman", "DejaVu Serif"]


def function_shares(counter):
    """Shares of the main functions plus 'other' (everything else) in a Counter of functions."""
    n = sum(counter.values())
    if not n:
        return {}
    out = {f: counter[f] / n for f in MAIN}
    out["other"] = 1 - sum(out.values())
    return out


def kelly_rows(fig, x0, width, top, bottom, n_rows):
    """Axes for Kelly et al. (2021, Figure 5, left panel) rows: rows touch, so their left spines form one black axis
    with an arrowhead at the top; each row has a tick at its baseline; only the last row shows the time axis."""
    h = (top - bottom) / n_rows
    axes = []
    for k in range(n_rows):
        ax = fig.add_axes([x0, top - (k + 1) * h, width, h])
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.spines["left"].set_color(INK); ax.spines["left"].set_linewidth(0.8)
        ax.spines["bottom"].set_visible(k == n_rows - 1); ax.spines["bottom"].set_color(INK); ax.spines["bottom"].set_linewidth(0.8)
        ax.tick_params(axis="y", length=3, width=0.8, color=INK, pad=4)
        ax.tick_params(axis="x", length=3, width=0.8, color=INK, labelsize=8, labelcolor=INK)
        axes.append(ax)
    axes[0].annotate("", xy=(0, 1.10), xytext=(0, 0.6), xycoords="axes fraction",
                     arrowprops=dict(arrowstyle="-|>,head_length=0.45,head_width=0.2", color=INK, lw=0.8, shrinkA=0, shrinkB=0))
    return axes


def _serif_width(fig):
    """Width of a word in figure fraction, Times, cached."""
    r, cache = fig.canvas.get_renderer(), {}

    def w(text, s, style="normal"):
        if (text, s, style) not in cache:
            t = fig.text(0, 0, text, fontsize=s, family=PAPER_SERIF, style=style)
            cache[(text, s, style)] = t.get_window_extent(r).width / fig.bbox.width
            t.remove()
        return cache[(text, s, style)]
    return w


def paper_title(fig, y, title, size=10.5):
    """'Figure n. Title' in small capitals (capitals full size, lower-case letters as capitals at 78%), centred at the
    top of the figure; y is the baseline. Words are set one by one with the width of 'x x' minus 'xx' as the space."""
    w = _serif_width(fig)
    space = w("x x", size) - w("xx", size)
    words = []
    for word in title.split():
        runs = []
        for ch in word:
            s = size * 0.78 if ch.islower() else size
            if runs and runs[-1][1] == s:
                runs[-1][0] += ch.upper()
            else:
                runs.append([ch.upper(), s])
        words.append(runs)
    total = sum(w(t, s) for runs in words for t, s in runs) + space * (len(words) - 1)
    x = 0.5 - total / 2
    for runs in words:
        for t, s in runs:
            fig.text(x, y, t, fontsize=s, family=PAPER_SERIF, va="baseline", color=INK); x += w(t, s)
        x += space


def paper_notes(fig, y, notes, x0=0.07, x1=0.93, size=9.5):
    """'Notes:' in italics and the notes in Times, justified between x0 and x1; y is the first baseline."""
    w = _serif_width(fig)
    pt = 1 / 72 / fig.get_figheight()
    words, space = notes.split(), w("x x", size) - w("xx", size)
    indent = w("Notes:", size, "italic") + space
    lines, cur, cur_w, avail = [], [], 0.0, x1 - x0 - indent
    for word in words:
        ww = w(word, size)
        if cur and cur_w + space + ww > avail:
            lines.append((cur, avail)); cur, cur_w, avail = [word], ww, x1 - x0
        else:
            cur_w += (space if cur else 0) + ww; cur.append(word)
    lines.append((cur, avail))
    yb = y
    fig.text(x0, yb, "Notes:", fontsize=size, family=PAPER_SERIF, style="italic", va="baseline", color=INK)
    for i, (ws, av) in enumerate(lines):
        x = x0 + (indent if i == 0 else 0)
        widths = [w(t, size) for t in ws]
        gap = (av - sum(widths)) / (len(ws) - 1) if i < len(lines) - 1 and len(ws) > 1 else space
        for t, ww in zip(ws, widths):
            fig.text(x, yb, t, fontsize=size, family=PAPER_SERIF, va="baseline", color=INK); x += ww + gap
        yb -= 1.3 * size * pt


def figure_longrun_overall():
    """Kelly et al. (2021, Figure 5) layout and framing. Panel A: one row per technology class, share of all US grants
    with at least one Reliance on Science v66 citation to a paper (front page or text), by decade, each row on its own
    scale. Panel B: role of the cited work among the sampled science-citing patents, all classes pooled, time running
    down. The sampling frame's loose text cue is not used for panel A: before 1980 it matches words such as 'journal'
    and would mix two definitions. Caption and notes below the panels, numbers in the notes computed here."""
    rows = science_rows(LONGRUN)
    pooled = collections.defaultdict(collections.Counter)
    for r in rows:
        pooled[r["decade"]][r["function"]] += 1
    years = [int(d[:4]) for d in LR_DECADES]
    counts = list(csv.DictReader(open(LONGRUN_COUNTS, encoding="utf-8")))   # written by pilot/longrun/labels_longrun.py
    uni = {(r["class"], int(r["decade"][:4])): int(r["n_grants"]) for r in counts}
    sci = {(r["class"], int(r["decade"][:4])): int(r["n_grants_citing_paper"]) for r in counts}
    share = {c: [100 * sci.get((c, y), 0) / uni[(c, y)] if uni.get((c, y)) else float("nan") for y in years] for c in LR_CLASSES}
    lo = min(LR_CLASSES, key=lambda c: share[c][-1]); hi = max(LR_CLASSES, key=lambda c: share[c][-1])
    n_dec = [sum(pooled[d].values()) for d in LR_DECADES]
    with plt.rc_context(PAPER_SANS):
        fig = plt.figure(figsize=(7.0, 8.4))
        paper_title(fig, 0.975, "Figure 1. Science in Invention over the Long Run")
        top, bottom = 0.895, 0.20
        # Panel A: one line per class
        lx0, lw = 0.31, 0.25
        fig.text(0.04, top + 0.02, "Panel A. Share of grants citing science", fontsize=9, color=INK)
        for k, (ax, cls) in enumerate(zip(kelly_rows(fig, lx0, lw, top, bottom, len(LR_CLASSES)), LR_CLASSES)):
            ys = share[cls]; m = max(v for v in ys if v == v)
            ax.plot(years, ys, color=KELLY_NAVY, linewidth=1.4, solid_capstyle="round")
            ax.set_xlim(years[0] - 2, years[-1] + 2); ax.set_ylim(-0.04 * m, m * 1.18)
            ax.set_yticks([0]); ax.set_yticklabels([cls], fontsize=8.5, color=INK)
            ax.set_xticks([1900, 1940, 1980, 2020] if k == len(LR_CLASSES) - 1 else [])
        # Panel B: stacked shares, time running down, black outlines and frame
        rx0, rw = 0.665, 0.30
        fig.text(rx0 - 0.065, top + 0.02, "Panel B. Role of the cited work", fontsize=9, color=INK)
        ax = fig.add_axes([rx0, bottom, rw, top - bottom])
        ys = list(range(len(LR_DECADES)))
        sh = [function_shares(pooled[d]) for d in LR_DECADES]
        ax.set_ylim(len(ys) - 1, 0); ax.set_xlim(0, 1)
        renderer = fig.canvas.get_renderer()
        left = [0.0] * len(ys)
        for key, name, color in LR_CATS:
            w = [x.get(key, 0) for x in sh]
            right = [a + b for a, b in zip(left, w)]
            ax.fill_betweenx(ys, left, right, color=color, edgecolor=INK, linewidth=0.5)
            i = max(range(1, len(ys) - 1), key=lambda j: w[j])   # label where the band is widest, as in Kelly et al.
            t = ax.text((left[i] + right[i]) / 2, i, LR_BAND_LABEL.get(key, name), ha="center", va="center", fontsize=8,
                        color="white" if key == "foundation" else INK, linespacing=1.15)
            if key == "foundation" and t.get_window_extent(renderer).transformed(ax.transData.inverted()).width > w[i]:
                i = max(range(2, len(ys) - 2), key=lambda j: w[j])   # white text must stay inside its band: run it along
                t.set_position(((left[i] + right[i]) / 2, i)); t.set_text(name); t.set_rotation(90)
            left = right
        ax.set_yticks(ys[::2]); ax.set_yticklabels([d[:4] for d in LR_DECADES[::2]], fontsize=8, color=INK)
        ax.set_xticks([])
        ax.tick_params(axis="y", length=3, width=0.8, color=INK, pad=3)
        for side in ax.spines.values():
            side.set_color(INK); side.set_linewidth(0.8)
        paper_notes(fig, bottom - 0.065,
            "Panel A shows the share of US grants citing a scientific paper in Reliance on Science, by class and decade, "
            f"each row on its own scale (2020s: {share[lo][-1]:.0f} to {share[hi][-1]:.0f} percent; a lower bound before the "
            "1940s). Panel B shows the role of the cited work in the sampled science-citing patents, all classes pooled "
            f"({n_dec[0]} patents in the 1900s, {n_dec[-1]} in the 2020s). Roles are coded by claude-opus-5-5.")
        fig.savefig(OUT / "longrun_overall.png", dpi=200, bbox_inches="tight", pad_inches=0.15); plt.close(fig)


def figure_longrun_classes(min_n=20, min_show=10):
    """Kelly et al. (2021, Figure 5, left panel) style small multiples with journal framing: one row per technology
    class, one column per role of the cited work, each line the share of the class's science-citing patents by decade.
    Every column has one scale (in the notes). The line is dotted where a class-decade holds min_show to min_n - 1
    science-citing patents and absent below min_show; the grey line behind is all classes pooled."""
    rows = science_rows(LONGRUN)
    by = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    pooled = collections.defaultdict(collections.Counter)
    for r in rows:
        by[r["sector"]][r["decade"]][r["function"]] += 1; pooled[r["decade"]][r["function"]] += 1
    years = [int(d[:4]) for d in LR_DECADES]
    scales = {}
    with plt.rc_context(PAPER_SANS):
        fig = plt.figure(figsize=(7.0, 9.2))
        paper_title(fig, 0.978, "Figure 2. How Science Is Used, by Technology Class")
        top, bottom = 0.895, 0.16
        x0, gap = 0.265, 0.024
        cw = (0.985 - x0 - gap * (len(MAIN) - 1)) / len(MAIN)
        for j, f in enumerate(MAIN):
            ok = [by[c][d][f] / sum(by[c][d].values()) for c in LR_CLASSES for d in LR_DECADES if sum(by[c][d].values()) >= min_n]
            ymax = scales[f] = max(0.2, -(-max(ok) * 10 // 1) / 10)
            cx = x0 + j * (cw + gap)
            fig.text(cx, top + 0.022, LR_BAND_LABEL.get(f, DISPLAY[f]), fontsize=8.5, color=INK, va="bottom", linespacing=1.1)
            ref = [pooled[d][f] / sum(pooled[d].values()) for d in LR_DECADES]
            for k, (ax, cls) in enumerate(zip(kelly_rows(fig, cx, cw, top, bottom, len(LR_CLASSES)), LR_CLASSES)):
                n = [sum(by[cls][d].values()) for d in LR_DECADES]
                v = [by[cls][d][f] / m if m >= min_show else float("nan") for d, m in zip(LR_DECADES, n)]
                solid = [x if m >= min_n else float("nan") for x, m in zip(v, n)]
                ax.plot(years, ref, color="#c4c1ba", linewidth=0.9)
                ax.plot(years, v, color=GRID_COLOR[f], linewidth=0.9, linestyle=(0, (1, 1.6)), alpha=0.85)
                ax.plot(years, solid, color=GRID_COLOR[f], linewidth=1.4, solid_capstyle="round")
                ax.set_xlim(years[0] - 3, years[-1] + 3); ax.set_ylim(-0.04 * ymax, ymax)
                ax.set_yticks([0]); ax.set_yticklabels([cls] if j == 0 else [""], fontsize=8.3, color=INK)
                ax.set_xticks([1910, 1960, 2010] if k == len(LR_CLASSES) - 1 else [])
        sc = ", ".join(f"{scales[f] * 100:.0f}" for f in MAIN[:-1]) + f" and {scales[MAIN[-1]] * 100:.0f}"
        paper_notes(fig, bottom - 0.06,
            "Share of each class's sampled science-citing patents in which the cited work plays the role above the column, "
            f"by decade; grey line: all classes pooled. Columns run from zero to {sc} percent. Dotted lines: {min_show} to "
            f"{min_n - 1} patents; none below {min_show}. Roles are coded by claude-opus-5-5.")
        fig.savefig(OUT / "longrun_by_class.png", dpi=200, bbox_inches="tight", pad_inches=0.15); plt.close(fig)


if __name__ == "__main__":
    figure_overall(); figure_sector(); figure_decade(); figure_firm(); figure_cited()
    if LONGRUN.exists():
        figure_longrun_classes(); figure_longrun_overall()
    print("wrote", ", ".join(p.name for p in sorted(OUT.glob("*.png"))), "to", OUT)
