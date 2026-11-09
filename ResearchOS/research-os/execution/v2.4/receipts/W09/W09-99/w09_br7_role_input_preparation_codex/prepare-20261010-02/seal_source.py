from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[6]
A=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(p):return json.loads(Path(p).read_bytes())
def save(n,v,raw=False):
 with (O/n).open('xb') as f:f.write(v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/n)
inputs=doc(O/'source-inputs.json')
for r in doc(O/'protected-inputs.json'):
 p=pin(r['path']);assert (p['sha256'],p['bytes'])==(r['sha256'],r['bytes'])
assert pin(O/'role_input_builder.source.py')['sha256']=='15425e193fdec56e49048e5788f6d59b6dab8fbb410d071fa083d07ab95046a5'
assert pin(O/'pure-metadata-controls.json')['sha256']=='346a83f4e050642fe31de695a40ef508da899e3d1e508ddc589aee138d505304'
tree=ast.parse(Path(inputs['Main_ref']['path']).read_bytes())
f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_role_audit')
required=next(ast.literal_eval(n.args[1]) for n in ast.walk(f) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='fields' and len(n.args)>1 and isinstance(n.args[0],ast.Name) and n.args[0].id=='audit')
bt=ast.parse((O/'role_input_builder.source.py').read_bytes());bf=next(n for n in bt.body if isinstance(n,ast.FunctionDef) and n.name=='audit_payload')
returned=next(n.value for n in bf.body if isinstance(n,ast.Return));keys=[k.arg for k in returned.keywords]
assert len(required)==len(keys)==10 and set(required)==set(keys)
schema=save('exact-Main-schema-count.json',dict(Main_ref=inputs['Main_ref'],Main_required_fields=list(required),builder_output_fields=keys,
 exact_count=10,prior_11_wording_corrected=True,actual_control_record_retained_unchanged=True,actual_Main_role_call=False))
prefix=A.stat().st_size;start=max(0,prefix-12*1024*1024);calls={};found=None
with A.open('rb') as f:
 head=f.readline();f.seek(start)
 if start:f.readline()
 while f.tell()<prefix:
  off=f.tell();line=f.readline()
  if not line or f.tell()>prefix:break
  try:j=json.loads(line)
  except ValueError:continue
  p=j.get('payload',{});t=p.get('type')
  if j.get('type')=='response_item' and t in ('function_call','custom_tool_call'):calls[p.get('call_id')]=(off,line,j)
  if j.get('type')=='response_item' and t in ('function_call_output','custom_tool_call_output') and p.get('call_id') in calls and '5f9748' in str(p.get('output','')):
   c=calls[p['call_id']];inp=str(c[2]['payload'].get('input',c[2]['payload'].get('arguments','')))
   if 'prepare_source.py' in inp and '5f9748' not in inp:found=[(0,head,json.loads(head)),c,(off,line,j)];break
assert found is not None
raw=save('actual-source-preparation.raw.jsonl',b''.join(x[1] for x in found),True)
binding=save('actual-source-preparation.binding.json',dict(actual_chunk_id='5f9748',actual_outer_exit=0,actual_python_exit=0,
 actor_id='codex:/root/attach_restore_independent_review',source_audit_path=str(A),source_prefix_size_observed=prefix,
 source_line_offsets=[x[0] for x in found],source_line_bytes=[len(x[1]) for x in found],original_line_sha256=[hashlib.sha256(x[1]).hexdigest() for x in found],
 original_capture_ref=raw,original_call_id=found[1][2]['payload']['call_id'],source_session_id=found[0][2]['payload']['id'],
 builder_run=False,Root_stage_Native_SQL_models_TP_calls=0))
for off,line,_ in found:
 with A.open('rb') as f:f.seek(off);assert f.read(len(line))==line
controls=doc(O/'pure-metadata-controls.json');assert controls['count']==10 and all(x['result']=='PASS' for x in controls['checks'])
closed=doc(O/'SourceGuard.closed.json');assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
caller=pin(O/'role_input_builder.source.py')
contract=save('root-calling-contract.source.json',dict(schema='researchos.w09-role-input-builder-calling-contract.v1',source_ref=caller,
 source_inputs_ref=pin(O/'source-inputs.json'),request_template_ref=pin(O/'builder-request.template.json'),fieldmap_ref=pin(O/'ROOT_FIELD_MAP.md'),
 argv_template=['C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe','-I','-S','-B','-X','utf8',caller['path'],'--request',None,'--sha256',None,'--bytes',None],
 cwd=str(R),request_ref_shape=['path','sha256','bytes'],request_fields=list(doc(O/'builder-request.template.json')),
 Main_role_audit_exact_fields=list(required),Main_role_audit_field_count=10,capture_wrapper_field_count_without_role=9,
 readonly_inputs='exact proposal/context seed + three prior actual Root observation audits + fixed prior peer evidence; no live Canon reads',
 future_write_scopes=['execution/v2.4/receipts/W09/W09-99/w09_br7_role_inputs_root/{preparation_id}/','execution/v2.4/root_original_events/W09/W09-99/roles-{preparation_id}/'],
 immutable_output_only=True,fixed_registry_write=False,Canon_Scope_Main_write=False,Root_stage_calls=0,
 supplemental_refs='Merge role-protection-refs.json.role_protection_refs array directly into future roles request before request hash/grant.',
 context_registry_refs_after_publication_only=True,registered_ref3=None,registry_ref2=None,root_grant_ref=None,
 source_status='SOURCE_ONLY_PENDING_ROOT_REVIEW',actual_builder_run=False,formal_acceptance=False,execution_grant=False))
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ('HDF.json','MF.json','postseal-tool-io.json')]
mf=save('MF.json',dict(schema='researchos.w09-role-input-builder-source-manifest.v1',members=members,exclusions=['HDF.json','MF.json','postseal-tool-io.json']))
h=save('HDF.json',dict(schema='researchos.w09-role-input-builder-source-handoff.v1',actor_id='codex:/root/attach_restore_independent_review',
 status='SOURCE_ONLY_PENDING_ROOT_REVIEW',source_ref=caller,manifest_ref=mf,source_inputs_ref=pin(O/'source-inputs.json'),
 contract_ref=contract,request_template_ref=pin(O/'builder-request.template.json'),fieldmap_ref=pin(O/'ROOT_FIELD_MAP.md'),
 controls_ref=pin(O/'pure-metadata-controls.json'),schema_count_correction_ref=schema,decision_ref=pin(O/'source-decision.json'),
 actual_prepare_raw_ref=raw,actual_prepare_binding_ref=binding,SourceGuard_closed_ref=pin(O/'SourceGuard.closed.json'),
 pure_metadata_controls=10,old_controls_replayed=False,actual_builder_run=False,future_original_copies_created=False,
 Root_stage_Native_SQL_models_TP_calls=0,Main_Canon_Scope_fixed_registry_writes=0,formal_acceptance=False,execution_grant=False,self_acceptance=False,STOP=True))
assert all(pin(r['path'])==r for r in members)
print(json.dumps(dict(HDF_ref=h,MF_ref=mf,source_ref=caller,contract_ref=contract,request_template_ref=pin(O/'builder-request.template.json'),
 Main_role_audit_fields=10,pure_metadata_controls=10,SourceGuard_closed_zero=True),ensure_ascii=False))
