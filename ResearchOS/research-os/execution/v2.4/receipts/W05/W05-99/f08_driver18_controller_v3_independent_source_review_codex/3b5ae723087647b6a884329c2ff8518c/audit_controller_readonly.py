from pathlib import Path
import ast, copy, hashlib, json, re

OWN=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_controller_v3_independent_source_review_codex/3b5ae723087647b6a884329c2ff8518c')
PACK=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_execution_revision_preparation_codex/fb328e152ae54da6b4be24cbc3b94ece')
def ref(p):
    p=Path(p);b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def require(row):
    p=Path(row['path']);actual=ref(p)
    assert actual['sha256']==row['sha256'] and actual['bytes']==row['bytes'], ('drift',str(p))
    return p
def emit(name,obj):
    p=OWN/name
    assert p.resolve().is_relative_to(OWN.resolve()) and not p.exists()
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    return ref(p)
def load(row):return json.loads(require(row).read_bytes())
def dump(node):return ast.dump(node,include_attributes=False)
def function(tree,name):
    return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
def nameis(node,name):return isinstance(node,ast.Name) and node.id==name
def iscall(node,owner,name):
    return isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and nameis(node.func.value,owner) and node.func.attr==name

h=load({'path':str(PACK/'handoff.json'),'sha256':'50b4b2c014a7eb164ec191fad904150b38426883b9544c28d086a1f19150cba6','bytes':4601})
mf=load({'path':str(PACK/'manifest.json'),'sha256':'d402403edebb77ffea3871a35f6b01da15ebd6584e9c5a398e38dd7b4da1b6b1','bytes':4585})
assert mf['count']==len(mf['files'])==14 and mf['excluded_only_self']
rows={}
def add(row):
    require(row);key=str(Path(row['path']).resolve()).casefold()
    if key in rows:
        assert rows[key]['sha256']==row['sha256'] and rows[key]['bytes']==row['bytes']
    else:rows[key]=row
for row in mf['files']:add(row)
add(ref(PACK/'manifest.json'))
for v in h.values():
    if isinstance(v,dict) and set(v)=={'path','sha256','bytes'}:add(v)
s=load(h['scope_ref'])
for v in s.values():
    if isinstance(v,dict) and set(v)=={'path','sha256','bytes'}:add(v)
priorh=load(h['original_review_handoff_ref'])
prior30=load(priorh['inputs_before_ref'])
assert len(prior30)==30 and prior30==load(priorh['inputs_after_ref'])
for row in prior30:add(row)
add(priorh['inputs_before_ref']);add(priorh['inputs_after_ref'])
author10=json.loads((PACK/'inputs.before.json').read_bytes())
assert len(author10)==10 and author10==json.loads((PACK/'inputs.after.json').read_bytes())
for row in author10:add(row)
fixed=load(s['fixed_inputs_ref'])
fixedrows=[v for v in fixed.values() if isinstance(v,dict) and set(v)=={'path','sha256','bytes'}]
for row in fixedrows:add(row)

snapshots=[]
for index,row in enumerate(rows.values()):
    source=require(row);dst=OWN/'snapshots'/f'{index:03d}-{source.name}'
    dst.parent.mkdir(parents=True,exist_ok=True)
    assert not dst.exists();dst.write_bytes(source.read_bytes())
    cp=ref(dst);assert cp['sha256']==row['sha256'] and cp['bytes']==row['bytes']
    snapshots.append({'source':row,'copy':cp})
emit('inputs.before.json',snapshots)

before=require(h['original_v2_controller_ref']).read_bytes()
after=require(h['controller_ref']).read_bytes()
transform=load(h['inverse_ref'])
old=transform['before'].encode('utf8');new=transform['after'].encode('utf8')
assert before.count(old)==1 and after.count(new)==1
assert before.replace(old,new)==after
assert after.replace(new,old)==before
assert hashlib.sha256(before).hexdigest()==transform['inverse_sha256']
assert transform['exact_replacements']==1
assert len(re.findall(rb'^@@ ',require(h['diff_ref']).read_bytes(),re.M))==1
v2=ast.parse(before);v3=ast.parse(after)
m2=function(v2,'main');m3=function(v3,'main')
tail=m3.body[-2]
assert isinstance(tail,ast.If) and iscall(tail.test.left,'time','monotonic')
assert isinstance(tail.test,ast.Compare) and isinstance(tail.test.ops[0],ast.GtE) and nameis(tail.test.comparators[0],'inner_deadline')
assert not tail.orelse and len(tail.body)==2
assert isinstance(tail.body[0],ast.Expr) and iscall(tail.body[0].value,'sys.stderr','write') is False
writecall=tail.body[0].value
assert isinstance(writecall,ast.Call) and dump(writecall.func)==dump(ast.parse('sys.stderr.write').body[0].value)
payload=writecall.args[0].left.args[0]
assert isinstance(payload,ast.Dict)
tail_fields={k.value:v for k,v in zip(payload.keys,payload.values)}
assert ast.literal_eval(tail_fields['stage'])=='FINAL_RETURN'
assert ast.literal_eval(tail_fields['error'])=='INNER_DEADLINE_EXPIRED'
assert nameis(tail_fields['first_cause'],'first') and ast.literal_eval(tail_fields['actual_native_exit']) is None
assert ast.literal_eval(tail_fields['outer_raw_authority']) is True
assert isinstance(tail.body[1],ast.Return) and ast.literal_eval(tail.body[1].value)==1
clone=copy.deepcopy(v3)
function(clone,'main').body.pop(-2)
assert dump(clone)==dump(v2)
unchanged=[n.name for n in v3.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name!='main']
for n in v3.body:
    if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name!='main':
        assert dump(n)==dump(next(q for q in v2.body if type(q)==type(n) and q.name==n.name))

entry=v3.body[-1]
assert isinstance(entry,ast.If) and isinstance(entry.body[0],ast.Try)
assert isinstance(entry.body[-1],ast.Expr) and iscall(entry.body[-1].value,'sys','exit')
assert not any(iscall(n,'sys','exit') for n in ast.walk(entry.body[0]))
assert nameis(entry.body[-1].value.args[0],'exit_code')

caps=ast.literal_eval(next(n.value for n in v3.body if isinstance(n,ast.Assign) and any(nameis(t,'CAPS') for t in n.targets)))
expected={'native_calls':32,'compiler_seconds':600,'test_seconds':750,'inner_seconds':3300,'outer_seconds':3600,'cleanup_seconds':5,'images':64,'compiler_processes':2048,'job_active_processes':16,'fixture_HTTP':0,'SDK_Node_model_external_paid':0}
assert caps==expected==s['caps']
run=next(n for n in ast.walk(m3) if isinstance(n,ast.FunctionDef) and n.name=='run')
effective=next(n for n in ast.walk(run) if isinstance(n,ast.Assign) and any(nameis(t,'effective_seconds') for t in n.targets))
assert dump(effective.value)==dump(ast.parse("min(seconds,remaining_seconds-CAPS['cleanup_seconds'])").body[0].value)
requested=next(n for n in ast.walk(run) if isinstance(n,ast.Dict) and any(isinstance(k,ast.Constant) and k.value=='effective_timeout' for k in n.keys))
requested_fields={k.value:v for k,v in zip(requested.keys,requested.values)}
assert nameis(requested_fields['timeout'],'effective_seconds') and nameis(requested_fields['effective_timeout'],'effective_seconds')
assert nameis(requested_fields['requested_timeout'],'seconds') and nameis(requested_fields['remaining_inner_seconds'],'remaining_seconds')
actual=next(n for n in ast.walk(run) if iscall(n,'debug','run_owned'))
assert nameis(actual.args[5],'effective_seconds') and ast.literal_eval(actual.args[-1])==2048
return_nodes=[]
def outer_walk(node):
    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.Lambda,ast.ClassDef)):return
    if isinstance(node,ast.Return):return_nodes.append(node)
    for child in ast.iter_child_nodes(node):outer_walk(child)
for statement in m3.body:outer_walk(statement)
assert len(return_nodes)==2 and return_nodes[0] is tail.body[1] and return_nodes[1] is m3.body[-1]
final_try=next(n for n in m3.body if isinstance(n,ast.Try))
assert final_try.finalbody[-1].end_lineno<tail.lineno
final_saves=[n for n in ast.walk(final_try.finalbody[-1]) if isinstance(n,ast.Call) and nameis(n.func,'save')]
assert max(n.end_lineno for n in final_saves)<tail.lineno

v1row=next(r for r in prior30 if Path(r['path']).name=='driver18_controller.proposed.py')
v1=ast.parse(require(v1row).read_bytes());m1=function(v1,'main')
def i16branches(main):
    return [n for n in ast.walk(main) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and nameis(n.test.left,'ident') and any(isinstance(c,ast.Constant) and c.value=='I16' for c in n.test.comparators)]
assert [dump(n) for n in i16branches(m1)]==[dump(n) for n in i16branches(m3)]
assert len(i16branches(m3))==2
go=require(fixed['test_source_ref']).read_bytes()
assert re.search(rb'func TestDriverI18\(t \*testing.T\)\s*\{\s*TestRegisteredFunctions\(t\)\s*\}',go)
assert b'I17 FATAL_OPEN' in go and b'driver18F08Bindings' in go and b'driver18F08Vectors' in go
assert fixed['test_source_ref']['sha256']=='5df920564f6213954e9202895a69001f42debb056ac264b652e0afe743171e50'
assert fixed['original_regression_ref']['sha256']=='85e63e33c8d22d89e426dd33dff7bfece1f472b4796cd067718d9a6d22fb4e54'
assert fixed['original_regression_ref']['bytes']==35317
launch=require(h['launcher_ref']).read_bytes()
assert hashlib.sha256(launch).hexdigest()=='fbf9c52568678e3733a0e50300a53c2044be96afee85672d3d2bf4df78af9086' and len(launch)==4996
la=ast.parse(launch)
outer_owned=next(n for n in ast.walk(la) if iscall(n,'helper','run_owned'))
assert ast.literal_eval(outer_owned.args[5])==3600
v2scope=json.loads(require(next(r for r in prior30 if Path(r['path']).name=='scope.UNBOUND.v2.proposed.json')).read_bytes())
sc=copy.deepcopy(s);sc['controller_ref']=v2scope['controller_ref'];assert sc==v2scope
nulls=[k for k in ('actual_Root_registration','actual_origin_cut','actual_non_author_controller_review_ref','authority_validator_ref','resource_catalog_ref','prepared_ref','mode','ordered_cases','public_environment','work_root','prepare_output_root','execute_output_root','prepare_launcher_output_root','execute_launcher_output_root') if s[k] is None]
assert len(nulls)==14 and s['preparation_only'] is True and s['source_acceptance'] is False
audit={
 'schema':'researchos.driver18.v3.independent-static-audit.v1',
 'verdict':'READY_SOURCE_PREPARATION_ONLY',
 'author_manifest_members':14,'author_manifest_plus_members_actual_hashed':15,'all_selected_unique_ref_count':len(snapshots),
 'author_original_inputs_count':10,'prior_review_30_refs_actual_rehashed':30,'actual_source_drift':0,
 'exact_byte_replacements':1,'physical_diff_hunks':1,'whole_forward_inverse_exact':True,
 'only_tail_guard_removed_restores_entire_v2_AST':True,'all_other_definitions_AST_equal':unchanged,
 'tail_guard_lines':[tail.lineno,tail.end_lineno],'all_finally_result_manifest_IO_before_guard':True,
 'all_main_returns_guarded_or_fail':True,'prepare_execute_and_error_finalization_paths_share_postIO_guard':True,
 'tail_stderr_preserves_first_cause_nativeNULL_and_outer_actual_authority':True,'sealed_written_artifacts_rewritten':False,
 'entry_sys_exit_outside_catch':True,'effective_timeout_same_in_request_and_actual_helper':True,
 'caps':caps,'partial17_native_calls_expected':30,'I16_branches_v1_v2_v3_AST_unchanged':2,
 'I18_original_35317B_source_pin_preserved':True,'TestDriverI18_calls_original_TestRegisteredFunctions':True,
 'I17_FATAL_OPEN_unchanged':True,'launcher_exact_original_bytes':True,'scope_only_controller_ref_changed':True,
 'all14_execution_authority_resource_output_fields_NULL':nulls,
 'current_canonical_tuple_used_as_drift_reference':False,
 'candidate_helper_Go_SQL_driver_HTTP_SDK_model_target_calls':0,'Python_AST_parser_only_not_module_imported':True,
 'actual_runtime_3300_completion_and_owned3600_kill_evidence':'NOT_RUN_OPEN',
 'synchronous_evidence_IO_interrupted_by_guard':False,
 'acceptance_requires_actual_controller_exit_and_raw_FINAL_RETURN_stderr':True,
 'new_failure_origins':[],
 'root_actual_grant_source_adoption_and_runtime_qualification_issued':False
}
emit('static-audit.json',audit)
emit('inputs.after.json',snapshots)
for record in snapshots:require(record['source']);require(record['copy'])
print(json.dumps({'verdict':audit['verdict'],'author14plusMF':15,'selected_refs':len(snapshots),'v3_byte_inverse_and_whole_AST_equal':True,'tail_lines':audit['tail_guard_lines'],'outer_native_target_calls':0,'new_origins':0},ensure_ascii=False))

