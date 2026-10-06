from pathlib import Path
import json,hashlib,sys,datetime,subprocess,fnmatch,re
ROOT=Path('D:/作品集/ResearchOS/research-os');OUT=Path(__file__).resolve().parent;RUN=ROOT/'execution/v2.4/receipts/W07/W07-99/source_executor_codex/run-86fe15fb910f42ac84b4b1c197c470d7';CTX=ROOT/'execution/v2.4/receipts/W07/W07-99/source_executor_codex/current-context-73b0ed13c0cd4138bd44315261ecbb01';NATIVE=ROOT/'execution/v2.4/receipts/W07/W07-99/integration_codex/native-runs/20261006T102413Z-388cc5110f';sys.path.insert(0,str(ROOT/'execution/v2.4'))
import formal_case_index as api
import formal_profile_w07 as profile
cache={}
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def verify(v):
 p=Path(v['path']);p=p if p.is_absolute() else ROOT/p
 assert p.is_file(),str(p)
 h=sha(p.read_bytes());assert h==v['sha256'].removeprefix('sha256:'),(str(p),h,v['sha256']);cache[str(p)]=h;return p
refs={}
def refs_walk(v):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str):
   p=verify(v);refs[str(p)]=ref(p) if p.is_relative_to(ROOT) else {'path':str(p),'sha256':cache[str(p)]}
  for x in v.values():refs_walk(x)
 elif isinstance(v,list):
  for x in v:refs_walk(x)
ctx=read(CTX/'context.json');proof=read(RUN/'proof.json');assert ref(CTX/'context.json')['sha256']=='a24d534f6c3d9b2e756dc8f147ad6e62ec5216feb2b4a4927207491fe930eb5a';assert ref(RUN/'proof.json')['sha256']=='67c977988159b6c76f1f31333ce70c38398c70d366af3292d9f4c3b613f08dbb'
refs_walk(proof);refs_walk(ctx);reader=api.Reader(ROOT);pinned,tools=profile._vector(api,reader,ctx);actualproof,reports=profile.product(api,reader,ctx,tools);assert actualproof==proof;profile._dispatches(api,reader,ctx,pinned,proof);reader.finish()
sv=read(verify(proof['source_before_ref']));assert sv==read(verify(proof['source_after_ref']));assert len(sv)==2283
for p,h in sv.items():verify({'path':p,'sha256':h})
formalpaths={r['path'] for r in ctx['version_vector']['source_files']};assert len(formalpaths)==2318
coverage=ctx['source_coverage'];observed=set(coverage['exact_files'])
for r in coverage['roots']:
 for p in (ROOT/r['path']).rglob('*'):
  if p.is_file() and any(fnmatch.fnmatchcase(p.relative_to(ROOT/r['path']).as_posix(),pattern) for pattern in r['patterns']):observed.add(p.relative_to(ROOT).as_posix())
assert observed==formalpaths and len(coverage['roots'])==22
# Independent current local-package census including platform variants/tests and literal embeds.
raw=(RUN/'go-list.stdout').read_text(encoding='utf-8');decoder=json.JSONDecoder();i=0;packages=[];localfiles=set();embeds=set()
while raw[i:].strip():
 i+=len(raw[i:])-len(raw[i:].lstrip());p,i=decoder.raw_decode(raw,i);packages.append(p);directory=Path(p['Dir'])
 if directory.is_relative_to(ROOT) and not directory.is_relative_to(ROOT/'.local'):
  for f in directory.glob('*.go'):localfiles.add(f.relative_to(ROOT).as_posix())
  for f in p.get('EmbedFiles',[]):embeds.add((directory/f).relative_to(ROOT).as_posix())
assert localfiles<=set(sv) and embeds<=set(sv)
# Four native origins remain exact, not regenerated receipt objects.
native=read(NATIVE/'result.json');assert ref(NATIVE/'result.json')['sha256']=='187cd1fc5c237d09102806c25b2160390ec5070075a770a3fdd6c429e23b8702';refs_walk(native);dispatch=[];fixture=None
for o in read(CTX/'native-receipt-origins.json'):
 original=verify(o['original_ref']);copied=verify(o['copied_ref']);assert original.read_bytes()==copied.read_bytes();r=read(original);refs_walk(r);stdout=read(verify(r['stdout']));assert r['exit_code']==r['child_exit_code']==0 and r['status']=='PASS';assert r['invocation_id']==original.parent.name;assert stdout['status']=='PASS';assert len(r['assertion_ids'])==(5 if o['id']=='A05' else 1)
 pr=stdout['product_proof_ref'];p=read(verify(pr));assert p['mode']==('FIXTURE' if o['id']=='W07-G01' else 'LIVE_SERVICE')
 if o['id']=='W07-G01':
  fixture=p;refs_walk(p);assert read(verify(p['source_before_ref']))==read(verify(p['source_after_ref']))==sv
 else:assert p==proof
 dispatch.append({'id':o['id'],'receipt':o['copied_ref'],'original':o['original_ref'],'stdout':r['stdout'],'stderr':r['stderr'],'actual_exit':0,'mode':p['mode'],'assertion_ids':r['assertion_ids']})
# Fresh events and all three package lifecycles are audited separately for fixture and live injection.
event_audits=[]
for label,p in [('LIVE_INJECTED',proof),('G01_FIXTURE',fixture)]:
 invocation=p['h07_invocations'][0];events=[json.loads(l) for l in verify(invocation['stdout_ref']).read_text(encoding='utf-8').splitlines() if l.strip()];assert invocation['exit_code']==0 and '-count=1' in invocation['actualargv'];assert not any(e.get('Action') in ['fail','skip'] for e in events)
 passed=[e['Test'] for e in events if e.get('Action')=='pass' and e.get('Test')];pkgs=[e['Package'] for e in events if e.get('Action')=='pass' and not e.get('Test')];assert len(set(pkgs))==3;assert 'TestW07HealthPublicIngressCannotForgeCapturedSource' in passed
 event_audits.append({'label':label,'raw':invocation['stdout_ref'],'top_level_pass':len([t for t in passed if '/'not in t]),'all_pass_including_subtests':len(passed),'fail':0,'skip':0,'packages':pkgs,'ingress_negative_pass':True})
# GLOBAL4 manual audit before issuing an actual acceptance, no provisional fake review.
assert list(ctx['global_evidence_refs'])==['run_receipt','version_manifest','command_receipt','assertion_results'];glob={k:read(verify(v)) for k,v in ctx['global_evidence_refs'].items()};g=glob['run_receipt'];assert g['verifier_id']=='codex:/root/w05_merge_review' and g['executor_id']==ctx['executor_id']==proof['executor_id']=='codex:/root/sources_parent_impl';assert g['run_id']==ctx['run_id']==proof['run_id'];assert g['environment_mode']=='LIVE_SERVICE';assert all(g[k]==ctx['version_vector']['environment'][k] for k in ['os','arch','timezone']);assert g['started_at']==proof['started_at'] and g['ended_at']==proof['ended_at']
v=glob['version_manifest'];er=read(verify(ctx['execution_report_ref']));assert v['code_revision']==er['execution_head']=='cf7ec1ec70cdeea842d878d131773b64ecb61d85';assert v['dirty']==bool(er['dirty_before']);assert read(verify(v['version_vector_ref']))==ctx['version_vector'];assert v['product_version_vector_ref']==proof['version_vector_ref'];verify(v['package_manifest_ref'])
c=glob['command_receipt'];assert c['registered_commands']==ctx['registered_commands'];assert all(c[k]==proof[k] for k in ['source_invocations','h07_invocations','build_invocation_ref'])
assertion_rows={x['id']:x for x in proof['assertion_rows']};baseline=read(verify(ctx['acceptance_baseline_ref']));frozen=next(x for x in baseline['cases'] if x['id']=='A05');assert len(frozen['assertions'])==5 and frozen['mode']=='LIVE_SERVICE';assert {x['id']:x['expected'] for x in frozen['assertions']}=={k:v['expected'] for k,v in assertion_rows.items()}
refusals=[]
for row in glob['assertion_results']['assertions']:
 assert all(row[k]==assertion_rows[row['id']][k] for k in ['expected','actual','status','raw_evidence_refs']);assert row['status']=='PASS' and row['command_keys']==['test.sources.live']
 for rr in row['refusal_evidence_refs']:
  val=profile.raw(api,reader,rr);refusals.append({'assertion':row['id'],'ref':rr,'value':val})
for inv in read(CTX/'tool-version-invocations.json'):
 assert inv['exit_code']==0;refs_walk(inv);name=next(k for k,t in tools.items() if Path(t['path'])==Path(inv['actualargv'][0]));assert verify(inv['stdout_ref']).read_text(encoding='utf-8').strip()==tools[name]['version'].strip()
# Dependency evidence is still accepted and hash current; no fabricated ACCEPTED W07 owner.
state=read(ROOT/'execution/v2.4/step_state.json');deps=[]
for name in ['W07-01','W07-02','W03-99']:
 row=next(x for x in state['steps'] if x['id']==name);assert row['status']=='ACCEPTED';assert row['executor_id'].casefold()!=row['verifier_id'].casefold()
 for v in row['evidence']:verify({'path':'execution/v2.4/'+v['path'],'sha256':v['sha256']})
 deps.append({'id':name,'status':row['status'],'evidence_count':len(row['evidence'])})
reader.finish();before_end=dict(cache)
for p,h in before_end.items():assert sha(Path(p).read_bytes())==h
result={'schema':'researchos.w07.independent-current-audit.v1','reviewer':'codex:/root/w05_merge_review','context':ref(CTX/'context.json'),'proof':ref(RUN/'proof.json'),'formal_sources':len(formalpaths),'coverage_roots':len(coverage['roots']),'captured_sources':len(sv),'local_package_go_files':len(localfiles),'literal_embeds':len(embeds),'all_before_after_current_hashes_equal':True,'G01_and_live_source_vectors_exact_equal':True,'trusted_current_profile_vector_product_dispatches':'PASS','manual_GLOBAL4':'PASS_BEFORE_REAL_REVIEW_ISSUANCE','GLOBAL_refs':ctx['global_evidence_refs'],'raw_refs_checked':list(refs.values()),'native_dispatches':dispatch,'event_audits':event_audits,'refusal_values':refusals,'dependencies':deps,'tools':tools,'environment':ctx['version_vector']['environment'],'proof_assertion_ids':list(assertion_rows),'gates':[x['id'] for x in proof['gate_rows']],'all_read_inputs_final_rehashed':len(before_end),'canonical_acceptance_written':False,'Root_issuance_written':False}
(OUT/'current_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'audit':ref(OUT/'current_audit.json'),'sources':len(sv),'formal':len(formalpaths),'checks':len(before_end),'events':event_audits},ensure_ascii=True))
