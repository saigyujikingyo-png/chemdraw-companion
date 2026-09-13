# Native semantic qualification v1.1

This revision implements the independent review in Issue #2 comment 5654674095.
Previous source freezes and r1/r2/r3 native evidence remain unchanged. The exact
execution receipt, not this design note, determines the final native outcome.

## Actual query properties

The reader rejects query attributes using their actual serialized CDXML names:
[FreeSites](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_RestrictFreeSites.htm),
[RingBondCount](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_RestrictRingBondCount.htm),
[SubstituentsUpTo](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_RestrictSubstituentsUpTo.htm),
[SubstituentsExactly](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_RestrictSubstituentsExactly.htm),
[UnsaturatedBonds](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_RestrictUnsaturatedBonds.htm)
and the previously documented query-only ImplicitHydrogens. These preserved SDK
definitions are format references, not a guarantee of all ChemDraw 26 behavior.
The query control starts with a fully bound single-atom FormulaHTML baseline
that actually matches ordinary ethane. Each test then changes only one query
attribute and requires the query-specific refusal reason and an unverified
comparison. Missing API data cannot make that test pass accidentally.

## Qualification admits measured branches

The control reader observes quantities before using independent expected
chemistry. Production additionally requires admitted branches. A branch records
source class/field, serialized-H and atom-label presence, actual atomic number,
charge/isotope, resolved H, explicit H/D neighbor isotopes and qualified graph
scope. These keys contain no atom IDs, sample coordinates or expected candidate
values. They limit demonstrated observation coverage; they are not a universal
valence model or a reaction layout rule.

Only independently matching controls with actual cleanup and different-process
reopen observations contribute branch coverage. A branch needs evidence in both
phases. Every other branch produces unknown with its candidate observation
preserved as raw evidence. The receipt says `qualified_covered_branches`, never
that an entire proposed profile is qualified. Label-only and carbon-field-only
H resolution remain unqualified. This phase's original 20 inputs are unchanged.

## Complete receipt and source evidence

`load_qualification` checks the receipt type/profile, exact frozen matrix,
complete control inventory, outcome counts and native process coverage. It
requires every original native input/output/selection-after/sidecar receipt and
every per-control comparison record named by the evidence manifest. It rehashes
those bytes, checks complete native provenance and reruns the delivered reader
offline on both control phases. It recomputes the independent comparison and
the admitted branch list. A missing artifact, two-key status summary, changed
observer or fabricated larger branch list cannot satisfy these checks.

The trusted boundary is still the authorized local executor and independently
supplied qualification record. Hashes do not authenticate an adversary who can
replace the entire source, native observations and trusted records together.
No service, registry, new dependency or platform is introduced.

Production `read_geometry` applies this branch admission to **both** cleanup and
reopened fragments, compares each with the same declared visible chemistry and
checks their semantic signatures, allowing native ID remapping. It retains both
observations. Old 0.4 sidecars remain refused and cannot inherit 0.5 evidence.

## Controller handoff

The package contains the exact source tree, frozen synthetic inputs, source
freeze, native CDXML/sidecars, process receipt, per-control observations and
comparison files. An admission proposal remains pending until controller review.
The proposal's `evidence_directory` names the extracted package directory next
to the proposal. A controller-approved qualification record must retain the
bound freeze/control receipt and point to that complete evidence directory.
The production loader intentionally refuses a pending proposal.

No private candidate is read or run by this implementation task. The controller
owns offline preflight and the phase's at-most-one fixed-input attempt; a known
replay refusal stops it. Native control consistency is separate from chemical
mechanism, visual and human acceptance. Gold remains zero.
