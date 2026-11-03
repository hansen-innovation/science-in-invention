"""Labels for the decade sample: citation windows from granted US patents of three sectors (pharma, chemicals,
electrical/electronics) in every decade from the 1900s to the 2020s, up to three windows per patent.

Core cells, 1980s-2010s (D001-D261, 94 patents of nine firms: Pfizer, Eli Lilly, Bristol-Myers; Dow Chemical,
Du Pont, Air Products; IBM, General Electric, Texas Instruments; priority and grant in the same decade).
Two draws, both from Google Patents with ../../fetch_patents.py on Oct 31, 2026 (the `draw` field of each row):
  "et al" (D001-D195): the first two granted US patents per firm and decade in Google's ranking that contain
    "et al". For the electronics firms this draw cited almost only patents (the 1990s cell had no paper
    citation at all), so electronics was topped up with
  "ieee" (D196-D261, electronics only): walking Google's ranking for the query "IEEE", the first two patents
    per firm and decade with at least one window that looks like a paper citation
    (--query IEEE --cue-ieee --require-paper-cue; "IEEE" added as a cue in the window finder). The electronics
    cells therefore pool both draws. US7570182B2 (TI, 2000s) was already in the first draw and was not added again.

Extension cells, 1900s-1970s and 2020s (D262-D420, 102 patents, draw "bigquery", Nov 1, 2026). Google Patents
blocks scraping after a few dozen queries, so these cells were drawn from the sampling frame of patents that
Reliance on Science v66 (Marx and Fuegi) lists as citing science in the body text, with assignee names and
full text from Google Patents Public Data on BigQuery (one query; local/decades_1900_2026/ in the working copy
holds frame.py, bq_draw.py, select_cells.py, merge_decades.py). Per sector and decade, up to three firms, taking
the nine firms above where they have such patents and period peers otherwise (Merck, Upjohn, Parke Davis;
Eastman Kodak, Monsanto, Union Carbide; Bell Telephone Laboratories, Western Electric, AT&T), the first two
patents per firm in FARM_FINGERPRINT order of the publication number with at least one window that looks like a
paper citation (--cue-early also accepts journal, volume and page without a year, as old citations are written).
The 1900s and 1910s hold every in-text citing grant in the frame whose assignee or CPC falls in the three
sectors; the frame has only about 145 such grants for those two decades and most of them are false positives of
the citation matching, so those cells are thin (one to three patents). Patents granted 1947-1975 print the front page's "References Cited" list at the end of the specification; the
window finder cuts that block (fetch_patents.cut_references_cited) so that only citations in the text count.
Window-finder recall on the frame's in-text citing patents after the cut: 9% (1900s), 6% (1910s), 46% (1920s), 33% (1930s), 26% (1940s), 26% (1950s), 35% (1960s), 50% (1970s), 79% (2020s),
as computed from select_cells.py's input; OCR text is the main loss before the 1950s.

Labels D001-D261 were produced on Oct 31, 2026 by claude-fable-5-1 in an interactive session with
prompts/label_citation_function.md; D262-D420 on Nov 1, 2026 by claude-fable-5-1 subagents inside Claude
Code (blind batches of 25 windows, same guide and schema). Each entry is window_id -> (cited_doc_type, function,
confidence, note). Run `python labels_decades.py` to write citation_windows_labeled.jsonl and summary.md. A blind
second coding by claude-opus-5-5 is in data/3_validate/results.md; it never replaces these labels.
"""
import collections, json, pathlib, re, sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from common.paths import DATA, out as dpath  # noqa: E402
from labels_pilot import first_citation, FUNCTIONS  # noqa: E402

L = {
 # pharma 1980s: Bristol-Myers US4675187A (antibiotic BBM-1675), US4775674A (imidazoquinolinones)
 "D001": ("paper", "method_or_tool", "high", "Taxonomic characterization methods (Becker 1965, Collins 1977) used to analyze the producing strain"),
 "D002": ("paper", "method_or_tool", "medium", "Goodfellow 1979 numerical taxonomy used as the scheme for classifying the producing strain"),
 "D003": ("paper", "method_or_tool", "high", "Prophage induction assay run according to the method of Lein 1962"),
 "D004": ("paper", "prior_art_distinguished", "medium", "Kozak 1930 describes the known unsubstituted parent compound; the claimed derivatives are delimited against it"),
 "D005": ("paper", "prior_art_distinguished", "medium", "Fryer 1977 describes a known trisubstituted compound in the background listing of related art"),
 "D006": ("paper", "prior_art_distinguished", "medium", "Reid 1956 describes a known diphenyl derivative in the background listing of related art"),
 # pharma 1980s: Eli Lilly US4727028A (hygromycin vectors), US4775624A (protein C expression)
 "D007": ("paper", "background_context", "medium", "Daniels 1973 cited to identify the antibiotic G418 whose resistance the vectors confer"),
 "D008": ("paper", "method_or_tool", "high", "SV40 and other eukaryotic promoters from the cited works are the components used or usable in the vectors"),
 "D009": ("paper", "method_or_tool", "high", "Gene synthesized in substantial accordance with the procedures of Itakura 1977 and Crea 1978"),
 "D010": ("paper", "method_or_tool", "high", "RSV long terminal repeat promoter from Gorman 1982 used as a component of the expression plasmid"),
 "D011": ("mixed", "method_or_tool", "high", "Thermoinducible runaway replicon of Uhlin 1979 / GB 1,557,774 used in the plasmid"),
 "D012": ("paper", "method_or_tool", "high", "Synthetic DNA made in substantial accordance with Itakura 1977 and Crea 1978"),
 # pharma 1980s: Pfizer US4750482A (hydrophilic adhesive), US4803076A (controlled-release tablet)
 "D013": ("patent", "prior_art_distinguished", "high", "Prior cross-linked hydrogel adhesive patents (Anderson, Hymes, Berg, Kater) described and contrasted"),
 "D014": ("patent", "prior_art_distinguished", "high", "Anderson patent's dipping process described as the prior approach"),
 "D015": ("patent", "prior_art_distinguished", "medium", "Further prior adhesive patents listed in the background"),
 "D016": ("mixed", "prior_art_distinguished", "high", "Brooke device (patent and J. Pharm. Sci. 1977) gives initially high release rates; no suggestion of tablet use"),
 "D017": ("paper", "foundation", "medium", "Langer 1981 analysis of geometries approaching zero-order release is the basis for the claimed tablet shape"),
 "D018": ("patent", "prior_art_distinguished", "high", "Prior ruminal bolus patents listed as related art"),
 # pharma 1990s: Bristol-Myers Squibb US5137877A (anthracycline conjugates), US5541110A (ribosome-inactivating protein)
 "D019": ("paper", "background_context", "high", "Mechanisms of anthracycline cytotoxicity (Peterson 1982, Bachur) frame the therapeutic context"),
 "D020": ("paper", "background_context", "medium", "Immunoconjugates of anthracyclines with antibodies are known in the art (Gallego 1984, Arnon 1982)"),
 "D021": ("paper", "prior_art_distinguished", "high", "Hurwitz 1975 amino-sugar attachment chemistry is the conventional approach the new linker departs from"),
 "D022": ("paper", "foundation", "medium", "Mechanism of ribosome inactivation (Endo 1987, Stirpe 1988) on which the new protein's activity rests"),
 "D023": ("paper", "background_context", "medium", "Montecucchi 1989 on sequence similarity among RIP families; context for the new protein"),
 "D024": ("paper", "prior_art_distinguished", "medium", "Known RIPs (Montecucchi 1989, Stirpe 1986) cited to show the new protein is similar to but distinct from them"),
 # pharma 1990s: Eli Lilly US5766846A (beta-amyloid detection), US6006753A (post-surgical catabolism)
 "D025": ("paper", "foundation", "medium", "APP mutation genetics (Goate 1991, Mullan 1992) is the evidence for the amyloid hypothesis the assay rests on"),
 "D026": ("paper", "background_context", "medium", "Prior reports that beta-amyloid is insoluble set up the problem the invention addresses"),
 "D027": ("paper", "prior_art_distinguished", "medium", "Earlier attempts to detect APP fragments in CSF and plasma, which the invention's assay goes beyond"),
 "D028": ("paper", "background_context", "high", "Surgery initiates metabolic changes (Shaw 1989, Little 1987): problem statement"),
 "D029": ("paper", "background_context", "high", "Catabolism raises morbidity (Thorell 1993, Chernow 1987): problem statement"),
 "D030": ("paper", "prior_art_distinguished", "medium", "Prior treatments with growth hormone, IGF-1 and insulin are the alternatives the invention differs from"),
 # pharma 1990s: Pfizer US5736534A (benzazepines), US5747498A (quinazolines)
 "D031": ("paper", "method_or_tool", "medium", "Literature preparations (Horning 1952, Huisgen 1954) of the benzazepinone starting materials used in the synthesis"),
 "D032": ("paper", "method_or_tool", "high", "ZnBH4 prepared according to Gensler 1960; reduction as described in Korsuki 1987"),
 "D033": ("paper", "method_or_tool", "high", "Ortho-acylation adapted from Sugasawa 1979"),
 "D034": ("paper", "method_or_tool", "high", "Tumor growth inhibition measured according to the methods of Corbett 1975"),
 # pharma 2000s: Bristol-Myers Squibb US7501420B2 (HIV aza-indoles), US7572618B2 (PCSK9 antibodies)
 "D035": ("paper", "background_context", "high", "HIV drug resistance literature (Larder and Kemp, Gulick) frames the need for new agents"),
 "D036": ("mixed", "prior_art_distinguished", "medium", "Indole derivatives reported as reverse transcriptase inhibitors (Greenlee, Romero; Boschelli patent) are the related art"),
 "D037": ("mixed", "prior_art_distinguished", "high", "Aza-indole amides disclosed previously (Kato, Levacher, WO and US filings); 'these structures differ from those claimed'"),
 "D038": ("paper", "background_context", "high", "Coronary heart disease risk factors and dyslipidemia genetics (Fredrickson 1967, Austin 1987): disease background"),
 "D039": ("paper", "background_context", "high", "Familial hypercholesterolemia genetics (Goldstein 1973, Goldstein and Brown 1978): disease background"),
 "D040": ("paper", "foundation", "medium", "PCSK9 identity and role in cholesterol homeostasis (Naureckiene 2003, Seidah 2003) is the target biology the antagonist rests on"),
 # pharma 2000s: Eli Lilly US7601700B2 (eIF4E), US7619069B2 (antibody)
 "D041": ("paper", "background_context", "medium", "Translation control under stress (Rosenwald 1999, Strudwick 2002): context"),
 "D042": ("paper", "foundation", "medium", "eIF4E as the rate-limiting cap-binding factor (Rychlik 1987) is the target biology the invention rests on"),
 "D043": ("paper", "background_context", "medium", "Regulation of eIF4E by Mnk1 phosphorylation (Flynn 1995, Waskiewicz 1997): further target context"),
 "D044": ("paper", "data_or_materials_source", "medium", "Germline framework segments DP-5, JH4, L1, Jk4 taken from Tomlinson 1992, Ravetch 1981, Cox 1994, Hieter 1982"),
 "D045": ("mixed", "method_or_tool", "high", "CHOK1SV glutamine synthetase expression system (de la Cruz Edmonds 2006, US 2007/0105771) used to produce the antibody"),
 "D046": ("paper", "method_or_tool", "high", "Standard CDR library construction approach of Wu 1998 used"),
 # pharma 2000s: Pfizer US7575746B2 (IGF-IR antibodies), US7626012B2 (CD40 antibodies)
 "D047": ("paper", "background_context", "medium", "IGF-IR structure and receptor family (Ullrich 1986, 1990): target description"),
 "D048": ("paper", "foundation", "medium", "Evidence that IGF-IR is elevated in tumors (Kaiser 1993, Pollak 1987) is the rationale for targeting it"),
 "D049": ("paper", "background_context", "medium", "Caloric restriction and the IGF-1 pathway (Hursting 2003): context"),
 "D050": ("paper", "background_context", "medium", "CD40 identity and expression (Stamenkovic 1989, Paulie 1985): target description"),
 "D051": ("paper", "foundation", "medium", "CD40's role in B cell proliferation and class switching (Foy 1996) is the biology the antibody acts on"),
 "D052": ("paper", "foundation", "medium", "CD40-TRAF signaling to NF-kB (Lee 1999, Pullen 1998) is the mechanism the antibody modulates"),
 # pharma 2010s: Bristol-Myers Squibb US10273236B2 (FXIa inhibitors), US9856320B2 (anti-PD-1)
 "D053": ("paper", "foundation", "high", "Coagulation cascade amplification via factor XIa (Gailani 2007, Hoffman 2003) is why FXIa is the target"),
 "D054": ("paper", "foundation", "high", "Clermont 2011 shows plasma kallikrein drives retinal vascular dysfunction; 'therefore a kallikrein inhibitor should have utility'"),
 "D055": ("book", "definitional_boilerplate", "high", "Prodrug preparation 'well known in the art' via standard medicinal chemistry texts (King 1994, Testa 2003, Wermuth 1999)"),
 "D056": ("paper", "background_context", "high", "Cancer neoantigens (Sjoblom 2006): immunotherapy context"),
 "D057": ("paper", "background_context", "high", "Ipilimumab for melanoma (Hodi 2010): the checkpoint-inhibitor context the invention joins"),
 "D058": ("mixed", "foundation", "high", "PD-1/PD-L1 ligand biology (Freeman 2000, Latchman 2001, Topalian 2012) is the mechanism the antibody blocks"),
 # pharma 2010s: Eli Lilly US10519158B2 (TRPA1 antagonists), US8741911B2
 "D059": ("paper", "foundation", "high", "TRPA1 knockout and antisense studies (Kwan 2006, Bautista 2006, Obata 2005) validate the target the antagonist acts on"),
 "D060": ("paper", "definitional_boilerplate", "high", "Pharmaceutical salts via Berge 1977: standard boilerplate"),
 "D061": ("paper", "foundation", "medium", "TRPA1's role in cancer, postoperative and pathological pain (Trevisan 2013, Wei 2012, Chen 2011) supports the claimed indications"),
 "D062": ("book", "definitional_boilerplate", "high", "Formulation 'well known in the art', see Remington: standard boilerplate"),
 "D063": ("book", "definitional_boilerplate", "high", "Pharmaceutical salts via Stahl handbook and Berge 1977: standard boilerplate"),
 "D064": ("book", "definitional_boilerplate", "medium", "Standard organic chemistry texts (Larock, March, Carey and Sundberg) cited for general synthetic methods"),
 # pharma 2010s: Pfizer US10138298B2 (antibody), US9683998B2 (anti-TL1A)
 "D065": ("book", "definitional_boilerplate", "high", "Conventional molecular biology techniques via Sambrook 1989 and laboratory manuals: standard boilerplate"),
 "D066": ("paper", "definitional_boilerplate", "high", "Antibody-fragment definition via Ward 1989 (dAb): standard boilerplate"),
 "D067": ("paper", "definitional_boilerplate", "high", "Kabat, Chothia and AbM CDR definitions (Johnson and Wu 2000, Chothia 1986, Martin 1989): standard boilerplate"),
 "D068": ("paper", "foundation", "medium", "TL1A/DR3 expression and co-stimulatory biology (Migone 2002, Prehn 2004, Shih 2009) is the target biology the antibody rests on"),
 "D069": ("paper", "foundation", "high", "TL1A/DR3-deficient and anti-TL1A mouse studies (Meylan 2008, Pappu 2008) show the pathway's role in autoimmune models"),
 "D070": ("paper", "foundation", "high", "Genome-wide association of TL1A polymorphisms with IBD (Yamazaki 2005, Barrett 2008, Jostins 2012) links the target to the indication"),
 # chemicals 1980s: Air Products US4542114A (FCC regenerator), US4602344A
 "D071": ("patent", "prior_art_distinguished", "high", "McGovern patent's oxygen-enriched regeneration with heat removal is the prior approach"),
 "D072": ("patent", "prior_art_distinguished", "high", "Miguerian patent's hot regeneration leaves nitrogen oxides untreated"),
 "D073": ("patent", "prior_art_distinguished", "high", "Pratt patent's oxygen diluted with flue gas has nearly the same effect as oxygen enrichment"),
 # chemicals 1980s: Dow US4587329A (dendrimers), US4798081A (ATREF)
 "D074": ("paper", "background_context", "medium", "Types of comb branching (Orofino 1961, Altores 1965, Sorenson 1968) described as background to branched polymers"),
 "D075": ("book", "background_context", "medium", "Cross-linked polymer types (Sorenson, Elias 1977) described as background"),
 "D076": ("paper", "method_or_tool", "high", "Hydrodynamic diameter calculated with the Hester-Mitchell relationship (Hester 1980)"),
 "D077": ("paper", "prior_art_distinguished", "high", "SEC (Lecacheux 1982, 1984) gives long-chain branching but 'leaves much to be desired' for short-chain branching"),
 "D078": ("paper", "background_context", "medium", "History of TREF (Desreux 1950, Shirayama): technique background"),
 "D079": ("paper", "prior_art_distinguished", "medium", "Wild's ATREF is the prior improvement the invention builds on and further improves"),
 # chemicals 1980s: Du Pont US4499082A (peptide boronic acids), US4732864A (radiolabeling)
 "D080": ("paper", "background_context", "high", "Protease classification (Cuypers 1982): background"),
 "D081": ("paper", "prior_art_distinguished", "high", "Known boronic acid protease inhibitors (Koehler 1971, Matteson 1981, Lindquist 1974) are the related art"),
 "D082": ("paper", "foundation", "medium", "Janoff's review of neutrophil elastase in emphysema is the rationale for inhibiting elastase"),
 "D083": ("paper", "background_context", "high", "Radiolabeled antibodies field (Eckelman 1980, Sfakianakis 1982); iodination disadvantages set up the problem"),
 "D084": ("paper", "prior_art_distinguished", "high", "Prior chelator-based metal labeling (Khaw 1980, Krejcarek 1977) is the approach the invention departs from"),
 "D085": ("paper", "data_or_materials_source", "high", "Thionein metal-binding fragments from Yoshida and Kondo 'can also be used in this invention'"),
 # chemicals 1990s: Air Products US5085731A and its sibling US5098516A (CVD copper)
 "D086": ("paper", "background_context", "high", "Selective tungsten CVD (Ohba 1990) given as the commercially practiced example of selective deposition"),
 "D087": ("mixed", "prior_art_distinguished", "high", "Prior uses of Cu(hfac)2 as a CVD precursor (Van Hemert 1965, Moshier patent, Reisman 1989, Kaloyeros 1990)"),
 "D088": ("mixed", "prior_art_distinguished", "high", "Prior copper CVD methods (Houle 1986, Charles patent, Girolami 1989) give contaminated films and no selectivity"),
 "D089": ("paper", "background_context", "high", "Duplicate of D086 (sibling patent US5098516A)"),
 "D090": ("mixed", "prior_art_distinguished", "high", "Duplicate of D087 (sibling patent US5098516A)"),
 "D091": ("mixed", "prior_art_distinguished", "high", "Duplicate of D088 (sibling patent US5098516A)"),
 # chemicals 1990s: Dow US5278272A and US5427807A (substantially linear ethylene polymers)
 "D092": ("paper", "prior_art_distinguished", "medium", "Ramamurthy 1986 and Moynihan 1990 give the sharkskin onset of conventional LLDPE that the new polymers exceed"),
 "D093": ("mixed", "prior_art_distinguished", "medium", "Kalika and Denn 1987 and WO 90/03414 are further prior findings and polymers compared against"),
 "D094": ("mixed", "method_or_tool", "high", "CDBI calculated from TREF as described in Wild 1982 and US 4,798,081"),
 "D095": ("paper", "method_or_tool", "high", "Ramamurthy 1986 classification of melt fracture used to identify the phenomena"),
 "D096": ("mixed", "method_or_tool", "high", "Duplicate of D094 (sibling patent US5427807A)"),
 "D097": ("patent", "method_or_tool", "medium", "Biaxial orientation processes in the cited patents 'can also be used to make the novel film structures'"),
 # chemicals 1990s: Du Pont US5530186A (high-oleic soybean), US5908975A (fructan)
 "D098": ("paper", "background_context", "high", "Monounsaturated fat and cholesterol (Mattson 1985): motivation"),
 "D099": ("paper", "prior_art_distinguished", "high", "McKeon 1982 thioesterase purification 'was not useful for soybean'"),
 "D100": ("paper", "method_or_tool", "high", "Seed-specific expression, antisense and cosuppression techniques (Goldberg 1989, van der Krol 1988, Napoli 1990) used"),
 "D101": ("book", "background_context", "high", "Sugarcane processing losses (Stout 1957, Alexander 1973): problem background"),
 "D102": ("paper", "background_context", "high", "Fructan content of tubers (Haunold 1989): problem background"),
 "D103": ("paper", "prior_art_distinguished", "medium", "Dykins 1933 constant-temperature storage prevents loss 'however the expense is prohibitive'"),
 # chemicals 2000s: Air Products US7473299B2 (adsorbents), US7551346B2 (displays)
 "D104": ("paper", "method_or_tool", "high", "Dual-site Langmuir model (Myers 1983) used to determine adsorbent working capacity"),
 "D105": ("paper", "method_or_tool", "high", "IAST (Myers and Prausnitz 1965) and HIAST (Mathias 1996) used for multicomponent adsorption"),
 "D106": ("mixed", "background_context", "high", "Electrochromic displays (O'Regan 1991, Bach 2002, patents) surveyed as another display type"),
 "D107": ("mixed", "background_context", "high", "Electro-wetting display (Hayes 2003) surveyed as another display type"),
 "D108": ("mixed", "background_context", "medium", "Gaseous-fluid electrophoretic media (Kitamura 2001, Yamaguchi 2001) noted as a variant"),
 # chemicals 2000s: Dow US6437014B1, US7592397B2
 "D109": ("patent", "prior_art_distinguished", "high", "Obijeski patent's elastic materials; 'do not disclose performance at elevated temperatures'"),
 "D110": ("patent", "prior_art_distinguished", "high", "Kurtz patent's irradiation; 'do not provide any disclosure regarding elasticity at elevated temperatures'"),
 "D111": ("patent", "prior_art_distinguished", "medium", "Known gamma-sterilization-resistant fibers (Jennings patent) listed as related art"),
 "D112": ("paper", "method_or_tool", "high", "ATREF-infrared method similar to GPC/FTIR described in Markovich 1991 and Deslauriers 2002"),
 "D113": ("book", "definitional_boilerplate", "medium", "Plastics Additives Handbook (Zweifel 2001) cited for additives in general"),
 "D114": ("mixed", "method_or_tool", "high", "Reductive amination as described in US 3,187,047 and Haskelberg 1948, Mastagli 1950, Alexander 1948"),
 # chemicals 2000s: Du Pont US7491536B2 (Bt toxins), US7541173B2 (isobutanol)
 "D115": ("paper", "foundation", "medium", "Proteolytic activation and receptor binding of Cry toxins (Rukmini 2000, Oppert 1999) is the mode of action of the claimed proteins"),
 "D116": ("paper", "background_context", "high", "Bt crops in agriculture (Aronson 2002, Schnepf 1998): background"),
 "D117": ("paper", "definitional_boilerplate", "high", "'Bt toxin' defined via Crickmore 1998, 2004 nomenclature"),
 "D118": ("mixed", "prior_art_distinguished", "high", "Petrochemical routes to isobutanol (Ullmann's, Carlini 2004) are 'expensive and not environmentally friendly'"),
 "D119": ("mixed", "prior_art_distinguished", "medium", "ABE fermentation (Blaschek patent, Girbal 1998) and recombinant 1-butanol hosts are the prior biological routes"),
 "D120": ("mixed", "prior_art_distinguished", "medium", "Prior approaches to butanol tolerance (mutagenesis patents, Tomas 2003, Quratulain 1995)"),
 # chemicals 2010s: Air Products US8993072B2 (aminosilanes), US9233990B2 (hydrosilylation)
 "D121": ("paper", "prior_art_distinguished", "medium", "Breederveld 1952 synthesis of dialkylaminochlorosilanes listed as related art"),
 "D122": ("paper", "prior_art_distinguished", "medium", "Anderson 1987 (dimethylamino)halogenosilanes listed as related art"),
 "D123": ("paper", "prior_art_distinguished", "medium", "Washburne 1969 chloro(dimethylamino)silanes listed as related art"),
 "D124": ("paper", "prior_art_distinguished", "medium", "Hao 1998 titanocene-catalyzed hydrosilylation of pyridines listed as related art"),
 "D125": ("paper", "prior_art_distinguished", "medium", "Hashimoto 2003 diruthenium hydrosilylation listed as related art"),
 "D126": ("paper", "prior_art_distinguished", "medium", "Gruber-Woelfler 2009 titanocene hydrosilylation of imines listed as related art"),
 # chemicals 2010s: Dow US9534064B2 (LDPE), US9777205B2
 "D127": ("paper", "method_or_tool", "high", "Goto 1981 reactor kinetic model used to set polymerization conditions"),
 "D128": ("paper", "data_or_materials_source", "high", "Rate constants in Table A taken from Goto 1981"),
 "D129": ("paper", "method_or_tool", "high", "'With the kinetics of Goto et al.' the required polymerization temperature is determined"),
 "D130": ("mixed", "method_or_tool", "medium", "Metallocene and constrained-geometry catalysts of the cited patents and papers (Spaleck 1994, Brintzinger 1994) are usable in the process"),
 # chemicals 2010s: Du Pont US10208298B2 (CRISPR delivery), US10435706B2 (insecticidal proteins)
 "D131": ("paper", "background_context", "high", "Gene knock-outs by homologous recombination (Austin 2004): background"),
 "D132": ("paper", "foundation", "medium", "Double-strand breaks enhance homologous recombination (Rudin 1989, Smih 1995): the principle genome-editing nucleases rest on"),
 "D133": ("paper", "prior_art_distinguished", "medium", "Nucleic-acid-based Cas9 and gRNA expression (DiCarlo 2013, Ma 2014) is the prior delivery approach the peptide-mediated method differs from"),
 "D134": ("paper", "definitional_boilerplate", "medium", "Catalog of known pesticidal proteins with citations, recurring across the assignee's plant patents"),
 "D135": ("mixed", "definitional_boilerplate", "medium", "Catalog of Cry proteins with patent and paper citations, recurring across the assignee's plant patents"),
 "D136": ("paper", "method_or_tool", "medium", "Fern phylogeny of Smith 2006 adopted as the classification used to define source species"),
 # electrical/electronics 1980s: General Electric US4417042A (RTV silicone), US4670899A (cellular radio)
 "D137": ("patent", "prior_art_distinguished", "high", "Nitzsche two-component RTV patent: 'the only trouble was that it was two-component'"),
 "D138": ("patent", "prior_art_distinguished", "high", "Nitzsche and Brown one-component alkoxy RTV patents had short shelf life"),
 "D139": ("patent", "prior_art_distinguished", "high", "Weyenberg, Cooper and Smith patents commercialized but 'still did not' meet the need"),
 "D140": ("patent", "background_context", "medium", "Conventional trunking techniques (Bowen, Williams patents) describe the system setting"),
 "D141": ("patent", "prior_art_distinguished", "low", "Bare entry in a list of prior-art patents (Hass 1983)"),
 "D142": ("patent", "prior_art_distinguished", "low", "Bare entry in a list of prior-art patents (Kai 1981)"),
 # electrical/electronics 1980s: IBM US4656580A (logic simulation machine), US4787040A (automotive display)
 "D143": ("patent", "prior_art_distinguished", "high", "Cocke patent's logic simulation machine; 'the present invention is an improvement upon' it"),
 "D144": ("patent", "prior_art_distinguished", "medium", "Cocke machine described as the base the invention improves"),
 "D145": ("patent", "prior_art_distinguished", "medium", "Cocke machine architecture walked through as the base design"),
 "D146": ("patent", "incorporated_reference_list", "medium", "Entry in the description's reference list (related IBM application)"),
 "D147": ("paper", "incorporated_reference_list", "medium", "Entry in the description's numbered reference list (Green 1978, Human Factors)"),
 "D148": ("paper", "incorporated_reference_list", "medium", "Entry in the description's numbered reference list (Preston 1982, IEE Proc.)"),
 # electrical/electronics 1980s: Texas Instruments US4673962A (DRAM cell), US4705361A (spatial light modulator)
 "D149": ("paper", "prior_art_distinguished", "high", "Jolly 1983 recrystallized-polysilicon DRAM cell is 'one approach' to the problem"),
 "D150": ("paper", "prior_art_distinguished", "high", "Corrugated capacitor cells (Sunami 1982, 1983; Itoh 1984) are a second prior approach"),
 "D151": ("paper", "prior_art_distinguished", "high", "Trench capacitor cells (Arai 1983, Minegishi 1983, Morie 1983) are a third prior approach"),
 "D152": ("paper", "background_context", "medium", "HEMT and superlattice physics explained with Drummond 1982"),
 "D153": ("paper", "foundation", "medium", "Resonant tunneling device physics (Chang 1974, Sollner 1983, Shewchuk 1985) that the modulator exploits"),
 # electrical/electronics 1990s: General Electric US5241456A, US5353498A (high density interconnect)
 "D154": ("patent", "own_family_continuation", "medium", "Related GE applications (Eichelberger, Kornrumpf) incorporated by reference"),
 "D155": ("patent", "method_or_tool", "high", "GE's HDI structure and fabrication methods disclosed in the Eichelberger patents are used"),
 "D156": ("patent", "own_family_continuation", "high", "Co-pending applications assigned to a common assignee, incorporated by reference"),
 "D157": ("patent", "method_or_tool", "high", "Adhesive blend and solvent die attach from commonly assigned Wojnarowski and Eichelberger filings used"),
 "D158": ("patent", "method_or_tool", "high", "Seed plating and metallization as disclosed in commonly assigned Wojnarowski patent used"),
 # electrical/electronics 1990s: IBM US5142578A (cryptography), US5317739A (coupling facility)
 "D159": ("patent", "incorporated_reference_list", "high", "Brachtl patent listed and incorporated by reference without a stated role"),
 "D160": ("patent", "incorporated_reference_list", "high", "Matyas patent listed and incorporated by reference without a stated role"),
 "D161": ("patent", "incorporated_reference_list", "high", "Matyas patent listed and incorporated by reference without a stated role"),
 "D162": ("patent", "own_family_continuation", "medium", "Related IBM applications (Bartow) listed"),
 "D163": ("patent", "own_family_continuation", "high", "Applications owned by the same assignee, filed the same day with the same priority date"),
 "D164": ("patent", "own_family_continuation", "medium", "Cross-invalidate mechanism disclosed in the co-filed Elko application, incorporated by reference"),
 # electrical/electronics 1990s: Texas Instruments Deutschland US5453747A, US5552789A (transponders)
 "D165": ("patent", "prior_art_distinguished", "high", "Cardullo and Schuermann patents describe prior interrogator-transponder systems"),
 "D166": ("patent", "method_or_tool", "high", "Transponder arrangement of Schuermann patent (the present inventor) used in the system"),
 "D167": ("patent", "method_or_tool", "medium", "TIRIS reader equipment of the Schuermann patent used as the on-board interrogator"),
 "D168": ("patent", "method_or_tool", "high", "Transponders operate 'according to the disclosure of' the Schuermann patent"),
 # electrical/electronics 2000s: General Electric US7581933B2 (airfoil coatings), US7584670B2 (actuator)
 "D169": ("patent", "prior_art_distinguished", "high", "Nitride coatings (Gupta, Sue patents); 'however, standard titanium nitride coatings are less capable'"),
 "D170": ("patent", "method_or_tool", "high", "McKibben fluid actuator of the Wassam patent used as the actuator"),
 # electrical/electronics 2000s: IBM US7606010B2 (magnetic tunnel junctions), US7609179B2 (compression)
 "D171": ("paper", "background_context", "high", "History of tunneling magnetoresistance (Julliere 1975, Moodera 1995, Miyazaki 1995)"),
 "D172": ("paper", "prior_art_distinguished", "high", "Alumina-barrier MTJs limited to about 50% TMR (Parkin 1999, Han 2000): the limitation overcome"),
 "D173": ("paper", "foundation", "medium", "Weak dependence of TMR on electrode composition (Parkin 1999, Monsma 2000) is the finding the design builds on"),
 "D174": ("paper", "background_context", "high", "Random reads miss in cache (Baer et al.): problem statement"),
 "D175": ("paper", "background_context", "high", "Branch misprediction penalties (Sprangle et al.): problem statement"),
 "D176": ("paper", "prior_art_distinguished", "medium", "LZ adaptive dictionaries (Lempel et al.) are the prior approach the fixed-dictionary scheme differs from"),
 # electrical/electronics 2000s: Texas Instruments US7570182B2 (ADPLL), US7589378B2 (LDMOS)
 "D177": ("patent", "method_or_tool", "high", "ADPLL described in the Staszewski publications and patent (incorporated by reference) is the architecture used"),
 "D178": ("patent", "method_or_tool", "high", "Same ADPLL reference repeated later in the same patent (see D177)"),
 "D179": ("patent", "prior_art_distinguished", "high", "D'Anna LDMOS patents use thick epitaxial layers; the prior devices"),
 "D180": ("patent", "method_or_tool", "medium", "LDD structure as known in the literature (Kwon patent) adopted in the device"),
 "D181": ("patent", "own_family_continuation", "high", "Co-pending commonly assigned Korec application, incorporated by reference"),
 # electrical/electronics 2010s: General Electric US9598963B2 (microchannel cooling), US9714578B2 (abradable coatings)
 "D182": ("patent", "method_or_tool", "medium", "Substrate materials as discussed in GE's Jackson patent adopted"),
 "D183": ("patent", "method_or_tool", "high", "Laser machining and EDM techniques of commonly assigned Wei and Bunker patents used to form grooves"),
 "D184": ("patent", "method_or_tool", "high", "Water jet and CNC systems as explained in the cited patents used"),
 "D185": ("patent", "method_or_tool", "medium", "Outer layer composition as described by Kirby et al. adopted"),
 "D186": ("paper", "prior_art_distinguished", "high", "Gel-casting of bulk articles by Janney et al.; the coating approach 'differs from' it"),
 "D187": ("patent", "prior_art_distinguished", "medium", "Kirby's transition layer contrasted with the abradable layers described here"),
 # electrical/electronics 2010s: IBM US9252120B2 (Cu post bumps), US9626298B2 (adapter functions)
 "D188": ("paper", "prior_art_distinguished", "medium", "Tessera's etched Cu post technology (Ran 2007) is an alternative prior approach"),
 "D189": ("paper", "prior_art_distinguished", "medium", "Cu die bumps in high-volume manufacturing (Yeoh 2006) is an alternative prior approach"),
 "D190": ("patent", "prior_art_distinguished", "medium", "Gruber compliant-mold solder deposition patents described as prior art"),
 "D191": ("patent", "own_family_continuation", "high", "Other IBM applications filed on the same day (Craddock)"),
 "D192": ("patent", "definitional_boilerplate", "medium", "IBM's standard emulation paragraph listing emulation patents (Beausoleil, Scalzi, Davidian)"),
 # electrical/electronics 2010s: Texas Instruments US10362326B2, US9584802B2 (HEVC video coding)
 "D193": ("standards_doc", "background_context", "medium", "HEVC working drafts (Wiegand WD3, Bross WD4) cited as the standard the invention operates within"),
 "D194": ("standards_doc", "background_context", "medium", "Duplicate of D193 (sibling patent US9584802B2)"),
 "D195": ("standards_doc", "own_family_continuation", "medium", "Inventors' own JCT-VC contributions (Sze and Budagavi) presenting aspects of this disclosure"),
 # ---- "IEEE" draw, electronics only (D196-D261): see module docstring ----
 # electronics 1980s: IBM US4455649A (split-band speech coder), US4441075A (LSSD package test)
 "D196": ("paper", "method_or_tool", "medium", "Split-band coding of Crochiere 1976 and Tribolet 1979 is the encoding scheme the apparatus implements"),
 "D197": ("paper", "background_context", "medium", "Esteban et al. cited for alternative split-band encoder arrangements; FIG. 1A is a generic representation"),
 "D198": ("paper", "method_or_tool", "high", "Johnson 1980 quadrature-mirror filter family is a suitable implementation of the sub-band filters"),
 "D199": ("patent", "own_family_continuation", "high", "Commonly assigned application Ser. No. 066,130 listed as related"),
 "D200": ("mixed", "method_or_tool", "medium", "LSSD design discipline of Eichelberger and Williams 1977 and the cited Eichelberger patents, incorporated by reference, is the structure the test method builds on"),
 "D201": ("paper", "method_or_tool", "high", "Bottorff 1977 partitioning technique is the automatic test-generation method employed"),
 # electronics 1980s: GE US4417385A (MOS process), US4622680A (hybrid subband coder)
 "D202": ("paper", "method_or_tool", "high", "Gibbons 1968/1972 ion implantation processes are the fabrication step employed"),
 "D203": ("paper", "method_or_tool", "high", "Hui 1981 selective oxidation technique is the process step used on the gate sidewalls"),
 "D204": ("paper", "method_or_tool", "high", "Hui 1981 again: the ways of forming the nitride oxidation mask used in the process"),
 "D205": ("patent", "own_family_continuation", "high", "Concurrently filed related application of the applicant (Szczutkowski et al.)"),
 "D206": ("patent", "own_family_continuation", "high", "Concurrently filed related application of the applicant (Szczutkowski et al.)"),
 "D207": ("paper", "background_context", "medium", "Inventor's own ICC 1984 paper cited as the survey of subband coder design art, followed by a reproduced reference list"),
 # electronics 1980s: TI US4811210A (optical crossbar interconnect), US4662746A (deformable mirror device)
 "D208": ("paper", "background_context", "medium", "McAulay 1983/1985, Haynes 1982 and Allen 1985 support the problem statement that parallelism is needed"),
 "D209": ("paper", "background_context", "medium", "McAulay 1983 cited for the documented difficulty of achieving parallelism, the problem the interconnection addresses"),
 "D210": ("paper", "prior_art_distinguished", "high", "Kung 1982 systolic architectures described and then limited by their fixed interconnections, which the invention avoids"),
 "D211": ("paper", "background_context", "high", "Hornbeck 1983 and its references cited for the range of SLM applications"),
 "D212": ("paper", "prior_art_distinguished", "medium", "Baumann 1953 Eidophor described as a known SLM in the background survey of prior devices"),
 "D213": ("mixed", "prior_art_distinguished", "medium", "Sprague 1981/1982 and US 4,380,373 describe prior SLM types in the background survey"),
 # electronics 1990s: IBM US5530963A (mobile Token Ring workstation), US5247597A (fiber-to-waveguide attachment)
 "D214": ("standards_doc", "background_context", "high", "IEEE 802.5 cited to define the Token Ring environment the invention operates in; 'well known in the art'"),
 "D215": ("standards_doc", "method_or_tool", "high", "The device driver presents a Token Ring appearance per IEEE 802.5: the protocol is implemented"),
 "D216": ("standards_doc", "method_or_tool", "medium", "Six-byte address field defined by IEEE 802.5 used in the invention's registration primitive"),
 "D217": ("paper", "incorporated_reference_list", "medium", "Entry in the description's reference list (Murphy 1985, fiber-to-waveguide attachment); role not stated in the window"),
 "D218": ("paper", "incorporated_reference_list", "medium", "Entry in the description's reference list (Kaufmann 1986, fiber attachment to GaAs waveguides)"),
 "D219": ("paper", "incorporated_reference_list", "medium", "Entry in the description's reference list (Armiento 1991, passive coupling on silicon waferboard)"),
 # electronics 1990s: GE US5127053A (speech coder), US5148167A (sigma-delta converter)
 "D220": ("paper", "background_context", "medium", "Markel and Gray 1974 cited to describe the standard LPC-10 vocoder in the problem framing"),
 "D221": ("paper", "prior_art_distinguished", "medium", "Schroeder and Atal 1984/1985 CELP coder described as the prior technique whose complexity the invention addresses"),
 "D222": ("paper", "prior_art_distinguished", "medium", "Atal and Remde 1982 multi-pulse coding described as the prior technique the hybrid coder builds on and improves"),
 "D223": ("paper", "incorporated_reference_list", "medium", "Entry in the description's numbered reference list (Candy 1974, sigma-delta modulation)"),
 "D224": ("paper", "incorporated_reference_list", "medium", "Entry in the description's numbered reference list (Candy 1976, interpolation from a sigma-delta modulator)"),
 "D225": ("paper", "incorporated_reference_list", "medium", "Entry in the description's numbered reference list (Candy 1985, double integration in sigma-delta modulation)"),
 # electronics 1990s: TI US5305317A (network adapter), US5828824A (test port)
 "D226": ("standards_doc", "method_or_tool", "high", "IEEE 802.5 token formats are the protocol the adapter transmits"),
 "D227": ("standards_doc", "method_or_tool", "medium", "IEEE 802.3 frame format is the protocol the embodiment handles"),
 "D228": ("standards_doc", "method_or_tool", "medium", "CRC algorithm common to the IEEE 802 MAC layers used for the frame check sequence"),
 "D229": ("standards_doc", "prior_art_distinguished", "high", "IEEE 1149.1 boundary scan described as a prior solution with pin-count and overhead drawbacks"),
 "D230": ("mixed", "prior_art_distinguished", "high", "The invention is stated to be an improvement on the IEEE 1149.1-1990 structure; own US 5,329,471 incorporated"),
 "D231": ("standards_doc", "method_or_tool", "medium", "IEEE 1149.1 interface reused by the invention's production test modes"),
 # electronics 2000s: IBM US7529388B2 (people counting), US7336095B2 (eFUSE)
 "D232": ("paper", "prior_art_distinguished", "high", "Hashimoto 1997 thermal-image counting described and its errors noted"),
 "D233": ("paper", "prior_art_distinguished", "medium", "Terada 1999 stereo-camera counting described as a prior method in the survey"),
 "D234": ("paper", "prior_art_distinguished", "high", "Kettnaker 1999 multi-camera counting described; its floor-topology assumption is the limitation"),
 "D235": ("standards_doc", "background_context", "medium", "IEEE 1149 JTAG cited as an example of well-known test interfaces in the background"),
 "D236": ("paper", "method_or_tool", "high", "Kothandaraman and Iyer 2002 eFUSE structure is the component implementation used"),
 # electronics 2000s: GE US7631564B1 (torque sensing), US6906630B2 (transformer monitoring)
 "D237": ("paper", "foundation", "medium", "Garshelis and Ivan 1974 detail the magnetoelastic effects on which the sensing systems, including the invention's, rest"),
 "D238": ("standards_doc", "method_or_tool", "high", "IEEE C57.91-1995 loading guide supplies the transformer models the system computes with"),
 "D239": ("standards_doc", "method_or_tool", "high", "Hot-spot computation based on IEEE C57.91-1995 and IEC 354"),
 "D240": ("standards_doc", "method_or_tool", "high", "Insulation aging computation based on IEEE C57.91-1995"),
 # electronics 2000s: TI US7467340B2 (dual-mode TAP)
 "D241": ("standards_doc", "method_or_tool", "high", "IEEE 1149.1 TAP architecture is the structure the dual-mode interface is built within"),
 "D242": ("standards_doc", "method_or_tool", "high", "Only the IEEE 1149.1 standard pins are needed for the TAP/STP interface: the standard port is used"),
 "D243": ("standards_doc", "background_context", "medium", "IEEE 1149.x family cited to describe what TAPs access; context for the interface"),
 # electronics 2010s: IBM US9300592B2 (link aggregation), US9794084B2 (VLAN)
 "D244": ("standards_doc", "background_context", "medium", "IEEE 802.3ad/802.1ax named as the standards defining link aggregation; context"),
 "D245": ("standards_doc", "prior_art_distinguished", "high", "The IEEE LAG architecture's no-sharing restriction is the limitation the invention works around"),
 "D246": ("standards_doc", "prior_art_distinguished", "medium", "Standard IEEE 802.3ad LAG configuration shown as the prior arrangement without port sharing"),
 "D247": ("standards_doc", "prior_art_distinguished", "high", "IEEE 802.1Q VLAN implementations described as conventional and facing the challenges the invention addresses"),
 "D248": ("standards_doc", "background_context", "medium", "IEEE 802.1Q named as the existing standard the invention stays compatible with"),
 "D249": ("standards_doc", "method_or_tool", "medium", "The IEEE 802.1Q tag format is the frame structure the method operates on"),
 # electronics 2010s: GE US9513630B2 (rail vehicle communication), US10511403B2 (time-sensitive networking scheduler)
 "D250": ("standards_doc", "method_or_tool", "medium", "IEEE 802.11 among the protocols the wireless network device uses"),
 "D251": ("standards_doc", "method_or_tool", "high", "IEEE 802.11-2012 is the protocol used for communication between vehicles; incorporated by reference"),
 "D252": ("standards_doc", "background_context", "medium", "IEEE 802.11 bands mentioned as the reference point for alternative frequencies"),
 "D253": ("standards_doc", "background_context", "medium", "IEEE 802.1 TSN standards introduced as the setting of the invention"),
 "D254": ("standards_doc", "method_or_tool", "high", "IEEE 802.1AS (gPTP) used by the scheduler to synchronize clocks"),
 "D255": ("standards_doc", "method_or_tool", "high", "IEEE 802.1AS used to detect clock instability and drift"),
 # electronics 2010s: TI US9854516B2 (TSCH networks), US9258829B1 (MIMO power-line communication)
 "D256": ("standards_doc", "method_or_tool", "medium", "IEEE 802.15.4e TSCH is the MAC protocol within which the invention operates"),
 "D257": ("standards_doc", "background_context", "medium", "IEEE 802.15.4 device classes (FFD, RFD) described as context"),
 "D258": ("standards_doc", "method_or_tool", "medium", "Duplicate of D256 within the same patent (the 802.15.4e paragraph is repeated)"),
 "D259": ("standards_doc", "method_or_tool", "high", "IEEE 1901.2 legacy preamble and frame format kept and extended by the MIMO frame"),
 "D260": ("standards_doc", "method_or_tool", "medium", "Legacy IEEE 1901.2 PHY frame structure is the format the MIMO frame extends"),
 "D261": ("patent", "own_family_continuation", "medium", "Commonly assigned US 8,265,197 incorporated for the power distribution system component"),
 # ---- pharma 1910s (bigquery draw, see docstring) ----
 # KUNHEIM AND CO US967775A (Pyrophoric metallic substance.)
 "D262": ("book", "definitional_boilerplate", "medium", "A 1903 monograph is cited with 'See' to support the definition of which elements count as rare-earth metals, a scope definition rather than a finding the invention builds on."),
 # ---- pharma 1920s (bigquery draw, see docstring) ----
 # PFIZER CHARLES & CO US1690128A (Process for preparing cinchophen)
 "D263": ("paper", "prior_art_distinguished", "medium", "Doebner's cinchophen synthesis is described with the skeptical 'purport to obtain' alongside a later patent method, reading as a review of earlier cinchophen routes the invention improves on, though the contrast is not stated in the window."),
 # ---- pharma 1930s (bigquery draw, see docstring) ----
 # MERCK & CO INC US1957461A (Acetyl-choline salts, dimethylamino-ethyl acetate, and proce)
 "D264": ("paper", "background_context", "medium", "The first citations document that acetylcholine salts are known to occur in natural products, framing the field; the later synthesis citations are then faulted for not isolating products, but the lead citation is context."),
 # MERCK & CO INC US2142140A (Salts of beta-alkylated-choline-alkyl-ethers and process for)
 "D265": ("paper", "prior_art_distinguished", "medium", "The invention's choline alkyl ether salts are said to be undescribed, while Dale and Ewins are cited for the related compounds where R is hydrogen, distinguishing the new compounds from the known ones."),
 # PFIZER CHARLES & CO US2165151A (Production of ascorbic acid and its isomers)
 "D266": ("paper", "background_context", "medium", "Maurer and Schiedt and Ohle are cited as a literature review of known conversions of 2-ketoaldonic esters to ascorbic acids ('It is known in the art'), with no contrast or reliance stated in the window; a Swiss patent follows in a separate sentence."),
 # UPJOHN CO US2120405A (Method of preparing hormones)
 "D267": ("mixed", "foundation", "medium", "The paper identifying the gonadotropic hormone in pregnant mares' serum is cited in the same sentence as the applicant's own copending application, and the invention concerns purifying these very substances, so the finding is what the invention rests on."),
 # ---- pharma 1940s (bigquery draw, see docstring) ----
 # PARKE DAVIS & CO US2226627A (Sterols of the male sex hormone type)
 "D268": ("paper", "method_or_tool", "high", "The starting mixture of pregnanediols is obtained by the solvent distribution method of Doisy et al., so the cited paper supplies a procedure used in the example."),
 # SQUIBB & SONS INC US2357364A (Keto derviatives of 17-ethynyl-17-hydroxy-perhydrocyclopente)
 "D269": ("book", "definitional_boilerplate", "high", "The monograph is cited only to fix the nomenclature and numbering system used in the description and claims."),
 # UPJOHN CO US2483999A (Nu-(beta-pyrrolidinoethyl)-phenothiazine)
 "D270": ("paper", "background_context", "medium", "The garbled OCR window points to published articles describing the antihistaminic results of the compounds as further reading rather than stating a role in the invention."),
 # ---- pharma 1950s (bigquery draw, see docstring) ----
 # BRISTOL COMPANY US2607223A (Apparatus for measuring rate of fluid flow)
 "D271": ("mixed", "background_context", "medium", "Faraday's book and Williams's paper are cited as the history of the magnetic-field principle, with the Kolin patent then named as the most advanced prior art, so the window frames the problem historically."),
 # BRISTOL LAB INC US2886595A (Tetracycline recovery)
 "D272": ("paper", "background_context", "medium", "The JACS article is cited as the place where the properties of tetracycline, with which the invention's substance is identified, are described, a pointer for more information."),
 # PARKE DAVIS & CO US2499290A (Process for preparing penicillin)
 "D273": ("paper", "method_or_tool", "high", "The penicillin solution is assayed by the cup method as described by Abraham et al. and Florey et al., so the papers supply the assay procedure and unit definition."),
 "D274": ("paper", "incorporated_reference_list", "medium", "This is the references-of-record list at the end of the patent, which gives the references without any stated role."),
 # PARKE DAVIS & CO US2820781A (Process for producing amides)
 "D275": ("paper", "method_or_tool", "high", "The ketene imine starting materials can be prepared by the methods set forth in the cited JACS articles, so they supply a preparation procedure."),
 # PFIZER & CO C US2637724A (Methylolstreptomycin)
 "D276": ("paper", "method_or_tool", "high", "Combined formaldehyde was 'assayed by the quantitative procedure of MacFayden' and streptomycin by the maltol assay of Boxer et al., so the cited papers supply the analytical procedures used in the examples."),
 "D277": ("paper", "method_or_tool", "high", "The product was 'analyzed by the method used previously (MacFayden ...)', so the cited paper supplies the assay procedure applied in the example."),
 # PFIZER & CO C US2771396A (Preparation of diaminopimelic acid and lysine)
 "D278": ("paper", "foundation", "medium", "The cited findings that lysine auxotrophs accumulate diaminopimelic acid and that a bacterial enzyme decarboxylates it to lysine are the biochemical basis a lysine-production process would exploit, although the window is truncated."),
 # ---- pharma 1960s (bigquery draw, see docstring) ----
 # BRISTOL MYERS CO US3322749A (Derivatives of penicillanic acid and cephalosporanic acid)
 "D279": ("paper", "method_or_tool", "high", "The carbodiimide reagent of Sheehan and Hess is listed as an equivalent acylating technique that the process may use."),
 "D280": ("paper", "method_or_tool", "high", "The acetylesterase treatment is carried out according to the procedure of Jansen et al., so the paper supplies the method used in the example."),
 # BRISTOL MYERS CO US3452039A (Certain 5-tetrazolyl benzothiophene compounds)
 "D281": ("paper", "method_or_tool", "high", "The general preparation process used for the intermediate acids is stated to be the one described by the cited papers."),
 "D282": ("paper", "method_or_tool", "high", "The preparation of rhodanine, a starting material, is stated to be the procedure described by Campbell et al."),
 "D283": ("paper", "method_or_tool", "high", "The example prepares the rhodanine intermediate by the cited route and then explicitly follows Campaigne's published method, so the papers supply synthesis procedures the invention uses."),
 # MERCK & CO INC US3321530A (3, 4-dihydro-2, 5-dimethoxynaphthalene)
 "D284": ("paper", "method_or_tool", "medium", "The first citation (OCR-split 'I. W. Cornforth et al.') is given as the procedure for preparing starting material (II) that the patent's preparations rely on, while the second, interleaved citation (Jacques 1953) is a prior method called undesirable; the first citation's role is a method used."),
 "D285": ("paper", "method_or_tool", "high", "The alkylation step is carried out 'by substantially the same procedure described by Cornforth et al.', so the cited paper supplies a synthesis procedure the example uses."),
 "D286": ("paper", "method_or_tool", "high", "The alkylation is performed 'by substantially the same procedure described by Cornforth et al.', so the cited paper provides the synthesis procedure used in the example."),
 # PFIZER & CO C US3232835A (2-chloro prednisones and the 9alpha-fluoro derivatives there)
 "D287": ("mixed", "method_or_tool", "high", "A patent and a journal paper are cited for the same point as the procedures by which the 11-hydroxyl blocking step of the process is accomplished."),
 "D288": ("paper", "method_or_tool", "high", "The 16-hydroxyl derivatives are prepared with osmium tetroxide 'in accordance with the method described by' the cited paper."),
 # PFIZER & CO C US3349124A (Oral antidiabetic agent)
 "D289": ("paper", "method_or_tool", "high", "The blood glucose assay used to test the compounds in dogs is the micro method of the cited paper."),
 # ---- pharma 1970s (bigquery draw, see docstring) ----
 # BRISTOL MYERS CO US3517024A (Anilinoalkyltetrazoles)
 "D290": ("mixed", "method_or_tool", "high", "Patents and journal papers are cited together as procedures of which 'use may be made' for the azide reaction step of the process."),
 # BRISTOL MYERS CO US3814755A (7-(omikron-aminomethylphenylacetamido)-3-(tetrazolo(4,5-b)py)
 "D291": ("mixed", "background_context", "high", "Book chapters, conference papers and 'two excellent recent reviews' are surveyed as a literature overview of cephalosporins without being relied on or distinguished."),
 "D292": ("paper", "incorporated_reference_list", "low", "A full bibliographic entry with no surrounding text, read as a references-cited list item without a stated role."),
 "D293": ("paper", "incorporated_reference_list", "low", "A full bibliographic entry with no surrounding text, read as a references-cited list item without a stated role."),
 # LILLY CO ELI US3890377A (3-Substituted phenylalkanohydroxamic acids)
 "D294": ("paper", "method_or_tool", "high", "The analgesic screening test used to demonstrate the activity of the compounds is a method similar to that reported in the cited paper."),
 # LILLY CO ELI US3927212A (Method for alleviating gastric mucosal bleeding)
 "D295": ("paper", "background_context", "medium", "Bromer et al. is cited for the established amino acid sequence of glucagon as background on the known hormone before the invention's new use in gastric bleeding is introduced."),
 "D296": ("paper", "method_or_tool", "high", "Aminopyrine is determined using the extraction procedure described by Jacobson et al. with a modification from Lin et al., so the papers supply the measurement method."),
 "D297": ("paper", "method_or_tool", "high", "Hemoglobin was measured 'in accordance with' the cited colorimetric method, so the paper supplies the assay protocol used in the experiment."),
 # PFIZER US3580921A (Heterocyclic mesoionic compounds)
 "D298": ("paper", "prior_art_distinguished", "high", "The paper is named as 'the closest prior art' teaching particular compounds from which the present compounds are distinguished."),
 "D299": ("paper", "method_or_tool", "high", "The diazotized aniline is treated with mercaptoacetic acid 'in accordance with the general procedure of' the cited paper in the process for preparing the compounds."),
 "D300": ("paper", "method_or_tool", "medium", "The intermediate arylazothioacetic acids are prepared by a slight modification of the general procedure of Duffin et al., so the cited work supplies a synthesis procedure the invention adapts."),
 # PFIZER US3702849A (4-(isoquinolin-1-yl) piperazine-1-carboxylic acid esters)
 "D301": ("paper", "method_or_tool", "high", "The 4-chloro-6,7-substituted quinoline intermediates are prepared by the method given by Riegel et al., a synthesis procedure the invention uses."),
 "D302": ("paper", "method_or_tool", "high", "The isoquinoline intermediates are prepared by a method derived from that of Anderson et al., a synthesis procedure the invention adapts."),
 "D303": ("paper", "method_or_tool", "high", "In the example the starting 4-chloro-6,7-dimethoxyquinoline is prepared by the general methods of Riegel et al., so the cited work supplies a synthesis procedure used in the invention."),
 # ---- pharma 2020s (bigquery draw, see docstring) ----
 # BRISTOL MYERS SQUIBB CO US11884650B2 (Substituted heterocyclic compounds)
 "D304": ("paper", "foundation", "medium", "The citation supports the mechanism that IL-23 signalling through IL-23R/IL-12Rbeta1 sustains pathogenic Th17 cells, the biological pathway the invention is built on."),
 "D305": ("paper", "foundation", "medium", "The knockout findings that p40-, p19- or IL-23R-deficient mice are protected from autoimmune disease are the target-validation evidence on which the invention's rationale rests."),
 "D306": ("paper", "foundation", "medium", "The clinical findings of elevated p40/p19 expression and Th17 cells in human disease lesions are the human evidence linking the target pathway to disease on which the invention relies."),
 # BRISTOL MYERS SQUIBB CO US12110290B2 (Triazolopyridinyl compounds as kinase inhibitors)
 "D307": ("paper", "background_context", "medium", "The citation supports a general description of necrosis versus apoptosis that frames the field before the window turns to regulated necrosis via RIPKs."),
 "D308": ("paper", "foundation", "medium", "The cited papers establish that necroptosis signalling depends on RIPK1 and RIPK3 kinase activity, the mechanism the invention exploits."),
 "D309": ("paper", "background_context", "medium", "The string of citations documents the diseases linked to the pathway, a literature overview that frames the therapeutic relevance without being relied on or distinguished."),
 # LILLY CO ELI US11970485B2 (RET kinase inhibitors)
 "D310": ("book", "definitional_boilerplate", "medium", "The standard statement that pharmaceutically acceptable salts and their preparation are well known in the art, with the usual Stahl handbook reference, is boilerplate copied across patents; the window is truncated."),
 "D311": ("mixed", "definitional_boilerplate", "medium", "The window is the tail of the standard pharmaceutically acceptable salts boilerplate citing the Stahl handbook and the Berge 1977 paper together."),
 "D312": ("book", "definitional_boilerplate", "high", "The statement that pharmaceutical compositions and their preparation are well known in the art, citing Remington, is standard formulation boilerplate."),
 # LILLY CO ELI US12351591B2 (KRas inhibitors)
 "D313": ("paper", "background_context", "low", "The window holds only a citation fragment to a review on RAS as a drug target with no sentence stating its role, so it is read as background literature on the target."),
 "D314": ("mixed", "definitional_boilerplate", "high", "The “as used herein” definition of pharmaceutically acceptable salt with the Stahl handbook and Berge 1977 references is standard boilerplate copied across patents."),
 "D315": ("book", "definitional_boilerplate", "high", "The definition of pharmaceutically acceptable carriers with the Remington reference for compositions and their preparation is standard formulation boilerplate."),
 # PFIZER US11643412B2 (Melanocortin 4 receptor antagonists and uses thereof)
 "D316": ("mixed", "background_context", "medium", "A patent and a review are cited together with “see e.g.” for an overview of melanocortin receptor expression patterns, general context that frames the target family."),
 "D317": ("paper", "background_context", "medium", "The citation supports a general description of MC4R as a GPCR and its brain expression, characterizing the target without stating a mechanism the invention exploits; the window is truncated."),
 "D318": ("paper", "foundation", "medium", "The cited studies establish that MC4R activation by alpha-MSH regulates body weight, the mechanism the invention rests on; the leading Gantz citation is cut off at the window start."),
 # PFIZER US12447207B2 (Human cytomegalovirus gB polypeptide)
 "D319": ("paper", "data_or_materials_source", "high", "The cited paper's S4 Fig. alignment of sixty HCMV gB sequences is the source of additional gB sequences for the invention."),
 "D320": ("mixed", "definitional_boilerplate", "high", "This is the standard sequence-identity definition boilerplate listing the Needleman-Wunsch, Pearson-Lipman, GCG software and Sambrook/Ausubel manual references; the leading citation is truncated."),
 "D321": ("paper", "data_or_materials_source", "high", "The sentence points to Burke et al. for the sixty native HCMV gB sequences available from NCBI RefSeq, a source of sequence data for the invention."),
 # ---- chemicals 1910s (bigquery draw, see docstring) ----
 # CORNING GLASS WORKS US1304623A (Glass.)
 "D322": ("paper", "method_or_tool", "high", "The citation is given “for procedure” of the hot-water solvent attack test used to measure the chemical stability of the glass, so the cited work supplies a test method."),
 # GEN BAKELITE COMPANY US1038475A (Process of making insoluble bodies derived from phenol alcoh)
 "D323": ("paper", "foundation", "medium", "The inventor cites his own earlier paper for the finding that heating phenol-alcohols with a small excess of phenol gives fusible, soluble resins, the chemistry the invention builds on."),
 # GEN BAKELITE COMPANY US1146045A (Process for making insoluble bodies derived from phenol alco)
 "D324": ("paper", "foundation", "medium", "The inventor cites his own earlier paper for the finding that heating phenol-alcohols with a small excess of phenol yields fusible, soluble resins, the chemistry on which the invention rests."),
 # ---- chemicals 1920s (bigquery draw, see docstring) ----
 # EASTMAN KODAK CO US1574944A (Photographic light-sensitive material and process of making )
 "D325": ("paper", "method_or_tool", "high", "The inert gelatin used in the invention 'may be prepared in the way described' in the cited article, so the paper supplies a preparation procedure the invention uses."),
 # EASTMAN KODAK CO US1600736A (Art of light-sensitive photographic materials)
 "D326": ("paper", "method_or_tool", "high", "The gelatin is prepared by the ash-free gelatin procedure described in the cited article, a preparation method the invention uses."),
 # ---- chemicals 1930s (bigquery draw, see docstring) ----
 # DU PONT US1967862A (Cyclic compound and process for preparing same)
 "D327": ("patent", "background_context", "low", "The window recounts the history of the field ('Following this work a series of patents has been applied for or issued') without stating reliance or a shortcoming, and it is truncated before any contrast."),
 # EASTMAN KODAK CO US2166736A (Photographic emulsion)
 "D328": ("paper", "data_or_materials_source", "medium", "The citation identifies one of the Formula III compounds that 'can advantageously be employed' as a reactant, i.e. it tells where the material is described, like 'substances listed in X may be used'."),
 "D329": ("paper", "method_or_tool", "high", "Compounds of Formula III 'can be prepared as described by' the cited authors, so the papers supply synthesis procedures the invention uses."),
 # EASTMAN KODAK CO US2177403A (Dye from imidazolones)
 "D330": ("paper", "data_or_materials_source", "low", "The truncated journal citation sits beside reagent quantities in a synthesis example, so it appears to identify a starting material, but the window is too short to be sure."),
 "D331": ("paper", "data_or_materials_source", "medium", "The citation is attached to the starting material 1,3-diphenyl-2-thiohydantoin in an example, identifying the source describing that reagent rather than a procedure or finding."),
 "D332": ("paper", "data_or_materials_source", "medium", "The citation identifies the starting material 3-phenyl-2-thiohydantoin used in the example, pointing to where that reagent is described."),
 # MONSANTO CHEMICALS US2064752A (Preservation of rubber)
 "D333": ("paper", "data_or_materials_source", "medium", "The citation identifies the acetone-aniline reaction product that is the starting material treated with hydrochloric acid in the embodiment, pointing to where that material is described."),
 # MONSANTO CHEMICALS US2100998A (Preservation of rubber)
 "D334": ("paper", "data_or_materials_source", "medium", "The citation identifies the ketone-amine reaction product used as one component of the antioxidant mixture, i.e. the source describing that material."),
 # ---- chemicals 1940s (bigquery draw, see docstring) ----
 # ALLIED CHEM & DYE CORP US2456358A (Thermoplastic resins and process of making)
 "D335": ("book", "method_or_tool", "high", "The melting points were determined by the cube-in-mercury method described in the Mattiello handbook, so the book supplies the measurement technique."),
 # DU PONT US2365493A (Purification of p-phenetidine)
 "D336": ("paper", "method_or_tool", "high", "The hydrogenation in Example III uses a reduced nickel on kieselguhr catalyst 'such as is described in' the cited paper, a reagent/technique the invention uses."),
 # EASTMAN KODAK CO US2251286A (Process of preparing oxatricarbocyanine dyes)
 "D337": ("paper", "prior_art_distinguished", "high", "The cited work is given for a known method that 'is not sufficient to produce' the tricarbocyanine dyes, a limitation the invention overcomes."),
 "D338": ("paper", "data_or_materials_source", "medium", "The salts of anil compounds that the invention employs 'are described by' the cited papers, so the citations identify the usable reagents rather than a procedure or finding."),
 # EASTMAN KODAK CO US2398454A (Anthraquinone compounds)
 "D339": ("mixed", "method_or_tool", "high", "The amine and alcohol intermediates 'can be prepared ... in accordance with the method of' the cited patent and paper, so both supply synthesis procedures the invention uses."),
 # ---- chemicals 1950s (bigquery draw, see docstring) ----
 # DOW CHEMICAL CO US2871269A (Preparation of keto ethers)
 "D340": ("mixed", "incorporated_reference_list", "low", "The window is a fragment of a references-cited list (a journal article and a book) with no surrounding text stating a role."),
 # DOW CHEMICAL CO US2905588A (Growing and protection of crops and compositions therefor co)
 "D341": ("book", "definitional_boilerplate", "high", "The dictionary is cited only to define the terms growth media and soil as used in the specification and claims."),
 # EASTMAN KODAK CO US2739956A (Methoxy vinylnaphthalenes and polymers thereof)
 "D342": ("paper", "incorporated_reference_list", "medium", "The Bachmann and Cohen entries are the references-cited list interleaved with the final claim by OCR, with no stated role."),
 # EASTMAN KODAK CO US2901466A (Linear polyesters and polyester-amides from 1,4-cyclohexaned)
 "D343": ("paper", "data_or_materials_source", "medium", "The citation is attached to the trans-1,4-cyclohexanedimethanol starting material and its melting point, identifying the source characterization of a reagent used in the example."),
 # UNION CARBIDE CORP US2816930A (Aralkyl carbinols)
 "D344": ("mixed", "incorporated_reference_list", "medium", "The window lists two references-cited entries (a Chemical Abstracts entry and a textbook) in list format with no stated role."),
 # ---- chemicals 1960s (bigquery draw, see docstring) ----
 # AIR PROD & CHEM US3150138A (Method of preparing monoquaternary nitrogen compounds)
 "D345": ("paper", "prior_art_distinguished", "high", "Explicitly introduced as prior art literature whose quaternization gave only diquaternary or secondary-alkyl monoquaternary products and no primary compounds, a limitation the invention addresses."),
 # AIR PROD & CHEM US3154522A (Polyisocyanurate preparation using a triethylene diamine and)
 "D346": ("paper", "background_context", "medium", "Cited as an example in a literature overview of how catalyst activity has been measured and ranked, framing the catalyst problem without being relied on or distinguished."),
 # DOW CHEMICAL CO US3207724A (Self-extinguishing styrene-acrylate copolymers with brominat)
 "D347": ("paper", "method_or_tool", "high", "The brominated cyclopropyl benzenes used as self-extinguishing agents are prepared by the synthesis method of the cited article."),
 # DU PONT US3214500A (Process for making filamentary structures prepared from the )
 "D348": ("mixed", "method_or_tool", "medium", "Patents are cited for the procedures by which the polycarbonates are produced and the Schnell article as a general discussion of their preparation and properties."),
 "D349": ("paper", "method_or_tool", "high", "Molecular orientation is measured by the sonic velocity method of the cited article."),
 # DU PONT US3364049A (Self-destructible decal with adhesive on one surface and ind)
 "D350": ("paper", "method_or_tool", "high", "Glass transition temperature is determined according to the method described in the cited article."),
 # ---- chemicals 1970s (bigquery draw, see docstring) ----
 # DOW CHEMICAL CO US3907815A (Process for preparing phosphorothioates and phenylphosphonot)
 "D351": ("none", "background_context", "low", "The cue is the inventor name in the patent's own header, not a citation to any work."),
 "D352": ("paper", "background_context", "medium", "The articles are cited with see-for-example as overviews listing commercially available phosphorothioates, framing the field rather than being relied on or distinguished."),
 # DU PONT US3502631A (Polymers of cyclic internal olefins)
 "D353": ("mixed", "method_or_tool", "high", "The high-pressure polymerizations are carried out in the tetrahedral anvil apparatus of the cited patent as modified in the cited NBS journal article."),
 "D354": ("mixed", "method_or_tool", "high", "The Beilstein handbook and journal articles are cited for the literature methods by which the monomeric cyclic olefins used in the invention are prepared."),
 # UNION CARBIDE CORP US3746738A (Silicon containing polyazimides)
 "D355": ("mixed", "method_or_tool", "medium", "A patent and a J. Org. Chem. paper are cited together as the full description of the Michael addition procedure that the invention uses, with further patents and papers listed as describing the same reaction."),
 # UNION CARBIDE CORP US3790522A (Polyepoxide and amine hardener compositions)
 "D356": ("mixed", "data_or_materials_source", "medium", "The patents and the Carswell book are cited only to identify the bisphenols and polyphenylols that may be used as the phenol reactants, i.e. where the materials are described."),
 "D357": ("paper", "method_or_tool", "high", "The article is cited as the full description of the settling gage and test procedure used to measure the property in the patent."),
 # ---- chemicals 2020s (bigquery draw, see docstring) ----
 # AIR PROD & CHEM US12421109B2 (Process and apparatus for cracking ammonia)
 "D358": ("paper", "background_context", "medium", "Reports the literature ranking of metal activity for ammonia cracking as context for the catalysts, without the window stating that the invention relies on or departs from it."),
 "D359": ("mixed", "data_or_materials_source", "high", "A patent application and three papers are cited together as the sources of suitable conventional catalysts that may be used in the invention."),
 "D360": ("paper", "method_or_tool", "high", "The required catalyst activity is defined relative to a rate calculated with equation 9 proposed by Lamb et al., so the cited equation is used as the benchmark calculation."),
 # AIR PROD & CHEM US12428294B2 (Process and apparatus for cracking ammonia)
 "D361": ("paper", "background_context", "medium", "Reports the literature ranking of metal activity for ammonia cracking as context for the catalysts, without the window stating that the invention relies on or departs from it."),
 "D362": ("mixed", "data_or_materials_source", "high", "A patent application and three papers are cited together as the sources of suitable conventional catalysts that may be used in the invention."),
 "D363": ("paper", "method_or_tool", "high", "The required catalyst activity is defined relative to a rate calculated with equation 9 proposed by Lamb et al., so the cited equation is used as the benchmark calculation."),
 # DOW GLOBAL TECHNOLOGIES LLC US12502872B2 (Synthetic leather)
 "D364": ("paper", "foundation", "medium", "The papers model the theoretical benefits of a polydisperse block distribution, the property the invention's copolymer exploits for its improved physical properties."),
 # DUPONT NUTRITION BIOSCI APS US11318174B2 (Probiotics for use in the prevention or treatment of illness)
 "D365": ("paper", "foundation", "high", "The finding that a commensal bacterium carrying a cross-reactive peptide influences CD8 T cells is the mechanism the probiotic invention builds on, as the following 'Thus, probiotics could influence' sentence makes explicit."),
 "D366": ("paper", "background_context", "high", "The study is cited for the prevalence of long-COVID symptoms, framing the disease burden rather than being relied on or distinguished."),
 "D367": ("paper", "data_or_materials_source", "high", "The predicted SARS-CoV-2 epitopes from the paper are the input dataset for the BLAST homology searches against the probiotic genomes."),
 # DUPONT SAFETY & CONSTRUCTION INC; PIONEER HI BRED INT US12279566B2 (Efficient hydroponic cultivation system and method)
 "D368": ("paper", "foundation", "medium", "The finding that high root temperature reduces root growth is the rationale on which the reflective housing membrane's cooling design rests."),
 "D369": ("paper", "foundation", "medium", "The finding that oxygen solubility falls and plant growth suffers at higher temperature supports the design rationale for keeping the nutrient solution cool."),
 "D370": ("patent", "method_or_tool", "medium", "The cited patents describe the flash spinning processes by which the plexifilamentary webs used in the invention are produced, incorporated by reference."),
 # ---- electrical/electronics 1900s (bigquery draw, see docstring) ----
 # STONE JOHN STONE US767972A (Method of receiving space-telegraph signals.)
 "D371": ("paper", "method_or_tool", "high", "The bolometer instrument the invention employs is described in Langley's papers, which the applicant cites in place of describing it."),
 "D372": ("paper", "incorporated_reference_list", "low", "The window is a bare bibliographic list of Langley's papers with no verb or stated role for the cited works."),
 "D373": ("paper", "background_context", "high", "The papers are cited for the history of other applications of the bolometer (dielectric constants, Hertz waves), framing context rather than something relied on."),
 # ---- electrical/electronics 1920s (bigquery draw, see docstring) ----
 # BELL TELEPHONE LABOR INC US1675880A (Electric-current transmission)
 "D374": ("paper", "method_or_tool", "medium", "The article describes the compressed powdered iron rings used as the core of the auto-transformer in the circuit."),
 # GEN ELECTRIC US1475164A (Signal-transmitting system)
 "D375": ("paper", "method_or_tool", "high", "The applicant states that the invention employs magnetrons as fully described in Hull's article."),
 # GEN ELECTRIC US1502904A (Elastic-fluid turbine rotor and method of avoiding tangentia)
 "D376": ("book", "method_or_tool", "medium", "The light-spot display arrangement used in the invention is a well-known one set forth in the cited book."),
 # WESTERN ELECTRIC CO US1563620A (Oscillation generator)
 "D377": ("paper", "foundation", "medium", "The circuit's linear differential equations, developed in the cited article, are the theoretical analysis on which the invention's operation rests."),
 # WESTERN ELECTRIC CO US1615988A (Carrier transmission system)
 "D378": ("paper", "method_or_tool", "high", "Morse telegraph equipment as shown in the article may be associated with the invention's transmitting and receiving channels."),
 # ---- electrical/electronics 1930s (bigquery draw, see docstring) ----
 # BELL TELEPHONE LABOR INC US2070666A (Modulating system)
 "D379": ("mixed", "method_or_tool", "high", "The negative feed-back technique disclosed in Black's article and copending application is applied in the invention to neutralize distortion."),
 "D380": ("patent", "method_or_tool", "high", "The modulator used in the circuit may be of the type disclosed in the cited patent."),
 # BELL TELEPHONE LABOR INC US2075956A (Electric wave translating system)
 "D381": ("mixed", "method_or_tool", "high", "The feed-back amplifier type and its notation used in the invention are those disclosed in Black's application and article."),
 # IBM US2153208A (Record controlled machine)
 "D382": ("none", "own_family_continuation", "low", "The window is the drawing-sheet header of the patent itself; the number is the patent's own and not a citation."),
 # WESTERN ELECTRIC CO US1818131A (Mechanical transmission system)
 "D383": ("mixed", "method_or_tool", "high", "The cited patents and Zobel's paper supply the electric wave filter design formulae applied to calculate the mechanical vibration filter."),
 # WESTERN ELECTRIC CO US1861851A (Submarine signaling cable)
 "D384": ("paper", "method_or_tool", "medium", "The paper gives the rigorous analytic process for computing the return-conductor resistance, a design calculation for which the patent also offers an approximation."),
 "D385": ("paper", "background_context", "low", "The window is a truncated citation fragment with no sentence stating how the article is used."),
 # ---- electrical/electronics 1940s (bigquery draw, see docstring) ----
 # AMERICAN TELEPHONE & TELEGRAPH US2345933A (Phase control in electrical transmission)
 "D386": ("paper", "method_or_tool", "medium", "Phase-shift measurements needed for the compensator may be made by the methods discussed in the article, although a limitation of those methods is also noted."),
 "D387": ("paper", "method_or_tool", "high", "The phase angle meter may be a recorder of the type shown in the cited article's Fig. 4, a component used in the apparatus."),
 # AMERICAN TELEPHONE & TELEGRAPH US2375066A (Automatic coin return system)
 "D388": ("paper", "method_or_tool", "medium", "The invention operates within the crossbar dial switching system whose line link frame and remaining apparatus are described in the cited paper."),
 # BELL TELEPHONE LABOR INC US2204762A (Piezoelectric crystal apparatus)
 "D389": ("paper", "background_context", "medium", "The paper is cited only as an illustration of how the crystal may be connected in a filter system, framing a use case rather than a technique the invention relies on."),
 "D390": ("paper", "data_or_materials_source", "medium", "The known elastic constants of quartz used in the orientation formula are taken from the cited publication, so it serves as the source of the numerical data."),
 # BELL TELEPHONE LABOR INC US2220942A (Acoustic device)
 "D391": ("paper", "method_or_tool", "high", "Zobel's transformation theorem is applied to show the equivalence of the modified damping arrangement, so the paper supplies a method used in the design."),
 # GEN ELECTRIC X RAY CORP US2343729A (X-ray apparatus)
 "D392": ("paper", "foundation", "medium", "The article investigated the rapid anode cooling thought to cause anode cracks, the physical mechanism the invention addresses."),
 # GEN ELECTRIC US2366071A (Stationary induction apparatus)
 "D393": ("mixed", "method_or_tool", "high", "A copending application and an article are cited together as describing a suitable method of applying the strip material to the winding leg, a technique used with the invention."),
 # ---- electrical/electronics 1950s (bigquery draw, see docstring) ----
 # BELL TELEPHONE LABOR INC US2556286A (Oscillation generator)
 "D394": ("paper", "method_or_tool", "medium", "The Peterson article supplies the equivalent four-pole representation that the patent adopts to describe the transistor's alternating-current characteristics, a modelling technique used rather than a finding exploited."),
 # BELL TELEPHONE LABOR INC US2763832A (Semiconductor circuit controlling device)
 "D395": ("paper", "foundation", "medium", "Shockley's paper is cited for the physical finding that NPN or PNP bodies exhibit current multiplication (alpha near unity), a mechanism the semiconductor device of the invention relies on."),
 # GEN ELECTRIC US2859360A (Wave generator)
 "D396": ("book", "prior_art_distinguished", "high", "The saw-tooth generator in Shea's book is the earlier circuit whose wave shape is said to deviate considerably from the linear ideal, the problem the invention addresses."),
 # IBM US2761965A (Electronic circuits)
 "D397": ("paper", "background_context", "high", "The papers are cited for the history of the transistor, framing the field without being relied on or distinguished."),
 "D398": ("paper", "incorporated_reference_list", "low", "The window is a bare reference entry ending in a semicolon with no surrounding text stating a role."),
 # IBM US2884625A (Code generator)
 "D399": ("mixed", "background_context", "medium", "The Hamming paper and reissue patent are cited to describe the existing state of error-detecting codes without the text stating that the invention uses or departs from them."),
 "D400": ("patent", "method_or_tool", "high", "The flip-flops are preferably of the type shown in the copending application, so it supplies a circuit component used in the invention."),
 # ---- electrical/electronics 1960s (bigquery draw, see docstring) ----
 # GEN ELECTRIC US3436582A (Plasma separator ion engine)
 "D401": ("paper", "background_context", "high", "The paper is offered as a convenient general reference to the voluminous literature, a literature overview."),
 # IBM US2989733A (Ferroelectric circuit element)
 "D402": ("paper", "foundation", "medium", "The article is cited for the physical effect of clamping on the crystal transitions, a finding the invention's electrode-area design exploits."),
 # IBM US3471396A (R.f. cathodic sputtering apparatus having an electrically co)
 "D403": ("paper", "background_context", "medium", "The paper is cited as generally disclosing radio frequency sputtering of dielectrics, a general description of the technique that frames the invention."),
 # TEXAS INSTRUMENTS INC US3471802A (Modulated laser using a solid fabry-perot etalon having a bi)
 "D404": ("paper", "background_context", "high", "The articles are cited as examples describing basic laser operation and theory, background that the text says needs only brief treatment."),
 "D405": ("paper", "method_or_tool", "medium", "The article describes the available electro-optic switches that can be employed as the in-cavity switch in the system of the invention."),
 # TEXAS INSTRUMENTS INC US3475700A (Monolithic microwave duplexer switch)
 "D406": ("paper", "foundation", "medium", "The reported properties of microstrip lines on semiconductor dielectrics are the basis for choosing line width to obtain the desired characteristic impedance."),
 # ---- electrical/electronics 1970s (bigquery draw, see docstring) ----
 # BELL TELEPHONE LABOR INC US3488606A (Unidirectional ring laser)
 "D407": ("paper", "foundation", "medium", "The patent states 'as shown by' Kogelnik the beam-waist imaging relation that the resonator design is built on, i.e. a physical result the invention rests on rather than a procedure it performs."),
 # BELL TELEPHONE LABOR INC US3539939A (Laser pulse generator using a rotating prism alternately as )
 "D408": ("paper", "foundation", "medium", "The opening paragraph presents the mode-locking arrangement of the cited article as the mechanism that produces the intracavity high-intensity pulse on which the pulse generator of the invention is based; the window is truncated before any contrast is drawn, so confidence is medium."),
 "D409": ("paper", "background_context", "high", "The citation is a parenthetical 'for a more detailed discussion of the gas laser see' pointer, giving general background on lasers rather than anything the invention relies on or distinguishes."),
 "D410": ("paper", "method_or_tool", "high", "The motor driving the prism 'can be of the type used by J. W. Beams' as illustrated in the cited article, so the paper supplies an apparatus design the invention adopts as a component."),
 # GEN ELECTRIC US3609719A (First order transition recording utilizing incomplete transi)
 "D411": ("paper", "method_or_tool", "high", "The recorded information is read out using the electron mirror microscopy or scanning electron microscope techniques described in the cited articles, so they supply a technique the invention uses."),
 # IBM US3576436A (Method and apparatus for adding or subtracting in an associa)
 "D412": ("paper", "prior_art_distinguished", "high", "Both cited articles describe earlier approaches and the text states that 'the problem with both of the approaches in the referenced articles is that they are relatively inefficient'."),
 # IBM US3699482A (Surface waveguiding in ceramics by selective poling)
 "D413": ("paper", "background_context", "high", "The article is cited as a thorough presentation of the history and state of the art of surface wave technology, i.e., a literature overview framing the field."),
 "D414": ("paper", "incorporated_reference_list", "low", "The window is a numbered bibliographic entry from a reference list with no stated role visible."),
 "D415": ("paper", "incorporated_reference_list", "low", "The window is a numbered bibliographic entry from a reference list with no stated role visible."),
 # ---- electrical/electronics 2020s (bigquery draw, see docstring) ----
 # GEN ELECTRIC US12384727B2 (Composite components and methods for preventing flow from in)
 "D416": ("paper", "method_or_tool", "high", "The permeability was measured through a capillary weight-gain procedure similar to the one reported in the cited article, so the paper supplies a measurement technique the invention uses."),
 # IBM US11288425B1 (Path-based timing driven placement using iterative pseudo ne)
 "D417": ("paper", "method_or_tool", "medium", "The papers are listed as net weighting techniques that can be applied to produce the weights shared with the placer, i.e., algorithms the invention may use (sentence start truncated)."),
 # IBM US11562240B2 (Efficient tile mapping for row-by-row convolutional neural n)
 "D418": ("paper", "background_context", "high", "The tutorial is cited for 'additional details of ANNs and learning rules', a for-more-information pointer rather than a technique relied on or distinguished."),
 # TEXAS INSTRUMENTS INC US11899082B2 (Silicon hall sensor with low offset and drift compensation c)
 "D419": ("paper", "background_context", "high", "The papers are explicitly introduced with 'For general background, see', while the co-pending application separately carries the implementation details."),
 # TEXAS INSTRUMENTS INC US12382658B2 (Reducing transistor breakdown in a power FET current sense s)
 "D420": ("paper", "foundation", "medium", "The paper supplies the BVceo-versus-base-emitter-voltage characteristics of FIG. 6 that the invention relies on to explain the behaviour of its parasitic NPN transistor."),
}

SCIENCE_TYPES = {"paper", "mixed", "standards_doc", "book", "software_or_database"}
SECTORS = ["pharma", "chemicals", "electrical/electronics"]
DECADES = ["1900s", "1910s", "1920s", "1930s", "1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]


MOJIBAKE = re.compile(r"[Â-ô][-¿]+")


def fix_text(s):
    """The fetch run decoded UTF-8 pages as Latin-1; undo that run by run (the inserted ellipsis is left alone)."""
    return MOJIBAKE.sub(lambda m: m.group().encode("latin-1").decode("utf-8", errors="replace"), s)


def main():
    raw = [json.loads(l) for l in open(DATA / "0_raw" / "decades" / "citation_windows_raw.jsonl", encoding="utf-8")]
    assert len(raw) == len(L), (len(raw), len(L)); assert all(r["window_id"] in L for r in raw)
    out = []
    for r in raw:
        dt, fn, conf, note = L[r["window_id"]]
        assert fn in FUNCTIONS, fn
        r2 = dict(r); r2["text"] = fix_text(r["text"]) if r.get("draw") == "et al" else r["text"]  # the first Google draw was mis-decoded
        r2.update({"cited_doc_type": dt, "function": fn, "confidence": conf, "note": note,
                   "cited_work_string": first_citation(r2["text"]),
                   "is_family_duplicate": bool(r.get("is_family_duplicate")) or "Duplicate of" in note})
        out.append(r2)
    with open(dpath("2_label", "decades", "citation_windows_labeled.jsonl"), "w", encoding="utf-8") as f:
        for r in out: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    uniq = [r for r in out if not r["is_family_duplicate"]]
    sci = [r for r in uniq if r["cited_doc_type"] in SCIENCE_TYPES]
    cell = collections.defaultdict(collections.Counter); cell_pat = collections.defaultdict(set)
    for r in sci:
        cell[(r["sector"], r["decade"])][r["function"]] += 1; cell_pat[(r["sector"], r["decade"])].add(r["pn"])
    c_dt = collections.Counter(r["cited_doc_type"] for r in uniq)
    lines = ["# Decade sample: how firms in three sectors used science, 1900s-2020s", "",
             f"- {len({r['pn'] for r in out})} granted US patents of {len({r['query_assignee'] for r in out})} firms, {len(out)} citation windows; {len(uniq)} after dropping sibling duplicates; {len(sci)} cite papers, books, standards documents or mixed sets (the rest cite patents only). Core cells 1980s-2010s: nine firms, Google Patents draws; extension cells 1900s-1970s and 2020s: the Reliance on Science frame on BigQuery (docstring).",
             "- Cited document type (de-duplicated): " + ", ".join(f"{k} {v}" for k, v in c_dt.most_common()) + ".",
             "", "## Function of science citations by sector and decade (windows; patents in parentheses)", "",
             "| Sector | Decade | n | " + " | ".join(FUNCTIONS) + " |", "|---|---|---|" + "---|" * len(FUNCTIONS)]
    for s in SECTORS:
        for d in DECADES:
            c = cell[(s, d)]; n = sum(c.values())
            lines.append(f"| {s} | {d} | {n} ({len(cell_pat[(s, d)])}) | " + " | ".join(str(c.get(f, 0)) for f in FUNCTIONS) + " |")
    lines += ["", "Shares with counts: `profiles_sector_decade.csv`, `profiles_sector.csv`, `profiles_decade.csv` (from `../../aggregate.py`).",
              "Labels and rationales: `citation_windows_labeled.jsonl` (`note` field). Sampling: module docstring of `labels_decades.py`."]
    dpath("4_aggregate", "decades", "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
