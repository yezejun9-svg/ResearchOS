import ast, hashlib, json, difflib
from pathlib import Path
N=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99')
O=R/'f08_driver18_execution_preparation_codex/d8a13bae58b341d8b28c0092527df4fc'
V=R/'f08_driver18_execution_independent_source_review_codex/86a653e6772140f1b85f472613ef6d81'
def need(v,m):
    if not v:raise RuntimeError(m)
def pin(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(name,b):
    with (N/name).open('xb') as f:f.write(b)
def save(name,v):put(name,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
inputs=[O/n for n in ['driver18_controller.proposed.py','launch.proposed.py','scope.UNBOUND.proposed.json','handoff.json','manifest.json','fixed-inputs.json','resource-and-authority-contract.json','I16-provenance-contract.json','finite-operation-roster.json']]+[V/n for n in ['handoff.json','source-review.json','REVIEW.md']]
before=[pin(p) for p in inputs]
raw=inputs[0].read_bytes();need(hashlib.sha256(raw).hexdigest()=='2dcf353c2d2f285234170d7d09b933521da4549565d2242a0e370de06dc75fa5','ORIGINAL_SHA')
s=raw.decode('utf8');changes=[]
def change(a,b):
    global s
    need(s.count(a)==1,'UNIQUE_ANCHOR '+repr(a));s=s.replace(a,b,1);changes.append({'before':a,'after':b})
change("active=None;last=None;calls=0;started=time.monotonic()", "active=None;last=None;calls=0;started=time.monotonic();inner_deadline=started+CAPS['inner_seconds']")
change("            stage=label;need(time.monotonic()-started<CAPS['inner_seconds'] and calls<32,'FINITE_DEADLINE_OR_CALLCAP')", "            stage=label;remaining_seconds=inner_deadline-time.monotonic()\n            need(remaining_seconds>CAPS['cleanup_seconds'] and calls<32,'FINITE_DEADLINE_OR_CALLCAP')\n            effective_seconds=min(seconds,remaining_seconds-CAPS['cleanup_seconds'])")
change("'timeout':seconds,'call':calls", "'timeout':effective_seconds,'requested_timeout':seconds,'effective_timeout':effective_seconds,\n                'remaining_inner_seconds':remaining_seconds,'cleanup_reserve_seconds':CAPS['cleanup_seconds'],'call':calls")
change("result=debug.run_owned(argv,str(cwd),ee,so,se,seconds,", "result=debug.run_owned(argv,str(cwd),ee,so,se,effective_seconds,")
change("ledger.check(ident+'-fixture-after');active.update(status='QUALIFIED'", "ledger.check(ident+'-fixture-after');need(time.monotonic()<inner_deadline,'INNER_DEADLINE_EXPIRED');active.update(status='QUALIFIED'")
change("ledger.check('final');save(out/'qualified-partial17.json'", "ledger.check('final');need(time.monotonic()<inner_deadline,'INNER_DEADLINE_EXPIRED');save(out/'qualified-partial17.json'")
change("            if first is None and secondary:first={'stage':'EVIDENCE_FINALIZATION'", "            if time.monotonic()>=inner_deadline:secondary.append({'stage':'EVIDENCE_FINALIZATION','error':'INNER_DEADLINE_EXPIRED','actual_stage_native_exit':None})\n            if first is None and secondary:first={'stage':'EVIDENCE_FINALIZATION'")
change("    try:sys.exit(main())\n    except BaseException as e:\n        sys.stderr.write(json.dumps({'stage':'ENTRY','error':repr(e),'traceback':traceback.format_exc(),'actual_native_exit':None,'outer_raw_authority':True})+'\\n');sys.exit(1)", "    try:exit_code=main()\n    except BaseException as e:\n        sys.stderr.write(json.dumps({'stage':'ENTRY','error':repr(e),'traceback':traceback.format_exc(),'actual_native_exit':None,'outer_raw_authority':True})+'\\n');exit_code=1\n    sys.exit(exit_code)")
new=s.encode();tree=ast.parse(new);oldtree=ast.parse(raw)
inv=s
for c in reversed(changes):
    need(inv.count(c['after'])==1,'INVERSE_UNIQUE');inv=inv.replace(c['after'],c['before'],1)
need(inv.encode()==raw,'FULL_BYTE_INVERSE')
oldfunc={x.name:ast.dump(x,include_attributes=False) for x in oldtree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
newfunc={x.name:ast.dump(x,include_attributes=False) for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
need(set(oldfunc)==set(newfunc),'FUNCTION_SET')
unchanged=[k for k in oldfunc if k!='main'];need(all(oldfunc[k]==newfunc[k] for k in unchanged),'OTHER_AST')
entry=tree.body[-1];need(isinstance(entry,ast.If) and len(entry.body)==2 and isinstance(entry.body[0],ast.Try),'ENTRY_SHAPE')
tr=entry.body[0]
need(not any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=='exit' for x in ast.walk(tr)),'EXIT_STILL_CAUGHT')
need(isinstance(entry.body[1],ast.Expr) and ast.unparse(entry.body[1])=='sys.exit(exit_code)','EXIT_OUTSIDE')
main=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='main');run=next(x for x in ast.walk(main) if isinstance(x,ast.FunctionDef) and x.name=='run')
helpercalls=[x for x in ast.walk(run) if isinstance(x,ast.Call) and ast.unparse(x.func)=='debug.run_owned'];need(len(helpercalls)==1 and ast.unparse(helpercalls[0].args[5])=='effective_seconds','HELPER_EFFECTIVE_TIMEOUT')
need("'timeout':effective_seconds" in s and "'effective_timeout':effective_seconds" in s,'REQUEST_EFFECTIVE_SAME')
need("remaining_seconds>CAPS['cleanup_seconds']" in s and "effective_seconds=min(seconds,remaining_seconds-CAPS['cleanup_seconds'])" in s,'RESERVE_AND_MIN')
need(s.index("need(remaining_seconds>CAPS")<s.index('calls+=1'),'STOP_BEFORE_CALL')
put('driver18_controller.v2.proposed.py',new)
scope=json.loads((O/'scope.UNBOUND.proposed.json').read_bytes());oldscope=json.loads((O/'scope.UNBOUND.proposed.json').read_bytes());scope['controller_ref']=pin(N/'driver18_controller.v2.proposed.py')
need({k:v for k,v in scope.items() if k!='controller_ref'}=={k:v for k,v in oldscope.items() if k!='controller_ref'},'SCOPE_DELTA')
save('scope.UNBOUND.v2.proposed.json',scope)
put('controller.diff', ''.join(difflib.unified_diff(raw.decode().splitlines(True),s.splitlines(True),fromfile='original/controller',tofile='revision/controller')).encode())
save('exact-transformations.json',changes)
for p in [O/'launch.proposed.py',N/'prepare_revision.py']:ast.parse(p.read_bytes())
examples=[]
for elapsed,requested in [(0,600),(2500,750),(3294,750),(3295,600),(3300,750)]:
    remaining=3300-elapsed;admitted=remaining>5
    examples.append({'illustrative_elapsed':elapsed,'requested':requested,'remaining':remaining,'would_admit':admitted,'effective_if_admitted':min(requested,remaining-5) if admitted else None,'candidate_executed':False})
after=[pin(p) for p in inputs];need(before==after,'INPUT_DRIFT')
save('inputs.before.json',before);save('inputs.after.json',after)
save('static-audit.json',{'schema':'researchos.driver18-revision-static-audit.v1','candidate_executed':False,'target_commands':0,'Go_SQL_HTTP_SDK':0,'full_byte_inverse':True,'original_sha256':before[0]['sha256'],'unchanged_functions_classes':unchanged,'entry_exit_outside_BaseException':True,'request_helper_same_effective_timeout':True,'absolute_deadline':True,'cleanup_reserved_seconds':5,'final_qualification_and_evidence_deadline_guard':True,'unchanged_scope_except_controller_ref':True,'unchanged_launcher_ref':scope['launcher_ref'],'illustrative_arithmetic_not_candidate_tests':examples,'input_drift':[],'actual_native_exit':None})
save('fix-mapping.json',{'D18-C01':{'fix':'main result assigned inside try, sys.exit outside; original ENTRY exception facts retained','proof':'exact-transformations.json + static-audit.json'},'D18-I01':{'fix':'absolute inner deadline, prelaunch remaining>5, helper timeout min(requested,remaining-5), same requested/effective/remaining facts, case/final/evidence completion expiry rejects','limitations':'Read/hash evidence collection remains cooperative; unchanged outer owned-job 3600 bound applies. Qualified leaf facts are historical point-in-time; authoritative result first_cause still rejects late finalization.'},'unchanged':['I16 three phases','I18 original TestRegisteredFunctions body','I17 FATAL_OPEN','resource and authority null gates','32/600/750/3300/3600/5 and process/image caps','source membership','two-phase prepare/execute grants'],'status':'PREPARATION_ONLY_NOT_RUN','independent_review_required':True})
print(json.dumps({'controller':pin(N/'driver18_controller.v2.proposed.py'),'scope':pin(N/'scope.UNBOUND.v2.proposed.json'),'audit':pin(N/'static-audit.json'),'transformations':len(changes),'candidate_executed':False},ensure_ascii=False))
