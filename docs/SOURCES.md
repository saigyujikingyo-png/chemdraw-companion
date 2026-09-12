# Official sources and evidence ledger

Checked 2026-09-12. Documentation facts are not native execution results.

## Revvity

Official repository: https://github.com/Revvity/ChemDraw-AddIns . Observed master commit: `119dcb011d6c57edf773b1733539709ef6ba99b2`.

[API reference at that commit](https://github.com/Revvity/ChemDraw-AddIns/blob/119dcb011d6c57edf773b1733539709ef6ba99b2/Documentation/ChemDraw%20JavaScript%20API%20Reference%20Guide.pdf): JavaScript API Reference Guide 1.6, 29 pages, copyright 2024. Read PDF bytes: 2,347,839; SHA-256 `0401e87a3c41dd7e14e547d5ac88c423da4b22081b8c4d6693465535f0317454`. Implementation should fetch the pinned source and compare bytes before relying on it.

| Source page | Documented surface |
| --- | --- |
| 10 | `ChemDrawAPI.activeDocument`; `.version` means API version |
| 13-14 | `Document.addCDXML`, `getCDXML`; coordinate/style-bearing append |
| 14-15 | `Document.addCDXBase64Encoded`, `getCDXBase64Encoded` |
| 15-16 | `Document.addSMILES`, `addInChI`; native structure input candidates |
| 23-24 | `Document.getPNGBase64Encoded(options)` |
| 25 | `Window.close` closes the add-in container |
| 26-29 | Selection `getCDXML`, `getSVG`, `containsPartialStructure`, `isEmpty`, `onChange` |
| 29 | Image options: `transparent`, `scalePercent`, `borderSizeInPixels` |

The guide describes limited active-document access and preview images. It does not specify a stable document ID, atomic mutation/snapshot, document open/save/replace, cleanup, electron-arrow authoring or PDF export. Absence from this guide is not absence from every vendor interface. The repository requires a supporting product level; version detection alone is insufficient.

## University

[School of Chemistry software table](https://chem.ed.ac.uk/cto/student-support/computing-software), checked 2026-09-12: ChemDraw and MNova appear with student entitlement and home/non-university-use availability. It does not identify all installed builds or SDK/module entitlements. Task-specific course/laboratory style requirements have not been supplied; no universal Edinburgh-format claim is made.

## Origin baseline and historical observations

Public design reference: [origin-agent-bridge at 85b6d333f09374913a66cd1b3e939719dc3a3639](https://github.com/saigyujikingyo-png/origin-agent-bridge/tree/85b6d333f09374913a66cd1b3e939719dc3a3639). The architecture task read the local matching commit's AGENTS, shared rules, retrospective and next-plugin assessment; local HEAD matched and working tree was clean before this work. The web tree reader returned a cache miss; local Git verification supplied baseline evidence.

The assessment records device-specific ChemDraw 26.0.0 and Mnova 17.0.41952 detection, with actual native feasibility untested. Existing ChemAIst quality was rejected by the owner. None of those observations establish today's licence or native execution on either device. No Origin or ChemAIst acceptance is inherited here.

## Mnova alternative

[Mestrelab Python scripting guide](https://mestrelab.com/resources/mnova-python-the-holy-grail-of-automation.html) describes native scripting workflows. [Mnova 17 changelog](https://support.mestrelab.com/kb/article/567-what-s-new-in-mnova-17-changelog/) lists Python 3.11 and additional phase, multiplet, assignment and integral functions. Both were read on 2026-09-12. Installed module permission and an executed workflow remain separate tests.

## Evidence status at architecture handoff

- Shared principles 2026-09-12.4: read; matching source copy carried into this repository.
- Official API guide: read and source hash recorded.
- Schemas/examples: design artifacts; validation results recorded separately.
- Native execution, safe document binding, rendering/quality, editable disk reopen: unverified.
- Actual host/model, artifact receipt, installer/update, release: unverified.
- Owner acceptance of proposed samples/style: pending.

## M2 Beckmann Snake sources and limits (2026-09-12)

- [Fernandez et al., PCCP 2009, DOI 10.1039/B816276J](https://pubs.rsc.org/en/content/articlehtml/2009/cp/b816276j): directly describes anti-phenyl migration from acetophenone oxime to acetanilide; its specific solid-acid conditions can also give isomerization/by-products. It supports the migration constraint, not a claim that our acid/water model reproduces those experiments.
- [ETH Industrial Chemistry, Lecture 10, page 14](https://ethz.ch/content/dam/ethz/special-interest/chab/icb/van-bokhoven-group-dam/coursework/Industrial%20Chemistry%20%28529-0192-00L%29/Spring2019/van_Bokhoven_JA_Lecture_10.pdf#page=14): original teaching material for the rearrangement/water-addition/imidic-acid/amide pathway; downloaded and visually inspected by the scientific reviewer. The seven-state explicit proton-transfer expansion is this project's test design, not seven experimentally observed intermediates.
- [Gregory, Moodie and Schofield, 1970](https://pubs.rsc.org/en/content/articlepdf/1970/j2/j29700000338): concentrated-sulfuric-acid mechanisms can involve activated oxime derivatives; our fixture deliberately makes no exact strong-acid condition claim.

The fixture excludes E/Z isomerization and side reactions. Its water/proton maps track one synthetic teaching path, not a unique experimental isotope provenance. No yield, kinetics, actual course requirement or universal mechanism coverage is asserted.
