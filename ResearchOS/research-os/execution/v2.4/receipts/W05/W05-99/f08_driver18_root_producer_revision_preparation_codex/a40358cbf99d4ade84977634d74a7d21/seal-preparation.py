"""Seal source-only preparation. Pure IO/hash/AST; no candidate import/execution."""
from pathlib import Path, PureWindowsPath
import ast, hashlib, json
OUT=Path(__file__).resolve().parent
P=OUT.parent.parent
def need(ok,why):
    if not ok:raise ValueError(why)
def ref(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,obj):
    raw=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode()
    with (OUT/name).open('xb') as f:f.write(raw)
    return ref(OUT/name)
def write(name,text):
    with (OUT/name).open('xb') as f:f.write(text.encode())
    return ref(OUT/name)
src=OUT/'driver18_root_producer.v3.proposed.py'
tree=ast.parse(src.read_bytes());nodes={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
def loc(name):return {'source_ref':ref(src),'function':name,'line':nodes[name].lineno,'end_line':nodes[name].end_lineno}
inv=json.loads((OUT/'whole-inverse.json').read_bytes())
cur=src.read_text(encoding='utf-8')
for h in reversed(inv['edits']):
    need(cur.count(h['new'])==1,'INVERSE_UNIQUE');cur=cur.replace(h['new'],h['old'],1)
need(cur.encode()==(OUT/'original.v2.py.txt').read_bytes(),'SECOND_WHOLE_INVERSE')
for p in [OUT/'construct.py',OUT/'seal-preparation.py',src]:ast.parse(p.read_bytes())
before=json.loads((OUT/'inputs.before.json').read_bytes())
need([ref(Path(x['path'])) for x in before]==before,'FINAL_FROZEN_INPUTS')
review=before[1]
fixes=[
 {'finding':'R01-REV','severity':'Critical','source_functions':[loc(n) for n in ['registration_layout','draft_inputs','preallocate','stage_sources','prepare_draft','run_registration','entry']],
  'closure':'Stage/draft/native are distinct direct siblings under an explicit Root registration_namespace whose leaf contains run_uuid. Stage intent precedes scope and is not authorization. Scope stores identical producer_layout. Draft validates exact scope/stage/controller-review/code fields and strict descendant relation before allocation/canonical copies. Native allocation protects current dref/regref/sref/d/index/MF/all Reader refs/gate/binder/actual producer, then checks unchanged inputs and live4 before leaf.',
  'unchanged':'Generic metadata UUID output restrictions remain for unrelated actions. Frozen gate strict-descendant and registration-code constraints unchanged.',
  'actual_execution':'NOT_RUN'},
 {'finding':'R02-REV','severity':'Important','source_functions':[loc('exact_resource_catalog')],
  'closure':'For every catalog row use actual=safe(path).resolve(), demand original string path == str(actual), and compare full original REF dict with pin(actual). GOROOT and Go entry use resolved literal strings. Reject aliases rather than silently rewrite the immutable catalog.',
  'limits':'Actual Windows resolved casing and future module-observation success require future execution. Unknown resources remain rejected; no resources added.', 'actual_execution':'NOT_RUN'},
 {'finding':'R03-REV','severity':'Important','source_functions':[loc('original_capture_closure'),loc('capture_action'),loc('seal_outer'),loc('seal_prepare')],
  'closure':'One shared complete closure now reads exact initial raw input, derives literal PowerShell cmd from action_identity argv, checks cwd and typed asynchronous response, checks terminal allowed keys/integer session/empty chars/terminal exit. Capture-only duplicate checks removed. Capture/outer seal/prepare seal all invoke shared closure before writing their derived capture or completion proofs.',
  'unchanged':'Real grant, original capture manifest, original host event refs, nonauthor pairing review, distinct locators and raw typed responses remain mandatory. No producer-created actor string is accepted as origin proof.', 'actual_execution':'NOT_RUN'}]
save('request-closure.json',{'review_ref':review,'findings':fixes,'source_preparation_only':True,'self_acceptance':False})

uid='11111111111111111111111111111111'
ns=PureWindowsPath(str(P))/('future-root-driver18-EXAMPLE-'+uid)
layout={'schema':'researchos.driver18-producer-registration-layout.v1','run_uuid':uid,'registration_namespace':str(ns),'stage_output_root':str(ns/'stage-code'),'draft_output_root':str(ns/'draft'),'native_output_root':str(ns/'native')}
paths=[PureWindowsPath(layout[k]) for k in ['stage_output_root','draft_output_root','native_output_root']]
path_checks={'namespace_name_contains_full_uuid':uid in ns.name,'three_direct_strict_children':all(p.parent==ns and p!=ns for p in paths),'distinct_children':len(set(paths))==3,'stage_code_register_under_namespace':(paths[0]/'register.py').is_relative_to(ns),'draft_original_under_namespace':(paths[1]/'checkpoint.original.json').is_relative_to(ns),'native_audit_under_namespace':(paths[2]/'registration-audit.json').is_relative_to(ns),'draft_not_namespace':paths[1]!=ns}
need(all(path_checks.values()),'STATIC_PATH_REACHABILITY')
save('positive-path-example.NOT_RUN.json',{'classification':'STATIC_PATH_ALGEBRA_ONLY_NOT_ROOT_INTENT','example_only_uuid':True,'no_directories_created':True,'producer_layout':layout,'actual_Root_registration_subset':{'run_uuid':uid,'registration_namespace':str(ns),'registration_output_root':layout['native_output_root'],'producer_layout':layout},'stage_input_subset':{'schema':'researchos.driver18-stage-code-input.v1','producer_layout':layout,'producer_output_binding':{'schema':'researchos.driver18-producer-output-binding.v1','owner':'codex:/root','action':'stage-code','metadata_output_root':layout['stage_output_root']}},'checks':path_checks,'files_and_references':'FUTURE_ROOT_REQUIRED_NOT_FABRICATED','runtime_result':'NOT_RUN'})
save('required-input-contract.json',{
 'source_preparation_only':True,'actual_Root_tuple':None,'actual_grant':None,'actual_resource_catalog':None,
 'new_field':'actual_Root_registration.producer_layout','exact_layout_keys':list(layout),
 'root_stage_input':'stage-code input adds producer_layout; producer_output_binding remains exact v1. Root first creates registration namespace parent only; all three children initially absent. Metadata input file must be in a separate receipt child/namespace, not at a parent enclosing any output.',
 'scope_binding':'Frozen binder passes actual_Root_registration unchanged. Root must put identical producer_layout in actual_Root_registration before complete-scope review. Scope-producing metadata output remains in generic executor/<newUUID>, disjoint from registration namespace children. No scope-review hash cycle added.',
 'draft_binding':'Root invokes the exact staged producer for draft/register; current producer REF must exactly equal staged-code producer_ref. staged-code.json carries layout and exact staged producer/register/wrapper refs. Draft source and every declared input/Reader ref are protected before allocating the explicit draft child.',
 'review_binding':'Existing nonauthor full-scope review and existing complete registration draft review remain required. Future reviews must reference this new producer bytes and full scope containing producer_layout.',
 'native_binding':'registration_output_root == producer_layout.native_output_root. Registration draft/source code live in separate sibling children. Protected trees include current scope/draft/review/index/MF/Reader refs/current producer. Evidence stored directly in the registration namespace root before native allocation would enclose output and is rejected; place such inputs in separate children or external sealed namespaces.',
 'later_bundle':'Unchanged seal_registration creates registration-bundle-<phase>.json at namespace root only after native execution has closed. Grant outputs remain the separate existing preflight/authorization namespaces.',
 'resources':'All file REF path strings must equal actual resolved canonical Windows spelling, SHA and bytes. Same content with alternative case/relative/path alias is rejected; Root must derive a NEW canonical catalog with provenance, never rewrite sealed inputs.',
 'caps':'Existing consumer CAPS unchanged; 32 native calls, compiler 600s, test 750s, inner 3300s, outer 3600s, cleanup 5s, PARTIAL_17_EXPLICIT. I17/SQL24/source/formal remain OPEN.',
 'sequence':['Root supplies actual public inputs and new layout intent','Root stages reviewed producer into stage child','Root builds exact scope with layout/resource catalog and gets nonauthor full-scope review','Root invokes staged producer to validate all draft inputs then allocate draft child','Nonauthor registration-draft review','Root-only reviewed registration allocates native sibling after all guards','Root seal registration','Root preflight/grant under unchanged authorization rules','Root actual tool dispatch/capture and nonauthor exact original pair review','All capture/seal entrypoints share complete raw command/session validation'],
 'future_execution_status':'NOT_RUN_NO_LEASE_NO_CAS_NO_GRANT'})
controls=[
 ('R01-P01','Root-created namespace parent with new stage/draft/native direct siblings and full exact input chain is accepted through path guards'),
 ('R01-N01','Output equals registration namespace rejected before allocation'),('R01-N02','Nested draft/native below staged evidence rejected'),('R01-N03','Different run_uuid/namespace/layout in stage and scope rejected'),('R01-N04','Missing or mismatched controller review/code refs rejected before draft allocation/copies'),('R01-N05','Native overlaps dref/regref/index/MF/Reader input tree rejected before allocation'),('R01-N06','Existing sibling or casefold-colliding sibling rejected'),('R01-N07','Stale or non-staged current producer ref rejected'),
 ('R02-P01','Full resource REF with actual resolved canonical path and exact SHA/bytes accepted by producer and consumer observations'),('R02-N01','Case-only path alias rejected despite WindowsPath equality'),('R02-N02','Mismatching path/SHA/bytes or tool REF dictionary rejected'),('R02-N03','GOROOT or Go path spelling differs from actual resolve rejected'),
 ('R03-P01','Real complete externally sealed original command/poll/session pair accepted by all three entrypoints'),('R03-N01','Direct outer seal with unrelated nonempty initial cmd rejected'),('R03-N02','Direct prepare seal with wrong initial workdir rejected'),('R03-N03','Capture mismatched input or altered argv quote literal rejected'),('R03-N04','Terminal wrong session/type/extra input key/nonempty chars rejected'),('R03-N05','Missing external manifest/pairreview/grant rejected')]
save('future-controls.NOT_RUN.json',{'controls':[{'id':i,'intent':v,'status':'NOT_RUN'} for i,v in controls],'candidate_or_consumer_execution':False,'runtime_PASS_claimed':False})
write('handoff.md','''# F08 producer v3 source-only revision

This candidate addresses only R01-REV, R02-REV and R03-REV in the pinned v2 review. No candidate, consumer, Go, SQL, helper, Job, network or model was executed. All future controls are NOT_RUN.

The new producer_layout is a future Root supplied path intent, not a grant. It fixes the previously impossible registration layout without changing the frozen gate or binder: stage-code, draft and native are distinct direct children of one registration namespace containing run_uuid. The scope remains fully reviewed and registration remains Root-only. Root must invoke the staged exact producer and protect all current original input parents; inputs in a parent encompassing an output are deliberately rejected.

Resource refs are rejected unless the original serialized path equals the actual resolved canonical spelling. This preparation neither rewrites a catalog nor proves future Python module observations. Exact raw initial command/cwd and typed terminal session checks now run in the one shared original-capture closure for all capture/seal paths. External original event capture and independent pairing review remain mandatory.

Whole byte inverse restores dcf v2, including all first-round fixes. Frozen c391/d2ad/75d3 consumers remain untouched. Limits and PARTIAL_17_EXPLICIT remain unchanged; I17 and SQL24 acceptance remain OPEN. Future Root resource/scope/draft/CAS/grant production and independent review are still required. STOPPED after sealing.
''')
save('tool-observations.json',{'observations':[
 {'chunk_id':'145aab','kind':'read full review','actual_outer_exit':0,'actual_native_exit':None},
 {'chunk_id':'611050','kind':'read frozen producer','actual_outer_exit':0,'actual_native_exit':None},
 {'chunk_id':'a55304','kind':'read AGENTS','actual_outer_exit':0,'actual_native_exit':None},
 {'chunk_id':'6a1090','kind':'read bounded producer source','actual_outer_exit':0,'actual_native_exit':None},
 {'chunk_id':'f38ea2','kind':'read frozen consumer bounds','actual_outer_exit':0,'actual_native_exit':None},
 {'chunk_id':'84865c','kind':'create new owned receipt leaf via pure Python IO','actual_outer_exit':0,'actual_native_exit':None},
 {'chunk_id':'4b4971','kind':'pure IO/AST source construction; candidate not imported','actual_outer_exit':0,'actual_native_exit':None},
 {'chunk_id':'3f5b4f','kind':'read frozen Reader/registration predicates','actual_outer_exit':0,'actual_native_exit':None}],
 'new_failure_origins':[],'native_exit_not_separately_sampled':True,'old_origins_unchanged':True})
save('final-static-audit.json',{'whole_inverse_second_check':True,'input_before_after':[ref(Path(x['path'])) for x in before],'input_drift':0,'AST_files':3,'static_path_algebra':path_checks,'static_path_examples_are_NOT_RUN':True,'candidate_import_or_execution':False,'new_failure_origins':[]})
handoff=save('handoff.json',{'schema':'researchos.source-preparation-handoff.v1','actor':'codex:/root/command_queue_impl','status':'SOURCE_PREPARATION_REPORTED_PENDING_NONAUTHOR_REVIEW','source_ref':ref(src),'review_request_ref':review,'base_v2_ref':before[0],'frozen_consumer_refs':before[4:7],'whole_inverse_ref':ref(OUT/'whole-inverse.json'),'fix_mapping_ref':ref(OUT/'request-closure.json'),'required_input_contract_ref':ref(OUT/'required-input-contract.json'),'positive_path_example_ref':ref(OUT/'positive-path-example.NOT_RUN.json'),'future_controls_ref':ref(OUT/'future-controls.NOT_RUN.json'),'static_audit_refs':[ref(OUT/'static-audit.json'),ref(OUT/'final-static-audit.json')],'actual_candidate_execution':False,'actual_CAS':False,'actual_grant':False,'source_acceptance':False,'new_failure_origins':[],'writer_status':'STOPPED_AFTER_SEAL','unchanged_functions':32,'input_drift':0,'limits_unchanged':True,'I17':'OPEN_NOT_AUTHORIZED','SQL24':'OPEN_NOT_AUTHORIZED'})
members=[ref(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json']
manifest=save('manifest.json',{'schema':'researchos.immutable-source-preparation-manifest.v1','files':members,'member_count':len(members),'excluded_only_self':True})
print(json.dumps({'source':ref(src),'handoff':handoff,'manifest':manifest,'members':len(members),'source_execution':False,'new_origins':0},ensure_ascii=False))
