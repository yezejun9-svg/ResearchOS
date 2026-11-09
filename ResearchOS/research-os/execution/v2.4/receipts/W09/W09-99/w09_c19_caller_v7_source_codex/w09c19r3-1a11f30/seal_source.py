import ast,hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
 with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
choice=json.loads((N/'source.integration.choice.json').read_bytes());controls=json.loads((N/'source-controls.json').read_bytes());guard=json.loads((N/'preparation-source-guard.cleanup.json').read_bytes())
assert controls['status']=='PASS' and controls['count']==141 and all(v['passed'] for v in controls['checks'])
assert guard['closed'] and not guard['errors'] and guard['retained_handles_count']==0
refs=[]
for n in ('source-input-pins.original.json','choice-input-pins.original.json'):refs+=json.loads((N/n).read_bytes())
refs=list({v['path']:v for v in refs}.values())
for v in refs:assert pin(v['path'])==v
assert all(not Path(p).exists() for p in choice['fixed_paths'].values())
for p in N.glob('*.py'):ast.parse(p.read_bytes())
origins=[pin(N/'failure-origin.933.original-tool-io.json'),pin(N/'failure-origin.934.original-tool-io.json')]
failures=save('failure-origins.json',dict(schema='researchos.w09-c19-r3-source-failure-disposition.v1',new_original_failures=origins,ordinals=[933,934],automatic_retry=False,counter_reset=False,future_failure_ordinal_reserved=False,old_producer_and_review_failures_preserved=True))
report='''# W09 C19 r3 producer Caller Source

Source preparation complete; non-author r3 Caller review, Root scope registration, explicit fresh canonical vector and actual execution remain pending. The v7 non-author review is pinned in the choice and contract with status SOURCE_ACCEPTED_PENDING_NEW_PRODUCER_AND_MODE_DECISIONS. Its 1505 checks and 130 input pins concern the closure Source only. Author controls do not grant independent Caller acceptance; this package is not an execution grant.

The two r2 caller scripts change only the five specified fixed-root strings. Their entire old byte content and AST are recoverable by exact inverse; all function ASTs, including dynamic canonical vector validation, remain identical. Six Sources retain the five original v6 pins; only ops/ci/w09_evidence_closure.py uses the new v7 pin. Choice metadata records the r2 base, old reviews, v7 author packet and historical CP365/OW169 provenance. Current canonical files are not static runtime pins and were neither read as current nor locked by this preparation, allowing Root checkpoint work to continue. Future prepare and producer must receive the same explicit vector after Root registration.

141 static controls passed: 128 unaffected prebinding results retained with exact provenance, and 13 affected or new binding checks passed after the final review receipts arrived. Preparation still takes six explicit arguments and producer takes ten. Both use locked Python -I -S -B -X utf8. Native test order remains ChainInvalidation then ExplicitOriginAndUnknown. The existing six Git jobs, Go input inventory, single producer job, raw packet export, all guards and cleanup bodies are unchanged. No new automatic consumer, dispatcher, formal increment or Main adoption was added.

Five future paths are absent. No worktree, environment, vector or actual receipt was created. No Git/Go/SQL/Native/API/model/consumer was executed. No Go formatting or actual compiler result is claimed; compiler inventory is generated only by the unchanged future actual caller. The Source read guard closed with zero retained handles and no errors. Old Source packages, raw native packet and reports remain untouched. Two original Source tooling failures are preserved: 933 read-only incorrect relative path (outer 1, Python/native/model NULL), and 934 builder indentation error (outer 1, explicit Source Python 1, native/model NULL). Both are reported to Root; no product failure was retried.
'''
with (N/'REPORT.md').open('xb') as f:f.write(report.encode())
mf=save('MF.json',dict(schema='researchos.w09-c19-r3-v7-caller-source-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ('MF.json','HDF.json')]))
h=save('HDF.json',dict(schema='researchos.w09-c19-r3-v7-caller-source-handoff.v1',status='SOURCE_PREPARED_PENDING_NONAUTHOR_REVIEW_ROOT_SCOPE_VECTOR_AND_ACTUAL',manifest_ref=mf,report_ref=pin(N/'REPORT.md'),prepare_ref=pin(N/'prepare_w09_c19.actual_owned.py'),producer_caller_ref=pin(N/'run_w09_c19.actual_owned.py'),choice_ref=pin(N/'source.integration.choice.json'),calling_contract_ref=pin(N/'root-calling-contract.json'),caller_inverse_ref=pin(N/'caller-complete-inverse.json'),choice_inverse_ref=pin(N/'choice-complete-inverse.json'),source_controls_ref=pin(N/'source-controls.json'),guard_cleanup_ref=pin(N/'preparation-source-guard.cleanup.json'),failure_origins_ref=failures,source_check_count=141,unchanged_input_count=len(refs),v7_closure_ref=choice['sources']['ops/ci/w09_evidence_closure.py'],v7_non_author_review_status=choice['r3_provenance']['v7_independent_review_status'],future_actual_requires_explicit_independent_review_binding=True,exact_other_five_Source_refs_unchanged=True,all_caller_functions_AST_equal_r2=True,whole_caller_byte_AST_inverse=True,fixed_paths=choice['fixed_paths'],all_five_future_paths_absent=True,prepare_parameter_count=6,producer_parameter_count=10,canonical_input_binding=choice['canonical_input_binding'],historical_canonical_provenance=choice['provenance_original'],current_canonical_locked_or_written=False,actual_Git_Go_SQL_Native_API_model_consumer=False,Go_formatting_executed=False,actual_compiler_inventory='NOT_RUN',Main_adopted=False,formal_consumers='NOT_RUN_REGISTRY_UNBOUND',formal_acceptance=False,execution_grant=False,new_original_failures=origins,STOP=True,FINAL=True))
print(json.dumps(dict(handoff_ref=h,manifest_ref=mf,prepare_ref=pin(N/'prepare_w09_c19.actual_owned.py'),producer_ref=pin(N/'run_w09_c19.actual_owned.py'),choice_ref=pin(N/'source.integration.choice.json'),contract_ref=pin(N/'root-calling-contract.json'),checks=141,unchanged_inputs=len(refs))))
