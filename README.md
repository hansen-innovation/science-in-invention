# Science in Invention

**How is science used in invention?**

When a patent cites a scientific paper in its description, what is the paper doing there: supplying the
mechanism the invention rests on, a method the inventors adopted, a prior approach they distinguish,
materials they sourced, or background? [Reliance on Science](https://zenodo.org/communities/relianceonscience)
(Marx and Fuegi) tells us *which* papers a patent cites. This project reads the text around each in-text
citation and labels *how* the paper is used, adds structural "depth" measures that need no language model,
links patents to firms, and aggregates to industry-year and firm-year **science-use profiles** so that the
purpose of citing science in invention can be compared across industries and types of inventors and
followed over time.

Pilot stage, October 2026 (109 patents, 68 assignees, 291 citation windows, all labeled). Built as the
working repository behind an NBER i3 Open Data Fellows 2027 proposal.

## What the dataset will contain

| Layer | Content | Keys |
| --- | --- | --- |
| Citation window | window text; cited-document type (paper, patent, standards doc, book, software, mixed); **function** (foundation, method or tool, prior art distinguished, data or materials source, background context, definitional boilerplate, incorporated reference list, own-family continuation); confidence; one-line rationale; family-duplicate flag | USPTO patent number + paragraph index; Reliance on Science citation record where it resolves; OpenAlex work id; verbatim citation string |
| Depth (no LLM) | how often the patent invokes the same work; standalone vs. flanked citation; position in the description | same |
| Profiles | shares by function and depth for assignee-year, firm-year (gvkey / permno) and industry-year, with window and patent counts | PatentsView assignee id → DISCERN, KPSS, the 1900–1980 Golden Age firm panel (`docs/firm_linkage.md`) |
| Benchmark | 2,000 windows double-coded with codebook and adjudication; precision/recall by sector, citation format and decade; model comparison (`benchmark/`) | window id |

## Worked example

`examples/demo/` runs four patents (Purdue/Corteva soybean genetics, Moderna lipid nanoparticles, NVIDIA 3D scene completion, Boston Scientific devices) through every stage, with all intermediate files and a readable `report.md` showing each of the 34 citation windows with its label and rationale. One command reproduces it: `python run_pipeline.py --patents US11466287B2 US11524023B2 US12620170B2 US12109412B2 --out examples/demo_rerun --provider openai --base-url <endpoint> --model <open-weight model>`. See `examples/README.md`.

## Pipeline

`run_pipeline.py` chains the stages below for a list of patents (fetch → window → depth → label → aggregate → report); each stage is also a standalone script.

1. `fetch_patents.py` — description paragraphs and citation windows (regex cue finder tuned for recall: author-year, "et al.", journal-volume-year, DOI, arXiv id, standards document numbers). In the full build the windows start from the in-text citations in Reliance on Science so every row inherits the patent–paper match and confidence score.
2. `depth_measures.py` — standalone / paired / string, position in the description, cue count; invocation count per cited work in the full build. Computed for every window; the first validation axis for the function label.
3. `common/llm.py --prompt prompts/label_citation_function.md --schema schema.json` — document type and function from a fixed prompt, JSON-constrained, cached by (model, prompt, schema, text). Works with the Anthropic API or any OpenAI-compatible endpoint (vLLM, Together, DeepInfra) so open-weight models can run the production pass.
4. Family de-duplication (identical windows across continuations and divisionals), then `aggregate.py --by assignee|sector|year` — shares by function with counts.
5. `common/validate.py agreement` — accuracy, Cohen's kappa, per-label precision/recall and disagreement lists between any two label files (model vs. human benchmark, model vs. model).

## Pilot results (October 26–30, 2026)

- 109 granted US patents (priority 2017+) from 68 corporate assignees in pharma, biotech tools, software/AI, semiconductors, chemicals/materials, medical devices, energy and automotive/aerospace; 291 windows, 273 after family and sibling de-duplication; every window labeled with the released prompt and a written rationale (`pilot/citation_windows_labeled.jsonl`, `pilot/summary.md`).
- Among the 163 paper citations: method or tool 29%, background context 25%, foundation 24%, prior art distinguished 18%, definitional boilerplate 3%, data or materials 1%.
- Sector signatures (`pilot/profiles_sector.csv`): pharma cites science as foundation (35%) and background (34%) and is the least substantive sector (50%); software/AI and chemicals cite methods (50% each); semiconductors cite prior art distinguished (38%); medical devices and automotive/aerospace are the most substantive (92%, 94%; small n).
- Depth measures (`pilot/depth_by_function.md`): whether a citation stands alone or sits in a string does not separate substantive from background use (67–69% substantive in every group), but standalone citations are disproportionately methods adopted (39% vs. 23%); position does separate them — 59% of citations in the first fifth of the description are substantive against 86% in the last 40%.
- Three design changes came out of the pilot: a document-type filter (85 of 273 de-duplicated windows cite patents, standards documents, books or software rather than papers), family de-duplication (Genentech, Google, Illumina, Bayer, Abbott and Monsanto continuations reuse identical text), and a boilerplate category (antibody-fragment definitions and BLAST citations recur across firms and would otherwise inflate "reliance on science" in biotech).

## Repository layout

```
README.md               this file
docs/firm_linkage.md        joins to PatentsView, DISCERN, KPSS and the Golden Age firm panel; pre-1976 coverage
schema.json             JSON schema for one labeled window (the prompt returns exactly these fields)
prompts/                the labeling prompt
run_pipeline.py         end-to-end: fetch -> window -> depth -> label -> aggregate -> report
fetch_patents.py        collection stage
depth_measures.py       structural measures with no LLM
aggregate.py            science-use profiles by assignee, sector or year
common/llm.py           schema-constrained labeling, provider-agnostic, cached
common/validate.py      agreement metrics and schema checks
benchmark/              model comparison: run_benchmark.sh, results.md (empty until run)
examples/demo/          worked example: four patents, every intermediate file, report.md
pilot/                  raw windows, labeled rows, labels_pilot.py (labels + rationales), depth and profile tables, summary.md
scripts/rebuild_pilot.sh    regenerates every derived pilot file and runs the schema checks
```

Contract: **fetch → window → depth → label (prompt + JSON schema) → validate against a double-coded benchmark → release with codebook.** Labeled rows carry the model, prompt hash, confidence and a one-sentence rationale.

## Reproducing the pilot

```
pip install -r requirements.txt
bash scripts/rebuild_pilot.sh            # labeled JSONL, summary, depth tables, profiles, schema checks (no API needed)

# re-label the pilot windows with a model and measure agreement with the pilot labels
export ANTHROPIC_API_KEY=...
python common/llm.py --prompt prompts/label_citation_function.md --schema schema.json \
    --input pilot/citation_windows_raw.jsonl --output pilot/relabeled.jsonl
python common/validate.py agreement --a pilot/citation_windows_labeled.jsonl --b pilot/relabeled.jsonl --id window_id --field function

# open-weight models on an OpenAI-compatible endpoint, with the agreement report written to benchmark/results.md
export OPENAI_API_KEY=...
bash benchmark/run_benchmark.sh https://api.together.xyz/v1 Qwen/Qwen3.6-32B-Instruct
```

## How the pilot data were collected, and by whom labeled

The pilot machine's shell could not reach patents.google.com, so the fetch stage ran as JavaScript inside a
browser session on the author's computer, on the data provider's own origin, and the JSON was saved into
`pilot/`; `fetch_patents.py` implements the same requests for a normal network environment. Details, including
the assignee queries and the fuzzy matches that were kept or dropped, are in `pilot/README_pilot_method.md`.

The pilot labels were produced by one closed model (claude-fable-5-1) in an interactive session with the
prompt in `prompts/`; `pilot/labels_pilot.py` holds every label with its rationale and regenerates the labeled
file. No second coder and no second model has labeled the pilot yet. Double coding, the open-weight model
comparison (`benchmark/`) and the 2,000-window benchmark are the first tasks of the fellowship year; the
production model will be chosen on that evidence and will be an open-weight model so the pipeline can be re-run
by anyone.

## Sources and terms

USPTO full text via PatentsView (public domain); Google Patents (terms of use; samples only); Reliance on
Science (Marx and Fuegi; cite it when using the patent–paper links); OpenAlex (CC0); DISCERN and KPSS under
their own licenses for the firm crosswalks. Code: MIT (`LICENSE`). Released data: CC BY 4.0. Citation:
`CITATION.cff`.

## Roadmap

- [x] Pilot: 109 patents, 291 windows labeled with rationales; depth measures; sector profiles (Oct 26–30, 2026)
- [ ] Double-code the pilot; open-weight model comparison (`benchmark/`)
- [ ] v0.1 (Q1 2027): depth measures for every Reliance on Science in-text citation in US patents 1976–2024, keyed to RoS
- [ ] 2,000-window benchmark (sector × citation format × decade), two coders, adjudication, codebook
- [ ] Full document-type and function passes over PatentsView description text, 1976–2024
- [ ] Firm linkage (DISCERN, KPSS, Golden Age panel) and industry-year / firm-year profiles; pre-1976 extension where in-text citations exist
- [ ] v1.0 release (code on GitHub, data on Zenodo and the i3 Index) with codebook, December 2027

Contact: Hansen Zhang, Duke University (Fuqua), hansen.zhang@duke.edu.
