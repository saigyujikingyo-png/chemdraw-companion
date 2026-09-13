"""Reaction-independent packing and electron-flow geometry for linear IRs.

The only coordinates read are intrinsic, freshly measured fragment geometry.
No fixture oracle, state-name branch, molecule template or page cache exists.
"""
from __future__ import annotations
import copy,itertools,math,textwrap
from runtime.chemical_ir import connected_components,linear_order,canonical_hash,chemical_colors
from runtime.arrow_ports import atom_ports

RULE_VERSION='generic-composer/0.3-development'
RULES={'panel_gap_bonds':1.7,'component_gap_bonds':.8,'electron_radius_bonds':.55,'curve_clearance_bonds':.18,'label_clearance_bonds':.12,'maximum_aux_permutation':5,'curve_bends_bonds':[.55,.9,1.4,1.95,2.5]}

def add(p,q):return (p[0]+q[0],p[1]+q[1])
def mul(v,s):return (v[0]*s,v[1]*s)
def vec(p,q):return (q[0]-p[0],q[1]-p[1])
def unit(v):
    d=math.hypot(*v);return (v[0]/d,v[1]/d) if d else (1,0)
def middle(a,b):return ((a[0]+b[0])/2,(a[1]+b[1])/2)
def curve_point(p,t):
    s=1-t;return tuple(s**3*p[0][k]+3*s*s*t*p[1][k]+3*s*t*t*p[2][k]+t**3*p[3][k] for k in (0,1))
def point_box_distance(p,b):return math.hypot(max(b[0]-p[0],0,p[0]-b[2]),max(b[1]-p[1],0,p[1]-b[3]))

def rotate_component(component,angle):
    c=copy.deepcopy(component);points=[a['position'] for a in c['atoms']];center=(math.fsum(p[0] for p in points)/len(points),math.fsum(p[1] for p in points)/len(points));co,si=math.cos(angle),math.sin(angle)
    for a in c['atoms']:
        dx,dy=vec(center,a['position']);a['position']=(center[0]+co*dx-si*dy,center[1]+si*dx+co*dy)
    return c

def component_bounds(component,padding):
    xs=[];ys=[]
    for a in component['atoms']:
        x,y=a['position'];reserve=padding if (a['label'] if 'atomic_number' in a else a['element'] in ('N','O')) else padding*.06;xs.extend((x-reserve,x+reserve));ys.extend((y-reserve,y+reserve))
        if a['label']:
            b=a['label']['bbox_offset'];xs.extend((x+b[0],x+b[2]));ys.extend((y+b[1],y+b[3]))
    return min(xs),min(ys),max(xs),max(ys)

def place_component(component,x,y,padding):
    result=copy.deepcopy(component);b=component_bounds(result,padding);dx,dy=x-b[0],y-b[1]
    for a in result['atoms']:a['position']=add(a['position'],(dx,dy))
    return result

def geometry_key(components):
    return tuple(sorted((a['chemical_role'],round(a['position'][0],7),round(a['position'][1],7)) for c in components for a in c['atoms']))


def canonical_pose(component):
    """Choose a rigid pose from labelled intrinsic geometry, without IDs.

    Every nonzero atom-pair axis is considered. A true geometric symmetry can
    exchange chemically equivalent atoms; it cannot choose a named atom/page.
    """
    points=[a['position'] for a in component['atoms']]
    angles={round(-math.atan2(q[1]-p[1],q[0]-p[0]),12) for p in points for q in points if math.dist(p,q)>1e-8}
    if not angles:return component
    candidates=[]
    for angle in sorted(angles):
        c=rotate_component(component,angle)
        center=tuple(math.fsum(a['position'][k] for a in c['atoms'])/len(c['atoms']) for k in (0,1))
        key=tuple(sorted((a['chemical_role'],round(a['position'][0]-center[0],6),round(a['position'][1]-center[1],6)) for a in c['atoms']))
        candidates.append((key,c))
    return min(candidates,key=lambda v:v[0])[1]


def prepare_components(state,measured,catalog,previous,roles):
    groups=connected_components(state,catalog);components=[]
    for group in groups:
        atoms=[{'map':i,'chemical_role':roles[i],**copy.deepcopy(measured['atoms'][i])} for i in group]
        atoms.sort(key=lambda a:(a['chemical_role'],*a['position']))
        bonds=[copy.deepcopy(b) for b in measured['bonds'] if b['atoms'][0] in group]
        components.append(canonical_pose({'atoms':atoms,'bonds':bonds,'source_sha256':measured['source_sha256']}))
    # Size and chemical properties choose a main component, never a named atom.
    signature=lambda c:(-sum(a['element']!='H' for a in c['atoms']),-len(c['atoms']),tuple(sorted(a['chemical_role'] for a in c['atoms'])))
    components.sort(key=signature)
    if previous:
        main=components[0];current={a['map']:a['position'] for a in main['atoms'] if a['element']!='H'};shared=set(current)&set(previous)
        if len(shared)>=2:
            pc=tuple(math.fsum(current[i][k] for i in shared)/len(shared) for k in (0,1));qc=tuple(math.fsum(previous[i][k] for i in shared)/len(shared) for k in (0,1))
            vectors=[(vec(pc,current[i]),vec(qc,previous[i])) for i in shared]
            dot=math.fsum(p[0]*q[0]+p[1]*q[1] for p,q in vectors);cross=math.fsum(p[0]*q[1]-p[1]*q[0] for p,q in vectors)
            components[0]=rotate_component(main,math.atan2(cross,dot))
    return components

def flow_endpoint(port,positions):
    return positions[port['atom']] if port['type'] in ('atom','lone_pair') else middle(*(positions[i] for i in port['atoms']))

def pack_panel(components,flows,width,B,label_height,step_height):
    pad=B*.62;gap=B*RULES['component_gap_bonds'];main=components[0];bounds=component_bounds(main,pad);mw,mh=bounds[2]-bounds[0],bounds[3]-bounds[1]
    if mw>width:raise ValueError('Measured main fragment exceeds panel width at the required bond/font scale')
    placed_main=place_component(main,(width-mw)/2,label_height+gap/2,pad);aux=components[1:];top=label_height+gap/2+mh+gap
    if not aux:return [placed_main],top+step_height
    choices=[]
    permutations=itertools.permutations(aux) if len(aux)<=RULES['maximum_aux_permutation'] else [tuple(aux)]
    for order in permutations:
        # Quarter-turn rigid rotations are chemistry-neutral; no reflection.
        rotations=itertools.product((0,math.pi/2,math.pi,3*math.pi/2),repeat=len(aux)) if len(aux)<=3 else [tuple(0 for _ in aux)]
        for angles in rotations:
            row=[];x=0;y=top;row_height=0;positioned=[placed_main]
            for c,angle in zip(order,angles):
                c=rotate_component(c,angle);b=component_bounds(c,pad);cw,ch=b[2]-b[0],b[3]-b[1]
                if cw>width:break
                if row and x+cw>width:
                    shift=(width-(x-gap))/2
                    for item in row:
                        for atom in item['atoms']:atom['position']=add(atom['position'],(shift,0))
                    positioned+=row;row=[];x=0;y+=row_height+gap;row_height=0
                item=place_component(c,x,y,pad);row.append(item);x+=cw+gap;row_height=max(row_height,ch)
            else:
                shift=(width-(x-gap))/2
                for item in row:
                    for atom in item['atoms']:atom['position']=add(atom['position'],(shift,0))
                positioned+=row;positions={a['map']:a['position'] for c in positioned for a in c['atoms']}
                distance=math.fsum(math.dist(flow_endpoint(f['source'],positions),flow_endpoint(f['target'],positions)) for f in flows)
                height=y+row_height+gap/2+step_height;choices.append((height*10+distance,positioned,height))
    if not choices:raise ValueError('Auxiliary inventory cannot fit at fixed style')
    _,positioned,height=min(choices,key=lambda t:(round(t[0],7),geometry_key(t[1])));return positioned,height

def lone_pair_ports(state,components,B,slots=None):
    atoms={a['map']:a for c in components for a in c['atoms']};positions={i:a['position'] for i,a in atoms.items()};result=[]
    selected={}
    if slots is not None:
        for slot in slots:selected.setdefault(slot['atom_ref'],{})[slot['pair_index']]=slot
    entries=state['lone_pairs'] if slots is None else [{'atom':i,'count':len(v)} for i,v in selected.items()]
    for entry in entries:
        i=entry['atom'];p=positions[i];occupied=[math.atan2(positions[j][1]-p[1],positions[j][0]-p[0]) for b in state['bonds'] if i in b['atoms'] for j in b['atoms'] if j!=i];chosen=[]
        for slot in (range(entry['count']) if slots is None else sorted(selected[i])):
            def radius(a):
                label=atoms[i]['label'];lower=B*RULES['electron_radius_bonds'];upper=B*1.1
                if not label:return lower
                box=label['bbox_offset'];u=(math.cos(a),math.sin(a));half=B*.0764
                axis=(-u[1],u[0]) if slots is not None else (1,0)
                def clearance(r):return min(point_box_distance((r*u[0]+side*half*axis[0],r*u[1]+side*half*axis[1]),box) for side in (-1,1))
                required=B*.18+B*.03
                if clearance(upper)<required:return float('inf')
                if clearance(lower)>=required:return lower
                for _ in range(30):
                    mid=(lower+upper)/2
                    if clearance(mid)<required:lower=mid
                    else:upper=mid
                return upper
            def score(a):return min(abs(math.atan2(math.sin(a-b),math.cos(a-b))) for b in occupied+chosen) if occupied+chosen else math.pi
            angles=[math.radians(d) for d in range(0,360,15) if math.isfinite(radius(math.radians(d)))]
            if not angles:raise ValueError('No lone-pair port outside measured label at fixed atom-association bound')
            angle=max(angles,key=lambda a:(round(score(a),10),-round(radius(a),7),-a));chosen.append(angle);r=radius(angle)
            position=add(p,(r*math.cos(angle),r*math.sin(angle)));result.append({'atom':i,'pair_index':slot,'position':position})
            if slots is not None:result[-1].update(**selected[i][slot],dot_axis=[-math.sin(angle),math.cos(angle)])
    return result

def route_flows(state,flows,components,pairs,B,head_extension=0,stroke=.6,pixel=.12):
    atoms={a['map']:a for c in components for a in c['atoms']};positions={i:a['position'] for i,a in atoms.items()};ports={(p['atom'],p['pair_index']):p['position'] for p in pairs};prior=[];result=[];threshold=B*RULES['curve_clearance_bonds']+stroke/2+pixel
    boxes={i:[a['position'][0]+a['label']['bbox_offset'][0],a['position'][1]+a['label']['bbox_offset'][1],a['position'][0]+a['label']['bbox_offset'][2],a['position'][1]+a['label']['bbox_offset'][3]] for i,a in atoms.items() if a['label']}
    # Routing priority derives from port geometry. Flow IDs and input order have
    # no layout meaning; indistinguishable routes may remain equivalent ties.
    def port_key(port):
        members=[port['atom']] if 'atom' in port else port['atoms']
        return (port['type'],port.get('electrons',''),port.get('pair_index',-1),tuple(sorted((atoms[i]['chemical_role'],*map(lambda x:round(x,7),positions[i])) for i in members)))
    ordered=sorted(flows,key=lambda f:(-round(math.dist(flow_endpoint(f['source'],positions),flow_endpoint(f['target'],positions)),7),port_key(f['source']),port_key(f['target'])))
    for f in ordered:
        source,target=f['source'],f['target'];start=ports[(source['atom'],source['pair_index'])] if source['type']=='lone_pair' else flow_endpoint(source,positions)
        if target['type']=='atom':
            i=target['atom'];ends=list(atom_ports(positions[i],boxes.get(i),B,head_extension))
        else:
            a,b=sorted(positions[i] for i in target['atoms']);direction=unit(vec(a,b));normal=(-direction[1],direction[0]);ends=[(add(middle(a,b),mul(normal,B*.15*s)),None,None) for s in (-1,1)]
        candidates=[]
        for end,outward,visible in ends:
            delta=vec(start,end);direction=unit(delta);normal=(-direction[1],direction[0])
            for side,bend,handle in itertools.product((-1,1),RULES['curve_bends_bonds'],(.5,1.,1.5) if outward is not None else (0,)):
                c1=add(add(start,mul(delta,.25)),mul(normal,B*bend*side));c2=add(end,mul(outward,B*handle)) if outward is not None else add(add(start,mul(delta,.75)),mul(normal,B*bend*side));points=[start,c1,c2,end];penalty=0;minimum=1e9;samples=[]
                for step in range(2,29):
                    point=curve_point(points,step/30);samples.append(point)
                    for box in boxes.values():d=point_box_distance(point,box);minimum=min(minimum,d);penalty+=max(0,threshold-d)**2
                    for bond in state['bonds']:
                        ends=bond['atoms']
                        if source['type']=='bond' and set(source['atoms'])==set(ends) and math.dist(point,start)<=B*.2:continue
                        if target['type']=='atom' and target['atom'] in ends and math.dist(point,positions[target['atom']])<=B*.22:continue
                        a,b=(positions[i] for i in ends);v=vec(a,b);den=v[0]**2+v[1]**2;t=max(0,min(1,((point[0]-a[0])*v[0]+(point[1]-a[1])*v[1])/den)) if den else 0
                        d=math.dist(point,add(a,mul(v,t)));penalty+=max(0,B*.18+stroke+pixel-d)**2
                    for old in prior:penalty+=max(0,threshold-min(math.dist(point,p) for p in old))**2*.4
                candidates.append((penalty+B*bend*.03,points,samples,minimum))
        score,points,samples,minimum=min(candidates,key=lambda c:(round(c[0],7),tuple(round(v,7) for p in c[1] for v in p)));prior.append(samples)
        result.append({'id':f['id'],'electron_count':f['electron_count'],'source':{'state':state['id'],**source},'target':{'state':state['id'],**target},'bezier':points,'diagnostics':{'native_label_bbox_clearance_pt':minimum,'required_clearance_pt':threshold,'route_score':score}})
        if 'lowered_ports' in f:result[-1]['lowered_ports']=copy.deepcopy(f['lowered_ports'])
    return result

def compose(mechanism,style,geometry,head_metrics=None,*,depiction_plan=None):
    from runtime.ir_v02_runtime import verify_runtime_plan
    verify_runtime_plan(mechanism,style,depiction_plan)
    states,transitions=linear_order(mechanism);catalog={a['map']:a for a in mechanism['atom_catalog']};outgoing={t['from']:t for t in transitions}
    depictions={s['state_ref']:s for s in depiction_plan['states']} if depiction_plan else {}
    slots_by_state={}
    if depiction_plan:
        # This is a geometry projection, never a replacement chemical IR.
        states=[{**s,'bonds':depictions[s['id']]['visible_bonds']} for s in states]
        outgoing={t['from']:{**t,'electron_flows':[]} for t in transitions}
        slots_by_state={sid:[{**s,'draw_lone_pair':True} for s in d['lone_pair_slots']] for sid,d in depictions.items()}
        for f in depiction_plan['electron_flows']:
            outgoing[f['state_ref']]['electron_flows'].append({'id':f['flow_ref'],'electron_count':f['electron_count'],'source':copy.deepcopy(f['source']['chemical_port']),'target':copy.deepcopy(f['sink']['chemical_port']),'lowered_ports':copy.deepcopy(f)})
            if f['source'].get('kind')=='virtual_lone_pair':
                p=f['source']['chemical_port'];slots=slots_by_state[f['state_ref']]
                if not any(s['atom_ref']==p['atom'] and s['pair_index']==p['pair_index'] for s in slots):slots.append({'atom_ref':p['atom'],'pair_index':p['pair_index'],'orientation':'auto','draw_lone_pair':False})
    B=style['bond_length_pt'];font=style['font_pt'];width=style['canvas_width_mm']*72/25.4;height=style['canvas_height_mm']*72/25.4;margin=style['outer_margin_mm']*72/25.4
    head_extension=0
    if head_metrics is not None:
        if head_metrics['bond_pt']!=B or head_metrics['font_pt']!=font or head_metrics['head_size']!='650':raise ValueError('Intrinsic head metric style mismatch')
        head_extension=head_metrics['conservative_forward_extension_pt']
        if not isinstance(head_extension,(int,float)) or not math.isfinite(head_extension) or not 0<=head_extension<=B:raise ValueError('Invalid intrinsic head extent')
    header=font*2.8;footer=font*1.5;column_gap=B*RULES['panel_gap_bonds'];row_gap=B*style['row_gap_bond_lengths'];available_width=width-2*margin;available_height=height-2*margin-header-footer
    prepared={};previous=None;roles=chemical_colors(mechanism)
    for state in states:
        visible_catalog={i:catalog[i] for i in geometry[state['id']]['atoms']} if depiction_plan else catalog
        cs=prepare_components(state,geometry[state['id']],visible_catalog,previous,roles);prepared[state['id']]=cs;previous={a['map']:a['position'] for a in cs[0]['atoms'] if a['element']!='H'}
    plan=None;rejections=[]
    for columns in range(min(style['max_columns'],len(states)),0,-1):
        rows=math.ceil(len(states)/columns)
        if rows-1<style['minimum_row_turns']:continue
        panel_width=(available_width-(columns-1)*column_gap)/columns
        packed=[]
        try:
            for state in states:
                # Character capacity is a shared preliminary estimate; native
                # glyph readback remains the final typography check.
                chars=max(6,int(panel_width/(font*.53)));label_lines=textwrap.wrap(state['label'],chars) or [''];transition=outgoing.get(state['id']);step_lines=textwrap.wrap(transition['label'],chars) if transition else []
                if depiction_plan:
                    label_lines=[];step_lines=[]
                    for caption in depictions[state['id']]['captions']:
                        destination=step_lines if 'transition_ref' in caption else label_lines
                        for line in textwrap.wrap(caption['text'],chars) or ['']:
                            destination.append({'text':line,'caption_ref':caption['occurrence_ref'],'role':caption['role'],'species_refs':caption.get('species_refs',[]),'original_text':caption['text']})
                label_height=(len(label_lines)+.4)*font*1.2;step_height=len(step_lines)*font*1.2
                components,panel_height=pack_panel(prepared[state['id']],transition['electron_flows'] if transition else [],panel_width,B,label_height,step_height)
                packed.append({'state':state,'components':components,'height':panel_height,'labels':label_lines,'step_labels':step_lines,'step_height':step_height})
            row_heights=[max(p['height'] for p in packed[i:i+columns]) for i in range(0,len(packed),columns)]
            total=sum(row_heights)+(rows-1)*row_gap
            if total>available_height:raise ValueError(f'Required physical height {total:.2f} exceeds {available_height:.2f} pt')
            plan=(columns,panel_width,packed,row_heights);break
        except ValueError as exc:rejections.append({'columns':columns,'reason':str(exc)})
    if plan is None:raise ValueError('No layout at the frozen font/bond scale: '+str(rejections))
    columns,panel_width,packed,row_heights=plan;scene={'scene_version':'mechanism-scene/0.1','rule_version':RULE_VERSION,'rules':RULES,'style':style,'mechanism_sha256':canonical_hash(mechanism),'width_pt':width,'height_pt':height,'states':[],'flows':[],'connectors':[],'texts':[],'layout_diagnostics':{'columns':columns,'row_heights_pt':row_heights,'rejected_plans':rejections},'source_geometry':'provided intrinsic geometry; native qualification is established by the adapter execution receipt, not asserted by Composer'}
    if depiction_plan:
        scene.update(scene_version='mechanism-scene/0.2',rule_version='generic-composer/0.4-v02-development',depiction_states=copy.deepcopy(depiction_plan['states']),chemical_inventory=copy.deepcopy(depiction_plan['chemical_inventory']))
        scene.update({k:depiction_plan[k] for k in ('ir_sha256','chemical_inventory_sha256','depiction_plan_sha256')})
    else:scene['texts'].append({'text':'Reaction mechanism','position':[margin,margin+font],'font_pt':font})
    if head_metrics is not None:scene['native_head_metrics']={k:head_metrics[k] for k in ('bond_pt','font_pt','head_size','conservative_forward_extension_pt','source_sha256')}
    origins={};sizes={};row_y=margin+header
    for row,start in enumerate(range(0,len(packed),columns)):
        left_to_right=(style['first_row_direction']=='left_to_right') == (row%2==0)
        row_entries=packed[start:start+columns]
        for logical,entry in enumerate(row_entries):
            column=logical if left_to_right else columns-1-logical;x=margin+column*(panel_width+column_gap);y=row_y;state=entry['state'];sid=state['id'];components=copy.deepcopy(entry['components'])
            for c in components:
                for a in c['atoms']:a['position']=add(a['position'],(x,y))
            pairs=lone_pair_ports(state,components,B,slots_by_state.get(sid) if depiction_plan else None);placed={'id':sid,'origin':[x,y],'row':row,'column':column,'components':components,'lone_pairs':[p for p in pairs if p.get('draw_lone_pair',True)],'native_source_sha256':geometry[sid]['source_sha256']};scene['states'].append(placed);origins[sid]=(x,y);sizes[sid]=(panel_width,row_heights[row])
            if depiction_plan:placed['virtual_lone_pair_ports']=[p for p in pairs if not p.get('draw_lone_pair',True)]
            for line,text in enumerate(entry['labels']):scene['texts'].append({**(text if isinstance(text,dict) else {'text':text}),'position':[x,y+(line+1)*font*1.2],'font_pt':font})
            for line,text in enumerate(entry['step_labels']):scene['texts'].append({**(text if isinstance(text,dict) else {'text':text}),'position':[x,y+entry['height']-entry['step_height']+(line+1)*font*1.2],'font_pt':font})
            if sid in outgoing:scene['flows']+=route_flows(state,outgoing[sid]['electron_flows'],components,pairs,B,head_extension,style['stroke_pt'],72/style['minimum_native_dpi'])
        row_y+=row_heights[row]+row_gap
    state_index={s['id']:s for s in scene['states']}
    for transition in transitions:
        source,target=state_index[transition['from']],state_index[transition['to']];sx,sy=source['origin'];tx,ty=target['origin'];sw,sh=sizes[source['id']]
        if source['row']==target['row']:
            level=max(sy,ty)+min(sh,sizes[target['id']][1])*.5
            if tx>sx:start,end=(sx+sw+B*.15,level),(tx-B*.15,level)
            else:start,end=(sx-B*.15,level),(tx+sw+B*.15,level)
            outer=False
        else:
            lane=width-margin*.5 if source['column']>=columns/2 else margin*.5;start,end=(lane,sy+sh),(lane,ty+font*2);outer=True
        scene['connectors'].append({'id':transition['id'],'from':source['id'],'to':target['id'],'path':[start,end],'outer_turn':outer})
    scene['stereo_checks']=[]
    for relation in mechanism['stereo_constraints']:
        a,b=relation['central_bond'];u,v=relation['substituent_atoms']
        for sid in relation['states']:
            positions={a['map']:a['position'] for c in state_index[sid]['components'] for a in c['atoms']};d=vec(positions[a],positions[b]);cross=lambda p,q:d[0]*(q[1]-p[1])-d[1]*(q[0]-p[0]);product=cross(positions[a],positions[u])*cross(positions[b],positions[v]);valid=product<0 if relation['type']=='anti_across_double_bond' else product>0
            if not valid:raise ValueError('Rigid composition lost a declared stereo relation')
            scene['stereo_checks'].append({'state':sid,'relation':relation['type'],'signed_product':product,'preserved':True})
    scene['layout_diagnostics']['curve_clearance_failures']=[f['id'] for f in scene['flows'] if f['diagnostics']['native_label_bbox_clearance_pt']<f['diagnostics']['required_clearance_pt']]
    return scene
