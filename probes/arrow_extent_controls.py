"""Independent development geometry controls; no reaction reference inputs."""
import argparse,hashlib,itertools,json,math,sys
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.adapters.chemdraw_cdxml import document
from verify_native_masks import frame_transform

STYLE={'font_family':'Arial','font_pt':8.,'bond_length_pt':14.4,'stroke_pt':.6,'canvas_width_mm':40.,'canvas_height_mm':40.}
HEAD={'HeadSize':'650','ArrowheadCenterSize':'569','ArrowheadWidth':'163'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def seed(out):
    out.mkdir(parents=True,exist_ok=False);B=STYLE['bond_length_pt'];W=STYLE['canvas_width_mm']*72/25.4;cases=[]
    for index,(angle,handle) in enumerate(itertools.product((0,90,180,270),(.5,1.,1.5))):
        theta=math.radians(angle);u=(math.cos(theta),math.sin(theta));n=(-u[1],u[0]);origin=(W/2,W/2)
        def local(x,y):return [origin[k]+B*(x*u[k]+y*n[k]) for k in (0,1)]
        points=[local(-1.5,-.75),local(-.75,-1.5),local(1.5-handle,0),local(1.5,0)]
        root,page=document(STYLE);ET.SubElement(page,'graphic',{'id':'9','GraphicType':'Rectangle','BoundingBox':f'0 0 {W} {W}','color':'2','LineWidth':'.1'})
        ET.SubElement(page,'curve',{'id':'10','CurveType':'8','ArrowheadHead':'Full','ArrowheadType':'Solid','LineWidth':'.6',**HEAD,'CurvePoints':' '.join(str(v) for p in [points[0],points[0],points[1],points[2],points[3],points[3]] for v in p)})
        name=f'curve-{index:02d}.cdxml';ET.ElementTree(root).write(out/name,encoding='utf-8',xml_declaration=True)
        cases.append({'file':name,'angle_deg':angle,'terminal_handle_bonds':handle,'bezier':points,'sha256':sha(out/name)})
    (out/'control-manifest.json').write_text(json.dumps({'source':'Procedural intrinsic curve geometry independent of M1/M2','style':STYLE,'heads':HEAD,'cases':cases},indent=2))


def measure(inputs,native,out):
    if out.exists():raise FileExistsError(out)
    manifest=json.loads((inputs/'control-manifest.json').read_text());results=[];uncertainties=[];B=STYLE['bond_length_pt']
    for case in manifest['cases']:
        name=case['file'];xml=native/name;png=xml.with_suffix('.png');root=ET.parse(xml).getroot();curve=next(root.iter('curve'));coords=list(map(float,curve.get('CurvePoints').split()));points=np.array(list(zip(coords[::2],coords[1::2])))
        if sha(inputs/name)!=case['sha256']:raise ValueError('Control input changed')
        # Native serialization adds defaults; compare native attributes/controls
        # to the explicitly declared input, without substituting input pixels.
        if len(points)!=6 or max(np.linalg.norm(points-np.array([case['bezier'][0],case['bezier'][0],case['bezier'][1],case['bezier'][2],case['bezier'][3],case['bezier'][3]]),axis=1))>.02:raise ValueError('Native control geometry changed')
        for key,value in HEAD.items():
            if curve.get(key)!=value:raise ValueError('Native head style changed: '+key)
        for key,value in {'CurveType':'8','ArrowheadHead':'Full','ArrowheadType':'Solid'}.items():
            if curve.get(key)!=value:raise ValueError('Native curve type changed: '+key)
        fonts={n.get('id'):n.get('name') for n in root.iter('font')}
        actual_style={'font_family':fonts[root.get('LabelFont')],'font_pt':float(root.get('LabelSize')),'bond_length_pt':float(root.get('BondLength')),'stroke_pt':float(curve.get('LineWidth',root.get('LineWidth')))}
        if any(actual_style[k]!=STYLE[k] for k in actual_style):raise ValueError('Native control style changed')
        rgba=np.array(Image.open(png).convert('RGBA'));origin,scale=frame_transform(rgba,[40*72/25.4]*2);yy,xx=np.where((rgba[:,:,3]>=8)&(rgba[:,:,:3].min(axis=2)<240))
        cloud=(np.column_stack((xx,yy))-np.array(origin))/np.array(scale);end=points[-1];u=end-points[-3];u/=np.linalg.norm(u);n=np.array([-u[1],u[0]]);offset=cloud-end;along=offset@u;across=np.abs(offset@n)
        near=(along>-.1*B)&(along<.55*B)&(across<.08*B)
        if not np.any(near):raise ValueError('Visible native arrowhead absent')
        extent=float(along[near].max());uncertainty=.5/min(scale)+.02;uncertainties.append(uncertainty)
        results.append({**case,'native_cdxml_sha256':sha(xml),'native_png_sha256':sha(png),'native_build':root.get('CreationProgram'),'native_style':actual_style,'native_control_endpoint':end.tolist(),'extent_pt':extent,'uncertainty_pt':uncertainty,'native_heads':{key:curve.get(key) for key in HEAD},'native_dpi':[s*72 for s in scale]})
    report={'experiment':'native-core-r3-independent-geometry','scope':'Intrinsic arrowhead extent on twelve independent development curves only; no reaction correctness or full curve-family guarantee','head_size':HEAD['HeadSize'],'font_pt':STYLE['font_pt'],'bond_pt':B,'conservative_forward_extension_pt':max(r['extent_pt']+r['uncertainty_pt'] for r in results),'minimum_observed_extension_pt':min(r['extent_pt'] for r in results),'source_sha256':sha(inputs/'control-manifest.json'),'native_cases':results,'owner_physical_review':'pending'}
    out.write_text(json.dumps(report,indent=2));return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('seed','measure'));p.add_argument('--inputs',type=Path);p.add_argument('--native',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.mode=='seed':seed(a.out)
    else:
        r=measure(a.inputs,a.native,a.out);print(json.dumps({k:v for k,v in r.items() if k!='native_cases'}))
