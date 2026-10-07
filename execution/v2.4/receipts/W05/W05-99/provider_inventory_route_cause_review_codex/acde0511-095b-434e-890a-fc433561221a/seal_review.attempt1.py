from pathlib import Path
import hashlib, json, datetime

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / 'go.mod').is_file())
WT = ROOT / '.local/worktrees/codex-w0599-provider-binding'
NS = Path('execution/v2.4/receipts/W05/W05-99/provider_binding_executor_codex/epoch-correction-69a52b78d491456792bf394b01629e02')
def digest(raw): return hashlib.sha256(raw).hexdigest()
def ref(p):
    raw=p.read_bytes()
    return {'path': str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p), 'sha256':digest(raw), 'bytes':len(raw)}
def write(name,obj):
    (HERE/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read(name): return json.loads((WT/NS/name).read_bytes())

audit=json.loads((HERE/'read_audit.json').read_bytes())
for item in audit['inputs']:
    if digest(Path(item['path']).read_bytes()) != item['sha256']:
        raise RuntimeError('review input changed: '+item['path'])
expected={
 'failure_origins.json':'4b2ae8ae1d035b12a7d52e17d1b36aa136a6bec0c0884173d6166b93cc31e7ac',
 'stopped_handoff.v2.json':'620a48476a39b21824c71b2b05bab71cfae9313f021947beb91155f6595655f7',
 'stopped_manifest.v2.json':'d3cead72141f975e8dbbb67c21eb4ef9ad37b061de30b671bc8e61da8b72a2bf',
 'route-readonly-bb8320b67eae4c5a8d73f8e152ce5a8c/facts.json':'90d49349b8753ee683c815fc1bf239005a70bbeebadbbe38143d7b10a8fe4858',
 'route-readonly-bb8320b67eae4c5a8d73f8e152ce5a8c/scope_proposal.json':'0c120088f5868e14497c7166dc64511764a5ca19f6df17c266ef004eccf47437'}
for name, sha in expected.items():
    if digest((WT/NS/name).read_bytes()) != sha: raise RuntimeError('specified evidence mismatch '+name)
source_paths=['internal/domain/runtime_model_verification.go','internal/domain/runtime_provider_binding_windows_test.go']
for name in source_paths:
    if (WT/name).read_bytes() != (WT/NS/(name.replace('/','__')+'.frozen')).read_bytes():
        raise RuntimeError('frozen source mismatch '+name)
cases=[]
for case in ['case-00-1-none','case-01-red-none','case-02-0-none']:
    result=read(case+'.result.json'); actual=read(case+'-evidence/actual.json')
    for stream in ['stdout','stderr']:
        if digest((WT/NS/(case+'.'+stream+'.raw')).read_bytes()) != result[stream]['sha256']:
            raise RuntimeError('raw mismatch '+case)
    cases.append({'case':case,'result':ref(WT/NS/(case+'.result.json')),'stdout':ref(WT/NS/(case+'.stdout.raw')),'actual':ref(WT/NS/(case+'-evidence/actual.json')),'exit':result['exit'], 'inventory_count':actual['inventory_count'],'inventory_error':actual['inventory_error'],'stream_backup_error':actual['stream_backup_error'],'input_sha256':actual['input_sha256'],'input_after_sha256':actual['input_after_sha256'],'closed_db_sha256':actual['closed_db_sha256'],'models_reported':actual['model_calls'],'worker_starts_reported':actual['worker_starts'],'http_calls_reported':actual['http_calls']})
write('actual_evidence_audit.json',{'inputs_unchanged':True,'specified_hashes_verified':expected,'exact2_equal_sealed_failed_source':True,'cases':cases,'database_bytes_read_by_reviewer':0,'raw_claim_scope':'Existing author JSON/raw inspected, not replayed. The two successful cases call internal validators only; no public restore qualification.'})

review={
 'schema':'researchos.independent-readonly-cause-review.v1',
 'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'reviewer':'/root/w05_merge_review','executor':'/root/command_queue_impl','independent':True,
 'decision':'SOURCE_SCOPE_READY_NARROW_TYPED_ROUTE_CORRECTION_PENDING_ROOT_AUTHORIZATION',
 'source_acceptance':False,'execution_authorized_by_this_review':False,
 'summary':'ID-only MODEL route lookup is a confirmed false positive for the sealed sameRun TOOL. The next proposal is viable within the same two files only when classification is preceded by immutable reservation/key/request proof; changing the route predicate alone is insufficient.',
 'inputs':{'read_audit':ref(HERE/'read_audit.json'),'actual_evidence_audit':ref(HERE/'actual_evidence_audit.json'),'source':[ref(WT/x) for x in source_paths],'proposal':ref(WT/NS/'route-readonly-bb8320b67eae4c5a8d73f8e152ce5a8c/scope_proposal.json'),'facts':ref(WT/NS/'route-readonly-bb8320b67eae4c5a8d73f8e152ce5a8c/facts.json')},
 'confirmed_cause':{
  'source_location':'runtime_model_verification.go validateProviderInventory: route.id == request.route && route.capability == MODEL before !modelEffect continue',
  'producer_location':'runtime_broker_windows.go providerRoute validates id + capability + credential_revision + upper_bound; brokerEffect records request and cost; durability.go prepareEffectTx hashes [payload,cost] and atomically stores the original ledger ID in PREPARED.',
  'typed_routes':[{'id':'provider-fixture','capability':'MODEL','credential_revision':'test-v1','upper_bound':{'amount':'1','currency':'USD'}},{'id':'provider-fixture','capability':'TOOL','credential_revision':'local-tools-v1','upper_bound':{'amount':'0','currency':'USD'}}],
  'effect':'a188c5f17f90f2d42505d138e4b0993e:ea881e8bb01c8ec60d2acfd4a3405a42:1:tool:1',
  'tool_reservation':'314d45b4e659146150cf74d722bce149',
  'raw_ref':cases[2]['stdout'],
  'observed_rejection':'provider original MODEL key',
  'no_claim':'This is a TOOL false positive in the current validator, not proof that held model qualification/sameRun history is valid.'},
 'measured_progress':{'case00':'Both internal validators accept untouched original PREPARED; inventory_count=1; actual exit0.','case01':'Both reject original red at required missing original MODEL dispatch/provenance layer; actual exit0.','case02':'Untouched sameRun archive refused at MODEL-key check; actual exit1; the whole attempt remains failed.','cases_actually_executed':3,'not_run':47,'issue_failed_invocations_cumulative':3,'author_repair_attempts':2,'old_model_history_refusals_held':5,'reset_allowed':False},
 'required_algorithm_in_order':[
  '1. Retain SQL project/run/key/sequence vs decoded body equality and Num(epoch) int64 >=1. Resolve original Run/version and runtime binding/profile from that historical epoch. Missing or ambiguous provenance remains a refusal; never use current Run/profile or a fixture marker as authority.',
  '2. Before any non-MODEL early continue, resolve the effect original reservation by project/kind/id. Validate body identity/revision/receipt_hash and immutable version/content-hash relationships using existing storage conventions. Preserve all existing budget/history checks; an immutable flag or self-recomputed hash alone is not provenance.',
  '3. Treat reservation.provider_request_id as an independent original obligation. Require it to equal SQL effect_key and body key, original run/project and epoch-qualified task namespace. MODEL obligation from that original key remains binding even if payload capability, credential, SQL/body key or transport marker was changed. Missing ledger, rebound reservation, malformed key or contradictory evidence rejects, rather than classifies as non-MODEL.',
  '4. For a native Mu effect, match exactly one frozen route by id + capability + credential_revision, then verify its complete upper_bound against the original reservation and original request/cost hash. Do not choose between duplicate typed tuples by money, order or current provider settings; even duplicate equal entries or alternate bounds are ambiguous and refuse. Same id across different capabilities is allowed only with the full independent proof.',
  '5. Validate the actual stored cost request fields, not just a freshly synthesized object: policy_id, run_id, operation, money, provider_request_id, provider_event_id, reservation_id, cost_basis, occurred_at. In this bounded policy MODEL/TOOL lane these must match RESERVE, UPPER_BOUND, prepare/<original key>, nil reservation_id, original Run.created_at and frozen bound. Recompute Hash([original request, exact cost request]) and compare original PREPARED and every observation request_hash. Verify policy/run and original Task/Goal budget provenance without replacing historical revisions with current heads.',
  '6. For the positively proven TOOL exclusion, require original canonical tool key with positive ordinal, no provider_transport, exact original TOOL request fields, unique frozen TOOL tuple and reservation/hash proof. A MODEL key in the immutable reservation, MODEL capability, transport witness or conflicting immutable identity cannot be cleared by a TOOL claim. For an original MODEL zero upper_bound is still MODEL; numeric amount is never a classifier.',
  '7. Prevent reservation swapping or duplicate use from erasing the original MODEL obligation: in the scoped native policy Run join original MODEL RESERVE/prepare obligations back to exactly their PREPARED effect chains. An unaccounted original MODEL reservation, effect alias using a different TOOL reservation, or competing intent mapping must refuse. This is a read-only reconciliation of existing rows, not a new scheduling mechanism. Limit it to original native effect reservations, not unrelated fixture-dispatch or general budget holds.',
  '8. Preserve original dispatch/admission/runtime_ref version/profile/technical joins for all MODEL obligations and positively excluded native TOOLs. Preserve MODEL transport, payload, ordinal, history sequence, sealed response, UNKNOWN liability and END/backup checks. Legacy nonpolicy behavior may pass only through its existing positive original admission rule; unsupported legacy proof remains explicitly open.'
 ],
 'precision_notes':[
  'upper_bound is in the frozen route and cost, not in the request envelope; it must be derived and cross-checked, not invented as a new wire field.',
  'The live producer currently permits multiple same-id routes and requires capability as part of selection. Do not make all duplicate IDs illegal to fix this validator.',
  'No new migration/schema/SDK/broker/ledger write is needed for this proposed read-only validator correction. Existing source facts already contain the required keys and stored reservation/hash. Failure to reconstruct a particular old archive means an explicit compatibility refusal, not permission to fill missing history.',
  'Receipt/hash consistency is not cryptographic authentication against wholesale rewriting of all trusted database history; do not overclaim that threat model. The controls preserve immutable original ledger/admission facts while mutating copied effect evidence.'
 ],
 'exact_scope':[
  {'path':source_paths[0],'bounds':'validateProviderInventory classification and narrowly related private proof helper only. Preserve typed epoch fix and all original MODEL acceptance checks. Read existing ledger/history; no writes or fallback.'},
  {'path':source_paths[1],'bounds':'Existing zero-model copied-archive causal harness plus explicitly SYNTHETIC typed-tuple/budget identity controls. Preserve required-cause assertions and original public DBs; no held positive/model/coordinator execution.'}
 ],
 'controls_for_root_to_register_not_executed':[
  {'id':'R01','case':'Original PREPARED','expect':'Both internal validators accept, exact nonempty MODEL inventory=1, unchanged original inputs.'},
  {'id':'R02','case':'Original P12 red same bytes','expect':'Both reject specifically missing original dispatch/provenance; an earlier unrelated error is failure.'},
  {'id':'R03','case':'Original sameRun mixed MODEL/TOOL','expect':'Both accept; exactly the original three MODEL keys across qualification and ordinary Run, TOOL never enters transport inventory. Report original MODEL/TOOL counts and stable budget rows; no new calls or history acceptance.'},
  {'id':'R04','case':'Copied original MODEL key+capability+credential changed to TOOL and transport removed, original ledger untouched','expect':'Refuse at original reservation/key/request proof; cap-only or shared-id exclusion must not bypass.'},
  {'id':'R05','case':'Copied MODEL reservation_id swapped to a real TOOL reservation, including a variant with rehashed forged request','expect':'Refuse original obligation mismatch/unmatched MODEL reservation or noninjective mapping; original ledger facts stay unchanged.'},
  {'id':'R06','case':'SYNTHETIC valid zero-money MODEL and forged TOOL disguise','expect':'Genuine zero-money MODEL retains full MODEL checks; disguise refuses. Zero amount never grants non-MODEL status.'},
  {'id':'R07','case':'SYNTHETIC same id with unique different capability/credential vs duplicate exact tuple and conflicting bounds','expect':'Unique full original tuple succeeds; duplicate/ambiguous tuple refuses before arbitrary route choice.'},
  {'id':'R08','case':'Copied TOOL original key/epoch/credential/request hash or stored cost event/time/basis/policy mismatch','expect':'Each rejects its declared cause. Whole tuple, zero money and receipt label alone cannot excuse altered cost fields.'},
  {'id':'R09','case':'Prior missing dispatch/double-marker/absent binding/history/runtime-ref, sparse sequence and PREPARED=0obs copied controls','expect':'Preserve original fail-closed layer and UNKNOWN reserve behavior; run only after prerequisites and only the separately registered remaining case budget.'}
 ],
 'execution_boundary':{'this_review_tests':0,'sql_probes':0,'db_opens':0,'models':0,'workers':0,'network':0,'product_edits':0,'canonical_edits':0,'next_attempt':'Not authorized here. Root must register exact inputs/control budget; freeze source/tools/binary before first case; first unexpected result stops dependent lanes without repair/retry. Original historical5 remains HELD, P1 cumulative3 not reset.'},
 'database_identity_limit':{'original_input_sha256':'5a4ba446bb908d89b5265f067cac330d694d49531b76a10ca0861b0ddc504d85','postclose_copy_sha256':'c6878f2f09811deabc93712dc51b0f05148c311d959cbe02ebb07e9db15d76da','claim':'Distinct byte images. Actual.json records original input before/after same and mutation=none. facts.json records closed copy unchanged while author read it. Neither establishes original-to-copy byte identity or full semantic equivalence. Header/WAL explanation and sealed table/schema vectors are pending at this review; no reviewer SQL executed. Source causality is established against the observed closed image and actual refusal, not an unverified byte-equality claim.'},
 'formal_increment':0,'parent_acceptance':False,'public_restore_pass_claim':False
}
write('source_scope_review.json',review)
write('failure_origins.json',{'product_execution_failures_added':[],'existing_author_failure_not_recounted':ref(WT/NS/'failure_origins.json'),'tooling_diagnostics':[{'origin_id':'independent-route-cause-discovery-d8f26a','tool_output_chunk':'d8f26a','actual_outer_exit':0,'diagnostic':'Earlier read-only rg named nonexistent internal/domain/runtime_effect_dispatch.go and emitted os error2; subsequent commands returned successfully. No standalone native stderr file was captured; tool output is the original locator.','product_failure':False,'handling':'Discovered actual durability.go/runtime_broker_windows.go using rg directory/file listings; no product/test execution.'}]})
entries=[ref(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in ('manifest.json','handoff.json')]
write('manifest.json',{'files':entries,'count':len(entries),'self_excluded':True,'database_files_copied':0})
write('handoff.json',{'decision':review['decision'],'review':ref(HERE/'source_scope_review.json'),'audit':ref(HERE/'actual_evidence_audit.json'),'failure_origins':ref(HERE/'failure_origins.json'),'manifest':ref(HERE/'manifest.json'),'independent_review_only':True,'source_acceptance':False,'formal_increment':0})
print(json.dumps({'review':ref(HERE/'source_scope_review.json'),'handoff':ref(HERE/'handoff.json'),'failure_origins':ref(HERE/'failure_origins.json'),'manifest':ref(HERE/'manifest.json')},ensure_ascii=False))
