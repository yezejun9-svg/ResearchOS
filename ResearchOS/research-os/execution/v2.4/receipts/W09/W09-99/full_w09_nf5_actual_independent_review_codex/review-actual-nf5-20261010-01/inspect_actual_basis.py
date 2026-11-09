"""Read bounded NF5 G02 closed public shapes. No product execution or acceptance."""
import hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
N=R/'execution/v2.4/receipts/W09/W09-99/full_w09_main_native_producer_source_codex/fullw09-20261010-05'
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def main():
    h=json.loads((N/'HDF.json').read_bytes());choice=json.loads(Path(h['source_choice_ref']['path']).read_bytes())
    c=choice['selectors']['W09-G02'];root=Path(c['receipt_root']);stage=root/'producer'
    closed=json.loads((stage/'validation.closed.json').read_bytes());ready=json.loads((root/'prepare.ready.json').read_bytes())
    report_ref=closed['summary']['report_ref'];tool_ref=closed['summary']['tool_run_ref']
    report=json.loads(Path(report_ref['path']).read_bytes());tool=json.loads(Path(tool_ref['path']).read_bytes())
    observations=[]
    for row in closed['invocation_observations']:
        observations.append(dict(row_keys=list(row),row=row))
    result=dict(source_hdf_ref=pin(N/'HDF.json'),source_mf_ref=h['manifest_ref'],calling_contract_ref=h['calling_contract_ref'],runtime_ref=h['runtime_ref'],choice_ref=h['source_choice_ref'],
        G02_closed_ref=pin(stage/'validation.closed.json'),G02_prepare_ref=pin(root/'prepare.ready.json'),
        G02_closed_keys=list(closed),G02_closed_boundary={k:v for k,v in closed.items()if k not in ('invocation_observations','guard_cleanups','invocation_refs','summary','canonical_vector')},
        G02_summary=closed['summary'],G02_invocation_observations=observations,
        G02_prepare_keys=list(ready),G02_prepare_environment=ready['environment'],G02_report_keys=list(report),G02_tool_keys=list(tool),
        G02_report_scalar_fields={k:v for k,v in report.items()if type(v)not in (dict,list)},
        G02_report_collection_shapes={k:dict(type=type(v).__name__,length=len(v),keys=list(v)if type(v)is dict else None)for k,v in report.items()if type(v)in(dict,list)},
        G02_tool=tool,actual_G02_report_ref=report_ref,actual_G02_tool_ref=tool_ref,
        no_product_called=True,acceptance=False)
    with (Q/'actual-input-shapes.json').open('xb')as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps({k:v for k,v in result.items()if k not in ('G02_tool','G02_invocation_observations','G02_closed_boundary')},ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
