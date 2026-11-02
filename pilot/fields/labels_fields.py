"""Field sample: how technology fields of different ages use the science they cite, 1900s-2020s.

Sample (Nov 2, 2026; scripts in local/firms_fields/ of the working copy). Fourteen fields defined by the first CPC code
of the patent (local/firms_fields/bq_firms_fields.FIELDS): electric lamps, aircraft, radio, petroleum refining,
polymers and plastics, television, pharmaceuticals, semiconductors, computing, lasers, genetic engineering, lithium
batteries, artificial intelligence and quantum computing. Per field and decade, eligible patents (an in-text Reliance on
Science v66 citation to a paper, or before 1980 a strict citation cue in the text) are taken in sha1 order of the
publication number; the window finder keeps one window per patent by the rules of the firm sample (labels_firms.py),
and the first 60 patents with a window form the cell (strict-rule windows before fallback windows). The year in which
each field's US grants pass fixed counts (field_year_counts.csv in data/1_fetch/firms_fields/) dates its takeoff.
Repeated window texts within a field are flagged is_family_duplicate as in the firm sample.
Labels: as in the firm sample (claude-opus-5-5, blind subagents, batches of 30; labels_fields.jsonl is the source of
truth; a partly labeled file is a balanced subsample and summary.md states the coverage).
Run `python labels_fields.py` to write citation_windows_labeled.jsonl and summary.md.
"""
import pathlib, sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "firms"))
from labels_firms import build  # noqa: E402

def write_field_grants():
    """field_grants_by_year.csv (field takeoff dates in Figures 9 and 10): US grants per field and grant year by first CPC
    code, all of Google Patents Public Data; rewritten from ../../../data/1_fetch/firms_fields/field_year_counts.csv when it
    exists (working copy), otherwise the committed file is kept."""
    src = HERE.parent.parent.parent / "data" / "1_fetch" / "firms_fields" / "field_year_counts.csv"
    if src.exists():
        (HERE / "field_grants_by_year.csv").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


if __name__ == "__main__":
    build(HERE, "labels_fields.jsonl", "field", "Field sample: how technology fields of different ages use the science they cite, 1900s-2020s")
    write_field_grants()
