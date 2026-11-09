import json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent;B=D.parent.parent;R=B.parents[4]
S=B/'sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/checkpoint-r357-atomic-closed-tool-qualified-fixture-revision-open'
T=S/'activate.transaction.339fdab569b0480681078f9df7918ad0'
refs={}
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def add(r):
 r=dict(path=str(Path(r['path'])),sha256=r['sha256'].removeprefix('sha256:'),bytes=r['bytes']);key=r['path'].casefold()
 assert key not in refs or refs[key]==r
 refs[key]=r
def read(p):
 add(pin(p));return json.loads(Path(p).read_bytes())
def walk(v):
 if isinstance(v,dict):
  if all(k in v for k in ('path','sha256','bytes')):add(v)
  for x in v.values():walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
def save(n,v):
 with (D/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
for p in S.rglob('*'):
 if p.is_file():add(pin(p))
a=read(T/'0.before.json');b=read(R/'execution/v2.4/checkpoint.json')
assert pin(T/'0.before.json')['sha256']=='9476bb385b95f5ed992d20b23171270d0c0525f22d2afaf5137f79ee00bc3f52'
assert pin(R/'execution/v2.4/checkpoint.json')['sha256']=='71f15760598f24631740dee94a70461f98ff4b06e05b687e80b677c9fca4708f'
assert (T/'0.after.proposed.json').read_bytes()==(R/'execution/v2.4/checkpoint.json').read_bytes()
assert (T/'1.before.json').read_bytes()==(T/'1.after.proposed.json').read_bytes()==(R/'execution/v2.4/path_ownership.json').read_bytes()
canonical=[pin(R/'execution/v2.4'/(n+'.json')) for n in ('checkpoint','path_ownership','step_state','commands')]
expected=['71f15760598f24631740dee94a70461f98ff4b06e05b687e80b677c9fca4708f','48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452','fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149','b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129']
# Ownership's full expected pin comes from immutable before/proposed evidence.
assert [r['sha256'] for r in canonical]==expected
for r in canonical:add(r)
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
assert changed==sorted(['updated_at','failure_counters','revision','note','expected_previous_revision','work_in_progress'])
assert b['revision']==357 and b['expected_previous_revision']==356
assert a['failure_counters']==b['failure_counters'][:806] and len(b['failure_counters'])==815
tail=b['failure_counters'][806:]
assert [x['original_payload']['observed_ordinal'] for x in tail]==list(range(809,818))
assert len({x['origin_key'] for x in tail})==9
for x in tail:
 assert x['counted_once'] and not x['counter_reset'] and not x['automatic_retry']
 assert x['original_payload']['actual_python_exit'] is None and x['original_payload']['actual_native_exit'] is None
 walk(x)
assert tail[0]['original_payload']['private_input_exported'] is False
assert tail[2]['original_payload']['actual_outer_exit']==0 and 'uncaptured inner rg exitNULL' in tail[2]['original_payload']['diagnostic']
assert 'reconstructed' in tail[6]['original_payload']['diagnostic']
manifest=read(S/'manifest.json');assert len(manifest['members'])==4;walk(manifest)
handoff=read(S/'handoff.json');walk(handoff)
proof=read(S/'canonical_pair.actual.json');walk(proof)
resume=read(S/'RESUME.r357.original.json');walk(resume)
io=read(S/'original-tool-io.root.json')
assert io['post_manifest_separate_io'] and io['result']['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in io['result']['output']
assert not any(Path(r['path']).name=='original-tool-io.root.json' for r in manifest['members'])
commit=read(T/'committed.json');walk(commit)
assert commit['written_indices']==[0,1] and commit['both_verified_while_exclusively_held']
g=read(S/'source_guard.cleanup.actual.json');walk(g)
assert len(g['entries'])==100 and g['closed'] and g['verification']=='PASSED' and not g['failure'] and not g['errors'] and g['retained_handles_count']==0
assert all(e['verified'] and e['final_path_match'] and e['closed'] for e in g['entries'])
wchanged={k:b['work_in_progress'].get(k) for k in set(a['work_in_progress'])|set(b['work_in_progress']) if a['work_in_progress'].get(k)!=b['work_in_progress'].get(k)}
walk(wchanged)
w=b['work_in_progress']
assert w['r357_registered_failure_count']==815 and w['r357_highest_observed_diagnostic_ordinal']==817
assert 'PARTIAL' in w['mu_sdk_w04_two_state'] and 'NOT_FORMAL' in w['mu_sdk_w04_two_state']
assert 'NOT_STARTED' in w['mu_sdk_native_positive_hostile_flow_state']
assert 'NOT_YET_EXECUTED' in w['mu_sdk_official_test2json_state']
assert 'DIGEST_PREFIX_AND_GO127_OUTPUTTYPE' in w['mu_sdk_typed_fixture_state']
assert resume['current_formal_accepted']==0 and resume['historical_accepted_parents']==6
assert not resume['native9_executed'] and not resume['completion_asserted'] and not resume['counter_reset']
assert resume['original_trial_provider_requests'] is None and resume['once_consumed'] and resume['original_clock_expired'] and not resume['financial_closed']
for r in refs.values():assert pin(r['path'])==r,('drift',r['path'])
e=save('evidence.json',dict(base_refs=list(refs.values()),changed_top_keys=changed,changed_work_in_progress=wchanged,old806prefix_equal=True,new_ordinals=list(range(809,818)),registered=815,highest_observed=817,guard_entries=100,canonical_refs=canonical,transaction_pair_exact=True,post_manifest_IO_separately_pinned=True,Root_outer_exit=0,Root_marked_Python_exit=0,new_reviewer_diagnostic=818,new_mechanical_errors=1,formal_acceptance=False))
print(json.dumps(dict(evidence_ref=e,base_refs=len(refs),canonical_revision=357,old_prefix=806,registered=815,high=817,guard=100,drift=0)))

