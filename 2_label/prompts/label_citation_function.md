# Labeling guide: how does this patent use the cited work?

You will see a window of text (about 800 characters) from the description of a granted US patent. The window contains at least one citation cue ("et al.", a journal name with a year, a DOI, an arXiv id, a standards document number, or a patent number). Decide two things.

## 1. cited_doc_type — what is being cited?

- `paper`: journal article, conference paper, preprint, thesis.
- `patent`: patent or patent application (U.S. Pat. No., WO, EP, US 20xx/..., "application Ser. No."). "Smith et al." attached to a patent number is a patent citation, not a paper.
- `standards_doc`: standards-body contribution or specification (JVET/MPEG documents, 3GPP TS/TR, IEEE 802.x drafts, IETF RFCs).
- `book`: textbook, monograph, handbook, encyclopedia, laboratory manual (Current Protocols), vendor documentation (Redbooks).
- `software_or_database`: a tool or database cited through its paper or URL (BLAST, GCG, ATCC catalog).
- `mixed`: papers and patents (or other types) cited together in the same sentence for the same point.
- `none`: the cue is not a citation (e.g., "et al." inside a quoted product name).

## 2. function — the primary role of the cited work for the invention

Pick exactly one. If two apply, choose the one the sentence's main verb supports.

- `foundation`: a scientific finding, mechanism, structure, or clinical result that the invention rests on or exploits ("IL-2 signals through a high-affinity receptor (Kreig 2010)"; "by utilizing this mechanism"). The invention would not make sense without it.
- `method_or_tool`: a technique, algorithm, protocol, reagent, model architecture, synthesis procedure, or software that the invention uses or adapts ("the CNN may use the VGG architecture described in Simonyan"; "prepared according to the procedure of Das 2017"; BLAST for sequence identity).
- `prior_art_distinguished`: an earlier approach that the invention improves on, differs from, or works around; often signalled by "however", "conventional", "limitations", "in contrast", or by a problem statement following the citation.
- `data_or_materials_source`: where materials, cell lines, datasets, or components came from (ATCC CHO-K1; "substances listed in Kennedy et al. may be used").
- `background_context`: general context that frames the problem without being relied on or distinguished: disease burden, standard of care, market size, history of a technique, literature overviews, "for more information see".
- `definitional_boilerplate`: standard definitions copied across patents (antibody fragment definitions via Ward 1989 / Bird 1988 / Huston 1988; surfactant handbooks; "as used herein, X means ... see").
- `incorporated_reference_list`: a bulk list of references incorporated by reference without a stated role.
- `own_family_continuation`: the applicant's own parent or related application.

## 3. confidence

`high` when the sentence states the role; `medium` when inferred from surrounding text; `low` when the window is truncated or ambiguous.

## Output

Return JSON with keys: cited_doc_type, function, confidence, cited_work_string (the first citation verbatim), note (one sentence giving the reason). No other text.
