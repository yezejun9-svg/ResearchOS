import ast,difflib,hashlib,json
from pathlib import Path
N=Path(__file__).parent
R=N.parent.parent
O=N.parent/'1f63ee1825f24a35b3e88759b5c24e6a'
V=R/'f08_driver18_controller_v2_independent_review_codex/2e6aada371e64d3b892533163cf85a39'
def need(v,m):
    if not v:raise RuntimeError(m)
def pin(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,b):
    with (N/name).open('xb') as f:f.write(b)
def save(name,v):write(name,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
h=json.loads((O/'handoff.json').read_bytes());vr=json.loads((V/'handoff.json').read_bytes())
paths=[O/'handoff.json',O/'manifest.json',Path(h['controller_ref']['path']),Path(h['scope_ref']['path']),Path(h['launcher_ref']['path']),V/'handoff.json',V/'manifest.json',V/'REVIEW.md',V/'source-review.json',V/'ast-deadline-evidence.json']
before=[pin(p) for p in paths]
need(pin(paths[2])==h['controller_ref'],'OLD_CONTROLLER_PIN');need(pin(V/'REVIEW.md')['sha256']=='f65880abdfb9dcf6819c119e177ef7814fe360d0f0fee5f9e3bca43fa9afaac8','REVIEW_PIN')
raw=paths[2].read_bytes();need(hashlib.sha256(raw).hexdigest()=='9d1dc8eedae32824b92742724bfd9b1174e367cc3c74102e5e5d268f5a6c60fb','INPUT_SHA')
a=b'    return 1 if first else 0\n'
b=b'''    if time.monotonic()>=inner_deadline:
        sys.stderr.write(json.dumps({'stage':'FINAL_RETURN','error':'INNER_DEADLINE_EXPIRED','first_cause':first,'actual_native_exit':None,'outer_raw_authority':True})+'\\n')
        return 1
    return 1 if first else 0
'''
need(raw.count(a)==1,'EXACT_ANCHOR');new=raw.replace(a,b,1)
need(new.count(b)==1 and new.replace(b,a,1)==raw,'BYTE_INVERSE')
t=ast.parse(new);old=ast.parse(raw);m=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=='main')
need(isinstance(m.body[-2],ast.If) and isinstance(m.body[-1],ast.Return),'TAIL_SHAPE')
tail=m.body[-2];need(ast.unparse(tail.test)=='time.monotonic() >= inner_deadline','ACTUAL_MONOTONIC_DEADLINE')
need(isinstance(tail.body[-1],ast.Return) and isinstance(tail.body[-1].value,ast.Constant) and tail.body[-1].value.value==1,'EXPIRED_ALWAYS_NONZERO')
need(ast.unparse(m.body[-1])=='return 1 if first else 0','ORIGINAL_FAILURE_RETURN')
need(not any(isinstance(x,(ast.Assign,ast.AugAssign,ast.NamedExpr)) for x in ast.walk(tail)),'NO_FIRSTCAUSE_MUTATION')
need(len(tail.body)==2 and ast.unparse(tail.body[0].value.func)=='sys.stderr.write','OUTER_STDERR_DIAGNOSTIC_ONLY')
need("'first_cause':first" in b.decode() and "'actual_native_exit':None" in b.decode(),'FIRST_AND_NULL_RETAINED')
oldmain=next(x for x in old.body if isinstance(x,ast.FunctionDef) and x.name=='main')
m.body.pop(-2)
need(ast.dump(t,include_attributes=False)==ast.dump(old,include_attributes=False),'WHOLE_AST_INVERSE')
# No candidate exec/import: the sole changed AST branch is removed only in this in-memory proof.
write('driver18_controller.v3.proposed.py',new)
scope=json.loads(paths[3].read_bytes());oldscope=json.loads(paths[3].read_bytes());scope['controller_ref']=pin(N/'driver18_controller.v3.proposed.py')
need(all(scope[k]==oldscope[k] for k in oldscope if k!='controller_ref'),'SCOPE_ONLY_CONTROLLER')
save('scope.UNBOUND.v3.proposed.json',scope)
write('controller.diff',''.join(difflib.unified_diff(raw.decode().splitlines(True),new.decode().splitlines(True),fromfile='v2/controller',tofile='v3/controller')).encode())
save('exact-transform.json',{'before':a.decode(),'after':b.decode(),'inverse_sha256':hashlib.sha256(new.replace(b,a,1)).hexdigest(),'exact_replacements':1})
after=[pin(p) for p in paths];need(before==after,'INPUT_DRIFT');save('inputs.before.json',before);save('inputs.after.json',after)
save('static-audit.json',{'finding':'D18-I01-TAIL','input_review_ref':pin(V/'REVIEW.md'),'full_byte_inverse':True,'whole_AST_inverse_after_removing_exact_tail':True,'AST_parsed_not_executed':True,'tail_after_finally_result_manifest_IO':True,'expired_tail_return':1,'first_cause_not_reassigned':True,'raw_stderr_diagnostic_includes_original_first_and_native_NULL':True,'unchanged_entry_sys_exit_outside_catch':True,'unchanged_launcher_ref':h['launcher_ref'],'scope_only_controller_ref_changed':True,'input_drift':[],'all_target_calls':0,'future_cases':'NOT_RUN','semantics':'Already written result/qualified/manifest files are point-in-time artifacts. A FINAL_RETURN stderr diagnostic plus nonzero actual controller exit rejects expired overall completion; outer captured raw/actual exit authority must be consumed. No old file is rewritten.','known_limit':'Synchronous IO remains cooperative; this patch refuses successful return after it completes late, it cannot interrupt a blocked filesystem call. Existing outer owned-job3600 remains unchanged.'})
print(json.dumps({'controller':pin(N/'driver18_controller.v3.proposed.py'),'scope':pin(N/'scope.UNBOUND.v3.proposed.json'),'audit':pin(N/'static-audit.json'),'candidate_executed':False},ensure_ascii=False))
