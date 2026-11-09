"""Inspect only supplied actual dictionaries and selected code; no SQL or runtime."""
import ast
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
P=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/public22.readonly.actual.complete-hostpair-seal.root.json')
def load(p):return json.loads(Path(p).read_bytes())
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(Path(p)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def main():
    b=load(P);assert pin(P)['sha256']=='e5d4e7628a0fbeb3e2a9640ff7e11f37a0c7eaf2aad9915269964d749a1dcc89'
    q=load(b['source_caller_request_ref']['path']);a=load(b['actual_request_ref']['path'])
    facts=load(a['facts_ref']['path']);scope=load(a['scope_ref']['path']);activate=load(a['registration_result_ref']['path'])
    source=load(q['source_hdf_ref']['path']);guard=load(b['source_guard_closed_ref']['path'])
    runtime=load(source['runtime_resources_ref']['path']);returned=load(q['evidence']['returned_state_ref']['path'])
    caller=Path(source['caller_ref']['path']);leaf=Path(scope['leaf_runner_ref']['path'])
    summaries={}
    for name,obj in [('guard',guard),('runtime',runtime),('returned',returned),('owner',load(facts['owner_ref']['path'])),('worker',load(facts['worker_ref']['path']))]:
        summaries[name]={key:dict(type=type(value).__name__,length=len(value) if isinstance(value,(dict,list)) else None,
            first_keys=list(value[0]) if isinstance(value,list) and value and isinstance(value[0],dict) else list(value)[:18] if isinstance(value,dict) else None,
            scalar=value if type(value) in (str,int,bool,type(None)) else None) for key,value in obj.items()}
    source_functions={str(p):[dict(name=n.name,line=n.lineno,end=n.end_lineno) for n in ast.parse(p.read_bytes()).body if isinstance(n,ast.FunctionDef)] for p in (caller,leaf)}
    journal=Path(activate['transaction']['transaction_journal'])
    out=dict(bundle_ref=pin(P),bundle_keys=list(b),summaries=summaries,source_functions=source_functions,
        transaction_journal=str(journal),journal_actual_inventory=sorted(p.name for p in journal.iterdir()),
        selected_ref_inputs=dict(facts_ref=a['facts_ref'],scope_ref=a['scope_ref'],activate_ref=a['registration_result_ref'],
            caller_ref=source['caller_ref'],leaf_ref=scope['leaf_runner_ref'],runtime_ref=source['runtime_resources_ref'],
            actual_guard_ref=b['source_guard_closed_ref'],returned_ref=q['evidence']['returned_state_ref']),
        SQL_queries=0,new_native_children=0,Source_Canon_Main_writes=0)
    with (D/'actual-dictionary-inspection.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
    print(json.dumps(out,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
