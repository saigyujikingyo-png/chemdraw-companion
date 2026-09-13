"""Create independent synthetic native-H controls; no corpus or private IR.

Run native-ir-fragments.ps1 with -IncludeAtomReadback against the new folder.
These are adapter controls, not Composer requests or native-quality evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime.adapters.chemdraw_cdxml import document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    folder = parser.parse_args().out
    folder.mkdir(parents=True, exist_ok=False)
    style = dict(font_pt=8, font_family='Arial', bond_length_pt=14.4, stroke_pt=.6,
                 canvas_width_mm=160, canvas_height_mm=100)
    cases = [
        ('ethene', [(11,6,2),(27,6,2)], [(11,27,2)]),
        ('ethyne', [(11,6,1),(27,6,1)], [(11,27,3)]),
        ('fluoromethane', [(11,6,3),(27,9,0)], [(11,27,1)]),
        ('tetrafluorocarbon', [(11,6,0),(27,9,0),(43,9,0),(58,9,0),(90,9,0)],
         [(11,i,1) for i in (27,43,58,90)]),
        ('methane', [(11,6,4)], []),
        ('explicit-deuterium', [(11,6,2),(27,9,0),(81,1,0)], [(11,27,1),(11,81,1)]),
        ('explicit-hydrogen', [(11,6,2),(27,9,0),(81,1,0)], [(11,27,1),(11,81,1)]),
    ]
    manifest, expected, inputs = [], {}, []
    for index, (name, atoms, bonds) in enumerate(cases):
        root, page = document(style)
        fragment = ET.SubElement(page, 'fragment', {'id':'5'})
        native = {m:str(100+i) for i,(m,_,_) in enumerate(atoms)}
        for i,(m,element,h) in enumerate(atoms):
            values = dict(id=native[m], AtomNumber=str(m), Element=str(element),
                          NumHydrogens=str(h), p=f'{50+30*i} {60+15*(i%2)}')
            if name == 'explicit-deuterium' and element == 1:
                values['Isotope'] = '2'
            ET.SubElement(fragment, 'n', values)
        for i,(a,b,order) in enumerate(bonds):
            ET.SubElement(fragment, 'b', dict(id=str(200+i), B=native[a], E=native[b], Order=str(order)))
        file = f'state-{index:03d}.cdxml'
        ET.indent(root)
        ET.ElementTree(root).write(folder/file, encoding='utf-8', xml_declaration=True)
        manifest.append(dict(state=name,file=file))
        expected[file] = dict(control=name, unmapped_h={str(m):h for m,_,h in atoms},
                              fallback_eligible=name != 'methane')
        inputs.append(dict(file=file,sha256=hashlib.sha256((folder/file).read_bytes()).hexdigest()))
    for name, value in [('geometry-manifest.json',manifest),('control-expected.json',expected),
                        ('seed-provenance.json',dict(scope='Synthetic native adapter control only; not a Composer seed receipt.',inputs=inputs))]:
        (folder/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
    print(json.dumps(dict(controls=len(cases),out=str(folder))))


if __name__ == '__main__':
    main()
