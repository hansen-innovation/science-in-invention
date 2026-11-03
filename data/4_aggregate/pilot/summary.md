# Pilot 1 summary: citation function in corporate patents

- Patents: 200 granted US patents from 127 assignees (priority 2017+; 65 assignee queries on Oct 26-27, three of which failed on an ampersand, and 51 more on Oct 31; two patents each where available), 515 citation windows found by the regex stage; 490 after dropping family and sibling duplicates (Genentech, Google, Illumina, Bayer, Abbott, Monsanto, Eastman, Oracle and Northrop Grumman sibling patents reuse identical text).
- Cited document type (regex stage catches 'et al.' in patent citations too): paper 316, patent 92, mixed 42, book 25, standards_doc 12, software_or_database 3.
- Function, all windows: method_or_tool 196, background_context 81, foundation 68, prior_art_distinguished 61, definitional_boilerplate 39, data_or_materials_source 25, own_family_continuation 14, incorporated_reference_list 6.
- Function, paper citations only (n=316): method_or_tool 114, foundation 64, background_context 57, prior_art_distinguished 45, definitional_boilerplate 21, data_or_materials_source 14, incorporated_reference_list 1.

## Function by sector (windows, family duplicates removed)

| Sector | foundation | method_or_tool | prior_art_distinguished | data_or_materials_source | background_context | definitional_boilerplate | incorporated_reference_list | own_family_continuation |
|---|---|---|---|---|---|---|---|---|
| automotive/aerospace | 8 | 26 | 7 | 0 | 4 | 0 | 1 | 0 |
| biotech tools | 6 | 29 | 3 | 2 | 4 | 7 | 2 | 2 |
| chemicals/materials | 7 | 30 | 9 | 5 | 11 | 12 | 1 | 1 |
| energy | 3 | 23 | 9 | 4 | 8 | 1 | 0 | 1 |
| medical devices | 4 | 25 | 8 | 4 | 8 | 0 | 0 | 4 |
| pharma | 33 | 9 | 7 | 6 | 26 | 15 | 2 | 0 |
| semiconductors | 5 | 19 | 11 | 0 | 10 | 3 | 0 | 5 |
| software/AI | 2 | 35 | 7 | 4 | 10 | 1 | 0 | 1 |

## What the pilot shows

1. The label set is applicable: every window received exactly one primary function, and the hard cases (one paper playing three roles in Scimed US11045648B2: materials source, mechanism, and distinguished prior art in consecutive paragraphs) are informative rather than ambiguous.
2. Sector signatures are visible: pharma patents cite science as *foundation* (target biology) and *background* (disease burden, standard of care); software/AI and semiconductor patents cite papers as *methods adopted* or *prior art distinguished*; chemicals patents cite *procedures* and *materials*. This is the firm-level 'science-use profile' the full dataset would deliver.
3. Two filters belong in the pipeline before labeling: (a) a cited-document-type classifier, because 'et al.' also marks patent citations (129 of 490 de-duplicated windows cite patents, standards contributions or books rather than papers); (b) family de-duplication, because description text is copied verbatim across continuations.
4. Boilerplate is a real category, not noise: antibody-fragment definitions (Ward 1989; Bird 1988; Huston 1988) and BLAST/FASTA citations recur across firms. Counting them as 'science use' would overstate reliance on science in biotech; the label keeps them separable.
5. Citation formats vary enough (author-year, numbered, 'supra', JVET document numbers, citations without years at Corteva) that the window finder should be a lightweight classifier rather than a regex in the full build; the regex here was tuned for recall and accepts noise.

Labels: `citation_windows_labeled.jsonl` (one row per window; `note` gives the reason). Prompt: `2_label/prompts/label_citation_function.md`.