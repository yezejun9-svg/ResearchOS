"""W06 exact fixture selectors. Live acceptance stays blocked by W05 qualification."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = json.loads((ROOT / 'tests/orchestration/expected.json').read_text(encoding='utf-8'))
GROUPS = {
    'W06-G01': sorted(k for k in EXPECTED if k != 'TestW06ContextContinuation'),
    'W06-G02': ['TestW06ContextContinuation'],
    'C01': ['TestW06ContextContinuation'],
    'A02': ['TestW06RouteEvidence', 'TestW06ConcurrentDispatch', 'TestW06RecoveryFence', 'TestW06DispatchAcceptance', 'TestW06AcceptanceGates'],
    'A03': ['TestW06APIConstraints', 'TestW06ConcurrentDispatch', 'TestW06CrashRollback', 'TestW06AcceptanceGates', 'TestW06AcceptanceRecheck', 'TestW06AcceptanceAtomicRollback', 'TestW06ArtifactReuse', 'TestW06DependenciesInvalidated'],
}

def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('fixture', 'live'), required=True)
    args = parser.parse_args()
    task, check, case = (os.getenv(k, '') for k in ('RESEARCHOS_TASK_ID', 'RESEARCHOS_CHECK_ID', 'RESEARCHOS_CASE_ID'))
    if task != 'W06' or bool(check) == bool(case) or check and check not in ('W06-G01','W06-G02','W06-G03') or case and case not in ('C01','A02','A03'):
        parser.error('exactly one known W06 check or owned case is required')
    selector = check or case
    if args.mode == 'live':
        if selector != 'W06-G03':
            parser.error('live mode is only valid for W06-G03')
        print(json.dumps({'status':'BLOCKED','assertions':0,'assertion_ids':[], 'reason':'RQ-W05-CLI-POLICY-001; W05 live qualification and W12 admission are unavailable','independent_acceptance':'NONE'}))
        return 1
    if selector not in GROUPS:
        parser.error('fixture mode cannot execute live gate')
    if selector == 'A02' and platform.system() != 'Windows':
        print(json.dumps({'status':'BLOCKED','assertion_ids':[],'reason':'A02 requires native Windows route evidence'}))
        return 1
    names = GROUPS[selector]
    expected = [id for name in names for id in EXPECTED[name]]
    if not expected or len(expected) != len(set(expected)):
        raise RuntimeError('empty or duplicate frozen assertion set')
    go = os.getenv('RESEARCHOS_GO') or str(ROOT / '.local/tools/go1.27.1/go/bin/go.exe')
    if not Path(go).is_file():
        parser.error('RESEARCHOS_GO must locate the pinned Go executable')
    out = ROOT / 'execution/receipts/W06' / str(uuid.uuid4())
    out.mkdir(parents=True)
    env = {k:v for k,v in os.environ.items() if not k.startswith('W06_')}
    env['W06_EVIDENCE_DIR'] = str(out)
    cmd = [go, 'test', './internal/domain', '-v', '-count=1', '-timeout=2m', '-run', '^('+'|'.join(names)+')$']
    before = {
        'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'mode':'FIXTURE_AND_NATIVE_WINDOWS' if platform.system()=='Windows' else 'FIXTURE',
        'os':platform.platform(), 'architecture':platform.machine(), 'timezone':list(time.tzname),
        'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'code_tree':subprocess.check_output(['git','write-tree'],cwd=ROOT,text=True).strip(),
        'dirty':subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),
        'argv':cmd, 'cwd':str(ROOT), 'environment_names':sorted(env),
        'versions':{str(p.relative_to(ROOT)):digest(p) for group in ('internal/domain/*.go','migrations/sqlite/*.sql','spec/v2.0/contracts/*.json','go.mod','go.sum','execution/route.json','qualification/core/*.json','tests/orchestration/*','ops/ci/orchestration.py') for p in ROOT.glob(group) if p.is_file()},
        'executor':os.getenv('RESEARCHOS_EXECUTOR_ID', 'local:operator'), 'implementation_model':'gpt-6-astra', 'reasoning_effort':'high',
        'runtime_model':None, 'live_provider':None, 'rubric_mode':'deterministic service; unavailable model rubric remains BLOCKED',
        'resource_request_id':'RQ-W05-CLI-POLICY-001', 'scope':'DEVELOPMENT_ONLY',
        'expected_assertion_ids':sorted(expected), 'selector':selector,
    }
    (out/'before.json').write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf-8')
    timed_out = False
    try:
        run = subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,timeout=130)
        stdout,stderr,code = run.stdout,run.stderr,run.returncode
    except subprocess.TimeoutExpired as e:
        stdout,stderr,code,timed_out = e.stdout or b'',e.stderr or b'',124,True
    (out/'stdout.txt').write_bytes(stdout)
    (out/'stderr.txt').write_bytes(stderr)
    rows=[]
    malformed=False
    for line_number,line in enumerate(stdout.decode('utf-8',errors='replace').splitlines(),1):
        if line.startswith('W06_ASSERTION '):
            try:
                row=json.loads(line[len('W06_ASSERTION '):])
                if not all(key in row for key in ('assertion_id','expected','actual','status','evidence')):
                    malformed=True
                row['raw']={'path':'stdout.txt','line':line_number}
                rows.append(row)
            except ValueError:
                malformed=True
    ids=[row.get('assertion_id') for row in rows]
    passed = code==0 and not malformed and len(ids)==len(expected) and set(ids)==set(expected) and all(row['status']=='PASS' for row in rows)
    report={
        'task':task,'check':check,'case':case,'status':'PASS' if passed else 'FAIL','exit':code,
        'assertion_ids':ids,'expected_assertion_ids':sorted(expected),'assertions':rows,
        'missing':sorted(set(expected)-set(ids)),'unexpected':sorted(str(x) for x in set(ids)-set(expected)),
        'timeout':timed_out,'malformed':malformed,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'hashes':{p.name:digest(p) for p in out.iterdir() if p.is_file()},
        'independent_acceptance':'NOT_REQUESTED','scope':'DEVELOPMENT_ONLY','live_qualification':'BLOCKED',
        'c01_agent':'MEMORYLESS_FIXTURE_AGENT' if 'TestW06ContextContinuation' in names else None,
        'real_model_verified':False,
    }
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':report['status'],'assertions':len(rows),'assertion_ids':ids,'receipt':str(out/'report.json')}))
    return 0 if passed else 1

if __name__ == '__main__':
    raise SystemExit(main())
