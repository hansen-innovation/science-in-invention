#!/usr/bin/env bash
# Regenerate the pilots' labeled files, summaries, profiles and README figures, then validate against the schema.
set -euo pipefail
cd "$(dirname "$0")/.."
# python3 on Windows may be the Store stub; fall back to python
PY=python3; "$PY" -c "" 2>/dev/null || PY=python
(cd pilot && "$PY" labels_pilot.py)
for by in assignee sector year; do "$PY" aggregate.py pilot/citation_windows_labeled.jsonl --by $by > /dev/null; done
# decade sample (nine firms, three sectors, 1980s-2010s)
(cd pilot/decades && "$PY" labels_decades.py > /dev/null)
for by in sector_decade sector decade; do "$PY" aggregate.py pilot/decades/citation_windows_labeled.jsonl --by $by > /dev/null; done
# long-run sample (Kelly et al. technology classes x decades, 1900s-2020s), once its labels exist
if [ -f pilot/longrun/labels_longrun.jsonl ]; then
  (cd pilot/longrun && "$PY" labels_longrun.py > /dev/null)
  for by in sector_decade sector decade; do "$PY" aggregate.py pilot/longrun/citation_windows_labeled.jsonl --by $by > /dev/null; done
fi
# firm and field samples (eleven firms; 14 technology fields of different ages), once their labels exist
for folder in firms fields; do
  if ls pilot/$folder/labels_$folder.jsonl* > /dev/null 2>&1; then
    (cd pilot/$folder && "$PY" labels_$folder.py > /dev/null)
    for by in sector_decade sector decade; do "$PY" aggregate.py $(ls pilot/$folder/citation_windows_labeled.jsonl*) --by $by > /dev/null; done
  fi
done
# README figures from the profiles
"$PY" scripts/make_figures.py
# worked example (offline stages on saved paragraphs + saved labels)
"$PY" run_pipeline.py --paragraphs examples/demo/paragraphs.jsonl --out examples/demo --labels examples/demo/labels_interactive.jsonl > /dev/null
"$PY" common/validate.py schema_check --schema schema.json --input examples/demo/labeled.jsonl
"$PY" common/validate.py schema_check --schema schema.json --input pilot/citation_windows_labeled.jsonl
"$PY" common/validate.py schema_check --schema schema.json --input pilot/decades/citation_windows_labeled.jsonl
[ -f pilot/longrun/citation_windows_labeled.jsonl ] && "$PY" common/validate.py schema_check --schema schema.json --input pilot/longrun/citation_windows_labeled.jsonl || true
for folder in firms fields; do
  for f in pilot/$folder/citation_windows_labeled.jsonl*; do [ -f "$f" ] && "$PY" common/validate.py schema_check --schema schema.json --input "$f"; done
done
