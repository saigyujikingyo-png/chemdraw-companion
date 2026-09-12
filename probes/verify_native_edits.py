"""Compare actual pre-save/post-reopen object snapshots from disposable edits."""
import argparse,json,math
from pathlib import Path


def flatten(value):
    if isinstance(value,list):return [n for item in value for n in flatten(item)]
    return [value]


def verify(folder):
    events=[json.loads(line) for line in (folder/'events.jsonl').read_text(encoding='utf-8-sig').splitlines()];stage={e['stage']:e['detail'] for e in events};records=[]
    for ext in ('cdx','cdxml'):
        expected=stage['motion_edited_'+ext];actual=stage['motion_reopened_'+ext];issues=[]
        for kind in ('atoms','curves','symbols','captions'):
            a={n['id']:n for n in expected[kind]};b={n['id']:n for n in actual[kind]}
            if a.keys()!=b.keys():issues.append('inventory:'+kind);continue
            for key,x in a.items():
                y=b[key]
                if kind=='atoms' and (x['charge']!=y['charge'] or max(abs(x[k]-y[k]) for k in ('x','y'))>.02):issues.append('atom_edit_readback:'+str(key))
                if kind in ('curves','symbols'):
                    left,right=flatten(x['points']),flatten(y['points'])
                    if len(left)!=len(right) or any(abs(p-q)>.02 for p,q in zip(left,right)):issues.append(kind+'_edit_readback:'+str(key))
                if kind=='captions' and x['text']!=y['text']:issues.append('caption_edit_readback:'+str(key))
        diagnostic=stage['diagnostic_reopened_'+ext];actions=[e['detail'] for e in events if e['stage']=='diagnostic_charge_pair_change'];action=actions[0 if ext=='cdx' else 1]
        atom=next(n for n in diagnostic['atoms'] if n['id']==action['atom_id'])
        if atom['charge']!=action['new_charge']:issues.append('diagnostic_charge_change_lost')
        if action['removed_pair_id'] in {s['id'] for s in diagnostic['symbols']} or len(diagnostic['symbols'])!=len(actual['symbols'])-1:issues.append('diagnostic_pair_delete_lost')
        records.append({'source_format':ext,'native_edit_save_reopen':'pass' if not issues else 'failed','issues':issues,'motion_atom_count':len(actual['atoms']),'retained_curves':len(actual['curves']),'retained_lone_pairs':len(actual['symbols']),'diagnostic_chemistry_accepted':False})
    report={'results':records,'manual_active_correction_seconds':None,'scope':'Automated native object controls on copies. Does not establish corrected figure quality.'}
    (folder/'edit-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);a=p.parse_args();print(json.dumps(verify(a.folder)))
