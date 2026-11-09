"""Use the compact actual observer; retain the original truncated API and failure."""
from pathlib import Path
source=Path(__file__).with_name('seal_old21_programme_root_binding.root.py').read_text(encoding='utf-8')
source=source.replace("=='ce7571'","=='7ba7fd'").replace('capture(AUDIT,106045,','capture(AUDIT,106046,')
source=source.replace("observer['schema']=='researchos.root-old21-capture-result.v2'","observer['schema']=='researchos.root-old21-programme-compact-capture-result.v1'")
old="assert observer['observed_refs']==request['observed_refs'] and observer['peer_actor']==payload['review_author']"
new="""assert observer['observer_input_ref']==pin(N/'old21.programme.root-binding.observer-input.json')
assert observer['observed_ref_count']==len(request['observed_refs']) and observer['all_requested_refs_read_and_verified']
assert observer['payload_ref']==payload_ref and observer['peer_actor']==payload['review_author']
def initial_observer(call,result):return 'ce7571' in json.dumps(result['payload'].get('output'),ensure_ascii=False)
first_pair=capture(AUDIT,106045,initial_observer,root=True);assert first_pair
initial_truncation=save('old21.programme.initial-observer.API-truncation.root.json',dict(
    schema='researchos.root-retained-original-api-truncation.v1',issued_by='codex:/root',original_pair_refs=list(first_pair),
    actual_chunk_id='ce7571',original_API_response_truncated=True,original_full_process_stdout_asserted=False,
    original_stdout_reconstructed=False,compact_completed_observer_binding_ref=issued_binding,
    new_readback_needed_for_unresolved_truncation=True,Go_or_Native_rerun=False,formal_acceptance=False))"""
assert source.count(old)==1;source=source.replace(old,new)
source=source.replace("prior_ref=pin(N/'RESUME.cp375-w09-profile-adopted.live1111.root.json');prior=json.loads(Path(prior_ref['path']).read_bytes())","""prior_ref=pin(N/'RESUME.cp375-w09-profile-adopted.live1111.root.json');prior=json.loads(Path(prior_ref['path']).read_bytes())
prior_pending=json.loads(Path(prior['pending_ref']['path']).read_bytes())
def failed1111(call,result):return any(x.get('chunk_id')=='0f1ac2' for x in outputs(result['payload'].get('output')))
failure=capture(AUDIT,1111,failed1111,root=True);assert failure
standard=save('original1111.standard-binding.live1113.root.json',dict(
    schema='researchos.root-original-diagnostic-binding.v1',issued_by='codex:/root',original_capture_ref=failure[0],
    original_source_binding_ref=failure[1],original_source_binding_selector='$',original_ordinal=1111,
    original_bytes_unchanged=True,formal_authority=False))
new_row=dict(ordinal=1111,origin_ref=failure[0],origin_selector='$',capture_binding_ref=standard,
    description='Root programme sealer could not structurally parse the truncated initial API observer return. Actual initial readback was zero; original API bytes and failed sealer preserved. New compact readback resolves missing binding without Go/Native rerun.',
    capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',actual_outer_exit=1,actual_python_exit=1,
    actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)
pending=save('pending-diagnostics.cp375.live1113.root-prefix.root.json',dict(prior_pending,
    pending=prior_pending['pending']+[new_row],next_original_failure_ordinal=1113,
    unsealed_peer_diagnostic_ordinals=[1112],all_new_diagnostics_sealed=False))""")
source=source.replace("RESUME.cp375-old21-qualified.live1111.root.json","RESUME.cp375-old21-qualified.live1113.root.json")
source=source.replace("created_utc=now.isoformat(),prior_resume_ref=prior_ref,old21=","created_utc=now.isoformat(),prior_resume_ref=prior_ref,pending_ref=pending,next_original_failure_ordinal=1113,pending_diagnostic_ordinals=[1109,1110,1111,1112],old21=")
source=source.replace('before-old21-binding.live1111','before-old21-binding.live1113').replace('live next1111','live next1113')
source=source.replace('original1109..1110 pending','original1109..1111 sealed pending; independent Source review original1112 pending sealing')
exec(compile(source,str(Path(__file__)),'exec'),globals())
