# Depth measures vs. function label (pilot)

211 non-duplicate windows whose cited document is a paper, book, standards document or mixed. Substantive = foundation + method/tool + data/materials + prior art distinguished; the rest (background, boilerplate, reference list, own-family) are the non-substantive uses. Structure is detected by counting citation cues in the window; position is the citing paragraph's index over the number of description paragraphs.

## Citation structure

| structure | n | foundation | method or tool | prior art distinguished | data or materials source | background context | definitional boilerplate | incorporated reference list | own family continuation | substantive share |
|---|---|---|---|---|---|---|---|---|---|---|
| paired | 60 | 16 (27%) | 14 (23%) | 8 (13%) | 2 (3%) | 14 (23%) | 6 (10%) | 0 (0%) | 0 (0%) | 67% |
| standalone | 103 | 15 (15%) | 40 (39%) | 16 (16%) | 0 (0%) | 27 (26%) | 5 (5%) | 0 (0%) | 0 (0%) | 69% |
| string | 48 | 11 (23%) | 11 (23%) | 9 (19%) | 1 (2%) | 9 (19%) | 5 (10%) | 2 (4%) | 0 (0%) | 67% |

## Position in the description

| position | n | foundation | method or tool | prior art distinguished | data or materials source | background context | definitional boilerplate | incorporated reference list | own family continuation | substantive share |
|---|---|---|---|---|---|---|---|---|---|---|
| 20-60% | 72 | 10 (14%) | 35 (49%) | 8 (11%) | 2 (3%) | 11 (15%) | 5 (7%) | 1 (1%) | 0 (0%) | 76% |
| first 20% | 118 | 28 (24%) | 19 (16%) | 23 (19%) | 0 (0%) | 38 (32%) | 9 (8%) | 1 (1%) | 0 (0%) | 59% |
| last 40% | 21 | 4 (19%) | 11 (52%) | 2 (10%) | 1 (5%) | 1 (5%) | 2 (10%) | 0 (0%) | 0 (0%) | 86% |

## Reading

- Standalone vs. flanked does not separate substantive from non-substantive use in patents (67-69% substantive in all three groups), but it shifts *which* substantive use: standalone citations are method/tool far more often, while pairs and strings lean to foundation and background.
- Position does separate them: citations in the first fifth of the description (the background section) are the least substantive; citations in the examples and detailed description are mostly methods and materials.
- Caveats: a single coder's labels, regex structure detection on an 800-character window, and a recent-corporate-patent sample. The full build computes these three measures for every in-text citation (plus per-patent invocation counts) and reports them alongside the function label.