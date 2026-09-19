"""Actual controller tests with independent fake worker effects; never use COM."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import uuid
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'probes'))
import lifecycle_controller as lc
import native_edit_loop as producer


class FakeWorker:
    def __init__(self, mode='valid'):
        self.mode = mode
        self.spawns = 0
        self.effects = 0
        self.identity = {'pid': 1234, 'start_utc': '2026-09-19T12:00:00+00:00', 'executable': 'portable-fake-worker'}
        self.alive = True
        self.folder = None
        self.document = str(uuid.uuid4())
        self.entered = threading.Event()
        self.release = threading.Event()

    def observe(self, identity):
        if not self.alive:
            return None
        if self.mode == 'stale':
            return {**self.identity, 'start_utc': '2026-09-20T12:00:00+00:00'}
        return self.identity

    def payload(self, q):
        revision = 0 if q['action'] == 'open-copy' else q['revision'] + (q['action'] != 'inspect')
        doc = self.document if q['action'] in {'open-copy', 'reopen'} else q['document_id']
        return {**{k: q[k] for k in ('action','request_id','operation_id','session_id','generation')},
                'ok': True, 'document_id': doc, 'revision': revision,
                'readiness': {'state':'not_ready' if q.get('end_session') else 'ready','document_bound':True,'observations_complete':True},
                'source_sha256': q.get('expected_sha256'), 'baseline_stability': {'ok':True},
                'observation': {'session_id':q['session_id'],'document_id':doc,'revision':revision,
                                'binding':{'pid':6789,'start_utc':'2026-09-19T12:00:01+00:00','hwnd':12,'executable':'portable-fake-native'}},
                'detail': {}}

    def deliver(self, q=None, mode=None):
        q = q or lc.read(self.folder / 'init.json')['request']
        mode = mode or self.mode
        raw = self.payload(q)
        if mode == 'wrong_identity':
            raw['request_id'] = str(uuid.uuid4())
        elif mode == 'wrong_generation':
            raw['generation'] = str(uuid.uuid4())
        elif mode == 'wrong_shape':
            raw['observation']['binding']['pid'] = 'invented'
        elif mode == 'not_ready':
            raw['readiness']['observations_complete'] = False
        elif mode == 'wrong_scope':
            raw['observation']['document_id'] = str(uuid.uuid4())
        elif mode == 'failed_legacy_false':
            raw.update(ok=False, native_write=False, reason='after an independently counted effect')
        path = self.folder / 'replies' / (q['request_id'] + '.json')
        if mode in {'malformed', 'truncated'}:
            path.write_bytes(b'{"ok": true,' if mode == 'truncated' else b'NOT JSON')
        else:
            lc.atomic(path, raw)

    def spawn(self, folder):
        self.spawns += 1
        self.effects += 1
        self.folder = folder
        self.entered.set()
        if self.mode == 'blocked_spawn':
            if not self.release.wait(3):
                raise AssertionError('test did not release spawn')
        if self.mode == 'dead':
            self.alive = False
        elif self.mode not in {'timeout', 'stale'}:
            self.deliver(mode='valid' if self.mode == 'blocked_spawn' else None)
        return self.identity


class LifecycleProducerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / 'ordinary.cdxml'
        self.source.write_text('<CDXML/>', encoding='utf-8')
        self.state = self.base / 'state'
        self.request = {'action':'open-copy','request_id':str(uuid.uuid4()),
                        'source':str(self.source),'expected_sha256':lc.file_hash(self.source),'role':'workflow-control'}

    def submit(self, worker=None, request=None, **kw):
        result = producer.submit(request or self.request, self.state, timeout=kw.pop('timeout', 1.0),
                                 result_version=lc.VERSION, _backend=worker, **kw)
        if result.get('result_version') == lc.VERSION:
            lc.validator().validate(result)
        elif result.get('result_version') == 'edit-preflight-error/0.1':
            from jsonschema import Draft202012Validator
            Draft202012Validator(lc.read(ROOT/'contracts/output/edit-preflight-error.schema.json')).validate(result)
        return result

    def test_frozen_default_never_copies_or_dispatches(self):
        result = self.submit()
        self.assertEqual(('refused', 'none', 'not_created'), (result['status'], result['mutation_outcome'], result['session_state']))
        self.assertFalse(self.state.exists())

    def test_legacy_contract_is_explicitly_frozen(self):
        result = producer.submit(self.request, self.state)
        self.assertIs(result['native_write'], False)
        self.assertFalse(self.state.exists())

    def test_valid_reply_round_trip_and_dedup(self):
        worker = FakeWorker()
        first = self.submit(worker)
        second = self.submit(worker)
        self.assertEqual('completed', first['status'])
        self.assertEqual('ready', first['lifecycle']['worker_state'])
        self.assertEqual(first, second)
        self.assertEqual((1,1), (worker.spawns,worker.effects))

    def test_changed_payload_same_id_is_refused(self):
        worker = FakeWorker()
        first = self.submit(worker)
        changed = {**self.request,'role':'development-copy'}
        result = self.submit(worker, changed)
        self.assertEqual('IDEMPOTENCY_CONFLICT', result['error']['code'])
        self.assertEqual(first['operation_id'], result['operation_id'])
        self.assertEqual(1, worker.spawns)

    def test_invalid_outputs_after_effect_preserve_identity_and_unknown(self):
        for mode in ('malformed','truncated','wrong_shape','wrong_identity','wrong_generation','not_ready','wrong_scope','failed_legacy_false'):
            with self.subTest(mode=mode):
                self.state = self.base / mode
                worker = FakeWorker(mode)
                result = self.submit(worker)
                self.assertEqual('outcome_unknown', result['status'])
                self.assertEqual('unknown', result['mutation_outcome'])
                self.assertEqual(self.request['request_id'], result['request_id'])
                self.assertIsNotNone(result['operation_id'])
                self.assertEqual(worker.folder.name, result['session_id'])
                self.assertIs(result['error']['retryable'], False)
                self.assertNotIn('native_write', result)
                again = self.submit(worker)
                self.assertEqual(result['operation_id'], again['operation_id'])
                self.assertEqual((1,1), (worker.spawns,worker.effects))
                self.assertTrue(list((self.state/'.lifecycle-v02'/'attempts'/self.request['request_id']/'receipts').glob('raw-*')))

    def test_timeout_is_bounded_and_late_reply_does_not_replay(self):
        worker = FakeWorker('timeout')
        started = time.monotonic()
        first = self.submit(worker, timeout=.05)
        self.assertLess(time.monotonic()-started, 1)
        self.assertEqual('JOB_TIMEOUT', first['error']['code'])
        self.assertTrue(worker.alive)
        worker.deliver(mode='valid')
        late = self.submit(worker)
        self.assertEqual(first['operation_id'], late['operation_id'])
        self.assertEqual('known', late['mutation_outcome'])
        self.assertEqual('unknown', late['session_state'])
        self.assertTrue(late['lifecycle']['quarantined'])
        self.assertEqual(1, worker.spawns)
        receipts = list((self.state/'.lifecycle-v02'/'attempts'/self.request['request_id']/'receipts').glob('receipt-*'))
        self.assertGreaterEqual(len(receipts), 2)

    def test_worker_exit_and_pid_reuse_are_not_ready(self):
        for mode, expected in [('dead','dead'),('stale','stale')]:
            with self.subTest(mode=mode):
                self.state=self.base/mode
                worker=FakeWorker(mode)
                result=self.submit(worker)
                self.assertEqual('unknown', result['mutation_outcome'])
                self.assertEqual(expected, result['lifecycle']['worker_state'])
                self.assertEqual(1,worker.spawns)

    def test_completed_old_reply_does_not_restore_rebooted_worker(self):
        worker=FakeWorker()
        first=self.submit(worker)
        worker.mode='stale'
        after=self.submit(worker)
        self.assertEqual('failed',after['status'])
        self.assertEqual('known',after['mutation_outcome'])
        self.assertEqual('stale',after['lifecycle']['worker_state'])
        self.assertEqual(first['operation_id'],after['operation_id'])
        self.assertEqual(1,worker.spawns)

    def test_crash_gaps_never_redispatch(self):
        for stage,spawns,outcome in [('intent_persisted',0,'none'),('prepared',0,'none'),('spawn_intent',0,'unknown'),('spawn_returned',1,'unknown'),('worker_persisted',1,'unknown')]:
            with self.subTest(stage=stage):
                self.state=self.base/stage
                worker=FakeWorker('timeout')
                def fail(point,current):
                    if point==stage: raise OSError('injected crash boundary '+stage)
                first=self.submit(worker,_checkpoint=fail)
                second=self.submit(worker)
                self.assertEqual(outcome,first['mutation_outcome'])
                self.assertEqual(first['operation_id'],second['operation_id'])
                self.assertEqual(spawns,worker.spawns)
                self.assertEqual(spawns,worker.effects)

    def test_two_clients_share_one_startup_attempt(self):
        worker=FakeWorker('blocked_spawn'); results=[]
        thread=threading.Thread(target=lambda: results.append(self.submit(worker)))
        thread.start()
        self.assertTrue(worker.entered.wait(2))
        concurrent=self.submit(worker)
        worker.release.set(); thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(results[0]['operation_id'],concurrent['operation_id'])
        self.assertEqual(1,worker.spawns)
        self.assertEqual('completed',self.submit(worker)['status'])

    def test_new_id_cannot_bypass_unresolved_startup(self):
        worker=FakeWorker('timeout'); self.submit(worker)
        result=self.submit(worker,{**self.request,'request_id':str(uuid.uuid4())})
        self.assertEqual('refused',result['status'])
        self.assertEqual(1,worker.spawns)

    def test_existing_legacy_directory_is_not_adopted(self):
        old=self.state/str(uuid.uuid4()); old.mkdir(parents=True)
        evidence=old/'UNCERTAIN.json'; evidence.write_bytes(b'original bytes')
        worker=FakeWorker()
        self.assertEqual('refused',self.submit(worker)['status'])
        self.assertEqual(b'original bytes',evidence.read_bytes())
        self.assertEqual(0,worker.spawns)

    def test_canonical_path_alias_deduplicates(self):
        worker=FakeWorker(); first=self.submit(worker)
        self.state=self.state/'..'/'state'
        second=self.submit(worker)
        self.assertEqual(first['operation_id'],second['operation_id'])
        self.assertEqual(1,worker.spawns)

    def test_stale_controller_claim_is_preserved(self):
        lock=self.state/'.lifecycle-v02'/'controller.lock'; lock.mkdir(parents=True)
        worker=FakeWorker()
        self.assertEqual('refused',self.submit(worker)['status'])
        self.assertTrue(lock.is_dir()); self.assertEqual(0,worker.spawns)

    def test_source_mismatch_before_spawn_reports_none(self):
        self.source.write_text('changed original')
        worker=FakeWorker(); result=self.submit(worker)
        self.assertEqual('none',result['mutation_outcome'])
        self.assertEqual(self.request['request_id'],result['request_id'])
        self.assertEqual(0,worker.spawns)

    def test_storage_failure_after_effect_retains_trusted_ids(self):
        worker=FakeWorker()
        original=lc.atomic
        def fail(path,value):
            if Path(path).name.startswith('receipt-'): raise OSError('disk full')
            return original(path,value)
        with patch.object(lc,'atomic',fail): result=self.submit(worker)
        self.assertEqual('known',result['mutation_outcome'])
        self.assertEqual(self.request['request_id'],result['request_id'])
        self.assertIsNotNone(result['operation_id'])
        self.assertEqual(1,worker.effects)

    def test_failed_reply_publication_never_looks_completed(self):
        target=self.base/'atomic.json'
        with patch.object(lc.os,'replace',side_effect=OSError('interrupted publication')):
            with self.assertRaises(OSError): lc.atomic(target,{'ok':True})
        self.assertFalse(target.exists())
        self.assertEqual(1,len(list(self.base.glob('atomic.json.*.tmp'))))

    def test_invalid_request_and_deadline_do_not_dispatch(self):
        worker=FakeWorker()
        bad=self.submit(worker,{**self.request,'unexpected':True})
        self.assertEqual('not_started',bad['dispatch'])
        bad=self.submit(worker,timeout=float('nan'))
        self.assertEqual('none',bad['mutation_outcome'])
        self.assertEqual(0,worker.spawns)


    def command(self, worker, previous, action='inspect', **fields):
        self.assertEqual('completed',previous['status'],previous)
        q={'action':action,'request_id':str(uuid.uuid4()),'session_id':previous['session_id'],
           'document_id':previous['document_id'],'revision':previous['revision'],**fields}
        def answer():
            path=worker.folder/'inbox'/(q['request_id']+'.json')
            deadline=time.monotonic()+2
            while not path.exists() and time.monotonic()<deadline: time.sleep(.002)
            if path.exists():
                worker.effects+=1
                worker.deliver(lc.read(path),mode='valid')
        thread=threading.Thread(target=answer);thread.start()
        result=self.submit(worker,q,timeout=.5);thread.join(2)
        return q,result

    def test_ending_while_worker_alive_refuses_new_enqueue(self):
        worker=FakeWorker();opened=self.submit(worker)
        end_request,ending=self.command(worker,opened,end_session=True)
        self.assertEqual(('pending','ending'),(ending['status'],ending['session_state']))
        self.assertEqual('not_ready',ending['lifecycle']['worker_state'])
        self.assertTrue(worker.alive)
        new_request={'action':'inspect','request_id':str(uuid.uuid4()),'session_id':opened['session_id'],
                     'document_id':opened['document_id'],'revision':opened['revision']}
        refused=self.submit(worker,new_request)
        self.assertEqual('refused',refused['status'])
        self.assertFalse((worker.folder/'inbox'/(new_request['request_id']+'.json')).exists())
        same=self.submit(worker,end_request)
        self.assertEqual(ending['operation_id'],same['operation_id'])
        self.assertEqual(2,worker.effects)
        stored=lc.read(self.state/'.lifecycle-v02'/'attempts'/end_request['request_id']/'state.json')
        self.assertEqual('ending',stored['session_state'])
        self.assertFalse(stored['ready'])


    def closure(self, worker, q, state='closed', exited=True):
        wire=lc.read(worker.folder/'inbox'/(q['request_id']+'.json'))
        app={'context_id':str(uuid.uuid4()),'generation':wire['generation'],'session_state':state,
             'observed_process_exit':exited,'ownership_verified':True,'saved_revision_verified':state=='detached',
             'document_id':q['document_id'],'revision':q['revision'],
             'owned_binding':{'pid':6789,'start_utc':'2026-09-19T12:00:01+00:00','executable':'portable-fake-native'},
             'ownership_transferred_to_user':state=='detached'}
        raw={'session_id':wire['session_id'],'generation':wire['generation'],'operation_id':wire['operation_id'],
             'session_state':state,'observed_process_exit':exited,'applications':[app],
             'ownership_transferred_to_user':state=='detached','document_close_returned':True,'application_quit_returned':True}
        lc.atomic(worker.folder/'closed.json',raw)

    def test_same_attempt_closure_reconciles_without_replay(self):
        worker=FakeWorker();opened=self.submit(worker)
        q,ending=self.command(worker,opened,end_session=True)
        self.closure(worker,q)
        worker.alive=False
        closed=self.submit(worker,q)
        self.assertEqual(('completed','known','closed'),(closed['status'],closed['mutation_outcome'],closed['session_state']))
        self.assertEqual(ending['operation_id'],closed['operation_id'])
        self.assertTrue(closed['details']['closure_receipt_id'])
        self.assertEqual(2,worker.effects)
        following=FakeWorker()
        new=self.submit(following,{**self.request,'request_id':str(uuid.uuid4())})
        self.assertEqual('completed',new['status'])
        self.assertEqual(1,following.spawns)

    def test_quit_return_without_exit_does_not_release_session(self):
        worker=FakeWorker();opened=self.submit(worker)
        q,ending=self.command(worker,opened,end_session=True)
        self.closure(worker,q,state='ending',exited=False)
        result=self.submit(worker,q)
        self.assertEqual('ending',result['session_state'])
        following=self.submit(worker,{**self.request,'request_id':str(uuid.uuid4())})
        self.assertEqual('refused',following['status'])
        self.assertEqual(1,worker.spawns)

    def test_detach_requires_explicit_saved_transfer_evidence(self):
        worker=FakeWorker();opened=self.submit(worker)
        q,ending=self.command(worker,opened,end_session=True,keep_open=True)
        self.closure(worker,q,state='detached',exited=False)
        result=self.submit(worker,q)
        self.assertEqual('detached',result['session_state'])
        self.assertTrue(worker.alive)
        self.assertEqual(2,worker.effects)
        denied=self.submit(worker,{'action':'inspect','request_id':str(uuid.uuid4()),'session_id':result['session_id'],
                                   'document_id':result['document_id'],'revision':result['revision']})
        self.assertEqual('refused',denied['status'])

    def test_false_closed_container_is_quarantined(self):
        worker=FakeWorker();opened=self.submit(worker)
        q,ending=self.command(worker,opened,end_session=True)
        self.closure(worker,q,state='closed',exited=False)
        result=self.submit(worker,q)
        self.assertEqual('failed',result['status'])
        self.assertEqual('known',result['mutation_outcome'])
        self.assertNotEqual('closed',result['session_state'])
        self.assertEqual(2,worker.effects)

    def test_crashed_os_process_leaves_claim_and_never_replays(self):
        script = """import sys,os,json;from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tests'))
from test_lifecycle_controller import FakeWorker
import lifecycle_controller as lc
stage,state,request=sys.argv[1:]
q=json.loads(request)
class Counted(FakeWorker):
 def spawn(self,folder):
  with (Path(state).parent/('effect-'+stage)).open('a') as f:f.write('effect\\n')
  return super().spawn(folder)
def checkpoint(point,current):
 if point==stage:os._exit(71)
lc.submit(q,Path(state),timeout=.2,_backend=Counted('timeout'),_checkpoint=checkpoint)
"""
        for stage,expected in [('intent_persisted',0),('prepared',0),('spawn_intent',0),('spawn_returned',1),('worker_persisted',1)]:
            with self.subTest(stage=stage):
                self.state=self.base/('crash-'+stage)
                run=subprocess.run([sys.executable,'-c',script,stage,str(self.state),json.dumps(self.request)],cwd=ROOT,capture_output=True,text=True)
                self.assertEqual(71,run.returncode,run.stderr)
                worker=FakeWorker();observed=self.submit(worker)
                self.assertEqual(self.request['request_id'],observed['request_id'])
                self.assertEqual(0,worker.spawns)
                self.assertTrue((self.state/'.lifecycle-v02'/'controller.lock').is_dir())
                effect=self.base/('effect-'+stage)
                self.assertEqual(expected,int(effect.exists()))


    def test_corrupt_state_recovers_intent_ids_and_never_reports_none(self):
        worker=FakeWorker('timeout');first=self.submit(worker)
        attempt=self.state/'.lifecycle-v02'/'attempts'/self.request['request_id']
        (attempt/'state.json').write_bytes(b'corrupted state')
        result=self.submit(worker)
        self.assertEqual('unknown',result['mutation_outcome'])
        self.assertEqual(first['operation_id'],result['operation_id'])
        self.assertEqual(first['session_id'],result['session_id'])
        self.assertEqual(1,worker.spawns)
        self.assertEqual(b'corrupted state',(attempt/'state.json').read_bytes())
        (attempt/'intent.json').write_bytes(b'corrupted intent')
        unknown=self.submit(worker)
        self.assertEqual('unknown',unknown['mutation_outcome'])
        self.assertIsNone(unknown['operation_id'])
        self.assertEqual(1,worker.spawns)

    def test_forged_terminal_filename_does_not_release_active_owner(self):
        worker=FakeWorker('timeout');first=self.submit(worker)
        terminal=self.state/'.lifecycle-v02'/'terminal-sessions';terminal.mkdir()
        (terminal/(first['session_id']+'.json')).write_text('{}')
        result=self.submit(worker,{**self.request,'request_id':str(uuid.uuid4())})
        self.assertEqual('refused',result['status'])
        self.assertEqual(1,worker.spawns)

    def test_wrong_closure_operation_or_process_identity_does_not_release(self):
        for field in ('operation_id','process'):
            with self.subTest(field=field):
                self.state=self.base/field
                worker=FakeWorker();opened=self.submit(worker)
                q,ending=self.command(worker,opened,end_session=True)
                self.closure(worker,q)
                path=worker.folder/'closed.json';raw=lc.read(path)
                if field=='operation_id':raw['operation_id']=str(uuid.uuid4())
                else:raw['applications'][0]['owned_binding']['start_utc']='2026-09-20T12:00:01+00:00'
                lc.atomic(path,raw)
                result=self.submit(worker,q)
                self.assertEqual('known',result['mutation_outcome'])
                self.assertEqual('failed',result['status'])
                self.assertNotEqual('closed',result['session_state'])


    def test_cli_preflight_error_contract_has_no_invented_operation(self):
        from jsonschema import Draft202012Validator
        validate=Draft202012Validator(lc.read(ROOT/'contracts/output/edit-preflight-error.schema.json')).validate
        for payload in ('{bad json',json.dumps({**self.request,'action':'unknown'}),json.dumps({**self.request,'request_id':'not-an-id'})):
            with self.subTest(payload=payload[:30]):
                run=subprocess.run([sys.executable,str(ROOT/'probes/native_edit_loop.py'),'--result-version',lc.VERSION,
                                    '--state-dir',str(self.state)],input=payload,text=True,capture_output=True)
                self.assertEqual(2,run.returncode,run.stderr)
                result=json.loads(run.stdout);validate(result)
                self.assertEqual('not_started',result['dispatch'])
                self.assertNotIn('operation',result)
                self.assertNotIn('session_id',result)
        self.assertFalse(self.state.exists())


    def test_partial_json_registry_contract_recovers_original_identity(self):
        worker=FakeWorker('timeout');first=self.submit(worker)
        path=self.state/'.lifecycle-v02'/'attempts'/self.request['request_id']/'state.json'
        raw=lc.read(path);del raw['fingerprint'];lc.atomic(path,raw)
        result=self.submit(worker)
        self.assertEqual(first['operation_id'],result['operation_id'])
        self.assertEqual('unknown',result['mutation_outcome'])
        self.assertEqual(1,worker.effects)

    def test_closure_observer_failure_can_resume_same_reconciliation(self):
        worker=FakeWorker();opened=self.submit(worker)
        q,ending=self.command(worker,opened,end_session=True)
        self.closure(worker,q)
        original=worker.observe
        worker.observe=lambda identity: (_ for _ in ()).throw(OSError('temporary observer failure'))
        failed=self.submit(worker,q)
        self.assertEqual('known',failed['mutation_outcome'])
        worker.observe=original
        closed=self.submit(worker,q)
        self.assertEqual('closed',closed['session_state'])
        self.assertEqual(ending['operation_id'],closed['operation_id'])
        self.assertEqual(2,worker.effects)


    def test_malformed_state_field_types_recover_intact_intent(self):
        for key,value in [('request',[]),('operation_id',7)]:
            with self.subTest(key=key):
                self.state=self.base/key
                worker=FakeWorker();first=self.submit(worker)
                path=self.state/'.lifecycle-v02'/'attempts'/self.request['request_id']/'state.json'
                raw=lc.read(path);raw[key]=value;lc.atomic(path,raw)
                result=self.submit(worker)
                self.assertEqual(first['operation_id'],result['operation_id'])
                self.assertEqual('unknown',result['mutation_outcome'])
                self.assertEqual(1,worker.effects)

    def test_cli_opt_in_refusal_is_real_producer_output(self):
        run=subprocess.run([sys.executable,str(ROOT/'probes/native_edit_loop.py'),'--result-version',lc.VERSION,
                            '--state-dir',str(self.state)],input=json.dumps(self.request),text=True,capture_output=True)
        self.assertEqual(2,run.returncode,run.stderr)
        result=json.loads(run.stdout); lc.validator().validate(result)
        self.assertEqual('CAPABILITY_UNVERIFIED',result['error']['code'])
        self.assertEqual(self.request['request_id'],result['request_id'])
        self.assertFalse(self.state.exists())


if __name__=='__main__': unittest.main()
