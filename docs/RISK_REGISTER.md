# P0 risk register and stop decisions

Design review, 2026-09-12. Likelihood is not estimated from unrun experiments. Every item below is open until linked native evidence closes it. The implementation owner records observations; the architecture owner reviews contract/scope changes. Owner visual acceptance remains the user's decision.

| ID | Failure mode / consequence | Bounded mitigation and proof | Stop condition |
| --- | --- | --- | --- |
| R01 | Edition supports installed ChemDraw but not the add-in/SDK | Probe running edition/entitlement and minimal official add-in; record sanitized native error and exact build | No confirmed lawful native route; do not request new keys by default or redistribute vendor modules |
| R02 | Active-document race writes into another file | Qualify retained handle or isolated native lifecycle with identical A/B, focus switch and user interference; plugin-wide mutex alone is insufficient | Cannot guarantee correct target; refuse writes and mark unattended editing unsupported |
| R03 | Append API mistaken for replace; duplicate objects on retry | Isolated document per revision; write-ahead intent, same-key replay and lost-reply reconciliation tests | Unknown insertion outcome; no blind repeat or Undo |
| R04 | Native serializer/render used to mask legacy layout defects | Native structure geometry stage plus explicit new page/curve layout provenance; review fresh 85 mm output | Three fixture figures still fail after bounded repair; stop renderer breadth |
| R05 | Molecular identity matches but arrows/conditions disappear or flatten | Drawable-object inventory and editable curve/text changes after native disk reopen | Any required object lost or uneditable, irrespective of valid SMILES/PNG |
| R06 | Preview image too small, cropped or from wrong selection/revision | Native pixel measurements, physical-size check, source scope and guarded pre/post export fingerprints; deliberate wrong-selection test | Incomplete or low-detail image; native vector route must be separately qualified |
| R07 | CDX bytes decode but reopen unsupported/corrupt | Open saved disk copy through a verified native lifecycle, inspect objects and save an edited copy | Disk artifact cannot be independently reopened and edited |
| R08 | Scene/library/native disagree on stereo, H, mapping or electron flow | Two-stage semantic comparison and explicit graph differences; fail ambiguous/unsupported chemistry | No deterministic agreement; ask only the missing chemical decision |
| R09 | Restart, cancellation or timeout produces a false success or destroys user work | Durable journal, worker-generation fencing, safe cancellation, immutable checkpoints, copy-only recovery | Cannot reconcile native outcome; quarantine and report `outcome_unknown` |
| R10 | Local add-in transport blocked or unauthenticated | Probe webview-supported transport, loopback/Origin/Host checks, pairing and per-request authorization | No supported authenticated transport; do not disable browser/vendor security |
| R11 | Stale broker/add-in/host tool map changes behavior | Version/manifest handshake, exact recipe/style identity and fresh-host check after supported updates | Identity mismatch; no scientific call before reconciliation |
| R12 | Deployment or update loses credentials, locks files or breaks rollback | Separate versions, drain jobs, preserve credential handles/config, reversible migration and rollback self-test | Old runtime cannot recover; do not replace active installation |
| R13 | Local artifact falsely advertised as delivered | Separate available/transferred/receipt-verified states; receiver bytes/open evidence; count manual steps | Delivery route blocked; native gate unaffected but receipt remains incomplete |
| R14 | University/host/model support inferred from a single machine | Device/version/license/host matrix with actual Terra max run and dated task-specific sources | Only a preset or another product's acceptance exists; leave unverified |
| R15 | Broad dependency/platform work consumes quota before feasibility | One worker, five tools, three fixtures; measured schemas/calls/time/resources; no extra paid reasoner | Native gate unresolved; pause expansion, not scientific checks |

## Evidence disposition

A blocker report names the failed operation, source, current device/app/edition, actual error, attempted supported alternatives, artifact hashes, safe recovery and next decision. Separate `documented`, `observed`, `failed`, `unverified` and `unsupported`; do not use a single red/green product flag. A task-specific requirement can only be waived by the user, and the waiver must appear in the applicable acceptance record rather than a rewritten historical pass.

Native diagnostics can proceed under supervision without certifying unattended support. If R01/R02/R04/R07 remains open at the bounded feasibility endpoint, return the blocker report and the Mnova alternative described in QUALITY_GATES.md. Do not start an unrelated product or contact vendors/university staff without task authorization.

## Resource and retention policy to implement

- Native write concurrency: one per application instance, with a global broker lane until stronger isolation is proven. Initial queue cap: 8 active/queued jobs per execution device. Return `RESOURCE_LIMIT` above this cap. Status/help do not consume a native job slot.
- Initial automatic deadline: 180 seconds per recipe excluding `needs_input` time; each native command also has a recorded finite timeout. A reached deadline with an in-flight call is an unknown/cancellation-requested outcome until verified, not a licence to kill the application.
- Idle document lease: 30 minutes, refreshed by successful authorized interaction. Lease expiry releases ownership but does not close an unsaved user document or delete artifacts. Continuation after expiry can reopen the last verified artifact into a new isolated binding only after explicit state checks; otherwise return `REVISION_CONFLICT` with recovery guidance.
- Live job storage is outside cloud sync. Default scratch cap: 1 GiB and 7 days for verified inactive diagnostic scratch only. Never evict active/unknown-outcome jobs, the current runtime, a rollback version, user-selected deliverables or the only verified artifact copy. If retention cannot safely release enough space, fail `RESOURCE_LIMIT` with cleanup guidance.
- P0 retains a compact durable idempotency ledger and tombstones without automatic expiry. Never forget a known key and rerun its mutation after scratch eviction. Initial ledger cap: 16 MiB; when full, stop new submissions with `RESOURCE_LIMIT` and require an explicit retention/contract decision. No issued-at/expiry field is assumed by the current wire schema. Future expiry requires defined replay protection and separately validated migration before old records can be removed.

These are initial bounded implementation policies, not measured performance or guarantees of automatic disk reclamation. Report actual resource use and revise by versioned policy only when evidence justifies it.
