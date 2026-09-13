"""Typed evidence checks, not native extraction or human identity authentication."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
from datetime import datetime
from decimal import Decimal
import json
import math
from pathlib import Path
import sys

try:
    from .common import require, read_json, validate_schema, asset_bytes
except ImportError:
    from common import require, read_json, validate_schema, asset_bytes

FIELDS = {
    'fragment': {'fragment_translation': 'position', 'fragment_rotation': 'rotation_deg'},
    'atom': {'atom_displacement': 'position'},
    'bond': {'bond_anchors': 'anchors'},
    'electron_flow': {'curve_anchors': 'anchors', 'curve_control_points': 'control_points'},
    'reaction_arrow': {'curve_anchors': 'anchors', 'curve_control_points': 'control_points'},
    'lone_pair': {'lone_pair_displacement': 'position'},
    'charge': {'charge_displacement': 'position'},
    'caption': {'caption_displacement': 'position'},
}
# Reuse the existing archival IR schema, without claiming its chemistry checker.
_corpus_spec = spec_from_file_location('quality_corpus_schema', Path(__file__).resolve().parents[1] / 'corpus' / 'validate_corpus.py')
_corpus = module_from_spec(_corpus_spec)
_corpus_spec.loader.exec_module(_corpus)

STAGES = ('first', 'final')
FORMATS = ('cdx', 'cdxml')
SCOPES = ('chemical', 'editability', 'visual', 'human_review')


def unique(rows, key='id'):
    result = {r[key]: r for r in rows}
    require(len(result) == len(rows), 'duplicate identity: ' + key)
    return result


def finite(value):
    if isinstance(value, float):
        require(math.isfinite(value), 'nonfinite number')
    elif isinstance(value, dict):
        for item in value.values():
            finite(item)
    elif isinstance(value, list):
        for item in value:
            finite(item)


def stamp(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, AttributeError) as exc:
        raise ValueError('invalid timestamp') from exc
    require(result.tzinfo is not None and result.utcoffset() is not None,
            'timestamp needs timezone')
    return result


def close(a, b):
    if isinstance(a, list) or isinstance(b, list):
        return isinstance(a, list) and isinstance(b, list) and len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    if isinstance(a, (float, int)) and isinstance(b, (float, int)):
        return math.isclose(a, b, rel_tol=0, abs_tol=1e-7)
    return a == b


def subtract(after, before):
    if isinstance(after, list):
        return [subtract(a, b) for a, b in zip(after, before)]
    return after - before


def expected_delta(field, after, before):
    # A complete turn is the same orientation, not a geometric correction.
    if field == 'fragment_rotation':
        return (after - before + 180) % 360 - 180
    return subtract(after, before)


def validate_record(value, base_dir: Path):
    """Validate supplied files/records. Never infer authentication or run ChemDraw."""
    finite(value)
    validate_schema('correction-record.schema.json', value)
    base_dir = Path(base_dir).resolve()
    assets = unique(value['assets'])
    for asset in assets.values():
        asset_bytes(asset, base_dir)
        require(set(asset['derived_from']) <= assets.keys(), 'missing parent asset')
    visiting, finished = set(), set()
    def visit(key):
        require(key not in visiting, 'asset lineage cycle')
        if key in finished:
            return
        visiting.add(key)
        for parent in assets[key]['derived_from']:
            visit(parent)
        visiting.remove(key)
        finished.add(key)
    for key in assets:
        visit(key)
    def refs(items, kind=None):
        require(set(items) <= assets.keys(), 'unknown evidence asset')
        if kind:
            require(all(assets[i]['kind'] == kind for i in items), 'evidence asset kind mismatch: ' + kind)
    snapshots = value['snapshots']
    require(snapshots['first']['revision_id'] != snapshots['final']['revision_id'], 'immutable revisions must differ')
    render_events = {}
    render_sets = {}
    for stage, snapshot in snapshots.items():
        for kind in ('ir', 'cdx', 'cdxml'):
            refs([snapshot[kind + '_asset_ref']], kind)
        ir = read_json(base_dir / assets[snapshot['ir_asset_ref']]['path'])
        _corpus.syntax('mechanism-ir', ir)
        refs(snapshot['render_asset_refs'], 'native_render')
        render_sets[stage] = set(snapshot['render_asset_refs'])
        for render_id in snapshot['render_asset_refs']:
            render = assets[render_id]
            capture = render['render_provenance']
            native_ids = {snapshot['cdx_asset_ref'], snapshot['cdxml_asset_ref']}
            require(capture['native_asset_ref'] in native_ids, 'render belongs to different native revision')
            require(capture['native_sha256'] == assets[capture['native_asset_ref']]['sha256'] and capture['revision_id'] == snapshot['revision_id'], 'render source hash/revision mismatch')
            native_parents = {i for i in render['derived_from'] if assets[i]['kind'] in FORMATS}
            require(native_parents == {capture['native_asset_ref']}, 'render must have exactly its declared native parent')
            render_events[render_id] = stamp(capture['rendered_at'])
    require(not render_sets['first'] & render_sets['final'], 'first/final render asset reused')
    render_paths = {stage: {(base_dir / assets[i]['path']).resolve() for i in ids} for stage, ids in render_sets.items()}
    require(not render_paths['first'] & render_paths['final'], 'first/final render file reused')
    readings = unique(value['readbacks'], key='readback_asset_ref')
    by_stage = {(r['stage'], r['format']): r for r in readings.values()}
    require(set(by_stage) == {(s, f) for s in STAGES for f in FORMATS}, 'four stage/format readbacks required')
    objects, spacings = {}, {}
    evidence_events = dict(render_events)
    for key, reading in by_stage.items():
        stage, fmt = key
        snapshot = snapshots[stage]
        require(reading['native_asset_ref'] == snapshot[fmt + '_asset_ref'], 'readback native reference mismatch')
        refs([reading['readback_asset_ref']], 'native_readback')
        native = assets[reading['native_asset_ref']]
        payload = reading['payload']
        require(payload['source_asset_sha256'] == native['sha256'] and payload['source_revision_id'] == snapshot['revision_id'] and payload['format'] == fmt, 'readback source hash/revision/format mismatch')
        require(read_json(base_dir / assets[reading['readback_asset_ref']]['path']) == payload, 'readback payload differs from locked file')
        if reading['reopened_at'] is not None:
            reopened = stamp(reading['reopened_at'])
            evidence_events[reading['readback_asset_ref']] = reopened
            evidence_events[reading['native_asset_ref']] = max(reopened, evidence_events.get(reading['native_asset_ref'], reopened))
        if reading['status'] == 'pass':
            require(reading['reopened_at'] is not None, 'passed readback needs reopen time')
        objects[key] = unique(payload['objects'])
        spacings[key] = unique(payload['step_spacings'])
        primary_semantics = set()
        for item in objects[key].values():
            role = item.get('representation_role', 'primary')
            if role == 'primary' and item['kind'] != 'caption' and item['semantic_ref'] is not None:
                identity = (item['kind'], item['semantic_ref'])
                require(identity not in primary_semantics, 'duplicate primary semantic occurrence in native snapshot')
                primary_semantics.add(identity)
            if role == 'auxiliary':
                parent = objects[key].get(item['primary_object_ref'])
                require(parent is not None and parent.get('representation_role', 'primary') == 'primary' and parent['kind'] == item['kind'] and parent['semantic_ref'] == item['semantic_ref'], 'auxiliary graphic has invalid primary object')
            needed = set(FIELDS[item['kind']].values())
            require(all((g in needed) == (x is not None) for g, x in item['geometry'].items()), 'object geometry fields incomplete or unsupported')
        expected_pairs = set(zip(value['step_ids'], value['step_ids'][1:]))
        pairs = {(x['from_step'], x['to_step']) for x in spacings[key].values()}
        require(pairs == expected_pairs and len(pairs) == len(spacings[key]), 'step spacing inventory incomplete')
    frames = {r['payload']['coordinate_frame'] for r in readings.values()}
    require(len(frames) == 1, 'normalize readbacks to one declared coordinate frame')
    frame = next(iter(frames))
    correspondence = unique(value['correspondences'], key='entity_id')
    used = {key: set() for key in by_stage}
    required_diffs = {}
    complete_correspondence = True
    for entity, row in correspondence.items():
        refs(row['evidence_refs'])
        role = row.get('representation_role', 'primary')
        primary_row = None
        if role == 'auxiliary':
            primary_row = correspondence.get(row['primary_entity_ref'])
            require(primary_row is not None and primary_row.get('representation_role', 'primary') == 'primary' and primary_row['kind'] == row['kind'] and primary_row['semantic_ref'] == row['semantic_ref'], 'auxiliary correspondence has invalid primary entity')
        mapped = {}
        for stage in STAGES:
            for fmt in FORMATS:
                key = (stage, fmt)
                locator = row[stage][fmt]
                if locator is None:
                    complete_correspondence = False
                    continue
                require(locator in objects[key] and locator not in used[key], 'missing or multiply mapped object')
                used[key].add(locator)
                item = objects[key][locator]
                require(item['kind'] == row['kind'] and item['semantic_ref'] == row['semantic_ref'] and item.get('representation_role', 'primary') == role, 'correspondence semantic identity/kind/role mismatch')
                if primary_row is not None:
                    require(item['primary_object_ref'] == primary_row[stage][fmt], 'auxiliary graphic mapped to different primary occurrence')
                mapped[key] = item
        if row['status'] != 'unique' or len(mapped) != 4:
            complete_correspondence = False
            continue
        require(row['evidence_refs'], 'unique correspondence needs evidence')
        for stage in STAGES:
            require(close(mapped[(stage, 'cdx')]['geometry'], mapped[(stage, 'cdxml')]['geometry']), 'CDX/CDXML geometry disagreement')
        for field, attr in FIELDS[row['kind']].items():
            required_diffs[(entity, field)] = (mapped[('first', 'cdxml')]['geometry'][attr], mapped[('final', 'cdxml')]['geometry'][attr])
    require(all(used[key] == objects[key].keys() for key in used), 'object correspondence inventory incomplete')
    spacing_ids = set(spacings[('first', 'cdxml')])
    require(all(set(v) == spacing_ids for v in spacings.values()), 'step spacing identity mismatch')
    for sid in spacing_ids:
        rows = {k: v[sid] for k, v in spacings.items()}
        require(len({(r['from_step'], r['to_step']) for r in rows.values()}) == 1, 'step spacing endpoints changed')
        for stage in STAGES:
            require(close(rows[(stage, 'cdx')]['value_pt'], rows[(stage, 'cdxml')]['value_pt']), 'CDX/CDXML spacing disagreement')
        required_diffs[(sid, 'step_spacing')] = (rows[('first', 'cdxml')]['value_pt'], rows[('final', 'cdxml')]['value_pt'])
    diffs = {(d['entity_id'], d['field']): d for d in value['diffs']}
    require(len(diffs) == len(value['diffs']), 'duplicate diff identity')
    require(diffs.keys() == required_diffs.keys(), 'diff inventory incomplete or unsupported')
    changed = 0
    for key, (before, after) in required_diffs.items():
        diff = diffs[key]
        require(diff['coordinate_frame'] == frame, 'diff coordinate frame mismatch')
        require(close(diff['before'], before) and close(diff['after'], after), 'diff values disagree with native readback record')
        delta = expected_delta(key[1], after, before)
        require(close(diff['delta'], delta), 'incorrect numerical delta')
        changed += (not close(delta, 0)) if key[1] == 'fragment_rotation' else (not close(before, after))
    for field, status in value['diff_coverage'].items():
        expected = 'complete' if any(k[1] == field for k in required_diffs) else 'not_applicable'
        require(status == expected, 'incorrect diff coverage: ' + field)
    provenance = value['provenance']
    created = stamp(provenance['created_at'])
    refs(provenance['evidence_refs'], 'provenance')
    p = value['partition']
    tags = set(p['benchmark_tags'])
    canonical = value['sample_id'].upper()
    if canonical in ('M1', 'M2'):
        require(canonical in tags, 'named benchmark missing tag')
        require(p['exposure'] in ('exposed', 'exposed_and_tuned'), 'named benchmark must retain exposure')
    unique(p['ancestors'], 'sample_id')
    require(value['sample_id'] not in {a['sample_id'] for a in p['ancestors']}, 'self ancestry')
    for ancestor in p['ancestors']:
        named = ancestor['sample_id'].upper()
        if named in ('M1', 'M2'):
            require(named in ancestor['benchmark_tags'], 'named benchmark ancestor missing tag')
            require(ancestor['exposure'] in ('exposed', 'exposed_and_tuned'), 'named benchmark ancestor must retain exposure')
        tags.update(ancestor['benchmark_tags'])
        if ancestor['relation'] == 'same_semantics' and ancestor['exposure'] != 'unseen':
            require(p['exposure'] != 'unseen', 'same-semantics derivative erases exposure')
    locked = bool(tags & {'M2', 'future_holdout'}) or p['split'] in ('fixed_regression', 'evaluation_reserved') or any(a['split'] in ('fixed_regression', 'evaluation_reserved') and 'M1' not in a['benchmark_tags'] for a in p['ancestors'])
    if locked:
        require(not p['uses']['tuning'] and not p['uses']['training'], 'evaluation lineage cannot tune/train')
        require(p['split'] in ('fixed_regression', 'evaluation_reserved', 'quarantined'), 'evaluation lineage assigned to development')
    if 'M1' in tags:
        require(p['exposure'] in ('exposed', 'exposed_and_tuned'), 'M1 must retain exposure')
    if p['split'] == 'evaluation_reserved':
        require(p['exposure'] == 'unseen', 'reserved input is not unseen')
    for use, permission in (('tuning','train'), ('training','train'), ('redistribution','redistribute')):
        if p['uses'][use]:
            require(provenance['rights_status'] == 'approved' and provenance['permissions'][permission], 'rights not cleared for ' + use)
    if p['uses']['tuning'] or p['uses']['training']:
        require(p['split'] == 'development' and value['requested_tier'] in ('silver','gold'), 'ungraded or excluded record cannot tune/train')
    timing = value['timing']
    active = Decimal(0)
    if timing['measurement'] == 'unmeasured':
        require(all(timing[k] is None for k in ('started_at','ended_at','wall_seconds','manual_active_seconds','automatic_seconds')) and not timing['sessions'], 'unmeasured timing must be null/empty')
    else:
        require(all(timing[k] is not None for k in ('started_at','ended_at','wall_seconds')), 'measured timing incomplete')
        start, end = stamp(timing['started_at']), stamp(timing['ended_at'])
        require(end >= start and close(timing['wall_seconds'], (end-start).total_seconds()), 'wall time disagrees with timestamps')
        intervals, active = [], Decimal(0)
        for session in timing['sessions']:
            a, b = stamp(session['started_at']), stamp(session['ended_at'])
            require(start <= a <= b <= end and session['active_seconds'] <= (b-a).total_seconds(), 'invalid active-time interval')
            require(session['actor_id'] == value['corrector']['id'] and value['corrector']['kind'] == 'human', 'active time needs human corrector')
            refs([session['evidence_ref']], 'timing_log')
            intervals.append((a,b)); active += Decimal(str(session['active_seconds']))
        intervals.sort()
        require(all(intervals[i][1] <= intervals[i+1][0] for i in range(len(intervals)-1)), 'overlapping active-time intervals')
        if timing['manual_active_seconds'] is not None:
            require(value['corrector']['kind'] == 'human' and bool(intervals) and active == Decimal(str(timing['manual_active_seconds'])), 'manual time not supported by sessions')
        else:
            require(not intervals, 'sessions require measured manual total')
        if timing['automatic_seconds'] is not None:
            require(timing['automatic_seconds'] <= timing['wall_seconds'], 'automatic time exceeds wall time')
    reviews = unique(value['reviews'])
    final_native = {snapshots['final'][f+'_asset_ref'] for f in FORMATS}
    scope_targets = {'chemical': {snapshots['first']['ir_asset_ref'], snapshots['final']['ir_asset_ref']}, 'editability': final_native | set(readings), 'visual': set(snapshots['final']['render_asset_refs']), 'human_review': final_native | set(snapshots['final']['render_asset_refs'])}
    for review in reviews.values():
        refs(review['target_asset_refs']); refs(review['evidence_refs'], 'review_evidence')
        require(stamp(review['reviewed_at']) >= created, 'review predates record provenance')
        if timing['ended_at'] is not None:
            require(stamp(review['reviewed_at']) >= stamp(timing['ended_at']), 'review predates correction completion')
        required_evidence = set(review['target_asset_refs'])
        if review['decision'] == 'accepted':
            required_evidence |= scope_targets[review['scope']]
        require(all(stamp(review['reviewed_at']) >= evidence_events[i] for i in required_evidence if i in evidence_events), 'review predates necessary native/readback/render evidence')
        if review['independent_of_author']:
            require(review['actor']['id'] != value['author']['id'], 'review author independence contradicts identity')
        if review['independent_of_corrector']:
            require(review['actor']['id'] != value['corrector']['id'], 'review corrector independence contradicts identity')
    eligible_scopes = {}
    for scope in SCOPES:
        status = value['statuses'][scope]
        require(set(status['review_refs']) <= reviews.keys(), 'unknown scope review')
        scoped = [reviews[i] for i in status['review_refs']]
        require(all(r['scope'] == scope for r in scoped), 'review attached to wrong scope')
        relevant_rejections = {r['id'] for r in reviews.values() if r['scope'] == scope and r['decision'] != 'accepted' and set(r['target_asset_refs']) & scope_targets[scope]}
        require(relevant_rejections <= set(status['review_refs']), 'recorded scope rejection omitted from status')
        accepted = [r for r in scoped if r['decision'] == 'accepted' and r['independent_of_author'] and r['independent_of_corrector'] and scope_targets[scope] <= set(r['target_asset_refs'])]
        if status['status'] == 'pass':
            require(accepted and not any(r['decision'] != 'accepted' for r in scoped), 'passed scope lacks uncontested independent review evidence')
        eligible_scopes[scope] = status['status'] == 'pass' and any(r['actor']['kind'] == 'human' for r in accepted)
    blockers = []
    conditions = {
        'actual observed human correction required': value['record_kind'] == 'observed_correction' and value['corrector']['kind'] == 'human',
        'positive measured human active time required': timing['manual_active_seconds'] is not None and active > 0 and any(s['active_seconds'] > 0 for s in timing['sessions']),
        'complete unique correspondence required': complete_correspondence,
        'chemical object occurrence references required': all(r['kind'] == 'caption' or r['semantic_ref'] is not None for r in correspondence.values()),
        'observed nonzero geometric correction required': changed > 0,
        'visible correction needs distinct first/final render bytes': not {assets[i]['sha256'] for i in render_sets['first']} & {assets[i]['sha256'] for i in render_sets['final']},
        'both native formats need distinct first/final bytes': all(assets[snapshots['first'][f+'_asset_ref']]['sha256'] != assets[snapshots['final'][f+'_asset_ref']]['sha256'] for f in FORMATS),
        'all independent scope reviews required': all(eligible_scopes.values()),
        'all native reopen records must pass': all(r['status'] == 'pass' for r in readings.values()),
        'storage/annotation rights must be approved': provenance['rights_status'] == 'approved' and provenance['permissions']['store'] and provenance['permissions']['annotate'],
        'quarantined records cannot qualify': value['requested_tier'] != 'quarantined' and p['split'] != 'quarantined',
    }
    for message, met in conditions.items():
        if not met:
            blockers.append(message)
    eligible = not blockers
    if value['requested_tier'] == 'gold':
        require(eligible, 'gold requirements missing: ' + '; '.join(blockers))
    return {'status':'pass', 'gold_eligible_by_record':eligible, 'identity_authenticated':False, 'actual_gold_collected':False, 'declared_tier':value['requested_tier'], 'eligibility_blockers':blockers, 'assets_hash_checked':len(assets), 'native_readback_records_checked':4, 'changed_diff_fields':changed, 'diff_coverage':value['diff_coverage'], 'ir_validation':'schema_only', 'native_execution':'not_performed', 'automatic_object_matching':'not_implemented', 'production_native_diff':'not_implemented'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate_record(read_json(args.record), args.record.resolve().parent), indent=2))
        return 0
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps({'status':'failed', 'error':str(exc)}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
