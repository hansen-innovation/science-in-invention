#!/usr/bin/env bash
# Regenerate every derived file from the raw windows and the label sources, then run the schema checks.
# Data root: data/ beside this script (public repository) or ../data (working copy), or $SCIENCE_DATA.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python}
DATA=${SCIENCE_DATA:-$([ -d data ] && echo data || echo ../data)}
export SCIENCE_DATA="$DATA"
agg() { for by in "${@:2}"; do "$PY" 4_aggregate/aggregate.py "$DATA"/2_label/$1/citation_windows_labeled.jsonl* --by "$by" --out-dir "$DATA/4_aggregate/$1" > /dev/null; done; }
# pilot (eight sectors, priority 2017+) and decade sample (nine firms, three sectors, 1980s-2010s): hand labels in 2_label/labels_*.py
"$PY" 2_label/labels_pilot.py; agg pilot assignee sector year
"$PY" 2_label/labels_decades.py > /dev/null; agg decades sector_decade sector decade
# long-run, firm and field samples: model labels in data/2_label/<sample>/labels_<sample>.jsonl(.gz)
for s in longrun firms fields; do
  if ls "$DATA"/2_label/$s/labels_$s.jsonl* > /dev/null 2>&1; then "$PY" "2_label/labels_$s.py" > /dev/null; agg $s sector_decade sector decade; fi
done
# figures (data/5_figures)
"$PY" 5_figures/make_figures.py
# worked example (offline stages on saved paragraphs + saved labels)
"$PY" run_pipeline.py --paragraphs "$DATA/examples/demo/paragraphs.jsonl" --out "$DATA/examples/demo" --labels "$DATA/examples/demo/labels_interactive.jsonl" > /dev/null
for f in "$DATA"/examples/demo/labeled.jsonl "$DATA"/2_label/*/citation_windows_labeled.jsonl*; do
  "$PY" 3_validate/validate.py schema_check --schema 2_label/schema.json --input "$f"
done
