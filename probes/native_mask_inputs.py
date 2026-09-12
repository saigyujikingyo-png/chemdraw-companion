"""Colour-only diagnostic copies for native object-mask raster readback.

No rendered image is modified. Each drawing primitive receives a distinct
colour in a COPY, which ChemDraw must render natively. Geometry/semantics and
the full source/diagnostic raster silhouettes are independently compared before
any mask clearance result is usable. Original black native files are retained.
"""
import argparse,colorsys,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET


def prepare(source,out,stems):
    out.mkdir(parents=True,exist_ok=False)
    for stem in stems:
        path=source/(stem+'.cdxml');root=ET.parse(path).getroot();table=root.find('colortable');groups=[]
        parents={child:node for node in root.iter() for child in node}
        for node in root.iter():
            kind=node.tag
            if kind=='n':
                if node.find('t') is None:continue
                kind='atom_label'
            elif kind=='t':
                if parents[node].tag=='n':continue
                kind='caption'
            elif kind=='graphic':
                if node.get('SupersededBy') or node.get('GraphicType')=='Rectangle':continue
                kind='symbol'
            elif kind not in ('b','curve','arrow'):continue
            index=len(groups);rgb=tuple(round(v*255) for v in colorsys.hsv_to_rgb((index*.618033988749895)%1,.86,.72));color=str(len(table)+2)
            ET.SubElement(table,'color',dict(zip(('r','g','b'),(str(v/255) for v in rgb))))
            for child in node.iter():
                if child.tag in ('n','t','s','b','curve','graphic','arrow'):child.set('color',color)
            groups.append({'native_id':node.get('id'),'kind':kind,'rgb':rgb,'atom_ends':[node.get('B'),node.get('E')] if kind=='b' else [],'color_index':color})
        target=out/(stem+'.cdxml');ET.ElementTree(root).write(target,encoding='utf-8',xml_declaration=True)
        record={'version':'native-mask-input/0.1','source_file':path.name,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'input_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'method':'Only object colours changed in a native CDXML copy; no image processing or geometry changes','groups':groups}
        (out/(stem+'.mask-map.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--stem',action='append',required=True);a=p.parse_args();prepare(a.source,a.out,a.stem)
