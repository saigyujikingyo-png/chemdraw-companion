"""Bounded native-fixture composer. Molecular coordinates come from ChemDraw.

This is a probe, not a general SMILES parser or production mechanism service.
Companion code places fragments and semantic electron-flow overlays. ChemDraw
imports, serializes and rasterizes the resulting editable native objects.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.annotation_layout import pack_row,displacement_curves,annotation_gap

STYLE = {"profile_id": "chembridge-review-v1", "font": "Arial", "label_pt": 8,
         "caption_pt": 8, "bond_pt": 14.4, "line_pt": 0.6, "target_dpi": 600}
GRAPHS = {
    "alanine": ({1:(7,1),2:(6,0),3:(6,0),4:(6,0),5:(8,0),6:(8,-1)}, [(1,2,1),(2,3,1),(2,4,1),(4,5,2),(4,6,1)]),
    "hydroxide": ({1:(8,-1)}, []),
    "bromomethane": ({2:(6,0),3:(35,0)}, [(2,3,1)]),
    "methanol": ({1:(8,0),2:(6,0)}, [(1,2,1)]),
    "bromide": ({3:(35,-1)}, []),
}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def graph_binding(fragment, expected):
    """Match the chemical graph, not the vendor's import order or dropped maps."""
    atoms, bonds = expected
    nodes = {n.attrib["id"]: (int(n.get("Element", 6)), int(n.get("Charge", 0))) for n in fragment.findall("n")}
    edges = {frozenset((b.attrib["B"], b.attrib["E"])):float(b.get("Order",1)) for b in fragment.findall("b")}
    want = {frozenset((a,b)):float(o) for a,b,o in bonds}
    if len(nodes)!=len(atoms) or len(edges)!=len(want):
        raise ValueError("Native graph size differs from the chemical fixture")
    def signature(v, e): return sorted(o for pair,o in e.items() if v in pair)
    candidates={a:[n for n in nodes if nodes[n]==spec and signature(n,edges)==signature(a,want)] for a,spec in atoms.items()}
    order=sorted(atoms,key=lambda a:len(candidates[a]))
    matches=[]
    def visit(mapping):
        if len(mapping)==len(order): matches.append(dict(mapping));return
        a=order[len(mapping)]
        for n in candidates[a]:
            if n in mapping.values(): continue
            if any(want.get(frozenset((a,b)))!=edges.get(frozenset((n,m))) for b,m in mapping.items()):continue
            mapping[a]=n;visit(mapping);del mapping[a]
    visit({})
    if len(matches)!=1: raise ValueError(f"Expected unique semantic graph binding, got {len(matches)}")
    return matches[0]

class Page:
    def __init__(self, fixture, width_mm, height_mm):
        self.fixture=fixture;self.next_id=10;self.width=width_mm*72/25.4;self.height=height_mm*72/25.4
        self.root=ET.Element("CDXML", {"CreationProgram":"ChemDraw Companion composition probe", "BondLength":"14.4", "BondSpacing":"18", "LineWidth":"0.6", "BoldWidth":"2", "HashSpacing":"2.5", "MarginWidth":"1.6", "LabelFont":"3", "LabelSize":"8", "LabelFace":"96", "CaptionFont":"3", "CaptionSize":"8", "CaptionFace":"0", "ShowAtomNumber":"no", "ShowTerminalCarbonLabels":"yes", "ShowNonTerminalCarbonLabels":"no", "HideImplicitHydrogens":"no", "color":"0", "bgcolor":"1"})
        colors=ET.SubElement(self.root,"colortable")
        for r,g,b in [(1,1,1),(0,0,0)]:ET.SubElement(colors,"color",{"r":str(r),"g":str(g),"b":str(b)})
        fonts=ET.SubElement(self.root,"fonttable");ET.SubElement(fonts,"font",{"id":"3","charset":"iso-8859-1","name":"Arial"})
        self.page=ET.SubElement(self.root,"page",{"id":"1","BoundingBox":f"0 0 {self.width:.4f} {self.height:.4f}","HeightPages":"1","WidthPages":"1","DrawingSpace":"poster"})
        # Explicit native white page boundary fixes export canvas. Effective
        # molecular DPI is checked independently; whitespace cannot pass it.
        ET.SubElement(self.page,"graphic",{"id":self.uid(),"GraphicType":"Rectangle","RectangleType":"Plain","BoundingBox":f"0 0 {self.width:.4f} {self.height:.4f}","color":"2","LineWidth":"0.01"})
        self.scene={"fixture":fixture,"canvas_mm":[width_mm,height_mm],"style":STYLE,"geometry_provenance":"native ChemDraw fragments with companion placement and electron-flow composition","components":[],"flows":[],"captions":[]}
    def uid(self):self.next_id+=1;return str(self.next_id)
    def text(self,text,x,y,size=8):
        node=ET.SubElement(self.page,"t",{"id":self.uid(),"p":f"{x:.4f} {y:.4f}","InterpretChemically":"no","Justification":"Left"})
        ET.SubElement(node,"s",{"font":"3","size":str(size),"face":"0","color":"0"}).text=text
        self.scene["captions"].append({"id":node.get("id"),"text":text,"x":x,"y":y,"size_pt":size})
        return node
    def fragment(self, path, kind, component, x, y, anchor=None, angle=0):
        raw=ET.parse(path).getroot().find("page/fragment")
        if raw is None:raise ValueError("Native fragment missing")
        binding=graph_binding(raw,GRAPHS[kind]);f=copy.deepcopy(raw)
        ids={n.attrib["id"]:self.uid() for n in f.iter() if "id" in n.attrib}
        points={int(m):tuple(map(float,f.find(f"n[@id='{n}']").attrib["p"].split())) for m,n in binding.items()}
        center=points[anchor] if anchor is not None else (sum(p[0] for p in points.values())/len(points),sum(p[1] for p in points.values())/len(points))
        a=math.radians(angle);co,si=math.cos(a),math.sin(a)
        mapped={}
        inverse={v:k for k,v in binding.items()}
        for n in f.iter():
            old_id=n.get("id")
            if old_id:n.set("id",ids[old_id])
            for key in ("B","E"):
                if key in n.attrib:n.set(key,ids[n.attrib[key]])
            if "BondOrdering" in n.attrib:n.set("BondOrdering"," ".join(ids.get(v,v) for v in n.attrib["BondOrdering"].split()))
            for key in ("BoundingBox","Z","AtomID","NeedsClean"):
                n.attrib.pop(key,None)
            if n.tag=="n":
                px,py=map(float,n.attrib["p"].split());dx,dy=px-center[0],py-center[1]
                old_x,old_y=px,py;px,py=x+co*dx-si*dy,y+si*dx+co*dy
                n.set("p",f"{px:.4f} {py:.4f}");n.set("AtomNumber",str(inverse[old_id]));n.set("ShowAtomNumber","no")
                # Native chemical label runs participate in charge/H parsing.
                # Preserve them and translate upright text with its atom.
                for child in n.findall('t'):
                    lx,ly=map(float,child.get('p').split())
                    child.set('p',f'{lx+px-old_x:.4f} {ly+py-old_y:.4f}')
                mapped[inverse[old_id]]={"native_id":n.get("id"),"x":px,"y":py}
        self.page.append(f)
        inv={v['native_id']:k for k,v in mapped.items()}
        stereo=[{'atoms':[inv[b.get('B')],inv[b.get('E')]],'display':b.get('Display')} for b in f.findall('b') if 'Wedge' in b.get('Display','') or 'Hash' in b.get('Display','')]
        self.scene["components"].append({"id":component,"kind":kind,"fragment_id":f.get("id"),"source_sha256":sha(path),"native_atom_bindings":mapped,"rotation_deg":angle,'directed_stereo_bonds':stereo})
        return mapped
    def arrow(self,x1,y1,x2,y2):
        # Native arrow convention: Head3D is the target, Tail3D is the source.
        return ET.SubElement(self.page,"arrow",{"id":self.uid(),"ArrowheadHead":"Full","ArrowheadType":"Solid","HeadSize":"900","ArrowheadCenterSize":"800","ArrowheadWidth":"250","Head3D":f"{x2} {y2} 0","Tail3D":f"{x1} {y1} 0","FillType":"None","LineWidth":"0.6"})
    def lone_pair(self,x,y):
        return ET.SubElement(self.page,"graphic",{"id":self.uid(),"GraphicType":"Symbol","SymbolType":"LonePair","BoundingBox":f"{x-1.1} {y} {x+1.1} {y}"})
    def flow(self,flow_id,source,target,p0,c1,c2,p3):
        points=[p0,p0,c1,c2,p3,p3]
        curve=ET.SubElement(self.page,"curve",{"id":self.uid(),"CurveType":"8","ArrowheadHead":"Full","ArrowheadType":"Solid","HeadSize":"650","HeadCenterSize":"550","HeadWidth":"220","LineWidth":"0.6","CurvePoints":" ".join(f"{v:.4f}" for p in points for v in p)})
        self.scene["flows"].append({"id":flow_id,"native_id":curve.get("id"),"electron_count":2,"source":source,"target":target,"bezier":[p0,c1,c2,p3]})
    def write(self,out):
        out.mkdir(parents=True,exist_ok=True);p=out/(self.fixture+'.cdxml')
        if p.exists():raise FileExistsError(p)
        ET.indent(self.root);ET.ElementTree(self.root).write(p,encoding='utf-8',xml_declaration=True)
        self.scene["input_cdxml_sha256"]=sha(p)
        (out/(self.fixture+'.scene.json')).write_text(json.dumps(self.scene,indent=2),encoding='utf-8')

def measured_fragment(path,kind):
    f=ET.parse(path).getroot().find('page/fragment');binding=graph_binding(f,GRAPHS[kind]);box=tuple(map(float,f.get('BoundingBox').split()));atoms={}
    for identity,nid in binding.items():
        n=f.find(f'n[@id="{nid}"]');pos=tuple(map(float,n.get('p').split()));t=n.find('t');label=None
        if t is not None:
            bb=tuple(map(float,t.get('BoundingBox').split()));label=(bb[0]-pos[0],bb[1]-pos[1],bb[2]-pos[0],bb[3]-pos[1])
        atoms[identity]={'position':pos,'label_box':label}
    return {'box':box,'atoms':atoms}


def compose(fragments,out,metrics,arrow_metrics):
    B=STYLE['bond_pt'];font=STYLE['caption_pt'];margin=B*.8
    if arrow_metrics['bond_pt']!=B or arrow_metrics['font_pt']!=font or arrow_metrics['head_size']!='650':raise ValueError('Arrow metric style mismatch')
    head_extension=arrow_metrics['conservative_forward_extension_pt'];gap=annotation_gap(B,head_extension)
    def text_box(text):
        m=metrics['metrics'][text]
        if m['font']!=STYLE['font']:raise ValueError('Measured caption font mismatch')
        return [v*font/m['size_pt'] for v in m['bbox_offset']]
    p=Page('S1',85,42)
    p.text('Alanine zwitterion',margin,font*2)
    p.fragment(fragments/'alanine.cdxml','alanine','alanine_zwitterion',p.width/2,p.height/2,anchor=2)
    p.text('Native stereochemistry and formal charges',margin,p.height-font*1.5,font)
    p.write(out)
    for fixture in ['R1','M1']:
        p=Page(fixture,85,42)
        p.text('Nucleophilic substitution' if fixture=='R1' else 'SN2 electron flow',margin,font*2)
        kinds=['hydroxide','bromomethane','methanol','bromide'];measured={k:measured_fragment(fragments/(k+'.cdxml'),k) for k in kinds};plus=text_box('+');plus_width=plus[2]-plus[0]
        arrow_width=max(3*B,max(text_box(t)[2]-text_box(t)[0] for t in ('aqueous','medium'))+gap)
        width=lambda k:measured[k]['box'][2]-measured[k]['box'][0]
        positions=pack_row(p.width,[width(kinds[0]),plus_width,width(kinds[1]),arrow_width,width(kinds[2]),plus_width,width(kinds[3])],margin,gap);center=p.height/2;maps={}
        for k,component,index,anchor in [('hydroxide','nucleophile',0,1),('bromomethane','substrate',2,2),('methanol','methanol',4,2),('bromide','bromide',6,3)]:
            m=measured[k];bb=m['box'];ap=m['atoms'][anchor]['position'];x=positions[index]-bb[0]+ap[0];y=center-(bb[1]+bb[3])/2+ap[1]
            maps[k]=p.fragment(fragments/(k+'.cdxml'),k,component,x,y,anchor=anchor)
        for index in (1,5):p.text('+',positions[index]-plus[0],center-(plus[1]+plus[3])/2,font)
        p.arrow(positions[3],center,positions[3]+arrow_width,center)
        for line,text in enumerate(('aqueous','medium')):
            bb=text_box(text);p.text(text,positions[3]+(arrow_width-(bb[2]-bb[0]))/2-bb[0],center-font*(2.1-line),font)
        p.scene['annotation_measurement_sha256']=metrics['source_sha256'];p.scene['row_minimum_gap_pt']=gap;p.scene['native_head_metrics']=arrow_metrics
        if fixture=='M1':
            xy=lambda a:(a['x'],a['y']);oxygen=xy(maps['hydroxide'][1]);carbon=xy(maps['bromomethane'][2]);leaving=xy(maps['bromomethane'][3]);ob=measured['hydroxide']['atoms'][1]['label_box'];lp=(oxygen[0],oxygen[1]+ob[1]-B*.25)
            pair=p.lone_pair(*lp);p.scene['lone_pairs']=[{'native_id':pair.get('id'),'component':'nucleophile','atom_map':1}]
            obstacles=[]
            for caption in p.scene['captions']:
                if caption['text'] not in metrics['metrics']:continue
                bb=text_box(caption['text']);obstacles.append([caption['x']+bb[0],caption['y']+bb[1],caption['x']+bb[2],caption['y']+bb[3]])
            attack,departure=displacement_curves(lp,carbon,leaving,measured['bromomethane']['atoms'][3]['label_box'],B,head_extension,obstacles)
            p.flow('attack',{'type':'lone_pair','component':'nucleophile','atom_map':1},{'type':'atom','component':'substrate','atom_map':2},*attack)
            p.flow('departure',{'type':'bond','component':'substrate','atom_maps':[2,3]},{'type':'atom','component':'substrate','atom_map':3},*departure)
            p.text('Two simultaneous electron-pair moves',margin,p.height-font*1.5,font)
        p.write(out)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--fragments',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--text-metrics',type=Path,required=True);parser.add_argument('--arrow-metrics',type=Path,required=True)
    args=parser.parse_args();compose(args.fragments,args.out,json.loads(args.text_metrics.read_text(encoding='utf-8')),json.loads(args.arrow_metrics.read_text(encoding='utf-8')))
