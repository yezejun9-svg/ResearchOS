"""Independent IO/AST review. Never import, eval, exec or call target/helper."""
from pathlib import Path
import ast
import hashlib
import json
import re

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
AUTHOR=ROOT/'execution/v2.4/receipts/W05/W05-99/f08_driver18_execution_revision_preparation_codex/1f63ee1825f24a35b3e88759b5c24e6a'
ORIGINAL=ROOT/'execution/v2.4/receipts/W05/W05-99/f08_driver18_execution_preparation_codex/d8a13bae58b341d8b28c0092527df4fc'
PRIOR=ROOT/'execution/v2.4/receipts/W05/W05-99/f08_driver18_execution_independent_source_review_codex/86a653e6772140f1b85f472613ef6d81'
seen={}

def ref(p):
    p=Path(p);raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def track(p,expected=None):
    r=ref(p)
    if expected is not None:assert r==expected,(r,expected)
    seen[r['path']]=r
    return Path(p).read_bytes()
def read_json(p,expected=None):return json.loads(track(p,expected))
def emit(name,value):
    p=OUT/name;p.write_bytes(json.dumps(value,ensure_ascii=False,indent=2).encode('utf-8')+b'\n');return ref(p)
def simple(node):return ast.dump(node,include_attributes=False)
def expression(text):return simple(ast.parse(text,mode='eval').body)
def calls(node,name):return [n for n in ast.walk(node) if isinstance(n,ast.Call) and ast.unparse(n.func)==name]
def source_block(text,node):return '\n'.join(text.splitlines()[node.lineno-1:node.end_lineno])
def functions(tree):return {n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}

expected_handoff={'path':str(AUTHOR/'handoff.json'),'sha256':'8538ab7ccdd046a906896d7736dda0bf857c87e9743cee056711c9843c7958ec','bytes':4894}
expected_manifest={'path':str(AUTHOR/'manifest.json'),'sha256':'7a241e598c1e07316b0d90bf5a04f6981817460fa92c0360212d39edf414593e','bytes':4001}
handoff=read_json(AUTHOR/'handoff.json',expected_handoff)
manifest=read_json(AUTHOR/'manifest.json',expected_manifest)
assert handoff['actor']=='codex:/root/command_queue_impl'
assert manifest['count']==len(manifest['files'])==12 and manifest['excluded_only_self'] is True
actual_members={str(p) for p in AUTHOR.iterdir() if p.is_file() and p.name!='manifest.json'}
assert actual_members=={r['path'] for r in manifest['files']}
for r in manifest['files']:track(Path(r['path']),r)

original_handoff=read_json(ORIGINAL/'handoff.json')
prior_handoff=read_json(PRIOR/'handoff.json',{'path':str(PRIOR/'handoff.json'),'sha256':'be53a38173d45d7e7655eb5f6eafc3644c879d66f216e47deeb884f5867f28c3','bytes':4335})
for r in handoff['review_input_refs']:track(Path(r['path']),r)
assert prior_handoff['verdict']=='REQUEST_CHANGES'
old_raw=track(Path(original_handoff['controller_ref']['path']),original_handoff['controller_ref'])
new_raw=track(Path(handoff['controller_ref']['path']),handoff['controller_ref'])
assert hashlib.sha256(new_raw).hexdigest()=='9d1dc8eedae32824b92742724bfd9b1174e367cc3c74102e5e5d268f5a6c60fb'
assert len(new_raw)==20492
launcher_raw=track(Path(handoff['launcher_ref']['path']),handoff['launcher_ref'])
assert handoff['launcher_ref']==original_handoff['launcher_ref']
assert hashlib.sha256(launcher_raw).hexdigest()=='fbf9c52568678e3733a0e50300a53c2044be96afee85672d3d2bf4df78af9086'
new_scope=read_json(Path(handoff['scope_ref']['path']),handoff['scope_ref'])
old_scope=read_json(Path(original_handoff['unbound_scope_ref']['path']),original_handoff['unbound_scope_ref'])
assert set(old_scope)==set(new_scope)
scope_diff=[k for k in new_scope if new_scope[k]!=old_scope[k]]
assert scope_diff==['controller_ref']
for k in ['actual_Root_registration','actual_origin_cut','actual_non_author_controller_review_ref','authority_validator_ref','resource_catalog_ref','prepared_ref','mode','ordered_cases','public_environment','work_root','prepare_output_root','execute_output_root','prepare_launcher_output_root','execute_launcher_output_root']:
    assert new_scope[k] is None,k
assert new_scope['preparation_only'] is True and new_scope['source_acceptance'] is False

old=old_raw.decode('utf-8');new=new_raw.decode('utf-8')
transformations=read_json(AUTHOR/'exact-transformations.json');assert len(transformations)==8
forward=old
for t in transformations:
    assert forward.count(t['before'])==1
    forward=forward.replace(t['before'],t['after'],1)
assert forward.encode('utf-8')==new_raw
inverse=new
for t in reversed(transformations):
    assert inverse.count(t['after'])==1
    inverse=inverse.replace(t['after'],t['before'],1)
assert inverse.encode('utf-8')==old_raw
diff=track(AUTHOR/'controller.diff').decode('utf-8')
hunks=len(re.findall(r'^@@ ',diff,re.M))
assert hunks==5
oldtree,newtree=ast.parse(old),ast.parse(new)
oldfunc,newfunc=functions(oldtree),functions(newtree)
unchanged=[]
for name in oldfunc:
    if name!='main':assert simple(oldfunc[name])==simple(newfunc[name]);unchanged.append(name)
assert set(oldfunc)==set(newfunc)
main=newfunc['main'];oldmain=oldfunc['main']
caps_node=next(n.value for n in newtree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CAPS' for t in n.targets))
caps=ast.literal_eval(caps_node)
assert caps==new_scope['caps']=={'native_calls':32,'compiler_seconds':600,'test_seconds':750,'inner_seconds':3300,'outer_seconds':3600,'cleanup_seconds':5,'images':64,'compiler_processes':2048,'job_active_processes':16,'fixture_HTTP':0,'SDK_Node_model_external_paid':0}
entry=next(n for n in newtree.body if isinstance(n,ast.If) and ast.unparse(n.test)=="__name__ == '__main__'")
entry_try=entry.body[0];assert isinstance(entry_try,ast.Try)
assert not calls(entry_try,'sys.exit')
assert len(entry.body)==2 and ast.unparse(entry.body[1])=='sys.exit(exit_code)'
assert ast.unparse(entry_try.body[0])=='exit_code = main()'
assert len(entry_try.handlers)==1 and ast.unparse(entry_try.handlers[0].type)=='BaseException'
assert ast.unparse(entry_try.handlers[0].body[-1])=='exit_code = 1'
old_entry=next(n for n in oldtree.body if isinstance(n,ast.If) and ast.unparse(n.test)=="__name__ == '__main__'")
new_error_write=calls(entry_try.handlers[0],'sys.stderr.write')[0]
old_error_write=calls(old_entry.body[0].handlers[0],'sys.stderr.write')[0]
assert simple(new_error_write)==simple(old_error_write)
entry_diag=next(n for n in ast.walk(new_error_write) if isinstance(n,ast.Dict))
diag_values=dict(zip([ast.literal_eval(k) for k in entry_diag.keys],entry_diag.values))
assert isinstance(diag_values['actual_native_exit'],ast.Constant) and diag_values['actual_native_exit'].value is None

run=next(n for n in ast.walk(main) if isinstance(n,ast.FunctionDef) and n.name=='run')
assignments={t.id:n.value for n in ast.walk(run) if isinstance(n,ast.Assign) for t in n.targets if isinstance(t,ast.Name)}
assert simple(assignments['remaining_seconds'])==expression('inner_deadline-time.monotonic()')
assert simple(assignments['effective_seconds'])==expression("min(seconds,remaining_seconds-CAPS['cleanup_seconds'])")
helper_call=calls(run,'debug.run_owned');assert len(helper_call)==1
assert isinstance(helper_call[0].args[5],ast.Name) and helper_call[0].args[5].id=='effective_seconds'
request_dict=next(n for n in ast.walk(run) if isinstance(n,ast.Dict) and any(isinstance(k,ast.Constant) and k.value=='requested_timeout' for k in n.keys))
req={ast.literal_eval(k):v for k,v in zip(request_dict.keys,request_dict.values)}
assert ast.unparse(req['timeout'])==ast.unparse(req['effective_timeout'])=='effective_seconds'
assert ast.unparse(req['requested_timeout'])=='seconds'
assert ast.unparse(req['remaining_inner_seconds'])=='remaining_seconds'
assert simple(req['cleanup_reserve_seconds'])==expression("CAPS['cleanup_seconds']")
assert any(simple(c.args[0])==expression("remaining_seconds>CAPS['cleanup_seconds'] and calls<32") for c in calls(run,'need'))
debug_raw=track(Path(new_scope['debug_helper_ref']['path']),new_scope['debug_helper_ref'])
debug_ast=ast.parse(debug_raw.decode('utf-8'))
debug_run=functions(debug_ast)['run_owned'];assert debug_run.args.args[5].arg=='timeout'
# Hash-pin/review original helpers; no OS API or run_owned execution occurs.
for k in ['utility_ref','owned_helper_ref']:
    track(Path(new_scope[k]['path']),new_scope[k])
assert 'deadline = time.monotonic() + 5.0' in debug_raw.decode('utf-8')

# All I16 phase branches and operations are structurally exact unchanged.
def i16_ifs(node):return [n for n in ast.walk(node) if isinstance(n,ast.If) and ast.unparse(n.test)=="ident == 'I16'"]
old16,new16=i16_ifs(oldmain),i16_ifs(main)
assert len(old16)==len(new16)==2 and all(simple(a)==simple(b) for a,b in zip(old16,new16))
fixed=read_json(Path(new_scope['fixed_inputs_ref']['path']),new_scope['fixed_inputs_ref'])
for k in ['test_source_ref','producer_ref','probe_ref','original_regression_ref','consumer_mod_ref','old_mod_ref']:
    track(Path(fixed[k]['path']),fixed[k])
regression=Path(fixed['original_regression_ref']['path']).read_bytes()
assert len(regression)==35317 and hashlib.sha256(regression).hexdigest()=='85e63e33c8d22d89e426dd33dff7bfece1f472b4796cd067718d9a6d22fb4e54'
test_text=Path(fixed['test_source_ref']['path']).read_text(encoding='utf-8')
i18=re.search(r'func TestDriverI18\(t \*testing.T\) \{(.*?)\n\}',test_text,re.S).group(1)
assert 'TestRegisteredFunctions(t)' in i18
assert 'driver18F08Bindings==nil' in test_text and 'I17 OPEN:' in test_text
assert "s['mode']=='PARTIAL_17_EXPLICIT'" in new and "s['ordered_cases']==[i for i in IDS if i!='I17']" in new
assert "need(s['authority_validator_ref'] is not None" in new
assert "need(s['preparation_only'] is False and s['caps']==CAPS" in new

# Case/final pre-qualification guards are present, but the last evidence guard
# precedes result+manifest IO. A successful late IO path has no further clock
# observation and return depends only on first. This is symbolic source analysis
# and never executes a fake/mocked target or manufactures native PASS.
monotonic_calls=calls(main,'time.monotonic')
last_clock=max(monotonic_calls,key=lambda c:c.lineno)
main_return=main.body[-1]
assert isinstance(main_return,ast.Return) and ast.unparse(main_return.value)=='1 if first else 0'
assert last_clock.lineno==250 and main_return.lineno==258
late_calls=[c for c in calls(main,'save') if last_clock.lineno<c.lineno<main_return.lineno]
assert {c.lineno for c in late_calls}=={253,254,255}
assert any(c.lineno==255 and calls(c,'pin') and calls(c,'u.files') for c in late_calls)
findings=[{
 'id':'D18-I01-TAIL','severity':'Important','status':'REQUEST_CHANGES',
 'source_ref':handoff['controller_ref'],'lines':[250,254,255,258],
 'cause':'Last inner deadline check is before result write and complete manifest read/hash/write; return only tests first.',
 'reachable_path':'first=None and deadline not yet expired at line250; line254/255 succeed but finish after inner_deadline; no later monotonic check updates first; line258 returns0.',
 'evidence_kind':'PYTHON_AST_AND_WHOLE_SOURCE_REASONING_ONLY_NOT_EXECUTED',
 'impact':'Late finalization inside3300..3600 can report controller success and partial17-qualified artifacts; outer3600 does not enforce the frozen inner3300 completion requirement.',
 'minimal_fix':'Add a final deadline rejection after last potentially blocking result/manifest work and before success return, preserving fixed failure diagnostics/native NULL and outer actual-exit authority. Independent review of a new author namespace is required; do not alter old sealed package.'
}]
checks={
 'whole_author_manifest12_plus_self_rehashed':True,'exact_transformations':8,'physical_unified_diff_hunks':hunks,'whole_forward_inverse_original_bytes_exact':True,
 'unchanged_nonmain_functions_classes':unchanged,'scope_only_controller_ref_changed':True,'launcher_whole_bytes_reused':True,
 'caps_32_600_750_3300_3600_cleanup5_unchanged':True,'NULL_authority_resource_registration_still_refuse':True,
 'I16_three_stage_business_unchanged':True,'I18_original_body_whole_pin_unchanged':True,'I17_still_FATAL_OPEN':True,
 'D18_C01_entry_exit_outside_BaseException':True,'original_ENTRY_exception_and_native_NULL_preserved':True,
 'D18_I01_helper_and_request_same_clamped_timeout':True,'D18_I01_case_and_prefinal_qualification_guards_present':True,
 'D18_I01_success_return_after_final_IO_deadline_guard':False,
 'candidate_helper_Go_SQL_SDK_HTTP_model_calls':0,'mock_or_fake_target_pass':False}
emit('source-review.json',{'schema':'researchos.driver18.controller-v2.independent-source-review.v1','actor':'codex:/root/f08_i17_binding_impl','author':handoff['actor'],'independent_non_author':True,'verdict':'REQUEST_CHANGES','checks':checks,'findings':findings,'not_run':'all candidate/helper/native execution','source_acceptance':False,'formal_increment':0})
emit('ast-deadline-evidence.json',{'schema':'researchos.ast-deadline-evidence.v1','controller_ref':handoff['controller_ref'],'last_monotonic_call':{'line':last_clock.lineno,'ast':simple(last_clock)},'later_save_calls':[{'line':n.lineno,'ast':simple(n)} for n in late_calls],'return':{'line':main_return.lineno,'ast':simple(main_return)},'symbolic_analysis_only':True,'candidate_execution':False,'excerpt':new.splitlines()[249:258]})
emit('inputs.before.json',list(seen.values()))
for i,r in enumerate(seen.values()):
    dest=OUT/'source-snapshots'/f'{i:03d}-{Path(r["path"]).name}'
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(Path(r['path']).read_bytes())
    assert ref(dest)['sha256']==r['sha256']
after=[]
for r in seen.values():
    current=ref(Path(r['path']));assert current==r;after.append(current)
emit('inputs.after.json',after)
print(json.dumps({'verdict':'REQUEST_CHANGES','D18_C01':'STATICALLY_ADDRESSED','D18_I01':'TAIL_FINALIZATION_DEADLINE_OPEN','inputs':len(seen),'transformations':8,'physical_diff_hunks':hunks,'whole_inverse_exact':True,'candidate_executed':False},ensure_ascii=False))
