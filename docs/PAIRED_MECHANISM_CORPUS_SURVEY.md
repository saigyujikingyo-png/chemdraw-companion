# Paired mechanism corpus survey

Actual bounded acquisition and native execution, 13 September 2026, for [Issue #2](https://github.com/saigyujikingyo-png/chemdraw-companion/issues/2).

## Measured outcome

The survey obtained **77 unique CDX drawings containing arc/curve objects** from six publicly downloadable Flynn Research Group Word/DOCX teaching documents. **64** have an exact associated author EMF preview; **12** were visually screened as useful mechanism candidates, with **114** electron-flow arrows counted in their author previews. These screening counts are AI-assisted observations, not authenticated human chemistry/gold labels. Seventy-seven files are not seventy-seven qualified mechanisms.

All **12 selected external targets** were actually opened in ChemDraw Prime **26.0.0.6141**, saved as CDXML/CDX/native PNG/native JPEG and reopened in both native formats. An independent evaluator verified **12/12 source hashes and 72/72 exported file hashes/sizes**. The first same-process Close/Open snapshots were subsequently downgraded because cached COM identity can invalidate a disk-reopen claim. A further **24 distinct fresh zero-document PID/HWND instances** independently read the twelve saved CDX and CDXML pairs, with verified input/output hashes and all 72 original artifacts unchanged. CDXML reopen changes some IDs, quantizes some arrow coordinates and changes some text object counts; one case drops a CrossingBonds attribute. These are usable hash-bound native pairs with recorded fidelity limits, not a blanket lossless-editability or quality PASS.

The main source is [Flynn Research Group, Organic Chemistry Assessments](https://www.flynnresearchgroup.com/organic-assessments). Exact downloads, DOCX members or direct DOC OLE streams, original/container hashes, retrieval times, formats, exposure history and private relative locators are in [pilot-source-inventory.json](../examples/paired/pilot-source-inventory.json) and [source-manifests.json](../examples/paired/source-manifests.json). All 168 listed asset bindings were checked against actual bytes. Original documents, embedded CDX, EMF and native exports remain private. Asset redistribution is **unknown**, which did not block authorized internal research.

| Candidate | Screened mechanism | Electron arrows | States / steps (screened) |
|---|---|---:|---:|
| flynn-aldol-055 | Enolate formation and intramolecular SN2 cyclization | 6 | 3 / 2 |
| flynn-aldol-032 | Carboxylate formation and intramolecular SN2 lactonization | 4 | 3 / 2 |
| flynn-aldol-013 | Base-catalyzed ketone epimerization through an enolate | 6 | 3 / 2 |
| flynn-aldol-026 | Intramolecular aldol addition | 8 | 4 / 3 |
| flynn-aldol-033 | Phenoxide carboxylation to salicylic acid | 8 | 5 / 4 |
| flynn-aldol-024 | Enolate alkylation of a fused-ring ketone | 6 | 3 / 2 |
| flynn-aldol-040 | Acid-catalyzed crossed aldol condensation | 17 | None / None |
| flynn-aldol-051 | Intramolecular aldol condensation with dehydration | 14 | 6 / None |
| flynn-aldol-061 | Wolff-Kishner reduction | 22 | None / None |
| flynn-aldol-063 | Acid-catalyzed nitrile hydrolysis | 17 | None / None |
| flynn-carbonyl-1257156820 | Diazomethane esterification of a carboxylic acid | 4 | 3 / 2 |
| flynn-carbonyl-1255682419 | Protic quench of methylmagnesium bromide | 2 | 2 / 1 |

The set covers proton transfer, SN2, enolate/carbonyl/acyl chemistry, aromatic chemistry, dense charge/LP regions, multi-arrow and multi-step/multirow layouts. It does not establish balanced E1/E2, pericyclic or rearrangement coverage. It is heavily concentrated in one author/teaching style. Expand those gaps only after evaluating the actual pipeline, rather than increasing the count with ordinary molecules.

`flynn-aldol-055` is the first blind attempt. Source container: [Aldol answers DOCX](https://www.flynnresearchgroup.com/s/Problem-Set-6-Aldol-answers.docx), SHA-256 `3b63557df14651b3ddaf7f4756e29ec6c43a75c3e9870218da257f961b7eb0cd`; member `word/embeddings/oleObject55.bin`, OLE `CONTENTS`, original CDX SHA-256 `de90d98615712b2ee69d9fb060955076cab92a1dacce255ac25a7638d66650f6`. It has a separate author-vector preview and a newly executed ChemDraw reference render. All structural details stay outside the generator context.

## Actual project investigation

[project-survey.json](../examples/paired/project-survey.json) records pinned repositories, tree scope/truncation, actual file URLs, hashes and rights observations. Six academic/OCSR repositories and eleven editor/toolkit repository investigations include one overlap; counts below are paths or downloaded files, never automatically mechanism counts.

| Source | Actual finding and use |
|---|---|
| [Ketcher](https://github.com/epam/ketcher) | Targeted complete test-data subtree has 189 CDX/CDXML paths after root-tree truncation. No established electron-flow target from filename triage; no blobs downloaded. |
| [Indigo](https://github.com/epam/Indigo) | 152 native-format paths; three downloaded reaction CDXML files are ordinary schemes without electron-flow curves. Parser controls only. |
| [JChemPaint](https://github.com/JChemPaint/jchempaint) | No CDX/CDXML in inspected complete tree; CML molecular tests are not the required native mechanism targets. |
| [BKChem](https://bkchem.zirael.org/wiki/oo-exporter-workflow) | Actual wiki archive supplies SVG with embedded CDML plus corrected ODG: ten molecule objects, four spline arrows, LP/radical marks. Useful vector silver lead; not a ChemDraw pair. |
| [Kendraw](https://github.com/electrosenpai/kendraw) | Three CDXML paths; selected four-step ESI fixture has ordinary arrows, no verified electron-flow curves. |
| [pycdxml](https://github.com/kienerj/pycdxml) / [cdxml-toolkit](https://github.com/leehiufung911/cdxml-toolkit) | Actual molecule/style fixture and a generated serpentine showcase were downloaded. Straight arrows and fixed showcase counts do not supply professional curly-arrow supervision. |
| [Revvity Add-ins](https://github.com/Revvity/ChemDraw-AddIns) / [JS examples](https://github.com/Revvity/ChemDraw-JS-Public-Examples) | Official automation examples, but no CDX/CDXML asset paths in inspected trees. |
| [BChemXtract](https://github.com/Beilstein-Institut/BChemXtract) | 355 native-format paths include duplicates. A generic fixture's 37 unheaded curves are decorative. Best external paper CDX has five headed modern arcs and superseded legacy copies; retain as a further candidate, not an accepted atom-level mechanism teacher. |
| [MolScribe](https://github.com/thomas0809/MolScribe) | Actual molecular example PNG downloaded; graph recognition component, no curly-arrow native teacher. |
| [DECIMER](https://github.com/Kohulan/DECIMER-Image_Transformer) | Actual caffeine PNG downloaded; image-to-SMILES component, not paired mechanism corpus. |
| [MolNexTR](https://github.com/CYF2000127/MolNexTR) | Actual molecular PNG downloaded. Curved-arrow perturbation data test OCSR robustness, not verified source/sink semantics or native professional layout. |
| [MolSight](https://github.com/hustvl/MolSight) | Actual charged/stereochemical molecular PNG downloaded. Molecular graph/coordinate recognition is useful, but no native mechanism pair found. |
| [RxnScribe](https://github.com/thomas0809/RxnScribe) | Actual Rh catalytic-cycle PNG downloaded. Process arrows and reactant/product/condition boxes are useful image-only layout data, not atom-attached electron-flow ground truth. |
| [MechFinder](https://github.com/snu-micc/MechFinder) | Inspected code/tree and source/sink CSV descriptions; [paper](https://www.nature.com/articles/s41597-024-03709-y) reports 31,364 mechanistic reactions. No CDX/CDXML visual assets found. Did not ingest unfiltered CSVs containing potentially excluded families. |

Editor/toolkit acquisition totals **8 CDXML + 2 CDX + one BKChem archive**, with zero native files yet qualified as atom-level curly-electron teacher targets in that sub-survey. The best paper lead is [Yamamoto et al., BJOC 2024 Scheme 4](https://doi.org/10.3762/bjoc.20.116), repository CDX SHA-256 `f0e280ca73586b53ae73727da43edfa41f6e0eee1c342b3c6b46661b2170c806`. Published article CC BY 4.0 does not alone establish rights in those separate CDX bytes.

[Diaz, Ecker and Fraser's mAMCase dataset](https://zenodo.org/records/7967958), DOI 10.5281/zenodo.7967958, advertises ChemDraw and step PNGs. File/API retrieval returned HTTP 504 and is retained as a failed acquisition, not a counted sample. The survey also inspected [ChemScanner's CDX reader](https://github.com/ComPlat/chem_scanner/blob/master/lib/chem_scanner/chem_draw/cdx_reader.rb) and [Open Babel CDX definitions](https://github.com/openbabel/openbabel/blob/master/include/chemdrawcdx.h) to interpret bounded binary inventories.

## What the native evidence changes

A structured teacher source is feasible: actual author CDX and associated previews exist, can be recovered without manual redrawing, and can be rendered by the existing native adapter. Reliability still needs chemical interpretation, object correspondence and visual calibration. Abbreviations expand on import; raw atom/fragment counts can change; formal state/step objects are not the same as semantic steps; CircleMinus/Plus graphics and atom charge properties can encode overlapping information. The old readback's is_radical flag even labels some LonePair symbols as radical, so that convenience flag is not chemical truth.

The native PNG stores black RGB with the shape carried in alpha. This was discovered during the real blind attempt and requires an explicit display-normalization boundary; retain the original PNG as native evidence. A fixed white alpha composite changes display encoding only, never the target geometry, and must have its own hash and transformation receipt.

All source samples are exposed development material. No M2, derivative or holdout was used; no learned model was trained; authenticated gold remains zero. The [fresh native checks](../verification/2026-09-13-paired-pilot/native-survey-checks.json) retain this distinction. See the [execution receipt](reviews/2026-09-13-issue2-paired-pilot.md) for actual model and Composer outcomes before drawing conclusions about reconstruction or automatic correction quality.
