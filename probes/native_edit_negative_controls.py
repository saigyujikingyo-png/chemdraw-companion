"""Replay corruptions against full, actual native edit journals."""
import argparse,copy,hashlib,json
from pathlib import Path
from verify_native_edits import verify_events


def run(source,out):
    out.mkdir(parents=True,exist_ok=False);events=[json.loads(s) for s in source.read_text(encoding='utf-8-sig').splitlines()];records=[]
    positive=verify_events(events)
    if any(r['native_edit_save_reopen']!='pass' for r in positive['results']):raise ValueError('Native positive control failed')
    for case in ('noop_curves','noop_symbols','noop_captions','changed_hydrogens','changed_bond_stereo','missing_head','small_charge_change'):
        changed=copy.deepcopy(events);stage={e['stage']:e['detail'] for e in changed}
        for ext in ('cdx','cdxml'):
            before=stage['before_'+ext]
            for moment in ('motion_edited_','motion_reopened_'):
                scene=stage[moment+ext]
                if case.startswith('noop_'):kind=case[5:];scene[kind]=copy.deepcopy(before[kind])
                elif case=='changed_hydrogens':scene['atoms'][0]['implicit_h']+=1
                elif case=='changed_bond_stereo':scene['bonds'][0]['stereo']+=1
                elif case=='missing_head':scene['curves'][0]['head']=0
                elif case=='small_charge_change':scene['atoms'][0]['charge']+=.01
        result=verify_events(changed);accepted=any(r['native_edit_save_reopen']=='pass' for r in result['results'])
        path=out/(case+'.jsonl');path.write_text('\n'.join(json.dumps(e,separators=(',',':')) for e in changed)+'\n',encoding='utf-8')
        records.append({'case':case,'status':'failed_guard' if accepted else 'rejected_as_required','journal_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'results':result['results']})
    report={'version':'native-edit-negative-controls/0.1','source_native_journal_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'native_positive_control':positive,'negative_controls':records}
    (out/'negative-controls.json').write_text(json.dumps(report,indent=2),encoding='utf-8');return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=run(a.source,a.out);print(json.dumps([{'case':c['case'],'status':c['status']} for c in r['negative_controls']]));raise SystemExit(0 if all(c['status']=='rejected_as_required' for c in r['negative_controls']) else 1)
