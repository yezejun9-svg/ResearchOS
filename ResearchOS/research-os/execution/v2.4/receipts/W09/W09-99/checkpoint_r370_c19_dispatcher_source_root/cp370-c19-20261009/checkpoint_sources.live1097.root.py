"""Root preserves all new originals before the next canonical registration."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
W=R/'execution/v2.4/receipts/W09/W09-99'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in
    {'pin','save','exact','outputs','capture'}],type_ignores=[]),'Root_helper_functions_only','exec'),globals())
prior=json.loads((N/'pending-diagnostics.cp373.live1092.root.json').read_bytes())
rows=list(prior['pending']);assert [x['ordinal'] for x in rows]==list(range(1067,1092))
review=W/'w09_profile_nf3_root_adoption_independent_review_codex/review-adopt-20261010-01'

def source_pair(number,raw_sha,raw_size,binding_sha,binding_size):
    raw_ref=exact(review/('original-%d.raw.jsonl'%number),raw_sha,raw_size)
    binding_ref=exact(review/('original-%d.binding.json'%number),binding_sha,binding_size)
    binding=json.loads(Path(binding_ref['path']).read_bytes());raw=Path(raw_ref['path']).read_bytes()
    lines=raw.splitlines(keepends=True);assert len(lines)==3
    bound=binding.get('original_capture_ref',binding.get('raw_ref'));assert bound['sha256']==raw_sha and bound['bytes']==raw_size
    assert [len(x) for x in lines]==binding['source_line_bytes']
    assert [hashlib.sha256(x).hexdigest() for x in lines]==binding.get('original_line_sha256',binding.get('source_line_sha256'))
    with Path(binding['source_audit_path']).open('rb') as f:
        for off,line in zip(binding['source_line_offsets'],lines):
            assert off+len(line)<=binding['source_prefix_size_observed'];f.seek(off);assert f.readline()==line
    first,last=[json.loads(x) for x in lines[1:]]
    assert first['payload']['call_id']==last['payload']['call_id']==binding.get('original_call_id',binding.get('actual_call_id'))
    return raw_ref,binding_ref

items=[
 (1092,*source_pair(1092,'e9ebd7516367a2ac34b3e345d33a52c4912c6636796230c8f3c224071e4116b8',32627,'db2e330db29228cf367ed5be544911c7c9ad8cdd2040c18fecbf0f801809701f',1664),0,None,'$',
  'Source reviewer guessed a nonexistent control filename during one mixed read invocation; actual host exit0, inner Python never launched and other exits NULL.'),
 (1093,*source_pair(1093,'eadcbd12ca4d72e8a217e0979d709abc270327a0a9a429e95445946f3e4fba10',42121,'519a5b360d6a22bce17371b2ca89fabe1cff3810a57251646b729f32e97b37aa',2517),1,1,'$',
  'Independent Source check incorrectly required four changed command keys for four new routes; actual CM40 has two changed keys and four new routes. Prior passed controls and finally closed guard preserved.'),
 (1096,*source_pair(1096,'cacd8c482189bf035287cd4c15c0ffecca7fa1217ef72d24a929e87e9d973b2d',43668,'835a3dece28fab5fc9fa53f90a7cc5769d59975c4317cabfd1ae608bdbe77e4b',2347),1,1,'$',
  'Source review sealer guessed a literal inner Python exit marker absent from genuine author returns. Original retained; independently unobservable author inner exits stay NULL; no controls rerun.')]
for number,chunk,selector,exit_code,description in (
 (1094,'c25a89','$.payload.output[1].text',1,'Root preparer creation expected two literal occurrences but actual template had three; generation stopped with no Main/Canon write.'),
 (1095,'58ad5d','$.payload.output[2].text',2,'Dependent Root preparer launch proceeded after failed generation; Python reported missing script. Corrected continuation waits for actual successful generation.')):
    def match(call,result):return any(x.get('chunk_id')==chunk for x in outputs(result['payload'].get('output')))
    pair=capture(AUDIT,number,match,root=True);assert pair
    actual=json.loads(Path(pair[0]['path']).read_bytes().splitlines()[-1])
    index=1 if number==1094 else 2
    host=json.loads(actual['payload']['output'][index]['text']);assert host['chunk_id']==chunk and host['exit_code']==exit_code
    items.append((number,*pair,exit_code,exit_code,selector,description))
for ordinal,raw_ref,source_binding,outer,python,selector,description in sorted(items):
    standard=save('original%d.standard-binding.live1097.root.json'%ordinal,dict(
        schema='researchos.root-original-diagnostic-binding.v1',issued_by='codex:/root',original_capture_ref=raw_ref,
        original_source_binding_ref=source_binding,original_source_binding_selector='$',original_ordinal=ordinal,
        original_bytes_unchanged=True,formal_authority=False))
    rows.append(dict(ordinal=ordinal,origin_ref=raw_ref,origin_selector=selector,capture_binding_ref=standard,
        description=description,capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',actual_outer_exit=outer,
        actual_python_exit=python,actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,
        actual_dispatcher_exit=None,actual_model_exit=None))
assert [x['ordinal'] for x in rows]==list(range(1067,1097))
assert len({(x['origin_ref']['sha256'],x['origin_selector']) for x in rows})==len(rows)
current=json.loads((N/'main23.v4.activation-after.current4.actual.root.json').read_bytes())['current_canonical_refs']
for ref in current:exact(Path(ref['path']),ref['sha256'],ref['bytes'])
pending=save('pending-diagnostics.cp373.live1097.root.json',dict(prior,pending=rows,next_original_failure_ordinal=1097,
    registered_in_current_canon=False,counter_reset=False,current_canonical_refs=current))
resume=save('RESUME.cp373-source-adoptions.live1097.root.json',dict(
    schema='researchos.root-execution-resume.v1',issued_by='codex:/root',root_thread_id=THREAD,created_utc=datetime.now(timezone.utc).isoformat(),
    canonical_refs=current,expected_revisions=dict(checkpoint=373,path_ownership=177,step_state=None,commands=39),
    pending_ref=pending,canonical_next_failure_ordinal=1067,next_original_failure_ordinal=1097,counter_reset=False,
    Main23='QUALIFIED_CURRENT_MAIN23_BUILD',old21='CALLER03_AND_BUILDER_REAL_ROOT_WITNESSES_PASSED_RUNTIME03_QUALIFIED_REGISTRATION_READY_NO_ACTUAL_OLD21_BUILD',
    old21_witnesses_ref=pin(N/'old21.v3.source-witnesses.sealed.actual.root.json'),
    old21_runtime_qualification_ref=pin(N/'old21.v3.runtime-qualification.issued.actual.root.json'),
    W09='TASK75_SOURCE_READY_TASK78_NONAUTHOR_SOURCE_REVIEW_SEAL_CONTINUATION_PENDING_CM39_UNCHANGED',
    public22='READONLY83_COMPONENT_QUALIFIED_ORIGINAL1025_FAILURE_RETAINED',goal_status='ACTIVE',
    formal_cases_current_accepted=0,formal_cases_required=42,parent_tasks_required=22,formal_acceptance=False,parent_acceptance=False,
    prior_resume_ref=pin(N/'RESUME.cp373-source-adoptions.live1092.root.json')))
handoff=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=handoff.read_bytes()
with (N/'historical.HANDOFF.before-live1097.root.md').open('xb') as f:f.write(old);f.flush();os.fsync(f.fileno())
prefix=('# Current Root continuation: CP373 / OW177 / CM39 / live next1097\n\n'
    'Main23 programme qualified. Old21 Caller03 and builder actual Root witnesses passed; runtime03 qualified; fresh registration ready. '
    'W09 Task78 Source review seal continuation pending. Goal ACTIVE; formal0/42; original counters/NULL exits and all old work preserved.\n\n'
    'Current resume: '+resume['path']+'\nSHA256 '+resume['sha256']+' bytes '+str(resume['bytes'])+'\n\n'
    'Pending diagnostics: '+pending['path']+'\nSHA256 '+pending['sha256']+' bytes '+str(pending['bytes'])+'\n\n').encode()
with handoff.open('wb') as f:f.write(prefix+old);f.flush();os.fsync(f.fileno())
assert handoff.read_bytes().endswith(old)
print(json.dumps(dict(resume_ref=resume,pending_ref=pending,pending_rows=len(rows),next_original_failure_ordinal=1097,
    handoff_ref=pin(handoff),Canon_unchanged=True),ensure_ascii=False,indent=2))
