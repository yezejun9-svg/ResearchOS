from pathlib import Path
import ast, hashlib, json

ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).parent
BASE=ROOT/'execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_revision_codex/02b58e39e08c457a8c48d10ce764fb94'
REVIEW=ROOT/'execution/v2.4/receipts/W05/W05-99/a04_formal_profile_revision_independent_review_codex/be0d42806fa145ee896d6da1a9379a33/review.json'
MAP=ROOT/'execution/v2.4/receipts/W05/W05-99/a04_producer_semantic_interface_readonly_codex/7bf0f159c3664564adf575a8ced9cc79/producer-semantic-interface-map.md'
AUTHOR='codex:/root/f08_whole_scope_review'
def pin(p):
    raw=p.read_bytes()
    return {'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,obj):
    with (OUT/name).open('xb') as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2).encode('utf-8')+b'\n')
    return pin(OUT/name)

construction=json.loads((OUT/'construction.actual.json').read_bytes())
sources=construction['source_pins']
for ref in sources.values():assert pin(Path(ref['path']))==ref
controls=json.loads((OUT/'source-controls.actual.v2.json').read_bytes())
assert controls['control_count']==79 and controls['matched_count']==79
earlier=json.loads((OUT/'source-controls.actual.json').read_bytes())
assert earlier['control_count']==79 and earlier['matched_count']==78
assert pin(MAP)['sha256']=='11a4cb23bd7f1a54d8c0704749b2a83caa2a28b84eb1facfd161f836dea25f9b' and pin(MAP)['bytes']==15811
text=Path(sources['execution/v2.4/formal_profile_w05.py']['path']).read_text(encoding='utf-8')
line_map={n.name:n.lineno for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
open_items=json.loads((BASE/'handoff.json').read_bytes())['open_requirements']
contract=json.loads((BASE/'evidence-contract.proposed.json').read_bytes())
contract['schema']='researchos.w05.a04-original-evidence-contract-proposal.v3'
contract['status']='PROPOSED_NOT_ROOT_ADOPTED'
contract['source_pins']=sources
contract['refusal_binding']='Root original issuance output names exact negative_scope_refs; selected scope/negative invocation/whole original response bind evidence run, current full product identity, task, exact assertion lane/id and frozen expected condition. Root original terminal JSON must contain that same negative_identity, negative_scope_ref and actual_refusal_response object. A relabeled response document alone is insufficient.'
contract['negative_issuance_additions']=['negative_scope_refs in issuance body and same ordered values in original_result.output grant JSON']
contract['negative_scope_schema']='researchos.w05.a04-negative-scope.v3'
contract['negative_invocation_schema']='researchos.w05.negative-invocation.v3'
contract['negative_original_response_schema']='researchos.w05.original-negative-response.v3'
contract['negative_common_binding_fields']=['run_id','task_id','lane','assertion_id','negative_condition','product_identity']
contract['negative_scope_abi_fields']=['root_grant_ref','argv','cwd','env_names','initial_tool_input','producer_ref']
contract['negative_invocation_additions']=['scope_ref','scope','root_tool_pair_ref','native_exit']+contract['negative_common_binding_fields']+contract['negative_scope_abi_fields']
contract['negative_root_original_stdout_fields']=['negative_identity','negative_scope_ref','actual_refusal_response','actual_launcher_native_exit']
contract['negative_hash_topology']='Existing grant first; scope references grant. Later external Root issuance observation names scope refs without rewriting grant. Original response references scope only; terminal pair contains response values without invocation/pair refs; invocation references pair; refusal references invocation and response. No output points to the hash of its own future consumer.'
contract['database_policy']='Complete immutable full SQLite raw snapshot remains mandatory. Actual DB kinds Task and Run, not TaskRun. Downstream memory key TaskRun aliases the validated Run. Task/Run require SQL content_hash NULL and exact current public body/identity/revision; Artifact requires sha256: digest equal SQL/body, same run/project, and full public Artifact schema. No SQL ran.'
contract['public_schema_projection_ref']=pin(OUT/'public-schema-projection.actual.json')
contract['session_event_policy']='Exact ten required keys; required-but-nullable run/command/domain-event IDs; published fixed kind and corresponding full payload; additional keys and sensitive payload keys reject. Sequence exact int>=1, duplicate event IDs and run/goal mismatches reject. Fixed closed 55-definition data projection of 3 pinned published schemas; no dynamic receipt imports or schema fetch.'
contract['remaining_open_requirements']=open_items
contract_ref=write('evidence-contract.binding.proposed.json',contract)
requests=[
{'id':'A04-REV-R02-IDENTITY','author_disposition':'IMPLEMENTED_SOURCE_PENDING_NONAUTHOR','file_ref':sources['execution/v2.4/formal_profile_w05.py'],'function':'verify_refusal','line':line_map['verify_refusal'],'change':'Exact original Root issuance scope list plus same current evidence run/product identities/task/lane/assertion/condition in scope, invocation, original response and observed terminal JSON. Raw response cannot be relabeled independently.','actual_producer_status':'OPEN; new v3 fields proposed, not adopted Root authority.'},
{'id':'A04-REV-R03-DB-SCHEMA','author_disposition':'IMPLEMENTED_SOURCE_PENDING_NONAUTHOR','file_ref':sources['execution/v2.4/formal_profile_w05.py'],'function':'_database_row','line':line_map['_database_row'],'change':'Actual Run DB kind; complete Task/Run public schema and NULL column; exact SQL/body identity/revision; Artifact strict sha256: prefix/hash equality/full entity/current run.','actual_reader_status':'NOT_RUN; no SQLite opened or SQL executed.'},
{'id':'A04-REV-R03-JSONL-SCHEMA','author_disposition':'IMPLEMENTED_SOURCE_PENDING_NONAUTHOR','file_ref':sources['execution/v2.4/formal_profile_w05.py'],'function':'_event_schema','line':line_map['_event_schema'],'change':'All published SessionEvent fields, kinds and per-kind payload schemas; typed identity/cursor, additional/sensitive fields rejected.','actual_stream_status':'NOT_RUN; full-schema positive controls are synthetic Source data, not captured LIVE events.'}]
report={
'schema':'researchos.a04-binding-source-revision-report.v1','author_id':AUTHOR,'decision':'SOURCE_PROPOSAL_WITH_OPEN_FOR_NONAUTHOR_REVIEW',
'basis_independent_review_ref':pin(REVIEW),'basis_handoff_ref':pin(BASE/'handoff.json'),'basis_manifest_ref':pin(BASE/'manifest.json'),
'producer_interface_mapping_ref':pin(MAP),'mapping_use':'Read-only map preserved as next semantic-decoder input. No four-decoder implementation added in this revision.',
'source_pins':sources,'request_dispositions':requests,'open_requirements':open_items,
'implementation_limits':['All six existing dispatcher selectors still end OPEN even if missing decoder functions were stubbed to succeed.','A04-03 and H08/P01/U02 actual semantic decoders remain unsupported.','Root finite LIVE capture, original refusal bridge/issuance formats, current source/resource/Job qualification and genuine nonauthor GLOBAL fifth part are not implemented by this Source package.','Current raw immutable DB snapshot, real SessionEvent stream, native/Job/budget/model originals are absent; synthetic controls cannot replace them.','Artifact reader validates SQL/body schema/hash reference only; actual content-storage bytes and complete settled-host receipt authority still need the full LIVE original producer/decoder qualification.'],
'verification':{'old_source_manifest_members_verified':len(construction['all_prior_members_verified']),'selected_sources':5,'profile_changed_definitions':construction['changed_profile_definitions'],'new_helper_definitions':['_public_value','_schema_value','_database_row','_event_schema'],'embedded_public_schema_definitions':55,'schema_effective_assertion_projection':'exact public assertion keys and refs, description-only annotations removed','runtime_pin_only_changes':2,'byte_exact_copied_sources':3,'whole_byte_forward_inverse':True,'source_controls_selected':79,'source_controls_matched':79,'earlier_control_record':{'controls':79,'matched':78,'reason':'Author synthetic Task fixture used IMPLEMENTATION, actual public Stage enum rejects it; corrected new fixture uses delivery. Source unchanged; earlier artifact retained.'},'no_full_candidate_module_imports':True,'SQL_calls':0,'Go_CLI_SDK_model_product_native_calls':0,'new_tool_failure_count':0},
'contract_proposal_ref':contract_ref,'public_source_basis':construction['public_source_basis'],'line_map':line_map,
'inverse_ref':pin(OUT/'source.inverse.actual.json'),'controls_ref':pin(OUT/'source-controls.actual.v2.json'),'earlier_controls_ref':pin(OUT/'source-controls.actual.json'),
'original_tool_io_ref':pin(OUT/'original-tool-io.json'),'independent_review_ref':None,'required_next_actor':'Root-selected command_queue_impl nonauthor; no author self acceptance.',
'main_adopted':False,'canonical_writes':0,'actual_root_authority':None,'source_acceptance':False,'formal_case_accepted_delta':0}
report_ref=write('report.json',report)
body='# A04 三项绑定修订（Source proposal）\n\n状态：SOURCE_PROPOSAL_WITH_OPEN，待不同作者身份复核。Main、canonical、正式接受均无改动。\n\n|原独审请求|本稿修改|实际资格|\n|---|---|---|\n|A04-REV-R02-IDENTITY|负向 scope、invocation、response 与 Root 原始工具 stdout 的同一 run/task/lane/条件绑定；Root 原始 issuance 逐值固定 scope 选集|新原始 producer ABI 尚 OPEN|\n|A04-REV-R03-DB-SCHEMA|查询实际 Run；Task/Run SQL NULL hash；完整公开实体校验；Artifact 保持 sha256: 严格摘要|SQL 和实际快照 reader 未运行|\n|A04-REV-R03-JSONL-SCHEMA|SessionEvent 十必填字段、未知 kind 拒绝、对应完整 payload；固定公开 schema 数据闭包|只有纯 AST 合成数据控，无 LIVE 流资格|\n\n79/79 纯数据控符合期望。首轮 78/79 的错误 Stage 正例被实际 enum 正确拒绝；该记录保留，新 fixture 使用公开 delivery，Source 未再修改。\n\n四个缺失 decoder、实际 Root capture/issuance 和独立第五 GLOBAL part 继续 OPEN；verify_capture_bundle 仍无条件拒绝所有 selector。\n'
with (OUT/'report.md').open('xb') as f:f.write(body.encode('utf-8'))
audit_ref=write('audit.json',{'schema':'researchos.a04-binding-source-audit.v1','author_id':AUTHOR,'source_pins':sources,'basis_review_ref':pin(REVIEW),'inverse_ref':pin(OUT/'source.inverse.actual.json'),'controls_ref':pin(OUT/'source-controls.actual.v2.json'),'construction_ref':pin(OUT/'construction.actual.json'),'source_only':True,'all_outputs_exclusive_create':True,'actual_producer_and_root_grant_open':True,'full_candidate_imports':0,'SQL_calls':0,'formal_count_delta':0,'new_origins':[]})
members=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ('manifest.json','handoff.json','postseal-original-tool-io.json')]
mf_ref=write('manifest.json',{'schema':'researchos.a04-binding-source-manifest.v1','author_id':AUTHOR,'member_count':len(members),'members':members,'self_included':False,'handoff_external':True,'postseal_original_tool_io_external':True,'status':'IMMUTABLE_SOURCE_PROPOSAL_WITH_OPEN'})
hdf_ref=write('handoff.json',{'schema':'researchos.a04-binding-source-handoff.v1','author_id':AUTHOR,'status':'STOPPED','decision':report['decision'],'source_pins':sources,'report_ref':report_ref,'audit_ref':audit_ref,'manifest_ref':mf_ref,'basis_independent_review_ref':pin(REVIEW),'contract_proposal_ref':contract_ref,'inverse_ref':pin(OUT/'source.inverse.actual.json'),'controls_ref':pin(OUT/'source-controls.actual.v2.json'),'original_tool_io_ref':pin(OUT/'original-tool-io.json'),'independent_review_ref':None,'next_review_actor':'Root-selected command_queue_impl nonauthor','remaining_open_requirements':open_items,'main_adopted':False,'actual_root_authority':None,'full_candidate_entrypoints':0,'SQL_Go_CLI_SDK_model_native_calls':0,'canonical_writes':0,'source_acceptance':False,'formal_case_accepted_delta':0,'new_tool_failure_origin_refs':[],'new_tool_failure_count':0,'postseal_original_io_annex':'postseal-original-tool-io.json; external to MF, no hash cycle.'})
for member in members:assert pin(Path(member['path']))==member
print(json.dumps({'handoff_ref':hdf_ref,'manifest_ref':mf_ref,'report_ref':report_ref,'audit_ref':audit_ref,'members':len(members),'decision':report['decision'],'new_tool_failures':0},ensure_ascii=False))

