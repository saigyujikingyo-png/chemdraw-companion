"""Actual diagnostic stdio and result-contract checks; no native software."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator, FormatChecker

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'packaging/chemdraw-companion'
sys.path.insert(0,str(PACKAGE))
import companion_status as core
spec=importlib.util.spec_from_file_location('diagnostic_server',PACKAGE/'server.py')
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
ERROR_SCHEMA=json.loads((ROOT/'contracts/output/diagnostic-jsonrpc-error.schema.json').read_text())


def request(method,rid=1,params=None):
    return {'jsonrpc':'2.0','id':rid,'method':method,'params':params or {}}


def initialized():
    instance=server.Server(PACKAGE)
    instance.respond(request('initialize',params={'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'portable-test','version':'1'}}))
    instance.respond({'jsonrpc':'2.0','method':'notifications/initialized'})
    return instance


class DiagnosticServerTests(unittest.TestCase):
    def validate(self,result):
        Draft202012Validator(core.STATUS_SCHEMA,format_checker=FormatChecker()).validate(result)

    def test_catalog_is_compact_specific_and_matches_published_schema(self):
        instance=initialized();catalog=instance.respond(request('tools/list'))['result']['tools']
        self.assertEqual(['chemdraw_companion_status'],[tool['name'] for tool in catalog])
        self.assertEqual(json.loads((ROOT/'contracts/output/diagnostic-status.schema.json').read_text()),catalog[0]['outputSchema'])
        self.assertLess(len(json.dumps(catalog)),7000)
        self.assertFalse(catalog[0]['inputSchema']['additionalProperties'])

    def test_actual_tool_output_and_text_agree(self):
        result=initialized().respond(request('tools/call',params={'name':server.TOOL,'arguments':{}}))['result']
        self.validate(result['structuredContent'])
        self.assertEqual(result['structuredContent'],json.loads(result['content'][0]['text']))
        self.assertFalse(result['structuredContent']['native_execution_enabled'])
        self.assertEqual('frozen',result['structuredContent']['native_acceptance'])
        self.assertEqual(['diagnostics'],result['structuredContent']['available_capabilities'])
        self.assertEqual('unverified',result['structuredContent']['package_integrity'])
        self.assertTrue(result['isError'])  # An unbuilt checkout is not an installed package.

    def test_invalid_protocol_and_unknown_native_tool_have_error_contracts(self):
        samples=[([],False),(request('tools/list'),False),(request('missing'),True),
                 (request('tools/call',params={'name':'chemdraw_edit','arguments':{}}),True),
                 (request('tools/call',params={'name':server.TOOL,'arguments':{'source':'never-read'}}),True),
                 ({'jsonrpc':'2.0','id':True,'method':'ping'},True),
                 ({'jsonrpc':'2.0','id':4,'method':'tools/call','params':[]},True)]
        for sample,is_initialized in samples:
            with self.subTest(sample=sample):
                instance=initialized() if is_initialized else server.Server(PACKAGE)
                result=instance.respond(sample)
                Draft202012Validator(ERROR_SCHEMA).validate(result)
                self.assertNotIn('result',result)

    def test_bad_producer_output_is_not_emitted_or_retried(self):
        instance=initialized()
        with patch.object(server,'status',return_value={'native_execution_enabled':True}) as producer:
            result=instance.respond(request('tools/call',params={'name':server.TOOL}))
        self.assertEqual(1,producer.call_count)
        self.assertEqual(-32603,result['error']['code'])
        Draft202012Validator(ERROR_SCHEMA).validate(result)
        self.assertNotIn('structuredContent',result)

    def test_typed_validator_rejects_semantically_wrong_status(self):
        original=core.status(PACKAGE)
        for key,value in [('native_execution_enabled',True),('ok',True),('checked_files',True),
                          ('source_commit','not-a-commit'),('available_capabilities',['editing']),
                          ('lifecycle',{**core.LIFECYCLE,'persistent':0}),('observed_at','2026-09-19')]:
            with self.subTest(key=key):
                wrong=copy.deepcopy(original);wrong[key]=value
                with self.assertRaises((ValueError,TypeError)):core.validate_status(wrong)

    def test_invalid_json_and_oversized_lines_do_not_break_next_request(self):
        source=b'{invalid\n'+b'x'*65537+b'\n'+json.dumps(request('ping',rid=7)).encode()+b'\n'
        output=io.StringIO();server.run(io.BytesIO(source),output,PACKAGE)
        results=[json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(3,len(results))
        for result in results[:2]:Draft202012Validator(ERROR_SCHEMA).validate(result)
        self.assertEqual({},results[2]['result'])

    def test_actual_stdio_frontends_initialize_call_and_exit_on_eof(self):
        messages=[request('initialize',params={'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'portable','version':'1'}}),
                  {'jsonrpc':'2.0','method':'notifications/initialized'},request('tools/list',2),
                  request('tools/call',3,{'name':server.TOOL,'arguments':{}})]
        data=''.join(json.dumps(m)+'\n' for m in messages)
        processes=[subprocess.Popen([sys.executable,'-I','-B',str(PACKAGE/'server.py')],stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(2)]
        try:
            for process in processes:
                out,err=process.communicate(data,timeout=10)
                self.assertEqual(0,process.returncode,err)
                replies=[json.loads(line) for line in out.splitlines()]
                self.assertEqual([1,2,3],[reply['id'] for reply in replies])
                self.validate(replies[-1]['result']['structuredContent'])
        finally:
            for process in processes:
                if process.poll() is None:process.kill();process.wait()


if __name__=='__main__':unittest.main()
