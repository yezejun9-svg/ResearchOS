"""One narrow Task100 checker correction. Original finite result is immutable."""
import ast,hashlib,json,sys,traceback,types
from pathlib import Path
Q=Path(__file__).resolve().parent
def ref(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,v):
    with (Q/name).open('xb')as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def main():
    shapes=json.loads((Q/'input-shapes.json').read_bytes())
    rr=shapes['runtime_ref'];gr=shapes['choice_guard_ref']
    for r in (rr,gr):
        if ref(r['path'])!=r:raise ValueError('DELTA_SOURCE_PIN_DRIFT')
    m=types.ModuleType('task100_delta_guard');m.__file__=gr['path']
    exec(compile(Path(gr['path']).read_bytes(),gr['path'],'exec'),m.__dict__)
    guard=m.SourceReadGuard();result=None
    try:
        guard.acquire([rr,gr,ref(__file__)])
        tree=ast.parse(guard.get_buffer(rr['path']))
        stage=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='stage')
        branch=next(x for x in ast.walk(stage)if isinstance(x,ast.If)and ast.unparse(x.test)=="kind == 'prepare'")
        # Traverse only the true body, excluding the producer's else branch.
        calls={ast.unparse(x.func)for body in branch.body for x in ast.walk(body)if isinstance(x,ast.Call)}
        passed=not any('run_owned'in x or x in ('invoke','stage','subprocess.run','os.system')for x in calls)
        result=dict(schema='researchos.w09-nf5-independent-checker-delta.v1',original_failure_ordinal=1147,
            original_result_ref=ref(Q/'finite-review.json'),name='prepare_branch_has_no_process_or_stage_recursion',
            passed=passed,actual_true_body_calls=sorted(calls),Source_ref=rr,actual_stage_calls=0,
            Source_changed=False,old_passed_26_replayed=False,resource_closure_4154_replayed=False,
            explanation='Original AST walker traversed the whole If including its else branch; corrected walker traverses only branch.body.')
    finally:save('prepare-delta.SourceGuard.closed.json',guard.close())
    save('prepare-body-delta.json',result)
    print(json.dumps(dict(passed=result['passed'],old_controls_rerun=False,Source_changed=False),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
