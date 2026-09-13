# Native semantic readback v1 implementation candidate

This source checkpoint is **not yet qualified by native controls**. The reviewed
20-input preregistration at 7633111 remains immutable. The architecture approved
execution in Issue #2 comment 5654477339; exact executed source and input bytes
must still be frozen before the first native call.

`native_semantics.observe_document` is the delivered reader. It has no expected
IR parameter. It preserves raw serialized label-H, complete nested atom-label
evidence, independent H/D neighbor nodes and native selected FormulaHTML before
resolving attached non-node H. `compare_document` is a later pure comparison;
its output cannot fill missing observations. The adapter preserves `implicit_h`
as the existing compatibility key. No label-H/attached-H/explicit-H sum exists.

The proposed scope is narrower than general ring support: neutral C/N/O acyclic
graphs, one saturated C5/C6 ring or one saturated C4O five-ring with ordinary
branches, terminal explicit H/D, isolated ammonium/chloride. Isolated carbon is
observation-only. Cyclic unsaturation, other ring sizes or heteroatom cores,
multiple cycles, query/radical/abnormal domains, heavy isotopes, compound labels,
conflicts and native warnings remain unresolved. The graph selects a scope and
checks cut bonds; it never calculates H from a valence table. Actual control
results may leave candidate branches unqualified.

The new `native-semantic-fragments.ps1` executor captures cleanup and then opens
each saved CDXML in another fresh initially empty native process without a
second cleanup. It records PID, OS start time, HWND and HWND-derived PID, job ID,
preexisting PIDs, document counts, warnings, binary/source hashes and retained
document identity. Existing native instances are not attached, activated or
closed. `native-atom-observation.ps1` captures raw calls and saves the exact
selection-after snapshot. Producer and consumer compare complete nested label
subtrees as well as atom/bond attributes and the native chemical export.

New production admission is explicit: `run_composer.py compose` accepts
`--semantic-qualification`. The trusted qualification record must reference a
passed native-control receipt and exact source freeze. The consumer rehashes
actual observer, executor, bridge, common helper, parser, adapter, profile and
other required files against that freeze. The sidecar must carry the same freeze
and exact source/build/process binding. Valid-looking hash syntax is insufficient.

**Old 0.4 sidecars are not accepted by v1**, including sidecars with matching
field values. New 0.5 controls cannot qualify the historical observer. Old APIs
and receipts retain their historical scope; the shared snapshot verifier now
also rejects label-only changes. Offline controller replay is explicitly replay;
a known refusal stops before any new private candidate invocation. There is no
legacy override in the new reader.

No dependency, native API enumeration, ChemScript, inference, private candidate
read, Composer layout/routing/threshold change or IR change is part of this
checkpoint. Source/input revisions and the first native outcome must remain
separate. Software tests and native consistency alone do not establish visual,
chemical-mechanism or human acceptance. Gold remains zero.
