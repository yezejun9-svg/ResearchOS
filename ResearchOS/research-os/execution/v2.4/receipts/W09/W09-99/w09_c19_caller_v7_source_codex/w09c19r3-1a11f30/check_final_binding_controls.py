import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
prior=json.loads((N/'pre-v7-review.original.source-controls.json').read_bytes())
assert prior['status']=='PASS' and prior['count']==131
changed={'choice_exact_call_pin','choice_full_semantic_inverse','choice_full_byte_inverse'}
checks=[v for v in prior['checks'] if v['name'] not in changed];retained=len(checks)
def check(name,ok):
 checks.append(dict(name=name,passed=bool(ok)));assert ok,name
choice=json.loads((N/'source.integration.choice.json').read_bytes());oldchoice=json.loads((N/'pre-v7-review.original.source.integration.choice.json').read_bytes())
binding=json.loads((N/'v7-independent-review.binding.json').read_bytes());contract=json.loads((N/'root-calling-contract.json').read_bytes())
for k in choice:
 if k not in ('review_refs','original_input_refs','r3_provenance'):assert choice[k]==oldchoice[k],k
assert {k:v for k,v in choice['r3_provenance'].items() if k!='v7_independent_review_status'}=={k:v for k,v in oldchoice['r3_provenance'].items() if k!='v7_independent_review_status'}
check('review_binding_only_expected_choice_fields_changed',True)
delta=json.loads((N/'choice-complete-inverse.json').read_bytes());original=Path(delta['original_ref']['path']).read_bytes();inverse=json.loads(json.dumps(choice))
for d in delta['semantic_deltas']:
 if d['old_present']:inverse[d['key']]=d['old']
 else:del inverse[d['key']]
check('choice_full_semantic_inverse',inverse==json.loads(original))
check('choice_full_byte_inverse',''.join(line for op in delta['opcodes'] for line in op['old_lines']).encode()==original)
check('choice_final_byte_forward',''.join(line for op in delta['opcodes'] for line in op['new_lines']).encode()==(N/'source.integration.choice.json').read_bytes())
check('choice_exact_call_pin',contract['producer_caller_argv'][7:9]==[pin(N/'source.integration.choice.json')['sha256'],str(pin(N/'source.integration.choice.json')['bytes'])])
for key in ('handoff_ref','manifest_ref'):check('review_binding_exact_'+key,pin(binding[key]['path'])==binding[key])
check('binding_self_pin_in_choice',pin(N/'v7-independent-review.binding.json') in choice['original_input_refs'])
check('review_receipts_in_choice_and_contract',all(v in choice['review_refs'] for v in (binding['handoff_ref'],binding['manifest_ref'])) and contract['v7_independent_review_refs']==[binding['handoff_ref'],binding['manifest_ref']])
h=json.loads(Path(binding['handoff_ref']['path']).read_bytes())
check('review_targets_exact_v7_source',h['candidate_ref']==choice['sources']['ops/ci/w09_evidence_closure.py'])
check('review_accepted_source_only',h['status']==binding['status']==contract['v7_source_review_status']==choice['r3_provenance']['v7_independent_review_status']=='SOURCE_ACCEPTED_PENDING_NEW_PRODUCER_AND_MODE_DECISIONS' and h['formal_acceptance'] is False)
proof=json.loads((N/'caller-complete-inverse.json').read_bytes())
for v in proof['callers']:check('caller_byte_pin_unchanged_after_review_binding_'+Path(v['candidate_ref']['path']).name,pin(v['candidate_ref']['path'])==v['candidate_ref'])
assert not (N/'HDF.json').exists() and not (N/'MF.json').exists()
result=dict(status='PASS',count=len(checks),checks=checks,retained_prebinding_check_count=retained,retained_prebinding_controls_ref=pin(N/'pre-v7-review.original.source-controls.json'),new_or_repeated_affected_check_count=len(checks)-retained,scope='PURE_STATIC_INVERSE_AND_REVIEW_BINDING_ONLY',actual_caller_executed=False,actual_Git_Go_SQL_native_API_model=False,canonical_read_as_current_or_written=False)
with (N/'source-controls.json').open('wb') as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(dict(status='PASS',count=len(checks),retained=retained,affected=len(checks)-retained,controls_ref=pin(N/'source-controls.json'))))
