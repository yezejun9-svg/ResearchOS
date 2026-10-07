from pathlib import Path
import json,hashlib,os,fnmatch,platform,time,sys,subprocess,copy
from datetime import datetime,timezone
ROOT=Path.cwd();OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'execution/v2.4'))
import formal_case_index as api
import formal_profile_w07 as profile
now=lambda:datetime.now(timezone.utc).isoformat()
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):
 p=Path(p);return {'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}
def write(name,value):
 p=OUT/name;p.write_bytes((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode());return ref(p)
run=ROOT/'execution/v2.4/receipts/W07/W07-99/source_executor_codex/run-86fe15fb910f42ac84b4b1c197c470d7'
proof=json.loads((run/'proof.json').read_text(encoding='utf-8'));report=json.loads((run/'report.json').read_text(encoding='utf-8'));before=json.loads((run/'source-before.json').read_text(encoding='utf-8'));assert before==json.loads((run/'source-after.json').read_text(encoding='utf-8'))
for name,d in before.items():assert digest(ROOT/name)==d.removeprefix('sha256:'),name
fieldmap=ROOT/'execution/v2.4/receipts/W07/W07-99/formal_review_codex/full_context_preflight/field_map.json';fm=json.loads(fieldmap.read_text(encoding='utf-8'))
specs=[]
for name,rule in fm['frozen_baselines'].items():
 p=Path(rule['repository_copy']['path']);assert digest(p)==rule['repository_copy']['sha256']==digest(Path(rule['external']['path'])),name;specs.append(ref(p))
acceptance=next(x for x in specs if x['path'].endswith('/contracts/acceptance.json'));manifest=next(x for x in specs if x['path'].endswith('/PACKAGE_MANIFEST.json'))
lockpath=ROOT/'execution/toolchains/locked.json';locked=json.loads(lockpath.read_text(encoding='utf-8'));tools=[];tool_runs=[]
for name in ['go','python','browser_act']:
 t=locked['tools'][name];assert digest(Path(t['path']))==t['sha256'];argv=[t['path']]+t['version_argv'];start=now();p=subprocess.run(argv,capture_output=True,cwd=ROOT);stdout=OUT/(name+'-version.stdout');stderr=OUT/(name+'-version.stderr');stdout.write_bytes(p.stdout);stderr.write_bytes(p.stderr);actual=p.stdout.decode('utf-8').strip();assert p.returncode==0 and actual==t['version_output'],(name,actual)
 tool_runs.append({'actualargv':argv,'cwd':str(ROOT),'exit_code':p.returncode,'started_at':start,'ended_at':now(),'stdout_ref':ref(stdout),'stderr_ref':ref(stderr)})
 tools.append({'name':name,'version':actual,'path':t['path'],'sha256':t['sha256']})
toolref=write('tool-identity.json',{'schema':'researchos.w07.tool-identity.v1','locked_ref':ref(lockpath),'tools':tools});write('tool-version-invocations.json',tool_runs)
text=(run/'go-list.stdout').read_text(encoding='utf-8');decoder=json.JSONDecoder();offset=0;packages=[]
while offset<len(text):
 while offset<len(text) and text[offset].isspace():offset+=1
 if offset>=len(text):break
 p,offset=decoder.raw_decode(text,offset)
 if p.get('ImportPath','').startswith('researchos.local/research-os/'):packages.append(p)
roots=[]
for p in packages:
 rel=Path(p['Dir']).relative_to(ROOT).as_posix();roots.append({'path':rel,'patterns':['*.go','*.json','*.md']})
roots += [{'path':'tests/sources/check','patterns':['*.py','*.json']},{'path':'ops/ci','patterns':['*.py']},{'path':'execution/command_dispatcher','patterns':['*.py']},{'path':'execution/v2.4','patterns':['formal*.py']},{'path':'migrations/sqlite','patterns':['*.sql']},{'path':'spec/v2.0/contracts','patterns':['*']}]
observed=set()
for rule in roots:
 top=ROOT/rule['path']
 for directory,dirs,files in os.walk(top,followlinks=False):
  for name in dirs:
   child=Path(directory)/name;assert not child.is_symlink() and not child.is_junction(),child
  for name in files:
   child=Path(directory)/name
   if any(fnmatch.fnmatchcase(child.relative_to(top).as_posix(),pattern) for pattern in rule['patterns']):observed.add(child.relative_to(ROOT).as_posix())
exact=sorted(set(before)-observed);observed.update(exact)
coverage={'roots':roots,'exact_files':exact,'paths_sha256':api.object_sha256(sorted(observed))}
source=[ref(ROOT/n) for n in sorted(observed)]
inputs=sorted({'execution/commands.json','execution/v2.4/commands.json','execution/project_identity.json'}|{n for n in before if n.startswith(('spec/v2.0/contracts/','migrations/sqlite/'))})
vector={'schema':'researchos.w07.version-vector.v1','package_version':'2.4.0','spec_files':specs,'source_files':source,'input_files':[ref(ROOT/n) for n in inputs],'lock_files':[ref(lockpath),ref(ROOT/'go.mod'),ref(ROOT/'go.sum')],'tool_files':[toolref],'environment':{'os':platform.system(),'arch':platform.machine(),'timezone':time.tzname[0]},'components':{'model':{'status':'not_applicable','reason':'No model-provider execution occurs in the bounded public source capture.'},'adapter':{'status':'applicable','version':'W07 SourceHealth v1 at captured '+report['execution_head'],'refs':[ref(ROOT/n) for n in ['adapters/sources/health.go','adapters/sources/x.go','adapters/sources/github_pr.go','internal/domain/sources_health.go']]},'rubric':{'status':'not_applicable','reason':'Frozen A05 deterministic assertions apply; no model rubric is executed.'},'policy':{'status':'applicable','version':'ResearchOS v2.4 W07 strict formal profile','refs':[ref(ROOT/n) for n in ['execution/v2.4/formal_profile_w07.py','execution/v2.4/formal_case_index.py','execution/commands.json','execution/v2.4/commands.json']]}}}
vectorref=write('formal-version-vector.json',vector)
nativepath=ROOT/sys.argv[1];assert digest(nativepath)==sys.argv[2];native=json.loads(nativepath.read_text(encoding='utf-8'));commands=[];origins=[]
(OUT/'native-receipts').mkdir()
for c in native['registered_commands']:
 original=ROOT/c['receipt_ref']['path'];assert digest(original)==c['receipt_ref']['sha256'];dest=OUT/'native-receipts'/(c['id']+'.receipt.json');dest.write_bytes(original.read_bytes());assert digest(dest)==digest(original);commands.append({'id':c['id'],'receipt_ref':ref(dest)});origins.append({'id':c['id'],'original_ref':c['receipt_ref'],'copied_ref':ref(dest)})
write('native-receipt-origins.json',origins)
identity={'case_id':'A05','run_id':proof['run_id']}
global_run=write('GLOBAL-run-receipt.json',dict(identity,schema='researchos.w07.run-receipt.v1',environment_mode='LIVE_SERVICE',**vector['environment'],started_at=proof['started_at'],ended_at=proof['ended_at'],executor_id=proof['executor_id'],verifier_id='codex:/root/w05_merge_review'))
global_version=write('GLOBAL-version-manifest.json',dict(identity,schema='researchos.w07.version-manifest.v1',package_version='2.4.0',package_manifest_ref=manifest,code_revision=report['execution_head'],dirty=bool(report['dirty_before']),version_vector_ref=vectorref,product_version_vector_ref=proof['version_vector_ref']))
global_command=write('GLOBAL-command-receipt.json',dict(identity,schema='researchos.w07.command-receipt.v1',registered_commands=commands,source_invocations=proof['source_invocations'],h07_invocations=proof['h07_invocations'],build_invocation_ref=proof['build_invocation_ref']))
h07ref=proof['h07_invocations'][0]['assertions_ref'];h07=json.loads((ROOT/h07ref['path']).read_text(encoding='utf-8'));indices={r['id']:i for i,r in enumerate(h07)}
refusals={'A05-01':['index_only','not_configured'],'A05-02':['visible_empty','index_only'],'A05-03':['429','401_or_revoked','timeout','effect_unresolved'],'A05-04':['not_configured','401_or_revoked'],'A05-05':['cycle_partial','effect_confirmed','index_only','pr_closed_unmerged','pr_open','pr_merged','empty_valid_result']}
assertions=[]
for row in proof['assertion_rows']:
 value=copy.deepcopy(row);value['refusal_evidence_refs']=[dict(h07ref,locator={'json_pointer':'/'+str(indices[name])+'/actual'}) for name in refusals[row['id']]];value['command_keys']=['test.sources.live']
 if row['id']=='A05-02':value['refusal_evidence_refs'].append(dict(ref(run/'report-X.json'),locator={'json_pointer':'/claim_check'}))
 assertions.append(value)
global_assertions=write('GLOBAL-assertion-results.json',dict(identity,schema='researchos.w07.assertion-results.v1',assertions=assertions))
context={'schema':'researchos.w07.current-context.v1','task_id':'W07','step_id':'W07-99','executor_id':proof['executor_id'],'run_id':proof['run_id'],'created_at':now(),'acceptance_baseline_ref':acceptance,'version_vector':vector,'source_coverage':coverage,'proof_ref':ref(run/'proof.json'),'compilation_invocation_ref':ref(run/'go-list.invocation.json'),'execution_report_ref':ref(run/'report.json'),'registered_commands':commands,'global_evidence_refs':{'run_receipt':global_run,'version_manifest':global_version,'command_receipt':global_command,'assertion_results':global_assertions}}
contextref=write('context.json',context)
missing=sorted({f.relative_to(ROOT).as_posix() for p in packages for f in Path(p['Dir']).glob('*.go') if f.is_file()}-set(before))
write('capture-coverage-gaps.json',{'source_before_ref':proof['source_before_ref'],'missing_from_capture_required_by_profile':missing,'missing_count':len(missing),'production_platform_variants':[n for n in missing if not n.endswith('_test.go')],'test_files':[n for n in missing if n.endswith('_test.go')]})
reader=api.Reader(ROOT);results=[];pinned=None;toolmap=None
for name,action in [('_vector',lambda:profile._vector(api,reader,context)),('product',lambda:profile.product(api,reader,context,toolmap)),('_dispatches',lambda:profile._dispatches(api,reader,context,pinned,proof))]:
 try:
  answer=action()
  if name=='_vector':pinned,toolmap=answer
  results.append({'stage':name,'status':'PASS'})
 except Exception as exc:results.append({'stage':name,'status':'FAIL','error_type':type(exc).__name__,'code':getattr(exc,'code',None),'detail':str(exc)})
try:
 for row in assertions:
  for r in row['refusal_evidence_refs']:profile.raw(api,reader,r)
 results.append({'stage':'GLOBAL_refusal_locators','status':'PASS'})
except Exception as exc:results.append({'stage':'GLOBAL_refusal_locators','status':'FAIL','detail':str(exc)})
try:reader.finish();results.append({'stage':'Reader.finish','status':'PASS'})
except Exception as exc:results.append({'stage':'Reader.finish','status':'FAIL','detail':str(exc)})
write('preflight.json',{'status':'PRE_REGISTRATION_REJECTED' if any(r['status']=='FAIL' for r in results) else 'PRE_REGISTRATION_NO_ACCEPTANCE','actor':proof['executor_id'],'at':now(),'context_ref':contextref,'stages':results,'source_count':len(source),'coverage_roots':len(roots),'exact_files':len(exact),'read_paths':len(reader.read_hashes),'formal_acceptances':0,'global_review':'NOT_RUN; independent reviewer must supply actual review','remaining_gaps':missing,'baseline_field_map_ref':ref(fieldmap),'native_run_ref':ref(nativepath)})
print(json.dumps({'context_ref':contextref,'output':str(OUT),'stages':results,'missing_count':len(missing),'source_count':len(source),'global_evidence_refs':context['global_evidence_refs']},ensure_ascii=False))
