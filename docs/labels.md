# Why these labels

The function label answers one question about each in-text citation: *what is the cited work doing for this
invention?* Eight values, where each comes from, and why it is there.

| Label | The cited work is... | Where it comes from |
| --- | --- | --- |
| foundation | the finding, mechanism, structure or clinical result the invention rests on | "conceptual" use (Moravcsik and Murugesan 1975); *Motivation* and *Extends* (Jurgens et al. 2018); research findings that suggest a project (Cohen, Nelson and Walsh 2002); the "could not have been developed without" criterion (Mansfield 1991) |
| method or tool | a technique, protocol, algorithm, reagent or software the inventors use or adapt | "operational" use (Moravcsik and Murugesan); *Uses* (Jurgens et al.); instruments and techniques (Cohen, Nelson and Walsh) |
| prior art distinguished | an earlier approach the invention improves on, differs from or works around | "negational" use (Moravcsik and Murugesan); *Compares or Contrasts* and *weakness* (Teufel et al. 2006; Jurgens et al.); patent law: the applicant must argue novelty over the prior art |
| data or materials source | where materials, cell lines, datasets or components came from | the enablement requirement makes patents name sources; a source is not a method |
| background | context that frames the problem without being relied on or distinguished: disease burden, standard of care, history of a technique, overviews | "perfunctory" use (Moravcsik and Murugesan); *Background* (Jurgens et al.) |
| definitional boilerplate | a standard definition copied across patents (antibody fragments via Ward 1989, Bird 1988, Huston 1988) | patent drafting, not science use; without it, repeated definitions inflate biotech's apparent reliance on science |
| incorporated reference list | a bulk list incorporated by reference without a stated role | legal incorporation by reference |
| own-family continuation | the applicant's own parent or related application | not a use of science |

Three design choices.

1. **One axis, one label per citation.** Information science separates several axes (conceptual/operational,
   organic/perfunctory, confirmative/negational). The dataset's unit is the citation and its outputs are shares,
   so each citation takes the single role the sentence's main verb supports; the one-sentence rationale records
   any second role. Two labels per citation would make the shares uninterpretable.
2. **Substantive use is separated from everything else.** The first four labels are ways an invention draws on
   science; background is weak use; the last three are not use at all. A citation count treats all eight alike.
   The profiles report the substantive share next to the function shares so the distinction is visible.
3. **Patent-specific labels exist because patents are legal documents.** Prior art distinguished, boilerplate,
   incorporated lists and own-family citations have no counterpart in the scientific-paper schemes; they appear
   because of novelty arguments, claim drafting and incorporation by reference, and they are common enough
   (boilerplate alone is 44% of pharma's science citations in the 2010s decade cell) that folding them into
   "background" would distort the profiles.

## How well tested is the set?

Not yet against alternatives. What the pilots show: every one of the 486 windows took exactly one label, no
"cannot classify" residual appeared, and the hard cases are informative rather than ambiguous (one Boston
Scientific paper is materials source, mechanism and distinguished prior art in three consecutive paragraphs). What
they do not show: agreement between coders, stability across models, or whether a different partition would be
more useful. The first tasks of the fellowship year:

- double-code a stratified benchmark with a codebook and adjudication; report Cohen's kappa and per-label
  precision and recall;
- label the same windows with the six-class scheme of Jurgens et al. and with a three-class collapse
  (foundation, method, context) to measure what the extra labels buy and where they disagree;
- an open-coding pass in which the model describes the function in its own words for a sample of windows, then
  cluster the descriptions to look for uses the scheme misses;
- the open-weight model comparison in `benchmark/`.

All labels in this repository were produced by one closed model (claude-fable-5-1) in an interactive session with
`prompts/label_citation_function.md`. No second coder and no second model has labeled anything yet.

## References

- Cohen, W. M., Nelson, R. R., and Walsh, J. P. (2002). Links and impacts: the influence of public research on
  industrial R&D. *Management Science* 48(1), 1-23.
- Jurgens, D., Kumar, S., Hoover, R., McFarland, D., and Jurafsky, D. (2018). Measuring the evolution of a
  scientific field through citation frames. *Transactions of the ACL* 6, 391-406.
- Mansfield, E. (1991). Academic research and industrial innovation. *Research Policy* 20(1), 1-12.
- Moravcsik, M. J., and Murugesan, P. (1975). Some results on the function and quality of citations. *Social
  Studies of Science* 5(1), 86-92.
- Teufel, S., Siddharthan, A., and Tidhar, D. (2006). Automatic classification of citation function. *EMNLP 2006*.
