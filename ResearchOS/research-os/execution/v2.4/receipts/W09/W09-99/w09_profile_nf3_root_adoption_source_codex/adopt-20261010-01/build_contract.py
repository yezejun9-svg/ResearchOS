"""Describe the future API without creating any Root request, lease or scope."""
import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 b=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,obj):
 p=N/name
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
 return pin(p)
inp=json.loads((N/'input-pins.json').read_bytes());p=inp['refs'];python=json.loads(Path(p['locked']['path']).read_bytes())['tools']['python']['path']
fields=['schema','issued_by','created_utc','kind','case_id','output_root','before_canonical_refs','main_profile_ref','formal_index_ref',
 'pending_ref','main23_qualification_ref','reviewed_source_audits_ref','reviewed_source_audit_refs','source_handoff_ref','source_manifest_ref',
 'source_review_handoff_ref','source_review_manifest_ref','source_review_decision_ref','source_author_audit_ref','source_review_audit_ref',
 'lease','native_leases','profile_commit_ref','profile_commit_audit_ref','formal_acceptance','parent_acceptance','formal_dispatcher',
 'automatic_retry','formal_case_accepted_delta','external_model_provider_requests','paid_provider_requests','production_DB_writes']
files={k:pin(N/name) for k,name in {'caller_ref':'register_w09_adoption.source.py','core_ref':'adoption_core.source.py','main_pair_ref':'main_pair_bytes.source.py'}.items()}
contract={'schema':'researchos.w09-root-adoption-calling-contract.v1','status':'SOURCE_ONLY_NO_EXECUTION_GRANT',
 'source_author':'codex:/root/native_temp_independent_review','root_actor':'codex:/root','root_thread_id':'01a11007-5233-7ca1-b71f-9e9e5ce84c98',
 'source_bindings':files,'input_pins_ref':pin(N/'input-pins.json'),'existing_dependencies_reused_not_retested':['Q','QR','NF3','NF3R'],
 'shared_canonical_transaction_ref':p['TP'],'existing_native_contract_ref':p['NF_contract'],
 'CLI':{'prefix':[python,'-I','-S','-B','-X','utf8',files['caller_ref']['path']],
  'propose':['propose','<Root-request-path>','<sha256>','<bytes>','<completed-Root-request-audit-path>','<sha256>','<bytes>'],
  'check':['check','<registration.plan.json-path>','<sha256>','<bytes>'],
  'activate':['activate','<registration.plan.json-path>','<sha256>','<bytes>'],
  'apply-profile':['apply-profile','<registration.plan.json-path>','<sha256>','<bytes>'],
  'finalize-native-requests':['finalize-native-requests','<registration.plan.json-path>','<sha256>','<bytes>',
    '<completed-activation-scope-audits-path>','<sha256>','<bytes>']},
 'root_request':{'schema':'researchos.root-w09-profile-nf3-registration-request.v1','exact_fields':fields,
  'kinds':['PROFILE_ADOPTION','NATIVE_SCOPES'],
  'output_root':'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/w09_profile_nf3_root_adoption_root/<32-lowerhex-case-id>',
  'output_parent':'Root creates the fixed output parent before propose; each case directory must be absent.',
  'current4':'Ordered checkpoint/path_ownership/step_state/commands full three-key refs from the actual current files; no fixed future revisions.',
  'pending':'A real Root-sealed pending suffix bound to the same Current4: exact-int cutoff=start-1, next>=start, rows exactly range(start,next). Empty is accepted only with next==start.',
  'main_profile_ref':'Current fixed Main path, exact bytes; PROFILE_ADOPTION must match accepted Q before; NATIVE_SCOPES must match actual committed Q after.',
  'formal_index_ref':'Current fixed Main formal_case_index.py three-key ref matching the accepted unchanged full index.',
  'lease':'Exactly lease_id/lease_issued_at/lease_expires_at; lowerhex32, aware times, issued<=created<=now<expires, duration<=3600 seconds.',
  'native_leases':'PROFILE_ADOPTION: {}; NATIVE_SCOPES: exact W09-G01,W09-G02,A06 lease objects, distinct ids, each within Root lease.',
  'profile_commit_ref':'PROFILE_ADOPTION: null; NATIVE_SCOPES: prior successful apply-profile.completed.json exact ref.',
  'profile_commit_audit_ref':'PROFILE_ADOPTION: null; NATIVE_SCOPES: completed actual Root call/return with commit SHA and W09_PROFILE_ADOPTED_CM40; completed before this new request.',
  'reviewed_source_audits_ref':p['peer_audits'],'reviewed_source_audit_refs':inp['peer_audit_refs'],
  'main23_qualification_ref':p['main23_qualification'],
  'false_fields':['formal_acceptance','parent_acceptance','formal_dispatcher','automatic_retry'],
  'zero_exact_integer_fields':['formal_case_accepted_delta','external_model_provider_requests','paid_provider_requests','production_DB_writes']},
 'own_independent_source_review_required':{'schema':'researchos.w09-root-adoption-independent-source-decision.v1',
  'decision':'SOURCE_ACCEPTED_FOR_ROOT_W09_ADOPTION','actor_role':'INDEPENDENT_NON_AUTHOR',
  'actor_id':'actual codex:/root/<peer>, different from Root and this Source author',
  'source_author_id':'codex:/root/native_temp_independent_review',
  'bindings':['source_handoff_ref','source_manifest_ref','caller_ref','core_ref','main_pair_ref','contract_ref'],
  'false_fields':['actual_executed','formal_acceptance','execution_grant'],
  'review_HDF':'manifest_ref,source_decision_ref,actor_id; decision must be a member of the exact review MF.',
  'actual_source_author_audit':'Existing NF3 actual-audit schema, author peer delivery bound to this HDF SHA.',
  'actual_source_review_audit':'Existing NF3 actual-audit schema, reviewer peer delivery bound to its decision SHA.'},
 'causal_order':[
  'Root obtains independent Source review and captures actual Source author/reviewer messages; no fabricated backdating.',
  'Root writes a PROFILE_ADOPTION request using fresh Current4 and sealed pending; completes an actual tool call exposing its SHA; captures that completed pair.',
  'propose writes only its new Root case directory: full Current4 archives, bounded profile Scope, exact CP/OW proposals, exact Main after bytes and reversible operations.',
  'check verifies the same proposal; activate uses the unchanged accepted TP update_pair with mandatory exclusive CP/OW ownership.',
  'apply-profile holds current CP/OW/SS/index and immutable Sources; fixed Main profile+commands are exclusively opened together, compared, journaled, written and read back.',
  'Root captures the actual apply-profile return; then writes a new NATIVE_SCOPES request with the new Current4, a newly sealed pending suffix and three finite leases.',
  'propose/check/activate register all three exact NF3 scopes/owners/workers using TP and retain all prior full archives and failures.',
  'Only after native activate returns, Root captures one actual Root call/return for each scope SHA; each capture must also include the activation receipt SHA and ROOT_SCOPE_REGISTERED.',
  'finalize-native-requests verifies those completed actual returns, writes the Current4 vector and three exact requests, and calls only existing NF3 validate_authority.',
  'Root later invokes unchanged NF3 prepare then run using the returned argv. These actual branches are never invoked by this registrar.'
 ],
 'native_scope_audit_bundle':{'schema':'researchos.root-w09-native-scope-actual-audits.v1',
  'exact_fields':['schema','issued_by','activation_ref','scope_audit_refs'],
  'scope_audit_refs_keys':['W09-G01','W09-G02','A06'],
  'capture_schema':'researchos.w09-native-producer.actual-audit.v1'},
 'minimum_shared_changes':{'Q':'One bounded CP WIP scope+registration entry, one CP worker, one OW subtask, append pending suffix, +1 CP/OW revisions through TP.',
  'Main':'Only fixed formal_profile_w09.py and commands.json; exact reviewed Q bytes, command proposal differs only by Root actual issued timestamp. Existing formal index untouched.',
  'NF3':'Close only the newly registered Q worker/owner status with actual adoption ref; add three exact NF3 scopes/workers/owners and one metadata record; append pending suffix; +1 CP/OW through TP.',
  'step_state':'Preserved byte-for-byte, never written.',
  'historical':'All previous Canon content, old D/11 evidence, original failures/NULL exit domains and existing receipts preserved.'},
 'counter_rules':['No hardcoded start ordinal or future CP/OW revision.','Empty suffix cannot lower next ordinal.',
  'All ordinal/cutoff/next/exit integers exclude bool.','No ordinal gaps, duplicate suffix entries, duplicate origin SHA+selector or reused prior invocation.',
  'Full original rows and standard source-binding refs retained; original failures counted once; unknown process-domain exits remain null.'],
 'failure_contract':{'TP':'Unchanged accepted transaction. Partial failures require Root reconciliation; no inverse executed automatically.',
  'Main':'shareMode=0 fixed two-target helper writes durable before/after archives and intent before first write; on failure preserves actual partial bytes, completed write indices, primary and secondary errors; reverse close in finally.',
  'one_shot':'Existing stage intent/journal means no automatic retry. First failure stops. Future NF3 UUID paths remain the exact reviewed one-shot choices.',
  'host_pair':'Root retains full actual request and return after each actual call completes; a future/not-yet-returned pair never authorizes its own launch.'},
 'non_authorities':['Main23 programme context grants no W09 execution or old21 authority.','Source and Source control fixtures never grant Root authority.',
  'No role registry, dispatcher route leases, ModeProof, programme qualification, full W09 formal capture or AcceptanceReceipt is issued here.'],
 'actual_branches_executed':False,'execution_grant':False,'formal_acceptance':False,'parent_acceptance':False,'formal_case_accepted_delta':0}
print(json.dumps({'contract_ref':save('root-calling-contract.source.json',contract)},ensure_ascii=False))
