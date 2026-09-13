"""Full-scene native colour-mask diagnostics, with named contact exemptions.

Reads original and colour-only native PNGs unchanged. It checks chemical and
drawable readback plus silhouette agreement before reporting clearances. Pixel
distance uses every nontransparent ink pixel (not glyph bounding boxes).
"""
import argparse,hashlib,itertools,json,math
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from verify_native_edits import equivalent


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def nums(v):return tuple(map(float,v.split()))


def records(path):
    root=ET.parse(path).getroot();result=[]
    fonts={}
    for font in root.iter('font'):
        if font.get('id') in fonts:raise ValueError('Duplicate font-table identity')
        fonts[font.get('id')]={k:v for k,v in font.attrib.items() if k!='id'}
    def family(identity):
        if identity not in fonts:raise ValueError('Unresolved native font identity: '+str(identity))
        return fonts[identity]
    # A colour-only copy must preserve the document's drawing/text defaults,
    # even where a currently explicit run does not inherit a particular one.
    defaults=('LabelFont','CaptionFont','LabelSize','CaptionSize','LabelFace','CaptionFace','LineWidth','BoldWidth','BondLength','BondSpacing','HashSpacing','MarginWidth','LabelJustification','CaptionJustification','ShowTerminalCarbonLabels','ShowNonTerminalCarbonLabels','HideImplicitHydrogens')
    style={k:family(root.get(k)) if k.endswith('Font') else root.get(k) for k in defaults if root.get(k) is not None}
    result.append(['document_defaults',style,None]);result.append(['fonttable',sorted(fonts.values(),key=lambda x:json.dumps(x,sort_keys=True)),None])
    parents={child:parent for parent in root.iter() for child in parent}
    def inherited(node,key,default=None):
        while node is not None:
            if node.get(key) is not None:return node.get(key)
            node=parents.get(node)
        return default
    keys={'n':['Element','Charge','NumHydrogens','Isotope','Radical','Geometry','BondOrdering','AtomNumber','p'],
          'b':['B','E','Order','Display','Display2','BS'],
          't':['p','BoundingBox','LabelAlignment','LabelJustification'],
          'curve':['CurvePoints','CurveType','ArrowheadHead','ArrowheadTail','ArrowheadType','HeadSize','ArrowheadCenterSize','ArrowheadWidth','LineWidth','LineType','FillType'],
          'graphic':['GraphicType','SymbolType','BoundingBox','LineWidth','LineType','FillType'],
          'arrow':['Head3D','Tail3D','ArrowheadHead','ArrowheadTail','ArrowheadType','HeadSize','ArrowheadCenterSize','ArrowheadWidth','LineWidth','LineType','FillType']}
    for n in root.iter():
        if n.tag not in keys or n.get('SupersededBy'):continue
        attrs={k:n.get(k) for k in keys[n.tag] if n.get(k) is not None}
        if n.tag in ('b','curve','graphic','arrow'):attrs['effective_line_width']=inherited(n,'LineWidth')
        if n.tag=='t':
            parent=parents[n];prefix='Label' if parent.tag=='n' else 'Caption'
            attrs['owner_atom']=parent.get('id') if parent.tag=='n' else None
            attrs['runs']=[{'text':s.text or '', 'font':family(s.get('font',inherited(s,prefix+'Font'))),'size':s.get('size',inherited(s,prefix+'Size')),'face':s.get('face',inherited(s,prefix+'Face','0'))} for s in n.findall('s')]
        for k in ('p','BoundingBox','CurvePoints','Head3D','Tail3D'):
            if k in attrs:attrs[k]=[round(v,2) for v in nums(attrs[k])]
        if n.tag not in ('arrow','s','t'):attrs['id']=n.get('id')
        result.append([n.tag,attrs,None])
    return result


def same_records(a,b):
    unmatched=list(b)
    for record in a:
        found=next((i for i,x in enumerate(unmatched) if equivalent(record,x)),None)
        if found is None:return False
        unmatched.pop(found)
    return not unmatched


def mixed_contact_evidence(points,rgb,palette,bounds_valid,groups,regions,tolerance=3.):
    """Resolve mixed ink only to a unique allowed pair of actual colours.

    Projection onto RGB line segments models source-over mixing of two native
    coloured primitives. Every plausible pair is retained; a third contributor
    or ambiguity fails closed. A circle alone never grants an exemption.
    """
    contributors=[set() for _ in points];candidates=[set() for _ in points]
    for i,j in itertools.combinations(range(len(groups)),2):
        a,b=palette[i].astype(float),palette[j].astype(float);delta=b-a;length=float(delta@delta)
        if not length:continue
        t=((rgb-a)@delta)/length;residual=np.linalg.norm(rgb-(a+t[:,None]*delta),axis=1)
        matched=(t>0)&(t<1)&(residual<=tolerance)&bounds_valid[:,i]&bounds_valid[:,j]
        for k in np.where(matched)[0]:
            pair=tuple(sorted((groups[i]['native_id'],groups[j]['native_id'])))
            candidates[k].add(pair);contributors[k].update(pair)
    unresolved=0;receipts={}
    for k,p in enumerate(points):
        pair=next(iter(candidates[k])) if len(candidates[k])==1 and len(contributors[k])==2 else None
        allowed=[r for r in regions if pair==tuple(sorted(r['objects'])) and float(np.sum((p-r['center'])**2))<=r['radius_px']**2]
        if not allowed:unresolved+=1
        key=(tuple(sorted(contributors[k])),tuple(sorted(candidates[k])),tuple(sorted(r['name'] for r in allowed)))
        if key not in receipts:receipts[key]={'contributor_object_ids':list(key[0]),'candidate_object_pairs':[list(v) for v in key[1]],'allowed_contacts':list(key[2]),'pixels':0,'exempted':bool(allowed),'contributor_colours':{g['native_id']:g['rgb'] for g in groups if g['native_id'] in key[0]}}
        receipts[key]['pixels']+=1
    return unresolved,list(receipts.values())


def neighbours(mask):
    padded=np.pad(mask,1);h,w=mask.shape
    return np.logical_or.reduce([padded[y:y+h,x:x+w] for x in range(3) for y in range(3)])


def frame_transform(rgba,canvas):
    rgb=rgba[:,:,:3];alpha=rgba[:,:,3].astype(float);h,w=alpha.shape
    white=(rgb.min(axis=2)>250)&(alpha>0)
    def centroid(region,axis):
        yy,xx=np.where(white&region);weight=alpha[yy,xx]
        if not len(weight):raise ValueError('Native white canvas frame missing')
        return float(np.sum((xx if axis==0 else yy)*weight)/np.sum(weight))
    yy,xx=np.indices((h,w));left=centroid((xx<w*.1)&(yy>h*.2)&(yy<h*.8),0);right=centroid((xx>w*.9)&(yy>h*.2)&(yy<h*.8),0)
    top=centroid((yy<h*.1)&(xx>w*.2)&(xx<w*.8),1);bottom=centroid((yy>h*.9)&(xx>w*.2)&(xx<w*.8),1)
    return (left,top),((right-left)/canvas[0],(bottom-top)/canvas[1])


def min_distance(a,b):
    # Chunk the pairwise calculation, bounding temporary memory independently
    # of the entire page dimensions or number of primitives.
    minimum=float('inf')
    for start in range(0,len(a),128):
        for other in range(0,len(b),2048):
            delta=a[start:start+128,None,:].astype(float)-b[None,other:other+2048,:]
            minimum=min(minimum,float(np.min(np.sum(delta*delta,axis=2))))
    return math.sqrt(minimum)


def verify(stem,source,inputs,native,composition):
    metadata=json.loads((inputs/(stem+'.mask-map.json')).read_text());scene=json.loads((composition/(stem+'.scene.json')).read_text());groups=metadata['groups'];issues=[]
    original=source/(stem+'.cdxml');readback=native/(stem+'.cdxml')
    if sha(original)!=metadata['source_sha256'] or sha(inputs/(stem+'.cdxml'))!=metadata['input_sha256']:issues.append('source_or_input_hash')
    try:readback_equal=same_records(records(original),records(readback))
    except (KeyError,ValueError):readback_equal=False
    if not readback_equal:issues.append('colour_copy_changed_chemical_or_drawable_readback')
    src=np.array(Image.open(source/(stem+'.png')).convert('RGBA'));dst=np.array(Image.open(native/(stem+'.png')).convert('RGBA'))
    if src.shape!=dst.shape:raise ValueError('Native canvas mismatch')
    canvas=[v*72/25.4 for v in scene['canvas_mm']];origin,scale=frame_transform(dst,canvas);B=scene['style']['bond_pt']
    ink=lambda a:(a[:,:,3]>=8)&(a[:,:,:3].min(axis=2)<240)
    src_ink,dst_ink=ink(src),ink(dst);union=int(np.count_nonzero(src_ink|dst_ink));mismatch=int(np.count_nonzero(src_ink^dst_ink));fraction=mismatch/union
    # CDXML has 0.01 pt coordinate rounding. Every differing antialias pixel
    # must have original/native ink within one pixel, with identical readback
    # to 0.02 pt. No large missing region is excused by an aggregate percentage.
    nonlocal_pixels=int(np.count_nonzero((src_ink&~neighbours(dst_ink))|(dst_ink&~neighbours(src_ink))))
    if nonlocal_pixels:issues.append('full_scene_silhouette_mismatch')
    yy,xx=np.where(dst_ink);rgb=dst[yy,xx,:3].astype(np.float32);palette=np.array([g['rgb'] for g in groups],dtype=np.float32)
    root=ET.parse(original).getroot();nodes={n.get('id'):n for n in root.iter() if n.get('id')}
    point=lambda p:np.array([origin[k]+p[k]*scale[k] for k in (0,1)])
    atom_pixel={n.get('id'):point(nums(n.get('p'))) for n in root.iter('n')}
    distance=np.sum((rgb[:,None,:]-palette[None,:,:])**2,axis=2);bounds_valid=np.ones(distance.shape,dtype=bool)
    for i,g in enumerate(groups):
        n=nodes[g['native_id']]
        if g['kind']=='atom_label':box=nums(n.find('t').get('BoundingBox'))
        elif g['kind']=='b':
            p,q=(nums(nodes[k].get('p')) for k in g['atom_ends']);box=(min(p[0],q[0]),min(p[1],q[1]),max(p[0],q[0]),max(p[1],q[1]))
        elif n.get('BoundingBox'):box=nums(n.get('BoundingBox'))
        else:
            values=nums(n.get('CurvePoints')) if n.tag=='curve' else nums(n.get('Head3D'))[:2]+nums(n.get('Tail3D'))[:2]
            box=(min(values[::2]),min(values[1::2]),max(values[::2]),max(values[1::2]))
        low=point(box[:2])-2*max(scale);high=point(box[2:])+2*max(scale)
        # Bounds constrain colour decoding only. Collision distances below use
        # actual native ink pixels, including all antialias coverage.
        valid=(xx>=low[0])&(xx<=high[0])&(yy>=low[1])&(yy<=high[1]);distance[~valid,i]=np.inf;bounds_valid[:,i]=valid
    classes=distance.argmin(axis=1);residual=np.sqrt(distance.min(axis=1));undecodable=int(np.count_nonzero(~np.isfinite(residual)))
    if undecodable:issues.append('ink_outside_all_native_object_bounds')
    clouds=[];boxes=[]
    for i,g in enumerate(groups):
        cloud=np.column_stack((xx[classes==i],yy[classes==i]));clouds.append(cloud)
        if not len(cloud):issues.append('missing_native_mask:'+g['native_id']);boxes.append(None);continue
        boxes.append([int(cloud[:,0].min()),int(cloud[:,1].min()),int(cloud[:,0].max()),int(cloud[:,1].max())])
    components={c['id']:c for c in scene['components']};native_atom=lambda port:str(components[port['component']]['native_atom_bindings'][str(port['atom_map'])]['native_id'])
    flow_index={f['native_id']:f for f in scene['flows']};pair_by_component={(p['component'],p['atom_map'],p.get('pair_index',0)):p['native_id'] for p in scene.get('lone_pairs',[])}
    if len(pair_by_component)!=len(scene.get('lone_pairs',[])):raise ValueError('Duplicate lone-pair slot binding')
    native_tips=[]
    for i,g in enumerate(groups):
        if g['kind']!='curve':continue
        f=flow_index[g['native_id']];values=nums(nodes[g['native_id']].get('CurvePoints'));points=list(zip(values[::2],values[1::2]));end=np.array(points[-1]);control=np.array(points[-3]);direction=end-control;direction/=np.linalg.norm(direction);normal=np.array([-direction[1],direction[0]])
        cloud=(clouds[i]-np.array(origin))/np.array(scale);offset=cloud-end;along=offset@direction;across=np.abs(offset@normal)
        near=(along>-.1*B)&(along<.55*B)&(across<.08*B)
        if not np.any(near):issues.append('missing_visible_arrowhead_tip');continue
        reach=float(along[near].max());tip=end+reach*direction;target=f['target'];target_id=native_atom(target);target_node=nodes[target_id];label=target_node.find('t')
        if label is not None:
            bb=nums(label.get('BoundingBox'));deviation=math.hypot(max(bb[0]-tip[0],0,tip[0]-bb[2]),max(bb[1]-tip[1],0,tip[1]-bb[3]))
            if bb[0]<=tip[0]<=bb[2] and bb[1]<=tip[1]<=bb[3]:deviation=None
        else:deviation=abs(float(np.linalg.norm(tip-np.array(nums(target_node.get('p')))))-B/6)
        native_tips.append({'flow':f['id'],'native_id':g['native_id'],'head_extension_pt':reach,'visible_tip_native_pt':tip.tolist(),'target_port_deviation_pt':deviation,'head_size':nodes[g['native_id']].get('HeadSize'),'head_width':nodes[g['native_id']].get('ArrowheadWidth')})
        if deviation is None or deviation>B*.20:issues.append('visible_native_head_port:'+f['id'])
    contacts=[];contact_regions=[];failures=[];checks=0
    for i,j in itertools.combinations(range(len(groups)),2):
        a,b=groups[i],groups[j]
        if boxes[i] is None or boxes[j] is None:continue
        threshold=B*(.18 if a['kind'] in ('curve','arrow') or b['kind'] in ('curve','arrow') else .12);exempt=[];related_target=False
        if a['kind']=='b' and b['kind']=='b':
            for shared in set(a['atom_ends'])&set(b['atom_ends']):exempt.append(('bond_shared_atom',atom_pixel[shared],B*.35))
        for bond,label in ((a,b),(b,a)):
            if bond['kind']=='b' and label['kind']=='atom_label' and label['native_id'] in bond['atom_ends']:exempt.append(('bond_own_atom_label',atom_pixel[label['native_id']],B*.6))
        for curve,obj in ((a,b),(b,a)):
            if curve['kind']!='curve':continue
            flow=flow_index[curve['native_id']]
            src_port=flow['source'];target=flow['target']
            if src_port['type']=='lone_pair' and obj['native_id']==pair_by_component[(src_port['component'],src_port['atom_map'],src_port.get('pair_index',0))]:exempt.append(('declared_lone_pair_tail',point(flow['bezier'][0]),B*.20))
            if src_port['type']=='bond' and obj['kind']=='b':
                ends={str(components[src_port['component']]['native_atom_bindings'][str(k)]['native_id']) for k in src_port['atom_maps']}
                if ends==set(obj['atom_ends']):exempt.append(('declared_source_bond_tail',point(flow['bezier'][0]),B*.20))
            if target['type']=='atom':
                target_id=native_atom(target)
                if obj['kind']=='atom_label' and obj['native_id']==target_id:related_target=True
                if obj['kind']=='b' and target_id in obj['atom_ends']:exempt.append(('declared_acceptor_atom_port',atom_pixel[target_id],B*.22))
        if related_target:threshold=0 # Related head must still have a positive ink gap.
        radius=threshold*max(scale)+2
        ba,bb=boxes[i],boxes[j];lower=math.hypot(max(ba[0]-bb[2],bb[0]-ba[2],0),max(ba[1]-bb[3],bb[1]-ba[3],0))
        if lower>radius:continue
        pa,pb=clouds[i],clouds[j]
        for name,center,r in exempt:
            # Only a small neighbourhood of the declared contact is exempt.
            pa=pa[np.sum((pa-center)**2,axis=1)>(r*max(scale))**2];pb=pb[np.sum((pb-center)**2,axis=1)>(r*max(scale))**2]
            contacts.append({'objects':[a['native_id'],b['native_id']],'colours':[a['rgb'],b['rgb']],'name':name,'radius_pt':r})
            contact_regions.append({'objects':[a['native_id'],b['native_id']],'name':name,'center':center,'radius_px':r*max(scale)})
        if not len(pa) or not len(pb):continue
        # Reduce point clouds to the mutually reachable expanded rectangles.
        pa=pa[(pa[:,0]>=bb[0]-radius)&(pa[:,0]<=bb[2]+radius)&(pa[:,1]>=bb[1]-radius)&(pa[:,1]<=bb[3]+radius)]
        pb=pb[(pb[:,0]>=ba[0]-radius)&(pb[:,0]<=ba[2]+radius)&(pb[:,1]>=ba[1]-radius)&(pb[:,1]<=ba[3]+radius)]
        if not len(pa) or not len(pb):continue
        d=min_distance(pa,pb);gap=max(0,d-1.5)/max(scale);checks+=1
        if gap<threshold or related_target and d<=1.5:failures.append({'objects':[a['native_id'],b['native_id']],'kinds':[a['kind'],b['kind']],'conservative_ink_gap_pt':gap,'required_pt':threshold})
    if failures:issues.append('native_mask_clearance')
    mixed=residual>40;mixed_points=np.column_stack((xx[mixed],yy[mixed]))
    unresolved,contributor_evidence=mixed_contact_evidence(mixed_points,rgb[mixed],palette,bounds_valid[mixed],groups,contact_regions)
    if unresolved:issues.append('unclassified_native_ink_outside_named_contacts')
    ink_y,ink_x=np.where(src_ink);bbox=[int(ink_x.min()),int(ink_y.min()),int(ink_x.max()),int(ink_y.max())]
    result={'fixture':stem,'source_cdxml_sha256':sha(original),'original_native_png_sha256':sha(source/(stem+'.png')),'diagnostic_native_png_sha256':sha(native/(stem+'.png')),'status':'pass' if not issues else 'failed','issues':issues,'native_pixel_dimensions':[src.shape[1],src.shape[0]],'embedded_dpi':list(Image.open(source/(stem+'.png')).info.get('dpi',())),'native_canvas_frame_px_per_pt':scale,'native_canvas_origin_px':origin,'canvas_dpi':[v*72 for v in scale],'ink_resolution':'Must also retain independent native bond/ruler calibration; canvas padding alone is not acceptance','native_ink_bbox_px':bbox,'native_ink_bbox_mm':[(bbox[k]-origin[k%2])/scale[k%2]*25.4/72 for k in range(4)],'silhouette_difference_pixels':mismatch,'silhouette_difference_fraction':fraction,'nonlocal_silhouette_difference_pixels':nonlocal_pixels,'allowed_registration_px':1,'mixed_colour_pixels_in_named_contacts':len(mixed_points)-unresolved,'unclassified_ink_pixels':unresolved,'object_masks':len(groups),'close_pair_distance_checks':checks,'named_contact_exemptions':contacts,'clearance_failures':failures,'owner_physical_size_review':'pending','manual_active_correction_seconds':None}
    result['native_arrowhead_tips']=native_tips
    result['mixed_colour_contributors']=contributor_evidence
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--composition',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--stem',action='append');a=p.parse_args()
    if a.report.exists():raise FileExistsError(a.report)
    results=[verify(stem,a.source,a.inputs,a.native,a.composition) for stem in (a.stem or ('S1','R1','M1'))]
    a.report.write_text(json.dumps({'method':'Original and colour-only native PNG readback; no raster image rewritten','results':results},indent=2),encoding='utf-8');print(json.dumps([{'fixture':r['fixture'],'issues':r['issues'],'silhouette_difference_fraction':r['silhouette_difference_fraction'],'clearance_failures':r['clearance_failures']} for r in results]));raise SystemExit(0 if all(r['status']=='pass' for r in results) else 1)
