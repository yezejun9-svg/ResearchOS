import hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
S=Q.parent.parent/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(ref):
    p=Path(ref['path']);raw=p.read_bytes();assert pin(p)==dict(ref,path=str(p));return json.loads(raw)
def main():
    packet=json.loads((S/'nf5-four-closed-actual-input02.root.json').read_bytes());facts={}
    for name,row in packet['groups'].items():
        bind=read(row['prepare_completed_Root_capture_ref']);rawref=bind['original_capture_ref'];raw=Path(rawref['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==rawref['sha256']and len(raw)==rawref['bytes']
        lines=[json.loads(x)for x in raw.splitlines()];facts[name]=dict(binding_ref=row['prepare_completed_Root_capture_ref'],call_input=lines[1]['payload']['input'],call_ordinal=lines[1]['ordinal'],actual_host_chunk_id=bind.get('actual_host_chunk_id'),actual_exit=bind.get('actual_outer_exit'))
    g=Q/'actual-review-v7-guard.closed.json';doc=json.loads(g.read_bytes());facts['own_guard']=dict(ref=pin(g),closed=doc['closed'],entries=len(doc['entries']),retained_handles_count=doc['retained_handles_count'],failure=doc['failure'],errors=doc['errors'])
    p=Q/'actual-prepare-completion-source-shapes.json'
    with p.open('xb')as f:f.write((json.dumps(facts,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(facts_ref=pin(p),facts=facts),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
