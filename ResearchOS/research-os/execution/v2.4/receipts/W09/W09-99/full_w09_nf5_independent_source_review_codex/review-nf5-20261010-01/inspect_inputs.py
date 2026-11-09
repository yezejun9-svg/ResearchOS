"""Task100 finite public Source shapes only; no entrypoint or executable helper."""
import hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
N=R/'execution/v2.4/receipts/W09/W09-99/full_w09_main_native_producer_source_codex/fullw09-20261010-05'
S=R/'execution/v2.4/receipts/W09/W09-99/w09_nf4_root_registration_source_codex/register-20261010-02'
def ref(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def main():
    nh=json.loads((N/'HDF.json').read_bytes());sh=json.loads((S/'HDF.json').read_bytes())
    choice=json.loads(Path(nh['source_choice_ref']['path']).read_bytes());bp=json.loads(Path(nh['compiler_blueprint_ref']['path']).read_bytes())
    pins=json.loads(Path(sh['input_pins_ref']['path']).read_bytes())
    delta=json.loads(Path(nh['source_delta_ref']['path']).read_bytes())
    resource=json.loads(Path(nh['resource_audit_ref']['path']).read_bytes())
    doc={'producer_hdf_ref':ref(N/'HDF.json'),'registrar_hdf_ref':ref(S/'HDF.json'),
        'producer_hdf_keys':list(nh),'registrar_hdf_keys':list(sh),'choice_common_keys':list(choice['common']),
        'choice_tool_refs':choice['common']['tool_refs'],'choice_guard_ref':choice['common']['guard_ref'],'choice_owned_job_ref':choice['common']['owned_job_ref'],
        'blueprint_keys':list(bp),'stable_input_count':len(bp['stable_input_refs']),'stable_input_total_bytes':sum(x['bytes'] for x in bp['stable_input_refs']),
        'blueprint_reference_groups':{k:{'type':type(v).__name__,'length':len(v) if type(v)in(list,dict)else None} for k,v in bp.items()},
        'registrar_input_keys':list(pins),'registrar_ref_keys':list(pins['refs']),
        'registrar_optional_null_refs':[k for k,v in pins['refs'].items() if v is None],
        'source_delta_keys':list(delta),'resource_audit_ref':nh['resource_audit_ref'],'resource_original_ref':resource['original_capture_ref'],
        'runtime_ref':nh['runtime_ref'],'overrides_ref':nh['overrides_ref'],'compiler_blueprint_ref':nh['compiler_blueprint_ref'],
        'root_resource_parent_ref':nh['resource_parent_ref'],'root_resource_owner_ref':nh['resource_owner_ref'],
        'subject_MF_shape':{str(home):list(json.loads((home/'MF.json').read_bytes())) for home in (N,S)},
        'no_stage_or_product_called':True}
    with (Q/'input-shapes.json').open('xb')as f:f.write((json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(doc,ensure_ascii=False));return 0
if __name__=='__main__':
    code=1
    try:code=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(code));sys.exit(code)
