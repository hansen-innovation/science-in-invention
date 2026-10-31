"""Labels for the decade sample: 195 citation windows from 72 patents of nine firms in three sectors
(pharma: Pfizer, Eli Lilly, Bristol-Myers; chemicals: Dow Chemical, Du Pont, Air Products;
electrical/electronics: IBM, General Electric, Texas Instruments), two patents per firm per decade
(priority and grant in the 1980s, 1990s, 2000s, 2010s), up to three windows per patent.

Fetched on Oct 31, 2026 with ../../fetch_patents.py (Google Patents; the first two granted US patents per
firm and decade in Google's ranking that contain "et al"). Labels were produced the same day by
claude-fable-5-1 in an interactive session with ../../prompts/label_citation_function.md; each entry is
window_id -> (cited_doc_type, function, confidence, note). Run `python labels_decades.py` to write
citation_windows_labeled.jsonl and summary.md. No second coder has labeled this set.
"""
import collections, json, pathlib, re, sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
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
}

SCIENCE_TYPES = {"paper", "mixed", "standards_doc", "book", "software_or_database"}
SECTORS = ["pharma", "chemicals", "electrical/electronics"]
DECADES = ["1980s", "1990s", "2000s", "2010s"]


MOJIBAKE = re.compile(r"[Â-ô][-¿]+")


def fix_text(s):
    """The fetch run decoded UTF-8 pages as Latin-1; undo that run by run (the inserted ellipsis is left alone)."""
    return MOJIBAKE.sub(lambda m: m.group().encode("latin-1").decode("utf-8", errors="replace"), s)


def main():
    raw = [json.loads(l) for l in open(HERE / "citation_windows_raw.jsonl", encoding="utf-8")]
    assert len(raw) == len(L), (len(raw), len(L)); assert all(r["window_id"] in L for r in raw)
    out = []
    for r in raw:
        dt, fn, conf, note = L[r["window_id"]]
        assert fn in FUNCTIONS, fn
        r2 = dict(r); r2["text"] = fix_text(r["text"])
        r2.update({"cited_doc_type": dt, "function": fn, "confidence": conf, "note": note,
                   "cited_work_string": first_citation(r2["text"]),
                   "is_family_duplicate": bool(r.get("is_family_duplicate")) or "Duplicate of" in note})
        out.append(r2)
    with open(HERE / "citation_windows_labeled.jsonl", "w", encoding="utf-8") as f:
        for r in out: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    uniq = [r for r in out if not r["is_family_duplicate"]]
    sci = [r for r in uniq if r["cited_doc_type"] in SCIENCE_TYPES]
    cell = collections.defaultdict(collections.Counter); cell_pat = collections.defaultdict(set)
    for r in sci:
        cell[(r["sector"], r["decade"])][r["function"]] += 1; cell_pat[(r["sector"], r["decade"])].add(r["pn"])
    c_dt = collections.Counter(r["cited_doc_type"] for r in uniq)
    lines = ["# Decade sample: how nine firms in three sectors used science, 1980s-2010s", "",
             f"- {len({r['pn'] for r in out})} granted US patents of nine firms, {len(out)} citation windows; {len(uniq)} after dropping sibling duplicates; {len(sci)} cite papers, books, standards documents or mixed sets (the rest cite patents only).",
             "- Cited document type (de-duplicated): " + ", ".join(f"{k} {v}" for k, v in c_dt.most_common()) + ".",
             "", "## Function of science citations by sector and decade (windows; patents in parentheses)", "",
             "| Sector | Decade | n | " + " | ".join(FUNCTIONS) + " |", "|---|---|---|" + "---|" * len(FUNCTIONS)]
    for s in SECTORS:
        for d in DECADES:
            c = cell[(s, d)]; n = sum(c.values())
            lines.append(f"| {s} | {d} | {n} ({len(cell_pat[(s, d)])}) | " + " | ".join(str(c.get(f, 0)) for f in FUNCTIONS) + " |")
    lines += ["", "Shares with counts: `profiles_sector_decade.csv`, `profiles_sector.csv`, `profiles_decade.csv` (from `../../aggregate.py`).",
              "Labels and rationales: `citation_windows_labeled.jsonl` (`note` field). Sampling: module docstring of `labels_decades.py`."]
    (HERE / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
