"""Figures for the README (no model call; runs in seconds).

    python 5_figures/make_figures.py

Everything is read from the labeled files, the profiles_*.csv written by aggregate.py and the long-run count files, so
the figures regenerate with the pilots (rebuild.sh). All figures share the journal framing of Kelly,
Papanikolaou, Seru and Taddy (2021, Figure 5): 'Figure n. Title' centred on top in Times small capitals, panels in
Arial with black axes and outlines, short notes below whose numbers are computed here. Numbering follows the README.
  longrun_overall.png     Figure 1: share of grants citing science by class (rows) and role of the cited work by decade
  longrun_by_class.png    Figure 2: role of the cited work by class and decade, long-run sample
  function_by_sector.png  Figure 7: role of the cited work by sector, pilot (role_dots)
  function_by_firm.png    Figure 8: role of the cited work by firm, decade sample pooled over decades (role_dots)
  what_is_cited.png       Figure A2: cited-document type, paper vs patent (linked from the README, not embedded)
  function_by_decade.png  Figure A1: shares by sector and decade, nine-firm decade sample (superseded by Figure 2)
  firms_by_role.png       Figure 3: role of the cited work by firm and decade, eleven firms (data/2_label/firms/)
  firms_long_run.png      Figure 4: six firms over the long run, time running down
  fields_by_role.png      Figure 5: role of the cited work by technology field and decade, fields by takeoff year (data/2_label/fields/)
  fields_maturity.png     Figure 6: decade-adjusted role shares by years since the field's takeoff
"""
import collections, csv, json, pathlib, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.transforms import blended_transform_factory  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "4_aggregate"))
from common.paths import DATA, out  # noqa: E402
from aggregate import SCIENCE_TYPES, DISPLAY, FUNCS, key_of, load_sector_map  # noqa: E402
OUT = DATA / "5_figures"; OUT.mkdir(parents=True, exist_ok=True)
PILOT = DATA / "2_label" / "pilot" / "citation_windows_labeled.jsonl"
DECADES = DATA / "2_label" / "decades" / "citation_windows_labeled.jsonl"

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
    import gzip
    with (gzip.open(path, "rt", encoding="utf-8") if str(path).endswith(".gz") else open(path, encoding="utf-8")) as f:
        return [json.loads(l) for l in f]


def science_rows(path):
    return [r for r in jsonl(path) if not r.get("is_family_duplicate") and r["cited_doc_type"] in SCIENCE_TYPES]


def read_csv(path):
    """Keep profile order and metadata; plot exact counts to avoid rounding rounded CSV shares."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    by = path.stem.removeprefix("profiles_")
    counts = collections.defaultdict(collections.Counter)
    sector_map = load_sector_map()
    for row in science_rows(DATA / "2_label" / path.parent.name / "citation_windows_labeled.jsonl"):
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


def role_dots(fig, groups, counts, pooled, top, bottom, x0, gap, labels=None):
    """Cross-section in the layout of role_grid: one row per group, one column per role of the cited work (MAIN); a dot
    at the group's share on a line from zero, a grey tick at the pooled share; one scale for every column (0 to the
    largest share, rounded up to a tenth). Returns that scale."""
    cw = (0.985 - x0 - gap * (len(MAIN) - 1)) / len(MAIN)
    mx = max(counts[g][f] / sum(counts[g].values()) for g in groups for f in MAIN); mx = -(-mx * 10 // 1) / 10
    for j, f in enumerate(MAIN):
        cx = x0 + j * (cw + gap)
        ax = fig.add_axes([cx, bottom, cw, top - bottom])
        fig.text(cx, top + 0.012, LR_BAND_LABEL.get(f, DISPLAY[f]), fontsize=8.5, color=INK, va="bottom", linespacing=1.1)
        pv = pooled[f] / sum(pooled.values())
        for k, g in enumerate(groups):
            v = counts[g][f] / sum(counts[g].values()); y = len(groups) - 1 - k
            ax.plot([0, v], [y, y], color=GRID_COLOR[f], linewidth=1.2, solid_capstyle="round", zorder=2)
            ax.plot([v], [y], "o", color=GRID_COLOR[f], markersize=4.5, zorder=3)
            ax.plot([pv, pv], [y - 0.28, y + 0.28], color="#b8b5ae", linewidth=1.0, zorder=1)
        ax.set_xlim(0, mx); ax.set_ylim(-0.6, len(groups) - 0.4); ax.set_yticks(range(len(groups)))
        ax.set_yticklabels([(labels or {}).get(g, g) for g in reversed(groups)] if j == 0 else [""] * len(groups), fontsize=8.3, color=INK)
        ax.set_xticks([0, mx / 2, mx]); ax.set_xticklabels(["0", f"{mx * 50:.0f}", f"{mx * 100:.0f}"], fontsize=7.5, color=INK2)
        ax.tick_params(axis="y", length=0, pad=4); ax.tick_params(axis="x", length=3, width=0.7, color=INK, pad=2)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(INK); ax.spines[side].set_linewidth(0.8)
    return mx


@paper_rc
def figure_sector():
    """Figure 7: the pilot's science-citing windows by sector, one column per role (role_dots); grey tick: all sectors."""
    rows = science_rows(PILOT); sector_map = load_sector_map()
    counts = collections.defaultdict(collections.Counter); pooled = collections.Counter()
    for r in rows:
        sct = cap(r.get("sector") or sector_map.get(r["assignee"], "other")); counts[sct][r["function"]] += 1; pooled[r["function"]] += 1
    groups = sorted(counts, key=lambda g: -counts[g]["foundation"] / sum(counts[g].values()))
    H = 0.42 * len(groups) + 2.6
    fig = plt.figure(figsize=(7.0, H))
    paper_title(fig, 1 - 0.32 / H, "Figure 7. What the Cited Science Does, by Sector")
    top, bottom = 1 - 0.95 / H, 1.45 / H
    mx = role_dots(fig, groups, counts, pooled, top, bottom, 0.26, 0.022, labels={g: f"{g} ({sum(counts[g].values())})" for g in groups})
    paper_notes(fig, bottom - 0.55 / H,
        f"Share of each sector's science-citing pilot windows ({len(rows)} windows citing papers, books, standards documents or "
        "mixed sets, family duplicates removed; windows in parentheses) in which the cited work plays the role above the column. "
        f"Grey tick: all sectors pooled. Scale: 0 to {mx * 100:.0f} percent. Roles are coded by claude-fable-5-1.")
    fig.savefig(OUT / "function_by_sector.png", dpi=200, bbox_inches="tight", pad_inches=0.15); plt.close(fig)


@paper_rc
def figure_decade():
    rows = {r["key"]["sector_decade"]: r for r in read_csv(DATA / "4_aggregate" / "decades" / "profiles_sector_decade.csv")}
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
    """Figure 8: the decade sample's nine firms, all decades pooled, one column per role (role_dots); grey tick: all firms."""
    by = collections.defaultdict(collections.Counter); pooled = collections.Counter()
    canon = {"International Business Machines": "IBM"}
    for r in science_rows(DECADES):
        f = canon.get(r["query_assignee"], r["query_assignee"]); by[f][r["function"]] += 1; pooled[r["function"]] += 1
    order = ["Pfizer", "Eli Lilly", "Bristol-Myers", "Dow Chemical", "Du Pont", "Air Products", "IBM", "General Electric", "Texas Instruments"]
    groups = [f for f in order if sum(by[f].values()) >= 5]
    H = 0.42 * len(groups) + 2.6
    fig = plt.figure(figsize=(7.0, H))
    paper_title(fig, 1 - 0.32 / H, "Figure 8. The Same Shares by Firm, Decade Sample")
    top, bottom = 1 - 0.95 / H, 1.45 / H
    mx = role_dots(fig, groups, by, pooled, top, bottom, 0.26, 0.022, labels={g: f"{g} ({sum(by[g].values())})" for g in groups})
    paper_notes(fig, bottom - 0.55 / H,
        "Share of each firm's science-citing windows in the decade sample, all decades pooled (windows in parentheses, family "
        "duplicates removed), in which the cited work plays the role above the column; pharma, chemicals and electronics "
        f"firms from top to bottom. Grey tick: all nine firms pooled. Scale: 0 to {mx * 100:.0f} percent. Roles are coded by claude-fable-5-1.")
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
    fig, ax, notes_y = canvas(groups, "Figure A2. What the Citation Window Points To", legend=DOC_CATS, note_lines=2)
    draw_rows(ax, groups, DOC_CATS, min_label=1.1)
    paper_notes(fig, notes_y, "Share of citation windows by type of cited document, family duplicates removed; windows in "
                "parentheses. Only science (papers, books, standards documents and mixed sets) enters the role profiles.")
    fig.savefig(OUT / "what_is_cited.png", dpi=200, bbox_inches="tight", pad_inches=0.15); plt.close(fig)


LONGRUN = DATA / "2_label" / "longrun" / "citation_windows_labeled.jsonl"
LONGRUN_COUNTS = DATA / "4_aggregate" / "longrun" / "grants_citing_science.csv"
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
    counts = list(csv.DictReader(open(LONGRUN_COUNTS, encoding="utf-8")))   # written by 2_label/labels_longrun.py
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


def role_grid(fig, groups, by, ref, top, bottom, x0, gap, labels=None, marks=None, min_n=20, min_show=10, ref_by_group=None):
    """Kelly et al. (2021, Figure 5, left panel) style small multiples: one row per group, one column per role of the
    cited work (MAIN), each line the group's share by decade; dotted where a cell holds min_show to min_n - 1
    science-citing patents, absent below min_show; grey: the reference shares (ref, by decade, or ref_by_group[group]
    when given); a dashed vertical line at marks[group] (e.g. a field's takeoff year). Returns each column's scale."""
    years = [int(d[:4]) for d in LR_DECADES]
    cw = (0.985 - x0 - gap * (len(MAIN) - 1)) / len(MAIN)
    scales = {}
    for j, f in enumerate(MAIN):
        ok = [by[g][d][f] / sum(by[g][d].values()) for g in groups for d in LR_DECADES if sum(by[g][d].values()) >= min_n]
        ymax = scales[f] = max(0.2, -(-max(ok) * 10 // 1) / 10) if ok else 1.0
        cx = x0 + j * (cw + gap)
        fig.text(cx, top + 0.022, LR_BAND_LABEL.get(f, DISPLAY[f]), fontsize=8.5, color=INK, va="bottom", linespacing=1.1)
        for k, (ax, g) in enumerate(zip(kelly_rows(fig, cx, cw, top, bottom, len(groups)), groups)):
            rr = ref_by_group[g] if ref_by_group else ref
            refline = [rr[d][f] / sum(rr[d].values()) if sum(rr[d].values()) else float("nan") for d in LR_DECADES]
            n = [sum(by[g][d].values()) for d in LR_DECADES]
            v = [by[g][d][f] / m if m >= min_show else float("nan") for d, m in zip(LR_DECADES, n)]
            solid = [x if m >= min_n else float("nan") for x, m in zip(v, n)]
            ax.plot(years, refline, color="#c4c1ba", linewidth=0.9)
            if marks and g in marks:
                ax.axvline(marks[g], color=MUTED, linewidth=0.7, linestyle=(0, (2, 2)))
            ax.plot(years, v, color=GRID_COLOR[f], linewidth=0.9, linestyle=(0, (1, 1.6)), alpha=0.85)
            ax.plot(years, solid, color=GRID_COLOR[f], linewidth=1.4, solid_capstyle="round")
            for i, x in enumerate(v):  # a decade without a neighbour draws no line: show it as a dot
                if x == x and all(not (0 <= i + s < len(v)) or v[i + s] != v[i + s] for s in (-1, 1)):
                    ax.plot(years[i], x, "o", color=GRID_COLOR[f], markersize=2.2 if n[i] >= min_n else 1.6)
            ax.set_xlim(years[0] - 3, years[-1] + 3); ax.set_ylim(-0.04 * ymax, ymax)
            ax.set_yticks([0]); ax.set_yticklabels([(labels or {}).get(g, g)] if j == 0 else [""], fontsize=8.3, color=INK)
            ax.set_xticks([1910, 1960, 2010] if k == len(groups) - 1 else [])
    return scales


def cells_by(rows, key):
    by = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    pooled = collections.defaultdict(collections.Counter)
    for r in rows:
        by[r[key]][r["decade"]][r["function"]] += 1; pooled[r["decade"]][r["function"]] += 1
    return by, pooled


def scale_text(scales):
    return ", ".join(f"{scales[f] * 100:.0f}" for f in MAIN[:-1]) + f" and {scales[MAIN[-1]] * 100:.0f}"


def figure_longrun_classes(min_n=20, min_show=10):
    """Figure 2: one row per technology class, one column per role (role_grid); grey: all classes pooled."""
    by, pooled = cells_by(science_rows(LONGRUN), "sector")
    with plt.rc_context(PAPER_SANS):
        fig = plt.figure(figsize=(7.0, 9.2))
        paper_title(fig, 0.978, "Figure 2. How Science Is Used, by Technology Class")
        top, bottom = 0.895, 0.16
        scales = role_grid(fig, LR_CLASSES, by, pooled, top, bottom, 0.265, 0.024, min_n=min_n, min_show=min_show)
        paper_notes(fig, bottom - 0.06,
            "Share of each class's sampled science-citing patents in which the cited work plays the role above the column, "
            f"by decade; grey line: all classes pooled. Columns run from zero to {scale_text(scales)} percent. Dotted lines: {min_show} to "
            f"{min_n - 1} patents; none below {min_show}. Roles are coded by claude-opus-5-5.")
        fig.savefig(OUT / "longrun_by_class.png", dpi=200, bbox_inches="tight", pad_inches=0.15); plt.close(fig)


FIRMS_FILE = DATA / "2_label" / "firms" / "citation_windows_labeled.jsonl.gz"
FIELDS_FILE = DATA / "2_label" / "fields" / "citation_windows_labeled.jsonl"
FIELD_GRANTS = DATA / "1_fetch" / "fields" / "field_grants_by_year.csv"
FIRM_ORDER = ["AT&T", "DuPont", "General Electric", "Pfizer", "IBM", "Ford", "Boeing", "Microsoft", "Nvidia", "Google", "Walmart"]


def class_matched_reference(rows, lr_rows):
    """Per group and decade, the long-run sample's role shares reweighted to the group's technology-class mix in that
    decade (classes with no long-run cell in the decade are dropped from the mix); returns {group: {decade: Counter}}."""
    lr_by, _ = cells_by(lr_rows, "sector")
    mix = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for r in rows:
        mix[r["firm"]][r["decade"]][r["cls"]] += 1
    out = {}
    for g, decs in mix.items():
        out[g] = collections.defaultdict(collections.Counter)
        for d, classes in decs.items():
            usable = {c: w for c, w in classes.items() if sum(lr_by[c][d].values())}
            tot = sum(usable.values())
            for c, w in usable.items():
                n = sum(lr_by[c][d].values())
                for f, v in lr_by[c][d].items():
                    out[g][d][f] += w / tot * v / n
    return out


@paper_rc
def figure_firms_grid(min_n=20, min_show=10):
    """Figure 3: one row per firm (role_grid), every firm patent with an in-text science citation; grey: the long-run
    sample reweighted to the firm's technology-class mix in each decade (class_matched_reference)."""
    rows = science_rows(FIRMS_FILE)
    by, _ = cells_by(rows, "firm")
    lr = science_rows(LONGRUN)
    _, ref = cells_by(lr, "sector")
    ref_g = class_matched_reference(rows, lr)
    firms = [f for f in FIRM_ORDER if any(sum(by[f][d].values()) >= min_n for d in LR_DECADES)]
    n = {f: sum(sum(by[f][d].values()) for d in LR_DECADES) for f in firms}
    H = 0.66 * len(firms) + 2.7
    fig = plt.figure(figsize=(7.0, H))
    paper_title(fig, 1 - 0.32 / H, "Figure 3. How Firms Use the Science They Cite")
    top, bottom = 1 - 1.0 / H, 1.75 / H
    scales = role_grid(fig, firms, by, ref, top, bottom, 0.2, 0.024, min_n=min_n, min_show=min_show, ref_by_group=ref_g)
    lo, hi = min(n, key=n.get), max(n, key=n.get)
    paper_notes(fig, bottom - 0.62 / H,
        "Share of each firm's science-citing patents in which the cited work plays the role above the column, by decade: "
        "every patent of the firm with an in-text citation to science, one window per patent, repeated texts counted once "
        f"({sum(n.values()):,} patents, from {n[lo]:,} for {lo} to {n[hi]:,} for {hi}). Grey line: the long-run sample reweighted "
        f"to the firm's technology-class mix in each decade. Columns run from zero to {scale_text(scales)} percent. Dotted lines or dots: {min_show} to {min_n - 1} "
        f"patents; none below {min_show}. Roles are coded by claude-opus-5-5.")
    fig.savefig(OUT / "firms_by_role.png", dpi=200, bbox_inches="tight", pad_inches=0.15); plt.close(fig)


def stacked_down(ax, shares_by_row):
    """Kelly et al. (2021, Figure 5, right panel) stacked shares with time running down; rows without data (None) leave
    a gap; black outlines."""
    runs, cur = [], []
    for i, s in enumerate(shares_by_row):
        if s is None:
            if cur: runs.append(cur); cur = []
        else:
            cur.append((i, s))
    if cur: runs.append(cur)
    for run in runs:
        ys = [i for i, _ in run]
        if len(ys) == 1:
            ys = [ys[0] - 0.35, ys[0] + 0.35]; run = run * 2
        left = [0.0] * len(ys)
        for key, _, color in LR_CATS:
            w = [s.get(key, 0) for _, s in run]
            right = [a + b for a, b in zip(left, w)]
            ax.fill_betweenx(ys, left, right, color=color, edgecolor=INK, linewidth=0.5)
            left = right


@paper_rc
def figure_firms_stacked(firms=("AT&T", "General Electric", "DuPont", "IBM", "Pfizer", "Google"), min_n=20):
    """Figure 4: six firms with long records, role of the cited work by decade, time running down (Kelly et al. right
    panel); decades with fewer than min_n science-citing patents are left blank."""
    by, _ = cells_by(science_rows(FIRMS_FILE), "firm")
    decs = LR_DECADES[2:]
    H = 6.6
    fig = plt.figure(figsize=(7.0, H))
    paper_title(fig, 1 - 0.32 / H, "Figure 4. Six Firms, 1920s to 2020s")
    fig.legend([Patch(facecolor=c, edgecolor=INK, linewidth=0.5) for _, _, c in LR_CATS], [n for _, n, _ in LR_CATS],
               loc="upper center", bbox_to_anchor=(0.5, 1 - 0.48 / H), ncol=3, frameon=False, fontsize=8, labelcolor=INK,
               handlelength=1.0, handleheight=1.0, columnspacing=1.6, handletextpad=0.5, borderaxespad=0)
    top, bottom = 1 - 1.12 / H, 1.35 / H
    x0, gap = 0.1, 0.016
    pw = (0.985 - x0 - gap * (len(firms) - 1)) / len(firms)
    for j, firm in enumerate(firms):
        ax = fig.add_axes([x0 + j * (pw + gap), bottom, pw, top - bottom])
        sh = [function_shares(by[firm][d]) if sum(by[firm][d].values()) >= min_n else None for d in decs]
        stacked_down(ax, sh)
        ax.set_ylim(len(decs) - 1, 0); ax.set_xlim(0, 1)
        ax.set_yticks(range(0, len(decs), 2)); ax.set_yticklabels([d[:4] for d in decs[::2]] if j == 0 else [], fontsize=8, color=INK)
        ax.set_xticks([])
        ax.tick_params(axis="y", length=3, width=0.8, color=INK, pad=3)
        for side in ax.spines.values():
            side.set_color(INK); side.set_linewidth(0.8)
        ax.set_title(firm, fontsize=8.5, color=INK, pad=4)
    n = {f: sum(sum(by[f][d].values()) for d in decs if sum(by[f][d].values()) >= min_n) for f in firms}
    paper_notes(fig, bottom - 0.42 / H,
        "Role of the cited work in each firm's science-citing patents, by decade (time runs down, shares at decade marks; every "
        "patent with an in-text citation to science, one window per patent, repeated texts counted once; decades with fewer "
        "than 20 such patents are blank, Google's record starts in the 2000s). Patents: "
        + ", ".join(f"{f} {n[f]:,}" for f in firms) + ". Other combines source of materials or data, reference list entry and "
        "own earlier patent. Roles are coded by claude-opus-5-5.")
    fig.savefig(OUT / "firms_long_run.png", dpi=200, bbox_inches="tight", pad_inches=0.15); plt.close(fig)


def field_takeoff(threshold=1000):
    """Year in which a field's cumulative US grants (first CPC code) reach `threshold` (data/1_fetch/fields/field_grants_by_year.csv)."""
    years = collections.defaultdict(dict)
    for r in csv.DictReader(open(FIELD_GRANTS, encoding="utf-8")):
        years[r["field"]][int(r["year"])] = int(r["n"])
    out = {}
    for f, ys in years.items():
        cum = 0
        for y in sorted(ys):
            cum += ys[y]
            if cum >= threshold:
                out[f] = y; break
    return out


@paper_rc
def figure_fields_grid(min_n=20, min_show=10):
    """Figure 5: one row per technology field, oldest takeoff first (role_grid); the dashed line marks the year of the
    field's 1,000th US grant; grey: all fields pooled."""
    by, pooled = cells_by(science_rows(FIELDS_FILE), "field")
    take = field_takeoff()
    fields = sorted([f for f in by if f in take and any(sum(by[f][d].values()) >= min_n for d in LR_DECADES)], key=lambda f: (take[f], f))
    H = 0.62 * len(fields) + 2.6
    fig = plt.figure(figsize=(7.0, H))
    paper_title(fig, 1 - 0.32 / H, "Figure 5. Technology Fields of Different Ages")
    top, bottom = 1 - 1.0 / H, 1.6 / H
    scales = role_grid(fig, fields, by, pooled, top, bottom, 0.255, 0.024, labels={f: f"{f} ({take[f]})" for f in fields},
                       marks=take, min_n=min_n, min_show=min_show)
    paper_notes(fig, bottom - 0.6 / H,
        "Share of each field's sampled science-citing patents in which the cited work plays the role above the column, by "
        "decade (up to 60 patents per field and decade, repeated texts counted once). The year after each field and the dashed "
        "line mark its 1,000th US grant. Grey line: all fields pooled. Columns run from zero to "
        f"{scale_text(scales)} percent. Dotted lines or dots: {min_show} to {min_n - 1} patents; none below {min_show}. Roles are coded by claude-opus-5-5.")
    fig.savefig(OUT / "fields_by_role.png", dpi=200, bbox_inches="tight", pad_inches=0.15); plt.close(fig)


AGE_BINS = [("Before\ntakeoff", None, 0), ("0-19", 0, 20), ("20-39", 20, 40), ("40-59", 40, 60), ("60-99", 60, 100), ("100+", 100, None)]


def maturity_margins(rows, take):
    """Linear probability model per role: role indicator on field-age bins (decade midpoint minus the year of the field's
    1,000th grant) and decade fixed effects; returns, per role, the decade-adjusted share in each age bin (the bin
    coefficient plus the sample-average decade effect) with a 95% interval from standard errors clustered by field, the
    raw share and the number of patents per bin."""
    import numpy as np
    def age_bin(r):
        age = int(r["decade"][:4]) + 5 - take[r["field"]]
        for i, (_, lo, hi) in enumerate(AGE_BINS):
            if (lo is None or age >= lo) and (hi is None or age < hi):
                return i
    rows = [r for r in rows if r["field"] in take]
    bins = [age_bin(r) for r in rows]
    decs = sorted({r["decade"] for r in rows})
    X = np.zeros((len(rows), len(AGE_BINS) + len(decs) - 1))
    for i, (r, b) in enumerate(zip(rows, bins)):
        X[i, b] = 1
        k = decs.index(r["decade"])
        if k: X[i, len(AGE_BINS) + k - 1] = 1
    cl = [r["field"] for r in rows]; G = sorted(set(cl)); N, K = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    L = np.zeros((len(AGE_BINS), K))
    dshare = [sum(1 for r in rows if r["decade"] == d) / N for d in decs]
    for b in range(len(AGE_BINS)):
        L[b, b] = 1; L[b, len(AGE_BINS):] = dshare[1:]
    out = {}
    for f in MAIN:
        y = np.array([1.0 if r["function"] == f else 0.0 for r in rows])
        beta = XtX_inv @ X.T @ y; u = y - X @ beta
        meat = np.zeros((K, K))
        for g in G:
            idx = [i for i, c in enumerate(cl) if c == g]
            s = X[idx].T @ u[idx]; meat += np.outer(s, s)
        V = XtX_inv @ meat @ XtX_inv * len(G) / (len(G) - 1) * (N - 1) / (N - K)
        m = L @ beta; se = np.sqrt(np.einsum("ij,jk,ik->i", L, V, L))
        raw = [np.mean([y[i] for i in range(N) if bins[i] == b]) if bins.count(b) else float("nan") for b in range(len(AGE_BINS))]
        out[f] = [(m[b], m[b] - 1.96 * se[b], m[b] + 1.96 * se[b], raw[b], bins.count(b)) for b in range(len(AGE_BINS))]
    return out


@paper_rc
def figure_maturity():
    """Figure 6: decade-adjusted role shares by field age (maturity_margins), one row per role in the style of Kelly et
    al. (2021, Figure 5, left panel); writes the numbers to data/5_figures/maturity_margins.csv."""
    rows = science_rows(FIELDS_FILE)
    take = field_takeoff()
    by, _ = cells_by(rows, "field")
    rows = [r for r in rows if any(sum(by[r["field"]][d].values()) >= 20 for d in LR_DECADES)]  # the fields of Figure 5
    mm = maturity_margins(rows, take)
    with open(OUT / "maturity_margins.csv", "w", newline="", encoding="utf-8") as fcsv:
        w = csv.writer(fcsv); w.writerow(["role", "age_bin", "adjusted_share", "ci_low", "ci_high", "raw_share", "n_patents"])
        for f in MAIN:
            for (name, _, _), (m, lo, hi, raw, n) in zip(AGE_BINS, mm[f]):
                w.writerow([f, name.replace("\n", " "), f"{m:.4f}", f"{lo:.4f}", f"{hi:.4f}", f"{raw:.4f}", n])
    H = 6.2
    fig = plt.figure(figsize=(7.0, H))
    paper_title(fig, 1 - 0.32 / H, "Figure 6. Science Use by the Age of a Technology Field")
    top, bottom = 1 - 0.75 / H, 1.75 / H
    xs = list(range(len(AGE_BINS)))
    axes = kelly_rows(fig, 0.3, 0.5, top, bottom, len(MAIN))
    for k, (ax, f) in enumerate(zip(axes, MAIN)):
        m = [t[0] for t in mm[f]]; lo = [t[1] for t in mm[f]]; hi = [t[2] for t in mm[f]]; raw = [t[3] for t in mm[f]]
        ax.fill_between(xs, [max(0, v) for v in lo], hi, color=GRID_COLOR[f], alpha=0.18, linewidth=0)
        ax.plot(xs, raw, color=MUTED, linewidth=0.9, linestyle=(0, (1, 1.6)))
        ax.plot(xs, m, color=GRID_COLOR[f], linewidth=1.5, marker="o", markersize=3)
        top_v = max(max(hi), max(raw)) * 1.15
        ax.set_ylim(-0.02 * top_v, top_v); ax.set_xlim(-0.3, len(xs) - 0.7)
        ax.set_yticks([0]); ax.set_yticklabels([DISPLAY[f]], fontsize=8.5, color=INK)
        ax.text(len(xs) - 0.6, m[-1], f"{m[-1] * 100:.0f}%", fontsize=7, color=MUTED, va="center")
        ax.text(-0.2, m[0], f"{m[0] * 100:.0f}%", fontsize=7, color=MUTED, va="center", ha="right")
        if k == len(MAIN) - 1:
            ax.set_xticks(xs); ax.set_xticklabels([b[0] for b in AGE_BINS], fontsize=8, color=INK)
            ax.set_xlabel("Years since the field's 1,000th US grant", fontsize=8, color=INK, labelpad=4)
        else:
            ax.set_xticks([])
    n = [t[4] for t in mm[MAIN[0]]]
    paper_notes(fig, bottom - 0.82 / H,
        "Share of science-citing patents in which the cited work plays each role, by the age of the patent's technology field "
        "in its decade (decade midpoint minus the year of the field's 1,000th US grant), for the fields of Figure 5. Solid "
        "line: shares adjusted for decade fixed effects, so that fields of different ages are compared within the same decade, "
        "with 95% intervals clustered by field; dotted line: raw shares; each row on its own scale. The youngest bin holds mostly "
        "lasers, genetic engineering, AI, lithium batteries and quantum computing, the oldest only fields that took off before 1912. Patents per age bin: "
        + ", ".join(f"{n[i]:,}" for i in range(len(n))) + ". Roles are coded by claude-opus-5-5.")
    fig.savefig(OUT / "fields_maturity.png", dpi=200, bbox_inches="tight", pad_inches=0.15); plt.close(fig)


if __name__ == "__main__":
    figure_sector(); figure_decade(); figure_firm(); figure_cited()
    if LONGRUN.exists():
        figure_longrun_classes(); figure_longrun_overall()
    if FIRMS_FILE.exists() and LONGRUN.exists():
        figure_firms_grid(); figure_firms_stacked()
    if FIELDS_FILE.exists() and FIELD_GRANTS.exists():
        figure_fields_grid(); figure_maturity()
    print("wrote", ", ".join(p.name for p in sorted(OUT.glob("*.png"))), "to", OUT)
