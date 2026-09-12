"""Independent native-readback checks for the fixed M2 experiment."""
import argparse,json,math,hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def bezier(points,t):
    s=1-t;return tuple(s**3*points[0][k]+3*s*s*t*points[1][k]+3*s*t*t*points[2][k]+t**3*points[3][k] for k in (0,1))
def rect_distance(p,r):return math.hypot(max(r[0]-p[0],0,p[0]-r[2]),max(r[1]-p[1],0,p[1]-r[3]))

def verify(fixture,scene,path):
    root=ET.parse(path).getroot();byid={n.get('id'):n for n in root.iter() if n.get('id')};issues=[];semantic=[]
    catalog={a['map']:a for a in fixture['atom_catalog']};all_bindings={}
    for state,placed in zip(fixture['states'],scene['states']):
        charges={x['atom']:x['value'] for x in state['formal_charges']};local={}
        for key,data in placed['atoms'].items():
            atom=int(key);native=byid.get(data['native_id']);local[data['native_id']]=atom;all_bindings[data['native_id']]=(state['id'],atom)
            if native is None or native.tag!='n':issues.append(f'missing_atom:{state["id"]}:{atom}');continue
            actual={'map':atom,'element':int(native.get('Element',6)),'charge':int(native.get('Charge',0)),'number':native.get('AtomNumber')}
            if actual['element']!={'C':6,'N':7,'O':8,'H':1}[catalog[atom]['element']] or actual['charge']!=charges.get(atom,0) or actual['number']!=str(atom):issues.append(f'atom_semantics:{state["id"]}:{atom}')
            semantic.append((state['id'],actual))
        actual={tuple(sorted((local[b.get('B')],local[b.get('E')]))):float(b.get('Order',1)) for b in root.iter('b') if b.get('B') in local and b.get('E') in local}
        expected={tuple(sorted(b['atoms'])):float(b['order']) for b in state['bonds']}
        if set(actual)!=set(expected):issues.append('bond_inventory:'+state['id'])
        for pair,order in expected.items():
            got=actual.get(pair)
            if got!=order and not (order==1.5 and got in (1,2)):issues.append(f'bond_order:{state["id"]}:{pair}')
        for atom in catalog:
            bonds=sum(v for pair,v in actual.items() if atom in pair)
            if catalog[atom]['element']=='C' and abs(bonds+catalog[atom]['implicit_h']-4)>1e-4:issues.append(f'carbon_h_valence:{state["id"]}:{atom}')
            if catalog[atom]['element']=='H' and bonds!=1:issues.append(f'explicit_h:{state["id"]}:{atom}')
        semantic.append((state['id'],'bonds',sorted(actual.items())))
        for lp in placed['lone_pairs']:
            n=byid.get(lp['native_id'])
            if n is None or n.tag!='graphic' or n.get('SymbolType')!='LonePair':issues.append(f'lone_pair_loss:{state["id"]}:{lp["atom"]}:{lp["pair_index"]}')
        if placed['anti_geometry']:
            ps={i:tuple(map(float,byid[placed['atoms'][str(i)]['native_id']].get('p').split())) for i in (1,2,3,10)}
            d=(ps[2][0]-ps[1][0],ps[2][1]-ps[1][1]);cross=lambda a,b:d[0]*(b[1]-a[1])-d[1]*(b[0]-a[0])
            if cross(ps[1],ps[10])*cross(ps[2],ps[3])>=0:issues.append('anti_lost:'+state['id'])
    if len(list(root.iter('n')))!=126:issues.append('global_atom_inventory')
    if len(list(root.iter('b')))!=111:issues.append('global_bond_inventory')
    curve_deltas=[];clearance_failures=[]
    for flow in scene['flows']:
        n=byid.get(flow['native_id'])
        if n is None or n.tag!='curve':issues.append('curve_loss:'+flow['id']);continue
        values=list(map(float,n.get('CurvePoints','').split()));points=list(zip(values[::2],values[1::2]));p=flow['bezier'];want=[p[0],p[0],p[1],p[2],p[3],p[3]]
        delta=max((math.dist(a,b) for a,b in zip(points,want)),default=1e9) if len(points)==6 else 1e9;curve_deltas.append(delta)
        if delta>.02 or n.get('ArrowheadHead')!='Full':issues.append('curve_geometry:'+flow['id'])
        if flow.get('composer_diagnostics',{}).get('approx_min_ink_clearance_pt',999)<2.592:clearance_failures.append({'flow':flow['id'],'approx_clearance_pt':flow['composer_diagnostics']['approx_min_ink_clearance_pt'],'threshold_pt':2.592})
    if len(list(root.iter('curve')))!=15 or len(list(root.iter('arrow')))!=6:issues.append('curve_or_step_count')
    actual_text=[''.join(t.itertext()) for t in root.iter('t')]
    for text in scene['captions']:
        if text['text'] not in actual_text:issues.append('caption_loss:'+text['text'])
    # Native-computed glyph rectangles, with existing pixels left untouched.
    # An actual-mask overlap proof is a separate check, never inferred from bbox.
    related_label_hits=[]
    atom_boxes={nid:list(map(float,t.get('BoundingBox').split())) for nid,n in byid.items() if n.tag=='n' for t in n.findall('t') if t.get('BoundingBox')}
    for flow in scene['flows']:
        for nid,box in atom_boxes.items():
            sid,atom=all_bindings.get(nid,(None,None))
            if sid!=flow['source']['state']:continue
            minimum=min(rect_distance(bezier(flow['bezier'],i/100),box) for i in range(12,89))
            if minimum<.6:related_label_hits.append({'flow':flow['id'],'atom_occurrence':f'{sid}:{atom}','native_glyph_bbox_distance_pt':minimum})
    return {'file':path.name,'semantic_and_native_inventory':'pass' if not issues else 'failed','issues':issues,'chemical_fingerprint':digest(semantic),'curve_max_native_rounding_pt':max(curve_deltas,default=0),'composer_clearance_failures':clearance_failures,'native_glyph_bbox_contacts':related_label_hits,'complete_rendered_mask_acceptance':'unverified','owner_visual_review':'pending'}

def run(fixture,scene,folder):
    files=['M2.cdxml','M2-cdx-readback.cdxml','M2-cdxml-readback.cdxml']
    results=[verify(fixture,scene,folder/f) for f in files]
    image=Image.open(folder/'M2.png');ink=image.convert('RGBA');alpha=ink.getchannel('A');rgb=ink.convert('RGB').convert('L')
    from PIL import ImageChops
    mask=ImageChops.multiply(alpha,rgb.point(lambda x:255 if x<180 else 0))
    report={'fixture':fixture['fixture_id'],'native_results':results,'both_format_chemical_fingerprint_equal':len({r['chemical_fingerprint'] for r in results})==1,'native_png':{'pixels':image.size,'embedded_dpi':image.info.get('dpi'),'black_ink_bbox_pixels':mask.getbbox(),'target_canvas_mm':[170,230],'canvas_pixel_requirement_met':image.width>=4016,'ink_scale_acceptance':'requires separate native pixel calibration; canvas alone does not pass'},'manual_active_correction_seconds':None,'manual_edit_count':None,'human_review':'not_measured','P0_C':'failed_geometry_or_pending_required_controls'}
    (folder/'m2-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--fixture',type=Path,required=True);p.add_argument('--scene',type=Path,required=True);p.add_argument('--native',type=Path,required=True);a=p.parse_args()
    r=run(json.loads(a.fixture.read_text()),json.loads(a.scene.read_text()),a.native)
    print(json.dumps({'native_semantics':[x['semantic_and_native_inventory'] for x in r['native_results']],'clearance_failures':len(r['native_results'][0]['composer_clearance_failures']),'glyph_bbox_contacts':len(r['native_results'][0]['native_glyph_bbox_contacts']),'P0_C':r['P0_C']},indent=2))
