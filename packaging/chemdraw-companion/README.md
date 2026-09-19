# ChemDraw Companion diagnostic preview

This preview checks its installed package and reports capability limits. **Native
execution is frozen:** it cannot read, edit, render, save or close ChemDraw. It
requires no ChemDraw licence check, account login or scientific input.

Version 0.2.0-preview.2 accepts standard MCP request metadata used by Codex. The
older preview.1 rejected that metadata during discovery. An update preserves the
old version for recovery; metadata never enables native operations.

## Install on Windows x64

1. Obtain the reviewed release ZIP and check its published SHA-256.
2. Extract the complete ZIP into a new folder. Open `chemdraw-companion` and
   double-click **Install.cmd**.
3. The installer verifies the files, installs a separate version and performs a
   diagnostic self-check. Keep its receipt and the earlier version for rollback.
4. When you choose to connect Codex, double-click **Connect Codex.cmd** in the
   installed folder printed by the installer. Codex must already be installed.
5. Refresh the host connection when convenient, then ask: “Check ChemDraw
   Companion package status.” A new task may be needed to discover a new tool.

Python is included; no Git checkout, coding project or separate Python install is
needed. Installation uses the current user's local application-data directory and
does not request administrator rights. It preserves ChemAIst (`chemdraw-agent`),
ChemDraw, other plugins, credentials and user documents.

File installation, MCP registration, host discovery, a fresh host tool call and
native functionality are separate results. This preview can only establish the
first four, when each has its own evidence. It cannot establish native acceptance.
The exact source commit and bundled runtime provenance are in build-info.json.

## What runs

The host starts one diagnostic Python frontend, which stops on stdin EOF. There
are no services, startup tasks, network connections, jobs or native child processes.
The optional plugin manifest uses a synchronous PowerShell launch shim. The direct
Codex connector uses the supported `codex mcp` CLI and the same Python/server files.
No user configuration is edited by string replacement.

`chemdraw_companion_status` has no arguments. It returns a validated compact status
object and an equivalent text block. Package mismatch returns an error disposition;
it does not attempt repair or start ChemDraw. Historical native receipts are not
read or imported by this diagnostic tool.

## Recovery and removal

Reinstalling the same intact version is idempotent. A modified existing version is
preserved and refused. Failed staging files and receipts are retained for inspection.
Previous versions are never removed automatically. File rollback verifies the
selected prior version; restoring a host connection requires the matching owned
connection receipt. A file rollback alone does not claim the host has switched.

Use Codex's supported MCP removal command or connection UI for this exact entry
when intentionally removing it. Keep the version folders and receipts until the
connection is removed and no frontend uses them. Do not remove ChemAIst, vendor
software or unrelated state as part of this product's rollback.

## Compatibility and current limits

| Surface | Implemented entry | Acceptance |
| --- | --- | --- |
| Windows x64 | Bundled CPython 3.13.15 diagnostic runtime | Package and self-check require exact build evidence |
| Codex | Supported stdio MCP CLI adapter; optional plugin manifest | Fresh registered host call required separately |
| Other local stdio MCP hosts | Same server and schema | Not host-qualified by this preview |
| ChatGPT Chat / cloud Work / remote connectors | No connector in this package | Unsupported in this preview |
| ChemDraw native editing/rendering | Operational gate remains closed | Frozen; historical evidence remains PARTIAL |

Public source is MIT; included CPython and third-party terms are retained. See
LICENSE, THIRD_PARTY_NOTICES.md and LIFECYCLE_RECORD.md. No vendor binaries, private
coursework, licences, protected samples or native test data are distributed.
