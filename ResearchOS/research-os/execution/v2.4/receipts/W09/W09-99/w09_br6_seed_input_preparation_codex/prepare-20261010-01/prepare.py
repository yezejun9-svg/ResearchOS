"""Prepare reviewable BR6 inputs only. Never import Main or invoke Root stages."""
from pathlib import Path
from datetime import datetime, timezone
import ast, copy, hashlib, json

O=Path(__file__).resolve().parent
R=O.parents[6]
W=R/'execution/v2.4/receipts/W09/W09-99'
B=W/'w09_formal_root_bridge_source_codex/bridge-20261010-06'
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
A=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')

def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin(p):
    p=Path(p).resolve(strict=True);raw=p.read_bytes()
    return dict(path=str(p),sha256=sha(raw),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def checked(ref):
    assert set(ref)=={'path','sha256','bytes'} and pin(ref['path'])==ref, ref
    return doc(ref['path'])
def save(name,value,raw=False):
    p=O/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def lit(p,name):
    rows=[ast.literal_eval(n.value) for n in ast.parse(Path(p).read_bytes()).body
          if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id==name]
    assert len(rows)==1,name
    return rows[0]
def main_ref(ref):return dict(path=Path(ref['path']).relative_to(R).as_posix(),sha256=ref['sha256'])

# Exact original I/O captures retain the two failed read-only observations.
rows=[]
with A.open('rb') as f:
    while True:
        offset=f.tell();line=f.readline()
        if not line:break
        rows.append((offset,line,json.loads(line)))
diagnostics=[]
for chunk,ordinal in [('aa4cdf',1197),('c4f434',1198)]:
    matches=[]
    for item in rows:
        d=item[2];p=d.get('payload',{})
        if d.get('type')!='response_item' or p.get('type') not in ('custom_tool_call_output','function_call_output'):continue
        for block in p.get('output',[]):
            if type(block) is not dict:continue
            try:v=json.loads(block.get('text',''))
            except ValueError:continue
            if type(v) is dict and v.get('chunk_id')==chunk:matches.append((item,v))
    assert len(matches)==1,(chunk,len(matches))
    result,tool=matches[0];cid=result[2]['payload']['call_id']
    calls=[x for x in rows if x[2].get('type')=='response_item' and x[2].get('payload',{}).get('type') in ('custom_tool_call','function_call') and x[2]['payload'].get('call_id')==cid]
    assert len(calls)==1 and tool['exit_code']==1
    call=calls[0]
    hosts=[x for x in rows if call[2]['ordinal']<x[2]['ordinal']<result[2]['ordinal'] and x[2].get('type')=='event_msg' and x[2].get('payload',{}).get('item',{}).get('type')=='CommandExecution']
    assert len(hosts)==1 and hosts[0][2]['payload']['item']['exit_code']==1
    host=hosts[0];triple=[rows[0],call,result]
    raw_ref=save(f'original-{ordinal}.raw.jsonl',b''.join(x[1] for x in triple),True)
    host_ref=save(f'original-{ordinal}.host-event.jsonl',host[1],True)
    diagnostics.append(save(f'original-{ordinal}.binding.json',dict(
        schema='researchos.w09-resource-readonly-host-binding.v1',actor_id='/root/attach_restore_independent_review',
        actor_thread_id=rows[0][2]['payload']['id'],source_audit_path=str(A),
        source_line_offsets=[x[0] for x in triple],original_line_sha256=[sha(x[1]) for x in triple],original_line_bytes=[len(x[1]) for x in triple],
        original_raw_ref=raw_ref,host_event_ref=host_ref,host_event_offset=host[0],host_event_ordinal=host[2]['ordinal'],
        actual_call_id=cid,actual_chunk_id=chunk,original_ordinal=ordinal,actual_outer_exit=1,
        actual_python_exit=None,actual_native_exit=None,actual_go_exit=None,actual_sql_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,actual_TP_exit=None,
        classification='READ_ONLY_WRONG_PARENT_DIRECTORY',product_calls=0,execution_grant=False,formal_acceptance=False)))

assert R.name=='research-os'
assert pin(B/'MF.json')['sha256']=='26c766cfe71628f12f95efcbe13b9bd28a3c14c8adcab7fc28d911d2ae373962'
hdf=doc(B/'HDF.json');contract=checked(hdf['root_calling_contract_ref'])
assert contract['source_ref']['sha256']=='59943073eb7c2e745d68acbe8b46e0031617de6d87fbe675584cb172de6ccd55'
source_ref=contract['source_ref'];checked_source=Path(source_ref['path']).read_bytes();assert sha(checked_source)==source_ref['sha256'] and len(checked_source)==source_ref['bytes']
review_dir=W/'w09_formal_root_bridge_independent_source_review_codex/review-20261010-06-attach'
review_ref=pin(review_dir/'review-decision.json');assert review_ref['sha256']=='9e07d804ce5e9cbafbbbb107862452bf3358458c27301d32ab0e93e42e323921'
source_refs=[pin(B/'HDF.json'),pin(B/'MF.json'),hdf['root_calling_contract_ref'],source_ref,contract['consumer_launcher_ref'],pin(review_dir/'HDF.json'),pin(review_dir/'MF.json'),review_ref]
frozen=lit(R/'execution/v2.4/formal_case_index.py','FROZEN_HASHES')
package=R.parent/'ResearchOS_Implementation_Package_v2.4'
frozen_refs=[];frozen_origins=[]
for name in [*frozen,'PACKAGE_MANIFEST.json']:
    src=package/(name if name=='PACKAGE_MANIFEST.json' else 'contracts/'+name)
    ref=pin(src)
    if name in frozen:assert ref['sha256']==frozen[name]
    frozen_origins.append(ref);frozen_refs.append(save('frozen-package/'+name,src.read_bytes(),True))

producer_sources=lit(R/'ops/ci/retrieval.py','SOURCES');assert len(producer_sources)==21
sources=set(lit(R/'execution/v2.4/formal_profile_w09.py','MINIMUM_SOURCE'))|set(producer_sources)
for d in ['internal/domain','adapters/retrieval']:
    sources.update(p.relative_to(R).as_posix() for p in (R/d).glob('*.go') if p.is_file())
source_files=[pin(R/x) for x in sorted(sources)]
source_by_rel={Path(x['path']).relative_to(R).as_posix():x for x in source_files}
assert source_by_rel['ops/ci/retrieval.py']['sha256']=='b85fb90d9927a2427ee29a5ff756b8e7d18b0639e9a3910a7621991bc3788f11'
bundle_ref=pin(S/'nf6-four-closed-actual-input.root.json');bundle=checked(bundle_ref)
native={};producer_refs=[bundle_ref,bundle['source_review_ref']];closed_observations=[]
for key,group in bundle['groups'].items():
    c=checked(group['producer_closed_ref']);summary=c['summary']
    assert c['status']=='MAIN_SELECTOR_NATIVE_PACKET_CLOSED_PENDING_INDEPENDENT_REVIEW' and c['error'] is None
    assert c['all_guards_closed'] and c['all_owned_jobs_closed'] and c['all_cleanup_receipts_saved'] and not c['cleanup_errors']
    assert summary['native_test_exit']==0 and summary['formal_acceptance'] is False
    report=checked(summary['report_ref']);tool=checked(summary['tool_run_ref'])
    assert report['run_id']==summary['run_id']==tool['run_id']
    assert report['check_id']==(key if key.startswith('W09-G') else None) and report['case_id']==(None if key.startswith('W09-G') else key)
    assert report['status']=='PASS' and report['exit_code']==0 and tool['native_exit_code']==0
    hashes=report['version_manifest']['source_sha256']
    assert set(hashes)==set(producer_sources)
    assert all(hashes[x]=='sha256:'+source_by_rel[x]['sha256'] for x in producer_sources)
    native[key]={'native_report_ref':summary['report_ref'],'native_tool_run_ref':summary['tool_run_ref']}
    producer_refs.extend([group['producer_closed_ref'],summary['report_ref'],summary['tool_run_ref']])
    closed_observations.append(dict(selector_key=key,run_id=summary['run_id'],producer_closed_ref=group['producer_closed_ref'],source21_equal=True,
        all_guards_closed=True,all_owned_jobs_closed=True,formal_acceptance=False))
assert set(native)=={'W09-G01','W09-G02','C19','A06'}
routes=[]
for command,check,case in contract['six_routes']:
    routes.append(dict(command_key=command,check_id=check,case_id=case,**native[check or case],mode_decision_ref=None,receipt_ref=None))
assert len(routes)==6
cm_ref=pin(R/'execution/v2.4/commands.json');locked_ref=pin(R/'execution/toolchains/locked.json')
assert doc(cm_ref['path'])['revision']==40
adapter_ref=source_by_rel['adapters/retrieval/local.go'];policy_ref=source_by_rel['ops/ci/w09_formal_router.py']
vector=dict(schema='researchos.w09.version-vector.v1',package_version='2.4.0',spec_files=frozen_refs,
    source_files=source_files,input_files=[cm_ref],lock_files=[pin(R/'go.mod'),pin(R/'go.sum')],tool_files=[locked_ref],
    environment=dict(os='Windows',arch='AMD64',timezone='Asia/Shanghai'),
    components=dict(model=dict(status='not_applicable',reason='W09 local retrieval Native selectors use no model provider.'),
       rubric=dict(status='not_applicable',reason='W09 checks use deterministic assertions and independent mode evidence, not a model rubric.'),
       adapter=dict(status='applicable',version='sha256:'+adapter_ref['sha256'],refs=[adapter_ref]),
       policy=dict(status='applicable',version='sha256:'+policy_ref['sha256'],refs=[policy_ref])))
blueprint=dict(schema='researchos.w09.current-context.v1',task_id='W09',step_id='W09-99',executor_id='codex:/root',
    run_id=None,created_at=None,acceptance_baseline_ref=next(x for x in frozen_refs if Path(x['path']).name=='acceptance.json'),
    version_vector=vector,source_coverage=None,registered_commands=routes,role_policy=None,global_evidence_refs=None)
blueprint_ref=save('context-input.full-pins.template.json',blueprint)
def convert(value):
    if isinstance(value,dict):
        if set(value)=={'path','sha256','bytes'}:return main_ref(value)
        return {k:convert(v) for k,v in value.items()}
    if isinstance(value,list):return [convert(x) for x in value]
    return value
main_template=convert(blueprint)
template_ref=save('context-input.main-format.template.json',main_template)
route_ref=save('registered-commands.native-map.json',dict(schema='researchos.w09-br6-native-route-preparation.v1',
    native_generation='fullw09-20261010-06',c19_policy='RUN_CURRENT_CM40',registered_commands=routes,closed_observations=closed_observations,
    mode_decisions_received=False,formal_acceptance=False))
open_fields=[dict(json_pointer='/run_id',owner='Root',requirement='Allocate one actual fresh formal context run identity before seed; distinct from the four Native run IDs.'),
    dict(json_pointer='/created_at',owner='BR6 seed',requirement='seed overwrites with actual UTC time.'),
    dict(json_pointer='/source_coverage',owner='BR6 seed',requirement='seed derives exact_files, two Go roots, paths_sha256 and source_files from current Main and producer Source21.'),
    dict(json_pointer='/role_policy',owner='Root roles and publish-registration',requirement='After actual role publication, set exact schema researchos.w09.execution-role-policy.v1 and exact registered registry_ref with path/sha256/bytes; add its Main two-key pin to version_vector.input_files.'),
    dict(json_pointer='/global_evidence_refs',owner='BR6 assemble',requirement='assemble creates C19/A06 run_receipt, version_manifest, command_receipt, assertion_results from actual consumers.')]
for i,row in enumerate(routes):
    open_fields.extend([dict(json_pointer=f'/registered_commands/{i}/mode_decision_ref',owner='/root/backup_regression_resources',
        requirement='Fill only the actual delivered QUALIFIED decision for this exact command_key/check_id/case_id and Native pair; pin complete path/sha256/bytes in handoff, convert to Main two-key relative ref.'),
        dict(json_pointer=f'/registered_commands/{i}/receipt_ref',owner='BR6 consume',requirement='Future actual CM40 dispatcher receipt; no historical substitution. Remains null for seed/propose and is replaced by consume.')])
guide=dict(schema='researchos.w09-br6-seed-preparation-guide.v1',status='PREPARED_OPEN_REQUIRED_INPUTS',
    full_pin_template_ref=blueprint_ref,main_format_template_ref=template_ref,native_map_ref=route_ref,
    reference_contract=dict(handoff='absolute path, sha256, bytes; existing file only',Main_vector_and_Native_refs='repository-relative POSIX path, sha256 only',
        Main_role_policy_registry_ref='repository-relative fixed Root capture path, sha256, bytes; preserve exact authority object',
        warning='full-pins template is an inventory blueprint; never pass it directly as context_input_ref content to Main.'),
    required_before_Root_seed=dict(actual_six_Mode_decisions=None,fresh_current4=None,fresh_Root_request=None,fresh_Root_grant=None,
        actual_Source_review_peer_proof=None,actual_Root_grant_audit=None,resource_environment_refs=None,formal_run_id=None),
    field_guide=open_fields,source_author_backend='/root/full_w09_source_review',source_author_canonical='codex:/root/full_w09_source_review',
    verifier_backend='/root/backup_regression_resources',Root_actor='codex:/root',Root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',
    c19_policy='RUN_CURRENT_CM40',live_CP_OW_read_or_held=False,current4_not_captured=True,
    stale_input_rule='Root must refresh every observed pin before seed. A changed Source21 invalidates reuse of these Native packets. CM40 must match fresh current4[3]. No old current4 authorizes seed.',
    stage_boundaries='seed builds vector only; propose verifies four Native pairs and six actual Mode decisions; consume must run all six registered consumers under fresh Root authority; roles/publish-registration precede assemble; formal verification remains separate.',
    formal_acceptance=False,Root_stages_run=0,TP_calls=0,dispatcher_calls=0,Native_calls=0,Go_calls=0,model_calls=0)
guide_ref=save('field-guide.json',guide)
readme='''BR6 seed input preparation only

The complete-pin template and route map preserve existing absolute path/SHA256/bytes identities. The Main-format template deliberately uses the strict Main repository-relative path/SHA256 format. Neither is a Root request or an accepted context. All six Mode decisions and all six dispatcher receipts remain null.

Root must first receive the actual six Backup Mode decisions, allocate the formal run ID, refresh current4 and all public pins, then materialize a new input from the Main-format template in Root-owned output. Add each actual Mode decision using its exact route and Native pair. Keep receipts null until consume. seed derives source coverage and actual timestamp. Use RUN_CURRENT_CM40 for both C19 routes.

The four frozen v2.4 files are byte copies from the original implementation package under this preparation directory. They make the otherwise external package files addressable by Main without escaping the repository. Existing Native reports retain their original producer spec manifest; no historical report was changed.

The Main vector already includes exact producer Source21, Main minimum sources, all current internal/domain and adapters/retrieval Go files, CM40, go.mod, go.sum and locked toolchain metadata. Component versions are exact source hashes, not invented release numbers. Windows/AMD64 and Asia/Shanghai are observed host metadata. Main role_policy and GLOBAL artifacts remain null until the prescribed Root stages. Root must add the eventual fixed role registry to input_files before formal verification.

This preparation ran no Main module, Root stage, Native selector, dispatcher, TP, Go or model. It read no live CP/OW or SS content and kept no Canon handles. It does not repeat the previous 36, 22, or 24+2 successful controls. Two wrong-parent read diagnostics are preserved as original1197/1198 with original call/output/host records; they were not Native or Python executions.
'''
readme_ref=save('README.md',readme.encode('utf-8'),True)
inputs=source_refs+producer_refs+frozen_origins+source_files+[cm_ref,locked_ref]
inputs=list({x['path']:x for x in inputs}.values())
for ref in inputs:assert pin(ref['path'])==ref
inventory_ref=save('input-pin-inventory.json',dict(schema='researchos.w09-br6-seed-input-inventory.v1',observed_at=datetime.now(timezone.utc).isoformat(),refs=inputs,
    frozen_copy_map=[dict(original=a,copy=b) for a,b in zip(frozen_origins,frozen_refs)],
    atomic_source_guard_used=False,source21_checked_against_four_reports=True,formal_acceptance=False))
verification_ref=save('preparation-observation.json',dict(schema='researchos.w09-br6-preparation-observation.v1',
    source21_count=21,covered_source_file_count=len(source_files),four_Native_pairs_pinned=True,six_routes_mapped=True,
    six_Mode_refs_null=True,six_consumer_receipts_null=True,frozen_contract_hashes_match=True,
    input_refs_rechecked=len(inputs),Main_imported=False,Root_stages_run=0,MainCanonScope_writes=0,CP_OW_handles=0,
    TP_calls=0,Native_calls=0,Go_calls=0,dispatcher_calls=0,model_calls=0,formal_acceptance=False,
    replayed_old_controls=False,original_diagnostic_refs=diagnostics))
out_refs=[pin(p) for p in sorted(O.rglob('*')) if p.is_file()]
mf_ref=save('MF.json',dict(schema='researchos.source-preparation-manifest.v1',files=out_refs,formal_acceptance=False))
hdf_ref=save('HDF.json',dict(schema='researchos.w09-br6-seed-input-preparation-handoff.v1',status='PREPARED_OPEN_MODE_AND_ROOT_AUTHORITY',
    actor='/root/attach_restore_independent_review',source_generation='bridge-20261010-06',native_generation='fullw09-20261010-06',
    source_refs=source_refs,MF_ref=mf_ref,context_input_full_pins_template_ref=blueprint_ref,context_input_main_format_template_ref=template_ref,
    field_guide_ref=guide_ref,native_route_map_ref=route_ref,input_inventory_ref=inventory_ref,preparation_observation_ref=verification_ref,
    original_diagnostic_refs=diagnostics,README_ref=readme_ref,
    six_Mode_decision_refs=[None]*6,fresh_current4=None,Root_request_ref=None,Root_grant_ref=None,formal_acceptance=False,
    execution_grant=False,MainCanonScope_writes=0,Root_stages_run=0,Native_calls=0,dispatcher_calls=0,TP_calls=0))
print(json.dumps(dict(HDF_ref=hdf_ref,MF_ref=mf_ref,template_ref=template_ref,guide_ref=guide_ref,diagnostic_refs=diagnostics),ensure_ascii=False))
