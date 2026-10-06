import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
def sha(p):return 'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
summary=json.loads((OUT/'collection-summary.json').read_text(encoding='utf-8'))
run=ROOT/summary['product_proof_ref']['path'];proof=json.loads(run.read_text(encoding='utf-8'));folder=run.parent
before=json.loads((folder/'source-before.json').read_text(encoding='utf-8'));after=json.loads((folder/'source-after.json').read_text(encoding='utf-8'))
assert before==after and len(before)==2283
assert all(sha(ROOT/n)==h for n,h in before.items())
assert not any('.local/worktrees/' in n for n in before)
validated=[]
def walk(x):
 if isinstance(x,dict):
  if 'path' in x and 'sha256' in x:
   p=ROOT/x['path'];assert sha(p).removeprefix('sha256:')==x['sha256'].removeprefix('sha256:');validated.append(ref(p))
  for value in x.values():walk(value)
 elif isinstance(x,list):
  for value in x:walk(value)
walk(proof)
assert all(i['exit_code']==0 for i in proof['source_invocations'])
assert len(proof['source_invocations'])==3
assert len(proof['h07_invocations'][0]['db_snapshots'])==13
events=[json.loads(x) for x in (folder/'fixture.stdout').read_text(encoding='utf-8').splitlines() if x.strip()]
assert not any(x.get('Action') in ('fail','skip') for x in events)
gaps=json.loads((ROOT/'execution/v2.4/receipts/W07/W07-99/source_executor_codex/current-context-2881cfa84dd64156b59d12795e6375a2/capture-coverage-gaps.json').read_text(encoding='utf-8'))['missing_from_capture_required_by_profile']
assert set(gaps)<=before.keys()
result={'status':'PRODUCT_CAPTURE_READY_FOR_REGISTERED_DISPATCH','formal_acceptance':'NOT_ISSUED','proof_ref':ref(run),
 'collection_summary_ref':ref(OUT/'collection-summary.json'),'collector_invocation_ref':ref(OUT/'collector.invocation.json'),
 'source_count':len(before),'source_before_equals_after_and_current':True,'old_27_missing_now_captured':gaps,
 'source_actual_exit_codes':{x['kind']:x['exit_code'] for x in proof['source_invocations']},'typed_H07_closed_snapshots':13,
 'fixture_top_level_pass':sum(x.get('Action')=='pass' and 'Test' in x and '/' not in x['Test'] for x in events),'fixture_fail':0,'fixture_skip':0,
 'validated_proof_file_ref_count':len(validated),'validated_proof_file_refs':validated,'current_verifier_id':'codex:/root/w05_merge_review'}
(OUT/'handoff.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'handoff_ref':ref(OUT/'handoff.json'),'proof_ref':ref(run),'source_count':len(before)},ensure_ascii=False))
