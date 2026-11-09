"""Persist current build progress and the seven later originals; keep Canon intact."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os
N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def exact(p,sha,size):
    ref=pin(p);assert (ref['sha256'],ref['bytes'])==(sha,size);return ref
def save(name,v):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(p)
previous=json.loads((N/'pending-diagnostics.cp373.live1068.root.json').read_bytes())
rows=list(previous['pending']);assert [x['ordinal'] for x in rows]==[1067]
review=B/'fresh_main23_programme_actual_independent_review_codex/actual-main23-20261010-01'
caller=B/'schema21_root_caller_registration_source_codex/s21root-20261010-01'
entries=[
 (1068,review/'failure-8cdcf5.actual-host.raw.jsonl','2cc85f9753a7647a29a6123209d2c628e37b7dae68c628897df2c9fff43d9558',24870,
  review/'failure-8cdcf5.actual-host.binding.json','e3c5992aba2f49d796153ced5b6c30610bd5989af26f2fd7f9d6bd5f65a807e0',1248,1,None,
  'Independent programme reviewer guessed an obsolete directory. Get-Content failed before Python or product execution.'),
 (1069,review/'failure-5cf215.actual-host.raw.jsonl','003d159a9f1e7c075dd269f50664094054052de15d05191afc97fd4b88bc6bdd',24872,
  review/'failure-5cf215.actual-host.binding.json','0cab613ffedfd08bc151d2c806c5774213caa5f8ee9ad31e270a0957cb7a8d1a',1247,1,None,
  'Independent programme reviewer rg included one nonexistent historical helper directory; original read-only diagnostic retained.'),
 (1070,review/'failure-37effd.actual-host.raw.jsonl','46fa34a5173365cebef56f0f6b486c415978ec2764602e41677219b0599c97ba',32781,
  review/'failure-37effd.actual-host.binding.json','13e86fd9cecb8582fe7ea5f40504a38fa76eebd02e96eb087c12a5bbf4add4b1',1249,0,None,
  'A mixed read command guessed caller basename. Outer0 came from later successful reads; rg OS error2 retained, rg actual exit unknown NULL.'),
 (1071,caller/'original1071.actual-host.raw.jsonl','911649502cc91055c7d896130dcd402712457ba251d2b0a252813f9649215ad2',25069,
  caller/'original1071.actual-host.binding.json','25051d6ef60048fadec52a8148633d33d1ca55d5773515bfd141bcf270574b4d',1351,1,1,
  'Old21 caller Source basis used undefined from missing JS store. Actual Python stopped before candidate writes; original closure not serialized.'),
 (1072,caller/'original1072.actual-host.raw.jsonl','7f39029362e464fa62663457f42a49c9ad46415a687f37c3fa37adf154b63c34',25535,
  caller/'original1072.actual-host.binding.json','12b9a18eb15558b1a9759b4e6a508503f426298dcdee104015201ff4ff944dd5',1351,1,1,
  'Old21 caller Source basis compared forward-slash and backslash ref dictionaries directly despite identical physical paths/SHA/bytes; original closure not serialized.'),
 (1073,review/'review-d788d4.actual-host.raw.jsonl','9646b87116d55b18a7084c82335f4fbf13f02c87295bda34ff0d3f87f759b102',26959,
  review/'review-d788d4.actual-host.binding.json','d00d242151f8c685f8d8fbe230d27830f5f7298c3ec16a5b1e1c1aa20cb9075b',1244,1,1,
  'Independent programme reviewer literal linker path did not decode Go JSON quoting. Actual 19984-ref guarded prefix and 23095 checks preserved; canonical quoted-argv finite continuation passed without rebuilding.')]
for ordinal,raw_path,sha,size,binding_path,bsha,bsize,outer,python,description in entries:
    raw=exact(raw_path,sha,size);binding=exact(binding_path,bsha,bsize)
    standard=save('original%d.standard-binding.live1074.root.json'%ordinal,dict(
        schema='researchos.root-original-diagnostic-binding.v1',issued_by='codex:/root',
        original_capture_ref=raw,original_source_binding_ref=binding,original_source_binding_selector='$',
        original_ordinal=ordinal,original_bytes_unchanged=True,formal_authority=False))
    rows.append(dict(ordinal=ordinal,origin_ref=raw,origin_selector='$',capture_binding_ref=standard,
        description=description,capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',actual_outer_exit=outer,
        actual_python_exit=python,actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,
        actual_dispatcher_exit=None,actual_model_exit=None))
assert [x['ordinal'] for x in rows]==list(range(1067,1074))
observed=exact(N/'main23.v4.activation-after.current4.actual.root.json','f7cb3bd5a29eefb9eafb0e253caa705d5f0de173cf7b080c1df7e3496aecba23',3716)
current=json.loads(Path(observed['path']).read_bytes())['current_canonical_refs']
for ref in current:exact(Path(ref['path']),ref['sha256'],ref['bytes'])
cp=json.loads(Path(current[0]['path']).read_bytes())
assert cp['revision']==373 and len(cp['failure_counters'])==1064 and cp['work_in_progress']['root_next_failure_ordinal_live']==1067
pending=save('pending-diagnostics.cp373.live1074.root.json',dict(previous,pending=rows,
    next_original_failure_ordinal=1074,counter_reset=False,registered_in_current_canon=False,current_canonical_refs=current))
resume=save('RESUME.cp373-main23-built-pending-review.live1074.root.json',dict(
    schema='researchos.root-execution-resume.v1',issued_by='codex:/root',root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',
    created_utc=datetime.now(timezone.utc).isoformat(),canonical_refs=current,
    expected_revisions=dict(checkpoint=373,path_ownership=177,step_state=None,commands=39),
    registered_failure_records=1064,canonical_next_failure_ordinal=1067,next_original_failure_ordinal=1076,
    sealed_pending_next_failure_ordinal=1074,awaiting_Source_original_capture_ordinals=[1074,1075],
    pending_ref=pending,counter_reset=False,formal_cases_current_accepted=0,formal_cases_required=42,parent_tasks_required=22,
    Main23='ACTUAL_FIVE_GO_RUNS_EXIT0_BUILT_CANDIDATE_PENDING_INDEPENDENT_FINAL_AND_ROOT_QUALIFICATION_BINDING',
    actual_bundle_ref=exact(N/'main23.v4.actual.complete-hostpair-seal-v2.root.json','fb1762e099f5d8b3a195811614a95ab571321f32b680d22b30da32533f10b300',16249),
    actual_return_file_observation_ref=pin(N/'main23.v4.actual-return-file-observation.root.json'),
    original_API_stdout_truncation_retained=True,original_process_stdout_not_reconstructed=True,
    public22='READONLY83_COMPONENT_INDEPENDENTLY_QUALIFIED_ORIGINAL1025_FAILURE_RETAINED',
    old21='BUILDER_SOURCE83CONTROLS_COMPLETE_TASK68_NONAUTHOR_REVIEW_TASK69_ROOTCALLER_SOURCE_ACTIVE_NO_ACTUAL_BUILD',
    old21_source_refs=[pin(B/'schema21_programme_builder_source_codex/main21b-20261010-01'/x) for x in ('HDF.json','MF.json')],
    W09='V3_SOURCE_AND_V5_COMPAT_SOURCE_ACCEPTED_ACTUAL_THREE_NATIVE_GROUPS_NOT_RUN_CM39_STILL_CURRENT',
    goal_status='ACTIVE',formal_acceptance=False,parent_acceptance=False,
    prior_resume_ref=pin(N/'RESUME.cp372-main23-qualified-runtime.live1067.root.json')))
handoff=R/'execution/v2.4/HANDOFF_RESUME_PACK.md'
old=handoff.read_bytes();archive=N/'historical.HANDOFF.before-cp373-live1074.root.md'
with archive.open('xb') as f:f.write(old);f.flush();os.fsync(f.fileno())
prefix=('# Current Root continuation: CP373 / OW177 / CM39\n\n'
    'Goal remains ACTIVE; 0 of 42 formal cases accepted. Main23 actual build completed with 5 Go exits0; '
    'candidate awaits independent final delivery and Root qualification binding. All original failures retained; '
    'canonical next1067, live next1076; pending1067..1073 sealed, Source captures1074..1075 await sealing. '
    'Original API stdout truncation is preserved, complete durable state independently read back.\n\n'
    'Current resume: '+resume['path']+'\nSHA256 '+resume['sha256']+' bytes '+str(resume['bytes'])+'\n\n'
    'Pending diagnostics: '+pending['path']+'\nSHA256 '+pending['sha256']+' bytes '+str(pending['bytes'])+'\n\n').encode('utf-8')
with handoff.open('wb') as f:f.write(prefix+old);f.flush();os.fsync(f.fileno())
assert handoff.read_bytes().endswith(old)
print(json.dumps(dict(pending_ref=pending,resume_ref=resume,handoff_ref=pin(handoff),
    old_handoff_archive_ref=pin(archive),pending_rows=len(rows),next_original_failure_ordinal=1076,
    Canonical_unchanged=True),ensure_ascii=False,indent=2))
