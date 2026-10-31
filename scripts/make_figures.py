"""Figures for the README from the aggregated profiles (no model call; runs in a second).

    python scripts/make_figures.py        # writes figures/function_by_sector.png and figures/function_by_decade.png

Figure 1: share of in-text science citations by function for each sector in the 291-window pilot.
Figure 2: the same shares by decade for nine firms in three sectors (pilot/decades/).
Both read the profiles_*.csv files written by aggregate.py, so they regenerate with the pilots.
"""
import csv, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "figures"; OUT.mkdir(exist_ok=True)

# fixed category order and colors (categorical palette validated for adjacent stacked segments)
CATS = [("share_foundation", "Foundation", "#2a78d6"),
        ("share_method_or_tool", "Method or tool", "#eb6834"),
        ("share_prior_art_distinguished", "Prior art distinguished", "#1baf7a"),
        ("share_background_context", "Background", "#eda100"),
        ("share_definitional_boilerplate", "Boilerplate", "#e87ba4"),
        ("other", "Other", "#c3c2b7")]
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Segoe UI", "Helvetica", "Arial", "DejaVu Sans"],
                     "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.facecolor": "white"})


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k, v in list(r.items()):
            if k.startswith("share_") or k.startswith("n_"):
                r[k] = float(v)
        r["other"] = max(0.0, 1.0 - sum(r[k] for k, _, _ in CATS if k != "other"))
    return rows


def stack(ax, xs, rows, horizontal, width=0.6, min_label=0.12):
    """Stacked bars with a 2px white gap between segments and labels on segments wide enough to hold them."""
    base = [0.0] * len(rows)
    for key, name, color in CATS:
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


def figure_sector():
    rows = read(ROOT / "pilot" / "profiles_sector.csv")
    rows.sort(key=lambda r: r["share_foundation"])          # pharma (most foundation) ends up on top
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    xs = list(range(len(rows)))
    stack(ax, xs, rows, horizontal=True)
    ax.set_yticks(xs); ax.set_yticklabels([r["sector"] for r in rows], color=INK)
    ax.set_xlim(0, 1.0); ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0", "25", "50", "75", "100%"])
    ax.xaxis.grid(True, color=GRID, linewidth=0.6); ax.set_axisbelow(True); ax.tick_params(length=0)
    for x, r in zip(xs, rows):
        ax.text(1.01, x, f"n = {int(r['n_windows'])}", va="center", ha="left", color=INK2, fontsize=8)
    fig.text(0.02, 0.965, "What the cited science does in the patent, by sector", color=INK, fontsize=11, va="top")
    fig.text(0.02, 0.905, "Share of in-text citations to papers, books and standards documents. 291-window pilot, priority 2017 or later, family duplicates removed.",
             color=INK2, fontsize=8, va="top")
    ax.legend(loc="upper left", bbox_to_anchor=(0, 1.09), ncol=6, frameon=False, fontsize=8, handlelength=1.0, columnspacing=1.0)
    fig.tight_layout(rect=(0, 0, 0.97, 0.86))
    fig.savefig(OUT / "function_by_sector.png", dpi=200); plt.close(fig)


def figure_decade():
    rows = read(ROOT / "pilot" / "decades" / "profiles_sector_decade.csv")
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
        ax.set_ylim(0, 1.0); ax.set_yticks([0, .25, .5, .75, 1]); ax.set_yticklabels(["0", "25", "50", "75", "100%"])
        ax.yaxis.grid(True, color=GRID, linewidth=0.6); ax.set_axisbelow(True); ax.tick_params(length=0)
        ax.set_title(s, loc="left", color=INK, fontsize=10)
    fig.text(0.02, 0.975, "The same shares by decade: nine firms, two patents per firm per decade", color=INK, fontsize=11, va="top")
    fig.text(0.02, 0.915, "Pfizer, Eli Lilly, Bristol-Myers  |  Dow Chemical, Du Pont, Air Products  |  IBM, General Electric, Texas Instruments.\n"
             "Patents with priority and grant in the decade; n = science-citing windows, family duplicates removed.", color=INK2, fontsize=8, va="top", linespacing=1.4)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=6, frameon=False, fontsize=8, handlelength=1.0, columnspacing=1.0, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, 0.07, 1, 0.84))
    fig.savefig(OUT / "function_by_decade.png", dpi=200); plt.close(fig)


if __name__ == "__main__":
    figure_sector(); figure_decade()
    print("wrote", OUT / "function_by_sector.png", "and", OUT / "function_by_decade.png")
