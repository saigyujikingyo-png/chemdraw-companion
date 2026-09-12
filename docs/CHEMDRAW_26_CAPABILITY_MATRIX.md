# ChemDraw 26 capability matrix

Qualification plan, not a completed matrix. Historical implementation commit f111c36564fcebf42640cedee809ee622087ba8c reports ChemDraw Prime 26.0.0.6141 x64. Interop assembly version is separate. Do not generalize to every edition/device/licence.

Repair SaveAs first, then fill this matrix before S1 -> R1 -> M1 -> M2. Use small microfixtures, not a generalized SDK wrapper.

| ID | Layer / capability | Minimum qualification | Current evidence |
| --- | --- | --- | --- |
| A01 | Create/bind document | Create and identify exact disposable target; active-document readback in A/B test | narrow_observed; retained refs did not cross-write, but actual ActiveDocument and COM-to-PID binding unproven |
| A02 | CDX/CDXML save | Immutable requested path, returned args/errors, expected bytes and readback; controlled repeat | ethanol success followed by missing-file failure; unresolved |
| A03 | CDX disk reopen | Close source, open disk copy through qualified lifecycle, inspect semantic/drawable inventory | narrow_observed ethanol only |
| A04 | CDXML disk reopen | Independently open saved XML, edit/save/reopen copy | unverified |
| A05 | Full-scene native export | Full inventory and physical pixel/ink scale; reject wrong selection | narrow_observed diagnostic ethanol PNG |
| B01 | Atom control | Create/read/change/remove; element, isotope, explicit H and specified stereo; reopen | MakeAtom O/N narrow_observed; full attributes unverified |
| B02 | Bond control | Create/read/change/delete endpoints, order, wedge/hash; reopen | imported ethanol single bonds only; control unverified |
| B03 | Curly-arrow geometry | Editable two-electron curve; read/move tail/head/control points; save/reopen | unverified |
| B04 | Curly-arrow anchors | IR source LP/bond and target atom/bond mapped; move fragment and explicitly reroute correctly | unverified; editable curve alone insufficient |
| B05 | Lone pairs | Create/read/change/remove electron pair, count/atom association/position; move fragment and reopen | unverified; raster/text dots insufficient as electron objects |
| B06 | Charges | Positive and negative formal charge plus attached glyph; change/read/remove and reopen | nonzero charge control unverified |
| B07 | Fragment transform | Rigid translation/rotation preserves stereo/anti and updates labels/electron anchors; reopen | unverified; no silent reflection |
| B08 | Cleanup | Verified native cleanup of disturbed geometry; graph/stereo/mapping preservation and rerouted curves | ethanol Clean(true) narrow_observed, not mechanism layout |
| B09 | Object identity | IR occurrence -> native ID mapping after cleanup/reopen; reject ambiguous duplicate matching | unverified |
| B10 | Both-format editability | Curve/electron object/charge/fragment edits on independent CDX/CDXML copies, save/reopen again | unverified |
| B11 | Reaction annotations | Editable step arrow, plus sign, conditions, label and association; text edit survives reopen | unverified |
| C01 | Mechanism composition | Frozen valid IR -> native fragments -> Composer -> native adapter -> all M2 checks | unrun; principal architecture risk |

Each row records backend (COM/Add-in/CDXML import/verified desktop route), actual operation/property, source/probe hash, app build/edition, document scope, mutation mode, object type, input/output hashes, supported edit subset, reopen results, evidence IDs, time and limits.

Editable native objects imported via CDXML may qualify a capability only after read/change/save/reopen evidence with provenance. That does not prove COM setters, native automatic layout or arbitrary-document patching. Disposable-revision rebuilding can qualify declared logical updates; label it rebuild, not in_place. Semantic anchors may be maintained by Composer, but do not describe them as vendor-maintained.

Native IDs may change on serialization; reconstruct unambiguous IR/native mapping and prove the intended occurrence is edited. Document safety identity is separate: atom IDs, content hashes, filenames and leases do not establish the target document/process.

The Add-in guide documents insertion/readback/serialization, not cleanup, disk lifecycle or reliable object identity. Absence there does not prove every native route unsupported. Missing Add-in availability must not prevent bounded qualification of a permitted COM route.

Receipt example (null evidence never passes):

~~~json
{
  "capability_id": "B03",
  "application_build": "26.0.0.6141",
  "edition": "Prime",
  "backend": "unverified",
  "operation": null,
  "mutation_mode": null,
  "status": "unverified",
  "native_object_type": null,
  "semantic_anchor_owner": null,
  "cdx_reopen_edit": "unverified",
  "cdxml_reopen_edit": "unverified",
  "evidence_ids": [],
  "limitations": ["No executed curly-arrow probe yet"]
}
~~~
