# Model benchmark: open-weight vs. closed models on the pilot windows

Purpose: choose the production model on evidence, and make the choice reproducible. The production run
should use an open-weight model so that anyone can re-run the pipeline; a closed model is used to spot-check.

## Status

- Pilot labels in `../pilot/citation_windows_labeled.jsonl` were produced with one closed model
  (claude-fable-5-1) in a single pass with written rationales.
- The open-model comparison below is the first task of the benchmark phase. Results are recorded in
  `results.md` as they are run; until then the table there is empty by design.

## How to run

```
# 1. label the pilot windows with each candidate (OpenAI-compatible endpoints: vLLM, Together, DeepInfra, Fireworks)
bash benchmark/run_benchmark.sh https://api.together.xyz/v1 Qwen/Qwen3.6-32B-Instruct zai-org/GLM-4.6 deepseek-ai/DeepSeek-V3.2
# 2. agreement of each candidate with the pilot labels, and pairwise between candidates
#    (accuracy, Cohen's kappa, per-label precision/recall, list of disagreements) -> benchmark/results.md
```

The same prompt (`../prompts/label_citation_function.md`) and schema are used for every model, with
temperature 0; outputs are cached by (model, prompt, schema, text), so a re-run after a prompt change
re-labels only what changed.

## What counts as "good enough"

Agreement with the human double-coded benchmark (2,000 windows, to be built) is the criterion, not agreement
with another model. Between now and then, kappa against the pilot labels and the pattern of disagreements
(which functions get confused) is what the model comparison reports. The known hard boundaries from the pilot
are foundation vs. background and method vs. prior art distinguished; a model that collapses those is not
usable even if its overall agreement is high.
