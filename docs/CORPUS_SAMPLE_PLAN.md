# Corpus sample plan

Status: planned coverage, not completed examples or accepted gold. Target **200 checked examples total: 40 human-verified gold and 160 other checked examples**. The initial three proof inputs are ungraded schema/annotation prototypes and do not count toward these targets. No native execution, further benchmark repair or data acquisition is authorized by this document.

## Coverage targets

| Primary chemistry family | Gold | Other checked | Total |
| --- | ---: | ---: | ---: |
| Proton transfer | 4 | 16 | 20 |
| SN1 / SN2 | 8 | 32 | 40 |
| E1 / E2 | 6 | 24 | 30 |
| Carbonyl addition / acyl substitution | 8 | 32 | 40 |
| Aromatic substitution | 4 | 16 | 20 |
| Rearrangement | 6 | 24 | 30 |
| Pericyclic | 4 | 16 | 20 |
| **Total** | **40** | **160** | **200** |

Assign one primary family and overlapping stress tags. Among the 40 gold targets, include at least 12 dense-charge/lone-pair cases, 12 cases containing a transition with three or more simultaneous arrows, 12 mechanisms with four or more states, and 8 requiring snake traversal. These overlapping subsets do not increase the count.

After the three known proof inputs validate the contracts, review 12 fresh candidate specifications before expanding: one proton transfer, one each SN1/SN2/E1/E2, three carbonyl/acyl cases spanning both categories, one aromatic substitution, one rearrangement and two pericyclic cases. Resolve conditions, proton transfers and stereochemistry before authoring. Unsupported chemistry stays pending.

## Review and promotion

Prefer independently authored native references under [the acquisition and rights policy](CORPUS_ACQUISITION_AND_RIGHTS.md). A chemistry reviewer other than the author checks every state, atom/H/charge balance, bond changes, lone pairs, simultaneous flows and stereochemistry. Record sources and teaching-model simplifications separately from experimental observations.

A recorded visual review examines the native full-page render at the declared physical size, including actual arrowhead tips, charge/label legibility, intended contacts and snake order. Gold additionally requires CDX and CDXML disk reopening, editable objects and a saved/reopened edit on a copy. Keep chemistry, layout, editability and rights outcomes separate. Automation or owner silence cannot confer gold status.

The other 160 may mix first-party variants, rights-cleared records, AI-assisted silver candidates and labelled negative/imperfect examples. Checked does not mean passed: record actual checks and outcomes. Retain first output, corrections and final version separately. Unmeasured human correction time remains null. A corrected reference cannot turn the original automated attempt into a success.

## Exposure, lineage and evaluation

M1 and M2 were exposed during historical implementation and repairs. Preserve that history explicitly. Lock them as `fixed_regression`, for evaluation only going forward. They and their derivatives are excluded from training/tuning corpus counts. Their coordinates, masks, correction targets and evaluation outcomes must not guide benchmark-specific rule selection or tuning. This restriction supersedes older instructions permitting iterative benchmark repair.

Record parentage and exclusion groups across substitutions, atom-ID changes, reordered arrays, restyling and rendering variants. Broad reaction-family labels and derivative-lineage groups serve different purposes; eligibility requires explicit lineage review. Report unique chemistry/lineage counts separately from artifact or variant counts.

Keep related variants together when defining corpus splits. Do not preselect future holdouts or include them in these 200 targets. After implementation/rule freeze, an independent evaluator selects fresh, unexposed cases and records their provenance. Previously disclosed cases cannot become unseen merely through renaming or a new split label.
