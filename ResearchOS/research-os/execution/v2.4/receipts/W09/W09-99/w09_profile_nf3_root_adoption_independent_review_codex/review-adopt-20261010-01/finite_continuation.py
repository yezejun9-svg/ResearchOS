"""Resolve one reviewer route/command assertion; reuse persisted checks."""
import ast,hashlib,json,types
from pathlib import Path
D=Path(__file__).resolve().parent
S=D.parent.parent/'w09_profile_nf3_root_adoption_source_codex/adopt-20261010-01'
def pin(path):
 p=Path(path);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(path):return json.loads(Path(path).read_bytes())
def save(name,value):
 with (D/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 return pin(D/name)
def module(path,name):
 m=types.ModuleType(name);m.__file__=str(path);exec(compile(Path(path).read_bytes(),str(path),'exec'),m.__dict__);return m
def main():
 h=doc(S/'HDF.json');p=doc(h['input_pins_ref']['path']);refs=p['refs']
 previous=[json.loads(x) for x in (D/'checks.progress.jsonl').read_bytes().splitlines()]
 wrong=[x for x in previous if x['passed'] is not True]
 assert len(wrong)==1 and wrong[0]['name']=='exact four declared command changes' and set(wrong[0]['changed_commands'])=={'test.security','test.retrieval'}
 old_guard=doc(D/'independent-Source-guard.closed.json');assert old_guard['closed'] and old_guard['retained_handles_count']==0 and not old_guard['errors']
 gm=module(refs['guard']['path'],'Task78_continuation_guard')
 guard=gm.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024);checks=[]
 held=[refs[x] for x in ('Q_profile','Q_commands','CM39_archive')]+[pin(D/'review.py'),pin(D/'checks.progress.jsonl'),pin(D/'independent-Source-guard.closed.json')]
 held=[dict(r,path=str(Path(r['path']))) for r in held]
 try:
  guard.acquire(held)
  source=Path(refs['Q_profile']['path']).read_bytes();tree=ast.parse(source)
  routes=ast.literal_eval(next(x.value for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ROUTES' for t in x.targets)))
  cm39=doc(refs['CM39_archive']['path']);cm40=doc(refs['Q_commands']['path'])
  new_routes=tuple(r for r in routes if r[2]!='C19');old_routes=tuple(r for r in routes if r[2]=='C19')
  expected_new=(('test.retrieval','W09-G01',''),('test.retrieval','W09-G02',''),('test.retrieval','','A06'),('test.security','','A06'))
  expected_old=(('test.research.fixture','','C19'),('test.retrieval','','C19'))
  checks.append(dict(name='exact four new routes plus two preserved C19 routes',passed=new_routes==expected_new and old_routes==expected_old and len(set(routes))==6,routes=routes,new_routes_count=len(new_routes),preserved_C19_routes_count=len(old_routes)))
  changed=[name for name in cm39['commands'] if cm39['commands'][name]!=cm40['commands'][name]]
  checks.append(dict(name='four routes belong to exactly two changed command keys; other30 preserved',passed=len(cm39['commands'])==len(cm40['commands'])==32 and set(cm39['commands'])==set(cm40['commands']) and set(changed)=={'test.security','test.retrieval'},changed_command_keys=changed,unchanged_command_count=32-len(changed)))
  old=cm39['commands']['test.retrieval']['selectors'];new=cm40['commands']['test.retrieval']['selectors']
  checks.append(dict(name='all old retrieval selectors including C19 preserved',passed=all(all(v in new[k] for v in values) for k,values in old.items()) and 'C19' in new['case_id'] and cm39['commands']['test.research.fixture']==cm40['commands']['test.research.fixture']))
  checks.append(dict(name='prior32 successful independent checks reused; originalfalse unchanged',passed=len(previous)==33 and len(previous)-len(wrong)==32,prior_success_count=len(previous)-len(wrong),reexecuted_prior_checks=False,original_failure_ordinal=1093,original_progress_ref=pin(D/'checks.progress.jsonl')))
  assert all(x['passed'] for x in checks),'CONTINUATION_EXPECTATION_FAILED'
  result=save('finite-Source-checks.resolved.json',dict(schema='researchos.w09-root-adoption-independent-finite-review.v1',status='ACCEPTED_SOURCE_ONLY',actor_id='codex:/root/full_w09_source_review',
   prior_success_count=32,original_failed_check_preserved=True,resolved_original_failure_ordinal=1093,resolution='Reviewer confused four routes with four command keys. Actual contract has four new routes in two changed command keys, with two legacy C19 routes preserved.',
   continuation_passed=len(checks),continuation_failed=0,checks=checks,original_progress_ref=pin(D/'checks.progress.jsonl'),original_script_ref=pin(D/'review.py'),previous_closed_guard_ref=pin(D/'independent-Source-guard.closed.json'),
   source_handoff_ref=pin(S/'HDF.json'),source_manifest_ref=h['manifest_ref'],author68_reexecuted=False,Q_NF3_previous_controls_reexecuted=False,actual_product_calls=0,RootScope_lease_qualification_grant_written=False,live_Canon_held=0,execution_grant=False,formal_acceptance=False))
 finally:
  closed=guard.close();guard_ref=save('continuation-Source-guard.closed.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
 print(json.dumps(dict(status='ACCEPTED_SOURCE_ONLY',result_ref=result,guard_ref=guard_ref,closed0=True,continuation_passed=len(checks),execution_grant=False,formal_acceptance=False),ensure_ascii=False))
if __name__=='__main__':main()
