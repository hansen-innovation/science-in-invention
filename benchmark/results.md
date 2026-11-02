# Benchmark results

Generated 2026-11-02 by `benchmark/subagent_batches.py report`.

Each section compares a sample's label file (first coder, the source of truth for that sample) with a blind second coder. Subagent coders ran as Claude Code subagents on batches of 25-30 windows with the same guide `prompts/label_citation_function.md` and `schema.json`, without access to the other coder's labels. Two LLM coders are not a human benchmark; the 2,000-window double-coded human benchmark is still the release criterion.

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

## pilot/decades/citation_windows_labeled.jsonl

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

## pilot/longrun/citation_windows_labeled.jsonl

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
