"""W10 exact-selector runner: execution evidence only, never independent acceptance."""
import argparse, datetime, hashlib, json, os, platform, subprocess, sys, time, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=['PF-%02d'%i for i in range(1,13)]+['C21-COUNTS','C21-ZERO']+['C21-TAMPER-'+x for x in ('config','dataset','candidate','baseline','rubric','unknown','raw')]+['C21-STABLE','C21-VALID','C21-REGRESSION','C21-HIGH-SCORE','C21-EXIT','C21-COUNT-TAMPER']
DOMAIN=[a+'-'+s for s in ('positive','negative','null','inconclusive','stable') for a in ('A07-HASH','A07-REGISTER-FIRST','A07-POSTHOC','A07-VERIFIED','A07-NO-RECEIPT','A07-METRIC-FORGE','A07-OUTCOME','A07-RECOMPUTE')]
SANDBOX=['SANDBOX-HOST-CONTROL']+[a for mode in ('baseline','candidate') for a in ['SANDBOX-EXIT-'+mode]+['SANDBOX-'+mode+'-'+k for k in ('read_denied','write_denied','input_write_denied','network_denied','external_denied')]+['SANDBOX-RECOMPUTE-'+mode]]+['SANDBOX-TIMEOUT','SANDBOX-OBSERVED-EGRESS','SANDBOX-STABLE-UNCHANGED']
def digest(p):return 'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main(family='evaluation'):
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=('fixture','live'),required=True);args=p.parse_args()
 task,check,case=(os.getenv(k,'') for k in ('RESEARCHOS_TASK_ID','RESEARCHOS_CHECK_ID','RESEARCHOS_CASE_ID'))
 allowed={'evaluation':{'W10-G03','C21'},'experiments':{'W10-G01','W10-G02','A07'}}[family];selector=check or case
 if task!='W10' or bool(check)==bool(case) or selector not in allowed:p.error('exactly one known W10 check/case selector is required')
 if (args.mode=='live')!=(selector=='W10-G02'):p.error('live mode is only W10-G02; fixture does not establish live qualification')
 if selector=='W10-G02':packages=['./ops/experiment_sandbox'];names=['TestNativeSandbox'];expected=SANDBOX
 elif family=='evaluation':packages=['./adapters/evaluation','./ops/experiment_sandbox'];names=['TestProtocol','TestNativeSandbox'];expected=PROTOCOL+SANDBOX
 else:packages=['./internal/domain'];names=['TestW10Experiment'];expected=DOMAIN
 if len(expected)!=len(set(expected)) or not expected:raise RuntimeError('empty/duplicate expectation')
 go=os.getenv('RESEARCHOS_GO','');
 if not Path(go).is_file():p.error('RESEARCHOS_GO must point at pinned Go')
 out=ROOT/'execution/receipts/W10'/str(uuid.uuid4());out.mkdir(parents=True)
 env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','TEMP','TMP','PATH','USERPROFILE','APPDATA','LOCALAPPDATA','COMSPEC','PATHEXT')};env.update(GOTOOLCHAIN='local',GOENV='off',W10_EVIDENCE_DIR=str(out))
 cmd=[go,'test',*packages,'-v','-count=1','-timeout=3m','-run','^('+'|'.join(names)+')$']
 files=[p for pattern in ('internal/domain/*.go','adapters/evaluation/*.go','ops/experiment_sandbox/*.go','migrations/sqlite/*.sql','go.mod','go.sum','spec/v2.0/contracts/*.json','spec/v2.0/examples/evaluation_smoke_cases.json','qualification/evaluation/package*.json','qualification/evaluation/source*','ops/ci/evaluation.py','ops/ci/experiments.py') for p in ROOT.glob(pattern) if p.is_file()]
 before={'run_receipt':{'case_id':case or None,'check_id':check or None,'task_id':task,'run_id':out.name,'environment_mode':'FIXTURE_AND_NATIVE_WINDOWS','os':platform.platform(),'architecture':platform.machine(),'timezone':time.tzname,'started_at':now(),'executor_identity':'codex:/root/experiments','independent_verifier_identity':None},'version_manifest':{'spec_version':'2.0.0','code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),'files':{str(x.relative_to(ROOT)):digest(x) for x in files},'model':'not_applicable: deterministic development provider; Jev not invoked','adapter':'NATIVE-1','rubric':'paired-mean-v1 / deterministic protocol labels'},'command_receipt':{'command_key':'test.'+family+('.fixture' if family=='evaluation' else ''),'argv':cmd,'cwd':str(ROOT),'environment_names':sorted(env)},'expected_assertion_ids':expected,'scope':'DEVELOPMENT_ONLY','resource_request_id':'RQ-W05-CLI-POLICY-001','revalidate':['W05 live runtime qualification','W06-G03','W12 budget admission integration'],'execution_status':'EXECUTION_REPORTED','acceptance_receipt':{'status':'NOT_REQUESTED','verifier_identity':None,'baseline_hash':None,'evidence_index_hash':None,'blockers':['Independent verifier pending','W05/W06 final live dependency','W17 formal holdout not established']}}
 (out/'before.json').write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf-8')
 try:r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,timeout=195);stdout,stderr,code=r.stdout,r.stderr,r.returncode
 except subprocess.TimeoutExpired as e:stdout,stderr,code=e.stdout or b'',e.stderr or b'',124
 (out/'stdout.txt').write_bytes(stdout);(out/'stderr.txt').write_bytes(stderr)
 rows=[];malformed=False
 for n,line in enumerate(stdout.decode('utf-8',errors='replace').splitlines(),1):
  if line.startswith('W10_ASSERTION '):
   try:
    row=json.loads(line[14:]);row['raw']={'path':'stdout.txt','line':n};rows.append(row)
    if not all(k in row for k in ('assertion_id','expected','actual','status','evidence')):malformed=True
   except ValueError:malformed=True
 ids=[r.get('assertion_id') for r in rows];passed=code==0 and not malformed and len(ids)==len(expected) and set(ids)==set(expected) and all(r['status']=='PASS' for r in rows)
 report={'schema':'GLOBAL_EVIDENCE_V1_CANDIDATE','status':'PASS' if passed else 'FAIL','execution_status':'EXECUTION_REPORTED','scope':'DEVELOPMENT_ONLY','selector':selector,'exit_code':code,'assertion_ids':ids,'assertions':rows,'missing':sorted(set(expected)-set(ids)),'unexpected':sorted(set(ids)-set(expected)),'ended_at':now(),'hashes':{str(x.relative_to(out)):digest(x) for x in out.rglob('*') if x.is_file()},'independent_acceptance':'NONE','formal_jev_qualification':'NOT_RUN','formal_holdout':'BLOCKED_W17','live_runtime_qualification':'BLOCKED_RQ-W05-CLI-POLICY-001'}
 (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'status':report['status'],'assertions':len(rows),'assertion_ids':ids,'receipt':str(out/'report.json')}));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
