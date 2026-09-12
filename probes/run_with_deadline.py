"""Bound a disposable probe worker; never terminate the ChemDraw process."""
import argparse,json,subprocess,time
from datetime import datetime,timezone
from pathlib import Path

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seconds',type=int,default=60);p.add_argument('--receipt',type=Path,required=True);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
    if not 1<=a.seconds<=600:raise ValueError('Finite worker deadline must be 1..600 seconds')
    if a.receipt.exists():raise FileExistsError(a.receipt)
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    record={'started_utc':datetime.now(timezone.utc).isoformat(),'worker_deadline_seconds':a.seconds,'native_call_bound':'Each native call is within the remaining worker deadline; no native process is terminated.','status':'running'}
    a.receipt.write_text(json.dumps(record,indent=2),encoding='utf-8');start=time.monotonic()
    try:
        result=subprocess.run(a.command,timeout=a.seconds,check=False)
        record.update(status='completed' if result.returncode==0 else 'failed',worker_exit_code=result.returncode)
    except subprocess.TimeoutExpired:
        record.update(status='outcome_unknown',worker_exit_code=None,retryable=False,next_action='Inspect existing native process and disk evidence; do not replay writes.')
    record['elapsed_seconds']=time.monotonic()-start
    a.receipt.write_text(json.dumps(record,indent=2),encoding='utf-8')
    raise SystemExit(0 if record['status']=='completed' else 1)
