import json,hashlib,subprocess,sys,datetime as dt
from pathlib import Path
E=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W17/W17-03/native25_actual_root_codex/20261014-current-chat/positive-replay-01'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def ref(p):
 raw=Path(p).read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,value):
 with (E/name).open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
old=read(P/'controller.public.config.json');new=read(P/'controller.public.config.v2.json')
assert old.keys()==new.keys()
assert {k:v for k,v in old.items() if k!='FrozenInputs'}=={k:v for k,v in new.items() if k!='FrozenInputs'}
before={v['path']:v for v in old['FrozenInputs']};after={v['path']:v for v in new['FrozenInputs']}
assert all(after[k]==v for k,v in before.items())
added=[v for k,v in after.items() if k not in before]
assert len(added)==1 and Path(added[0]['path'])==Path('C:/Windows/System32/kernel.appcore.dll')
assert added[0]['sha256']=='sha256:ed6d62f2555d260547cc94a5cdfe2a6fcb684f18b8e182f78f9e4de224321fc9' and added[0]['bytes']==121360
assert ref(added[0]['path'])['sha256']==added[0]['sha256'][7:]
assert ref(P/'controller.public.config.v2.json')['sha256']=='f21d508263674ca57672fddf2db897e78ffd06b355a6512acc47738b46f2c7fc'
probes=[]
for label,extra in [('fresh',[]),('after-real-metadata-child',['--reviewer-imports'])]:
 argv=[sys.executable,'-B','-X','utf8',str(E/'context_probe_v2.py'),*extra]
 run=subprocess.run(argv,capture_output=True,timeout=30)
 (E/(label+'-v2.stdout.raw.json')).write_bytes(run.stdout);(E/(label+'-v2.stderr.raw.txt')).write_bytes(run.stderr)
 result=json.loads(run.stdout)
 probes.append({'name':label,'argv':argv,'actual_native_exit':run.returncode,'result':result,'stdout_ref':ref(E/(label+'-v2.stdout.raw.json')),'stderr_ref':ref(E/(label+'-v2.stderr.raw.txt'))})
 assert run.returncode==0 and result['context_result']=='PASS' and result['missing_runtime_paths']==[]
 assert not result['serve_called'] and not result['signing_called']
write('v2-context-probes.json',probes)
base=read(E/'revision02/readiness-report.json')
assert base['state']=='READY_FOR_ROOT_ISOLATED_POSITIVE_HARNESS_TO_FIRST_PUBLIC_PAYLOAD_ONLY'
# Earlier source review remains immutable even though this separately manifested subtree was added.
prior=E.parent/'manifest.json'
assert ref(prior)['sha256']=='271fc919e921df7c9f36b4b93776f68e146c4d45e835411141fd50625fb781c1'
for member in read(prior)['members']:
 actual=ref(member['path']);assert actual['sha256']==member['sha256'] and actual['bytes']==member['bytes']
report={
 'schema':'researchos.native25-independent-execution-readiness-final/1','state':base['state'],
 'reviewer':'codex:/root/native25_controller_review','at':dt.datetime.now(dt.timezone.utc).isoformat(),
 'config_ref':ref(P/'controller.public.config.v2.json'),'detail_report_ref':ref(E/'revision02/readiness-report.json'),
 'compiler_and_config_checks':base['validated_counts'],'context_probes_ref':ref(E/'v2-context-probes.json'),
 'program_metadata_ref':ref(E/'program-metadata-check.json'),
 'prior_source_report_ref':ref(E.parent/'FINAL-report.json'),'prior_source_manifest_ref':ref(prior),
 'fixed_finding':{'id':'NATIVE25-READINESS-RUNTIME-001','priority':'P2','state':'CLOSED_BY_V2_CONFIG_PIN',
  'trigger':'In the v1 config a Python process that had actually launched git --version loaded kernel.appcore.dll, causing controller.context to reject its runtime module set.',
  'evidence_refs':[ref(E/'review.stderr.raw.txt'),ref(E/'after-metadata-context.stdout.raw.json')],
  'fresh_v1_context':'PASS','import_subprocess_without_child_v1_context':'PASS','after_real_child_v1_context':'FAIL',
  'root_cause':'Additional native system DLL loaded after child process creation, not merely importing subprocess.',
  'resolution':'Root preserved v1 and appended only the exact public kernel.appcore.dll pin to v2 FrozenInputs; controller unchanged.',
  'added_public_ref':added[0],
  'lineage_ref':ref(P/'configuration.v2.prepared.json'),
  'verification':'Fresh v2 context and context after a real read-only git child both PASS with zero missing runtime resources; full v2 public inputs independently rehashed.'},
 'open_findings':[],
 'decision':'Exact v2 config is ready for Root to start one isolated positive-replay harness and stop at its first concrete public release payload for Root review. Execute serially when Root is ready; this report does not launch it.',
 'signing_or_publication_authorized':False,
 'next_gate':'Inspect actual held Job, concrete fixture/path/native identity, public payload bytes and evidence before any separate Root signing/publication decision. Final retained fixture inspection and Native outcome review remain required.',
 'validation_limits':['Actual go list raw output was independently parsed; 3771 selected inputs, 38 embed occurrences, 19 GoMod files, 648 product files and eight compiler tools were checked against current bytes and held-guard receipts.','Go version -m inspected the six binary metadata records without executing those binaries: old producer a7ec7eb, four target programs and test binary f809555, all vcs.modified=false.','Original build Job closure is reviewed recorded evidence; reviewer did not retroactively observe or rebuild the original compilation.','No private key, DPAPI data, original product DB, Native Root/Control process, GUI, model or external provider used. Python read-only context probes and metadata tooling are the only new child invocations.'],
 'diagnostics_retained':{'v1_readiness_attempt_exit':1,'v1_context_after_child_exit':1,'v2_readiness_attempt_exit':0,'v2_fresh_context_exit':0,'v2_after_child_context_exit':0,'reset_existing_failure_counters':False},
 'native_harness_runs':0,'signatures_created':0,'formal_increment':0,'formal_accepted_cases':'0/42','parent_tasks_open':22,
 'writes':'Only this new execution-readiness evidence subtree; earlier 33-member source manifest and all its members reverified unchanged.'}
write('FINAL-report.json',report)
members=[ref(p) for p in sorted(E.rglob('*')) if p.is_file() and p!=E/'manifest.json']
write('manifest.json',{'schema':'researchos.native25-readiness-independent-evidence-manifest/1','state':report['state'],'reviewer':report['reviewer'],'config_ref':report['config_ref'],'report_ref':ref(E/'FINAL-report.json'),'members':members,'formal_increment':0})
print(json.dumps({'report_ref':ref(E/'FINAL-report.json'),'manifest_ref':ref(E/'manifest.json'),'members':len(members),'state':report['state']},ensure_ascii=True))
