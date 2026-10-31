# Pilot 1 summary: citation function in corporate patents

- Patents: 109 granted US patents from 68 assignees (priority 2017+; 65 assignee queries in two batches, three of which failed on an ampersand, Oct 26-27), 291 citation windows found by the regex stage; 273 after dropping family and sibling duplicates (Genentech, Google, Illumina, Bayer, Abbott and Monsanto variety patents reuse identical text).
- Cited document type (regex stage catches 'et al.' in patent citations too): paper 163, patent 59, mixed 22, book 15, standards_doc 11, software_or_database 3.
- Function, all windows: method_or_tool 101, background_context 57, foundation 42, prior_art_distinguished 38, definitional_boilerplate 17, data_or_materials_source 8, own_family_continuation 8, incorporated_reference_list 2.
- Function, paper citations only (n=163): method_or_tool 47, background_context 40, foundation 39, prior_art_distinguished 29, definitional_boilerplate 5, data_or_materials_source 2, incorporated_reference_list 1.

## Function by sector (windows, family duplicates removed)

| Sector | foundation | method_or_tool | prior_art_distinguished | data_or_materials_source | background_context | definitional_boilerplate | incorporated_reference_list | own_family_continuation |
|---|---|---|---|---|---|---|---|---|
| automotive/aerospace | 6 | 9 | 4 | 0 | 3 | 0 | 0 | 0 |
| biotech tools | 3 | 10 | 1 | 0 | 1 | 2 | 0 | 0 |
| chemicals/materials | 3 | 23 | 4 | 4 | 6 | 4 | 1 | 1 |
| energy | 1 | 12 | 4 | 1 | 5 | 0 | 0 | 1 |
| medical devices | 3 | 11 | 4 | 1 | 1 | 0 | 0 | 3 |
| pharma | 24 | 6 | 4 | 1 | 23 | 10 | 1 | 0 |
| semiconductors | 1 | 9 | 10 | 0 | 9 | 0 | 0 | 2 |
| software/AI | 1 | 21 | 7 | 1 | 9 | 1 | 0 | 1 |

## What the pilot shows

1. The label set is applicable: every window received exactly one primary function, and the hard cases (one paper playing three roles in Scimed US11045648B2: materials source, mechanism, and distinguished prior art in consecutive paragraphs) are informative rather than ambiguous.
2. Sector signatures are visible: pharma patents cite science as *foundation* (target biology) and *background* (disease burden, standard of care); software/AI and semiconductor patents cite papers as *methods adopted* or *prior art distinguished*; chemicals patents cite *procedures* and *materials*. This is the firm-level 'science-use profile' the full dataset would deliver.
3. Two filters belong in the pipeline before labeling: (a) a cited-document-type classifier, because 'et al.' also marks patent citations (85 of 273 de-duplicated windows cite patents, standards contributions or books rather than papers); (b) family de-duplication, because description text is copied verbatim across continuations.
4. Boilerplate is a real category, not noise: antibody-fragment definitions (Ward 1989; Bird 1988; Huston 1988) and BLAST/FASTA citations recur across firms. Counting them as 'science use' would overstate reliance on science in biotech; the label keeps them separable.
5. Citation formats vary enough (author-year, numbered, 'supra', JVET document numbers, citations without years at Corteva) that the window finder should be a lightweight classifier rather than a regex in the full build; the regex here was tuned for recall and accepts noise.
6. Structural 'depth' measures (standalone vs. flanked citation; position in the description) are computable for every window without an LLM and line up with the function label in an informative way: position separates substantive from background use (59% substantive in the first fifth of the description vs. 86% in the last 40%), while standalone citations are disproportionately *methods adopted* (see `depth_by_function.md`, computed by `../depth_measures.py`).

Labels: `citation_windows_labeled.jsonl` (one row per window; `note` gives the reason). Prompt: `../prompts/label_citation_function.md`. Depth measures: `citation_windows_depth.jsonl`, `depth_by_function.md`.