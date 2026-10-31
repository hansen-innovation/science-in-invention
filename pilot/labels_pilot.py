"""Pilot labels for the 118 citation windows in citation_windows_raw.jsonl.

Labels were produced on Oct 27, 2026 by running prompts/label_citation_function.md
interactively through Claude (claude-fable-5-1) on each window; label_llm.py
reproduces the same call through the API. Each entry: window_id -> (cited_doc_type,
function, confidence, note).  Run `python labels_pilot.py` to write
citation_windows_labeled.jsonl and summary.md.
"""
import json, re, collections, pathlib

HERE = pathlib.Path(__file__).parent
L = {
 # Genentech US11077189B2 / US10849849B2 (same family text, duplicated)
 "W001": ("mixed", "foundation", "medium", "Baselga 1996 clinical activity of trastuzumab is the clinical basis of the adjuvant regimen; also cites US 5,821,337"),
 "W002": ("paper", "background_context", "high", "Slamon 2001, Marty 2005: standard of care; sets the clinical context"),
 "W003": ("patent", "method_or_tool", "medium", "WO/US publications on IHC/FISH used to select patients; 'et al.' here names patent applicants, not a paper"),
 "W004": ("mixed", "foundation", "medium", "Duplicate of W001 (same family); dedupe at family level"),
 "W005": ("paper", "background_context", "high", "Duplicate of W002"),
 "W006": ("patent", "method_or_tool", "medium", "Duplicate of W003"),
 # Regeneron
 "W007": ("paper", "foundation", "medium", "Wang 2007: known C-terminal cleavage supports the claimed sequence variants"),
 "W008": ("paper", "foundation", "high", "Bolton 2011: Gibbs-Donnan effect is the phenomenon the formulation process must correct for"),
 "W009": ("mixed", "definitional_boilerplate", "high", "Defines 'microinfusor' via US patents and Meehan 1996"),
 "W010": ("mixed", "data_or_materials_source", "high", "Cell lines (CHO DG44, DHFR-) sourced via Chasin 1986, Urlaub 1980, ATCC"),
 "W011": ("paper", "method_or_tool", "high", "Switzar 2013 review of protein digestion techniques used in the process"),
 "W012": ("paper", "method_or_tool", "medium", "Ghaderi 2012 review of production platforms"),
 # Moderna Enzymatics (Japanese firm, fuzzy assignee match)
 "W013": ("paper", "foundation", "high", "Tus-ter replication termination mechanism 'utilized' by the method"),
 "W014": ("paper", "foundation", "high", "XerCD multimer resolution mechanism utilized by the method"),
 "W015": ("software_or_database", "method_or_tool", "high", "BLAST (Altschul 1990) for sequence identity; biotech boilerplate"),
 # Pfizer
 "W016": ("paper", "foundation", "high", "Hsu/Yang/Emmerson 2017: GDF15-GFRAL receptor biology underpins the antibody"),
 "W017": ("paper", "foundation", "medium", "PD-L1 biology for the combination claims"),
 "W018": ("paper", "background_context", "medium", "Ribas 2018: landscape of approved PD-1 antagonists"),
 "W019": ("mixed", "foundation", "high", "TGFb inhibition rationale (Gorelik 2001, Tauriello 2018, Mariathasan 2018) plus US 10,167,334"),
 "W020": ("paper", "foundation", "high", "Prior studies on TGFb and immunotherapy response"),
 "W021": ("paper", "foundation", "high", "Itgb8 knockout biology (Travis 2007, Melton 2010) motivates targeting alpha-v-beta-8"),
 # IBM
 "W022": ("patent", "prior_art_distinguished", "high", "Carlen et al. US 9,645,811 discussed as prior approach"),
 "W023": ("paper", "background_context", "medium", "Goodfellow ICLR 2015 and attack families define the threat the invention defends against"),
 "W024": ("book", "method_or_tool", "medium", "Self-citation to IBM Watson documentation (Redbooks, developerWorks) for the pipeline used"),
 # Nvidia
 "W025": ("paper", "prior_art_distinguished", "medium", "Xiao 2010 barrier synchronization: existing GPU sync mechanisms the invention extends"),
 "W026": ("mixed", "background_context", "medium", "Self-citation to Tesla/Volta IEEE Micro papers, CUDA docs and own patents 'for more information'"),
 "W027": ("book", "background_context", "high", "Foley et al. textbook on rasterization"),
 "W028": ("paper", "background_context", "high", "Ray tracing history (SIGGRAPH 1986; Pixar 2016)"),
 "W029": ("book", "background_context", "medium", "Glassner 1989; Akenine-Moller: ray tracing as embarrassingly parallel"),
 # Microsoft
 "W030": ("paper", "method_or_tool", "high", "Gastal 2011 domain transform filter and Gatys style transfer used as components"),
 "W031": ("paper", "method_or_tool", "high", "Simonyan VGG (arXiv) used as the CNN architecture"),
 # Google (two family members, duplicated)
 "W032": ("paper", "background_context", "medium", "Survey of Bayesian optimization literature (Bergstra, Shahriari, Snoek)"),
 "W033": ("paper", "background_context", "medium", "CMA-ES (Hansen 1996) among classic algorithms"),
 "W034": ("mixed", "background_context", "medium", "Nelder-Mead 1965; Conn 2009 (SIAM book)"),
 "W035": ("paper", "background_context", "medium", "Duplicate of W032 (same family)"),
 "W036": ("paper", "background_context", "medium", "Duplicate of W033"),
 "W037": ("mixed", "background_context", "medium", "Duplicate of W034"),
 # Intel
 "W038": ("paper", "prior_art_distinguished", "high", "Besl 1992 ICP: conventional method whose assumption the invention relaxes"),
 "W039": ("paper", "prior_art_distinguished", "high", "NICP, RPM: known improvements to ICP, categorized"),
 "W040": ("paper", "prior_art_distinguished", "high", "Point-to-plane, GICP, IRLS variants"),
 "W041": ("paper", "prior_art_distinguished", "medium", "R-CNN family as the two-stage detectors the invention improves on"),
 "W042": ("paper", "prior_art_distinguished", "medium", "SqueezeDet as prior lightweight detector"),
 "W043": ("paper", "prior_art_distinguished", "medium", "Xception, MobileNet-SSD, Pelee"),
 # Dow
 "W044": ("patent", "prior_art_distinguished", "high", "US 8,426,519 (Cogen) related prior process"),
 "W045": ("mixed", "prior_art_distinguished", "high", "CN104277182A and Wu RSC Advances 2014 on POSS crosslinking"),
 "W046": ("book", "definitional_boilerplate", "medium", "Stark 1982 cited to define excluded catalyst classes"),
 "W047": ("paper", "method_or_tool", "medium", "Herberich 1995 boratabenzenyl ligands known in the art, used in catalyst"),
 "W048": ("paper", "method_or_tool", "high", "Kaminski 1995, Zambelli 1988, Dias 2002 catalysts that may be used for chain-walking"),
 "W049": ("paper", "incorporated_reference_list", "high", "Long list of organometallic references (Bercaw et al.) without specific use"),
 # 3M
 "W050": ("patent", "background_context", "medium", "WO/US publications describing direct-printed aligners"),
 "W051": ("patent", "method_or_tool", "high", "US patents for processes to prepare urethane (meth)acrylates"),
 "W052": ("patent", "data_or_materials_source", "medium", "EP2167013B1 describes the commercial component DESMA"),
 "W053": ("patent", "data_or_materials_source", "medium", "US patents as examples of sol-gel ceramic particles"),
 "W054": ("patent", "method_or_tool", "high", "US patents for molding processes of shaped particles"),
 "W055": ("patent", "method_or_tool", "medium", "US 8,034,137 shaped-then-crushed particles"),
 # Illumina (two entities, same text)
 "W056": ("mixed", "method_or_tool", "high", "Pearson & Lipman 1988; GCG package; Current Protocols: sequence similarity boilerplate"),
 "W057": ("software_or_database", "method_or_tool", "high", "BLAST (Altschul 1990) boilerplate"),
 "W058": ("paper", "method_or_tool", "high", "Crameri 1998 DNA shuffling as a mutagenesis approach"),
 "W059": ("mixed", "method_or_tool", "high", "Duplicate of W056 (same family)"),
 "W060": ("software_or_database", "method_or_tool", "high", "Duplicate of W057"),
 "W061": ("paper", "method_or_tool", "high", "Duplicate of W058"),
 # Merck
 "W062": ("paper", "foundation", "high", "VGSC biology (Yu 2003, Goldin 1999)"),
 "W063": ("paper", "foundation", "high", "Nav1.8 subunit identification (Goldin 2000)"),
 "W064": ("paper", "foundation", "high", "Catterall 2017 nociception; target rationale"),
 "W065": ("mixed", "background_context", "high", "CDC MMWR and Arditi 1998: disease burden"),
 "W066": ("paper", "background_context", "high", "Serotype coverage limits of Prevnar (unmet need)"),
 "W067": ("mixed", "prior_art_distinguished", "medium", "Prevnar 13 composition and trials: the existing product the invention extends"),
 # BMS
 "W068": ("paper", "foundation", "high", "TLR7 ligand biology (Lund 2004, Berghofer 2007, Zhang 2016)"),
 "W069": ("paper", "prior_art_distinguished", "medium", "Vesatolimod and purine-8-one potency as prior agonists"),
 "W070": ("mixed", "incorporated_reference_list", "high", "Bulk list of prior disclosures of purine-like TLR7 agonists"),
 "W071": ("paper", "background_context", "high", "Dempke 2017 T-cell exhaustion as problem context"),
 "W072": ("paper", "definitional_boilerplate", "high", "Ward 1989 dAb definition"),
 "W073": ("paper", "definitional_boilerplate", "high", "Bird 1988, Huston 1988 scFv definition"),
 # Amgen
 "W074": ("paper", "background_context", "high", "Chi 2003, Roberts 2014: protein instability as the problem addressed"),
 "W075": ("paper", "background_context", "high", "Aggregation conditions; same references"),
 "W076": ("paper", "background_context", "medium", "HMW removal challenge (Chi 2003)"),
 "W077": ("paper", "background_context", "high", "Bang 2010, Fuchs 2014: approved targeted therapies in gastric cancer"),
 "W078": ("paper", "background_context", "high", "Le 2017, Fuchs 2017, Kang 2017: checkpoint therapy approvals"),
 "W079": ("paper", "background_context", "high", "Uccello 2018 pancreatic cancer chemotherapy"),
 # Novartis
 "W080": ("paper", "foundation", "high", "IL2 cloning and structure (Taniguchi 1983, Smith 1988)"),
 "W081": ("paper", "foundation", "high", "IL2 receptor affinity biology (Kreig 2010) exploited by the engineered protein"),
 "W082": ("paper", "background_context", "high", "Coventry 2012 clinical history of rhIL2"),
 "W083": ("paper", "definitional_boilerplate", "high", "Ward 1989 dAb"),
 "W084": ("paper", "definitional_boilerplate", "high", "Bird 1988, Huston 1988 scFv"),
 "W085": ("book", "method_or_tool", "medium", "Singh 2009 Methods in Molecular Biology: linker attachment methods"),
 # Corteva
 "W086": ("paper", "background_context", "high", "Rivero; Gubler: vector-borne disease burden (citations lack years)"),
 "W087": ("paper", "background_context", "high", "Nicol et al.: nematode losses"),
 "W088": ("paper", "background_context", "high", "Sparks et al.: GPA resistance"),
 "W089": ("patent", "method_or_tool", "high", "US 9,637,505 synthesis procedures incorporated by reference"),
 "W090": ("book", "definitional_boilerplate", "high", "McCutcheon's; Encyclopedia of Surfactants: formulation lists"),
 "W091": ("paper", "method_or_tool", "high", "Das 2017 Org. Lett. literature procedure followed to make the compound"),
 # Qualcomm (JVET standards contributions)
 "W092": ("standards_doc", "prior_art_distinguished", "high", "JVET-Y0125 prior proposal; invention changes OOB handling"),
 "W093": ("standards_doc", "method_or_tool", "high", "JVET-O0066 LIC 'may be used ... with the following modifications'"),
 "W094": ("standards_doc", "method_or_tool", "high", "JVET-L0399 non-adjacent merge candidates used as described"),
 "W095": ("standards_doc", "prior_art_distinguished", "medium", "JVET-P0426 proposed signaling; invention differs"),
 "W096": ("standards_doc", "background_context", "high", "VVC Draft 6 as the standard context"),
 "W097": ("standards_doc", "method_or_tool", "medium", "JVET-O0105/O0543 joint chroma residual techniques built on"),
 # Samsung
 "W098": ("paper", "method_or_tool", "high", "Asano ICLR 2020 self-labelling used for clustering"),
 "W099": ("paper", "method_or_tool", "high", "'The method described in this application typically follows this latter approach'"),
 "W100": ("paper", "method_or_tool", "high", "MoCo (He 2019), SwAV (Caron 2020) implementation details"),
 "W101": ("paper", "background_context", "high", "LDA literature review (Blei 2003 and extensions)"),
 "W102": ("paper", "background_context", "high", "Aspect-based sentiment literature"),
 "W103": ("paper", "prior_art_distinguished", "medium", "JST, ASUM, USTM, Tutubalina-Nikolenko as related-art models"),
 # Medtronic
 "W104": ("patent", "method_or_tool", "medium", "Imaging systems in US publications 'may be used in conjunction'"),
 "W105": ("paper", "method_or_tool", "medium", "Sweeney 2010, Van Deursen 2012 activation indicators described in"),
 "W106": ("patent", "method_or_tool", "medium", "Own prior US publications (Ghosh et al.) incorporated; self-citation"),
 # Boston Scientific / Scimed
 "W107": ("paper", "data_or_materials_source", "medium", "Kennedy PLoS One 2014 lists substances usable as charged molecules"),
 "W108": ("paper", "foundation", "high", "Kennedy 2014 cellular result summarized in FIG. 8 as the mechanism"),
 "W109": ("paper", "prior_art_distinguished", "high", "Kennedy's spatial management judged impractical in vivo; invention differs"),
 # ExxonMobil
 "W110": ("paper", "background_context", "high", "Chu 2009, Haszeldine 2009, Lackner 2012: CCS motivation"),
 "W111": ("paper", "background_context", "medium", "Cabal 2009 regeneration methods overview"),
 "W112": ("paper", "background_context", "medium", "Shah 2013 criteria for regeneration"),
 "W113": ("paper", "prior_art_distinguished", "high", "Prestack 4D inversion schemes (Tura 1999 ...) called ill-conditioned (Nicolao 1993)"),
 "W114": ("paper", "prior_art_distinguished", "high", "Statistical calibration methods (Floricich 2005 ...) and their data requirements"),
 "W115": ("paper", "prior_art_distinguished", "high", "Time-shift inversion approaches (Rickett 2007, Williamson 2007)"),
 # Honeywell
 "W116": ("patent", "own_family_continuation", "high", "Continuation of the applicant's own application; not a science citation"),
 "W117": ("patent", "prior_art_distinguished", "high", "US 7,196,236 (Mukhopadhyay) prior catalytic process"),
 "W118": ("patent", "prior_art_distinguished", "high", "US 7,132,578: prior process using unstable IF"),
 # ---- batch 2 (Oct 27, 2026): 70 more patents from 30 assignee queries ----
 "W119": ("paper", "background_context", "high", "IBD epidemiology (Loftus 2004; Probert 1996)"),
 "W120": ("paper", "background_context", "high", "Norwegian cohort on Crohn's disease course"),
 "W121": ("paper", "background_context", "high", "Molodecky 2012 incidence and prevalence"),
 "W122": ("paper", "foundation", "high", "p40/p19-deficient mice protected (Hue 2006; Hong 1999): target biology"),
 "W123": ("paper", "foundation", "medium", "Liang 2013 Jak2/Tyk2; Jak2 toxicity rationale for selective Tyk2 inhibition"),
 "W124": ("book", "definitional_boilerplate", "high", "Organic chemistry textbooks cited for general principles"),
 "W125": ("book", "background_context", "medium", "Shearer 2017 GeneReviews: prevalence of hereditary hearing loss"),
 "W126": ("mixed", "background_context", "medium", "GeneReviews DFNB1; Kemperman 2002"),
 "W127": ("book", "definitional_boilerplate", "high", "Dictionaries cited for term definitions"),
 "W128": ("paper", "foundation", "high", "CD73-adenosine pathway (Zhang 2010; Antonioli 2017)"),
 "W129": ("paper", "foundation", "high", "Stagg 2011 CD73-deficient mice"),
 "W130": ("paper", "foundation", "high", "Jin 2010; Beavis 2012, 2015; Loi 2013"),
 "W131": ("book", "method_or_tool", "high", "Sambrook; Current Protocols; Methods in Enzymology (standard-methods boilerplate)"),
 "W132": ("mixed", "method_or_tool", "high", "Kohler-Milstein (Nature 256:495), US 4,816,567, McCafferty 1990 phage display"),
 "W133": ("book", "definitional_boilerplate", "high", "Kabat 1991 CDR numbering"),
 "W134": ("paper", "prior_art_distinguished", "high", "Prior HBV therapeutic vaccination attempts (Dikici 2003 ...)"),
 "W135": ("paper", "prior_art_distinguished", "medium", "Swadling 2016 criteria; prior vaccines did not meet them"),
 "W136": ("mixed", "background_context", "medium", "Arenavirus taxonomy (Buchmeier 2001; Radoshitzky 2015) for vector selection"),
 "W137": ("paper", "background_context", "high", "Champiat 2018 early-mortality phenomenon with ICIs (the problem)"),
 "W138": ("book", "definitional_boilerplate", "high", "Dictionaries cited for term definitions"),
 "W139": ("paper", "background_context", "high", "Garon 2019 5-year OS; Borghaei"),
 "W140": ("paper", "foundation", "high", "Chipuk 2010; Yip: BCL-2 family biology"),
 "W141": ("paper", "foundation", "high", "Chipuk, Yip (infra): anti-apoptotic mechanism targeted"),
 "W142": ("mixed", "definitional_boilerplate", "high", "Remington's; Berge 1977; Stahl & Wermuth: pharmaceutical salts"),
 "W143": ("paper", "background_context", "high", "YOLO, SSD, Mask R-CNN as state of the art in 2D detection"),
 "W144": ("paper", "prior_art_distinguished", "medium", "Mercier 2019: synthetic-data approaches have a domain gap"),
 "W145": ("paper", "prior_art_distinguished", "high", "Chen 2016/2017: approaches restricted to yaw-only 3D boxes"),
 "W146": ("paper", "foundation", "high", "Ceder 2015 bcc anion sublattice of Li-ion conductors"),
 "W147": ("paper", "foundation", "high", "Nature Materials 2015 lattice matching used as screening criterion"),
 "W148": ("paper", "method_or_tool", "high", "Hautier 2011 ionic-substitution probability model used to pick dopants"),
 "W149": ("paper", "method_or_tool", "high", "PSPNet, FCN, SegNet as example segmentation techniques used"),
 "W150": ("paper", "method_or_tool", "high", "Structure-from-motion techniques (Crandall 2013; Nilosek)"),
 "W151": ("paper", "method_or_tool", "high", "Point-cloud filtering (Mitra 2004; Han 2017)"),
 "W152": ("patent", "method_or_tool", "high", "US 8,232,533 photoluminescent structure construction, incorporated"),
 "W153": ("patent", "method_or_tool", "high", "US 8,163,201 short-persistence materials"),
 "W154": ("patent", "method_or_tool", "high", "US 8,163,201 long-persistence materials"),
 "W155": ("patent", "background_context", "medium", "Prior Boeing stringer-manufacturing patents incorporated"),
 "W156": ("paper", "foundation", "high", "Stevens 1998; Hodgson: photocatalytic oxidation removes VOCs"),
 "W157": ("paper", "foundation", "high", "AlScN properties (Caro 2015; Moram 2014; Deng)"),
 "W158": ("paper", "foundation", "high", "Moram 2014: wurtzite structure below 40-50% Sc"),
 "W159": ("paper", "method_or_tool", "high", "Guo 2012 ohmic regrowth process used"),
 "W160": ("paper", "prior_art_distinguished", "high", "Meneghini 2017; Greco 2018 p-GaN gate HEMTs"),
 "W161": ("paper", "foundation", "high", "Lee 2006: Be-doped GaN is insulating"),
 "W162": ("paper", "prior_art_distinguished", "high", "'in spite of the teaching of Meneghini et al. and Greco et al.'"),
 "W163": ("paper", "foundation", "medium", "Kumar 2007 etch selectivity reported, relied on for the design"),
 "W164": ("patent", "own_family_continuation", "high", "Continuation of own application"),
 "W165": ("patent", "method_or_tool", "high", "Own depth-mapping patents (Freedman, Pesach, Shpunt) incorporated"),
 "W166": ("patent", "method_or_tool", "high", "Own application (Gernoth) for pose assessment"),
 "W167": ("paper", "method_or_tool", "high", "GPT-2 (Radford 2019) as the language model"),
 "W168": ("paper", "method_or_tool", "high", "RoBERTa (Liu 2019) as the classifier"),
 "W169": ("paper", "method_or_tool", "high", "Byte-pair encoding (Sennrich 2016)"),
 "W170": ("paper", "method_or_tool", "medium", "3D morphable models (Egger 2020; Li 2017 FLAME)"),
 "W171": ("paper", "method_or_tool", "high", "Deferred neural rendering (Thies 2019)"),
 "W172": ("paper", "method_or_tool", "medium", "SMPL-X (Pavlakos 2019); FLAME"),
 "W173": ("paper", "prior_art_distinguished", "medium", "Existing QA tasks (Bordes 2015; Rajpurkar 2018) vs the new task introduced"),
 "W174": ("paper", "prior_art_distinguished", "high", "Jiang 2018 limited by lack of a dataset"),
 "W175": ("paper", "method_or_tool", "high", "Bi-LSTM (Conneau 2017); GloVe (Pennington 2014)"),
 "W176": ("paper", "background_context", "medium", "Chen 2018 on engagement in dialog systems"),
 "W177": ("software_or_database", "method_or_tool", "high", "ParlAI (Miller 2017) used to collect the dataset"),
 "W178": ("paper", "method_or_tool", "high", "TransE KG embeddings (Bordes 2013)"),
 "W179": ("paper", "background_context", "medium", "Burns 2013: additives shown to increase cycle life"),
 "W180": ("paper", "method_or_tool", "high", "UHPC procedure (Bond 2013) incorporated"),
 "W181": ("paper", "method_or_tool", "high", "Parasitic heat-flow procedures (Downie 2014; Glazier 2017)"),
 "W183": ("paper", "prior_art_distinguished", "high", "Glocker 2012 two-stage vertebra localization"),
 "W184": ("paper", "prior_art_distinguished", "high", "Benchmark settings of Glocker, Chen, Suzani"),
 "W185": ("paper", "prior_art_distinguished", "high", "Results table vs Glocker, Suzani, Chen"),
 "W186": ("paper", "method_or_tool", "high", "Yuan 2010a max-flow segmentation used"),
 "W187": ("paper", "method_or_tool", "high", "Cost terms designed following Han 2020b"),
 "W188": ("paper", "method_or_tool", "high", "Parameters chosen based on Han 2020b"),
 "W189": ("patent", "method_or_tool", "medium", "SCR catalyst compositions in US 4,961,917 and 5,516,497"),
 "W190": ("mixed", "method_or_tool", "medium", "Zeolite syntheses (Breck 1973; Barrer 1956; patents)"),
 "W191": ("patent", "method_or_tool", "high", "SAPO-34 / SAPO-44 synthesis patents"),
 "W192": ("paper", "foundation", "high", "PPO enzyme function (Matringe 1989; Duke 1991)"),
 "W193": ("paper", "foundation", "high", "Lee 1993 mechanism of herbicidal cell death"),
 "W194": ("paper", "foundation", "high", "Herbicide-resistant PPO enzymes (Sasarmen 1993; Dailey 1994; Kataoka 1990)"),
 "W195": ("paper", "background_context", "high", "B. subtilis as production host (Van Dijl 2013 ...)"),
 "W196": ("paper", "method_or_tool", "high", "Ferrari 1989 transformation methods (boilerplate)"),
 "W197": ("paper", "method_or_tool", "high", "Ferrari 1989 again (repeat within the same patent)"),
 "W201": ("mixed", "method_or_tool", "high", "SSLP, RAPD, AFLP techniques (Williams 1990; EP) for variety identification (boilerplate)"),
 "W202": ("book", "definitional_boilerplate", "high", "Breeding textbooks (Poehlman 1995; Fehr 1987) define backcrossing"),
 "W203": ("mixed", "method_or_tool", "high", "Transformation methods (US patents; Omirulleh 1993) (boilerplate)"),
 "W204": ("mixed", "method_or_tool", "high", "Duplicate of W201 (sibling variety patent US9924694)"),
 "W205": ("book", "definitional_boilerplate", "high", "Duplicate of W202 (sibling variety patent)"),
 "W206": ("mixed", "method_or_tool", "high", "Duplicate of W203 (sibling variety patent)"),
 "W207": ("mixed", "method_or_tool", "high", "EDC activation (Chen & Benoiton 1979); acrylamide preparation references"),
 "W208": ("mixed", "method_or_tool", "medium", "Gene transfer to plants (Potrykus & Spangenberg 1995; Christou 1996)"),
 "W209": ("book", "method_or_tool", "high", "Sambrook 1989; Winnacker: cloning methods (boilerplate)"),
 "W210": ("mixed", "method_or_tool", "high", "Duplicate of W207 (same family US11613522)"),
 "W211": ("mixed", "method_or_tool", "medium", "Duplicate of W208"),
 "W212": ("book", "method_or_tool", "high", "Duplicate of W209"),
 "W213": ("paper", "background_context", "high", "Kawamura 1999 review; Gahan 2008 (founders' prior work)"),
 "W214": ("paper", "foundation", "high", "Talley 2017 field sagging in grid holes"),
 "W215": ("patent", "prior_art_distinguished", "high", "Mahoney WO 2005/017937 dual-Langmuir probes"),
 "W216": ("patent", "method_or_tool", "high", "Own plasma-reactor publications (Todorow; Banna) that may be modified"),
 "W217": ("patent", "background_context", "medium", "Own ADC publications (Shi; El-Chammas; Nagarajan; Naru)"),
 "W218": ("patent", "method_or_tool", "high", "Own delay-based ADC applications incorporated"),
 "W219": ("paper", "background_context", "medium", "Wu 2019; Perrott 2010 as example phase-detector structures"),
 "W220": ("paper", "method_or_tool", "high", "Phase detectors 'described in more detail in' Perrott 2010"),
 "W221": ("patent", "own_family_continuation", "high", "Divisional chain"),
 "W222": ("patent", "method_or_tool", "high", "Own cross-point memory applications (Castro) for deck building"),
 "W223": ("patent", "own_family_continuation", "high", "Continuation chain"),
 "W224": ("standards_doc", "background_context", "medium", "RFC 5059 BSR as an example announcement protocol"),
 "W225": ("standards_doc", "method_or_tool", "high", "RFC 4601 PIM-SM; RFC 3376 IGMPv3 incorporated"),
 "W226": ("standards_doc", "definitional_boilerplate", "medium", "RFC 2858; RFC 1700 define AFI/SAFI"),
 "W227": ("standards_doc", "method_or_tool", "high", "IETF drafts VXLAN-GPE, group policy"),
 "W228": ("standards_doc", "method_or_tool", "high", "RFC 6830 LISP; LISP mobile node draft"),
 "W229": ("paper", "prior_art_distinguished", "medium", "Kalman-filter and SVR prediction models (Zhang-Jian 2013; Wang 2012; Hu)"),
 "W230": ("paper", "prior_art_distinguished", "high", "Tran 2016 PD-GABP; 'contrary to all historical data, the sliding window ...'"),
 "W231": ("paper", "prior_art_distinguished", "medium", "Repeat of W229 within the same patent"),
 "W232": ("paper", "background_context", "medium", "Seeds 2015 microwave photonics status"),
 "W233": ("paper", "method_or_tool", "medium", "Carpintero 2016 PIC RF generation approaches"),
 "W234": ("paper", "data_or_materials_source", "medium", "Materials for photomixer and antennas (Lin 2009; Chernysheva 2016; Habibpour)"),
 "W235": ("paper", "method_or_tool", "high", "Affinity maturation methods (Marks 1992; Barbas 1994; Schier 1995) (boilerplate)"),
 "W236": ("mixed", "definitional_boilerplate", "high", "DVD-Ig definition (Wu 2007; WO 2001/058956)"),
 "W237": ("paper", "definitional_boilerplate", "high", "Bispecific antibody definition (Milstein 1983; Staerz 1985; Holliger)"),
 "W238": ("paper", "method_or_tool", "high", "Duplicate of W235 (same family US10877038)"),
 "W239": ("mixed", "definitional_boilerplate", "high", "Duplicate of W236"),
 "W240": ("paper", "definitional_boilerplate", "high", "Duplicate of W237"),
 "W241": ("paper", "prior_art_distinguished", "medium", "Peckner 2018 Specter deconvolution as prior attempt"),
 "W242": ("mixed", "method_or_tool", "high", "TMT labelling (WO 01/68664; Thompson 2003)"),
 "W243": ("paper", "foundation", "medium", "Cheung 2020 recommended carrier ratio N~20"),
 "W244": ("patent", "method_or_tool", "high", "Own WO2019/231854 (Senko) CDMS apparatus"),
 "W245": ("patent", "method_or_tool", "high", "'as described in the aforementioned Senko et al. publication'"),
 "W246": ("patent", "own_family_continuation", "high", "Continuation of PCT"),
 "W247": ("patent", "method_or_tool", "high", "Own PCT (Iflah) adjustment mechanism"),
 "W248": ("patent", "own_family_continuation", "high", "Continuation of PCT"),
 "W249": ("patent", "method_or_tool", "high", "Own Zipory publication techniques used mutatis mutandis"),
 "W250": ("patent", "method_or_tool", "high", "Own Zipory publication"),
 "W251": ("patent", "own_family_continuation", "high", "Priority claim chain"),
 "W252": ("patent", "method_or_tool", "medium", "Commonly assigned bed constructions (Lemire; Becker)"),
 "W253": ("patent", "method_or_tool", "high", "Commonly assigned Ethernet patient-support application"),
 "W254": ("paper", "foundation", "medium", "Tachibana 2012: SSD/SAD outperform NCC on greyscale, guides method choice"),
 "W255": ("paper", "foundation", "high", "Hip joint kinematics [6], Apkarian [7]"),
 "W256": ("paper", "background_context", "medium", "DH parameters standard [17]; Wu [18]; Fujie [19]"),
 "W257": ("paper", "method_or_tool", "high", "SPE papers (Dwarakanath 2016; Kim 2018) procedures incorporated; authored by Chevron staff"),
 "W258": ("patent", "method_or_tool", "high", "Own US 2018/0031462 apparatus"),
 "W259": ("patent", "data_or_materials_source", "medium", "Suitable surfactants in own patents"),
 "W260": ("patent", "method_or_tool", "medium", "Benham US 8,372,771 activator variables"),
 "W261": ("paper", "method_or_tool", "high", "Lattice Boltzmann method (Chen 1998; Alpak 2018)"),
 "W262": ("paper", "method_or_tool", "high", "De Kort 2019 flow-MRI pulse sequence"),
 "W263": ("paper", "method_or_tool", "high", "Karlsons 2019 sampling patterns"),
 "W264": ("paper", "background_context", "medium", "Waldeland 2017 deep-learning salt classification; ambiguous between background and adopted method"),
 "W265": ("paper", "method_or_tool", "medium", "CNN-on-cube advantage stated by Waldeland, adopted"),
 "W266": ("paper", "prior_art_distinguished", "medium", "Waldeland acknowledges difficulty; invention selects cubes accordingly"),
 "W267": ("patent", "background_context", "medium", "Co-owned optimization patents (Rashid; Prange)"),
 "W268": ("paper", "method_or_tool", "high", "Inclination correction multiplier modified from Shi et al. [5]"),
 "W269": ("book", "foundation", "medium", "Aziz & Settari 1979 governing physics of reservoir simulation"),
 "W270": ("paper", "method_or_tool", "high", "Isola 2017 cGAN incorporated"),
 "W271": ("paper", "method_or_tool", "high", "Gatys 2015 style transfer"),
 "W272": ("paper", "method_or_tool", "high", "Ronneberger (U-Net); Isola operations"),
 "W273": ("paper", "method_or_tool", "high", "AI Feynman (Udrescu 2020) symbolic regression may be applied"),
 "W274": ("patent", "own_family_continuation", "high", "Continuation-in-part"),
 "W275": ("paper", "method_or_tool", "medium", "Thermodynamic temperature calculation (Bourgeois 2018; Xiao 2016)"),
 "W276": ("paper", "method_or_tool", "high", "Hopcalite preparation comparable to Hutchings 1998"),
 "W277": ("patent", "background_context", "medium", "Own US 8,202,064 (Tian) cavitation adjuster discussed"),
 "W278": ("patent", "method_or_tool", "high", "'A suitable design for inlet valve 18 is known from commonly owned ... Tian et al.'"),
 "W280": ("patent", "data_or_materials_source", "medium", "Barrier films per own US 6,599,597 (Bon)"),
 "W281": ("patent", "data_or_materials_source", "medium", "Plates per own patents (Dupre; Connell)"),
 "W282": ("patent", "background_context", "medium", "Own US 10,505,726 (Andon) cryptographic assets"),
 "W283": ("patent", "background_context", "medium", "Own publication (Andon) geocaching"),
 "W284": ("patent", "method_or_tool", "medium", "Own foot-presence sensing publications (Walker)"),
 "W285": ("patent", "method_or_tool", "high", "Meltblown process US 3,849,241 (Butin) (nonwovens boilerplate)"),
 "W286": ("patent", "method_or_tool", "high", "Spunbond process patents list (nonwovens boilerplate)"),
 "W287": ("patent", "definitional_boilerplate", "high", "Bonded carded webs defined via US 4,488,928"),
 "W288": ("patent", "method_or_tool", "high", "Spunbond filament patents"),
 "W289": ("patent", "method_or_tool", "medium", "Distributor designs (Wilkie; CA2621712)"),
 "W290": ("patent", "method_or_tool", "high", "Melt-spinning systems patents"),
 "W291": ("paper", "foundation", "high", "NGF biology (Smeyne 1994; Crowley 1994; Lindsay 1989)"),
 "W292": ("paper", "foundation", "high", "NGF effects outside the nervous system (Otten 1984, 1989)"),
 "W293": ("paper", "foundation", "high", "NGF-producing cell types (Leon 1994; Torcia 1996 ...)"),
 "W294": ("paper", "background_context", "high", "Olivry 2001 definition of canine atopic dermatitis"),
 "W295": ("paper", "background_context", "high", "Picco 2008 triggers of atopic dermatitis"),
 "W296": ("paper", "background_context", "high", "Prevalence (Marsella & Olivry 2003; Scott 2002; Hillier 2001)"),
}

FUNCTIONS = ["foundation", "method_or_tool", "prior_art_distinguished", "data_or_materials_source",
             "background_context", "definitional_boilerplate", "incorporated_reference_list", "own_family_continuation"]

CITE_RX = re.compile(r"(?:[A-Z][\w'\-]+(?:,? [A-Z]\.)*(?:,? (?:and|&) [A-Z][\w'\-]+)?,? et al\.?[^;)\]]{0,90}"
                     r"|U\.?S\.? ?Pat(?:ent)?\.? ?(?:No\.?|Application|Publication)[^;)\]]{0,60}|WO ?\d{2,4}/\d+[^;)\]]{0,40}"
                     r"|JVET-[A-Z]\d{4}[^;)\]]{0,40}|[A-Z][\w'\-]+ (?:and|&) [A-Z][\w'\-]+,? (?:\(?(?:19|20)\d{2}\)?)[^;)\]]{0,80})")

def first_citation(text):
    m = CITE_RX.search(text)
    return m.group(0).strip() if m else text[:80]


# assignee (as printed on the patent) -> sector; used by the summary and by ../aggregate.py
SECTOR = {"Genentech Inc": "pharma", "Regeneron Pharmaceuticals Inc": "pharma", "Pfizer Inc": "pharma", "Merck Sharp & Dohme LLC": "pharma",
              "Bristol Myers Squibb Co": "pharma", "Amgen Research Munich GmbH": "pharma", "Novartis Institute for Functional Genomics Inc": "pharma", "Novartis AG": "pharma",
              "Moderna Enzymatics Co Ltd": "biotech tools", "Illumina Cambridge Ltd": "biotech tools", "Illumina Singapore Pte Ltd": "biotech tools",
              "International Business Machines Corp": "software/AI", "Microsoft Technology Licensing LLC": "software/AI", "Google LLC": "software/AI", "Samsung Electronics Co Ltd": "software/AI",
              "Nvidia Corp": "semiconductors", "Intel Corp": "semiconductors", "Qualcomm Inc": "semiconductors",
              "Dow Global Technologies LLC": "chemicals/materials", "3M Innovative Properties Co": "chemicals/materials", "Corteva Agriscience LLC": "chemicals/materials", "Honeywell International Inc": "chemicals/materials",
              "Medtronic Inc": "medical devices", "Scimed Life Systems Inc": "medical devices",
              "ExxonMobil Research and Engineering Co": "energy", "ExxonMobil Upstream Research Co": "energy",
              "AbbVie Inc": "pharma", "Eli Lilly and Co": "pharma", "Gilead Sciences Inc": "pharma", "MedImmune LLC": "pharma", "AstraZeneca AB": "pharma", "Zoetis Services LLC": "pharma",
              "Abbott Laboratories": "biotech tools", "Thermo Fisher Scientific Bremen GmbH": "biotech tools", "Danisco US Inc": "biotech tools",
              "Toyota Motor Corp": "automotive/aerospace", "Toyota Motor Engineering and Manufacturing North America Inc": "automotive/aerospace", "Ford Global Technologies LLC": "automotive/aerospace", "Boeing Co": "automotive/aerospace", "Raytheon BBN Technologies Corp": "automotive/aerospace", "Raytheon Co": "automotive/aerospace", "Caterpillar Inc": "automotive/aerospace",
              "Apple Inc": "software/AI", "Amazon Technologies Inc": "software/AI", "Meta Platforms Technologies LLC": "software/AI", "Cisco Technology Inc": "software/AI", "Telefonaktiebolaget LM Ericsson AB": "software/AI",
              "Panasonic Holdings Corp": "semiconductors", "Applied Materials Inc": "semiconductors", "Texas Instruments Inc": "semiconductors", "Micron Technology Inc": "semiconductors", "IMPEDANS Ltd": "semiconductors",
              "Siemens Healthcare GmbH": "medical devices", "Edwards Lifesciences Innovation Israel Ltd": "medical devices", "Stryker Corp": "medical devices", "Stryker Australia Pty Ltd": "medical devices",
              "BASF Corp": "chemicals/materials", "BASF SE": "chemicals/materials", "Monsanto Technology LLC": "chemicals/materials", "Bayer AG": "chemicals/materials", "Air Products and Chemicals Inc": "chemicals/materials", "Kimberly Clark Worldwide Inc": "chemicals/materials", "Nike Inc": "chemicals/materials",
              "Chevron USA Inc": "energy", "Chevron Phillips Chemical Co LP": "energy", "Shell USA Inc": "energy", "Schlumberger Technology Corp": "energy", "Halliburton Energy Services Inc": "energy"}


def main():
    raw = [json.loads(l) for l in open(HERE / "citation_windows_raw.jsonl", encoding="utf-8")]
    assert len(raw) == len(L), (len(raw), len(L)); assert all(r["window_id"] in L for r in raw)
    out = []
    for r in raw:
        dt, fn, conf, note = L[r["window_id"]]
        assert fn in FUNCTIONS
        r2 = dict(r); r2.update({"cited_doc_type": dt, "function": fn, "confidence": conf, "note": note,
                                 "cited_work_string": first_citation(r["text"]),
                                 "is_family_duplicate": "Duplicate of" in note})
        out.append(r2)
    with open(HERE / "citation_windows_labeled.jsonl", "w", encoding="utf-8") as f:
        for r in out: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    # summary
    uniq = [r for r in out if not r["is_family_duplicate"]]
    papers = [r for r in uniq if r["cited_doc_type"] in ("paper", "mixed", "software_or_database", "book", "standards_doc")]
    c_dt = collections.Counter(r["cited_doc_type"] for r in uniq)
    c_fn = collections.Counter(r["function"] for r in uniq)
    c_fn_paper = collections.Counter(r["function"] for r in uniq if r["cited_doc_type"] == "paper")
    sector = SECTOR
    by_sector = collections.defaultdict(collections.Counter)
    for r in uniq: by_sector[sector.get(r["assignee"], "other")][r["function"]] += 1
    lines = ["# Pilot 1 summary: citation function in corporate patents", "",
             f"- Patents: {len({r['pn'] for r in out})} granted US patents from {len({r['assignee'] for r in out})} assignees (priority 2017+; 65 assignee queries in two batches, three of which failed on an ampersand, Oct 26-27), {len(out)} citation windows found by the regex stage; {len(uniq)} after dropping family and sibling duplicates (Genentech, Google, Illumina, Bayer, Abbott and Monsanto variety patents reuse identical text).",
             f"- Cited document type (regex stage catches 'et al.' in patent citations too): " + ", ".join(f"{k} {v}" for k, v in c_dt.most_common()) + ".",
             f"- Function, all windows: " + ", ".join(f"{k} {v}" for k, v in c_fn.most_common()) + ".",
             f"- Function, paper citations only (n={sum(c_fn_paper.values())}): " + ", ".join(f"{k} {v}" for k, v in c_fn_paper.most_common()) + ".",
             "", "## Function by sector (windows, family duplicates removed)", "", "| Sector | " + " | ".join(FUNCTIONS) + " |", "|---|" + "---|" * len(FUNCTIONS)]
    for s, cnt in sorted(by_sector.items()):
        lines.append(f"| {s} | " + " | ".join(str(cnt.get(f, 0)) for f in FUNCTIONS) + " |")
    lines += ["", "## What the pilot shows", "",
              "1. The label set is applicable: every window received exactly one primary function, and the hard cases (one paper playing three roles in Scimed US11045648B2: materials source, mechanism, and distinguished prior art in consecutive paragraphs) are informative rather than ambiguous.",
              "2. Sector signatures are visible: pharma patents cite science as *foundation* (target biology) and *background* (disease burden, standard of care); software/AI and semiconductor patents cite papers as *methods adopted* or *prior art distinguished*; chemicals patents cite *procedures* and *materials*. This is the firm-level 'science-use profile' the full dataset would deliver.",
              f"3. Two filters belong in the pipeline before labeling: (a) a cited-document-type classifier, because 'et al.' also marks patent citations ({sum(1 for r in uniq if r['cited_doc_type'] in ('patent','book','standards_doc'))} of {len(uniq)} de-duplicated windows cite patents, standards contributions or books rather than papers); (b) family de-duplication, because description text is copied verbatim across continuations.",
              "4. Boilerplate is a real category, not noise: antibody-fragment definitions (Ward 1989; Bird 1988; Huston 1988) and BLAST/FASTA citations recur across firms. Counting them as 'science use' would overstate reliance on science in biotech; the label keeps them separable.",
              "5. Citation formats vary enough (author-year, numbered, 'supra', JVET document numbers, citations without years at Corteva) that the window finder should be a lightweight classifier rather than a regex in the full build; the regex here was tuned for recall and accepts noise.",
              "", "Labels: `citation_windows_labeled.jsonl` (one row per window; `note` gives the reason). Prompt: `../prompts/label_citation_function.md`."]
    (HERE / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:6]))

if __name__ == "__main__":
    main()
