"""Portable owned-process lifecycle checks; never loads vendor COM code."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
PWSH = shutil.which('pwsh')


@unittest.skipUnless(PWSH, 'PowerShell 7 is required for the portable worker seam')
class OwnedLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = r'''
param([string]$HelperPath)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. $HelperPath
$results=@{}
function Run-Case([string]$Name,[hashtable]$Options){
    $script:fake=@{clock=0;closes=0;quits=0;observations=0;scope_observations=0;options=$Options}
    $context=@{creation_attempted=$true;application_created=$true;document_present=$true;saved_revision_verified=$true;
        binding=@{pid=42;start_utc='2026-09-19T00:00:00.0000000Z';executable='C:\\Synthetic\\ChemDraw.exe';hwnd=100};
        generation='generation-a';operation_id='operation-a';context_id='context-a';document_id='document-a';revision=7}
    if($Options.ContainsKey('document_present')){$context.document_present=$Options.document_present}
    if($Options.ContainsKey('created')){$context.application_created=$Options.created}
    if($Options.ContainsKey('attempted')){$context.creation_attempted=$Options.attempted}
    if($Options.ContainsKey('no_binding')){$context.binding=$null}
    if($Options.ContainsKey('saved')){$context.saved_revision_verified=$Options.saved}
    $observe={param($binding)
        $script:fake.observations++
        $opt=$script:fake.options
        if($opt.ContainsKey('process_error')){throw 'Process identity unavailable'}
        if(($opt.ContainsKey('absent_before')) -or ($script:fake.quits -gt 0 -and !$opt.ContainsKey('alive') -and !$opt.ContainsKey('reuse_after')) -or ($script:fake.closes -gt 0 -and $opt.ContainsKey('exit_on_close'))){return @{state='absent'}}
        $start=$binding.start_utc;$exe=$binding.executable
        if($opt.ContainsKey('reuse_before') -or ($script:fake.quits -gt 0 -and $opt.ContainsKey('reuse_after'))){$start='2026-09-19T00:00:01.0000000Z'}
        if($opt.ContainsKey('wrong_executable')){$exe='C:\\Synthetic\\Unrelated.exe'}
        return @{state='present';pid=42;start_utc=$start;executable=$exe}
    }
    $scope={
        $script:fake.scope_observations++
        $opt=$script:fake.options
        $count=if(($opt.ContainsKey('document_present') -and !$opt.document_present) -or $script:fake.closes -gt 0){0}else{1}
        if($opt.ContainsKey('extra_document')){$count=2}
        if($opt.ContainsKey('still_document') -and $script:fake.closes -gt 0){$count=1}
        return @{application_pid=42;hwnd=100;document_count=$count;retained_document_matches=(!$opt.ContainsKey('wrong_document'));retained_application=$true}
    }
    $close={$script:fake.closes++;if($script:fake.options.ContainsKey('close_error')){throw 'Synthetic close failed'}}
    $quit={$script:fake.quits++;if($script:fake.options.ContainsKey('quit_error')){throw 'Synthetic quit failed'}}
    $detach=$Options.ContainsKey('detach');$preserve=$Options.ContainsKey('preserve')
    $receipt=Invoke-OwnedLifecycleCleanup -Context $context -ObserveProcess $observe -ObserveApplication $scope -CloseDocument $close -QuitApplication $quit -Detach:$detach -Preserve:$preserve -TimeoutMilliseconds 120 -PollMilliseconds 50 -NowMilliseconds {$script:fake.clock} -Pause {param($ms)$script:fake.clock+=$ms}
    $script:results[$Name]=@{receipt=$receipt;closes=$script:fake.closes;quits=$script:fake.quits;clock=$script:fake.clock;observations=$script:fake.observations;scope_observations=$script:fake.scope_observations}
}
Run-Case 'failed_connect_no_document' @{document_present=$false}
Run-Case 'close_error' @{close_error=$true}
Run-Case 'quit_still_alive' @{alive=$true}
Run-Case 'quit_error_but_exited' @{quit_error=$true}
Run-Case 'pid_reused_before' @{reuse_before=$true}
Run-Case 'pid_reused_after_quit' @{reuse_after=$true}
Run-Case 'wrong_executable' @{wrong_executable=$true}
Run-Case 'ambiguous_document' @{extra_document=$true}
Run-Case 'wrong_document' @{wrong_document=$true}
Run-Case 'document_remains_after_close' @{still_document=$true}
Run-Case 'detach_saved' @{detach=$true}
Run-Case 'detach_unsaved' @{detach=$true;saved=$false}
Run-Case 'preserve' @{preserve=$true}
Run-Case 'absent' @{absent_before=$true}
Run-Case 'exit_on_close' @{exit_on_close=$true}
Run-Case 'process_error' @{process_error=$true}
Run-Case 'no_binding' @{no_binding=$true}
Run-Case 'creation_uncertain' @{created=$false;no_binding=$true}
Run-Case 'not_created' @{created=$false;attempted=$false;no_binding=$true}
$results|ConvertTo-Json -Depth 30 -Compress
'''
        with tempfile.TemporaryDirectory(prefix='chemdraw-owned-tests-') as directory:
            harness = Path(directory) / 'run.ps1'
            harness.write_text(script, encoding='utf-8')
            completed = subprocess.run([PWSH, '-NoProfile', '-File', str(harness), '-HelperPath', str(ROOT / 'probes' / 'lifecycle-owned.ps1')], capture_output=True, text=True, timeout=20)
        if completed.returncode:
            raise AssertionError(f'Portable helper harness failed ({completed.returncode}): {completed.stderr}\n{completed.stdout}')
        cls.cases = json.loads(completed.stdout)

    def assert_no_cleanup(self, name, state='unknown'):
        case = self.cases[name]
        self.assertEqual(case['closes'], 0)
        self.assertEqual(case['quits'], 0)
        self.assertFalse(case['receipt']['observed_process_exit'])
        self.assertEqual(case['receipt']['session_state'], state)

    def test_created_application_without_document_is_cleaned(self):
        case = self.cases['failed_connect_no_document']
        self.assertEqual((case['closes'], case['quits']), (0, 1))
        self.assertFalse(case['receipt']['document_close_returned'])
        self.assertTrue(case['receipt']['application_quit_returned'])
        self.assertTrue(case['receipt']['observed_process_exit'])
        self.assertEqual(case['receipt']['session_state'], 'closed')

    def test_close_failure_never_quits(self):
        case = self.cases['close_error']
        self.assertEqual((case['closes'], case['quits']), (1, 0))
        self.assertFalse(case['receipt']['document_close_returned'])
        self.assertFalse(case['receipt']['observed_process_exit'])
        self.assertEqual(case['receipt']['session_state'], 'unknown')

    def test_quit_return_is_not_exit_and_wait_is_bounded(self):
        case = self.cases['quit_still_alive']
        self.assertEqual((case['closes'], case['quits']), (1, 1))
        self.assertTrue(case['receipt']['document_close_returned'])
        self.assertTrue(case['receipt']['application_quit_returned'])
        self.assertFalse(case['receipt']['observed_process_exit'])
        self.assertEqual(case['receipt']['session_state'], 'ending')
        self.assertEqual(case['clock'], 120)
        self.assertLess(case['observations'], 12)

    def test_exit_observation_does_not_require_successful_quit_return(self):
        case = self.cases['quit_error_but_exited']
        self.assertFalse(case['receipt']['application_quit_returned'])
        self.assertTrue(case['receipt']['observed_process_exit'])
        self.assertEqual(case['receipt']['session_state'], 'closed')

    def test_pid_reuse_is_not_ownership_or_exit_proof(self):
        self.assert_no_cleanup('pid_reused_before')
        case = self.cases['pid_reused_after_quit']
        self.assertEqual(case['quits'], 1)
        self.assertFalse(case['receipt']['observed_process_exit'])
        self.assertEqual(case['receipt']['process_state'], 'identity_changed')
        self.assertEqual(case['receipt']['session_state'], 'unknown')

    def test_ownership_ambiguity_preserves_resources(self):
        for name in ['wrong_executable', 'ambiguous_document', 'wrong_document', 'process_error', 'no_binding', 'creation_uncertain']:
            with self.subTest(name=name):
                self.assert_no_cleanup(name)

    def test_close_return_does_not_authorize_quit_with_document_remaining(self):
        case = self.cases['document_remains_after_close']
        self.assertEqual((case['closes'], case['quits']), (1, 0))
        self.assertTrue(case['receipt']['document_close_returned'])
        self.assertFalse(case['receipt']['observed_process_exit'])
        self.assertEqual(case['receipt']['session_state'], 'unknown')

    def test_explicit_saved_detach_preserves_document(self):
        self.assert_no_cleanup('detach_saved', 'detached')
        self.assertTrue(self.cases['detach_saved']['receipt']['ownership_transferred_to_user'])
        self.assertTrue(self.cases['detach_saved']['receipt']['saved_revision_verified'])
        self.assert_no_cleanup('detach_unsaved')

    def test_explicit_preservation_never_closes(self):
        self.assert_no_cleanup('preserve')
        self.assertTrue(self.cases['preserve']['receipt']['preserved'])

    def test_absence_of_exact_owned_pid_proves_exit(self):
        for name in ['absent', 'exit_on_close']:
            with self.subTest(name=name):
                case = self.cases[name]
                self.assertEqual(case['quits'], 0)
                self.assertTrue(case['receipt']['observed_process_exit'])
                self.assertEqual(case['receipt']['session_state'], 'closed')

    def test_no_attempt_is_not_created(self):
        self.assert_no_cleanup('not_created', 'not_created')

    def test_context_identity_is_retained(self):
        for case in self.cases.values():
            self.assertEqual(case['receipt']['generation'], 'generation-a')
            self.assertEqual(case['receipt']['operation_id'], 'operation-a')
            self.assertEqual(case['receipt']['context_id'], 'context-a')
            self.assertEqual(case['receipt']['document_id'], 'document-a')
            self.assertEqual(case['receipt']['revision'], 7)
            self.assertIsInstance(case['receipt']['saved_revision_verified'], bool)



@unittest.skipUnless(PWSH, 'PowerShell 7 is required for the portable worker seam')
class FrozenWorkerTests(unittest.TestCase):
    def run_frozen_worker(self, initialization):
        workspace = tempfile.TemporaryDirectory(prefix='chemdraw-frozen-worker-')
        self.addCleanup(workspace.cleanup)
        root = Path(workspace.name)
        source = root / 'probes'
        source.mkdir()
        files = ['native-edit-loop.ps1', 'native_edit_loop.py', 'NativeChemDraw.cs',
                 'native-common.ps1', 'lifecycle-owned.ps1', 'lifecycle_controller.py']
        for name in files:
            shutil.copyfile(ROOT / 'probes' / name, source / name)
        marker = root / 'vendor-initialization-would-have-run'
        (source / 'native-common.ps1').write_text(
            "$ErrorActionPreference='Stop'\nSet-Content -LiteralPath '" + str(marker).replace("'", "''")
            + "' -Value 'unexpected'\nthrow 'Vendor initialization is prohibited in portable tests.'\n",
            encoding='utf-8')
        state = root / 'session'
        state.mkdir()
        (state / 'init.json').write_text(initialization if isinstance(initialization, str) else json.dumps(initialization), encoding='utf-8')
        completed = subprocess.run([PWSH, '-NoProfile', '-File', str(source / 'native-edit-loop.ps1'),
                                    '-SessionDirectory', str(state), '-PythonExe', 'python-is-not-used'],
                                   capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertFalse(marker.exists(), 'Frozen worker loaded vendor initialization')
        self.assertEqual(completed.stdout, '', 'Worker helpers must not leak values into stdout')
        return state, source

    def initialization(self):
        request = {name: str(uuid.uuid4()) for name in ['request_id', 'session_id', 'operation_id', 'generation']}
        request['action'] = 'open-copy'
        return {'request': request, 'operation_id': request['operation_id'], 'generation': request['generation']}

    def test_frozen_dispatch_returns_identity_without_loading_vendor_code(self):
        initialization = self.initialization()
        state, source = self.run_frozen_worker(initialization)
        request = initialization['request']
        reply = json.loads((state / 'replies' / (request['request_id'] + '.json')).read_text(encoding='utf-8'))
        for field in ['request_id', 'operation_id', 'generation', 'action', 'session_id']:
            self.assertEqual(reply[field], request[field])
        self.assertFalse(reply['ok'])
        self.assertFalse(reply['native_write'])
        self.assertFalse(reply['native_execution_enabled'])
        self.assertEqual(reply['reason'], 'native_execution_frozen')
        self.assertEqual(reply['readiness'], {'state': 'not_ready', 'document_bound': False, 'observations_complete': False})
        self.assertEqual(len(reply['tool_source_hashes']), 6)
        for name, digest in reply['tool_source_hashes'].items():
            self.assertEqual(digest, hashlib.sha256((source / name).read_bytes()).hexdigest())
        closed = json.loads((state / 'closed.json').read_text(encoding='utf-8'))
        self.assertEqual(closed['generation'], request['generation'])
        self.assertEqual(closed['session_state'], 'not_created')
        self.assertFalse(closed['observed_process_exit'])
        self.assertEqual(closed['applications'], [])
        status = json.loads((state / 'worker-status.json').read_text(encoding='utf-8'))
        self.assertEqual(status['generation'], request['generation'])
        self.assertFalse(status['native_execution_enabled'])
        self.assertFalse(list((state / 'replies').glob('*.tmp')))

    def test_malformed_initialization_leaves_failure_receipt(self):
        state, _ = self.run_frozen_worker('{')
        events = [json.loads(line) for line in (state / 'events.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertIn('worker_failure', [event['stage'] for event in events])
        closed = json.loads((state / 'closed.json').read_text(encoding='utf-8'))
        self.assertTrue(closed['poisoned'])
        self.assertIsNone(closed['generation'])
        self.assertEqual(closed['session_state'], 'not_created')
        self.assertFalse(closed['observed_process_exit'])

    def test_initialization_identity_mismatch_retains_known_request_context(self):
        initialization = self.initialization()
        initialization['operation_id'] = str(uuid.uuid4())
        state, _ = self.run_frozen_worker(initialization)
        request = initialization['request']
        reply = json.loads((state / 'replies' / (request['request_id'] + '.json')).read_text(encoding='utf-8'))
        self.assertEqual(reply['operation_id'], request['operation_id'])
        self.assertEqual(reply['generation'], request['generation'])
        self.assertEqual(reply['session_id'], request['session_id'])
        self.assertFalse(reply['ok'])
        self.assertEqual(reply['readiness']['state'], 'unknown')

    def test_atomic_publication_preserves_first_receipt_on_duplicate(self):
        script = r"""
param([string]$HelperPath,[string]$ReceiptPath)
$ErrorActionPreference='Stop'
. $HelperPath
Write-LifecycleJson -Path $ReceiptPath -Value @{sequence=1;complete=$true} -NoOverwrite
$refused=$false
try{Write-LifecycleJson -Path $ReceiptPath -Value @{sequence=2;complete=$true} -NoOverwrite}catch{$refused=$true}
@{refused=$refused;receipt=(Get-Content -LiteralPath $ReceiptPath -Raw|ConvertFrom-Json)}|ConvertTo-Json -Compress
"""
        with tempfile.TemporaryDirectory(prefix='chemdraw-atomic-receipt-') as directory:
            harness = Path(directory) / 'test.ps1'
            harness.write_text(script, encoding='utf-8')
            completed = subprocess.run([PWSH, '-NoProfile', '-File', str(harness), '-HelperPath', str(ROOT / 'probes' / 'lifecycle-owned.ps1'), '-ReceiptPath', str(Path(directory) / 'reply.json')], capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertTrue(result['refused'])
        self.assertEqual(result['receipt'], {'sequence': 1, 'complete': True})



@unittest.skipUnless(PWSH, 'PowerShell 7 is required for the portable worker seam')
class WorkerOwnedAdapterTests(unittest.TestCase):
    def test_actual_worker_ownership_adapter_without_native_software(self):
        # Load only the actual function ASTs; process/application boundaries
        # are synthetic objects in this disposable PowerShell process.
        script = r"""
param([string]$WorkerPath,[string]$HelperPath,[string]$StateDirectory)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. $HelperPath
Add-Type -TypeDefinition @'
using System;
using System.Collections;
namespace ChemDraw { public interface IChemDrawApplication { void Quit(); } }
public static class FakeLifecycleState {
    public static bool Present=false;
    public static int QuitCalls=0;
}
public sealed class FakeLifecycleApplication : ChemDraw.IChemDrawApplication {
    public ArrayList Documents=new ArrayList();
    public long MainWindow=100;
    public object ActiveDocument { get { return Documents.Count == 0 ? null : Documents[0]; } }
    public void Quit() { FakeLifecycleState.QuitCalls++; FakeLifecycleState.Present=false; }
}
public static class NativeChemDraw {
    public static int ApplicationProcess(object application) { return 42; }
    public static bool SameIdentity(object a, object b) { return Object.ReferenceEquals(a,b); }
}
'@
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile($WorkerPath,[ref]$tokens,[ref]$errors)
if($errors.Count -gt 0){throw 'Worker syntax errors'}
$names=@('Observe-OwnedProcess','Assert-Binding','Start-Owned','Close-OwnedContext','Current-Readiness')
foreach($name in $names){
    $fn=$ast.Find({param($node)$node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name},$true)
    if($null -eq $fn){throw ('Missing worker function '+$name)}
    . ([scriptblock]::Create($fn.Extent.Text))
}
$run=$StateDirectory;$exe='C:\Synthetic\ChemDraw.exe';$generation='generation';$operationId='operation'
$script:ownedContexts=[Collections.Generic.List[hashtable]]::new()
$script:events=[Collections.Generic.List[object]]::new()
$script:creationContextRecorded=$false;$script:throwAfterCreate=$false;$script:ambiguous=$false
function Record($stage,$detail){$script:events.Add(@{stage=$stage;detail=$detail})}
function Get-Process {
    [CmdletBinding()]param([string]$Name,[int]$Id)
    if(![FakeLifecycleState]::Present){
        if($PSBoundParameters.ContainsKey('Id')){Write-Error 'No synthetic process' -ErrorId NoProcessFoundForGivenId -Category ObjectNotFound}
        return
    }
    [pscustomobject]@{Id=42;StartTime=[DateTime]::Parse('2026-09-19T00:00:00Z').ToUniversalTime();Path=$exe;MainWindowHandle=100}
    if($script:ambiguous -and !$PSBoundParameters.ContainsKey('Id')){
        [pscustomobject]@{Id=43;StartTime=[DateTime]::Parse('2026-09-19T00:00:00Z').ToUniversalTime();Path=$exe;MainWindowHandle=101}
    }
}
function New-Object([string]$ComObject){
    if($ComObject -cne 'ChemDraw_x64.Application'){throw 'Unexpected object creation'}
    $script:creationContextRecorded=$script:ownedContexts.Count -eq 1 -and $script:ownedContexts[0].creation_attempted -and $script:events[-1].stage -eq 'owned_application_creation_intent'
    [FakeLifecycleState]::Present=$true
    if($script:throwAfterCreate){throw 'Synthetic creation failed after a process may exist'}
    return [FakeLifecycleApplication]::new()
}
# Application returned, but document Open never happened.
$context=Start-Owned
$first=Close-OwnedContext $context
$second=Close-OwnedContext $context
$withoutDocument=@{creation_context_recorded=$script:creationContextRecorded;contexts=$script:ownedContexts.Count;
    receipt=$first;quit_calls=[FakeLifecycleState]::QuitCalls;retained_same_receipt=[object]::ReferenceEquals($first,$second)}
# New-Object can throw after creation; do not invent a binding.
$script:ownedContexts=[Collections.Generic.List[hashtable]]::new();$script:throwAfterCreate=$true
[FakeLifecycleState]::QuitCalls=0
$creationFailed=$false
try{[void](Start-Owned)}catch{$creationFailed=$true}
$uncertain=Close-OwnedContext $script:ownedContexts[0]
$afterFailure=@{creation_failed=$creationFailed;creation_context_recorded=$script:creationContextRecorded;receipt=$uncertain;quit_calls=[FakeLifecycleState]::QuitCalls}
# More than one candidate process cannot acquire ownership.
[FakeLifecycleState]::Present=$false;$script:ownedContexts=[Collections.Generic.List[hashtable]]::new()
$script:throwAfterCreate=$false;$script:ambiguous=$true
$bindingFailed=$false
try{[void](Start-Owned)}catch{$bindingFailed=$true}
$ambiguousReceipt=Close-OwnedContext $script:ownedContexts[0]
$ambiguousResult=@{binding_failed=$bindingFailed;receipt=$ambiguousReceipt;quit_calls=[FakeLifecycleState]::QuitCalls}
$poisoned=$false;$stop=$false;$bindingCurrent=$true;$observationsComplete=$false
$starting=Current-Readiness
$observationsComplete=$true;$ready=Current-Readiness
$stop=$true;$ending=Current-Readiness
@{without_document=$withoutDocument;creation_failure=$afterFailure;ambiguous=$ambiguousResult;readiness=@{starting=$starting;ready=$ready;ending=$ending}}|ConvertTo-Json -Depth 30 -Compress
"""
        with tempfile.TemporaryDirectory(prefix='chemdraw-owned-adapter-') as directory:
            root = Path(directory)
            harness = root / 'adapter.ps1'
            harness.write_text(script, encoding='utf-8')
            completed = subprocess.run([PWSH, '-NoProfile', '-File', str(harness), '-WorkerPath', str(ROOT / 'probes' / 'native-edit-loop.ps1'), '-HelperPath', str(ROOT / 'probes' / 'lifecycle-owned.ps1'), '-StateDirectory', str(root)], capture_output=True, text=True, timeout=20)
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            result = json.loads(completed.stdout)
            receipts = [json.loads(path.read_text(encoding='utf-8')) for path in (root / 'lifecycle').glob('*.json')]
        successful = result['without_document']
        self.assertTrue(successful['creation_context_recorded'])
        self.assertEqual(successful['contexts'], 1)
        self.assertEqual(successful['quit_calls'], 1)
        self.assertTrue(successful['retained_same_receipt'])
        self.assertTrue(successful['receipt']['observed_process_exit'])
        self.assertFalse(successful['receipt']['document_close_returned'])
        self.assertEqual(successful['receipt']['session_state'], 'closed')
        failed = result['creation_failure']
        self.assertTrue(failed['creation_failed'])
        self.assertTrue(failed['creation_context_recorded'])
        self.assertEqual(failed['quit_calls'], 0)
        self.assertEqual(failed['receipt']['session_state'], 'unknown')
        self.assertFalse(failed['receipt']['observed_process_exit'])
        ambiguous = result['ambiguous']
        self.assertTrue(ambiguous['binding_failed'])
        self.assertEqual(ambiguous['quit_calls'], 0)
        self.assertEqual(ambiguous['receipt']['session_state'], 'unknown')
        self.assertEqual(len(receipts), 3)
        self.assertEqual(result['readiness']['starting']['state'], 'not_ready')
        self.assertEqual(result['readiness']['ready']['state'], 'ready')
        self.assertEqual(result['readiness']['ending']['state'], 'not_ready')


if __name__ == '__main__':
    unittest.main()
