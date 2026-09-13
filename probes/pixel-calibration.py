"""Create/measure a native physical-scale control, not a mechanism layout."""
import argparse,json
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image
from compose_fixtures import Page

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['create','measure']);p.add_argument('path',type=Path);a=p.parse_args()
    if a.mode=='create':
        page=Page('scale-control',85,24);page.text('Native scale control',16,16,8)
        ET.SubElement(page.page,'graphic',{'id':page.uid(),'GraphicType':'Line','BoundingBox':'184 42 40 42','LineWidth':'0.6'})
        ET.SubElement(page.page,'graphic',{'id':page.uid(),'GraphicType':'Line','BoundingBox':'54.4 55 40 55','LineWidth':'0.6'})
        page.write(a.path)
    else:
        results=[]
        for path in a.path.glob('*.png'):
            im=Image.open(path).convert('RGBA');runs=[]
            for y in range(im.height):
                best=0;count=0
                for x in range(im.width):
                    r,g,b,alpha=im.getpixel((x,y))
                    if alpha>128 and max(r,g,b)<100:count+=1;best=max(best,count)
                    else:count=0
                if best>100:runs.append((y,best))
            # The 144 pt control is exactly two inches. Native cap/antialias
            # pixels are reported separately from the nominal centerline span.
            maximum=max(n for y,n in runs)
            results.append({'file':path.name,'dimensions':im.size,'metadata_dpi':Image.open(path).info.get('dpi'),'longest_dark_run_pixels':maximum,'reference_length_pt':144,'dpi_from_ink_extent_before_cap_correction':maximum/2,'expected_600dpi_centerline_pixels':1200,'native_stroke_pt':.6,'raw_scanlines':runs})
        (a.path/'pixel-scale-report.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        print(json.dumps([{k:v for k,v in r.items() if k!='raw_scanlines'} for r in results],indent=2))
