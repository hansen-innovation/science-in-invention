# Worked example: four patents through the whole pipeline

`examples/demo/` is a complete run of `run_pipeline.py` on four granted US patents chosen to span sectors and
assignee types, so a reader can see what each stage produces without running anything:

| Patent | Assignee | Field | Description paragraphs | Citation windows |
| --- | --- | --- | --- | --- |
| US11466287B2 | Purdue Research Foundation (with Corteva) | soybean disease resistance (plant genetics) | 243 | 20 |
| US11524023B2 | ModernaTX | lipid nanoparticle formulation (mRNA) | 727 | 8 |
| US12620170B2 | NVIDIA | camera-based 3D scene completion (computer vision) | 270 | 5 |
| US12109412B2 | Boston Scientific Scimed | electrical + chemotherapeutic cancer treatment (devices) | 244 | 1 |

Files, in pipeline order:

1. `paragraphs.jsonl` — fetch stage: metadata and description paragraphs from Google Patents (fetched 2026-10-31).
2. `windows.jsonl` — one row per citation cue with the surrounding text, paragraph index and family-duplicate flag.
3. `labels_interactive.jsonl` — the label stage's output for these 34 windows: document type, function, confidence, verbatim citation string, one-line rationale. These were produced with the prompt in `prompts/label_citation_function.md` by claude-fable-5-1 in an interactive session (the same model and prompt the pilot used); `run_pipeline.py --provider openai --model ...` produces the same file automatically from any model.
4. `labeled.jsonl` — windows joined with labels (what the released citation-level table looks like).
5. `profiles_assignee.csv`, `profiles_year.csv` — the aggregation stage: shares by function with counts.
6. `report.md` — every window with its label and rationale, readable top to bottom.

What the four patents show:

- The cue finder is high-recall by design: it catches patent citations (`US12109412B2:111`, a commonly owned patent cited for sensor components) and lab manuals, which the document-type label then separates from papers.
- The function label does real work inside one patent. The Purdue/Corteva patent cites science in five different ways within 243 paragraphs: a disease-burden statistic as background, the earlier fine-mapping result as foundation, SSR markers and SNP data as materials, inoculation and transformation protocols as methods, and IUPAC/BLAST/codon-usage paragraphs as boilerplate that recurs across plant patents.
- Sector signatures appear even at n=4: NVIDIA cites papers as methods adopted and one as prior art distinguished (MonoScene, whose projection the invention improves on); Moderna's citations are formulation methods and lipid sources, with one mechanism (CD47 "self" peptides) as foundation.

To reproduce from scratch (network + a model endpoint needed):

```
python run_pipeline.py --patents US11466287B2 US11524023B2 US12620170B2 US12109412B2 --out examples/demo_rerun \
    --provider openai --base-url https://api.together.xyz/v1 --model Qwen/Qwen3.6-32B-Instruct
python common/validate.py agreement --a examples/demo/labeled.jsonl --b examples/demo_rerun/labeled.jsonl --id window_id --field function
```

To re-run only the offline stages on the saved paragraphs: `python run_pipeline.py --paragraphs examples/demo/paragraphs.jsonl --out examples/demo --labels examples/demo/labels_interactive.jsonl`.
