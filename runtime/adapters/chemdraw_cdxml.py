"""CDXML materialization and native-geometry readback for generic mechanisms."""
from __future__ import annotations
import copy,json,math,hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
from runtime.chemical_ir import connected_components,linear_order,edge,canonical_hash

ELEMENTS={'H':1,'C':6,'N':7,'O':8}

def chemical_colors(mechanism):
    states,transitions=linear_order(mechanism);catalog={a['map']:a for a in mechanism['atom_catalog']}
    initial={}
    for i,a in catalog.items():
        state_roles=[];flow_roles=[]
        for s in states:
            q={x['atom']:x['value'] for x in s['formal_charges']};lp={x['atom']:x['count'] for x in s['lone_pairs']}
            state_roles.append((q.get(i,0),lp.get(i,0),sorted(b['order'] for b in s['bonds'] if i in b['atoms'])))
        for t in transitions:
            roles=[]
            for f in t['electron_flows']:
                for side in ('source','target'):
                    p=f[side]
                    if p.get('atom')==i or i in p.get('atoms',[]):roles.append((side,p['type'],p.get('electrons',''),p.get('pair_index',-1)))
            flow_roles.append(sorted(roles))
        initial[i]=(a['element'],a['implicit_h'],state_roles,flow_roles)
    colors={i:canonical_hash(v) for i,v in initial.items()}
    for _ in range(min(len(catalog),8)):
        new={}
        for i in catalog:
            neighborhoods=[]
            for s in states:
                neighborhoods.append(sorted((b['order'],colors[next(j for j in b['atoms'] if j!=i)]) for b in s['bonds'] if i in b['atoms']))
            new[i]=canonical_hash((initial[i],neighborhoods))
        colors=new
    return colors

def kekule_orders(state,catalog):
    """Solve valence demands for supported all-carbon aromatic subgraphs."""
    aromatic=[b for b in state['bonds'] if b['order']==1.5]
    result={edge(b['atoms']):b['order'] for b in state['bonds']}
    if not aromatic:return result
    involved=set(i for b in aromatic for i in b['atoms'])
    if any(catalog[i]['element']!='C' for i in involved):raise ValueError('Aromatic heteroatom conversion is not qualified')
    need={i:4-catalog[i]['implicit_h']-sum(b['order'] if b['order']!=1.5 else 1 for b in state['bonds'] if i in b['atoms']) for i in involved}
    chosen={}
    def solve(index):
        if index==len(aromatic):return all(v==0 for v in need.values())
        a,b=aromatic[index]['atoms']
        for extra in (0,1):
            if need[a]<extra or need[b]<extra:continue
            need[a]-=extra;need[b]-=extra;chosen[edge((a,b))]=1+extra
            if solve(index+1):return True
            need[a]+=extra;need[b]+=extra
        return False
    if not solve(0):raise ValueError('No supported aromatic valence assignment')
    result.update(chosen);return result

def document(style):
    root=ET.Element('CDXML',{'CreationProgram':'ChemDraw Companion experimental adapter','LabelFont':'3','CaptionFont':'3','LabelSize':str(style['font_pt']),'CaptionSize':str(style['font_pt']),'LabelFace':'96','CaptionFace':'0','BondLength':str(style['bond_length_pt']),'BondSpacing':'18','LineWidth':str(style['stroke_pt']),'BoldWidth':str(style['stroke_pt']*3.3),'HashSpacing':str(style['bond_length_pt']*.1736),'MarginWidth':str(style['bond_length_pt']*.111),'ShowAtomNumber':'no','ShowTerminalCarbonLabels':'yes','color':'0','bgcolor':'1'})
    colors=ET.SubElement(root,'colortable')
    for c in (1,0):ET.SubElement(colors,'color',{'r':str(c),'g':str(c),'b':str(c)})
    fonts=ET.SubElement(root,'fonttable');ET.SubElement(fonts,'font',{'id':'3','charset':'iso-8859-1','name':style['font_family']})
    w=style['canvas_width_mm']*72/25.4;h=style['canvas_height_mm']*72/25.4
    page=ET.SubElement(root,'page',{'id':'1','BoundingBox':f'0 0 {w:.4f} {h:.4f}','DrawingSpace':'poster','WidthPages':'1','HeightPages':'1'})
    return root,page

def seed_documents(mechanism,style,folder):
    folder.mkdir(parents=True,exist_ok=False);catalog={a['map']:a for a in mechanism['atom_catalog']};colors=chemical_colors(mechanism);states,_=linear_order(mechanism);manifest=[];B=style['bond_length_pt']
    for index,state in enumerate(states):
        root,page=document(style);ids={};positions={};ordered=sorted(catalog,key=lambda i:colors[i]);groups=connected_components(state,ordered)
        groups.sort(key=lambda g:(-len(g),tuple(sorted(colors[i] for i in g))))
        for ci,group in enumerate(groups):
            order=sorted(group,key=lambda i:colors[i]);radius=max(B,B*len(order)/(2*math.pi));center=(B*8+ci*B*8,B*8)
            for j,i in enumerate(order):a=2*math.pi*j/len(order);positions[i]=(center[0]+radius*math.cos(a),center[1]+radius*math.sin(a))
        for relation in mechanism['stereo_constraints']:
            if state['id'] not in relation['states']:continue
            a,b=relation['central_bond'];x,y=relation['substituent_atoms'];origin=positions[a];vertical=B*math.sqrt(3)/2
            positions[b]=(origin[0]+B,origin[1]);positions[x]=(origin[0]-B/2,origin[1]-vertical);positions[y]=(origin[0]+B*1.5,origin[1]+vertical*(1 if relation['type']=='anti_across_double_bond' else -1))
            # Define both substituent sectors at each double-bond endpoint.
            # Constraining only one substituent leaves a geometrically
            # contradictory seed when the other happens to be on the same side.
            for center,partner,chosen,dx,side in ((a,b,x,-B/2,1),(b,a,y,B/2,-1 if relation['type']=='anti_across_double_bond' else 1)):
                others=[j for bond in state['bonds'] if center in bond['atoms'] for j in bond['atoms'] if j not in (center,partner,chosen)]
                if len(others)>1:raise ValueError('Unsupported substituent multiplicity at stereo double bond')
                for other in others:positions[other]=(positions[center][0]+dx,positions[center][1]+side*vertical)
        q={x['atom']:x['value'] for x in state['formal_charges']};orders=kekule_orders(state,catalog);uid=10
        for group in groups:
            uid+=1;fragment=ET.SubElement(page,'fragment',{'id':str(uid)})
            for i in sorted(group,key=lambda i:colors[i]):
                uid+=1;ids[i]=str(uid);x,y=positions[i];attrs={'id':ids[i],'AtomNumber':str(i),'ShowAtomNumber':'no','p':f'{x:.4f} {y:.4f}','Element':str(ELEMENTS[catalog[i]['element']]),'NumHydrogens':str(catalog[i]['implicit_h'])}
                if q.get(i):attrs['Charge']=str(q[i])
                ET.SubElement(fragment,'n',attrs)
            for bond in state['bonds']:
                a,b=bond['atoms']
                if a in group:
                    uid+=1;ET.SubElement(fragment,'b',{'id':str(uid),'B':ids[a],'E':ids[b],'Order':str(orders[edge((a,b))])})
        name=f'state-{index:03d}.cdxml';ET.indent(root);ET.ElementTree(root).write(folder/name,encoding='utf-8',xml_declaration=True);manifest.append({'state':state['id'],'file':name})
    (folder/'geometry-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest

def read_geometry(mechanism,manifest,folder):
    catalog={a['map']:a for a in mechanism['atom_catalog']};states={s['id']:s for s in mechanism['states']};result={}
    for entry in manifest:
        path=folder/entry['file'];root=ET.parse(path).getroot();state=states[entry['state']];q={x['atom']:x['value'] for x in state['formal_charges']};nodes={int(n.get('AtomNumber','-1')):n for n in root.iter('n')}
        if set(nodes)!=set(catalog) or len(list(root.iter('n')))!=len(catalog):raise ValueError('Native atom mapping changed')
        ids={n.get('id'):i for i,n in nodes.items()};bonds=[];atoms={}
        for i,n in nodes.items():
            if int(n.get('Element',6))!=ELEMENTS[catalog[i]['element']] or int(n.get('Charge',0))!=q.get(i,0):raise ValueError('Native atom semantics changed')
            p=tuple(map(float,n.get('p').split()));label=None;t=n.find('t')
            if t is not None:
                anchor=tuple(map(float,t.get('p').split()));bounds=list(map(float,t.get('BoundingBox').split()))
                label={'offset':[anchor[0]-p[0],anchor[1]-p[1]],'bbox_offset':[bounds[0]-p[0],bounds[1]-p[1],bounds[2]-p[0],bounds[3]-p[1]],'runs':[{'text':s.text or '', 'face':s.get('face','0'),'size':float(s.get('size',8))} for s in t.findall('s')]}
            atoms[i]={'position':p,'label':label,'element':catalog[i]['element'],'charge':q.get(i,0),'implicit_h':catalog[i]['implicit_h']}
        actual={}
        for b in root.iter('b'):
            endpoints=(ids[b.get('B')],ids[b.get('E')]);o=float(b.get('Order',1));actual[edge(endpoints)]=o;bonds.append({'atoms':endpoints,'order':o,'display':b.get('Display','Solid')})
        expected={edge(b['atoms']):b['order'] for b in state['bonds']}
        if set(actual)!=set(expected) or any(actual[e]!=o and not(o==1.5 and actual[e] in (1,2)) for e,o in expected.items()):raise ValueError('Native bond graph changed')
        for i in catalog:
            if catalog[i]['element']=='C' and sum(o for e,o in actual.items() if i in e)+catalog[i]['implicit_h']!=4:raise ValueError('Native carbon valence changed')
        for relation in mechanism['stereo_constraints']:
            if state['id'] in relation['states'] and not stereo_satisfied(relation,{i:a['position'] for i,a in atoms.items()}):raise ValueError('Native seed/cleanup did not preserve specified stereo relation')
        result[state['id']]={'atoms':atoms,'bonds':bonds,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source':'ChemDraw native Clean(true) readback'}
    return result

def stereo_satisfied(relation,positions):
    a,b=relation['central_bond'];x,y=relation['substituent_atoms'];p,q=positions[a],positions[b];d=(q[0]-p[0],q[1]-p[1]);cross=lambda origin,t:d[0]*(t[1]-origin[1])-d[1]*(t[0]-origin[0]);product=cross(p,positions[x])*cross(q,positions[y])
    return product<0 if relation['type']=='anti_across_double_bond' else product>0

def materialize(scene,folder,stem='mechanism'):
    folder.mkdir(parents=True,exist_ok=False);root,page=document(scene['style']);uid=10
    def new_id():
        nonlocal uid;uid+=1;return str(uid)
    w=scene['width_pt'];h=scene['height_pt'];ET.SubElement(page,'graphic',{'id':new_id(),'GraphicType':'Rectangle','RectangleType':'Plain','BoundingBox':f'0 0 {w:.4f} {h:.4f}','color':'2','LineWidth':'0.01'})
    mapping={'states':[],'flows':[],'connectors':[]}
    for state in scene['states']:
        record={'id':state['id'],'atoms':{},'lone_pairs':[],'fragment_ids':[]}
        for component in state['components']:
            f=ET.SubElement(page,'fragment',{'id':new_id()});record['fragment_ids'].append(f.get('id'));ids={}
            for atom in component['atoms']:
                nid=new_id();ids[atom['map']]=nid;pos=atom['position'];attrs={'id':nid,'AtomNumber':str(atom['map']),'ShowAtomNumber':'no','p':f'{pos[0]:.4f} {pos[1]:.4f}','Element':str(ELEMENTS[atom['element']]),'NumHydrogens':str(atom['implicit_h'])}
                if atom['charge']:attrs['Charge']=str(atom['charge'])
                n=ET.SubElement(f,'n',attrs);record['atoms'][str(atom['map'])]={'native_id':nid,'position':pos}
                if atom['label']:
                    label=atom['label'];t=ET.SubElement(n,'t',{'p':f'{pos[0]+label["offset"][0]:.4f} {pos[1]+label["offset"][1]:.4f}'})
                    for run in label['runs']:ET.SubElement(t,'s',{'font':'3','size':str(run['size']),'color':'0','face':run['face']}).text=run['text']
            # ChemDraw accepts the CDXML enum token "2", but silently imports
            # the otherwise valid numeric string "2.0" as a single bond.
            for b in component['bonds']:ET.SubElement(f,'b',{'id':new_id(),'B':ids[b['atoms'][0]],'E':ids[b['atoms'][1]],'Order':format(b['order'],'g'),'Display':b['display']})
        for lp in state['lone_pairs']:
            x,y=lp['position'];nid=new_id();half=scene['style']['bond_length_pt']*.0764;ET.SubElement(page,'graphic',{'id':nid,'GraphicType':'Symbol','SymbolType':'LonePair','BoundingBox':f'{x-half} {y} {x+half} {y}'})
            record['lone_pairs'].append({**lp,'native_id':nid,'atom_native_id':record['atoms'][str(lp['atom'])]['native_id']})
        mapping['states'].append(record)
    for text in scene['texts']:
        n=ET.SubElement(page,'t',{'id':new_id(),'p':f'{text["position"][0]} {text["position"][1]}','InterpretChemically':'no'})
        ET.SubElement(n,'s',{'font':'3','size':str(text['font_pt']),'face':'0','color':'0'}).text=text['text']
    for flow in scene['flows']:
        p=flow['bezier'];points=[p[0],p[0],p[1],p[2],p[3],p[3]];nid=new_id();ET.SubElement(page,'curve',{'id':nid,'CurveType':'8','ArrowheadHead':'Full','ArrowheadType':'Solid','HeadSize':'650','HeadCenterSize':'550','HeadWidth':'220','LineWidth':str(scene['style']['stroke_pt']),'CurvePoints':' '.join(f'{v:.4f}' for q in points for v in q)})
        mapping['flows'].append({**flow,'native_id':nid})
    for connector in scene['connectors']:
        start,end=connector['path'];nid=new_id();ET.SubElement(page,'arrow',{'id':nid,'ArrowheadHead':'Full','ArrowheadType':'Solid','HeadSize':'900','ArrowheadCenterSize':'800','ArrowheadWidth':'250','Head3D':f'{end[0]} {end[1]} 0','Tail3D':f'{start[0]} {start[1]} 0','FillType':'None','LineWidth':str(scene['style']['stroke_pt'])});mapping['connectors'].append({**connector,'native_id':nid})
    ET.indent(root);ET.ElementTree(root).write(folder/(stem+'.cdxml'),encoding='utf-8',xml_declaration=True)
    (folder/(stem+'.mapping.json')).write_text(json.dumps(mapping,indent=2),encoding='utf-8');(folder/(stem+'.scene.json')).write_text(json.dumps(scene,indent=2),encoding='utf-8')
    return mapping
