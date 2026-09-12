"""Test-only S1/R1/M1 graph, object and disk comparison. Not a Composer."""
import argparse,json,math
from pathlib import Path
import xml.etree.ElementTree as ET

EXPECTED={
 'alanine':({1:(7,1),2:(6,0),3:(6,0),4:(6,0),5:(8,0),6:(8,-1)},{(1,2):1,(2,3):1,(2,4):1,(4,5):2,(4,6):1}),
 'hydroxide':({1:(8,-1)},{}),'bromomethane':({2:(6,0),3:(35,0)},{(2,3):1}),
 'methanol':({1:(8,0),2:(6,0)},{(1,2):1}),'bromide':({3:(35,-1)},{}),
}


def verify(scene,path):
    root=ET.parse(path).getroot();nodes={n.get('id'):n for n in root.iter() if n.get('id')};issues=[]
    for component in scene['components']:
        expected_atoms,expected_bonds=EXPECTED[component['kind']];local={}
        for label,data in component['native_atom_bindings'].items():
            atom=int(label);nid=data['native_id'];local[nid]=atom;n=nodes.get(nid)
            if n is None or (int(n.get('Element',6)),int(n.get('Charge',0)))!=expected_atoms[atom]:issues.append('atom:'+component['id']+':'+label)
        actual={tuple(sorted((local[b.get('B')],local[b.get('E')]))):float(b.get('Order',1)) for b in root.iter('b') if b.get('B') in local and b.get('E') in local}
        if actual!=expected_bonds:issues.append('bonds:'+component['id'])
    for caption in scene['captions']:
        if caption['text'] not in [''.join(s.text or '' for s in t.findall('s')) for t in root.iter('t')]:issues.append('caption:'+caption['text'])
    for f in scene['flows']:
        n=nodes.get(f['native_id'])
        if n is None or n.tag!='curve' or n.get('ArrowheadHead')!='Full' or len(n.get('CurvePoints','').split())!=12:issues.append('curve:'+f['id'])
    target_atoms=sum(len(c['native_atom_bindings']) for c in scene['components']);target_bonds=sum(len(EXPECTED[c['kind']][1]) for c in scene['components'])
    if len(list(root.iter('n')))!=target_atoms or len(list(root.iter('b')))!=target_bonds:issues.append('atom_bond_count')
    if len(list(root.iter('curve')))!=len(scene['flows']):issues.append('curve_count')
    wedges=[b.attrib for b in root.iter('b') if 'Wedge' in b.get('Display','') or 'WedgedHash' in b.get('Display','')]
    if scene['fixture']=='S1' and not wedges:issues.append('missing_stereo_wedge')
    if scene['fixture'] in ('R1','M1') and len(list(root.iter('arrow')))!=1:issues.append('step_arrow_count')
    return {'file':path.name,'graph_and_object_readback':'pass' if not issues else 'failed','issues':issues,'atom_count':target_atoms,'bond_count':target_bonds,'visible_stereo_wedges':len(wedges),'absolute_cip_assignment':'not_independently_established' if scene['fixture']=='S1' else 'not_applicable','quality_and_owner_review':'pending'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--composition',type=Path,required=True);p.add_argument('--native',type=Path,required=True);a=p.parse_args();results=[]
    for fixture in ('S1','R1','M1'):
        scene=json.loads((a.composition/(fixture+'.scene.json')).read_text(encoding='utf-8'))
        results.append({'fixture':fixture,'checks':[verify(scene,a.native/name) for name in (fixture+'.cdxml',fixture+'-cdx-readback.cdxml',fixture+'-cdxml-readback.cdxml')],'manual_active_correction_seconds':None})
    report={'results':results,'native_quality_acceptance':'pending_final_size_masks_and_owner_review'}
    (a.native/'small-fixture-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
