#!/usr/bin/env bash
# Regenerate the pilot's labeled files and summary, then validate against the schema(s).
set -euo pipefail
cd "$(dirname "$0")/.."
(cd pilot && python3 labels_pilot.py)
python3 depth_measures.py pilot/citation_windows_labeled.jsonl > /dev/null
for by in assignee sector year; do python3 aggregate.py pilot/citation_windows_labeled.jsonl --by $by > /dev/null; done
# worked example (offline stages on saved paragraphs + saved labels)
python3 run_pipeline.py --paragraphs examples/demo/paragraphs.jsonl --out examples/demo --labels examples/demo/labels_interactive.jsonl > /dev/null
python3 common/validate.py schema_check --schema schema.json --input examples/demo/labeled.jsonl
python3 common/validate.py schema_check --schema schema.json --input pilot/citation_windows_labeled.jsonl
