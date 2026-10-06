import copy,contextlib,datetime,hashlib,io,itertools,json,pathlib,subprocess,sys,tempfile
from unittest.mock import patch
R=pathlib.Path('D:/作品集/ResearchOS/research-os'); O=pathlib.Path(__file__).resolve().parent; B=O.parent
sys.path.insert(0,str(R/'qualification/v2.4'))
import parent_gates as g
import dispatch_parent as d
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]; refs={}
def check(id,ok,detail=None):
 checks.append({'id':id,'ok':bool(ok),'detail':detail}); print(json.dumps(checks[-1],ensure_ascii=False)); assert ok,id
def ref(p):
 refs[str(p)]=sha(p);return read(p)
pin=ref(R/'qualification/v2.4/parent_inputs.json'); head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
check('source-freeze',head=='265137d9566c8f56d793ad75c6f16877176924a1',head)
for p in ['parent_gates.py','dispatch_parent.py','windows_sample.py','test_parent_gates.py','qualify.py','PARENT_GATES.md']:
 refs[str(R/'qualification/v2.4'/p)]=sha(R/'qualification/v2.4'/p)
ref(B/'implementation_summary_codex.json')
bad=[p for p,h in pin['files'].items() if sha(R/p)!=h]
check('all-pinned-file-hashes',not bad,{'count':len(pin['files']),'drift':bad})
for p,h in pin['files'].items():refs[str(R/p)]=h
check('locked-tools',all(sha(pathlib.Path(v['path']))==v['sha256'] for v in pin['tools'].values()),list(pin['tools']))
for k in ['frozen_tasks','spec_manifest']:check(k,sha(R/pin[k])==pin[k+'_sha256'])
tasks=ref(R/pin['frozen_tasks']); task=next(x for x in tasks['tasks'] if x['task_id']=='W01')
check('formal-case-ownership-empty',task['owned_acceptance_ids']==[])
check('four-frozen-gates',[(x['check_id'],x['mode']) for x in task['task_gate_checks']]==list(g.MODES.items()))
observed=ref(B/'integration_codex/exact_dispatch_results.json'); receipts={}
for x in observed['actual_registered_selectors']:
 cid=x['check_id']; inv=x['dispatcher']['invocation_id']; p=R/'execution/invocations'/inv
 raw=ref(p/'receipt.json'); std=ref(p/'stdout.txt'); child=ref(pathlib.Path(std['receipt'])); receipts[cid]=child
 check(cid+'-actual-dispatch',raw['status']==std['status']==child['status']=='PASS' and raw['exit_code']==raw['child_exit_code']==child['exit_code']==0 and raw['assertion_ids']==std['assertion_ids']==child['assertion_ids']==[cid] and raw['code_revision']==head and raw['selectors']=={'task_id':'W01','check_id':cid,'case_id':''})
 check(cid+'-mirror-and-stream-hashes',all((p/f).read_bytes()==(B/'registered-dispatch'/inv/f).read_bytes() for f in ['receipt.json','stdout.txt','stderr.txt']) and all(sha(R/raw[k]['path'])==raw[k]['sha256'] for k in ['stdout','stderr']))
 check(cid+'-child-input-hashes',all(sha(pathlib.Path(k))==v for k,v in child['source_inputs_sha256'].items()),len(child['source_inputs_sha256']))
 check(cid+'-checks-scope',g.strict_results(child['checks'],child['required_check_ids']) and child['owned_acceptance_ids']==child['formal_cases_accepted']==[] and child['whole_card_accepted'] is False and child['new_provider_calls']==0,{'checks':len(child['checks']),'mode':child['mode']})
 manifest=ref(pathlib.Path(std['receipt']).parent/'manifest.json')
 check(cid+'-child-manifest',all(sha(pathlib.Path(std['receipt']).parent/k)==v for k,v in manifest.items()))
sample=R/pin['current_sample']; original=ref(sample/'receipt.json'); meta=ref(sample/'fixture-metadata.json'); result=ref(sample/'result.json')
assembly=ref(sample/'assembly-files.json'); installed=ref(sample/'installed-files.json')
check('127-installed-identical',assembly==installed and len(installed)==127)
check('installed-product-source-bindings',all(installed[p]==sha(R/p) for p in installed if p.startswith(('apps/desktop/main/','apps/desktop/preload/','migrations/','contracts/','internal/api/contracts/','spec/v2.0/contracts/'))) and installed['runtime/electron.exe']==pin['tools']['electron']['sha256'])
check('29-observations',len(result['cli_checks'])==12 and len(result['gui_checks'])==17 and all(v is True for v in [*result['cli_checks'].values(),*result['gui_checks'].values()]))
cli=ref(sample/'cli-status.stdout.txt'); native=ref(sample/'native-session.json'); writer=ref(sample/'native-resumed-writer.json'); file=ref(sample/'native-restored-file.json'); desktop=ref(sample/'installed-desktop-report.json')
session=next(x['result'] for x in cli['operations'] if x['method']=='session.get'); host=next(x['result'] for x in cli['operations'] if x['method']=='host.status')
check('independent-native-identity',all(session[k]==native[k]==writer['snapshot'][k]==meta[k] for k in ['project_id','session_id','goal_id']) and cli['continuation']['next_step']['task_id']==meta['task_id'] and writer['host_ok'] is True)
check('physical-original-file',file['ok'] is True and file['result']['text']=='package continued\n' and file['result']['content_hash']=='sha256:'+hashlib.sha256(file['result']['text'].encode()).hexdigest())
check('actual-native-runtime',desktop['electron']=='37.10.3' and desktop['event']=='ready_to_show' and desktop['protocol'] in host['protocol_versions'] and desktop['host_url']==cli['host_url'] and desktop['renderer']['bridge'] is True)
check('business-counts-and-originals',ref(sample/'business-before.json')==ref(sample/'business-after.json'))
check('old-blocked-preserved',original['status']=='BLOCKED' and original['exit_code']==4 and all(read(B/x/'receipt.json')['status']=='BLOCKED' for x in ['20261005T200612Z-6b39ef79143a','20261005T200831Z-f27d7e6ef06b']))
cleanup=ref(R/pin['cleanup_resolution'])
check('cleanup-post-exit-resolution',cleanup['status']=='PASS' and cleanup['process_check']['exit_code']==0 and cleanup['owned_gui_host_processes']==[] and all(not pathlib.Path(p).exists() for p in cleanup['removed_only_owned_temporary_dirs']) and 'after observation' in cleanup['measurement_limit'])
sources=ref(sample/'source-hashes.json'); current={p:sha(R/p) for p in subprocess.check_output(['git','ls-files','apps/cli','apps/control','apps/desktop/main','apps/desktop/preload','apps/web/src','internal','adapters','migrations','contracts','go.mod','go.sum'],cwd=R,text=True).splitlines()}
check('current-source-no-changed-existing',all(current.get(p)==h for p,h in sources.items()) and {p:h for p,h in current.items() if p not in sources}==pin['allowed_additive_sources'],{'sample_count':len(sources),'current_count':len(current),'additions':pin['allowed_additive_sources']})
baseline=pin['integration_baseline']['candidate_revision']; supplemental=cleanup['additional_build_source_hashes']
check('late-measurement-baseline-proof',all(sha(R/p)==h and hashlib.sha256(subprocess.check_output(['git','show',baseline+':'+p],cwd=R)).hexdigest()==h for p,h in supplemental.items()),len(supplemental))
check('w11-independent-pin',sha(pathlib.Path(pin['integration_baseline']['review_provenance']['source_path']))==sha(R/pin['integration_review_files'][0])=='1f807031df751f8e9dea46b5ff89ef22c9ce69baf4c4d7ffe14be5fa249fae7b')
raw=(R/pin['current_counterexamples']/'qualification-counterexamples.stdout.txt').read_text(encoding='utf-8')
events=[json.loads(l) for l in raw.splitlines()]; passed=[e['Test'] for e in events if e.get('Action')=='pass' and 'Test' in e]
streams={}
for e in events:streams[e.get('Test','')]=streams.get(e.get('Test',''),'')+e.get('Output','')
named=[json.loads(l[len('W06_ASSERTION '):]) for s in streams.values() for l in s.splitlines() if l.startswith('W06_ASSERTION ')]
check('independent-seven-go-results',set(g.TESTS)<=set(passed) and all(e['Action'] not in ['fail','skip'] for e in events) and any(e['Action']=='pass' and 'Test' not in e for e in events))
check('31-distinct-named-negatives',len(named)==len({x['assertion_id'] for x in named})==31 and all(x['status']=='PASS' for x in named) and set(pin['required_go_assertions'])<={x['assertion_id'] for x in named})
# Exhaustive exact-selector table. The child executor is synthetic and never runs commands.
table=[]
for taskid,cid,case in itertools.product(['','W01','W02','W06','W99'],['',*g.SELECTORS,'W01-G05','W02-G01'],['','A02','C04']):
 calls=[]; env=dict(zip(['RESEARCHOS_TASK_ID','RESEARCHOS_CHECK_ID','RESEARCHOS_CASE_ID'],[taskid,cid,case]));env['MARKER']='preserve'
 expected=(taskid=='W01' and cid in g.SELECTORS and not case) or (taskid in ['','W01','W02','W06'] and not cid and case in ['','A02'])
 with contextlib.redirect_stdout(io.StringIO()): code=d.main(env,lambda argv,**kw:(calls.append((argv,kw)) or 37))
 assert (code==37 and len(calls)==1 and calls[0][1]['env'] is env) if expected else (code==2 and not calls)
 table.append({'task':taskid,'check':cid,'case':case,'expected_child':expected,'exit':code})
check('105-selector-combinations',len(table)==105,{'accepted':sum(x['expected_child'] for x in table),'denied':sum(not x['expected_child'] for x in table)})
g.save(O/'selector-matrix.json',table)
# Semantic mutations happen in memory after the separately verified file hash layer.
mutants=[]
def exercise(cid,label,mutator=None):
 obj=g.Gate.__new__(g.Gate);obj.selector=cid;obj.pin=copy.deepcopy(pin);obj.main=R;obj.inputs={};obj.checks=[];obj.commands=[];obj.out=O;obj.local=O
 def data(rel):
  v=read(obj.pinned(rel));return mutator(rel,v) if mutator else v
 obj.data=data
 try:
  with patch.object(g,'save',lambda *a:None):getattr(obj,'g'+cid[-2:])()
  ok=bool(obj.checks) and all(x['ok'] is True for x in obj.checks)
  detail=[x['id'] for x in obj.checks if not x['ok']]
 except Exception as e:ok=False;detail=[type(e).__name__,str(e)]
 mutants.append({'id':label,'gate':cid,'accepted':ok,'failures':detail})
 return ok
for cid in g.SELECTORS:check(cid+'-independent-semantic-baseline',exercise(cid,'baseline-'+cid))
def alter(suffix,fn):
 def mutate(rel,v):
  if rel.endswith(suffix):fn(v)
  return v
 return mutate
cases=[('W01-G01','inventory-order','inventory.json',lambda v:v.update(created_at='2099-01-01T00:00:00+00:00')),
('W01-G01','unchecked-as-absent','inventory.json',lambda v:v['tools']['promptfoo'].update(status='NOT_FOUND')),
('W01-G01','unauthorized-root','inventory.json',lambda v:v['authorization'].update(authorized_roots=['X:/private'])),
('W01-G02','missing-gui','/result.json',lambda v:v['gui_checks'].pop('native_bridge_present')),
('W01-G02','string-true','/result.json',lambda v:v['cli_checks'].update(session_id_exact='true')),
('W01-G02','wrong-native-session','/native-session.json',lambda v:v.update(session_id='other')),
('W01-G02','provider-promotion','/result.json',lambda v:v.update(mode='LIVE')),
('W01-G02','changed-source','/product-sources-before.json',lambda v:v.update({'go.mod':'0'*64})),
('W01-G03','missing-startup','/receipt.json',lambda v:v.update(checks=[x for x in v['checks'] if x['id']!='installed_desktop_started_actual_native'])),
('W01-G03','installation-byte-drift','/installed-files.json',lambda v:v.update({'bin/control.exe':'0'*64})),
('W01-G03','cleanup-unresolved','/resolution.json',lambda v:v.update(status='BLOCKED')),
('W01-G03','cleanup-wrong-run','/resolution.json',lambda v:v.update(original_run_id='other')),
('W01-G04','route-reselection','execution/v2.4/route.json',lambda v:v.update(selected_route='GAP_ONLY_COMPOSE')),
('W01-G04','inherited-product-pass','execution/v2.4/route.json',lambda v:v.update(product_acceptance='PASS')),
('W01-G04','expanded-custom-gap','reuse_decisions.json',lambda v:v['per_capability']['writer_epoch_lease_dedupe_watermark'].update(scope_bound='all product')),
('W01-G04','carry-forward-removed','carry_forward_obligations.json',lambda v:v['carry_forward'].pop('W13-01'))]
for cid,label,suffix,fn in cases:check('reject-'+label,not exercise(cid,label,alter(suffix,fn)))
with tempfile.TemporaryDirectory(dir=O) as temp:
 p=pathlib.Path(temp)/'raw.json';p.write_text('{}'); h=sha(p);obj=g.Gate.__new__(g.Gate);obj.inputs={};obj.input('raw.json',h,pathlib.Path(temp));p.write_text('{"PASS":true}')
 try:obj.input('raw.json',h,pathlib.Path(temp));caught=False
 except ValueError:caught=True
 check('reject-raw-byte-tamper',caught)
for label,mutated in [('no-tests',''),('skip',raw.replace('"Action":"pass"','"Action":"skip"')),('truncated',raw+'\n{'),('named-failure',raw.replace('PASS','FAIL'))]:
 check('go-parser-reject-'+label,not g.parse_go(mutated,g.TESTS)['ok'])
check('inputs-stable-at-review-end',all(sha(pathlib.Path(p))==v for p,v in refs.items()))
g.save(O/'mutation-results.json',mutants)
g.save(O/'verification.json',{'source_revision':head,'checks':checks,'reference_hashes':refs,'actual_command':[sys.executable,*sys.argv],'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model':'gpt-6-astra','reasoning_effort':'high','new_gui_provider_service_calls':0})
print(json.dumps({'status':'PASS','checks':len(checks),'semantic_mutations':len(cases),'selector_combinations':len(table)}))
