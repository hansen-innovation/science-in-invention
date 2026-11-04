# Benchmark results

Generated 2026-11-04 by `3_validate/subagent_batches.py report`.

Each section compares a sample's label file (first coder, the source of truth for that sample) with a blind second coder. The provider in parentheses says how the second coder ran: `claude-code-subagent` coders were Claude Code subagents on batches of 25-30 windows; GPT-6 Astra Pro (reasoning effort max) took batches of 100 windows for the pilot and the first 1,500 long-run windows and 300 for the rest. Every coder had the same guide `2_label/prompts/label_citation_function.md` and `schema.json` and no access to the other coder's labels. Two LLM coders are not a human benchmark; the 2,000-window double-coded human benchmark is still the release criterion.

## pilot/citation_windows_labeled.jsonl

First coder: `claude-fable-5-1 (interactive session; the L dict next to the file)`. Second coder: `claude-opus-5-5` (claude-code-subagent, guide version `276adff408`). 515 of 515 windows coded by both.

### function

```
n=515 accuracy=0.788 kappa=0.726
label                             n_ref   prec    rec
background_context                   86   0.58   0.85
data_or_materials_source             25   0.64   0.64
definitional_boilerplate             42   0.78   0.83
foundation                           69   0.88   0.62
incorporated_reference_list           7   1.00   0.71
method_or_tool                      211   0.93   0.82
own_family_continuation              14   1.00   0.93
prior_art_distinguished              61   0.74   0.79

most common disagreements:
  foundation -> background_context: 20
  method_or_tool -> background_context: 16
  prior_art_distinguished -> background_context: 11
  method_or_tool -> definitional_boilerplate: 9
  background_context -> prior_art_distinguished: 8
  method_or_tool -> data_or_materials_source: 7
  method_or_tool -> prior_art_distinguished: 5
  definitional_boilerplate -> method_or_tool: 5
  data_or_materials_source -> background_context: 4
  foundation -> prior_art_distinguished: 3
  background_context -> method_or_tool: 3
  foundation -> method_or_tool: 3
  data_or_materials_source -> foundation: 3
  definitional_boilerplate -> data_or_materials_source: 1
  incorporated_reference_list -> background_context: 1
  prior_art_distinguished -> foundation: 1
  definitional_boilerplate -> background_context: 1
  prior_art_distinguished -> method_or_tool: 1
  background_context -> data_or_materials_source: 1
  incorporated_reference_list -> definitional_boilerplate: 1
  data_or_materials_source -> method_or_tool: 1
  own_family_continuation -> method_or_tool: 1
  method_or_tool -> foundation: 1
  data_or_materials_source -> prior_art_distinguished: 1
  background_context -> foundation: 1
```

### cited_doc_type

```
n=515 accuracy=0.948 kappa=0.905
label                             n_ref   prec    rec
book                                 27   0.93   0.93
mixed                                51   0.85   0.80
paper                               327   0.97   0.96
patent                               94   0.97   0.99
software_or_database                  4   0.44   1.00
standards_doc                        12   1.00   0.92

most common disagreements:
  mixed -> paper: 8
  paper -> mixed: 6
  paper -> software_or_database: 5
  mixed -> patent: 2
  paper -> book: 2
  book -> patent: 1
  book -> paper: 1
  patent -> paper: 1
  standards_doc -> mixed: 1
```

## pilot/citation_windows_labeled.jsonl

First coder: `claude-fable-5-1 (interactive session; the L dict next to the file)`. Second coder: `gpt-6-astra-pro` (reasoning effort max, batches of 100-300 windows, guide version `276adff408`). 515 of 515 windows coded by both.

### function

```
n=515 accuracy=0.705 kappa=0.619
label                             n_ref   prec    rec
background_context                   86   0.41   0.73
data_or_materials_source             25   0.67   0.72
definitional_boilerplate             42   0.89   0.74
foundation                           69   0.88   0.65
incorporated_reference_list           7   0.83   0.71
method_or_tool                      211   0.90   0.76
own_family_continuation              14   1.00   0.93
prior_art_distinguished              61   0.53   0.44

most common disagreements:
  method_or_tool -> background_context: 36
  prior_art_distinguished -> background_context: 32
  foundation -> background_context: 17
  background_context -> prior_art_distinguished: 15
  definitional_boilerplate -> method_or_tool: 7
  method_or_tool -> data_or_materials_source: 5
  foundation -> prior_art_distinguished: 4
  background_context -> method_or_tool: 4
  method_or_tool -> prior_art_distinguished: 4
  definitional_boilerplate -> data_or_materials_source: 3
  method_or_tool -> definitional_boilerplate: 3
  foundation -> method_or_tool: 3
  incorporated_reference_list -> background_context: 2
  data_or_materials_source -> background_context: 2
  data_or_materials_source -> foundation: 2
  data_or_materials_source -> method_or_tool: 2
  background_context -> foundation: 2
  prior_art_distinguished -> foundation: 1
  background_context -> data_or_materials_source: 1
  definitional_boilerplate -> background_context: 1
  prior_art_distinguished -> method_or_tool: 1
  background_context -> definitional_boilerplate: 1
  own_family_continuation -> method_or_tool: 1
  method_or_tool -> foundation: 1
  data_or_materials_source -> prior_art_distinguished: 1
  method_or_tool -> incorporated_reference_list: 1
```

### cited_doc_type

```
n=515 accuracy=0.926 kappa=0.869
label                             n_ref   prec    rec
book                                 27   0.74   0.93
mixed                                51   0.84   0.75
paper                               327   0.97   0.94
patent                               94   0.96   0.99
software_or_database                  4   0.33   1.00
standards_doc                        12   1.00   0.92

most common disagreements:
  paper -> book: 8
  mixed -> paper: 8
  paper -> software_or_database: 7
  paper -> mixed: 6
  mixed -> patent: 3
  book -> patent: 1
  book -> paper: 1
  mixed -> software_or_database: 1
  mixed -> book: 1
  patent -> paper: 1
  standards_doc -> mixed: 1
```

## decades/citation_windows_labeled.jsonl

First coder: `claude-fable-5-1 (interactive session; the L dict next to the file)`. Second coder: `claude-opus-5-5` (claude-code-subagent, guide version `276adff408`). 420 of 420 windows coded by both.

### function

```
n=420 accuracy=0.826 kappa=0.784
label                             n_ref   prec    rec
background_context                   84   0.69   0.82
data_or_materials_source             18   0.67   1.00
definitional_boilerplate             22   0.86   0.82
foundation                           43   0.76   0.74
incorporated_reference_list          22   0.85   1.00
method_or_tool                      135   0.91   0.85
own_family_continuation              13   1.00   0.77
prior_art_distinguished              83   0.93   0.76

most common disagreements:
  prior_art_distinguished -> background_context: 15
  foundation -> background_context: 9
  background_context -> foundation: 8
  method_or_tool -> data_or_materials_source: 7
  method_or_tool -> background_context: 6
  background_context -> prior_art_distinguished: 4
  method_or_tool -> definitional_boilerplate: 3
  prior_art_distinguished -> method_or_tool: 3
  background_context -> method_or_tool: 3
  method_or_tool -> foundation: 2
  method_or_tool -> incorporated_reference_list: 2
  definitional_boilerplate -> data_or_materials_source: 2
  prior_art_distinguished -> incorporated_reference_list: 2
  own_family_continuation -> method_or_tool: 2
  definitional_boilerplate -> method_or_tool: 2
  foundation -> prior_art_distinguished: 1
  foundation -> method_or_tool: 1
  own_family_continuation -> background_context: 1
```

### cited_doc_type

```
n=420 accuracy=0.962 kappa=0.933
label                             n_ref   prec    rec
book                                 17   0.88   0.88
mixed                                49   0.93   0.80
none                                  2   1.00   1.00
paper                               258   0.96   0.99
patent                               59   1.00   0.98
standards_doc                        35   1.00   1.00

most common disagreements:
  mixed -> paper: 10
  paper -> book: 2
  book -> mixed: 2
  paper -> mixed: 1
  patent -> paper: 1
```

## decades/citation_windows_labeled.jsonl

First coder: `claude-fable-5-1 (interactive session; the L dict next to the file)`. Second coder: `gpt-6-astra-pro` (reasoning effort max, batches of 100-300 windows, guide version `276adff408`). 420 of 420 windows coded by both.

### function

```
n=420 accuracy=0.629 kappa=0.529
label                             n_ref   prec    rec
background_context                   84   0.37   0.70
data_or_materials_source             18   0.60   0.83
definitional_boilerplate             22   0.75   0.41
foundation                           43   0.76   0.67
incorporated_reference_list          22   0.43   0.14
method_or_tool                      135   0.85   0.83
own_family_continuation              13   1.00   0.38
prior_art_distinguished              83   0.80   0.39

most common disagreements:
  prior_art_distinguished -> background_context: 49
  incorporated_reference_list -> background_context: 19
  method_or_tool -> background_context: 13
  foundation -> background_context: 12
  background_context -> foundation: 9
  background_context -> prior_art_distinguished: 6
  definitional_boilerplate -> method_or_tool: 6
  method_or_tool -> data_or_materials_source: 6
  background_context -> method_or_tool: 5
  definitional_boilerplate -> background_context: 4
  own_family_continuation -> background_context: 4
  own_family_continuation -> method_or_tool: 4
  definitional_boilerplate -> data_or_materials_source: 3
  background_context -> definitional_boilerplate: 2
  method_or_tool -> incorporated_reference_list: 2
  prior_art_distinguished -> method_or_tool: 2
  background_context -> incorporated_reference_list: 2
  data_or_materials_source -> method_or_tool: 2
  foundation -> prior_art_distinguished: 1
  method_or_tool -> definitional_boilerplate: 1
  data_or_materials_source -> background_context: 1
  background_context -> data_or_materials_source: 1
  foundation -> method_or_tool: 1
  method_or_tool -> prior_art_distinguished: 1
```

### cited_doc_type

```
n=420 accuracy=0.919 kappa=0.859
label                             n_ref   prec    rec
book                                 17   0.67   0.82
mixed                                49   0.88   0.61
none                                  2   0.50   1.00
paper                               258   0.95   0.97
patent                               59   0.90   0.95
software_or_database                  0   0.00    nan
standards_doc                        35   1.00   0.94

most common disagreements:
  mixed -> paper: 11
  mixed -> patent: 5
  paper -> book: 3
  mixed -> book: 3
  book -> mixed: 2
  paper -> mixed: 2
  patent -> paper: 2
  standards_doc -> none: 2
  patent -> book: 1
  book -> paper: 1
  paper -> software_or_database: 1
  paper -> patent: 1
```

## longrun/citation_windows_labeled.jsonl

First coder: `claude-opus-5-5`. Second coder: `claude-fable-5-1` (claude-code-subagent, guide version `276adff408`). 3017 of 8288 windows coded by both.

### function

```
n=3017 accuracy=0.818 kappa=0.768
label                             n_ref   prec    rec
background_context                  746   0.75   0.79
data_or_materials_source            159   0.87   0.66
definitional_boilerplate            116   0.81   0.69
foundation                          277   0.69   0.86
incorporated_reference_list         154   0.90   0.73
method_or_tool                      995   0.89   0.91
own_family_continuation              35   0.44   0.86
prior_art_distinguished             535   0.88   0.76

most common disagreements:
  prior_art_distinguished -> background_context: 79
  background_context -> foundation: 50
  method_or_tool -> background_context: 38
  background_context -> method_or_tool: 38
  background_context -> own_family_continuation: 36
  foundation -> background_context: 25
  prior_art_distinguished -> foundation: 24
  data_or_materials_source -> method_or_tool: 23
  background_context -> prior_art_distinguished: 20
  incorporated_reference_list -> background_context: 19
  data_or_materials_source -> background_context: 18
  method_or_tool -> foundation: 18
  prior_art_distinguished -> method_or_tool: 17
  incorporated_reference_list -> prior_art_distinguished: 15
  method_or_tool -> prior_art_distinguished: 14
  definitional_boilerplate -> method_or_tool: 12
  definitional_boilerplate -> background_context: 12
  foundation -> method_or_tool: 9
  data_or_materials_source -> foundation: 9
  background_context -> incorporated_reference_list: 7
  incorporated_reference_list -> method_or_tool: 6
  background_context -> definitional_boilerplate: 6
  method_or_tool -> definitional_boilerplate: 5
  definitional_boilerplate -> foundation: 5
  method_or_tool -> data_or_materials_source: 5
  prior_art_distinguished -> definitional_boilerplate: 4
  definitional_boilerplate -> data_or_materials_source: 4
  method_or_tool -> incorporated_reference_list: 3
  foundation -> prior_art_distinguished: 3
  prior_art_distinguished -> data_or_materials_source: 3
  background_context -> data_or_materials_source: 3
  data_or_materials_source -> definitional_boilerplate: 3
  prior_art_distinguished -> incorporated_reference_list: 2
  definitional_boilerplate -> prior_art_distinguished: 2
  own_family_continuation -> method_or_tool: 2
  method_or_tool -> own_family_continuation: 2
  own_family_continuation -> foundation: 1
  incorporated_reference_list -> data_or_materials_source: 1
  foundation -> definitional_boilerplate: 1
  data_or_materials_source -> prior_art_distinguished: 1
  definitional_boilerplate -> incorporated_reference_list: 1
  own_family_continuation -> prior_art_distinguished: 1
  own_family_continuation -> background_context: 1
```

### cited_doc_type

```
n=3017 accuracy=0.952 kappa=0.907
label                             n_ref   prec    rec
book                                194   0.83   0.88
mixed                               291   0.82   0.90
none                                108   0.97   0.97
paper                              2070   0.98   0.96
patent                              221   0.97   0.95
software_or_database                  3   0.67   0.67
standards_doc                       130   0.99   0.99

most common disagreements:
  paper -> mixed: 45
  paper -> book: 25
  mixed -> paper: 18
  book -> paper: 14
  mixed -> book: 9
  book -> mixed: 9
  patent -> paper: 6
  patent -> mixed: 3
  paper -> patent: 3
  mixed -> patent: 2
  paper -> none: 1
  none -> paper: 1
  patent -> book: 1
  none -> book: 1
  patent -> none: 1
  software_or_database -> paper: 1
  none -> patent: 1
  book -> standards_doc: 1
  paper -> software_or_database: 1
  standards_doc -> none: 1
```

## longrun/citation_windows_labeled.jsonl

First coder: `claude-opus-5-5`. Second coder: `gpt-6-astra-pro` (reasoning effort max, batches of 100-300 windows, guide version `276adff408`). 8288 of 8288 windows coded by both.

### function

```
n=8288 accuracy=0.764 kappa=0.676
label                             n_ref   prec    rec
background_context                 2952   0.67   0.91
data_or_materials_source            411   0.85   0.69
definitional_boilerplate            250   0.90   0.75
foundation                          676   0.83   0.65
incorporated_reference_list         410   0.68   0.04
method_or_tool                     2260   0.87   0.88
own_family_continuation             124   0.84   0.25
prior_art_distinguished            1205   0.80   0.59

most common disagreements:
  prior_art_distinguished -> background_context: 480
  incorporated_reference_list -> background_context: 391
  method_or_tool -> background_context: 200
  foundation -> background_context: 157
  background_context -> prior_art_distinguished: 103
  background_context -> method_or_tool: 91
  data_or_materials_source -> method_or_tool: 79
  background_context -> foundation: 60
  own_family_continuation -> method_or_tool: 44
  own_family_continuation -> background_context: 37
  foundation -> prior_art_distinguished: 34
  data_or_materials_source -> background_context: 33
  foundation -> method_or_tool: 33
  method_or_tool -> prior_art_distinguished: 25
  method_or_tool -> data_or_materials_source: 25
  definitional_boilerplate -> method_or_tool: 24
  definitional_boilerplate -> background_context: 24
  method_or_tool -> foundation: 15
  prior_art_distinguished -> method_or_tool: 13
  own_family_continuation -> prior_art_distinguished: 12
  data_or_materials_source -> foundation: 10
  definitional_boilerplate -> data_or_materials_source: 10
  background_context -> definitional_boilerplate: 8
  method_or_tool -> definitional_boilerplate: 7
  foundation -> data_or_materials_source: 7
  background_context -> data_or_materials_source: 6
  method_or_tool -> incorporated_reference_list: 5
  data_or_materials_source -> prior_art_distinguished: 4
  prior_art_distinguished -> foundation: 3
  foundation -> definitional_boilerplate: 3
  foundation -> own_family_continuation: 3
  definitional_boilerplate -> foundation: 3
  data_or_materials_source -> definitional_boilerplate: 2
  prior_art_distinguished -> data_or_materials_source: 1
  background_context -> incorporated_reference_list: 1
  prior_art_distinguished -> own_family_continuation: 1
  foundation -> incorporated_reference_list: 1
  incorporated_reference_list -> method_or_tool: 1
  definitional_boilerplate -> incorporated_reference_list: 1
  incorporated_reference_list -> own_family_continuation: 1
  background_context -> own_family_continuation: 1
```

### cited_doc_type

```
n=8288 accuracy=0.959 kappa=0.939
label                             n_ref   prec    rec
book                                774   0.89   0.97
mixed                               624   0.89   0.75
none                               1533   0.99   1.00
paper                              4409   0.99   0.97
patent                              587   0.83   1.00
software_or_database                  6   0.28   0.83
standards_doc                       355   0.97   0.95

most common disagreements:
  mixed -> patent: 86
  paper -> mixed: 51
  paper -> book: 45
  mixed -> book: 40
  mixed -> paper: 26
  paper -> patent: 22
  paper -> software_or_database: 10
  standards_doc -> none: 10
  book -> paper: 8
  standards_doc -> book: 6
  book -> mixed: 5
  paper -> standards_doc: 5
  book -> patent: 5
  none -> patent: 4
  book -> standards_doc: 3
  mixed -> standards_doc: 2
  none -> standards_doc: 2
  paper -> none: 2
  book -> software_or_database: 2
  software_or_database -> paper: 1
  standards_doc -> patent: 1
  standards_doc -> software_or_database: 1
  patent -> none: 1
  book -> none: 1
```

## firms/citation_windows_labeled.jsonl.gz

First coder: `claude-opus-5-5`. Second coder: `claude-opus-5-5` (claude-code-subagent, guide version `276adff408`). 2585 of 52816 windows coded by both.

### function

```
n=2585 accuracy=0.916 kappa=0.891
label                             n_ref   prec    rec
background_context                  719   0.89   0.90
data_or_materials_source            119   0.86   0.85
definitional_boilerplate            112   0.93   0.91
foundation                          180   0.86   0.86
incorporated_reference_list          87   0.93   0.93
method_or_tool                      878   0.94   0.93
own_family_continuation              24   0.96   0.92
prior_art_distinguished             466   0.94   0.94

most common disagreements:
  method_or_tool -> background_context: 33
  background_context -> method_or_tool: 23
  background_context -> prior_art_distinguished: 22
  prior_art_distinguished -> background_context: 22
  background_context -> foundation: 18
  foundation -> background_context: 15
  method_or_tool -> data_or_materials_source: 13
  data_or_materials_source -> method_or_tool: 10
  foundation -> method_or_tool: 6
  definitional_boilerplate -> method_or_tool: 6
  data_or_materials_source -> background_context: 5
  method_or_tool -> foundation: 5
  incorporated_reference_list -> background_context: 5
  method_or_tool -> definitional_boilerplate: 4
  background_context -> definitional_boilerplate: 3
  foundation -> prior_art_distinguished: 3
  definitional_boilerplate -> background_context: 3
  background_context -> incorporated_reference_list: 3
  method_or_tool -> prior_art_distinguished: 3
  prior_art_distinguished -> foundation: 2
  foundation -> data_or_materials_source: 2
  own_family_continuation -> method_or_tool: 1
  definitional_boilerplate -> data_or_materials_source: 1
  method_or_tool -> incorporated_reference_list: 1
  data_or_materials_source -> definitional_boilerplate: 1
  data_or_materials_source -> own_family_continuation: 1
  prior_art_distinguished -> incorporated_reference_list: 1
  data_or_materials_source -> incorporated_reference_list: 1
  own_family_continuation -> background_context: 1
  incorporated_reference_list -> method_or_tool: 1
  prior_art_distinguished -> method_or_tool: 1
```

### cited_doc_type

```
n=2585 accuracy=0.979 kappa=0.958
label                             n_ref   prec    rec
book                                393   0.98   0.98
mixed                               209   0.91   0.89
none                                 77   0.95   0.95
paper                              1764   0.99   0.99
patent                               60   0.98   1.00
software_or_database                 13   0.80   0.92
standards_doc                        69   0.96   0.93

most common disagreements:
  mixed -> paper: 15
  paper -> mixed: 13
  mixed -> book: 6
  book -> mixed: 5
  standards_doc -> none: 4
  none -> standards_doc: 3
  paper -> book: 2
  mixed -> patent: 1
  software_or_database -> paper: 1
  mixed -> software_or_database: 1
  none -> software_or_database: 1
  book -> paper: 1
  standards_doc -> mixed: 1
  paper -> software_or_database: 1
```

## firms/citation_windows_labeled.jsonl.gz

First coder: `claude-opus-5-5`. Second coder: `gpt-6-astra-pro` (reasoning effort max, batches of 100-300 windows, guide version `276adff408`). 52816 of 52816 windows coded by both.

### function

```
n=52816 accuracy=0.732 kappa=0.642
label                             n_ref   prec    rec
background_context                15156   0.57   0.83
data_or_materials_source           2097   0.77   0.75
definitional_boilerplate           2263   0.84   0.73
foundation                         3591   0.75   0.63
incorporated_reference_list        2028   0.77   0.31
method_or_tool                    17291   0.89   0.85
own_family_continuation             480   0.88   0.32
prior_art_distinguished            9910   0.84   0.51

most common disagreements:
  prior_art_distinguished -> background_context: 4730
  method_or_tool -> background_context: 1934
  incorporated_reference_list -> background_context: 1401
  background_context -> method_or_tool: 972
  foundation -> background_context: 949
  background_context -> prior_art_distinguished: 690
  background_context -> foundation: 518
  definitional_boilerplate -> method_or_tool: 266
  data_or_materials_source -> method_or_tool: 246
  data_or_materials_source -> background_context: 212
  definitional_boilerplate -> background_context: 203
  method_or_tool -> data_or_materials_source: 176
  foundation -> method_or_tool: 173
  own_family_continuation -> background_context: 150
  foundation -> prior_art_distinguished: 142
  background_context -> definitional_boilerplate: 141
  method_or_tool -> foundation: 132
  method_or_tool -> prior_art_distinguished: 129
  background_context -> data_or_materials_source: 126
  own_family_continuation -> method_or_tool: 113
  method_or_tool -> definitional_boilerplate: 111
  definitional_boilerplate -> data_or_materials_source: 105
  background_context -> incorporated_reference_list: 93
  prior_art_distinguished -> method_or_tool: 83
  data_or_materials_source -> foundation: 43
  own_family_continuation -> incorporated_reference_list: 43
  foundation -> data_or_materials_source: 38
  method_or_tool -> incorporated_reference_list: 37
  definitional_boilerplate -> foundation: 32
  foundation -> definitional_boilerplate: 29
  prior_art_distinguished -> foundation: 29
  data_or_materials_source -> definitional_boilerplate: 23
  prior_art_distinguished -> data_or_materials_source: 11
  own_family_continuation -> prior_art_distinguished: 11
  background_context -> own_family_continuation: 8
  method_or_tool -> own_family_continuation: 6
  own_family_continuation -> data_or_materials_source: 5
  data_or_materials_source -> prior_art_distinguished: 4
  data_or_materials_source -> incorporated_reference_list: 4
  own_family_continuation -> foundation: 4
  incorporated_reference_list -> method_or_tool: 3
  definitional_boilerplate -> prior_art_distinguished: 3
  prior_art_distinguished -> own_family_continuation: 3
  foundation -> own_family_continuation: 2
  prior_art_distinguished -> incorporated_reference_list: 2
  prior_art_distinguished -> definitional_boilerplate: 2
  definitional_boilerplate -> incorporated_reference_list: 2
  own_family_continuation -> definitional_boilerplate: 2
  incorporated_reference_list -> own_family_continuation: 1
  incorporated_reference_list -> definitional_boilerplate: 1
  incorporated_reference_list -> foundation: 1
  foundation -> incorporated_reference_list: 1
  incorporated_reference_list -> data_or_materials_source: 1
```

### cited_doc_type

```
n=52816 accuracy=0.936 kappa=0.875
label                             n_ref   prec    rec
book                               7573   0.93   0.98
mixed                              3947   0.86   0.69
none                               1721   0.92   0.90
paper                             36406   0.99   0.96
patent                             1340   0.59   0.97
software_or_database                293   0.26   0.92
standards_doc                      1536   0.82   0.91

most common disagreements:
  mixed -> patent: 728
  paper -> software_or_database: 722
  paper -> mixed: 374
  mixed -> book: 256
  paper -> book: 231
  mixed -> paper: 199
  paper -> patent: 147
  paper -> standards_doc: 141
  standards_doc -> none: 119
  none -> standards_doc: 110
  book -> mixed: 69
  mixed -> standards_doc: 38
  patent -> paper: 33
  none -> software_or_database: 32
  book -> patent: 26
  book -> standards_doc: 26
  mixed -> software_or_database: 20
  none -> book: 18
  book -> paper: 16
  book -> software_or_database: 12
  patent -> none: 9
  standards_doc -> book: 9
  software_or_database -> book: 9
  software_or_database -> mixed: 5
  standards_doc -> paper: 5
  paper -> none: 5
  none -> patent: 4
  none -> paper: 4
  standards_doc -> software_or_database: 4
  software_or_database -> paper: 4
  software_or_database -> none: 4
  standards_doc -> patent: 3
  standards_doc -> mixed: 2
  book -> none: 2
```

## fields/citation_windows_labeled.jsonl

First coder: `claude-opus-5-5`. Second coder: `claude-opus-5-5` (claude-code-subagent, guide version `276adff408`). 235 of 5822 windows coded by both.

### function

```
n=235 accuracy=0.906 kappa=0.881
label                             n_ref   prec    rec
background_context                   59   0.79   0.92
data_or_materials_source             10   1.00   0.80
definitional_boilerplate              8   0.80   1.00
foundation                           19   0.89   0.84
incorporated_reference_list          20   0.95   0.95
method_or_tool                       68   0.98   0.93
prior_art_distinguished              51   0.96   0.88

most common disagreements:
  prior_art_distinguished -> background_context: 6
  method_or_tool -> background_context: 4
  background_context -> prior_art_distinguished: 2
  foundation -> background_context: 2
  method_or_tool -> foundation: 1
  background_context -> foundation: 1
  incorporated_reference_list -> background_context: 1
  data_or_materials_source -> definitional_boilerplate: 1
  background_context -> incorporated_reference_list: 1
  background_context -> definitional_boilerplate: 1
  data_or_materials_source -> background_context: 1
  foundation -> method_or_tool: 1
```

### cited_doc_type

```
n=235 accuracy=0.979 kappa=0.948
label                             n_ref   prec    rec
book                                 35   1.00   0.91
mixed                                15   0.83   1.00
none                                  4   1.00   1.00
paper                               176   0.99   0.99
software_or_database                  1   1.00   1.00
standards_doc                         4   1.00   0.75

most common disagreements:
  book -> paper: 2
  paper -> mixed: 1
  standards_doc -> mixed: 1
  book -> mixed: 1
```

## fields/citation_windows_labeled.jsonl

First coder: `claude-opus-5-5`. Second coder: `gpt-6-astra-pro` (reasoning effort max, batches of 100-300 windows, guide version `276adff408`). 5822 of 5822 windows coded by both.

### function

```
n=5822 accuracy=0.707 kappa=0.619
label                             n_ref   prec    rec
background_context                 1549   0.52   0.81
data_or_materials_source            268   0.83   0.70
definitional_boilerplate            229   0.88   0.76
foundation                          524   0.72   0.61
incorporated_reference_list         416   0.83   0.23
method_or_tool                     1747   0.89   0.86
own_family_continuation              13   0.23   0.23
prior_art_distinguished            1076   0.80   0.54

most common disagreements:
  prior_art_distinguished -> background_context: 478
  incorporated_reference_list -> background_context: 322
  method_or_tool -> background_context: 175
  foundation -> background_context: 139
  background_context -> prior_art_distinguished: 96
  background_context -> foundation: 88
  background_context -> method_or_tool: 87
  data_or_materials_source -> background_context: 33
  data_or_materials_source -> method_or_tool: 31
  foundation -> method_or_tool: 29
  foundation -> prior_art_distinguished: 27
  definitional_boilerplate -> method_or_tool: 20
  method_or_tool -> prior_art_distinguished: 18
  method_or_tool -> data_or_materials_source: 16
  definitional_boilerplate -> background_context: 14
  method_or_tool -> foundation: 13
  data_or_materials_source -> foundation: 13
  definitional_boilerplate -> data_or_materials_source: 13
  background_context -> definitional_boilerplate: 12
  prior_art_distinguished -> method_or_tool: 8
  background_context -> incorporated_reference_list: 8
  background_context -> data_or_materials_source: 8
  method_or_tool -> definitional_boilerplate: 8
  method_or_tool -> incorporated_reference_list: 6
  own_family_continuation -> background_context: 5
  prior_art_distinguished -> foundation: 5
  definitional_boilerplate -> foundation: 5
  foundation -> own_family_continuation: 4
  own_family_continuation -> method_or_tool: 3
  background_context -> own_family_continuation: 3
  data_or_materials_source -> prior_art_distinguished: 3
  method_or_tool -> own_family_continuation: 2
  own_family_continuation -> incorporated_reference_list: 2
  foundation -> definitional_boilerplate: 2
  definitional_boilerplate -> prior_art_distinguished: 2
  definitional_boilerplate -> incorporated_reference_list: 2
  foundation -> data_or_materials_source: 2
  prior_art_distinguished -> definitional_boilerplate: 1
  data_or_materials_source -> definitional_boilerplate: 1
  prior_art_distinguished -> own_family_continuation: 1
  prior_art_distinguished -> incorporated_reference_list: 1
```

### cited_doc_type

```
n=5822 accuracy=0.950 kappa=0.881
label                             n_ref   prec    rec
book                                777   0.92   0.97
mixed                               424   0.84   0.74
none                                 73   0.96   0.89
paper                              4393   0.99   0.97
patent                               62   0.41   0.97
software_or_database                 11   0.32   1.00
standards_doc                        82   0.77   0.96

most common disagreements:
  mixed -> patent: 60
  paper -> mixed: 51
  paper -> book: 41
  mixed -> book: 27
  paper -> patent: 21
  paper -> software_or_database: 21
  mixed -> paper: 17
  book -> mixed: 9
  paper -> standards_doc: 8
  book -> paper: 7
  none -> standards_doc: 7
  book -> standards_doc: 4
  mixed -> standards_doc: 4
  book -> patent: 4
  patent -> paper: 2
  mixed -> software_or_database: 2
  standards_doc -> mixed: 2
  none -> book: 1
  paper -> none: 1
  standards_doc -> none: 1
  book -> none: 1
```
