from pathlib import Path
import ast, hashlib, json, traceback, types

R = Path(r'D:/作品集/ResearchOS/research-os')
W = R/'execution/v2.4/receipts/W09/W09-99'
D = Path(__file__).resolve().parent
N = W/'w09_br8_formal_actual_review_codex/prepare-20261010-01'
S = W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
support = W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
raw_support = support.read_bytes()
assert len(raw_support) == 4940 and hashlib.sha256(raw_support).hexdigest() == '567f53cadfab3781d6345ed1c6b04b52b85135e0843ce3c217e2f7fadf2a021a'
s = types.ModuleType('independent_frev_support');s.__file__ = str(support)
exec(compile(raw_support,str(support),'exec'),s.__dict__);s.D = D
anchors = [
 s.exact_ref(N/'HDF.json','22a978505d86734e16d73ef58e7ca59550553e1a1983beed6637b0e7cf1d947b',17135),
 s.exact_ref(N/'MF.json','3d374ceb266b91bac6c4c02adb870b44d56c23aa01aa5ac7c57fd46fde9984cc',5957),
 s.exact_ref(N/'preparation-decision.json','0a2743828ade588288503ac6a398570b8b5307c3a144a59ff50cd5c8d1d741f5',6293),
 s.exact_ref(N/'br8_actual_review.source.py','08db9f87cd186f14713e74f853dff88a169bb979fa566db5c1e661c134f700c6',19407),
 s.exact_ref(N/'input-contract.json','f332836db8cfd6cf19e7b6b427cc059843e652820b74d95519085ff9f9811ecb',22062),
 s.exact_ref(N/'basis.json','37b0e5a10895881f721ca8867094f915a9b8786ac2334d4599b18961b5d4827e',31811),
 s.exact_ref(S/'w09.br8-formal-review-source04.actual-audit.root.json','b7db5cdf223eb61a9b2402071ab940674005d1a0e260be673b4fd2234d34503c',1121),
]
for ref in anchors: assert s.pin(ref['path']) == ref
mf = json.loads((N/'MF.json').read_bytes()); hdf = json.loads((N/'HDF.json').read_bytes())
decision = json.loads((N/'preparation-decision.json').read_bytes())
author_audit = json.loads(Path(anchors[6]['path']).read_bytes())
base_refs = [decision[k] for k in ('base_source_ref','base_hdf_ref','base_mf_ref')]
contract = json.loads((N/'input-contract.json').read_bytes())
base_refs.extend([contract['input_self_reference_revision']['base_contract_ref'],contract['input_self_reference_revision']['base_basis_ref']])
refs = anchors+mf['members']+hdf['source_inputs']+base_refs+[author_audit['original_capture_ref'],s.pin(Path(__file__)),s.pin(support)]
refs = list({x['path']:x for x in refs}.values())
g = s.guard(); checks = []; evidence = {}; failure = None
def check(name, predicate, detail=None):
 checks.append({'name':name,'passed':bool(predicate),'detail':detail})
def tree(raw): return ast.parse(raw)
def dump(node): return ast.dump(node,include_attributes=False)
try:
 g.acquire(refs)
 def get(ref): return g.get_buffer(ref['path'])
 before = get(base_refs[0]); after = get(anchors[3]); inv = json.loads(g.get_buffer(str(N/'exact-inverse.json')))
 restored = after
 spans = inv['byte_span_replacements']
 for span in reversed(spans):
  a,b = bytes.fromhex(span['old_hex']),bytes.fromhex(span['new_hex'])
  assert restored.count(b) == 1
  restored = restored.replace(b,a,1)
 check('exact_three_byte_span_inverse_restores_published_v3_source',len(spans)==3 and restored==before and hashlib.sha256(restored).hexdigest()==base_refs[0]['sha256'])
 old_tree,new_tree = tree(before),tree(after)
 old_funcs={n.name:n for n in old_tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 new_funcs={n.name:n for n in new_tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 changed=[name for name in old_funcs if dump(old_funcs[name])!=dump(new_funcs[name])]
 check('only_review_actual_AST_changes_all_helpers_constants_schemas_retained',set(old_funcs)==set(new_funcs) and changed==['review_actual'] and [dump(n) for n in old_tree.body if not isinstance(n,(ast.FunctionDef,ast.ClassDef))]==[dump(n) for n in new_tree.body if not isinstance(n,(ast.FunctionDef,ast.ClassDef))],changed)
 # Exclude only the independently pinned input bundle from its own body.
 # This proves the hash-dependency graph is no longer cyclic; no actual
 # bundle or future formal result is manufactured or passed to the caller.
 old_node,new_node=old_funcs['review_actual'],new_funcs['review_actual']
 def assigned(node,name):
  return [n for n in ast.walk(node) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)]
 old_required,new_required=assigned(old_node,'required')[0].value,assigned(new_node,'required')[0].value
 check('required_set_removes_only_input_self_ref_every_publication_requirement_retained',isinstance(old_required,ast.List) and isinstance(new_required,ast.List) and isinstance(old_required.elts[0],ast.Name) and old_required.elts[0].id=='input_ref' and [dump(x) for x in old_required.elts[1:]]==[dump(x) for x in new_required.elts])
 text=after.decode('utf-8')
 check('canonical_input_identity_is_rejected_before_exact_external_ref_is_authorized',"input_key = guard_module._canonical(absolute_ref(input_ref)['path'])" in text and text.index("need(input_key not in authorized, 'BUNDLE_RESOURCE_SELF_REFERENCE')")<text.index('authorized[input_key] = input_ref') and "need(len(authorized) == len(resources), 'RESOURCE_DUPLICATE_PATH')" in text)
 old_acq=[n for n in ast.walk(old_node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='guard' and n.func.attr=='acquire']
 new_acq=[n for n in ast.walk(new_node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='guard' and n.func.attr=='acquire']
 expected=ast.parse('guard.acquire([input_ref, *resources])').body[0].value
 check('guard_holds_external_exact_input_plus_every_original_resource',len(old_acq)==len(new_acq)==1 and dump(new_acq[0])==dump(expected) and dump(old_acq[0].args[0])==dump(ast.Name(id='resources',ctx=ast.Load())))
 check('input_pin_checked_before_parsing_and_guard_rechecks_original_bytes',"observed_input = pin(input_ref['path'])" in text and "need(observed_input['sha256'] == input_ref['sha256'] and observed_input['bytes'] == input_ref['bytes'], 'INPUT_PIN')" in text and "shape_ref(input_ref, ('path', 'sha256', 'bytes'))" in text and text.index("need(observed_input['sha256']")<text.index('bundle = validate_bundle'))
 original_contract=json.loads(get(base_refs[3])); original_basis=get(base_refs[4])
 check('basis_bytes_and_entire_input_schema_role_time_global_modes_contract_unchanged',original_basis==get(anchors[5]) and all(contract[k]==original_contract[k] for k in ('input_schema','input_fields','context_reference_fields','metadata_reference_fields','Root_publication_fields','Root_publication_binding','current4_order','current4_rule','routes','consumer_result_schema','consumer_checks','GLOBAL','review_schema','verdict_ids','verdict_rule','time_order','phase_one_rule','phase_two_rule','Main_original_provenance','future_capture_index','future_Root_issuance_ref','future_owner_acceptance_ref')))
 preparation=json.loads(g.get_buffer(str(N/'Source-preparation.json')))
 check('reuse_author_four_prefix_two_tail_without_replaying_controls_or_actual_review',preparation['total_distinct_passed_controls']==6 and len(preparation['prior_successful_control_prefix'])==4 and all(x['passed'] is True for x in preparation['prior_successful_control_prefix']) and len(preparation['tail_checks'])==2 and all(x['passed'] is True for x in preparation['tail_checks']) and preparation['prior_prefix_not_replayed'] is True and preparation['actual_formal_review_called'] is False and preparation['Root_stages_Native_Go_SQL_model_TP_dispatcher_calls']==0)
 prior_guard_refs=hdf['guard_refs']
 for ref in prior_guard_refs:
  c=json.loads(get(ref));assert c['verification']=='PASSED' and c['closed'] is True and c['retained_handles_count']==0 and c['failure'] is None and c['errors']==[]
  assert all(x['verified'] is True and x['closed'] is True for x in c['entries'])
 check('preserved_failure1235_true_IO_and_all_author_guards_closed',len(prior_guard_refs)==3 and preparation['failed_original_control_retained']['passed'] is False and hdf['original1235_actual_binding_ref'] in refs and hdf['original1235_actual_raw_ref'] in refs)
 audit=json.loads(get(anchors[6])); raw_capture=get(audit['original_capture_ref']); lines=raw_capture.splitlines(keepends=True)
 assert len(lines)==3
 rows=[json.loads(line) for line in lines]
 assert [hashlib.sha256(line).hexdigest() for line in lines]==audit['original_line_sha256']
 offsets=audit['source_line_offsets']
 assert len(offsets)==3 and all(type(x)is int and x>=0 for x in offsets)
 with Path(audit['source_audit_path']).open('rb') as source_stream:
  for offset,line in zip(offsets,lines):
   source_stream.seek(offset);assert source_stream.read(len(line))==line
 msg=rows[2]['payload']; body=msg['content'][0]['text']
 prefix='Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/backup_regression_resources\nPayload:\n'
 assert body.startswith(prefix)
 delivered=json.loads(body[len(prefix):])
 for key,ref in zip(('hdf_ref','mf_ref','decision_ref','caller_ref','input_contract_ref','basis_ref'),anchors[:6]):
  actual=delivered[key]
  assert Path(actual['path']).resolve(strict=True)==Path(ref['path']).resolve(strict=True) and actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes']
 check('real_Backup_author_Final_header_adjacent_metadata_offsets_bytes_and_six_pins',rows[0]['type']=='session_meta' and rows[0]['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98' and rows[1]['type']=='inter_agent_communication_metadata' and rows[2]['type']=='response_item' and msg['type']=='agent_message' and msg['author']=='/root/backup_regression_resources' and msg['recipient']=='/root' and rows[2]['metadata']['client_authored'] is False and rows[1]['ordinal']+1==rows[2]['ordinal'] and offsets[1]+len(lines[1])==offsets[2] and rows[1]['timestamp']==rows[2]['timestamp'] and audit['binding_sha256']==anchors[0]['sha256'],{'actor':msg['author'],'recipient':msg['recipient'],'timestamp':rows[2]['timestamp'],'offsets':offsets,'ordinals':[rows[1]['ordinal'],rows[2]['ordinal']],'client_authored':False,'capture_ref':audit['original_capture_ref']})
 check('future_actual_root_issuance_and_formal_acceptance_remain_unissued',contract['future_capture_index'] is None and contract['future_Root_issuance_ref'] is None and contract['future_owner_acceptance_ref'] is None and hdf['future_actual_review_called'] is False and hdf['formal_acceptance'] is False and hdf['execution_grant'] is False and preparation['Source_self_acceptance'] is False)
 evidence={'source_refs':anchors[:6],'author_audit_ref':anchors[6],'author_original_capture_ref':audit['original_capture_ref'],'base_source_ref':base_refs[0],'base_hdf_ref':base_refs[1],'base_mf_ref':base_refs[2],'base_contract_ref':base_refs[3],'base_basis_ref':base_refs[4],'guard_held_refs':refs,'changed_AST_functions':changed,'byte_spans':spans,'complete_byte_inverse':True,'source_hash_dependency':'External pin(input bundle) plus resource_refs excluding input canonical path; Guard independently holds exact input_ref. This is Source proof only, not a manufactured actual bundle.','prior_guard_refs':prior_guard_refs,'original1235_binding_ref':hdf['original1235_actual_binding_ref'],'original1235_raw_ref':hdf['original1235_actual_raw_ref'],'actual_formal_review_called':False,'author_controls_replayed':False,'formal_acceptance':False,'execution_grant':False}
except BaseException:
 failure=traceback.format_exc();raise
finally:
 closed=g.close();guard_ref=s.write('source-review-guard.closed.json',closed)
 result_ref=s.write('independent-delta-checks.json',{'schema':'researchos.w09-formal-review-independent-source-delta-checks.v1','checks':checks,'count':len(checks),'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'failure':failure,'evidence':evidence,'guard_ref':guard_ref,'actual_formal_review_called':False,'author_controls_replayed':False,'product_calls':0,'formal_acceptance':False,'execution_grant':False})
assert closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
print(json.dumps({'result_ref':result_ref,'guard_ref':guard_ref,'count':len(checks),'passed':sum(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']],'retained_handles_count':0,'product_calls':0},ensure_ascii=False))
