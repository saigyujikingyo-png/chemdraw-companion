# Corpus acquisition and rights

Status: acquisition policy and source shortlist, not an acquired dataset. Official source terms were checked on 13 September 2026. No datasets or source artwork were downloaded for this plan. Follow [the sample plan](CORPUS_SAMPLE_PLAN.md), the corpus contracts, and the shared development/storage rules.

## Acquisition order

1. Validate the mechanism, annotation, manifest, correction and split contracts using the three known proof inputs. These are ungraded prototypes; schema validity grants no gold status.
2. Prefer first-party native authoring for the 40 proposed gold references. Record the author, original-work declaration and permission to distribute each contribution. Author a new composition from reviewed chemistry; do not trace published artwork or treat a redraw as automatically free of source restrictions.
3. Select individual external records to fill a documented chemistry gap. Begin with identifiers and metadata; verify rights before retrieving the selected assets. Avoid bulk downloads, repository-wide data hydration and unnecessary dependencies.
4. Preserve the original acquired bytes and their SHA-256, then record every transformation and annotation separately. Keep active work outside cloud sync and publish only eligible, sanitized assets.

A database structure can seed a candidate. A paper can support a chemical interpretation. Neither supplies a human-approved native mechanism drawing merely by being cited.

## Sources and permitted roles

| Source or tool | Proposed use | Verified terms and boundary |
| --- | --- | --- |
| ChEBI | Preferred external molecular identifiers and selected structure records | ChEBI states its data remains CC BY 4.0. Retain accession, release, attribution and changes. [Official licence statement](https://www.ebi.ac.uk/about/news/updates-from-data-resources/chebi-2-0-launches/); [available data products](https://www.ebi.ac.uk/chebi/downloads). |
| PubChem | Secondary identity checks and selected structural records | Contributor terms can differ; do not label the whole database public domain. Record the contributing source and its current licence. [Official download/provenance guidance](https://pubchem.ncbi.nlm.nih.gov/docs/downloads). |
| Open Reaction Database | Selected reactant/product/condition records; independently reviewed mechanism annotations | Data and describing metadata are CC BY-SA 4.0; repository scripts and schema code have separate Apache-2.0 terms. Preserve applicable attribution and share-alike terms for derived data. [Official licence table](https://github.com/open-reaction-database/ord-data#license). |
| RDKit | Optional independent graph, valence and stereo checks | BSD-3-Clause software; retain required notices when distributing it. Its licence does not cover input datasets or certify mechanisms/native rendering. [Official licence](https://github.com/rdkit/rdkit/blob/master/license.txt). |
| PMC Open Access Subset | Citation-first discovery of mechanism references | Article terms vary; not all PMC content permits reuse. Use permitted retrieval services if acquisition is later required. [Official access and reuse guidance](https://pmc.ncbi.nlm.nih.gov/tools/openftlist/). |

## Per-asset rights and provenance

The manifest must connect sources, assets, rights and lineage. Record the canonical URL/accession, version or commit, retrieval date, author/contributor, byte hash, exact licence and scope, attribution, modifications, permission evidence and distribution eligibility. Unknown rights remain unresolved; retain a citation instead of admitting the asset to a distributable corpus.

Assess paper text, figures, supplementary CDX/CDXML, embedded resources and newly authored annotations separately. Check individual credit lines and exclusions; a paper's licence does not establish permission for every linked or embedded asset. A Creative Commons licence grants covered permissions subject to its terms, including attribution and indicating changes. [Official CC BY 4.0 terms](https://creativecommons.org/licenses/by/4.0/).

Rights clearance and quality are independent. AI-generated or toolkit-derived candidates remain separately labelled silver/mixed material until the required human reviews and native evidence exist. Record their producers and corrections; never erase their origin when promoting a reviewed version. Native software entitlement does not authorize redistribution of vendor binaries, templates or licensed third-party resources.
