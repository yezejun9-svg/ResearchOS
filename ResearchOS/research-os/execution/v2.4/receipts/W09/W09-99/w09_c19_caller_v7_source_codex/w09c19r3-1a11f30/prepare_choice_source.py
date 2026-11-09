import copy,difflib,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');W=R/'execution/v2.4/receipts/W09/W09-99';N=Path(__file__).resolve().parent
S=W/'w09_c19_caller_source_revision_codex/w09c19r2-1a11f08';V=W/'w09_evidence_v7_fragment_source_codex/fragv7-1a11f30';Q=W/'w09_c19_caller_r2_independent_review_codex/w09c19r2r-20261009-source-review'
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def verify(v):
 p=pin(v['path']);assert (p['sha256'],p['bytes'])==(v['sha256'].removeprefix('sha256:'),v['bytes']);return p
def save(n,v):
 assert not (N/'HDF.json').exists() and not (N/'MF.json').exists()
 with (N/n).open('wb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/n)
original=(S/'source.integration.choice.json').read_bytes();old=json.loads(original);new=copy.deepcopy(old)
v7=pin(V/'w09_evidence_closure.v7.proposed.py');assert v7['sha256']=='1cc37f4fec48d2e2bae39db3c1f8d1da9fdfe6bd788a44396ea0a8b877be6777' and v7['bytes']==42716
closure='ops/ci/w09_evidence_closure.py';new['sources'][closure]=v7
new['fixed_paths']=json.loads((N/'fixed-future-paths.json').read_bytes())
new['base_driver_refs']=[pin(S/name) for name in ('prepare_w09_c19.actual_owned.py','run_w09_c19.actual_owned.py')]
new['original_input_refs']=[v7 if v==old['sources'][closure] else v for v in old['original_input_refs']]
new['original_input_refs'] += [pin(S/'HDF.json'),pin(S/'MF.json'),pin(S/'source.integration.choice.json'),pin(V/'HDF.json'),pin(V/'MF.json'),pin(V/'source-contract.json')]
assert pin(Q/'HDF.json')['sha256']=='e1e6bad4357aa045b90e86e7e3d07ce3f3d02bcadbe0ac110b721dcb43119ee5'
assert pin(Q/'MF.json')['sha256']=='8759a702db34490765433cfcd62f888dfce8e1647ef4c58321a68b7459428194'
new['review_refs'] += [pin(Q/'HDF.json'),pin(Q/'MF.json')]
binding_path=N/'v7-independent-review.binding.json'
if binding_path.is_file():
 binding=json.loads(binding_path.read_bytes());new['review_refs'] += [verify(binding['handoff_ref']),verify(binding['manifest_ref'])]
 new['original_input_refs'].append(pin(binding_path))
 independent_status=binding['status'];assert independent_status=='SOURCE_ACCEPTED_PENDING_NEW_PRODUCER_AND_MODE_DECISIONS'
 assert json.loads(Path(binding['handoff_ref']['path']).read_bytes())['candidate_ref']==v7
else:
 independent_status='PENDING_NONAUTHOR_V7_REVIEW_NO_ACTUAL_AUTHORITY'
historical=json.loads((V/'HDF.json').read_bytes())['canonical_refs_unchanged']
new['provenance_original']=dict(canonical_refs=historical,checkpoint_ref=historical[0],checkpoint_revision=365,ownership_revision=169,purpose='HISTORICAL_SOURCE_PREPARATION_ONLY_NOT_ACTUAL_BINDING')
new['r3_provenance']=dict(base_source_handoff_ref=pin(S/'HDF.json'),base_source_manifest_ref=pin(S/'MF.json'),v7_source_handoff_ref=pin(V/'HDF.json'),v7_source_manifest_ref=pin(V/'MF.json'),v7_independent_review_status=independent_status,old_v6_closure_ref=old['sources'][closure],r2_historical_canonical_provenance=old['provenance_original'],replaced_only_one_of_six_source_refs=True,no_Main_source_adoption=True,new_native_run_required=True,old_v6_native_packet_not_reused=True,actual_Git_Go_SQL_API_model_consumer=False)
refs=[]
for v in list(new['sources'].values())+new['base_driver_refs']+new['review_refs']+new['original_input_refs']:refs.append(verify(v))
choice=save('source.integration.choice.json',new)
delta=[]
for key in set(old)|set(new):
 if old.get(key)!=new.get(key):delta.append(dict(key=key,old_present=key in old,old=old.get(key),new=new.get(key)))
inverse=copy.deepcopy(new)
for item in delta:
 if item['old_present']:inverse[item['key']]=item['old']
 else:del inverse[item['key']]
assert inverse==old
candidate=Path(choice['path']).read_bytes();a=original.decode().splitlines(keepends=True);b=candidate.decode().splitlines(keepends=True);ops=[]
for op,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes():ops.append(dict(op=op,old_start=i,old_end=j,new_start=k,new_end=l,old_lines=a[i:j],new_lines=b[k:l]))
assert ''.join(x for v in ops for x in v['old_lines']).encode()==original and ''.join(x for v in ops for x in v['new_lines']).encode()==candidate
save('choice-complete-inverse.json',dict(original_ref=pin(S/'source.integration.choice.json'),candidate_ref=choice,semantic_deltas=delta,opcodes=ops,whole_semantic_inverse=True,whole_original_byte_inverse=True,whole_candidate_byte_forward=True))
save('choice-input-pins.original.json',list({v['path']:v for v in refs}.values()))
contract=json.loads((S/'root-calling-contract.json').read_bytes());contract['schema']='researchos.w09-c19-r3-v7-calling-contract.v1';contract['preparation_argv'][6]=str(N/'prepare_w09_c19.actual_owned.py');contract['producer_caller_argv'][6]=str(N/'run_w09_c19.actual_owned.py');contract['producer_caller_argv'][7:9]=[choice['sha256'],str(choice['bytes'])];contract['fixed_paths']=new['fixed_paths'];contract['immutable_old_checkpoint']=new['provenance_original'];contract['v7_closure_ref']=v7;contract['v7_source_review_status']=independent_status
contract.update(status='SOURCE_ONLY_PENDING_NONAUTHOR_CALLER_REVIEW_ROOT_SCOPE_VECTOR_AND_ACTUAL',prepare_parameter_count=6,producer_parameter_count=10,source_adoption_authorized=False,actual_created_vector=False,actual_created_worktree=False,actual_native_executed=False,actual_formal_consumer_executed=False,closure_source_change_requires_new_producer_Source21=True,old_v6_packet_immutable=True,Go_formatting_executed=False,compiler_input_inventory_actual='NOT_RUN_THIS_SOURCE_TASK',runtime_job_guard_compiler_export_code_equal_r2_after_path_inverse=True)
contract['v7_independent_review_refs']=[binding['handoff_ref'],binding['manifest_ref']]
save('root-calling-contract.json',contract)
for v in refs:assert pin(v['path'])==v
print(json.dumps(dict(status='R3_CHOICE_CONTRACT_SOURCE_ONLY',choice_ref=choice,input_count=len({v['path'] for v in refs}),v7_independent_review_status=independent_status)))
