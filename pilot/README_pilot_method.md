# How the pilot data were collected (Oct 26–27, 2026)

The pilot machine's shell could not reach patents.google.com, api.openalex.org or sec.gov, so the
fetch stage was executed as JavaScript inside a browser session on Hansen's computer and the JSON
results were saved here. The Python files in this repository implement the same logic for a normal
network environment. The JavaScript used for this pipeline:

```js
// granted US patents of an assignee (priority >= 2017) that contain "et al"
'/xhr/query?url=q%3D%22et+al%22%26assignee%3D' + encodeURIComponent(a) +
  '%26country%3DUS%26status%3DGRANT%26after%3Dpriority%3A20170101%26type%3DPATENT%26num%3D25&exp='
// description paragraphs from /patent/<pn>/en: div.description-paragraph
// citation cue regex (same as fetch_patents.CIT); window = 380 chars before, 420 after the cue
```

Sampling: 65 assignee queries in two batches (26 on Oct 26, 39 on Oct 27; two granted patents each
where available, up to three windows each), chosen to cover pharma, biotech tools, software/AI,
semiconductors, chemicals/materials, medical devices, energy and automotive/aerospace; 109 patents
from 68 assignees as printed on the patents. Three queries failed because an ampersand in the
assignee name (Johnson & Johnson, Procter & Gamble, Merck Sharp & Dohme) breaks the XHR JSON; "Merck
Sharp" was used instead. Google's assignee search is fuzzy, so several queries returned other firms
("Moderna" -> Moderna Enzymatics Co., Japan; "Boston Scientific Scimed" -> Medtronic and Scimed;
Panasonic and IMPEDANS for other queries); corporate fuzzy matches were kept and recorded under the
assignee as printed on the patent, and non-corporate or wrong-entity matches (Universite Laval,
Tesla Viet Nam Technology, Zimeno) were dropped (5 windows). Family and sibling duplicates (identical
windows across continuations and variety patents) are flagged with `is_family_duplicate` rather than
removed from the raw file.

Expansion draw (Oct 31, 2026, batches d1 and d2): 51 further assignee queries run with `../fetch_patents.py`
(`--source google --per-assignee 2 --max-windows 3 --after-priority 20170101`, the regex after `~` filtering on
the printed assignee), chosen to add new firms to each of the eight sectors; three queries (Uber, Netflix,
Broadcom) returned nothing, and the last eight patents were taken in query order to bring the pilot to exactly
200 patents (91 new patents, 224 windows, 59 printed assignees). Sibling patents with identical windows (Eastman,
Oracle, Northrop Grumman) are flagged as family duplicates; a boilerplate paragraph repeated across unrelated
patents of one firm (Twist Bioscience) is not, because that recurrence is what the definition-only label measures.

Labels were assigned by Claude (claude-fable-5-1) in an interactive session using the prompt in
`../prompts/label_citation_function.md`; the rationale for each label is in the `note` field.
A second coder has not yet labeled this set; double coding is the first task of the benchmark.
