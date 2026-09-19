"""Minimal stdio MCP adapter. No native routes, network, subprocesses or persistent jobs."""
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from companion_status import VERSION, STATUS_SCHEMA, status, validate_status

PROTOCOL='2025-06-18'
TOOL='chemdraw_companion_status'
MAX_LINE=65536


class ProtocolError(Exception):
    def __init__(self,code,message):
        self.code=code;self.message=message


def validate_operation_params(params, fields):
    """Separate standard transport metadata from diagnostic operation fields."""
    if set(params) - fields - {'_meta'}:
        raise ProtocolError(-32602,'Unknown operation parameters')
    if '_meta' in params:
        meta=params['_meta']
        if not isinstance(meta,dict):
            raise ProtocolError(-32602,'Request metadata must be an object')
        if 'progressToken' in meta:
            token=meta['progressToken']
            if type(token) not in (str,int,float) or (type(token) is float and not math.isfinite(token)):
                raise ProtocolError(-32602,'Progress token must be a string or finite number')


class Server:
    def __init__(self,root=ROOT):
        self.root=root;self.initialized=False;self.initializing=False

    def respond(self,request):
        rid=request.get('id') if isinstance(request,dict) else None
        if type(rid) not in (str,int,type(None)):
            rid=None
        try:
            if (not isinstance(request,dict) or request.get('jsonrpc')!='2.0'
                    or not isinstance(request.get('method'),str)):
                raise ProtocolError(-32600,'Invalid JSON-RPC request')
            method=request['method'];params=request.get('params',{})
            if not isinstance(params,dict):
                raise ProtocolError(-32602,'Parameters must be an object')
            if 'id' not in request:
                if method=='notifications/initialized' and self.initializing:
                    self.initialized=True
                return None
            if type(request['id']) not in (str,int,type(None)):
                raise ProtocolError(-32600,'Invalid request id')
            if method=='initialize':
                if self.initializing or not isinstance(params.get('protocolVersion'),str):
                    raise ProtocolError(-32602,'A single initialization with protocolVersion is required')
                self.initializing=True
                result={'protocolVersion':PROTOCOL,'capabilities':{'tools':{'listChanged':False}},
                        'serverInfo':{'name':'chemdraw-companion','version':VERSION},
                        'instructions':'This diagnostic preview cannot start, read, edit, render or close ChemDraw. Native execution remains frozen.'}
            elif method=='ping':
                result={}
            elif not self.initialized:
                raise ProtocolError(-32002,'Initialize this connection first')
            elif method=='tools/list':
                validate_operation_params(params,{'cursor'})
                if 'cursor' in params:
                    raise ProtocolError(-32602,'Invalid cursor: this complete catalog has no continuation page')
                result={'tools':[{'name':TOOL,'title':'ChemDraw Companion status',
                    'description':'Verify this diagnostic package and report its frozen native capability. No ChemDraw interaction.',
                    'inputSchema':{'type':'object','properties':{},'additionalProperties':False},
                    'outputSchema':STATUS_SCHEMA,
                    'annotations':{'readOnlyHint':True,'destructiveHint':False,'idempotentHint':True,'openWorldHint':False}}]}
            elif method=='tools/call':
                validate_operation_params(params,{'name','arguments'})
                arguments=params.get('arguments',{})
                if params.get('name')!=TOOL or not isinstance(arguments,dict) or arguments:
                    raise ProtocolError(-32602,'Unknown tool or invalid arguments; only diagnostic status is available')
                value=validate_status(status(self.root))
                result={'structuredContent':value,'content':[{'type':'text','text':json.dumps(value,separators=(',',':'))}],
                        'isError':not value['ok']}
            else:
                raise ProtocolError(-32601,'Method not supported')
            return {'jsonrpc':'2.0','id':rid,'result':result}
        except ProtocolError as exc:
            return {'jsonrpc':'2.0','id':rid,'error':{'code':exc.code,'message':exc.message}}
        except Exception:
            # Do not publish a malformed structured result or retry any handler.
            return {'jsonrpc':'2.0','id':rid,'error':{'code':-32603,'message':'Diagnostic output validation or package inspection failed'}}


def run(stream_in,stream_out,root=ROOT):
    server=Server(root)
    while True:
        line=stream_in.readline(MAX_LINE+1)
        if not line:
            return
        if len(line)>MAX_LINE:
            while line and not line.endswith(b'\n'):
                line=stream_in.readline(MAX_LINE+1)
            response={'jsonrpc':'2.0','id':None,'error':{'code':-32700,'message':'Message exceeds 64 KiB'}}
        else:
            try:
                request=json.loads(line.decode('utf-8'),parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite number')))
                response=server.respond(request)
            except (ValueError,UnicodeError):
                response={'jsonrpc':'2.0','id':None,'error':{'code':-32700,'message':'Invalid JSON'}}
        if response is not None:
            stream_out.write(json.dumps(response,ensure_ascii=True,separators=(',',':'))+'\n')
            stream_out.flush()


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if sys.argv[1:]==['--self-check']:
        value=status(ROOT)
        print(json.dumps(value,separators=(',',':')))
        raise SystemExit(0 if value['ok'] else 2)
    if sys.argv[1:]:
        raise SystemExit('Only --self-check or stdio mode is supported')
    run(sys.stdin.buffer,sys.stdout)
