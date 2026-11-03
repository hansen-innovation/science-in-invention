#!/usr/bin/env bash
# Label a sample's windows with one or more models on an OpenAI-compatible endpoint (vLLM, Together, ...), then report
# agreement with the sample's label file.
#   bash 3_validate/run_benchmark.sh <base_url> <sample> <model> [<model> ...]      sample: pilot | decades | longrun
# Needs OPENAI_API_KEY for hosted endpoints (any value for a local vLLM server). Extra llm.py options (for example
# "--workers 32") go in $LLM_ARGS. Labels go to data/3_validate/labels_<model>_<sample>.jsonl; the agreement report
# is appended to data/3_validate/results.md.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-python}
DATA=${SCIENCE_DATA:-$([ -d data ] && echo data || echo ../data)}
BASE_URL="$1"; SAMPLE="$2"; shift 2
RAW="$DATA/0_raw/$SAMPLE/citation_windows_raw.jsonl"; GOLD="$DATA/2_label/$SAMPLE/citation_windows_labeled.jsonl"; OUT="$DATA/3_validate/results.md"
for M in "$@"; do
  SAFE=$(echo "$M" | tr '/:' '__')
  LAB="$DATA/3_validate/labels_${SAFE}_${SAMPLE}.jsonl"
  "$PY" 2_label/llm.py --provider openai --base-url "$BASE_URL" --model "$M" --prompt 2_label/prompts/label_citation_function.md \
    --schema 2_label/schema.json --input "$RAW" --output "$LAB" --text-field text ${LLM_ARGS:-}
  {
    echo; echo "## $SAMPLE: $M"; echo; echo "Second coder \`$M\` on an OpenAI-compatible endpoint, reference labels \`$GOLD\`."; echo; echo '```'
    "$PY" 3_validate/validate.py agreement --a "$GOLD" --b "$LAB" --id window_id --field function
    echo; echo "cited_doc_type:"
    "$PY" 3_validate/validate.py agreement --a "$GOLD" --b "$LAB" --id window_id --field cited_doc_type
    echo '```'
  } >> "$OUT"
done
echo "appended to $OUT"
