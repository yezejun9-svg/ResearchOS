from pathlib import Path
import ast, copy, hashlib, json, re

OWN=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_controller_v3_independent_source_review_codex/3b5ae723087647b6a884329c2ff8518c')
PACK=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_execution_revision_preparation_codex/fb328e152ae54da6b4be24cbc3b94ece')
def pin(p):
    p=Path(p);b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def verify(r):
    actual=pin(r['path'])
    assert (actual['sha256'],actual['bytes'])==(r['sha256'],r['bytes']),r['path']
    return Path(r['path']).read_bytes()
def write(name,data):
    p=OWN/name
    assert p.resolve().is_relative_to(OWN.resolve()) and not p.exists()
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def doc(r):return json.loads(verify(r))
def fn(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
def shape(node):return ast.dump(node,include_attributes=False)
def is_name(n,name):return isinstance(n,ast.Name) and n.id==name
def expr(text):return ast.parse(text).body[0].value
def is_call(n,text):return isinstance(n,ast.Call) and shape(n.func)==shape(expr(text))

records=json.loads((OWN/'inputs.before.json').read_bytes())
assert len(records)==63
for record in records:verify(record['source']);verify(record['copy'])
h=doc({'path':str(PACK/'handoff.json'),'sha256':'50b4b2c014a7eb164ec191fad904150b38426883b9544c28d086a1f19150cba6','bytes':4601})
mf=doc({'path':str(PACK/'manifest.json'),'sha256':'d402403edebb77ffea3871a35f6b01da15ebd6584e9c5a398e38dd7b4da1b6b1','bytes':4585})
assert len(mf['files'])==mf['count']==14
for row in mf['files']:verify(row)
s=doc(h['scope_ref']);fixed=doc(s['fixed_inputs_ref'])
priorh=doc(h['original_review_handoff_ref'])
prior=doc(priorh['inputs_before_ref'])
assert prior==doc(priorh['inputs_after_ref']) and len(prior)==30
for row in prior:verify(row)
original=verify(h['original_v2_controller_ref'])
candidate=verify(h['controller_ref'])
transform=doc(h['inverse_ref'])
before=transform['before'].encode('utf8');after=transform['after'].encode('utf8')
assert original.count(before)==1 and candidate.count(after)==1
assert original.replace(before,after)==candidate and candidate.replace(after,before)==original
assert hashlib.sha256(original).hexdigest()==transform['inverse_sha256']
assert len(re.findall(rb'^@@ ',verify(h['diff_ref']),re.M))==1
a2=ast.parse(original);a3=ast.parse(candidate);m=fn(a3,'main')
tail=m.body[-2]
assert isinstance(tail,ast.If) and shape(tail.test)==shape(expr('time.monotonic()>=inner_deadline'))
assert not tail.orelse and len(tail.body)==2
assert is_call(tail.body[0].value,'sys.stderr.write')
payload=tail.body[0].value.args[0].left.args[0]
fields={k.value:v for k,v in zip(payload.keys,payload.values)}
assert ast.literal_eval(fields['stage'])=='FINAL_RETURN' and ast.literal_eval(fields['error'])=='INNER_DEADLINE_EXPIRED'
assert is_name(fields['first_cause'],'first') and ast.literal_eval(fields['actual_native_exit']) is None
assert ast.literal_eval(fields['outer_raw_authority']) is True
assert isinstance(tail.body[1],ast.Return) and ast.literal_eval(tail.body[1].value)==1
rest=copy.deepcopy(a3);fn(rest,'main').body.pop(-2);assert shape(rest)==shape(a2)
other_defs=[n.name for n in a3.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name!='main']
assert len(other_defs)==11
entry=a3.body[-1]
assert isinstance(entry,ast.If) and isinstance(entry.body[0],ast.Try)
assert is_call(entry.body[-1].value,'sys.exit')
assert not any(is_call(n,'sys.exit') for n in ast.walk(entry.body[0]))
assert is_name(entry.body[-1].value.args[0],'exit_code')
expected={'native_calls':32,'compiler_seconds':600,'test_seconds':750,'inner_seconds':3300,'outer_seconds':3600,'cleanup_seconds':5,'images':64,'compiler_processes':2048,'job_active_processes':16,'fixture_HTTP':0,'SDK_Node_model_external_paid':0}
caps=ast.literal_eval(next(n.value for n in a3.body if isinstance(n,ast.Assign) and any(is_name(t,'CAPS') for t in n.targets)))
assert caps==s['caps']==expected
run=next(n for n in ast.walk(m) if isinstance(n,ast.FunctionDef) and n.name=='run')
effective=next(n.value for n in ast.walk(run) if isinstance(n,ast.Assign) and any(is_name(t,'effective_seconds') for t in n.targets))
assert shape(effective)==shape(expr("min(seconds,remaining_seconds-CAPS['cleanup_seconds'])"))
remaining=next(n.value for n in ast.walk(run) if isinstance(n,ast.Assign) and any(is_name(t,'remaining_seconds') for t in n.targets))
assert shape(remaining)==shape(expr("inner_deadline-time.monotonic()"))
request=next(n for n in ast.walk(run) if isinstance(n,ast.Dict) and any(isinstance(k,ast.Constant) and k.value=='effective_timeout' for k in n.keys))
fields_req={k.value:v for k,v in zip(request.keys,request.values)}
for key in ['timeout','effective_timeout']:assert is_name(fields_req[key],'effective_seconds')
assert is_name(fields_req['requested_timeout'],'seconds') and is_name(fields_req['remaining_inner_seconds'],'remaining_seconds')
call=next(n for n in ast.walk(run) if is_call(n,'debug.run_owned'))
assert is_name(call.args[5],'effective_seconds') and ast.literal_eval(call.args[-1])==2048
assert any(is_call(n,'need') and any(isinstance(arg,ast.Constant) and arg.value=='FINITE_DEADLINE_OR_CALLCAP' for arg in n.args) for n in ast.walk(run))
returns=[]
def walk_outer(n):
    if isinstance(n,(ast.FunctionDef,ast.ClassDef,ast.Lambda)):return
    if isinstance(n,ast.Return):returns.append(n)
    for c in ast.iter_child_nodes(n):walk_outer(c)
for statement in m.body:walk_outer(statement)
assert len(returns)==2 and returns[0] is tail.body[1] and returns[1] is m.body[-1]
bodytry=next(n for n in m.body if isinstance(n,ast.Try))
assert bodytry.finalbody[-1].end_lineno<tail.lineno
saves=[n for n in ast.walk(bodytry.finalbody[-1]) if is_call(n,'save')]
assert saves and max(n.end_lineno for n in saves)<tail.lineno
assert any(isinstance(hh.type,ast.Name) and hh.type.id=='PreparedComplete' for hh in bodytry.handlers)

a1=ast.parse(verify(next(r for r in prior if Path(r['path']).name=='driver18_controller.proposed.py')))
def branches(main):
    return [n for n in ast.walk(main) if isinstance(n,ast.If) and shape(n.test)==shape(expr("ident=='I16'"))]
assert len(branches(m))==2 and [shape(n) for n in branches(m)]==[shape(n) for n in branches(fn(a1,'main'))]
go=verify(fixed['test_source_ref'])
assert fixed['test_source_ref']['sha256']=='5df920564f6213954e9202895a69001f42debb056ac264b652e0afe743171e50' and len(go)==17372
# Actual pinned body lines296..300 contain two line comments plus one original call.
i18=re.search(rb'func TestDriverI18\(t \*testing.T\)\s*\{(?P<body>[\s\S]*?)\}',go)
assert i18 is not None
actual_body=i18.group('body')
without_line_comments=re.sub(rb'^\s*//[^\n]*$',b'',actual_body,flags=re.M).strip()
assert without_line_comments==b'TestRegisteredFunctions(t)'
assert b'I17 FATAL_OPEN' in go and b'driver18F08Bindings' in go and b'driver18F08Vectors' in go
regression=verify(fixed['original_regression_ref'])
assert len(regression)==35317 and hashlib.sha256(regression).hexdigest()=='85e63e33c8d22d89e426dd33dff7bfece1f472b4796cd067718d9a6d22fb4e54'
launcher=verify(h['launcher_ref'])
assert len(launcher)==4996 and hashlib.sha256(launcher).hexdigest()=='fbf9c52568678e3733a0e50300a53c2044be96afee85672d3d2bf4df78af9086'
outer=next(n for n in ast.walk(ast.parse(launcher)) if is_call(n,'helper.run_owned'))
assert ast.literal_eval(outer.args[5])==3600
oldscope=doc(next(r for r in prior if Path(r['path']).name=='scope.UNBOUND.v2.proposed.json'))
copy_scope=copy.deepcopy(s);copy_scope['controller_ref']=oldscope['controller_ref'];assert copy_scope==oldscope
null_keys=['actual_Root_registration','actual_origin_cut','actual_non_author_controller_review_ref','authority_validator_ref','resource_catalog_ref','prepared_ref','mode','ordered_cases','public_environment','work_root','prepare_output_root','execute_output_root','prepare_launcher_output_root','execute_launcher_output_root']
assert all(s[k] is None for k in null_keys) and s['preparation_only'] is True and s['source_acceptance'] is False

audit={
 'schema':'researchos.driver18.v3.independent-static-audit.v2','verdict':'READY_SOURCE_PREPARATION_ONLY',
 'source_manifest_members':14,'source_members_plus_manifest':15,'selected_actual_frozen_ref_count':len(records),
 'prior30_references_rehashed':30,'author10_metadata_equal':True,'source_drift':0,
 'exact_replacement_count':1,'physical_diff_hunks':1,'whole_forward_inverse_byte_exact':True,
 'removed_only_tail_guard_entire_v2_AST_equal':True,'all_other11_defs_AST_equal':other_defs,
 'post_all_result_manifest_IO_guard_lines':[tail.lineno,tail.end_lineno],
 'outer_main_all_return_paths':[n.lineno for n in returns],
 'prepared_complete_and_all_try_error_finalization_paths_share_postIO_guard':True,
 'tail_preserves_first_cause_actual_native_NULL_and_outer_raw_authority':True,
 'already_written_qualified_or_result_artifacts_not_rewritten':True,
 'entry_sys_exit_outside_catch':True,'effective_timeout_same_in_request_and_actual_debug_helper':True,'caps':caps,
 'partial17_native_calls_expected':30,'I16_v1_v2_v3_two_branches_byteAST_behavior_unchanged':True,
 'I18_actual_original_body_with_comments_kept':True,'I18_only_statement':'TestRegisteredFunctions(t)',
 'I18_original_regression_SHA35317B_preserved':fixed['original_regression_ref'],
 'I17_and_all18_complete_not_authorized':True,'launcher_full_bytes_unchanged':True,
 'scope_only_controller_ref_changed':True,'null_authority_resource_prepared_fields':null_keys,
 'current_canonical_tuple_used_as_drift_reference':False,
 'actual_target_or_helper_calls':0,'source_AST_parse_only':True,'runtime_tests':'ALL_NOT_RUN',
 'synchronous_IO_interruptibility':'No new IO interrupt; genuine owned outer3600 job still required',
 'reader_acceptance_requirement':'Actual enclosing controller exit and captured raw stderr govern; any FINAL_RETURN rejects despite previously written qualified/result files.',
 'new_review_metadata_failure_count':1,'original_metadata_failure_ref':pin(OWN/'origin.I18-regex-shape.json'),
 'original_failed_input_reexecuted':False,'new_explicit_shape_runs':1,
 'failure_is_reviewer_comment_insensitive_regex_not_product_regression':True,
 'actual_Root_grant_or_source_adoption_or_qualification':False
}
write('static-audit.v2.json',audit)
for r in records:verify(r['source']);verify(r['copy'])
write('inputs.after.json',records)
print(json.dumps({'verdict':audit['verdict'],'frozen_input_refs':len(records),'source14plusmanifest':15,'tail_lines':[tail.lineno,tail.end_lineno],'exact_inverse':True,'whole_AST_other_than_tail_equal':True,'I18_actual_comments_preserved':True,'target_calls':0,'new_origins':1},ensure_ascii=False))

