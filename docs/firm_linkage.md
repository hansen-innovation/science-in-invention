# From citation windows to firm-year science-use profiles

The citation-level table answers *how* a patent uses a paper. The research use is one level up: how the
use of science in invention differs across industries and types of inventors, and how it has changed over
time. That needs three joins, all to existing open crosswalks, and `aggregate.py` to produce the shares.

## Units and keys

| Level | Key in this dataset | Joined to |
| --- | --- | --- |
| Citation window | USPTO patent number + paragraph index + cited-work string; Reliance on Science (RoS) citation record where it resolves | RoS v66 (patent–paper pair, in-text flag, confidence score); OpenAlex work id for the cited paper |
| Patent | USPTO patent number | PatentsView (`g_patent`, `g_cpc_current`, `g_assignee_disambiguated`): grant and priority dates, CPC classes, disambiguated assignee ids and assignee type (firm, university, government, individual) |
| Assignee-year | PatentsView disambiguated `assignee_id` × grant year | Firm identifiers below |
| Firm-year | gvkey / permno / Golden-Age firm id | Compustat, CRSP, the 1900–1980 firm panel |

## Firm crosswalks (1976–2024 first, then back in time)

1. **DISCERN** (Arora, Belenzon and Sheer): PatentsView assignees matched to Compustat firms (gvkey) with
   subsidiary ownership trees, so a patent assigned to "Genentech Inc" or "Amgen Research Munich GmbH" rolls
   up to the parent. Public firms, 1980 onward. This is the primary crosswalk for the modern period.
2. **KPSS** (Kogan, Papanikolaou, Seru and Stoffman): patents matched to CRSP permno from 1926 onward, with
   the market-value-based patent value measure. Used (a) for public firms before DISCERN starts and (b) as a
   second opinion on the DISCERN match where both exist.
3. **Golden Age firm panel** (Arora, Belenzon, Suh and Zhang, "The Rise of Absorptive Research in Corporate
   America, 1945–1980"): the 1900–1980 firm sample with patents and publications already matched. This is
   co-authored data; the plan is to release the *crosswalk* (assignee name → firm id → gvkey/permno where the
   firm survives into Compustat/CRSP) with the co-authors' agreement, not the underlying panel.
4. **Non-firm inventors**: universities, hospitals, government labs and individuals are kept as their own
   assignee types from PatentsView and ROR (for universities), so "types of inventors" can be compared
   without a firm identifier.

Industry comes from the firm (Compustat SIC/NAICS) where a firm match exists and from CPC → NAICS
concordances otherwise, so every patent has an industry even when the assignee is not a public firm.

## Time coverage and the pre-1976 question

PatentsView full description text starts in 1976, so the first release covers 1976–2024. The century-long
question ("when did American inventors start using science as the foundation of invention rather than as a
method or as background?") needs in-text citations from earlier patents. Two things decide how far back the
series goes: which years RoS's in-text citations cover (OCR'd full text exists for older US patents through
Google Patents and the USPTO bulk OCR files, with OCR noise rising before the 1950s), and the quality of the
cue finder on OCR text. The plan is to validate the cue finder and the labels on a stratified sample of
pre-1976 windows before extending the series, and to report OCR-related recall by decade.

## What the pilot already shows at this level

`aggregate.py --by sector` on the pilot (200 patents, 127 printed assignees, priority 2017+; sectors assigned
by hand from the assignee) gives the shape of the planned table. The 515 raw windows become 490 after
deduplication; sector profiles use the 395 windows citing papers, books, standards documents or mixed sets.
Pharma cites science as the basis of the invention (34%) and as context (27%); software/AI, biotech tools and
automotive/aerospace cite methods (57%, 50%, 51%); semiconductors and energy cite prior approaches improved on
(23%, 24%). These are descriptive patterns in a purposive sample, not population estimates or validated firm
linkages. Output: `pilot/profiles_sector.csv`, `pilot/profiles_assignee.csv`, `pilot/profiles_year.csv`.
Shares are reported with window and patent counts so that small cells are visible.

## Known pitfalls

- Continuations and divisionals copy description text verbatim: the family flag must be applied before any
  firm-year share is computed, or prolific filers (Genentech, Google, Illumina in the pilot) are over-weighted.
- Subsidiaries and name variants: rely on the DISCERN/KPSS parent mapping; never on string matching alone.
- Assignee changes at reassignment: profiles are keyed to the assignee at grant.
- The document-type filter must run first: "et al." marks patent citations and standards contributions too,
  and definitional boilerplate (antibody-fragment definitions, BLAST) inflates "reliance on science" in biotech
  if counted as science use.
