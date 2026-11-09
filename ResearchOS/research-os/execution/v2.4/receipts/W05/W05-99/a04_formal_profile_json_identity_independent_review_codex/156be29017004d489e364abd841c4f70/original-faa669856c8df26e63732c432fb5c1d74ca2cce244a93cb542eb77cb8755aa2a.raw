from pathlib import Path
import ast, hashlib, json
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).parent
BASE=ROOT/'execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_binding_revision_codex/c97e11df194d431cb901934bf01e6c94'
PEER=ROOT/'execution/v2.4/receipts/W05/W05-99/a04_formal_profile_binding_independent_review_codex/70ca957e1f4b4d7fb4223159361c86e4'
ACTOR='codex:/root/f08_whole_scope_review'
def pin(p):
 b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,d):
 with (OUT/name).open('xb') as f:f.write(json.dumps(d,ensure_ascii=False,indent=2).encode('utf-8')+b'\n')
 return pin(OUT/name)
construction=json.loads((OUT/'construction.actual.json').read_bytes())
sources=construction['source_pins']
for ref in sources.values():assert pin(Path(ref['path']))==ref
controls=json.loads((OUT/'source-controls.actual.v2.json').read_bytes())
assert controls['count']==26 and controls['matched_count']==26
old_hdf=json.loads((BASE/'handoff.json').read_bytes())
contract=json.loads((BASE/'evidence-contract.binding.proposed.json').read_bytes())
contract['schema']='researchos.w05.a04-original-evidence-contract-proposal.v4'
contract['source_pins']=sources
contract['strict_original_response_comparison']='Recursive JSON value equality requires identical types at every value, including int/bool/float; object member order is irrelevant, array order is strict. Nonfinite or non-JSON values reject. No canonicalization merges numeric types.'
contract['task_active_run_rule']='The public nullable pointer may be null for a legitimate terminal state; any nonempty pointer different from the selected product Run is rejected both by complete row validation and at the composite original-evidence entry. Existing Run/event/native/terminal version provenance requirements remain mandatory; null alone is not settlement proof.'
contract_ref=write('evidence-contract.identity.proposed.json',contract)
source_text=Path(sources['execution/v2.4/formal_profile_w05.py']['path']).read_text(encoding='utf-8')
lines={n.name:n.lineno for n in ast.parse(source_text).body if isinstance(n,ast.FunctionDef)}
inverse=json.loads((OUT/'source.inverse.actual.json').read_bytes())
runtime_pin=construction['runtime_producer_ref']
assert pin(Path(runtime_pin['path']))==runtime_pin
failure=pin(OUT/'failure-origin.9691d9.json')
assert failure['sha256']=='80d666653910310afeeb06dcf11a5e73ac72e4c2db79e43f21311409359b2194'
report={
'schema':'researchos.a04-json-identity-source-revision-report.v1',
'author_id':ACTOR,'decision':'SOURCE_PROPOSAL_WITH_OPEN_FOR_NONAUTHOR_REVIEW',
'basis_independent_review_ref':pin(PEER/'review.json'),'basis_review_handoff_ref':pin(PEER/'handoff.json'),
'basis_peer_controls_ref':construction['basis_peer_controls_ref'],
'basis_source_handoff_ref':pin(BASE/'handoff.json'),'basis_source_manifest_ref':pin(BASE/'manifest.json'),
'source_pins':sources,'request_dispositions':[
{'id':'A04-BIND-R01','disposition':'AUTHOR_IMPLEMENTED_PENDING_NONAUTHOR','function':'verify_refusal','line':lines['verify_refusal'],'helper':'_same_json','helper_line':lines['_same_json'],'change':'Complete Root original terminal actual_refusal_response and independently read response use recursive exact JSON types; int1/boolTrue/float1.0 cannot alias, identical typed values with different object key order remain legal.','actual_root_negative_producer':'OPEN_NOT_IMPLEMENTED'},
{'id':'A04-BIND-R02','disposition':'AUTHOR_IMPLEMENTED_PENDING_NONAUTHOR','functions':['verify_live_originals','_database_row'],'lines':[lines['verify_live_originals'],lines['_database_row']],'helper':'_current_run','helper_line':lines['_current_run'],'change':'Reject Task.active_run_id pointing at any different Run in the raw row and composite original entry; permit the public nullable terminal pointer. Existing typed terminal Run/state/native/version provenance remains required, no null-only PASS.','public_producer_ref':runtime_pin,'public_producer_lines':[276,279,283,284,285]}],
'unchanged_boundaries':[
'Fixed 55-definition schema assignment is byte unchanged. Task/Run nullable SQL content_hash and strict Artifact schema/hash remain intact.',
'Published SessionEvent, unknown-kind/per-kind payload and complete original JSONL guards remain byte unchanged.',
'Root-issued negative scope/identity/condition/native/whole original response requirements remain intact.',
'No new selector, lane, Root scope, grant, native action or SDK/paid-model authority added.',
'All six dispatcher selectors still end unconditionally OPEN. Four semantic decoders and actual capture/issuance remain OPEN.',
'The producer semantic interface mapping is not implemented by this revision.'],
'open_requirements':old_hdf['remaining_open_requirements'],
'verification':{
'prior_manifest_members_verified':30,'selected_source_count':5,'whole_byte_forward_inverse_entries':5,
'profile_changed_definitions':inverse['entries'][0]['changed_definitions'],'profile_new_pure_helpers':['_same_json','_current_run'],
'public55_schema_bytes_unchanged':True,'three_other_sources_byte_exact_copy':True,'runtime_exact_pin_changes':2,
'selected_pure_AST_controls':26,'matched_controls':26,'previous_peer_four_false_acceptance_inputs_replayed':4,
'previous_peer_74_70_artifact_unchanged':True,'full_candidate_modules_imported':0,'formal_path_hash_reader_exercised':False,
'composite_database_stub_controls':3,'actual_SQL_calls':0,'Go_CLI_SDK_model_native_product_calls':0,
'fullLIVE_original_proof':False,'actual_root_authority':None},
'controls_ref':pin(OUT/'source-controls.actual.v2.json'),'inverse_ref':pin(OUT/'source.inverse.actual.json'),
'contract_proposal_ref':contract_ref,'original_tool_io_ref':pin(OUT/'original-tool-io.json'),
'new_tool_failures':[{'root_assigned_ordinal':677,'origin_ref':failure,'outer_exit':1,'metadata_python_exit':1,'native_product_exit':None,'reason':'Selected AST extractor omitted IDS prerequisite of ASSERTION_LANES. Old failed source_controls.py preserved and never retried; new controls.v2 adds IDS dependency, separate output.'}],
'new_tool_failure_count':1,'prior_failure_674_recounted':False,
'non_author_review_ref':None,'next_actor':'Root-selected command_queue_impl independent reviewer',
'main_adopted':False,'canonical_writes':0,'source_acceptance':False,'formal_case_accepted_delta':0}
report_ref=write('report.json',report)
md='# A04 JSON 类型与当前 Run 绑定修订\n\nSOURCE_PROPOSAL_WITH_OPEN；未采用 Main，待非作者复核。\n\n|请求|改动|纯控结果|\n|---|---|---|\n|A04-BIND-R01|完整原始 response 递归按 JSON 类型比较；对象键顺序可不同，数组和数值类型严格|1/true/1.0 替换拒绝；完整合法同型记录保留|\n|A04-BIND-R02|Task 的非空 active_run_id 必须是所选 Run；原始行和组合入口均校验|独审旧 Run 反例拒绝；当前 Run 与合法 nullable 终态正例保留|\n\n26/26 有限纯 AST 控符合。四个独审误接受输入实际复用；数据库组合控明确使用回调 stub，SQL/产品/SDK 调用为 0。\n\n第一次 AST 抽取遗漏 IDS 依赖，工具9691d9真实 outer/Python1/1、native产品NULL，已封为677一次；旧程序原件保留，无重跑。新 v2控只补依赖，候选 Source 字节未再修改。\n\n55个公开schema定义、SessionEvent与Artifact严格Hash边界不变。四decoder、六selector最终OPEN、实际Rootproducer/原始资格、第五GLOBAL part继续OPEN；源码修订不是正式接受。\n'
with (OUT/'report.md').open('xb') as f:f.write(md.encode('utf-8'))
audit_ref=write('audit.json',{'schema':'researchos.a04-json-identity-source-audit.v1','author_id':ACTOR,'source_pins':sources,'inverse_ref':pin(OUT/'source.inverse.actual.json'),'controls_ref':pin(OUT/'source-controls.actual.v2.json'),'construction_ref':pin(OUT/'construction.actual.json'),'whole_package_source_only':True,'scope_widening':False,'new_failure_origin_ref':failure,'new_failure_count':1,'SQL_native_product_calls':0,'canonical_writes':0})
members=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ('manifest.json','handoff.json','postseal-original-tool-io.json')]
mf_ref=write('manifest.json',{'schema':'researchos.a04-json-identity-source-manifest.v1','author_id':ACTOR,'status':'IMMUTABLE_SOURCE_PROPOSAL_WITH_OPEN','member_count':len(members),'members':members,'self_included':False,'handoff_external':True,'postseal_original_io_external':True})
hdf_ref=write('handoff.json',{'schema':'researchos.a04-json-identity-source-handoff.v1','author_id':ACTOR,'status':'STOPPED','decision':report['decision'],'source_pins':sources,'report_ref':report_ref,'audit_ref':audit_ref,'manifest_ref':mf_ref,'basis_independent_review_ref':pin(PEER/'review.json'),'basis_review_handoff_ref':pin(PEER/'handoff.json'),'basis_source_handoff_ref':pin(BASE/'handoff.json'),'basis_source_manifest_ref':pin(BASE/'manifest.json'),'contract_proposal_ref':contract_ref,'inverse_ref':pin(OUT/'source.inverse.actual.json'),'controls_ref':pin(OUT/'source-controls.actual.v2.json'),'original_tool_io_ref':pin(OUT/'original-tool-io.json'),'requested_author_fix_ids':['A04-BIND-R01','A04-BIND-R02'],'independent_review_ref':None,'required_next_actor':'Root-selected command_queue_impl independent reviewer','remaining_open_requirements':old_hdf['remaining_open_requirements'],'current_selectors_can_qualify':False,'main_adopted':False,'actual_root_authority':None,'SQL_Go_CLI_SDK_model_product_native_calls':0,'canonical_writes':0,'source_acceptance':False,'formal_case_accepted_delta':0,'new_tool_failure_origin_refs':[failure],'new_tool_failure_count':1,'root_assigned_new_origin':677,'old_674_recounted':False,'postseal_original_io_annex':'postseal-original-tool-io.json external to MF; no hash cycle.'})
for ref in members:assert pin(Path(ref['path']))==ref
print(json.dumps({'handoff_ref':hdf_ref,'manifest_ref':mf_ref,'report_ref':report_ref,'audit_ref':audit_ref,'members':len(members),'decision':report['decision'],'new_failure_count':1,'root_assigned_origin':677},ensure_ascii=False))

