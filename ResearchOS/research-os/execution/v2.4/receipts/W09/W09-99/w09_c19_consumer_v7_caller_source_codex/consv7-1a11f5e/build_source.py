import ast,copy,difflib,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');W=R/'execution/v2.4/receipts/W09/W09-99';N=Path(__file__).resolve().parent
S=W/'w09_c19_consumer_caller_source_codex/w09cons-1a11f30';P=W/'w09_c19_caller_v7_source_codex/w09c19r3-1a11f30';Q=W/'v7_fragment_independent_review_codex/v7r-01a11f3f'
STATUS='SOURCE_PREPARED_PENDING_NEW_PRODUCER_QUALIFICATION_AND_ROOT_SCOPE'
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def verify(v):
 actual=pin(v['path']);assert actual['sha256']==v['sha256'].removeprefix('sha256:') and actual['bytes']==v['bytes'];return actual
def save(name,value):
 raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
 with (N/name).open('xb') as f:f.write(raw)
 return pin(N/name)
def members(p):
 values=json.loads(p.read_bytes())['members'];return list(values.values()) if isinstance(values,dict) else values
def inverse(name,original,candidate):
 a=original.decode().splitlines(keepends=True);b=candidate.decode().splitlines(keepends=True);ops=[]
 for op,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes():ops.append(dict(op=op,old_lines=a[i:j],new_lines=b[k:l]))
 assert ''.join(x for v in ops for x in v['old_lines']).encode()==original
 assert ''.join(x for v in ops for x in v['new_lines']).encode()==candidate
 return save(name,dict(whole_old_byte_inverse=True,whole_new_byte_forward=True,opcodes=ops))
assert (pin(S/'HDF.json')['sha256'],pin(S/'HDF.json')['bytes'])==('44b384a543bff2250165c5c2e5aa4035fb89f52f47a1d77530b77e650b8cf470',4584)
assert (pin(S/'MF.json')['sha256'],pin(S/'MF.json')['bytes'])==('c56ca7faa42b8377c7d781909b42cea2d6adaae5b2970e563a2599cbabb5de35',4212)
assert (pin(P/'HDF.json')['sha256'],pin(P/'HDF.json')['bytes'])==('1ad85d20080d9ad8c0fb5cd4220a04646f3d1a6d2f04296713dbe1b24520e0f3',7985)
assert (pin(P/'MF.json')['sha256'],pin(P/'MF.json')['bytes'])==('991592e7cccb49947dabc63cbeb0d76c656ae73568d1f7da97c3e3ecc87f04a1',9297)
assert (pin(Q/'HDF.json')['sha256'],pin(Q/'HDF.json')['bytes'])==('dc5eaea8d4b7c8a74db392b9a4782af7075e657d607c42a79ce1e61b8e979ef6',2660)
assert (pin(Q/'MF.json')['sha256'],pin(Q/'MF.json')['bytes'])==('0b30564210352839b4bb435e6086b74828e06b9172d7b802817329e043eb6f0f',3555)
old_choice=json.loads((S/'source.choice.json').read_bytes());producer_choice=json.loads((P/'source.integration.choice.json').read_bytes());review=json.loads((Q/'HDF.json').read_bytes())
assert review['status']=='SOURCE_ACCEPTED_PENDING_NEW_PRODUCER_AND_MODE_DECISIONS'
closure=producer_choice['sources']['ops/ci/w09_evidence_closure.py'];assert review['candidate_ref']==closure
replacements=[('w09c19-1a11f08','w09c19v7-1a11f30'),('w09c19-producer-1a11f08','w09c19v7-producer-1a11f30'),('w09c19-producer-env-1a11f08','w09c19v7-producer-env-1a11f30'),('w09c19-consumers-1a11f30','w09c19v7-consumers-1a11f30'),('w09c19-consumers-env-1a11f30','w09c19v7-consumers-env-1a11f30')]
def replace_paths(v):
 if isinstance(v,str):
  for a,b in replacements:v=v.replace(a,b)
  return v
 if isinstance(v,list):return [replace_paths(x) for x in v]
 if isinstance(v,dict):return {k:replace_paths(x) for k,x in v.items()}
 return v
old_contract=Path(old_choice['contract_ref']['path']);derived=json.loads(old_contract.read_bytes());derived=replace_paths(derived)
derived['source_refs']['ops/ci/w09_evidence_closure.py']=closure
derived['calling_contract_ref']=pin(P/'root-calling-contract.json')
derived['source_derivation']=dict(original_contract_ref=pin(old_contract),r3_handoff_ref=pin(P/'HDF.json'),r3_manifest_ref=pin(P/'MF.json'),v7_review_handoff_ref=pin(Q/'HDF.json'),v7_review_manifest_ref=pin(Q/'MF.json'),old_registry_ref_historical_only=True,actual_execution=False)
derived_ref=save('consumer-contract.v7.json',derived)
inverse('consumer-contract.complete-inverse.json',old_contract.read_bytes(),(N/'consumer-contract.v7.json').read_bytes())
choice=copy.deepcopy(old_choice);choice['contract_ref']=derived_ref;choice['six_source_refs']=copy.deepcopy(producer_choice['sources']);choice['fixed_future_paths']=replace_paths(choice['fixed_future_paths'])
choice['source_revision']=dict(status=STATUS,base_consumer_handoff_ref=pin(S/'HDF.json'),base_consumer_manifest_ref=pin(S/'MF.json'),r3_handoff_ref=pin(P/'HDF.json'),r3_manifest_ref=pin(P/'MF.json'),v7_review_handoff_ref=pin(Q/'HDF.json'),v7_review_manifest_ref=pin(Q/'MF.json'),v7_review_status=review['status'],current_canonical_not_read=True,canonical_at_source_preparation_is_historical=True,new_producer_and_mode_decisions_required=True,actual_ready=False)
refs=[]
for v in old_choice['input_refs']:
 path=Path(v['path'])
 if 'w09_c19_caller_source_revision_codex' in path.parts or path==old_contract or v==old_choice['six_source_refs']['ops/ci/w09_evidence_closure.py']:continue
 refs.append(verify(v))
refs += [derived_ref,verify(closure)]+[pin(z/name) for z in (S,P,Q) for name in ('HDF.json','MF.json')]
refs += [verify(v) for z in (P,Q) for v in members(z/'MF.json')]
choice['input_refs']=list({v['path']:v for v in refs}.values())
choice_ref=save('source.choice.json',choice)
inverse('choice.complete-inverse.json',(S/'source.choice.json').read_bytes(),(N/'source.choice.json').read_bytes())
source=(S/'run_c19_consumers.actual_owned.py').read_bytes();assert hashlib.sha256(source).hexdigest()=='d8b50d3e1818d9c9db2f831079d687d76c336d00f497a01ae0373db36430b827' and len(source)==21734
text=source.decode();changes=[]
def sub(a,b):
 global text
 count=text.count(a);assert count>0,a
 text=text.replace(a,b);changes.append(dict(old=a,new=b,occurrences=count))
for a,b in replacements:sub(a,b)
sub("CHOICE_SHA='6dab14b88b18f5f8117ec179f85ceafce44f06ebfe9f16b024ffc69edb537ebf'","CHOICE_SHA='"+choice_ref['sha256']+"'")
sub('CHOICE_BYTES=20131','CHOICE_BYTES='+str(choice_ref['bytes']))
sub("vector=load(request['canonical_vector_ref']);require(vector['schema']=='researchos.w09-c19-canonical-input-vector.v1' and vector['checkpoint_revision']==365,'CANONICAL_VECTOR_CP365')", "vector=load(request['canonical_vector_ref']);require(isinstance(vector,dict) and set(vector)=={'schema','checkpoint_revision','refs'} and vector['schema']=='researchos.w09-c19-canonical-input-vector.v1' and type(vector['checkpoint_revision']) is int and vector['checkpoint_revision']>0,'CANONICAL_VECTOR_EXPLICIT_REVISION')")
sub("require(json.loads(canonical[0].read_bytes())['revision']==365 and json.loads(canonical[1].read_bytes())['revision']==169,'CP365_OW169')", "checkpoint_revision=json.loads(canonical[0].read_bytes())['revision'];ownership_revision=json.loads(canonical[1].read_bytes())['revision']\n  require(type(checkpoint_revision) is int and checkpoint_revision==vector['checkpoint_revision'] and type(ownership_revision) is int and ownership_revision>0,'EXACT_VECTOR_BOUND_CANONICAL_REVISIONS')")
candidate=text.encode();ast.parse(candidate);back=text
for change in reversed(changes):back=back.replace(change['new'],change['old'])
assert back.encode()==source and ast.dump(ast.parse(back))==ast.dump(ast.parse(source))
with (N/'run_c19_consumers.actual_owned.py').open('xb') as f:f.write(candidate)
caller_ref=pin(N/'run_c19_consumers.actual_owned.py')
inverse('caller.complete-byte-inverse.json',source,candidate)
save('caller.allowed-substitutions.json',dict(original_ref=pin(S/'run_c19_consumers.actual_owned.py'),candidate_ref=caller_ref,substitutions=changes,whole_byte_AST_inverse=True,allowed_function_change='main: only explicit vector schema/revision checks replacing old CP365/OW169 constants',unchanged_other_functions=True))
contract=replace_paths(json.loads((S/'calling-contract.json').read_bytes()))
contract['status']=STATUS;contract['known_blocker_ref']=json.loads((S/'calling-contract.json').read_bytes())['known_blocker_ref'];contract['known_blocker_is_historical_v6_only']=True
contract['source_caller_ref']=caller_ref;contract['source_choice_ref']=choice_ref;contract['Root_argv'][6]=caller_ref['path'];contract['scope_fixed_values']['source_caller_ref']=caller_ref
contract['guard_contract']=contract['guard_contract'].replace('at CP365/OW169','from the exact explicit Root vector also bound by producer pre-run')
contract['canonical_vector_contract']=dict(schema='researchos.w09-c19-canonical-input-vector.v1',exact_fields=['schema','checkpoint_revision','refs'],checkpoint_revision='POSITIVE_INT_EQUAL_PINNED_CHECKPOINT_CONTENT',ownership_revision='POSITIVE_INT_FROM_EXACT_VECTOR_PINNED_PATH_OWNERSHIP',same_ref_as_producer_pre_run_and_Root_scope=True,historical_source_canonical_not_runtime_binding=True,expected_future_revision=None)
contract['v7_source_review_refs']=[pin(Q/'HDF.json'),pin(Q/'MF.json')];contract['r3_producer_source_refs']=[pin(P/'HDF.json'),pin(P/'MF.json')]
contract['new_producer_report_tool_mode_actual_review_and_Root_scope_required']=True;contract['actual_ready']=False
save('calling-contract.json',contract);inverse('calling-contract.complete-inverse.json',(S/'calling-contract.json').read_bytes(),(N/'calling-contract.json').read_bytes())
all_refs=choice['input_refs']+[pin(S/n) for n in ('run_c19_consumers.actual_owned.py','source.choice.json','calling-contract.json')]+[pin(old_contract)]
all_refs=list({v['path']:v for v in all_refs}.values())
for v in all_refs:assert pin(v['path'])==v
save('source-input-pins.original.json',all_refs)
save('construction-result.json',dict(status=STATUS,caller_ref=caller_ref,choice_ref=choice_ref,input_count=len(all_refs),canonical_read_as_current=False,actual_execution=False,new_failures=[]))
print(json.dumps(dict(status=STATUS,caller_ref=caller_ref,choice_ref=choice_ref,input_count=len(all_refs))))
