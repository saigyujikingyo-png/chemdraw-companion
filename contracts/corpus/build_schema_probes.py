"""Create schema representation probes, not corpus gold or generation templates."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"examples/corpus";OUT.mkdir(exist_ok=True)
def write(name,value):
    p=OUT/name;p.write_text(json.dumps(value,indent=2)+"\n",encoding="utf-8",newline="\n");return p
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def edge(a,b,order=1):return {"atoms":[a,b],"order":order}
def state(id,bonds,charges,pairs):
    return {"id":id,"label":id,"bonds":bonds,"formal_charges":[{"atom":a,"value":v} for a,v in charges.items()],"lone_pairs":[{"atom":a,"count":v} for a,v in pairs.items()]}
def flow(id,source,target):return {"id":id,"electron_count":2,"source":source,"target":target}
def lp(a):return {"type":"lone_pair","atom":a,"pair_index":0}
def atom(a):return {"type":"atom","atom":a}
def bond(a,b):return {"type":"bond","atoms":[a,b],"electrons":"sigma"}
def step(id,source,target,flows):return {"id":id,"from":source,"to":target,"kind":"elementary_step","label":"electron-pair step","electron_flows":flows}
proton={"atom_catalog":[{"map":1,"element":"O","implicit_h":0},{"map":2,"element":"N","implicit_h":0}]+[{"map":i,"element":"H","implicit_h":0} for i in range(3,8)],
"states":[state("before",[edge(1,3),edge(2,4),edge(2,5),edge(2,6),edge(2,7)],{1:-1,2:1},{1:3,2:0}),state("after",[edge(1,3),edge(1,4),edge(2,5),edge(2,6),edge(2,7)],{},{1:2,2:1})],
"transitions":[step("transfer","before","after",[flow("make_OH",lp(1),atom(4)),flow("break_NH",bond(2,4),atom(2))])],"stereo_constraints":[],"entry_state":"before"}
m1={"atom_catalog":[{"map":1,"element":"O","implicit_h":1},{"map":2,"element":"C","implicit_h":3},{"map":3,"element":"Br","implicit_h":0}],
"states":[state("before",[edge(2,3)],{1:-1},{1:3,3:3}),state("after",[edge(1,2)],{3:-1},{1:2,3:4})],
"transitions":[step("substitution","before","after",[flow("attack",lp(1),atom(2)),flow("departure",bond(2,3),atom(3))])],"stereo_constraints":[],"entry_state":"before"}
m2=json.loads((ROOT/"examples/m2-composer-request.json").read_text())["mechanism"]
def convert(name,old):
    arrays=("atoms","states","species","molecules","atom_occurrences","bonds","charges","radicals","lone_pairs","reaction_steps","reaction_arrows","condition_texts","electron_flows","layout_constraints")
    result={"version":"corpus-mechanism-ir/0.1","id":name,"entry_state":old["entry_state"],"scope":{"atom_inventory":"closed","omissions":["No implicit counterion is asserted; total represented charge is checked."],"scientific_status":"unreviewed"},**{k:[] for k in arrays}}
    result["atoms"]=[{"id":f'a{a["map"]}',"element":a["element"],"isotope":None} for a in old["atom_catalog"]]
    maps=[a["map"] for a in old["atom_catalog"]]; atom_by_map={a["map"]:a for a in old["atom_catalog"]}
    occurrence=lambda sid,i:f"{sid}:a{i}"
    edge_id=lambda sid,ab:sid+":b:"+":".join(str(i) for i in sorted(ab))
    for s in old["states"]:
        sid=s["id"];adj={i:set() for i in maps}
        for b in s["bonds"]:
            a,c=b["atoms"];adj[a].add(c);adj[c].add(a)
            result["bonds"].append({"id":edge_id(sid,b["atoms"]),"state_ref":sid,"atom_refs":[occurrence(sid,i) for i in b["atoms"]],"order":b["order"],"stereo":"none"})
        unseen=set(maps);components=[]
        while unseen:
            todo=[min(unseen)];component=set()
            while todo:
                current=todo.pop()
                if current not in component:component.add(current);todo.extend(adj[current]-component)
            unseen-=component;components.append(sorted(component))
        species_refs=[]
        for n,component in enumerate(components):
            mid=f"{sid}:m{n}";spid=f"{sid}:species{n}";species_refs.append(spid)
            result["molecules"].append({"id":mid,"state_ref":sid,"atom_refs":[occurrence(sid,i) for i in component],"bond_refs":[edge_id(sid,b["atoms"]) for b in s["bonds"] if set(b["atoms"])<=set(component)]})
            result["species"].append({"id":spid,"state_ref":sid,"molecule_refs":[mid],"role":"participant","stoichiometry":1})
            for i in component:
                result["atom_occurrences"].append({"id":occurrence(sid,i),"atom_ref":f"a{i}","state_ref":sid,"molecule_ref":mid,"implicit_h":atom_by_map[i]["implicit_h"]})
        result["states"].append({"id":sid,"label":s["label"],"species_refs":species_refs})
        for q in s["formal_charges"]:
            result["charges"].append({"id":f'{sid}:q{q["atom"]}',"atom_ref":occurrence(sid,q["atom"]),"value":q["value"],"display":"shown"})
        for pair in s["lone_pairs"]:
            for slot in range(pair["count"]):
                result["lone_pairs"].append({"id":f'{sid}:lp{pair["atom"]}:{slot}',"atom_ref":occurrence(sid,pair["atom"]),"slot":slot,"display":"unresolved"})
    def port(p,sid,source):
        if p["type"]=="atom":return {"type":"atom","state_ref":sid,"atom_ref":occurrence(sid,p["atom"])}
        if p["type"]=="lone_pair":return {"type":"lone_pair","state_ref":sid,"lone_pair_ref":f'{sid}:lp{p["atom"]}:{p["pair_index"]}'}
        if source:return {"type":"bond","state_ref":sid,"bond_ref":edge_id(sid,p["atoms"]),"electron_kind":p["electrons"]}
        return {"type":"prospective_bond","state_ref":sid,"atom_refs":[occurrence(sid,i) for i in p["atoms"]]}
    for t in old["transitions"]:
        tid=t["id"];cid="condition:"+tid
        result["reaction_steps"].append({"id":tid,"from_state":t["from"],"to_state":t["to"],"kind":"teaching_elementary","electron_flow_refs":[f["id"] for f in t["electron_flows"]],"condition_refs":[cid]})
        result["reaction_arrows"].append({"id":"reaction-arrow:"+tid,"step_ref":tid,"kind":"forward","from_state":t["from"],"to_state":t["to"]})
        result["condition_texts"].append({"id":cid,"step_ref":tid,"text":t["label"],"kind":"annotation","evidence_status":"specified"})
        for f in t["electron_flows"]:
            result["electron_flows"].append({"id":f["id"],"step_ref":tid,"electron_count":f["electron_count"],"source":port(f["source"],t["from"],True),"sink":port(f["target"],t["from"],False),"simultaneous_group":tid})
    for i,r in enumerate(old["stereo_constraints"]):
        for sid in r["states"]:
            result["layout_constraints"].append({"id":f"stereo:{i}:{sid}","kind":"anti" if r["type"].startswith("anti") else "syn","subjects":[occurrence(sid,n) for n in r["central_bond"]+r["substituent_atoms"]],"strength":"hard","parameters":{}})
    result["layout_constraints"] += [
        {"id":"constraint:reading","kind":"reading_order","subjects":[],"strength":"hard","parameters":{}},
        {"id":"constraint:clearance","kind":"min_clearance","subjects":[],"strength":"hard","parameters":{"minimum_gap":0.18,"unit":"bond_length"}},
        {"id":"constraint:snake","kind":"serpentine","subjects":[],"strength":"soft","parameters":{"direction":"alternating","max_columns":3,"minimum_row_turns":0}}]
    return result
for name,data in [("proton-transfer",proton),("M1",m1),("M2",m2)]:
    rich=convert(name,data)
    if name=="M1":
        rich["condition_texts"][0].update(text="aqueous medium",kind="condition")
        rich["layout_constraints"].append({"id":"constraint:backside","kind":"backside_approach","subjects":["before:a1","before:a2","before:a3"],"strength":"hard","parameters":{"angle_deg":180}})
    for sp in rich["species"]:
        molecule = next(m for m in rich["molecules"] if m["id"] == sp["molecule_refs"][0])
        members = {o["atom_ref"] for o in rich["atom_occurrences"] if o["id"] in molecule["atom_refs"]}
        if name == "M1":
            sp["role"] = ("nucleophile" if "a1" in members else "substrate") if sp["state_ref"] == "before" else "product"
        elif name == "proton-transfer":
            sp["role"] = "reactant" if sp["state_ref"] == "before" else "product"
    if name == "M2":
        policy = json.loads((ROOT/"examples/m2-composer-request.json").read_text())["layout_policy"]
        snake = next(c for c in rich["layout_constraints"] if c["kind"] == "serpentine")
        snake["strength"] = "hard"
        snake["parameters"].update(max_columns=policy["max_columns"], minimum_row_turns=policy["minimum_row_turns"])
    write(name+".ir.json",rich)
# A demonstrator aligns an extracted native curve to proposed semantic IDs.
# It does not claim native authorship, human review, or a new native execution.
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--native-evidence",type=Path,default=ROOT/"verification/2026-09-12-r2")
native=parser.parse_args().native_evidence
if not (native/"samples/M1/M1.cdxml").is_file():
    raise FileNotFoundError("Provide the immutable R2 evidence directory with --native-evidence; no native execution is performed.")
import xml.etree.ElementTree as ET
xml=ET.parse(native/"samples/M1/M1.cdxml").getroot();curve=xml.find(".//curve[@id='31']")
values=list(map(float,curve.get("CurvePoints").split()));pts=list(zip(values[::2],values[1::2]))
layers=["page_and_reading_order","molecular_graph","participant_roles","reaction_arrows","conditions","electronic_marks","electron_flow","visual_geometry"]
annotation={"version":"mechanism-annotation/0.1","id":"annotation:M1","sample_id":"M1","revision_id":"corpus-proof-r1","mechanism_sha256":sha(OUT/"M1.ir.json"),
"layers":[{"name":name,"status":"proposed" if name in ("electron_flow","visual_geometry") else "not_started","depends_on":layers[:i]} for i,name in enumerate(layers)],
"observations":[{"id":"observation:attack","layer":"electron_flow","entity_refs":["attack"],"asset_ref":"M1-native-cdxml","asset_sha256":sha(native/"samples/M1/M1.cdxml"),"frame_ref":"M1-native-page","locator":{"kind":"native_id","value":"31"},"geometry":{"kind":"bezier","points":[pts[i] for i in (0,2,3,5)],"measurement_status":"observed"},"method":"derived_measurement","actor_ref":"schema-agent","alignment_status":"proposed","confidence":None,"alternatives":[],"review_refs":[]}],
"actors":[{"id":"schema-agent","kind":"ai","tool_or_model":"unavailable","version_or_run":"corpus-schema-proof-r1"}],"reviews":[]}
annotation["observations"][0].update(evidence_asset_refs=["M1-native-cdxml"],assessments=[])
mask=next(r for r in json.loads((native/"small-native-mask-verification.json").read_text())["results"] if r["fixture"]=="M1")
tip=next(t for t in mask["native_arrowhead_tips"] if t["flow"]=="departure")["visible_tip_native_pt"]
scale=mask["native_canvas_frame_px_per_pt"];origin=mask["native_canvas_origin_px"]
annotation["observations"].append({"id":"observation:departure-tip","layer":"visual_geometry","entity_refs":["departure","before:a3"],"asset_ref":"M1-native-png","asset_sha256":sha(native/"samples/M1/M1.png"),"frame_ref":"M1-native-pixels","locator":{"kind":"raster_region","value":"visible departure tip measured in archived native-mask receipt"},"geometry":{"kind":"point","points":[[tip[i]*scale[i]+origin[i] for i in (0,1)]],"measurement_status":"observed"},"method":"derived_measurement","actor_ref":"schema-agent","alignment_status":"proposed","confidence":None,"alternatives":[],"review_refs":[],"evidence_asset_refs":["M1-native-png","M1-mask-calibration"],"assessments":[{"kind":"clearance","entity_refs":["departure","before:a3"],"value":0,"unit":"pt","label":"failed","intended_contact":False,"evidence_asset_refs":["M1-mask-calibration"]}]})
write("M1.annotation.json",annotation)
rights={"id":"rights-probe","status":"pending","license_expression":"NOASSERTION","license_url":None,"scope":"Schema representation probes and references to previously published synthetic native benchmark artifacts; no dataset reuse permission inferred.","attribution":"ChemDraw Companion project; native execution evidence eb8b4c8","permission_evidence":[],"checked_on":None,"permissions":{"store":True,"annotate":True,"train":False,"redistribute":False}}
def asset(id,kind,p,uri,frames=[]):
    return {"id":id,"kind":kind,"mime":"application/json" if p.suffix==".json" else {"cdx":"chemical/x-cdx","cdxml":"chemical/x-cdxml","native_render":"image/png"}[kind],"uri":uri,"sha256":sha(p),"bytes":p.stat().st_size,"producer":"schema probe" if p.suffix==".json" else "recorded ChemDraw Prime 26.0.0.6141","derived_from":[],"rights_ref":"rights-probe","frames":frames}
samples=[]
for name in ("proton-transfer","M1","M2"):
    irpath=OUT/(name+".ir.json");is_benchmark=name in ("M1","M2")
    assets=[asset(name+"-ir","ir",irpath,irpath.name)]
    if name=="M1":
        assets.append(asset("M1-annotation","annotation",OUT/"M1.annotation.json","M1.annotation.json"))
        base="https://github.com/saigyujikingyo-png/chemdraw-companion/blob/eb8b4c869a23237f726f8cf127be18743f573a14/verification/2026-09-12-r2/samples/M1/"
        nativeframe={"id":"M1-native-page","page":0,"units":"pt","origin":"top_left","y_axis":"down","width":85*72/25.4,"height":42*72/25.4,"parent_frame_ref":None,"to_parent_affine":None,"calibration":"native_readback"}
        mask=next(r for r in json.loads((native/"small-native-mask-verification.json").read_text())["results"] if r["fixture"]=="M1")
        sx,sy=mask["native_canvas_frame_px_per_pt"];ox,oy=mask["native_canvas_origin_px"]
        pixelframe={"id":"M1-native-pixels","page":0,"units":"px","origin":"top_left","y_axis":"down","width":2044,"height":1028,"parent_frame_ref":"M1-native-page","to_parent_affine":[1/sx,0,0,1/sy,-ox/sx,-oy/sy],"calibration":"measured"}
        for kind,ext,frames in [("cdx","cdx",[]),("cdxml","cdxml",[nativeframe]),("native_render","png",[pixelframe])]:
            assets.append(asset("M1-native-"+ext,kind,native/f"samples/M1/M1.{ext}",base+"M1."+ext,frames))
        assets.append(asset("M1-mask-calibration","receipt",native/"small-native-mask-verification.json",base.split("samples/M1/")[0]+"small-native-mask-verification.json"))
    samples.append({"id":name,"revision_id":"corpus-proof-r1","tier":"ungraded","gold_scopes":[],"split":"fixed_regression" if is_benchmark else "development","exposure_status":"exposed_and_tuned" if is_benchmark else "exposed","leakage_group_id":"benchmark/"+name if is_benchmark else "schema-proof/proton-transfer","derived_from":[],"lineage_relation":"root","family_tags":["rearrangement" if name=="M2" else "SN2" if name=="M1" else "proton_transfer"],"stress_tags":["schema_representation_only"],"task_mode":"schema_representation","generation_asset_refs":[],"oracle_asset_refs":[],"source":{"kind":"schema_probe","url":None,"accession_or_version":"existing exposed fixture re-encoded" if is_benchmark else "new synthetic schema probe","retrieved_on":None,"author":"AI architecture task; no human scientific sign-off"},"mechanism_asset_ref":name+"-ir","annotation_asset_ref":"M1-annotation" if name=="M1" else None,"assets":assets,"rights":[rights],"reviews":[],"uses":{"rule_tuning":False,"training":False,"evaluation":is_benchmark,"public_distribution":False},"status":{"representable":"pass","semantic_valid":"unverified","runtime_projection":"unverified","native_verified":"unverified","visual_accepted":"unverified"},"exposure_log":[{"event":"tuning" if is_benchmark else "authoring","at":"2026-09-12" if is_benchmark else "2026-09-13","known_to":"development","artifact_sha256":sha(ROOT/("examples/electron-flow-step.json" if name=="M1" else "examples/m2-composer-request.json")) if is_benchmark else sha(irpath)}]})
write("proof-manifest.json",{"version":"corpus-manifest/0.1","id":"schema-representation-pilots","revision":"corpus-proof-r1","policy_version":"corpus-policy/0.1","samples":samples})
write("split-manifest.json",{"version":"split-manifest/0.1","id":"schema-pilot-splits","corpus_revision":"corpus-proof-r1","policy_version":"corpus-policy/0.1","assignments":[{"sample_id":s["id"],"leakage_group_id":s["leakage_group_id"],"split":s["split"],"exposure_status":s["exposure_status"],"assigned_at":"2026-09-13","reason":"Exposed regression lineage, no fitting" if s["split"]=="fixed_regression" else "Ungraded schema proof only"} for s in samples],"freeze":{"status":"not_started","commit":None,"bundle_sha256":None,"selected_holdout_ids":[],"generation":0,"base_pass_receipt_sha256":None,"base_passed_at":None,"frozen_at":None,"selections":[]},"duplicate_audit":{"status":"not_started","methods":[],"version":"not_run","unresolved_groups":[]}})
print("Created three ungraded IR probes, one partial native-alignment proposal, and registry/split examples. No SVG, gold or new native output fabricated.")
