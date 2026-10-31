#!/usr/bin/env bash
# Label the pilot windows with one or more models on an OpenAI-compatible endpoint, then report agreement.
#   bash benchmark/run_benchmark.sh <base_url> <model> [<model> ...]
# Needs OPENAI_API_KEY for hosted endpoints (any value for a local vLLM server).
set -euo pipefail
cd "$(dirname "$0")/.."
BASE_URL="$1"; shift
GOLD=pilot/citation_windows_labeled.jsonl
OUT=benchmark/results.md
{
  echo "# Benchmark results"; echo
  echo "Generated $(date -u +%Y-%m-%dT%H:%MZ). Reference labels: $GOLD (single closed-model pass; to be replaced by the double-coded benchmark)."; echo
} > "$OUT"
for M in "$@"; do
  SAFE=$(echo "$M" | tr '/:' '__')
  python3 common/llm.py --provider openai --base-url "$BASE_URL" --model "$M" \
    --prompt prompts/label_citation_function.md --schema schema.json \
    --input pilot/citation_windows_raw.jsonl --output "benchmark/labels_${SAFE}.jsonl" --text-field text
  {
    echo "## $M"; echo; echo '```'
    python3 common/validate.py agreement --a "$GOLD" --b "benchmark/labels_${SAFE}.jsonl" --id window_id --field function
    echo; echo "cited_doc_type:"
    python3 common/validate.py agreement --a "$GOLD" --b "benchmark/labels_${SAFE}.jsonl" --id window_id --field cited_doc_type
    echo '```'; echo
  } >> "$OUT"
done
echo "wrote $OUT"
