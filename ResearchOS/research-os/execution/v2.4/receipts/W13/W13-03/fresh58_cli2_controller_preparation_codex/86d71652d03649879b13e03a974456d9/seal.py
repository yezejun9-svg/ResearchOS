"""Pure IO/AST seal of this preparation only; no candidate evaluation/import."""
import ast
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os')
def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def pin(p):
    p=Path(p);raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def doc(p):return json.loads(Path(p).read_bytes())
def save(name,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with (OUT/name).open('xb') as f:f.write(raw)
    return pin(OUT/name)

mappingpath=ROOT/'execution/v2.4/receipts/W13/W13-03/fresh58_validation_reference_mapping_codex/c745e294c1304498a6094777a42ed6e2/mapping.json'
m=doc(mappingpath);r=m['references'];scope=doc(OUT/'scope.current58.proposed.json')
closure=doc(r['source_commit_closure']['path'])
before=doc(OUT/'input.before.json')
for item in before:need(pin(item['path'])==item,'Original input changed')
extra=[closure['scope_ref'],closure['audit_refs'][1]]
oldauthority=doc(r['current43_authority_ref']['path'])
extra.extend(oldauthority['sealed_integration_refs'][:2])
extra.extend([pin(ROOT/'AGENTS.md'),pin(ROOT/'execution/v2.4/receipts/W13/W13-03/desktop58_forward_head_metadata_preparation_revision_codex/756f86f1976e4f80b6d006b5549c2370/forward_head_engine.final.proposed.py')])
for item in extra:
    p=Path(item['path']);p=p if p.is_absolute() else ROOT/p
    actual=pin(p)
    need(actual['sha256']==item['sha256'] and actual['bytes']==item['bytes'],'Additional input changed')
save('supplemental-read-inputs.json',extra)
for name in ['prepare.py','seal.py','runner.current58.proposed.py','authorization_gate.current58.proposed.py']:
    ast.parse((OUT/name).read_text(encoding='utf-8'),filename=name)

contract={
 'schema':'researchos.fresh58-cli2-binding-contract-proposal.v1',
 'status':'SOURCE_PREPARATION_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ACTUAL_ROOT_BINDING',
 'owner':'codex:/root/command_queue_impl','Root_sole_integrator':True,
 'source_commit':scope['source_commit'],'actual_parent':scope['actual_candidate_parent_expected'],
 'wire_compatibility':{'preserved':['researchos.cli43-fresh-compiler-held2-scope.v2','current43_authority_ref',
     'researchos.cli43.current-source-validation-authority.v1','researchos.cli43-compiler-authorization.v1',
     'cli43_fresh_compiler_held2_scope_ref','cli43_fresh_compiler_current_source_authority_ref',
     'cli43_fresh_compiler_controller_review_ref','researchos.cli43-compiler-controller-static-review.v1',
     'READY_FOR_ROOT_CURRENT43_HELD2_ONCE'],
     'meaning':'Compatibility names only. New SOURCE=e2ee/PARENT=a510, full-scope SHA and new gate/runner SHA forbid inheriting old r331 qualification or grant.'},
 'Root_authority_additions':{
   'source_parent':'a510dbef4a7e08fb5c428df44c39b133f3ffa856','unique_combined_source_paths':58,
   'source_commit_closure_ref':r['source_commit_closure'],
   'combined_source_set_ref':'New immutable researchos.current58-combined-source-set.v1: exact58 current ROOT-relative {path,sha256,bytes} refs. Root derives union from accepted Main38+CLI8+Desktop15 path mappings, verifies exact e2ee Git tree, independent full-scope review checks exact membership. Gate compares every ref to fresh catalog and hashes actual source; count58 alone is not derivation proof.',
   'forward_head_audit_ref':'Actual sealed forward registration audit, not a planned/request/grant. Must carry researchos.desktop58-forward-head-registration-audit.v1, e2ee registered_head, exit0, source closure pin, no source/formal/compile/GUI/model acceptance.',
   'forward_head_manifest_ref':'Actual post-registration manifest. Every entry verified; audit/invocation/intent/verified must be members. Hash-consistent original Root evidence is required; this template manufactures none.',
   'sealed_integration_refs':'Retain prior source-import provenance and append source_commit_closure_ref, forward_head_audit_ref, forward_head_manifest_ref with exact same REF representations.',
   'current_canonical_refs':'Future Root must use immutable copies; do not carry historical live CP paths as immutable runtime inputs.',
   'resource_preparation_audit_ref':'Future actual Root resource preparation audit; no current value invented.'},
 'future_scope_REQUIRED_NULL_fields':[k for k,v in scope.items() if v is None],
 'gate_registration_behavior':'Original independent W05 full-scope review -> real Root CAS/seal -> unique grant chain remains. Gate reads copied canonical4, not live CP for a long run. Full scope hash binds future resources, source set authority, controller review path and new runner/gate.',
 'metadata_producer_boundary':'Root must bind these new refs through its reviewed metadata builder/engine and fresh runtime overlay; existing module/wrapper bytes may be reused if consumer compatibility is independently verified. This package does not generate or execute a Root draft/CAS/grant.',
 'resource_requirements':[
   'Actual e2ee public Git source catalog; old597 input is historical metadata only, never relabelled. Include exact58 combined files and all public Go/schema/embed/platform/test dependencies required by actual CLI graph.',
   'Compiler selected22138 is a starting resource list only. Root revalidates actual immutable paths/membership and OS/tool pins; no current executable/cache/archive reused.',
   'New runtime catalog includes original Python __file__/__cached__/loaded module point-in-time pins and new controller/gate/Root metadata wrappers/binder. No lifecycle claim from two point-in-time observations.',
   'Fresh export/cache/WORK/importcfg/importcfg.link/generated testmain/all archives and newly built cmd/test2json, CLI, CLItest remain mandatory.',
   'Desktop Node/Electron/Vite build and169-case lane is separate, NOT implicitly authorized here; Node/SDK/model/external paid/private calls remain0.'
 ],
 'preserved_caps':{'case_count':2,'native_calls_max':16,'compiler_seconds':600,'case_owned_seconds':510,
  'Go_test_timeout_seconds':480,'inner_soft_seconds':3300,'outer_seconds':3600,'cleanup_seconds':5,
  'compiler_process_cap':2048,'case_process_cap':16,'active_job_limit':16,'total_image_cap':64,
  'upstream_dispatch_per_case':32,'proxy_admission_per_case':32,'qualification_observed_HTTP_legs':128,
  'unobserved_client_outbound_hard_cap':None,'SDK_Node_MODEL_external_paid_private':0},
 'native_operation_graph':['git-head','git-public-blobs','go-version','go-env','go-list','go-list-test2json',
  'build-test2json','build-cli','build-test','buildinfo-cli','buildinfo-test','buildinfo-test2json','case-00','case-01'],
 'native_graph_count':14,'fresh_actual_native_calls':0,
 'unchanged_test_evidence':'Exact original readonly/self-send leaves, actual compiler process tree, paired setup/proxy transport counters/raw/write facts, original assertion inverse, immutable closed-copy schema/typed rows and original DB not reopened.',
 'all_future_case_status':'NOT_RUN',
 'not_claimed':['Root execution authority','fresh58 qualification','Desktop169/Go3 execution','installed GUI/NVDA','P02/SDK/Pause/checkpoint completion','formal22/42','source acceptance'],
 'scope_review_loop':'Scope binds predeclared review path only; actual sealed CP WIP supplies review REF. Review pins full scope SHA plus new code; no scope<->review SHA cycle.'}
contractref=save('binding-contract.json',contract)
controls=[
 'Old a510 SOURCE or old a5 parent is rejected before helper/native; e2ee/a510 proposed binding is the only source pair.',
 'Old r331 scope/grant/review SHA cannot match new code/full scope; missing future tuple/authority/runtime/catalog NULL refuses.',
 'Current58 authority without fixed Desktop15 source review, closed writer or matching canonical head refuses.',
 'Source set wrong count/duplicate/alias/missing Desktop15/path absent from new catalog/hash mismatch refuses.',
 'Old597 catalog commit a510 refuses; new e2ee catalog exact current paths and ref values is the future positive route.',
 'Forward planned request in place of sealed audit, missing manifest member or nonzero invocation refuses.',
 'Malformed or later-than-current forward tuple refuses; forward source import does not grant tests by itself.',
 'Instrumentation preimage drift or reverse mismatch refuses; original business assertions and helper remain byte pinned.',
 'Any unknown executable/module, Job/cleanup error, timeout, native nonzero or first fixture failure stops dependent lane; no automatic retry.',
 'Only ordered readonly/self-send leaves may qualify; skipped/extra/missing test events or wrong CLI0/3 refuse.',
 'HTTP admission/dispatch/observation counters and closed-copy evidence preserve original independent semantics; no claim that unobserved outgoing network is hardcapped.',
 'All actual compiled/loaded/runtime/input vectors remain fresh-run requirements; source-only AST cannot substitute.'
]
save('future-controls.NOT_RUN.json',{'status':'NOT_RUN','controls':[{'id':'F58-%02d'%(i+1),'predicate':s,'actual':None} for i,s in enumerate(controls)],'no_candidate_evaluated':True})
save('source-delta-summary.json',{'runner':{'changed':'one SOURCE assignment only','all_functions_byte_and_AST_unchanged':True},
 'gate':{'changed':['SOURCE','PARENT','new validate_current58_source helper','one call after existing authority chain checks'],
 'unchanged':['load_scope','binding','registration_refs','validate_grant','Reader','all old register/CAS/manifest/independent-review predicates']},
 'launcher':r['launcher_ref'],'instrumentation_files':[r[k] for k in ['instrumentation_ref','instrumented_source_ref','instrumentation_helper_ref','roster_ref']],
 'main_product_writes':0,'canonical_writes':0,'target_execution':0})
save('tool-observations.json',{'actual_new_target_invocations':0,'new_failure_origins':[],
 'tools':[{'chunk':x,'actual_outer_exit':0,'actual_native_exit':None,'purpose':p} for x,p in [
 ('cb97cc','Read mapping'),('ceb9e3','Read pinned gate'),('85409e','Read runner source spans'),
 ('f25cdb','Read independent Desktop closure and old authority'),('25147a','Read engine/schema; returned display truncated, no nonzero'),
 ('b794f9','Read fixed engine seal and AGENTS'),('86844e','Read engine manifest producer tail'),
 ('8c3815','Pure IO audit type/keys'),('8018b4','Pure IO fixed scope fields'),('7949bf','Pure IO prior review path metadata'),
 ('88a016','Create own new receipt namespace'),('967b30','Pure IO/AST candidate generation and inverse checks'),('c5baa7','Read actual forward lease producer')]],
 'raw_limitation':'These are exact visible tool result identifiers and observed outer exits; native exits were not independently sampled. Candidate modules were never imported or run.'})
save('inputs.final.json',[pin(x['path']) for x in before])
need(doc(OUT/'inputs.final.json')==before,'Final input drift')
h=save('handoff.json',{'schema':'researchos.fresh58-cli2-controller-source-preparation-handoff.v1',
 'actor':'codex:/root/command_queue_impl','status':'SOURCE_PREPARATION_REPORTED_NOT_EXECUTION_AUTHORIZED',
 'runner_ref':pin(OUT/'runner.current58.proposed.py'),'authorization_gate_ref':pin(OUT/'authorization_gate.current58.proposed.py'),
 'launcher_ref':r['launcher_ref'],'scope_proposal_ref':pin(OUT/'scope.current58.proposed.json'),
 'authority_proposal_ref':pin(OUT/'current58-authority.proposed.json'),'source_set_proposal_ref':pin(OUT/'combined58-source-set.proposed.json'),
 'binding_contract_ref':contractref,'static_audit_ref':pin(OUT/'static-audit.json'),
 'future_controls_ref':pin(OUT/'future-controls.NOT_RUN.json'),'input_vector_ref':pin(OUT/'inputs.final.json'),
 'original_mapping_ref':pin(mappingpath),'original_source_closure_ref':r['source_commit_closure'],
 'changed_source_scope':'Only this new receipt runner/gate proposal. Existing launcher/helpers/Go fixtures, Main product, Root metadata and canonical unchanged.',
 'inverse_proofs':['runner.edits.json','gate.edits.json','runner.diff','gate.diff','static-audit.json'],
 'future_Root_registration':None,'future_resource_binding':None,'actual_compile_graph':None,'actual_case_results':None,
 'actual_target_calls':0,'new_failure_origins':[],'source_acceptance':False,'formal_increment':0,
 'open':['Non-author source/controller review','Actual Root forward-head seal and current58 authority','Fresh exact source/runtime/compiler catalogs',
         'Root metadata code binding + full-scope review + actual CAS + unique grant','One finite fresh2 execution and independent evidence closure',
         'Separate Desktop169/GUI/Go3/full-product/formal gates'],
 'state':'STOPPED'})
members=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file()]
mf=save('manifest.json',{'schema':'researchos.immutable-preparation-manifest.v1','entries':members,'count':len(members),'self_excluded':True})
print(json.dumps({'handoff':h,'manifest':mf,'members':len(members),'new_failure_origins':0,'STOPPED':True},ensure_ascii=False))
