import hashlib,json,sys,traceback,types
from pathlib import Path
Q=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def main():
    shape=json.loads((Q/'actual-input-shapes.json').read_bytes());h=json.loads(Path(shape['source_hdf_ref']['path']).read_bytes())
    all_choices=json.loads(Path(h['source_choice_ref']['path']).read_bytes());choice=dict(all_choices['common'],**all_choices['selectors']['W09-G02'])
    contract=json.loads((Q/'input-contract.v3.json').read_bytes())
    refs=[shape['source_hdf_ref'],shape['source_mf_ref'],shape['calling_contract_ref'],shape['runtime_ref'],shape['choice_ref'],h['compiler_blueprint_ref'],
        *choice['source21'],*contract['prior_Source_review_refs'].values(),pin(R/'execution/v2.4/formal_profile_w09.py'),pin(R/'execution/toolchains/locked.json')]
    captures=json.loads((Q/'G02-Root-capture-shapes.json').read_bytes())
    for row in captures.values():refs.extend([row['binding_ref'],row['binding']['original_capture_ref']])
    refs.extend(pin(Q/name)for name in('review_actual_nf5.v2.py','input-contract.json','input-contract.v3.json','prepare-host-delta-controls.json','source-preparation-controls.json','prepare_review_contract.py','actual-input-shapes.json','small-actual-metadata.json','G02-Root-capture-shapes.json','G02-Root-encoding.json'))
    guard_path=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
    guard_raw=guard_path.read_bytes();assert len(guard_raw)==11404 and hashlib.sha256(guard_raw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
    refs.append(pin(guard_path));unique={str(Path(ref['path']).resolve(strict=True)).casefold():ref for ref in refs}
    module=types.ModuleType('prepared_nf5_actual_guard');module.__file__=str(guard_path);exec(compile(guard_raw,str(guard_path),'exec'),module.__dict__)
    guard=module.SourceReadGuard(per_file_cap=16*1024*1024,total_cap=64*1024*1024);primary=None;closed=None
    try:guard.acquire(list(unique.values()))
    except BaseException as exc:primary=exc
    finally:
        closed=guard.close()
        with(Q/'preparation.Sourceguard.closed.json').open('xb')as f:f.write((json.dumps(closed,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    if primary is not None:raise primary
    assert closed['closed']is True and closed['retained_handles_count']==0 and not closed['errors']
    print(json.dumps(dict(status='PREPARATION_SOURCEGUARD_CLOSED',resource_count=len(unique),guard_ref=pin(Q/'preparation.Sourceguard.closed.json'),Native_runs=0,Root_stages=0,live_Canon_or_audit_handles=False,acceptance=False),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
