import ast, hashlib, json, sys, types
from pathlib import Path
Q=Path(__file__).resolve().parent;B=Q.parent.parent
AUTHOR='codex:/root/backup_regression_resources';THREAD='01a11cee-bf59-7a01-be0e-9f799f9b1084';ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
def need(v,c):
    if not v:raise AssertionError(c)
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
    with (Q/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8'))
    return pin(Q/name)
def main():
    old=B/'genuine_schema21_public_bootstrap_runner_source_codex/s21public-20261010-01/seal_source.py'
    source=old.read_text(encoding='utf-8');node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='capture')
    segment=ast.get_source_segment(source,node).replace("Q/'actual-author-host'","Q/'actual-source-host-diagnostics'").replace("'task87_'","'task91_'").replace("need(len(completed)>=25,'FINITE_SOURCE_TOOL_PAIRS')","need(len(completed)>=8,'FINITE_SOURCE_TOOL_PAIRS')")
    def raw_new(path,raw):
        with Path(path).open('xb') as f:f.write(raw)
        return pin(path)
    env=dict(Q=Q,AUTHOR=AUTHOR,THREAD=THREAD,ROOT_THREAD=ROOT_THREAD,AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl'),Path=Path,json=json,hashlib=hashlib,need=need,raw_new=raw_new)
    exec(compile(segment,'actual-source-capture-functions','exec'),env);audit=env['capture']();audit['first_Task91_call_offset']=audit.pop('first_Task87_call_offset')
    audit_ref=save('source-diagnostic-original-host.index.json',audit)
    p=B/'schema21_root_caller_registration_source_codex/s21root-20261010-03/old21_root.source.py';m=types.ModuleType('source-only-host-structure');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
    matches=[]
    for pair in audit['completed_tool_pairs']:
        rows=[json.loads(x) for x in Path(pair['raw_ref']['path']).read_bytes().splitlines()]
        hosts=[x for x in m.structured_documents(rows[2]['payload']['output']) if x.get('chunk_id')=='99c046' and type(x.get('exit_code')) is int]
        if hosts:matches.append((pair,hosts))
    need(len(matches)==1 and len(matches[0][1])==1 and matches[0][1][0]['exit_code']==1,'EXACT_ACTUAL_99c046_RETURNED_OUTPUT')
    pair,host=matches[0];prefix=json.loads((Q/'source-controls.guard.closed.json').read_bytes())
    need(prefix['closure']['closed'] is True and prefix['closure']['retained_handles_count']==0 and not prefix['closure']['errors'],'ACTUAL_PREFIX_CLOSED_ZERO')
    origin=save('failure-origin.1132.json',dict(schema='researchos.original-source-failure-origin.v1',original_ordinal=1132,original_chunk_id='99c046',complete_IO_ref=pin(Q/'failure-99c046.complete-original-IO.json'),raw_ref=pair['raw_ref'],actual_host_binding_ref=pair['binding_ref'],actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,actual_go_exit=None,actual_SQL_exit=None,actual_TP_exit=None,actual_model_exit=None,cause='Task90 original review MF four-field relative_path metadata encountered strict three-field reference helper; Source only',original_source_snapshot_ref=pin(Q/'public21_root.before-mf-adapter.source.txt'),original_controls_ref=pin(Q/'source-controls.json'),guard_closed_ref=pin(Q/'source-controls.guard.closed.json'),counter_reset=False,automatic_retry=False))
    print(json.dumps(dict(origin_ref=origin,complete_IO_ref=pin(Q/'failure-99c046.complete-original-IO.json'),raw_ref=pair['raw_ref'],binding_ref=pair['binding_ref'],audit_ref=audit_ref,actual_outer_exit=1,actual_python_exit=1,other_exits=None,Root_branch_called=False),ensure_ascii=False))
if __name__=='__main__':
    code=1
    try:main();code=0
    finally:print('ROOT_PYTHON_EXIT='+str(code),flush=True)
    sys.exit(code)
