"""Independent algorithmic native-H controls; no evaluation input or geometry.

Expected H is seed-only bookkeeping for synthetic graphs, never native readback.
Only saturated single-carbon monocycles with saturated carbon branches are
proposed positives. Every other profile is a deliberate capability negative.
"""
import argparse
import hashlib
import json
import math
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
    cases = [(f'saturated-cycle-{n}', n, 'plain', True) for n in range(3,9)]
    cases += [('single-carbon-branch',5,'branch',True),('two-carbon-branches',6,'gem',True),
              ('carbonyl-negative',5,'carbonyl',False),('unsaturation-negative',6,'alkene',False),
              ('alternating-cycle-negative',6,'aromatic',False),('multiple-cycle-negative',6,'chord',False),
              ('isotope-negative',4,'isotope',False),('charge-negative',4,'charge',False),
              ('radical-negative',4,'radical',False),('explicit-d-negative',4,'deuterium',False)]
    manifest, expected, inputs = [], {}, []
    for index,(name,n,variant,positive) in enumerate(cases):
        elements = [6]*n
        bonds = [(i,(i+1)%n,2 if (variant=='alkene' and i==0) or (variant=='aromatic' and i%2==0) else 1)
                 for i in range(n)]
        if variant=='chord': bonds.append((0,3,1))
        if variant in ('branch','gem','carbonyl','deuterium'):
            for _ in range(2 if variant=='gem' else 1):
                other=len(elements); elements.append(8 if variant=='carbonyl' else 1 if variant=='deuterium' else 6)
                bonds.append((0,other,2 if variant=='carbonyl' else 1))
        hydrogens = [4 if e==6 else 2 if e==8 else 1 for e in elements]
        for a,b,order in bonds:
            hydrogens[a]-=order;hydrogens[b]-=order
        if variant in ('charge','radical'): hydrogens[0]-=1
        root,page=document(style)
        fragment=ET.SubElement(page,'fragment',dict(id='5'))
        maps=[101+17*i for i in range(len(elements))]
        for i,element in enumerate(elements):
            angle=2*math.pi*i/n
            x,y=(90+35*math.cos(angle),90+35*math.sin(angle)) if i<n else (150,65+35*(i-n))
            values=dict(id=str(100+i),AtomNumber=str(maps[i]),Element=str(element),
                        NumHydrogens=str(hydrogens[i]),p=f'{x:.6f} {y:.6f}')
            if variant=='isotope' and i==0: values['Isotope']='13'
            if variant=='charge' and i==0: values['Charge']='1'
            if variant=='radical' and i==0: values['Radical']='Doublet'
            if variant=='deuterium' and element==1: values['Isotope']='2'
            ET.SubElement(fragment,'n',values)
        for i,(a,b,order) in enumerate(bonds):
            ET.SubElement(fragment,'b',dict(id=str(200+i),B=str(100+a),E=str(100+b),Order=str(order)))
        file=f'state-{index:03d}.cdxml'
        ET.indent(root); ET.ElementTree(root).write(folder/file,encoding='utf-8',xml_declaration=True)
        manifest.append(dict(state=name,file=file))
        expected[file]=dict(control=name,ring_size=n,variant=variant,cyclic_profile_expected=positive,
                            ring_atom_maps=maps[:n],seed_only_h={str(m):h for m,h in zip(maps,hydrogens)})
        inputs.append(dict(file=file,sha256=hashlib.sha256((folder/file).read_bytes()).hexdigest()))
    for name,value in [('geometry-manifest.json',manifest),('control-expected.json',expected),
                       ('seed-provenance.json',dict(scope='Independent synthetic native adapter controls, not a Composer seed receipt.',inputs=inputs))]:
        (folder/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(controls=len(cases),positives=sum(c[3] for c in cases),out=str(folder))))


if __name__=='__main__':
    main()
