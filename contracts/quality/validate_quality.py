"""Quality Oracle v1 bounded pixel metric prototype.

Recomputes ink from full object-layer PNGs and binds assets, semantic references
and calibration. It does not implement a trusted native layer exporter, automatic
occlusion recovery or human review authentication. No full native acceptance is
issued by this first prototype. Per-metric failures are useful even when evidence
coverage is incomplete. Synthetic controls never become native evidence.
"""
import argparse
from collections import deque
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import numpy as np
from PIL import Image
from common import require, read_json, parse_json_bytes, validate_schema, asset_bytes
from calibration import load_calibration

HERE = Path(__file__).resolve().parent
class Unmeasured(ValueError): pass

def unit(v):
    length=math.hypot(*v)
    if length<1e-8: raise Unmeasured("zero direction")
    return (v[0]/length,v[1]/length)

def sub(a,b): return (a[0]-b[0],a[1]-b[1])
def dot(a,b): return a[0]*b[0]+a[1]*b[1]
def cross(a,b): return a[0]*b[1]-a[1]*b[0]
def centroid(points):
    if not points: raise Unmeasured("empty pixel object")
    return (sum(p[0] for p in points)/len(points),sum(p[1] for p in points)/len(points))
def angle(v): return math.degrees(math.atan2(v[1],v[0]))
def angle_error(a,b,period=360): return abs((a-b+period/2)%period-period/2)

def image_ink(data):
    with Image.open(io.BytesIO(data)) as im:
        require(im.format=="PNG","oracle requires lossless PNG")
        require(im.width*im.height<=2000000,"prototype image size limit")
        rgba=np.array(im.convert("RGBA"),dtype=float)
    rgb=rgba[:,:,:3]*(rgba[:,:,3:4]/255)+255*(1-rgba[:,:,3:4]/255)
    ys,xs=np.where(np.min(rgb,axis=2)<245)
    points=set(zip(xs.tolist(),ys.tolist()))
    require(len(points)<=200000,"prototype ink count limit")
    return (rgba.shape[1],rgba.shape[0]),points

def components(points):
    remaining=set(points);result=[]
    while remaining:
        seed=remaining.pop();found={seed};queue=deque([seed])
        while queue:
            x,y=queue.popleft()
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    p=(x+dx,y+dy)
                    if p in remaining:remaining.remove(p);found.add(p);queue.append(p)
        result.append(found)
    return result

def boundary(points):
    return {p for p in points if any((p[0]+dx,p[1]+dy) not in points for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)])}

def pixel_distance(a,b):
    if not a or not b: raise Unmeasured("missing ink")
    if a & b:return 0.0
    aa=np.array(list(boundary(a)),dtype=float);bb=np.array(list(boundary(b)),dtype=float)
    if len(aa)*len(bb)>4000000:raise Unmeasured("prototype distance workload limit")
    best=float("inf")
    for i in range(0,len(aa),128):
        distances=np.sum((aa[i:i+128,None,:]-bb[None,:,:])**2,axis=2)
        best=min(best,float(np.min(distances)))
    return math.sqrt(best)

def hull(points):
    pts=sorted(points)
    if len(pts)<3:raise Unmeasured("head has insufficient pixels")
    lower=[];upper=[]
    for p in pts:
        while len(lower)>=2 and cross(sub(lower[-1],lower[-2]),sub(p,lower[-1]))<=0:lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper)>=2 and cross(sub(upper[-1],upper[-2]),sub(p,upper[-1]))<=0:upper.pop()
        upper.append(p)
    result=lower[:-1]+upper[:-1]
    # Fixed subpixel simplification of raster hull stair steps, not curve smoothing.
    changed=True
    while changed and len(result)>3:
        changed=False
        for i,p in enumerate(result):
            a=result[i-1];b=result[(i+1)%len(result)]
            distance=abs(cross(sub(p,a),sub(b,a)))/max(math.dist(a,b),1e-9)
            if distance<.8:result.pop(i);changed=True;break
    return result

def visible_tip(head):
    if len(components(head))!=1:raise Unmeasured("disconnected head or incomplete isolated head")
    vertices=hull(head);candidates=[]
    for i,p in enumerate(vertices):
        a=unit(sub(vertices[i-1],p));b=unit(sub(vertices[(i+1)%len(vertices)],p))
        candidates.append((math.degrees(math.acos(max(-1,min(1,dot(a,b))))),p))
    candidates.sort()
    if not candidates or candidates[0][0]>70:raise Unmeasured("no unique sharp apex")
    if len(candidates)>1 and candidates[1][0]-candidates[0][0]<5 and math.dist(candidates[0][1],candidates[1][1])>2:
        raise Unmeasured("ambiguous apex")
    return candidates[0][1]

def shaft_topology(shaft):
    if not shaft:raise Unmeasured("missing visible shaft")
    xs=[p[0] for p in shaft];ys=[p[1] for p in shaft];x0=min(xs)-2;y0=min(ys)-2
    a=np.zeros((max(ys)-y0+3,max(xs)-x0+3),dtype=bool)
    for x,y in shaft:a[y-y0,x-x0]=True
    # Bounded Zhang-Suen thinning; morphology is a topology guard, not tip truth.
    for iteration in range(512):
        changed=False
        for phase in (0,1):
            p2=np.roll(a,1,axis=0);p3=np.roll(p2,-1,axis=1);p4=np.roll(a,-1,axis=1)
            p5=np.roll(p4,-1,axis=0);p6=np.roll(a,-1,axis=0);p7=np.roll(p6,1,axis=1)
            p8=np.roll(a,1,axis=1);p9=np.roll(p8,1,axis=0)
            ring=[p2,p3,p4,p5,p6,p7,p8,p9,p2]
            neighbours=sum(x.astype(np.uint8) for x in ring[:-1])
            transitions=sum((~x & y).astype(np.uint8) for x,y in zip(ring,ring[1:]))
            if phase==0:guard=~(p2 & p4 & p6) & ~(p4 & p6 & p8)
            else:guard=~(p2 & p4 & p8) & ~(p2 & p6 & p8)
            remove=a & (neighbours>=2) & (neighbours<=6) & (transitions==1) & guard
            if np.any(remove):a[remove]=False;changed=True
        if not changed:break
    else:raise Unmeasured("shaft thinning budget")
    yy,xx=np.where(a);points={(int(x+x0),int(y+y0)) for x,y in zip(xx,yy)}
    require(points,"empty shaft skeleton")
    graph={}
    for x,y in points:
        adjacent=[]
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if not (dx or dy):continue
                if dx and dy and ((x+dx,y) in points or (x,y+dy) in points):continue
                if (x+dx,y+dy) in points:adjacent.append((x+dx,y+dy))
        graph[(x,y)]=adjacent
    ends=[p for p,n in graph.items() if len(n)==1]
    edges=sum(map(len,graph.values()))//2
    if len(ends)!=2 or any(len(n)>2 for n in graph.values()) or edges!=len(points)-1 or len(components(points))!=1:
        raise Unmeasured("visible shaft is closed, branched, self-crossing or topologically ambiguous")
    return ends

def visible_tail(arrow,head):
    require(head<=arrow,"head layer is not a subset of its arrow")
    if len(components(arrow))!=1:raise Unmeasured("branched/disconnected arrow cannot be qualified")
    shaft_topology(arrow-head)
    distances={p:0 for p in head};queue=deque(head)
    while queue:
        x,y=queue.popleft()
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                p=(x+dx,y+dy)
                if p in arrow and p not in distances:
                    distances[p]=distances[(x,y)]+1;queue.append(p)
    maximum=max(distances.values())
    if maximum<=2:raise Unmeasured("shaft too short")
    farthest={p for p,d in distances.items() if d>=maximum-1}
    if len(components(farthest))!=1:raise Unmeasured("ambiguous visible tail")
    return centroid(farthest)

def segment_distance(p,a,b):
    v=sub(b,a);den=dot(v,v)
    t=max(0,min(1,dot(sub(p,a),v)/den)) if den else 0
    return math.dist(p,(a[0]+t*v[0],a[1]+t*v[1]))

def polyline_samples(points,spacing=.75):
    required=sum(max(1,math.ceil(math.dist(a,b)/spacing)) for a,b in zip(points,points[1:]))+1
    require(required<=20000,"centerline workload limit before allocation")
    samples=[]
    for a,b in zip(points,points[1:]):
        n=max(1,math.ceil(math.dist(a,b)/spacing))
        samples.extend((a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n) for i in range(n))
    return samples+[tuple(points[-1])]

def maximum_status(value,error,threshold):
    if value-error>threshold:return "fail"
    if value+error<=threshold:return "pass"
    return "unmeasured"

def minimum_status(value,error,threshold):
    if value+error<threshold:return "fail"
    if value-error>=threshold:return "pass"
    return "unmeasured"

def combined(*values):
    return "fail" if "fail" in values else "unmeasured" if "unmeasured" in values else "pass"

def port_ref(port):
    field={"atom":"atom_ref","bond":"bond_ref","lone_pair":"lone_pair_ref","radical":"radical_ref"}.get(port["type"])
    if field is None:raise Unmeasured("prospective/composite port not implemented")
    return port[field]

def unique(rows):
    result={r["id"]:r for r in rows}
    require(len(result)==len(rows),"duplicate identity")
    return result

def evaluate(value,base_dir,reference_file):
    validate_schema("oracle.schema.json",value)
    policy_bytes=(HERE/"policy-v1.json").read_bytes()
    require(hashlib.sha256(policy_bytes).hexdigest()==value["policy_sha256"],"quality policy hash mismatch")
    policy=json.loads(policy_bytes);assets=unique(value["assets"])
    require(len(assets)<=500 and sum(a["bytes"] for a in assets.values())<=100000000,"prototype asset budget")
    data={key:asset_bytes(asset,base_dir) for key,asset in assets.items()}
    for field in ("native_receipt_asset_ref","annotation_review_asset_ref"):
        require(value["evidence"][field] is None or value["evidence"][field] in assets,"dangling provenance reference")
    require(value["render_asset_ref"] in data and value["ir_asset_ref"] in data,"missing source/IR")
    reference_bytes=Path(reference_file).read_bytes()
    require(hashlib.sha256(reference_bytes).hexdigest()==value["reference_sha256"],"independent reference hash mismatch")
    reference=parse_json_bytes(reference_bytes);validate_schema("reference.schema.json",reference)
    require(reference["ir_sha256"]==assets[value["ir_asset_ref"]]["sha256"],"reference IR binding mismatch")
    require(reference["pixels_per_pt"]==value["pixels_per_pt"],"independent frame scale mismatch")
    locked=unique(reference["measurements"])
    require(set(locked)=={m["id"] for m in value["measurements"]},"reference measurement inventory mismatch")
    for m in value["measurements"]:
        require(all(m.get(k)==v for k,v in locked[m["id"]].items()),"candidate altered locked reference: "+m["id"])
    expected_bindings=unique(reference["object_bindings"])
    require(set(expected_bindings)=={o["id"] for o in value["objects"]},"reference object inventory mismatch")
    for o in value["objects"]:
        require(all(o.get(k)==v for k,v in expected_bindings[o["id"]].items()),"reference object/semantic mapping mismatch")
    ir=parse_json_bytes(data[value["ir_asset_ref"]])
    sys.path.insert(0,str(HERE.parent/"corpus"))
    from validate_corpus import mechanism
    chemical=mechanism(ir)
    entities={r["id"]:r for rows in ir.values() if isinstance(rows,list) for r in rows if isinstance(r,dict) and "id" in r}
    flows={r["id"]:r for r in ir["electron_flows"]}
    objects=unique(value["objects"]);masks={}
    size,original=image_ink(data[value["render_asset_ref"]])
    for key,o in objects.items():
        require(o["state_ref"] in {s["id"] for s in ir["states"]},"object unknown state")
        require(set(o["semantic_refs"])<=set(entities),"object unknown semantic reference")
        dimensions,masks[key]=image_ink(data[o["asset_ref"]])
        require(dimensions==size,"object layer is not registered to original canvas")
        require(masks[key],"empty object layer")
        require(sum(len(points) for points in masks.values())<=1000000,"prototype object ink budget")
    union=set().union(*masks.values())
    require(union<=original,"object layers contain ink absent from final render")
    uncovered=len(original-union)
    calibration=load_calibration(assets[value["calibration_asset_ref"]],base_dir,value["style"],value["native_build"])
    if value["evidence_mode"]=="native":
        require(assets[value["render_asset_ref"]]["kind"]=="native_render","native request requires native-render asset kind")
        require(calibration["measurement_source"]=="native_render","synthetic calibration cannot become native")
        require(all(assets[o["asset_ref"]]["kind"]=="native_object_render" for o in objects.values()),"native object-layer kind mismatch")
    pp=value["pixels_per_pt"];B=value["style"]["bond_pt"]*pp
    require(B>0,"invalid bond scale")
    uncertainty=policy["pixel_uncertainty"]+calibration["limits"]["uncertainty_pt"]*pp
    require(uncertainty<B*.15,"uncertainty too large for prototype")
    ids=[r["id"] for r in value["measurements"]]
    require(len(ids)==len(set(ids)),"duplicate metric observation")
    results=[]
    def mask(key):require(key in masks,"unknown object");return masks[key]
    def entity(key):require(key in entities,"unknown semantic entity");return entities[key]
    for m in value["measurements"]:
        kind=m["metric"];limit=policy["metrics"][kind];metrics={};status="pass";reason=None
        try:
            if reference["source"]=="unqualified":
                raise Unmeasured("independent reference is unqualified")
            if kind in ("visible_tip_target","visible_tail_source"):
                require(m["flow_ref"] in flows,"unknown electron flow")
                flow=flows[m["flow_ref"]];head=mask(m["head_object"]);arrow=mask(m["arrow_object"])
                require(all(objects[key]["state_ref"]==flow["source"]["state_ref"] for key in (m["arrow_object"],m["head_object"])),"flow objects belong to wrong state")
                require(m["flow_ref"] in objects[m["arrow_object"]]["semantic_refs"],"arrow/flow binding")
                require(m["flow_ref"] in objects[m["head_object"]]["semantic_refs"],"head/flow binding")
                require(objects[m["head_object"]]["kind"]=="arrowhead" and objects[m["arrow_object"]]["kind"]=="arrow","flow object kind")
                require(head<=arrow,"head not in original arrow")
                side="target" if kind=="visible_tip_target" else "source"
                require(m[side]["entity_ref"]==port_ref(flow["sink" if side=="target" else "source"]),"wrong semantic port occurrence/LP slot")
                point=visible_tip(head) if side=="target" else visible_tail(arrow,head)
                distance=math.dist(point,m[side]["point"])/B;upper=distance+uncertainty/B
                metrics={"visible_point_px":point,"distance_B":distance,"conservative_upper_B":upper,"calibration_used_to_expand_tolerance":False}
                status=maximum_status(distance,uncertainty/B,limit["maximum_distance"])
            elif kind=="lone_pair_orientation":
                lp=entity(m["lp_ref"]);require(m["lp_ref"] in {r["id"] for r in ir["lone_pairs"]},"not a lone pair")
                require(m["lp_ref"] in objects[m["lp_object"]]["semantic_refs"],"LP slot binding")
                require(objects[m["lp_object"]]["kind"]=="lone_pair","LP object kind mismatch")
                require(objects[m["lp_object"]]["state_ref"]==entity(lp["atom_ref"])["state_ref"],"LP object belongs to wrong state")
                parts=components(mask(m["lp_object"]))
                if len(parts)!=2:raise Unmeasured("LP must have two separately visible dots")
                centers=sorted(centroid(p) for p in parts);center=centroid(mask(m["lp_object"]))
                axis_angle=angle(unit(m["local_axis"]));radial=sub(center,m["atom_point"])
                if math.hypot(*radial)<uncertainty:raise Unmeasured("LP radial direction ambiguous")
                radial_deg=(angle(radial)-axis_angle)%360;dot_deg=(angle(sub(centers[1],centers[0]))-axis_angle)%180
                quadrant=int(radial_deg//90)+1
                radial_error=angle_error(radial_deg,m["expected_radial_deg"])
                dot_error=angle_error(dot_deg,m["expected_dot_deg"],180)
                angular_error=math.degrees(math.asin(min(1,uncertainty/math.hypot(*radial))))
                dot_uncertainty=math.degrees(math.asin(min(1,2*uncertainty/math.dist(*centers))))
                metrics={"dot_uncertainty_deg":dot_uncertainty,"quadrant":quadrant,"radial_deg":radial_deg,"dot_axis_deg":dot_deg,"radial_error_deg":radial_error,"dot_error_deg":dot_error,"radial_uncertainty_deg":angular_error}
                boundary_distance=min(radial_deg%90,90-radial_deg%90)
                quadrant_status=("pass" if quadrant in m["allowed_quadrants"] else "fail") if boundary_distance>angular_error else "unmeasured"
                status=combined(quadrant_status,maximum_status(radial_error,angular_error,limit["maximum_radial_error_deg"]),maximum_status(dot_error,dot_uncertainty,limit["maximum_dot_error_deg"]))
            elif kind=="ink_clearance":
                a,b=m["objects"];distance=pixel_distance(mask(a),mask(b));gap=max(0,distance-1-2*uncertainty)/B
                threshold=limit["minimum_arrow_gap"] if any(objects[x]["kind"] in ("arrow","arrowhead","reaction_arrow") for x in (a,b)) else limit["minimum_gap"]
                metrics={"objects":[a,b],"conservative_lower_B":gap,"required_B":threshold}
                status=minimum_status(max(0,distance-1)/B,2*uncertainty/B,threshold)
            elif kind=="head_glyph_overlap":
                require(objects[m["head_object"]]["kind"]=="arrowhead","overlap head kind")
                require(objects[m["glyph_object"]]["kind"] in ("label","charge","caption"),"overlap glyph kind")
                a=mask(m["head_object"]);b=mask(m["glyph_object"]);overlap=len(a & b)
                gap=max(0,pixel_distance(a,b)-1-2*uncertainty)/B
                metrics={"overlap_pixels":overlap,"conservative_gap_B":gap}
                if overlap:status="fail"
                elif value["evidence"]["object_layers"]!="independent_renders":raise Unmeasured("mutually exclusive colour masks cannot prove absence of hidden overlap")
                else:status=minimum_status(max(0,pixel_distance(a,b)-1)/B,2*uncertainty/B,limit["minimum_gap"])
            elif kind=="curve_bend_severity":
                require(m["flow_ref"] in flows,"unknown flow")
                arrow=mask(m["arrow_object"]);head=mask(m["head_object"]);path=m["centerline"]
                require(all(objects[key]["state_ref"]==flows[m["flow_ref"]]["source"]["state_ref"] for key in (m["arrow_object"],m["head_object"])),"curve objects belong to wrong state")
                require(m["flow_ref"] in objects[m["arrow_object"]]["semantic_refs"],"curve flow binding")
                sampled=polyline_samples(path);tube=value["style"]["stroke_pt"]*pp/2+1
                require(len(sampled)<=20000,"centerline workload limit")
                for point in sampled:
                    if min(math.dist(point,p) for p in arrow)>1.5:raise Unmeasured("centerline unsupported by native pixels")
                for pixel in boundary(arrow-head):
                    if min(segment_distance(pixel,a,b) for a,b in zip(path,path[1:]))>tube:raise Unmeasured("centerline omits visible bend/branch")
                require(math.dist(path[0],visible_tail(arrow,head))<=tube+2,"centerline missing visible tail")
                chord=math.dist(path[0],path[-1])
                if chord<B*.05:raise Unmeasured("closed/degenerate curve")
                length=sum(math.dist(a,b) for a,b in zip(path,path[1:]))
                vectors=[sub(b,a) for a,b in zip(path,path[1:]) if math.dist(a,b)>1e-8]
                turning=sum(angle_error(angle(a),angle(b)) for a,b in zip(vectors,vectors[1:]))
                excursion=max(segment_distance(p,path[0],path[-1]) for p in path)/B
                metrics={"arc_chord_ratio":length/chord,"maximum_excursion_B":excursion,"total_turn_deg":turning}
                status="pass" if length/chord<=limit["maximum_arc_chord_ratio"] and excursion<=limit["maximum_excursion"] and turning<=limit["maximum_total_turn_deg"] else "fail"
            elif kind=="step_spacing":
                require(any(s["from_state"]==m["from_state"] and s["to_state"]==m["to_state"] for s in ir["reaction_steps"]),"spacing not a semantic step")
                for field,state in (("from_objects",m["from_state"]),("to_objects",m["to_state"])):
                    require(all(objects[key]["state_ref"]==state for key in m[field]),"wrong step object ownership")
                    expected={key for key,o in objects.items() if o["state_ref"]==state and o["kind"]!="reaction_arrow"}
                    if set(m[field])!=expected:raise Unmeasured("step spacing omits registered state objects")
                a=set().union(*(mask(k) for k in m["from_objects"]));b=set().union(*(mask(k) for k in m["to_objects"]));axis=unit(m["axis"])
                gap=(min(dot(p,axis) for p in b)-max(dot(p,axis) for p in a))/B
                metrics={"gap_B":gap,"lower_B":gap-2*uncertainty/B,"upper_B":gap+2*uncertainty/B}
                status=combined(minimum_status(gap,2*uncertainty/B,limit["minimum_gap"]),maximum_status(gap,2*uncertainty/B,limit["maximum_gap"]))
            elif kind=="common_scaffold":
                pairs=m["atom_pairs"];require(len({p["before_ref"] for p in pairs})==len(pairs) and len({p["after_ref"] for p in pairs})==len(pairs),"duplicate scaffold mapping")
                occurrence_ids={a["id"] for a in ir["atom_occurrences"]}
                require(all(p["before_ref"] in occurrence_ids and p["after_ref"] in occurrence_ids for p in pairs),"scaffold must reference atom occurrences")
                before_states={entity(p["before_ref"])["state_ref"] for p in pairs};after_states={entity(p["after_ref"])["state_ref"] for p in pairs}
                require(len(before_states)==len(after_states)==1 and before_states!=after_states,"scaffold must compare two distinct states")
                for p in pairs:
                    a=entity(p["before_ref"]);b=entity(p["after_ref"])
                    require("atom_ref" in a and a.get("atom_ref")==b.get("atom_ref"),"scaffold changes stable atom identity")
                if value["evidence_mode"]!="synthetic":
                    raise Unmeasured("qualified native atom-position extractor not implemented")
                def marker_position(occurrence, declared):
                    candidates=[key for key,o in objects.items() if o["kind"]=="label" and o["semantic_refs"]==[occurrence] and o["state_ref"]==entity(occurrence)["state_ref"]]
                    if len(candidates)!=1:raise Unmeasured("ambiguous synthetic atom marker")
                    ink=mask(candidates[0])
                    if len(components(ink))!=1:raise Unmeasured("disconnected synthetic atom marker")
                    point=centroid(ink)
                    if math.dist(point,declared)>uncertainty:raise Unmeasured("cached scaffold position disagrees with marker pixels")
                    return point
                a=[marker_position(p["before_ref"],p["before"]) for p in pairs]
                b=[marker_position(p["after_ref"],p["after"]) for p in pairs];ca=centroid(a);cb=centroid(b)
                aa=[sub(p,ca) for p in a];bb=[sub(p,cb) for p in b]
                if max(abs(cross(x,y)) for x in aa for y in aa)<B*B*.01:raise Unmeasured("scaffold has fewer than three noncollinear points")
                theta=math.atan2(sum(cross(x,y) for x,y in zip(aa,bb)),sum(dot(x,y) for x,y in zip(aa,bb)))
                rotated=[(x[0]*math.cos(theta)-x[1]*math.sin(theta),x[0]*math.sin(theta)+x[1]*math.cos(theta)) for x in aa]
                residuals=[math.dist(x,y)/B for x,y in zip(rotated,bb)];rms=math.sqrt(sum(x*x for x in residuals)/len(residuals));rotation=math.degrees(theta)
                metrics={"rigid_rmsd_B":rms,"maximum_residual_B":max(residuals),"rotation_deg":rotation,"rotation_error_deg":angle_error(rotation,m["expected_rotation_deg"]),"scaling_or_reflection_fitted":False}
                status="pass" if rms<=limit["maximum_rmsd"] and max(residuals)<=limit["maximum_residual"] and metrics["rotation_error_deg"]<=limit["maximum_rotation_error_deg"] else "fail"
        except Unmeasured as exc:status="unmeasured";reason=str(exc)
        if status=="unmeasured" and reason is None:reason="measurement uncertainty straddles policy boundary"
        results.append({"id":m["id"],"metric":kind,"status":status,"measurements":metrics,"reason":reason})
    present={r["metric"] for r in results};missing=sorted(set(policy["metrics"])-present)
    failed=any(r["status"]=="fail" for r in results)
    incomplete=bool(missing) or any(r["status"]=="unmeasured" for r in results)
    metric_verdict="fail" if failed else "unmeasured" if incomplete else "pass_measured_subset"
    return {"version":"quality-result/1.0","sample_id":value["sample_id"],"policy_sha256":value["policy_sha256"],"metrics":results,"missing_metric_families":missing,"metric_verdict":metric_verdict,
      "render_hash_checked":assets[value["render_asset_ref"]]["sha256"],"uncovered_render_ink_pixels":uncovered,
      "chemical_correctness":{"bounded_bookkeeping":chemical.get("semantic_valid"),"independent_scientific_review":"unverified"},
      "native_editability":"unverified_by_this_validator","visual_quality":"failed" if failed else "unverified",
      "human_acceptance":"rejected_record" if value["evidence"]["human_acceptance"]=="rejected" else "unverified",
      "evidence_mode":value["evidence_mode"],"native_layer_authenticity":"not_authenticated","reference_source":reference["source"],"reference_sha256":value["reference_sha256"],
      "quality_scope":"Provisional per-metric pixel checks; no trusted native segmentation/receipt authentication or complete inventory qualification implemented",
      "actual_gold_collected":False,"calibration_allowance_added_to_port_tolerance":False}

def main():
    parser=argparse.ArgumentParser();parser.add_argument("file",type=Path);parser.add_argument("--reference",type=Path,required=True);parser.add_argument("--output",type=Path);args=parser.parse_args()
    try:
        result=evaluate(read_json(args.file),args.file.parent,args.reference)
        code=1 if result["visual_quality"]=="failed" else 2
    except (ValueError,KeyError,TypeError,OSError) as exc:
        result={"version":"quality-result/1.0","status":"invalid","error":str(exc)};code=1
    text=json.dumps(result,indent=2,allow_nan=False)
    if args.output:
        require(not args.output.exists(),"refusing to overwrite result")
        args.output.write_text(text+"\n",encoding="utf-8")
    print(text);return code

if __name__=="__main__":sys.exit(main())
