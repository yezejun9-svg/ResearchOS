import datetime, hashlib, json, ntpath, sys, traceback, types
from pathlib import Path

R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W09/W09-99'
Q=Path(__file__).resolve().parent
U=B/'w09_nf6_registration_independent_source_review_codex/review-20261010-01'
P=B/'full_w09_main_native_producer_source_codex/fullw09-20261010-06'
G=B/'w09_nf6_root_registration_source_codex/register-20261010-01'
S=B/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'

def pin(p):
    raw=Path(p).read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(p,v):
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def walk(v):
    yield v
    if type(v)is dict:
        for x in v.values():yield from walk(x)
    elif type(v)is list:
        for x in v:yield from walk(x)
def same(a,b):
    return (ntpath.normcase(ntpath.normpath(a['path'])),a['sha256'],a['bytes'])==(ntpath.normcase(ntpath.normpath(b['path'])),b['sha256'],b['bytes'])
def main():
    choice=json.loads((P/'source.choice.json').read_bytes())
    guard_ref=choice['common']['guard_ref']
    guard_bytes=Path(guard_ref['path']).read_bytes()
    if pin(guard_ref['path'])['sha256']!=guard_ref['sha256']:raise ValueError('PINNED_GUARD_SOURCE')
    mod=types.ModuleType('nf6_registrar_author_guard');mod.__file__=guard_ref['path']
    exec(compile(guard_bytes,guard_ref['path'],'exec'),mod.__dict__)
    audit_ref=dict(path=str(S/'w09.nf6-registrar-source-author.actual-audit.root.json'),sha256='fe9372aaaf64de38bfc521679d052151262045c9cd9bc07b8061139c55b4d92d',bytes=1117)
    raw_ref=dict(path=str(S/'w09.nf6-registrar-source-author.original.raw.jsonl'),sha256='7d2b39e4be197e411a2a593cbc6bd79c13a958ac761972293bb102fa9b7facc1',bytes=32378)
    guard=mod.SourceReadGuard(per_file_cap=1024*1024,total_cap=2*1024*1024)
    result=dict(schema='researchos.w09-nf6-registrar-author-supplement.v1',actor_id='codex:/root/backup_regression_resources',new_controls=1,passed=False,actual_executed=False,execution_grant=False,formal_acceptance=False,Native=None,Go=None,SQL=None,model=None,TP=None,dispatcher=None)
    primary=None
    try:
        guard.acquire([audit_ref,raw_ref])
        audit=json.loads(guard.get_buffer(audit_ref['path']))
        raw=guard.get_buffer(raw_ref['path']);lines=raw.splitlines(keepends=True)
        rows=[json.loads(x) for x in lines]
        if len(rows)!=3:raise ValueError('EXACT_THREE_RAW_LINES')
        header,meta,final=rows
        text='\n'.join(x['text'] for x in final['payload']['content'] if x['type']=='input_text')
        prefix='Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/full_w09_source_review\nPayload:\n'
        payload=json.loads(text[len(prefix):] if text.startswith(prefix) else text)
        refs=[x for x in walk(payload) if type(x)is dict and set(x)=={'path','sha256','bytes'}]
        expected=[pin(G/'HDF.json'),pin(G/'MF.json')]
        conditions=[audit['schema']=='researchos.w09-native-producer.actual-audit.v1',audit['actor_id']=='codex:/root/full_w09_source_review',audit['Root_thread_id']==header['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98',audit['binding_sha256']==expected[0]['sha256'],same(audit['original_capture_ref'],raw_ref),audit['original_line_sha256']==[hashlib.sha256(x).hexdigest() for x in lines],final['payload']['author']=='/root/full_w09_source_review',final['payload']['recipient']=='/root',final['metadata']['client_authored'] is False,meta['timestamp']==final['timestamp']=='2026-10-09T23:53:27.581Z',all(any(same(a,b) for a in refs) for b in expected)]
        if not all(conditions):raise ValueError('TRUE_REGISTRAR_SPECIFIC_SOURCE_FINAL_BINDING')
        result.update(passed=True,author_audit_ref=audit_ref,author_original_raw_ref=raw_ref,published_registrar_refs=expected,exact_published_time=final['timestamp'],producer_and_registrar_same_real_Final=True,scope_or_runtime_issuance=False)
    except BaseException as exc:
        primary=dict(type=type(exc).__name__,message=str(exc));traceback.print_exc()
    finally:
        close=guard.close()
        cleanup_ref=save(Q/'registrar-author-SourceGuard.closed.json',close)
        result.update(primary_error=primary,guard_cleanup_ref=cleanup_ref,guard_closed=close['closed'],retained_handles_count=close['retained_handles_count'])
        result_ref=save(Q/'registrar-author-supplement-result.json',result)
        save(U/'registrar-author-supplement-reference.json',dict(supplement_result_ref=result_ref,guard_cleanup_ref=cleanup_ref,execution_grant=False,formal_acceptance=False))
        print(json.dumps(dict(result_ref=result_ref,guard_cleanup_ref=cleanup_ref,passed=result['passed'],primary_error=primary,guards_closed=close['closed'],retained_handles_count=close['retained_handles_count']),ensure_ascii=False))
    return 0 if result['passed'] and close['closed'] and not close['errors'] and close['retained_handles_count']==0 else 1

if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
