import hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(p,v):
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    result=json.loads((Q/'preparation-result.json').read_bytes())
    cleanup=json.loads((Q/'preparation-SourceGuard.closed.json').read_bytes())
    if result['primary_error'] is not None or cleanup['closed'] is not True or cleanup['retained_handles_count']!=0 or cleanup['errors']:raise ValueError('EXACT_SUCCESSFUL_PREPARATION_CLOSURE')
    if not all(x['verified'] and x['closed'] for x in cleanup['entries']):raise ValueError('ALL_PREPARATION_INPUTS_CLOSED')
    members=[pin(p) for p in sorted(Q.iterdir(),key=lambda p:p.name) if p.is_file() and p.name not in ('HDF.prepared.json','MF.prepared.json')]
    mf=save(Q/'MF.prepared.json',dict(schema='researchos.nf6-actual-review-preparation-manifest.v1',members=members,immutable_stage='PREPARATION_ONLY',actual_reports_included=False))
    hdf=save(Q/'HDF.prepared.json',dict(schema='researchos.nf6-actual-review-preparation-handoff.v1',actor_id='codex:/root/backup_regression_resources',backend_actor='/root/backup_regression_resources',source_author='codex:/root/full_w09_source_review',executor='codex:/root',status='PREPARED_PENDING_FOUR_CLOSED_ROOT_GROUPS',manifest_ref=mf,**result['produced_refs'],preparation_result_ref=pin(Q/'preparation-result.json'),guard_cleanup_ref=result['guard_cleanup_ref'],tool_io_ref=pin(Q/'preparation-tool-io.reencoded.json'),actual_host_chunk_id='87223d',actual_outer_exit=0,actual_python_exit=0,Source_inputs_verified=len(cleanup['entries']),all_guards_closed=True,retained_handles_count=0,live_audit_capture=False,future_actual_input_ref=None,current_Mode_decisions=[],actual_review_executed=False,execution_grant=False,formal_acceptance=False,formal_case_accepted_delta=0))
    print(json.dumps(dict(HDF_ref=hdf,MF_ref=mf,**result['produced_refs'],guard_cleanup_ref=result['guard_cleanup_ref'],status='PREPARED_PENDING_FOUR_CLOSED_ROOT_GROUPS',execution_grant=False,formal_acceptance=False,Mode_issued=False),ensure_ascii=False))
    return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
