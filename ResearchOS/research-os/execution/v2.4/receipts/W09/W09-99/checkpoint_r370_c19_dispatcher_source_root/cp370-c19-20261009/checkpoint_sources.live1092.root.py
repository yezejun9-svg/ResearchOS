"""Retain three new original failures and current independent Source progress."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os
R=Path(r'D:\作品集\ResearchOS\research-os'); N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99'; W=R/'execution/v2.4/receipts/W09/W09-99'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
tree=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)
    and x.name in {'pin','save','exact','outputs','capture'}],type_ignores=[]),'Root_original_helpers_only','exec'),globals())

def source_original(raw_ref,binding_ref):
    exact(Path(raw_ref['path']),raw_ref['sha256'],raw_ref['bytes'])
    exact(Path(binding_ref['path']),binding_ref['sha256'],binding_ref['bytes'])
    binding=json.loads(Path(binding_ref['path']).read_bytes())
    lines=Path(raw_ref['path']).read_bytes().splitlines(keepends=True)
    assert len(lines)==3 and binding['original_capture_ref']['sha256']==raw_ref['sha256']
    assert [len(x) for x in lines]==binding.get('source_line_bytes',binding.get('source_line_lengths'))
    assert [hashlib.sha256(x).hexdigest() for x in lines]==binding.get('original_line_sha256',binding.get('source_line_sha256'))
    with Path(binding['source_audit_path']).open('rb') as stream:
        for offset,line in zip(binding['source_line_offsets'],lines):
            assert offset+len(line)<=binding['source_prefix_size_observed']
            stream.seek(offset); assert stream.readline()==line
    first,last=[json.loads(x) for x in lines[1:]]
    assert first['payload']['call_id']==last['payload']['call_id']==binding['original_call_id']
    return raw_ref,binding_ref

prior=json.loads((N/'pending-diagnostics.cp373.live1089.root.json').read_bytes())
rows=list(prior['pending']); assert [x['ordinal'] for x in rows]==list(range(1067,1089))
f89=json.loads((B/'schema21_root_caller_registration_independent_source_review_codex/review-s21root-20261010-02/original1089.full-IO.json').read_bytes())
f90=json.loads((W/'w09_profile_nf3_root_adoption_source_codex/adopt-20261010-01/original-failure-1090.json').read_bytes())
inputs=[(1089,*source_original(f89['actual_origin']['raw_ref'],f89['actual_origin']['binding_ref']),1,1,f89['diagnosis']),
        (1090,*source_original(f90['origin_ref'],f90['source_binding_ref']),None,None,f90['description'])]
def match(call,result):return any(x.get('chunk_id')=='fb1da2' for x in outputs(result['payload'].get('output')))
root_pair=capture(AUDIT,1091,match,root=True); assert root_pair is not None
inputs.append((1091,*root_pair,1,1,'Root preparation rejected genuine adjacent backend peer records with a 1ms metadata-to-delivery interval. Source03 minimal timestamp repair requested; no Main/Canon was written.'))
for ordinal,raw_ref,source_binding,outer,python,description in inputs:
    standard=save('original%d.standard-binding.live1092.root.json'%ordinal,dict(
        schema='researchos.root-original-diagnostic-binding.v1',issued_by='codex:/root',
        original_capture_ref=raw_ref,original_source_binding_ref=source_binding,original_source_binding_selector='$',
        original_ordinal=ordinal,original_bytes_unchanged=True,formal_authority=False))
    rows.append(dict(ordinal=ordinal,origin_ref=raw_ref,origin_selector='$',capture_binding_ref=standard,
        description=description,capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',actual_outer_exit=outer,
        actual_python_exit=python,actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,
        actual_dispatcher_exit=None,actual_model_exit=None))
assert [x['ordinal'] for x in rows]==list(range(1067,1092))
current=json.loads((N/'main23.v4.activation-after.current4.actual.root.json').read_bytes())['current_canonical_refs']
for ref in current:exact(Path(ref['path']),ref['sha256'],ref['bytes'])
pending=save('pending-diagnostics.cp373.live1092.root.json',dict(prior,pending=rows,
    next_original_failure_ordinal=1092,registered_in_current_canon=False,counter_reset=False))
resume=save('RESUME.cp373-source-adoptions.live1092.root.json',dict(
    schema='researchos.root-execution-resume.v1',issued_by='codex:/root',root_thread_id=THREAD,
    created_utc=datetime.now(timezone.utc).isoformat(),canonical_refs=current,
    expected_revisions=dict(checkpoint=373,path_ownership=177,step_state=None,commands=39),pending_ref=pending,
    canonical_next_failure_ordinal=1067,next_original_failure_ordinal=1092,counter_reset=False,
    Main23='QUALIFIED_CURRENT_MAIN23_BUILD',Main23_qualification_ref=pin(N/'main23.programme.qualification.bound.actual.root.json'),
    old21='SOURCE02_COUNTER_LEGACY_FIXES_ACCEPTED_RUNTIME02_ACCEPTED_SOURCE03_TIMESTAMP_FIX_TASK79_ACTIVE_NO_ACTUAL_BUILD',
    old21_independent_source02_hdf_ref=pin(B/'schema21_root_caller_registration_independent_source_review_codex/review-s21root-20261010-02/HDF.json'),
    old21_runtime02_hdf_ref=pin(B/'schema21_runtime_resource_independent_review_codex/runtime-s21root-20261010-02/HDF.json'),
    W09='Q_NF3_ACTUAL_PEERS_CAPTURED_TASK75_SOURCE_READY_68_DELTA_PASSED_TASK78_NONAUTHOR_REVIEW_ACTIVE_CM39_UNCHANGED',
    W09_adopter_Source_hdf_ref=exact(W/'w09_profile_nf3_root_adoption_source_codex/adopt-20261010-01/HDF.json',
        'fae54fd911b86b8e11cb617c4fb35b22907609d69214d941728742635be45f9a',5083),
    public22='READONLY83_COMPONENT_QUALIFIED_ORIGINAL1025_FAILURE_RETAINED',
    goal_status='ACTIVE',formal_cases_current_accepted=0,formal_cases_required=42,parent_tasks_required=22,
    formal_acceptance=False,parent_acceptance=False,prior_resume_ref=pin(N/'RESUME.cp373-source-adoptions.live1089.root.json')))
handoff=R/'execution/v2.4/HANDOFF_RESUME_PACK.md'; old=handoff.read_bytes()
with (N/'historical.HANDOFF.before-live1092.root.md').open('xb') as stream:
    stream.write(old);stream.flush();os.fsync(stream.fileno())
prefix=('# Current Root continuation: CP373 / OW177 / CM39 / live next1092\n\n'
    'Main23 programme qualified. Old21 Source02/runtime02 accepted; Source03 repairs genuine 1ms peer timestamp rejection. '
    'W09 Root adopter Source Task75 ready; non-author Task78 review active. No actual old21/full-W09 execution yet. '
    'Goal ACTIVE; formal0/42; all counters and old work retained.\n\n'
    'Current resume: '+resume['path']+'\nSHA256 '+resume['sha256']+' bytes '+str(resume['bytes'])+'\n\n'
    'Pending diagnostics: '+pending['path']+'\nSHA256 '+pending['sha256']+' bytes '+str(pending['bytes'])+'\n\n').encode()
with handoff.open('wb') as stream:stream.write(prefix+old);stream.flush();os.fsync(stream.fileno())
assert handoff.read_bytes().endswith(old)
print(json.dumps(dict(resume_ref=resume,pending_ref=pending,pending_rows=len(rows),
    next_original_failure_ordinal=1092,handoff_ref=pin(handoff),Canon_unchanged=True),ensure_ascii=False,indent=2))
