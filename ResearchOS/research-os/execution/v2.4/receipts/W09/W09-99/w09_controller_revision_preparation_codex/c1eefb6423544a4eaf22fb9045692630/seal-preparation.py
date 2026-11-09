"""Pure receipt IO/AST, not a candidate import or runtime test."""
import ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;SEL=ROOT/'selected';BASE=ROOT.parent.parent
OLD=BASE/'finite_controller_preparation_codex/2098f8232b5a4331b0cac70eccd32ce0'
RV=BASE/'f08_controller_independent_review_codex/d16a4b150b4e4fa9836f852c4a2bc505'
def ref(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,obj):
 p=ROOT/name
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
def check(condition,label):
 if not condition:raise RuntimeError(label)
 checks.append({'check':label,'result':'PASS_STATIC_ONLY'})
checks=[]
check(ref(RV/'review.json')['sha256']=='a630bb36136b44df28ba94a2a6b2a6d9e721baba596686733b2a34f10ad9e21b','exact independent review SHA')
mf=json.loads((OLD/'manifest.json').read_bytes());prefix=[]
for r in mf['members']:
 actual=ref(Path(r['path']));check(actual==r,'old immutable member '+Path(r['path']).name);prefix.append(actual)
spec=json.loads((SEL/'spec.proposed.json').read_bytes());oldspec=json.loads((OLD/'spec.json').read_bytes())
check(spec['roster']==oldspec['roster'],'all 49 original roster rows unchanged')
check(spec['caps']==oldspec['caps'],'all original caps unchanged')
check(sum(not r['requires_resource'] for r in spec['roster'])==45,'45 no-OS rows / 4 OS-dependent rows')
check(sum(len(r['expected_records']['run_records']) for r in spec['roster'])==89,'89 expected RUN events only')
check(sum(len(r['expected_records']['pass_records']) for r in spec['roster'])==89,'89 expected PASS events only')
check(spec['authorized'] is False and spec['root_binding'] is None,'false grant and absent actual Root binding')
edits=json.loads((SEL/'edits.json').read_bytes())
for name in ['controller_common.py','controller.py','case_worker.py','launch.py','seal_readonly.py','windows_debug_job_tree.py']:
 raw=(SEL/name).read_bytes();ast.parse(raw);inverse=raw
 for edit in reversed(edits.get(name,[])):
  before=edit['before'].encode();after=edit['after'].encode();check(inverse.count(after)==1,'unique inverse '+name)
  inverse=inverse.replace(after,before,1)
 check(inverse==(OLD/name).read_bytes(),'whole file inverse '+name)
check((SEL/'launch.py').read_bytes()==(OLD/'launch.py').read_bytes(),'launcher unchanged')
check((SEL/'windows_owned_process.py').read_bytes()==(OLD/'inputs/2-windows_owned_process.py').read_bytes(),'normal helper unchanged 6a4')
helper=(SEL/'windows_debug_job_tree.py').read_text(encoding='utf-8')
controller=(SEL/'controller.py').read_text(encoding='utf-8')
sealer=(SEL/'seal_readonly.py').read_text(encoding='utf-8')
common=(SEL/'controller_common.py').read_text(encoding='utf-8')
check(helper.index("debug['process_generations'] = generations")<helper.index('def pump'),'partial identities published before all debug pumping')
check(helper.index("cleanup['termination_succeeded'] = bool(terminate_job(job, 0xE0000308))")<helper.index('if may_continue:'),'failure termination precedes allowed cleanup continuation')
check("may_continue = event_owned" in helper and "debug['pending_failure_event'] = pending" in helper,'unconfirmed event ownership cannot be continued')
check('allow_nonzero' not in controller and "adjusted['actual_exit']" not in controller,'no fabricated zero exit admission')
check('HOLD_RESOURCE_UNEXPLAINED' not in controller and 'STOP_UNEXPECTED_RESOURCE_FAILURE' in controller,'unknown resource failure stops')
check("elif 'junction-resource'" not in sealer and "require_job(entry['owned_result'],True)" in sealer,'every native invocation needs full job closure')
check("g['normal_helper_ref']!=spec['normal_helper_ref']" in common and "g['debug_helper_ref']!=spec['debug_helper_ref']" in common,'mechanism role pins exact')
check("g['_authorization_input_refs']=root_authority" in common,'semantic authority checker mandatory')
check("spec.get('root_binding')" in common and "UNBOUND: actual Root binding absent" in common,'missing actual authority remains blocked')
original_failure=ref(RV/'failure-origins.json')
mapping=[
 {'id':'W09-C01','files':['windows_debug_job_tree.py'],'change':'On failed held event, terminate assigned exclusive Job first; continue only after actual successful termination and actual event ownership. On failure retain pending event and stop; cleanup may release it only after successful owned termination. No unknown image authorized.','runtime_status':'NOT_RUN'},
 {'id':'W09-C02','files':['windows_debug_job_tree.py'],'change':'Publish mutable observed generations list immediately; error/timeout result retains only actually observed PID/ctime/exit facts. Existing complete=false and NULL behavior preserved.','runtime_status':'NOT_RUN'},
 {'id':'W09-C03','files':['controller.py'],'change':'Remove adjusted exit-zero copy and allow_nonzero. Granted resource probe OSError/nonzero/NULL is STOP; only an explicitly ungranted resource yields the original resource HOLD. No new expected-error whitelist.','runtime_status':'NOT_RUN'},
 {'id':'W09-C04','files':['seal_readonly.py','controller_common.py'],'change':'All invocations require actual integer zero and complete Job/debug closure; no junction-directory exemption. HOLD must match an explicitly false resource in the actual validated grant.','runtime_status':'NOT_RUN'},
 {'id':'W09-C05','files':['controller_common.py','controller.py','case_worker.py','seal_readonly.py'],'change':'Proposed semantic Root capsule: immutable actual CAS request/invocation/raw/intent/audit/review/manifest and ordered canonical copies; tuple/failure-prefix/scope/lease/nonce/full execution-binding checks. Authority inputs join ledger. Actual Root producer and approved canonical field mapping absent: OPEN, root_binding NULL, execution forbidden.','runtime_status':'NOT_RUN'},
 {'id':'W09-C06','files':['controller_common.py','case_worker.py'],'change':'Exact seven spec mechanism roles, exact four tool roles, real entry/common/Python identity; helpers equal exact reviewed role pins. Raw bytes verified and compiled from same buffer. Case worker binds actual Root grant/spec and role pins.','runtime_status':'NOT_RUN'}]
write('fix-mapping.json',mapping)
contract={
 'schema':'researchos.w09.proposed-root-authority-contract.v1','status':'PREPARATION_ONLY_UNBOUND','actual_registration':None,'actual_root_tuple':None,'actual_resource_closure':None,
 'scope_root_binding_required':['before[checkpoint,ownership,failure_count]','after[checkpoint,ownership,failure_count]','registration_namespace absolute','canonical_original_paths ordered checkpoint/ownership/step_state/commands','canonical_fields explicit JSON key paths checkpoint_revision/ownership_revision/failure_origins/scope_ref/review_ref/lease','new_failure_origins exact fixed cut','controller_review_path path only'],
 'grant_new_required_refs':['registration_evidence_ref','controller_review_ref','root_issuance_ref'],
 'registration_capsule_schema':'researchos.w09.root-registration-capsule.v1',
 'capsule_required':['actor=codex:/root','before','after','registration_namespace','manifest_ref','audit_ref','invocation_ref','request_ref','intent_ref','registration_review_ref','canonical_copies ordered4'],
 'canonical_copies_shape':{'role':'checkpoint|ownership|step_state|commands','original_path':'actual fixed canonical target','before_ref':'immutable original raw','after_ref':'immutable actual desired/installed raw'},
 'cas_evidence':'Manifest pins every original/desired copy and all actual request/invocation/raw/intent/audit/review; reviewed register/wrapper/prepared refs must match actual request, argv/cwd and actual native zero with complete owned Job. Intent/audit/capsule canonical pairs equal. Step/commands byte SHA equal. Failure list is original prefix plus exact reviewed cut.',
 'lease_exact_shape':{'owner':'codex:/root','status':'EXECUTION_AUTHORIZED_ONCE','scope_ref':'actual bound fullspec ref','run_nonce':'actual once nonce','source_commit':spec['source_commit']},
 'reviews':['researchos.w09.root-registration-review.v1: reviewer codex:/root/w05_merge_review, REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION, requested_changes [], actual_registration_executed false; exact request/code refs/tuple','researchos.w09.finite-controller-bound-review.v1: reviewer codex:/root/w05_merge_review, READY_FOR_ROOT_W09_FINITE_ONCE, requested_changes []; fullscope and all execution_binding fields'],
 'acyclic_order':['Root binds spec with review path only','nonauthor reviews full spec and full finite execution inputs','Root prepares/reviews/actually registers CAS with review ref','Root seals immutable original+desired+actual evidence','Root issues once execution binding referencing sealed registration and actual nonauthor review','controller reads only immutable copies; later live canonical movement not reread'],
 'trust_boundary':'This does not cryptographically authenticate an arbitrary local JSON issuer. Root supplies actual original tool/CAS receipts under independently reviewed registration code. The corresponding Root producer/adapter is not implemented or authorized here. Merely setting authorized=true or supplying source-only review hashes cannot satisfy this protocol.',
 'open':['Root must adapt actual current canonical field paths and existing real registration wire format under separate review; no claim this new capsule already matches a real Root registration','Actual public resource catalog/current combined Main graph not constructed','Earlier W09 v2/v3 export coverage and exact vector-prefix changes are NOT silently merged into this fixed2098 revision; composition review remains required','Fresh nonauthor review of this five-module delta and future bound grant required','All 49 actual cases, helper behavior, compiler closure and OS probes NOT_RUN; no formal G01/G02 acceptance']}
write('root-authority-contract.proposed.json',contract)
controls=[('C01','unknown CREATE image, LOAD DLL, hash-timeout: termination before continuation; termination failure keeps held event'),('C02','fail after descendant CREATE and during finalization: partial generations retained, unobserved values NULL'),('C03','ungranted OS resource HOLD; granted symlink OSError and junction nonzero/NULL STOP'),('C04','directory-name substitution cannot exempt incomplete/error/timeout/NULL Job'),('C05','old source-only refs, wrong tuple/lease/nonce/caps/output/resources/review issuer, truncated failure prefix or stale canonical copies all reject'),('C06','different cataloged helper, unknown role, changed entry/common/Python hash, case-worker grant mismatch reject')]
write('future-controls.NOT_RUN.json',[{'finding':a,'controls':b,'status':'NOT_RUN','authority':None} for a,b in controls])
write('original-manifest-prefix.audit.json',{'original_manifest_ref':ref(OLD/'manifest.json'),'checked_members':prefix,'members_unchanged':True})
write('tool-observations.json',{'records':[{'tool_chunk_id':n,'actual_outer_exit':0,'actual_native_exit':None,'activity':activity} for n,activity in [('62090d','read review/handoff'),('0b7ea0','read common'),('73cbbb','read controller'),('66f047','read sealer'),('c3b736','read helper/failure'),('544886','read handoff/grant'),('a98830','read helper/worker/launcher'),('e7db29','read spec'),('b4f5b2','exclusive new namespace'),('b9495e','read original common'),('c9bddf','read exact source spans'),('bfdded','read helper pump/cleanup'),('657c94','read original anchors'),('f2023c','pure IO/AST initial source construction'),('6baa83','read full independent review'),('2c826d','pure IO/AST builder refinement'),('0bec10','pure IO/AST selected source construction'),('e65864','read manifest/spec shape')]],'target_calls':0,'no_raw_tool_transcripts_reconstructed':True,'new_failure_origins':[],'original_os206_failure_ref':original_failure,'original_os206_recounted':False})
audit=write('static-checks.final.json',{'schema':'researchos.w09.source-preparation-static-checks.v1','checks':checks,'failed':0,'candidate_imports':0,'target_calls':0,'actual_cases':0,'actual_native_exit':None,'all_inputs_after_equal_before':json.loads((SEL/'inputs.before.json').read_bytes())==json.loads((SEL/'inputs.after.json').read_bytes()),'preserved_original_failure_ref':original_failure})
hdf=write('handoff.json',{'schema':'researchos.w09.controller-revision-preparation-handoff.v1','author':'codex:/root/command_queue_impl','status':'SOURCE_PREPARATION_REPORTED_PENDING_NONAUTHOR_REVIEW','writer_status':'STOPPED_AFTER_SEAL','selected_directory':str(SEL),'selected_spec_ref':ref(SEL/'spec.proposed.json'),'selected_sources':[ref(SEL/n) for n in ['controller_common.py','controller.py','case_worker.py','launch.py','seal_readonly.py','windows_debug_job_tree.py','windows_owned_process.py']],'original_review_ref':ref(RV/'review.json'),'fix_mapping_ref':ref(ROOT/'fix-mapping.json'),'authority_contract_ref':ref(ROOT/'root-authority-contract.proposed.json'),'static_audit_ref':audit,'original_manifest_prefix_ref':ref(ROOT/'original-manifest-prefix.audit.json'),'source_inverse_ref':ref(SEL/'edits.json'),'input_before_ref':ref(SEL/'inputs.before.json'),'input_after_ref':ref(SEL/'inputs.after.json'),'roster':{'total':49,'resource_free':45,'OS_dependent':4,'expected_RUN':89,'expected_PASS':89,'actual_cases':0},'new_failure_origins':[],'preserved_original_os206_ref':original_failure,'known_open':contract['open'],'source_accepted':False,'Root_actual_grant':False,'formal_increment':0,'SQL24_permission':False,'manifest':'manifest.json; excludes only itself'})
members=[ref(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='manifest.json']
mfref=write('manifest.json',{'schema':'researchos.immutable-public-receipt-manifest.v1','members':members,'member_count':len(members),'self_excluded':True})
print(json.dumps({'handoff':hdf,'manifest':mfref,'members':len(members),'checks':len(checks),'selected_spec':ref(SEL/'spec.proposed.json')},ensure_ascii=False))
