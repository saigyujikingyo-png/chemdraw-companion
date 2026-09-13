"""Extract intrinsic native glyph extents, never whole-page placement."""
import argparse,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET


def extract(path,texts):
    root=ET.parse(path).getroot();result={};fonts={f.get('id'):f.get('name') for f in root.findall('fonttable/font')}
    for text in texts:
        found=[]
        for t in root.findall('page/t'):
            if ''.join(s.text or '' for s in t.findall('s'))!=text:continue
            runs=t.findall('s')
            if len(runs)!=1 or not t.get('BoundingBox'):raise ValueError('Text measurement is not unambiguous')
            p=list(map(float,t.get('p').split()));b=list(map(float,t.get('BoundingBox').split()));s=runs[0]
            found.append({'font':fonts[s.get('font')],'size_pt':float(s.get('size')),'face':s.get('face','0'),'bbox_offset':[b[0]-p[0],b[1]-p[1],b[2]-p[0],b[3]-p[1]]})
        if not found:raise ValueError('Missing native text measurement: '+text)
        first=found[0]
        if any(x['font']!=first['font'] or x['size_pt']!=first['size_pt'] or max(abs(a-b) for a,b in zip(x['bbox_offset'],first['bbox_offset']))>.03 for x in found):raise ValueError('Inconsistent native glyph measurements')
        result[text]=first
    return {'version':'native-caption-metrics/0.1','source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'scope':'Only font-specific glyph offsets; no page/state/atom placement cache. Scaled sizes require final native layout readback.','metrics':result}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--native',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--text',action='append',required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    a.out.write_text(json.dumps(extract(a.native,a.text),indent=2),encoding='utf-8')
