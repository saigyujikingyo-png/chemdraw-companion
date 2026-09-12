"""Bounded diagnostic ablations of the failed M1, never a production template.

Remove only named non-molecular overlays. Molecular attributes/positions remain
identical to the preserved failed input. Control drawings are not acceptance
figures and are not holdout inputs.
"""
import argparse,copy,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET


def make(source,out):
    out.mkdir(parents=True,exist_ok=False);original=source.read_bytes();root=ET.fromstring(original);entries=[]
    cases=[('a_original',True,True,True),('b_no_separators',False,True,True),('c_no_curves',True,False,True),('d_no_separators_or_curves',False,False,True),('e_no_curves_or_pairs',True,False,False)]
    atom_hash=lambda r:hashlib.sha256(json.dumps([(n.tag,dict(n.attrib),''.join(n.itertext()).strip()) for n in r.iter() if n.tag in ('n','b')],sort_keys=True).encode()).hexdigest()
    molecular_hash=atom_hash(root)
    for name,separators,curves,pairs in cases:
        case=copy.deepcopy(root)
        for parent in case.iter():
            for child in list(parent):
                remove=(not separators and parent.tag=='page' and child.tag=='t' and ''.join(child.itertext()).strip()=='+') or (not curves and child.tag=='curve') or (not pairs and child.tag=='graphic' and child.get('SymbolType')=='LonePair')
                if remove:parent.remove(child)
        if atom_hash(case)!=molecular_hash:raise ValueError('Diagnostic changed molecular input')
        path=out/(name+'.cdxml')
        if name=='a_original':path.write_bytes(original)
        else:ET.ElementTree(case).write(path,encoding='utf-8',xml_declaration=True)
        entries.append({'case':name,'separators':separators,'curves':curves,'lone_pairs':pairs,'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'molecular_input_fingerprint':molecular_hash})
    report={'source_sha256':hashlib.sha256(original).hexdigest(),'control_count':len(cases),'max_control_variants':6,'scope':'Five predeclared ablations of the same failed molecular input; not scored repaired figures.','cases':entries};(out/'control-plan.json').write_text(json.dumps(report,indent=2),encoding='utf-8');return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(make(a.source,a.out)))
