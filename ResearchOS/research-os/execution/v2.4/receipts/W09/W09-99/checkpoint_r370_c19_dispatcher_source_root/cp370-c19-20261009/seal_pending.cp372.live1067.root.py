"""Preserve the two new failures and every earlier original, without Canon writes."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os
N = Path(__file__).resolve().parent
R = Path(r'D:\作品集\ResearchOS\research-os')
B = R/'execution/v2.4/receipts/W05/W05-99'
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT = Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
tree=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)
    and x.name in {'pin','exact','save','outputs','capture'}],type_ignores=[]),'Root_capture_functions_only','exec'),globals())
p=json.loads((N/'pending-diagnostics.cp372.live1065.root.json').read_bytes())
rows=list(p['pending'])
assert [r['ordinal'] for r in rows] == list(range(1024,1065))
def verify(ref):
    a=pin(Path(ref['path']));assert (a['sha256'],a['bytes'])==(ref['sha256'],ref['bytes']);return ref
def add(ordinal,raw,binding,description,script_ref=None,guard_ref=None):
    verify(raw);verify(binding)
    wrapper=save('original%d.standard-binding.live1067.root.json'%ordinal,dict(
        schema='researchos.root-original-diagnostic-binding.v1',issued_by='codex:/root',
        original_capture_ref=raw,original_source_binding_ref=binding,
        original_source_binding_selector='$',original_ordinal=ordinal,original_bytes_unchanged=True,formal_authority=False))
    row=dict(ordinal=ordinal,origin_ref=raw,origin_selector='$',description=description,
        capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',capture_binding_ref=wrapper,
        actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,actual_Go_exit=None,
        actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)
    if script_ref:row['original_script_ref']=verify(script_ref)
    if guard_ref:row['original_guard_ref']=verify(guard_ref)
    rows.append(row)
f=B/'public22_existing_observation_actual_independent_review_codex/actual-20261010-01'
add(1065,
    exact(f/'actual-review-420c4b.raw.jsonl','fb9b5e584608f04c10165a3177d7521ec1fc6eae36c57c0de11493129582ff7f',25614),
    exact(f/'actual-review-420c4b.binding.json','9c8da23b6888bdf042eb99a83bc29c5938efddefb0ddad7c36c944fa02b01bfd',1424),
    'Independent public22 readonly actual reviewer applied .get to a mixed list. Actual product probes were zero; original validated prefix and finally guard closed0 retained.',
    exact(f/'review_actual.py','58f526cc274b91001e68f3f2cddb9a0315f4f96177aff56f7ecad0fca46a2108',16060),
    exact(f/'independent-Source-guard.closed.json','f7838683e6898b60986a5e0ff669de6448fa90a7d38c91e781a71304628eefdd',382390))
def failed_root(call,result):
    return any(x.get('chunk_id')=='b6f09c' for x in outputs(result['payload'].get('output')))
raw,binding=capture(AUDIT,1066,failed_root,root=True)
add(1066,raw,binding,
    'Root runtime qualification check rejected multiline typed observer JSON followed by an exit marker. Its original wrapper remains unqualified; subsequent one-line actual observation and new time-ordered wrapper validated without changing Source or repeating resource review.',
    pin(N/'main23.v4.seal-runtime-qualification.root.py'))
assert [r['ordinal'] for r in rows] == list(range(1024,1067))
canonical=[verify(r) for r in p['current_canonical_refs']]
cp=json.loads(Path(canonical[0]['path']).read_bytes())
assert cp['revision']==372 and len(cp['failure_counters'])==1021 and cp['work_in_progress']['root_next_failure_ordinal_live']==1024
pending=save('pending-diagnostics.cp372.live1067.root.json',dict(p,pending=rows,
    next_original_failure_ordinal=1067,counter_reset=False,registered_in_current_canon=False))
resume=save('RESUME.cp372-main23-qualified-runtime.live1067.root.json',dict(
    schema='researchos.root-execution-resume.v1',issued_by='codex:/root',root_thread_id=THREAD,
    created_utc=datetime.now(timezone.utc).isoformat(),canonical_refs=canonical,
    expected_revisions=dict(checkpoint=372,path_ownership=176,step_state=None,commands=39),
    registered_failure_records=1021,next_original_failure_ordinal=1067,pending_ref=pending,counter_reset=False,
    formal_cases_current_accepted=0,formal_cases_required=42,parent_tasks_required=22,
    original_public22_result='FAILED_ORIGINAL1025_RETAINED',public22_readonly_actual_status='COMPONENT_EXISTING_ARTIFACTS_INTEGRATION_QUALIFIED',
    component_review_refs=[pin(f/x) for x in ('HDF.json','MF.json','decision.json')],
    Main23='M4_QUALIFIED_RUNTIME_AND_SOURCE_INDEPENDENT_REVIEW_PENDING_FINAL_NO_ACTUAL_BUILD',
    runtime_qualification_ref=exact(N/'main23.v4.runtime-qualification-v2.issued.actual.root.json',
        'be5e4799f995222cf7867ec7d9319357dfac873a2bcf83b512ab219606b37c55',36864),
    W09='V3_SOURCE_NONAUTHOR_ACCEPTED_NO_THREE_GROUP_EXECUTION',
    old21='ORIGINAL_SOURCE_FOUND_SOURCE_BUILDER_TASK66_NO_ACTUAL_BUILD',
    goal_status='ACTIVE',formal_acceptance=False,parent_acceptance=False,
    prior_resume_ref=pin(N/'RESUME.cp372-public22-readonly-actual.live1065.root.json')))
print(json.dumps(dict(pending_ref=pending,resume_ref=resume,pending_rows=len(rows),
    next_original_failure_ordinal=1067,Canonical_unchanged=True),ensure_ascii=False,indent=2))
