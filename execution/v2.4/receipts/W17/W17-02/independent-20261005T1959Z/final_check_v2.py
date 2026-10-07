import datetime, hashlib, json, pathlib, sys

ROOT = pathlib.Path('D:/作品集/ResearchOS/research-os')
OUT = pathlib.Path(__file__).resolve().parent
BASE = OUT.parent
RUN = BASE / '20261005T194516Z-0a2dbc8f72'
INVOCATION = 'f65c7d80-a8ba-4271-a2ce-950d6a946395'
sys.path.insert(0, str(ROOT / 'tests/security'))
import c22_fixture as c22
import w1702

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):
    with p.open('x',encoding='utf-8') as f: json.dump(v,f,ensure_ascii=False,indent=2)
def rel(p): return p.relative_to(ROOT).as_posix()

checks=[]
def check(id,valid,details):
    checks.append({'assertion_id':id,'status':'PASS' if valid else 'FAIL','details':details})
    if not valid: raise AssertionError(id)

report=read(RUN/'report.json')
manifest=read(RUN/'source-manifest.json')
index=read(RUN/'evidence-index.json')
registry=read(ROOT/'execution/v2.4/commands.json')
binding=read(BASE/'test_binding_codex.json')
inv=ROOT/'execution/invocations'/INVOCATION
dispatch=read(inv/'receipt.json')
check('MAIN-REPORT-HASH',sha(RUN/'report.json')=='cba26905c0cfd6bc800e120ab3122ee93294c5104937f2bae04d67cc3d894ec6',sha(RUN/'report.json'))
drift=[p for p,h in manifest['files'].items() if c22.digest(ROOT/p)!=h]
check('MAIN-CURRENT-SOURCE',not drift,{'count':len(manifest['files']),'drift':drift,'source_commit':manifest['source_commit']})
drift=[p for p,h in index['files'].items() if c22.digest(RUN/p)!=h]
check('MAIN-EVIDENCE-INTEGRITY',not drift,{'count':len(index['files']),'drift':drift})
events=lambda f:[json.loads(x) for x in (RUN/f).read_text(encoding='utf-8').splitlines()]
baseline=c22.validate_evidence(RUN,events('c22.stdout.jsonl'),read(ROOT/'tests/security/c22_expected.json'))
increment=w1702.validate_increment(events('increment.stdout.jsonl'))
allrows=baseline['assertions']+increment
ids=[r['assertion_id'] for r in allrows]
check('MAIN-RAW-154-UNIQUE',len(ids)==len(set(ids))==154 and report['assertions']==allrows,{'total':len(ids),'baseline':len(baseline['assertions']),'increment':len(increment),'http_count':baseline['http_count'],'scan':baseline['scan']})
check('MAIN-COMMAND-EXITS',report['status']=='PASS' and len(report['commands'])==2 and all(c['exit_code']==0 for c in report['commands']),report['commands'])
entry=registry['commands']['test.evaluation.security']
check('EXACT-REGISTRY-BINDING',registry['revision']==32 and binding['command']==entry and entry['selectors']=={'task_id':['W17'],'check_id':['W17-02'],'case_id':[]} and entry['argv']==['-B','-X','utf8','tests/security/w1702.py'] and binding['handler_sha256']==sha(ROOT/'tests/security/w1702.py'),{'revision':registry['revision'],'sha256':sha(ROOT/'execution/v2.4/commands.json'),'selectors':entry['selectors']})
check('DISPATCH-EXIT-AND-SOURCE',dispatch['status']=='PASS' and dispatch['exit_code']==0 and dispatch['child_exit_code']==0 and dispatch['code_revision']==report['source_commit']=='e5a20a1d6042046c75e54786c0a7273e459cc58d' and dispatch['registered_command_revision']==sha(ROOT/'execution/v2.4/commands.json') and dispatch['selectors']=={'task_id':'W17','check_id':'W17-02','case_id':''} and dispatch['assertion_ids']==ids,{'status':dispatch['status'],'exit_code':dispatch['exit_code'],'child_exit_code':dispatch['child_exit_code'],'source_commit':dispatch['code_revision']})
check('DISPATCH-RAW-MIRROR',all((inv/f).read_bytes()==(BASE/'dispatched'/INVOCATION/f).read_bytes() for f in ('receipt.json','stdout.txt','stderr.txt')),INVOCATION)
for kind in ('stdout','stderr'):
    check('DISPATCH-'+kind.upper()+'-HASH',sha(ROOT/dispatch[kind]['path'])==dispatch[kind]['sha256'],dispatch[kind])
parsed=read(inv/'stdout.txt')
check('DISPATCH-HANDLER-REPORT-LINK',pathlib.Path(parsed['receipt']).resolve()==(RUN/'report.json').resolve() and parsed['assertions']==154 and parsed['assertion_ids']==ids,parsed['receipt'])
check('RESOURCE-SCOPE-HONEST',report['mode']=='FIXTURE' and not report['formal_holdout_accessed'] and not report['LIVE_qualified'] and not report['BOUNDED_AUTO_granted'] and report['resource_status']['C22']['formal_resource']=='NOT_OBSERVED',report['resource_status'])
save(OUT/'main-checks.json',{'checks':checks,'count':len(checks),'unique':len({c['assertion_id'] for c in checks})==len(checks),'status':'PASS','validation_mode':'READ_ONLY_CURRENT_SOURCE_AND_RAW_EVIDENCE'})
spec=ROOT/'.local/worktrees/v24-continuation/spec/v2.4'
specfiles=['tasks/steps/W17-02.md','08_AGENT_EXECUTION_GOAL.md','05_WBS.md','contracts/tasks.json','06_ACCEPTANCE_TESTS.md','11_EVALUATION_AND_INTEGRATION.md']
rawfiles=[p for p in OUT.iterdir() if p.is_file()]
review={
  'schema':'researchos-v24-independent-construction-review/1',
  'step_id':'W17-02','reviewer_id':'codex:/root/w1702_review','producer_id':'codex:/root/w1702_impl',
  'actual_host':'Codex','model':'gpt-6-astra','reasoning_effort':'high',
  'model_provenance':'Root confirmed actual spawn_agent parameters gpt-6-astra/high with fork_turns none; selected for security-sensitive independent acceptance per AGENTS.md.',
  'decision':'PASS','construction_acceptance_recommendation':'ACCEPT',
  'scope':'Bounded W17-02 IMPLEMENTATION_SLICE in DEVELOPMENT/FIXTURE, under path ownership revision 40 and exact command registry revision 32. No parent W17/-99, formal complete C22/A11/C07, LIVE qualification or automatic authority accepted.',
  'executor_commit':'1971e48be4e2989383d74060faf15bcd0f95cb73',
  'integrated_commit':'28f2344cafb75662cc3343ace9162fe2f59927e2',
  'tested_source_commit':report['source_commit'],
  'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'summary':'No blocking defect found in this card. Existing production authorization covers the tested API/list/search/events/content/context/cache/file/backup surfaces; 17 independent incremental assertions confirm current role/grant/credential/version/provider revalidation and registration fail-closed behavior. Producer and main 154 unique assertions were independently revalidated from raw evidence. Exact registered main dispatcher succeeded with unchanged integrated implementation bytes. Formal independent Verifier data access remains unobserved and outside this local development slice.',
  'blocking_findings':[],
  'card_checks':[
    {'check_id':'W17-02-OUTPUT','status':'PASS','mode':'FIXTURE','evidence':'Restricted grant alone does not permit EXECUTOR/PLANNER. Known ID/content and list denials plus current pre/post-provider authority checks pass. Authorized OWNER/VERIFIER positive controls pass. Real AppContainer file denials are distinct from host-issued credential HTTP. This accepts the card local-development increment; formal holdout labels/independent service availability were not observed.'},
    {'check_id':'W17-02-NEGATIVE','status':'PASS','mode':'FIXTURE','evidence':'Private marker and protected identifiers absent from tested candidate responses, SQLite caches/events, generated server logs and controlled provider-error responses. Real backup engine rejects protected artifacts without publishing destination; search/context use current service authorization. Guessed unavailable routes do not count as exports and all possible exception stacks are not claimed scanned.'},
    {'check_id':'W17-02-EVIDENCE','status':'PASS','mode':'FIXTURE','evidence':'390 current source hashes and 35 evidence hashes match on both candidate and main runs. Main dispatcher/child and both Go commands exit 0; 154 unique nonzero product assertions match exact raw inventories. Independent reviewer executed 17 increments and 6 separate validator mutation tests. Root integration source, exact registered selector and receipt mirror verified.'}
  ],
  'assertion_accounting':{'producer_and_main_product_assertions_each':154,'baseline_c22_assertions_each':137,'incremental_assertions_each':17,'reviewer_new_product_assertions':17,'reviewer_validator_mutation_tests':6,'main_evidence_checks':len(checks),'note':'Do not add repeated product assertions or synthetic handler mutation tests into a fabricated unique product total.'},
  'tested_registry':read(OUT/'integration-pre-dispatch.json'),
  'commands':read(OUT/'checks.json')['commands']+report['commands'],
  'dispatcher':{'invocation_id':INVOCATION,'path':rel(inv/'receipt.json'),'sha256':sha(inv/'receipt.json'),'status':dispatch['status'],'exit_code':dispatch['exit_code'],'child_exit_code':dispatch['child_exit_code']},
  'producer_report':{'path':'.local/worktrees/codex-w1702/execution/v2.4/receipts/W17/W17-02/20261005T193538Z-b41b6c472b/report.json','sha256':sha(ROOT/'.local/worktrees/codex-w1702/execution/v2.4/receipts/W17/W17-02/20261005T193538Z-b41b6c472b/report.json')},
  'main_report':{'path':rel(RUN/'report.json'),'sha256':sha(RUN/'report.json')},
  'frozen_input_hashes':{rel(spec/p):sha(spec/p) for p in specfiles},
  'independent_evidence_hashes':{rel(p):sha(p) for p in rawfiles},
  'source_review':read(OUT/'source-review.json')['source_review'],
  'resource_status':report['resource_status'],
  'observations_and_limits':report['limitations']+[
    'Independent review agent identity is separate from the producer but shares this OS user. This review is construction separation, never proof of formal holdout isolation.',
    'FrozenProvider.Read is deliberately closed to host body export; existing protected summary/import/qualification source remains intact and was not probed against the formal service.',
    'No old W13 workspace audit, NVDA, external provider or formal label access was performed. All newly written files are the authorized independent review receipt and its new raw evidence directory.',
    'No production authorization logic was changed by W17-02. Current existing behavior plus scoped defensive test/handler increments satisfy the bounded local resource contract.'
  ],
  'formal_cases_accepted':[],'parent_task_accepted':False,'formal_holdout_accessed':False,'LIVE_qualified':False,'BOUNDED_AUTO_granted':False
}
save(BASE/'independent_review_codex.json',review)
print(json.dumps({'decision':'PASS','card_checks':3,'main_evidence_checks':len(checks),'review_path':str(BASE/'independent_review_codex.json'),'sha256':sha(BASE/'independent_review_codex.json')}))
