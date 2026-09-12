"""Restyle native fragment copies before a fresh native Clean and measurement.

This small-fixture helper is outside production generation. Chemical labels,
graph, stereo and the original files are preserved; native glyph boxes must be
remeasured after the declared text/style changes.
"""
import argparse,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET


def prepare(source,out,font_pt):
    out.mkdir(parents=True,exist_ok=False);manifest=[];inputs=[];originals=[]
    for path in sorted(source.glob('*.cdxml')):
        if path.stem.endswith('-before'):continue
        root=ET.parse(path).getroot()
        root.set('LabelSize',str(font_pt));root.set('CaptionSize',str(font_pt));root.set('BondLength','14.4');root.set('LineWidth','0.6')
        for run in root.iter('s'):run.set('size',str(font_pt))
        # Native cleanup recomputes label positions and all drawable bounds.
        target=out/path.name;ET.ElementTree(root).write(target,encoding='utf-8',xml_declaration=True)
        manifest.append({'state':path.stem,'file':path.name})
        inputs.append({'file':path.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
        originals.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (out/'geometry-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (out/'seed-provenance.json').write_text(json.dumps({'version':'native-style-seed/0.1','scope':'Test-only native fragment restyling, not general-IR qualification','font_pt':font_pt,'originals':originals,'inputs':inputs},indent=2),encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--font-pt',type=float,required=True);a=p.parse_args();prepare(a.source,a.out,a.font_pt)
