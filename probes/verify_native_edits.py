"""Fail-closed before -> declared nonzero edit -> reopen verification."""
from __future__ import annotations
import argparse,copy,json,math
from pathlib import Path

KINDS=('atoms','bonds','curves','symbols','captions','arrows')
EXACT={'id','element','charge','implicit_h','isotope','radical','stereo','node_type','num_points','head','tail','head_type','line_type','fill_type','face','order','display','display2','a','b','warnings'}
REQUIRED={
 'atoms':{'id','type','element','charge','implicit_h','isotope','radical','stereo','node_type','number','label','x','y'},
 'bonds':{'id','type','a','b','order','display','display2','stereo'},
 'curves':{'id','type','num_points','head','tail','head_type','line_type','fill_type','head_size','head_width','points'},
 'symbols':{'id','type','symbol_type','is_radical','is_charge','points'},
 'captions':{'id','type','text','anchor','left','top','family','size','face','angle','styles'},
 'arrows':{'id','type','start','end','head','tail','head_type','line_type','head_size','head_width'}}


def validate_snapshot(scene):
    if scene.get('snapshot_version')!='native-scene/0.2':raise ValueError('Incomplete legacy snapshot; fresh native execution required')
    for kind in KINDS:
        if kind not in scene or not isinstance(scene[kind],list):raise ValueError('Missing object collection: '+kind)
        if len({x['id'] for x in scene[kind]})!=len(scene[kind]):raise ValueError('Duplicate object IDs')
        for obj in scene[kind]:
            if not REQUIRED[kind]<=set(obj):raise ValueError('Incomplete '+kind+' properties')
    if 'warnings' not in scene or 'style' not in scene:raise ValueError('Missing warning/style snapshot')


def equivalent(a,b):
    if isinstance(a,bool) or isinstance(b,bool):return a is b
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):return math.isfinite(a) and math.isfinite(b) and abs(a-b)<=.02
    if isinstance(a,dict) and isinstance(b,dict):return a.keys()==b.keys() and all((a[k]==b[k]) if k in EXACT else equivalent(a[k],b[k]) for k in a)
    if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(equivalent(x,y) for x,y in zip(a,b))
    return a==b


def compare(expected,actual):
    issues=[];validate_snapshot(expected);validate_snapshot(actual)
    for key in ('style','warnings'):
        if not equivalent(expected[key],actual[key]):issues.append('changed_'+key)
    for kind in KINDS:
        if kind=='arrows':
            # Untouched step arrows may receive new serialization IDs. Compare
            # the complete drawable multiset, not order or ID alone. No arrow
            # edit or identity qualification is claimed by this equivalence.
            unmatched=[{k:v for k,v in x.items() if k!='id'} for x in actual[kind]]
            for item in expected[kind]:
                item={k:v for k,v in item.items() if k!='id'}
                candidates=[i for i,x in enumerate(unmatched) if equivalent(item,x)]
                if not candidates:issues.append('changed_step_arrow');continue
                unmatched.pop(candidates[0])
            if unmatched:issues.append('extra_step_arrow')
            continue
        left={x['id']:x for x in expected[kind]};right={x['id']:x for x in actual[kind]}
        if left.keys()!=right.keys():issues.append('inventory:'+kind);continue
        for identity,obj in left.items():
            if not equivalent(obj,right[identity]):issues.append(f'undeclared_or_missing_edit:{kind}:{identity}')
    return issues


def apply_captions(table,changes):
    if not changes:raise ValueError('Missing caption edit intent')
    for change in changes:
        obj=table[change['id']]
        if obj['text']!=change['from'] or change['from']==change['to']:raise ValueError('Caption precondition or nonzero edit missing')
        obj['text']=change['to']


def expected_motion(before,intent):
    validate_snapshot(before)
    if intent.get('version')!='native-edit-intent/0.2':raise ValueError('Missing complete pre-mutation intent')
    result=copy.deepcopy(before);tables={k:{x['id']:x for x in result[k]} for k in KINDS}
    move=intent['atom_translation']
    if not move['ids'] or math.hypot(move['dx'],move['dy'])<=.02:raise ValueError('Zero atom movement intent')
    for i in move['ids']:tables['atoms'][i]['x']+=move['dx'];tables['atoms'][i]['y']+=move['dy']
    for kind,key in [('symbols','symbol_translations'),('curves','curve_changes')]:
        if before[kind] and not intent[key]:raise ValueError('Missing nonzero '+kind+' edit intent')
        for change in intent[key]:
            obj=tables[kind][change['id']];deltas=change['deltas']
            if len(deltas)!=len(obj['points']) or not any(abs(x)>.02 for x in deltas):raise ValueError('Zero/invalid point edit intent')
            obj['points']=[x+d for x,d in zip(obj['points'],deltas)]
    apply_captions(tables['captions'],intent['caption_replacements'])
    return result


def expected_diagnostic(before,intent):
    if intent.get('version')!='native-edit-intent/0.2':raise ValueError('Missing diagnostic intent')
    result=copy.deepcopy(before);charge=intent['charge_change'];obj=next(a for a in result['atoms'] if a['id']==charge['id'])
    if obj['charge']!=charge['from'] or charge['from']==charge['to']:raise ValueError('Charge edit precondition/nonzero missing')
    obj['charge']=charge['to'];removed=intent['removed_symbol_id']
    if removed not in {x['id'] for x in result['symbols']}:raise ValueError('Missing symbol deletion target')
    result['symbols']=[x for x in result['symbols'] if x['id']!=removed]
    apply_captions({x['id']:x for x in result['captions']},intent['caption_replacements'])
    return result


def account_changed_text_bounds(expected,actual,intent):
    """Only changed text may recompute its glyph top; anchor/style remain exact.

    Native read-only control shows Position stays fixed while Top changes with
    different glyphs. Full actual bounds must still agree after disk reopening.
    """
    for change in intent['caption_replacements']:
        before=next(c for c in expected['captions'] if c['id']==change['id'])
        after=next(c for c in actual['captions'] if c['id']==change['id'])
        before['top']=after['top']


def verify_events(events):
    stage={e['stage']:e['detail'] for e in events};indices={e['stage']:i for i,e in enumerate(events)};records=[]
    for ext in ('cdx','cdxml'):
        issues=[]
        try:
            before=stage['before_'+ext];edited=stage['motion_edited_'+ext];reopened=stage['motion_reopened_'+ext];intent=stage['motion_intent_'+ext]
            if not indices['before_'+ext]<indices['motion_intent_'+ext]<indices['motion_edited_'+ext]<indices['motion_reopened_'+ext]:raise ValueError('Intent/event ordering invalid')
            if before['warnings']!=0:issues.append('preexisting_native_warnings')
            expected=expected_motion(before,intent);account_changed_text_bounds(expected,edited,intent);issues+=compare(expected,edited);issues+=compare(edited,reopened)
            diagnostic_intent=stage['diagnostic_intent_'+ext];diagnostic=stage['diagnostic_edited_'+ext];checked=stage['diagnostic_reopened_'+ext]
            if not indices['motion_reopened_'+ext]<indices['diagnostic_intent_'+ext]<indices['diagnostic_edited_'+ext]<indices['diagnostic_reopened_'+ext]:raise ValueError('Diagnostic intent ordering invalid')
            expected=expected_diagnostic(reopened,diagnostic_intent)
            account_changed_text_bounds(expected,diagnostic,diagnostic_intent)
            if not 0<=diagnostic['warnings']<=reopened['warnings']+2:issues.append('unexpected_diagnostic_warnings')
            expected['warnings']=diagnostic['warnings']
            target=diagnostic_intent['charge_change']['id']
            # Charge-dependent display text is a named diagnostic-only change;
            # H/bonds/stereo and unrelated objects remain fixed. Exact modified
            # label text must survive reopening, and is not accepted chemistry.
            next(a for a in expected['atoms'] if a['id']==target)['label']=next(a for a in diagnostic['atoms'] if a['id']==target)['label']
            issues+=compare(expected,diagnostic);issues+=compare(diagnostic,checked)
        except (KeyError,ValueError,StopIteration,TypeError) as exc:issues.append('incomplete_or_invalid_evidence:'+str(exc))
        records.append({'source_format':ext,'native_edit_save_reopen':'pass' if not issues else 'failed','issues':issues,'diagnostic_chemistry_accepted':False})
    return {'results':records,'manual_active_correction_seconds':None,'scope':'Exact declared nonzero edits and all captured non-target chemical/drawable fields. Separate figure quality and owner acceptance required.'}


def verify(folder):
    events=[json.loads(line) for line in (folder/'events.jsonl').read_text(encoding='utf-8-sig').splitlines()]
    report=verify_events(events);(folder/'edit-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);a=p.parse_args();report=verify(a.folder);print(json.dumps(report));raise SystemExit(0 if all(x['native_edit_save_reopen']=='pass' for x in report['results']) else 1)
