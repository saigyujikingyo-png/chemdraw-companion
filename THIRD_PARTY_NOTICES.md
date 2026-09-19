# Third-party notices

Original ChemDraw Companion source is licensed under the MIT license in LICENSE.
The bounded source ownership review is not a certification of every historical
research artifact. Existing attribution and historical evidence remain intact.

## Diagnostic preview runtime

The Windows x64 diagnostic package redistributes the unmodified official CPython
3.13.15 embeddable distribution. Its Python Software Foundation license and
included third-party terms are retained in runtime/LICENSE.txt. The upstream
archive is verified against the SHA-256 published on the official release page:

- https://www.python.org/downloads/release/python-31315/
- https://www.python.org/ftp/python/3.13.15/python-3.13.15-embed-amd64.zip
- SHA-256: d1f04d990aee1253d8569e8e5104e30fa9f5fa830899f14843448872d936a2cf

The diagnostic server itself uses only the Python standard library. It does not
bundle the native bridge, jsonschema, ChemDraw, vendor interop assemblies, licences,
private documents or protected samples. ChemDraw is proprietary software from
Revvity Signals Software; this independent project does not grant a vendor licence
or imply vendor endorsement.

## Development validation only

The lifecycle controller's explicit draft result validator uses jsonschema 4.25.1
(MIT), attrs 26.1.0 (MIT), jsonschema-specifications 2025.9.1 (MIT), referencing
0.37.0 (MIT), rpds-py 2026.6.3 (MIT), and PyYAML 6.0.3 (MIT, plugin manifest validation only). Those packages and their original notices
remain in the isolated development environment and downloaded wheel metadata;
they are not redistributed in the diagnostic preview. The Windows CPython 3.13
validation wheel hashes are pinned in requirements-lifecycle-win-py313.lock.
