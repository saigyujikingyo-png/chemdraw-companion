"""Freeze 20 prospective P0-B controls from literal, independently stated chemistry.

This writes synthetic inputs only. It never opens native software, reads an
evaluation input, computes a valence model, or creates a native observation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from contracts.ir_v02 import ATOMIC_NUMBERS
from runtime.adapters.chemdraw_cdxml import document


def atom(role, element, h, charge=0, isotope=0, radical=0):
    return dict(role=role,element=element,non_node_attached_h=h,charge=charge,isotope=isotope,radical_electrons=radical)


def cases():
    A=atom
    rows=[
      ('methane','CH4',[A('c','C',4)],[],'observation_candidate'),
      ('ethanol','CH3-CH2-OH',[A('c1','C',3),A('c2','C',2),A('o','O',1)],[(0,1,1),(1,2,1)],'qualification_candidate'),
      ('ethylamine','CH3-CH2-NH2',[A('c1','C',3),A('c2','C',2),A('n','N',2)],[(0,1,1),(1,2,1)],'qualification_candidate'),
      ('label-field-conflict','Text CH4 conflicts with NumHydrogens=3',[A('c','C',None)],[],'conflict_negative'),
      ('acetone','CH3-C(=O)-CH3',[A('c1','C',3),A('carbonyl','C',0),A('o','O',0),A('c2','C',3)],[(0,1,1),(1,2,2),(1,3,1)],'qualification_candidate'),
      ('acetaldehyde','CH3-CH=O',[A('methyl','C',3),A('carbonyl','C',1),A('o','O',0)],[(0,1,1),(1,2,2)],'qualification_candidate'),
      ('acetic-acid','CH3-C(=O)-OH',[A('methyl','C',3),A('carbonyl','C',0),A('oxo','O',0),A('hydroxy','O',1)],[(0,1,1),(1,2,2),(1,3,1)],'qualification_candidate'),
      ('methyl-acetate','CH3-C(=O)-O-CH3',[A('c1','C',3),A('carbonyl','C',0),A('oxo','O',0),A('ester_o','O',0),A('c2','C',3)],[(0,1,1),(1,2,2),(1,3,1),(3,4,1)],'qualification_candidate'),
      ('acetamide','CH3-C(=O)-NH2',[A('methyl','C',3),A('carbonyl','C',0),A('o','O',0),A('n','N',2)],[(0,1,1),(1,2,2),(1,3,1)],'qualification_candidate'),
      ('ethene','CH2=CH2',[A('c1','C',2),A('c2','C',2)],[(0,1,2)],'qualification_candidate'),
      ('acetonitrile','CH3-C#N',[A('methyl','C',3),A('nitrile_c','C',0),A('n','N',0)],[(0,1,1),(1,2,3)],'qualification_candidate'),
      ('cyclohexane','Six saturated carbon ring atoms',[A('c'+str(i+1),'C',2) for i in range(6)],[(i,(i+1)%6,1) for i in range(6)],'qualification_candidate'),
      ('tetrahydrofuran','Four CH2 and one O in a saturated five-member ring',[A('c'+str(i+1),'C',2) for i in range(4)]+[A('o','O',0)],[(i,(i+1)%5,1) for i in range(5)],'qualification_candidate'),
      ('cyclopentanone','Five-member carbon ring with one exocyclic C=O',[A('carbonyl','C',0)]+[A('c'+str(i),'C',2) for i in range(1,5)]+[A('o','O',0)],[(i,(i+1)%5,1) for i in range(5)]+[(0,5,2)],'qualification_candidate'),
      ('carbon-deuterated-methanol','CH2D-OH; D is a separate node',[A('c','C',2),A('o','O',1),A('d','H',0,isotope=2)],[(0,1,1),(0,2,1)],'qualification_candidate'),
      ('explicit-h-d-formaldehyde','H-C(=O)-D; both H and D are separate nodes',[A('carbonyl','C',0),A('o','O',0),A('h','H',0),A('d','H',0,isotope=2)],[(0,1,2),(0,2,1),(0,3,1)],'qualification_candidate'),
      ('benzene-unqualified','Alternating six-member carbon ring; aromatic domain not qualified',[A('c'+str(i+1),'C',1) for i in range(6)],[(i,(i+1)%6,2 if i%2==0 else 1) for i in range(6)],'unsupported_negative'),
      ('methyl-radical-unqualified','Neutral CH3 doublet; radical domain not qualified',[A('c','C',3,radical=1)],[],'unsupported_negative'),
      ('ammonium','Isolated NH4+; label/API scopes must remain distinct',[A('n','N',4,charge=1)],[],'observation_candidate'),
      ('chloride','Isolated Cl-; unused valences must not supply H',[A('cl','Cl',0,charge=-1)],[],'observation_candidate'),
    ]
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    folder=parser.parse_args().out
    folder.mkdir(parents=True,exist_ok=False)
    style=dict(font_pt=8,font_family='Arial',bond_length_pt=14.4,stroke_pt=.6,canvas_width_mm=160,canvas_height_mm=100)
    matrix=[];geometry_manifest=[]
    for index,(name,description,atoms,bonds,kind) in enumerate(cases()):
        root,page=document(style);fragment=ET.SubElement(page,'fragment',dict(id='5'))
        maps=[101+17*i for i in range(len(atoms))]
        expected_atoms=[]
        for i,a in enumerate(atoms):
            position=f'{50+25*(i%4)} {60+25*(i//4)}'
            attrs=dict(id=str(100+i),NodeType='Element',AtomNumber=str(maps[i]),Element=str(ATOMIC_NUMBERS[a['element']]),
                       NumHydrogens=str(a['non_node_attached_h'] if a['non_node_attached_h'] is not None else 3),p=position)
            if a['charge']:attrs['Charge']=str(a['charge'])
            if a['isotope']:attrs['Isotope']=str(a['isotope'])
            if a['radical_electrons']:attrs['Radical']='Doublet'
            node=ET.SubElement(fragment,'n',attrs)
            if kind=='conflict_negative':
                label=ET.SubElement(node,'t',dict(id='500',p=position))
                ET.SubElement(label,'s',dict(font=root.get('LabelFont'),size='8',face='0')).text='CH4'
            explicit=[]
            for left,right,order in bonds:
                other=right if left==i else left if right==i else None
                if other is not None and atoms[other]['element']=='H':
                    explicit.append(dict(atom_map=maps[other],role=atoms[other]['role'],isotope=atoms[other]['isotope'],bond_order=order))
            expected_atoms.append(dict(atom_map=maps[i],**a,explicit_h_neighbor_nodes=explicit,
                                       expected_native_serialized_label_h='capture_presence_and_actual_value; not prefilled',
                                       source='literal prospective control chemistry, not native output or valence inference'))
        for i,(left,right,order) in enumerate(bonds):
            ET.SubElement(fragment,'b',dict(id=str(200+i),B=str(100+left),E=str(100+right),Order=str(order)))
        file=f'state-{index:03d}.cdxml'
        ET.indent(root);ET.ElementTree(root).write(folder/file,encoding='utf-8',xml_declaration=True)
        geometry_manifest.append(dict(state=name,file=file))
        matrix.append(dict(control=name,file=file,description=description,purpose=kind,
                           expected_atoms=expected_atoms,expected_bonds=[dict(atoms=[maps[a],maps[b]],order=o) for a,b,o in bonds],
                           seed_sha256=hashlib.sha256((folder/file).read_bytes()).hexdigest(),
                           source_conflict=dict(serialized_NumHydrogens='3',nested_label_text='CH4',resolved_expected_h=None) if kind=='conflict_negative' else None,
                           evidence_status='preregistered_not_native_executed'))
    payload=dict(version='p0b-native-semantic-control-matrix/0.1',baseline_runtime='bc428205a0066d7b544fe634910310d55fb3a893',
                 architecture_protocol='c29af27d429a2e8c9fd4c4e94e0eb0def6071837',controls=matrix,
                 no_private_candidate_or_target_input=True,no_model_inference=True,no_native_execution=True,
                 expectations='Independent literal chemical definitions. Labels/API/field presence after native execution are observations, not copied from these expectations.',
                 unsupported_domains=['aromatic','query','radical','abnormal_valence','unqualified_elements_or_encodings'],
                 query_and_abnormal_controls='Parser/guard negative unit fixtures only; no native chemical qualification is claimed for those domains.')
    for name,value in [('control-matrix.json',payload),('geometry-manifest.json',geometry_manifest),
                       ('seed-provenance.json',dict(scope='Preregistered synthetic controls; not a Composer seed receipt.',inputs=[dict(file=r['file'],sha256=r['seed_sha256']) for r in matrix]))]:
        (folder/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(controls=len(matrix),atoms=sum(len(c['expected_atoms']) for c in matrix),out=str(folder))))


if __name__=='__main__':main()
