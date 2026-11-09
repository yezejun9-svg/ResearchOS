"""Derive a successor Source package without reading Main/Canon or running jobs."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import types
import uuid

N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
OLD=W/'w09_c19_main_root_producer_source_codex/mainc19p-1a11fbc'
Q=W/'main_c19_root_producer_independent_review_codex/review-1a11fa1'
def pin(p):
    p=Path(p).resolve(strict=True);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def load(p):return json.loads(Path(p).read_bytes())
def save(name,value,raw=False):
    data=value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with (N/name).open('xb') as f:f.write(data)
    return pin(N/name)
def main():
    expected={OLD/'HDF.json':('2f8127a4bae45ac7c31c24f59a878c01c74549bc200a43162d16783618b1ea2f',13717),
        OLD/'MF.json':('270027d8caacac6ad5996d627d09549c05b9102ac5b7aa588d33cbea9347265d',10819),
        Q/'HDF.json':('caa970f551f80b647fb31b5453910c9aa9cc75d3ec21a0e07f81a4a6797f0c29',2371),
        Q/'MF.json':('5e4ee48982f207abb22b33363f9792845d2ef0adf048e19175afe0a4576ba9c8',3083)}
    inputs={}
    def add(ref):
        assert pin(ref['path'])==ref
        key=ref['path'].casefold();assert key not in inputs or inputs[key]==ref;inputs[key]=ref
    for p,(sha,size) in expected.items():
        ref=pin(p);assert (ref['sha256'],ref['bytes'])==(sha,size);add(ref)
    for home in (OLD,Q):
        assert load(home/'HDF.json')['manifest_ref']==pin(home/'MF.json')
        for ref in load(home/'MF.json')['members']:add(ref)
    findings=load(Q/'findings.json')
    assert len(findings)==1 and findings[0]['id']=='MAIN-C19-PRODUCER-01' and findings[0]['priority']=='P1'
    assert load(Q/'HDF.json')['status']=='REQUEST_CHANGES'
    for ref in load(OLD/'source-input-pins.original.json')['refs']:add(ref)
    c=load(OLD/'source.choice.json')
    forbidden={r['path'].casefold() for r in c['main_seven_after_refs']}|{str(R/'execution/v2.4'/f'{n}.json').casefold() for n in ('checkpoint','path_ownership','step_state','commands')}
    assert not forbidden.intersection(inputs)
    gp=c['guard_ref'];m=types.ModuleType('v2_preparation_guard');m.__file__=gp['path']
    exec(compile(Path(gp['path']).read_bytes(),gp['path'],'exec'),m.__dict__)
    guard=m.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
    try:
        guard.acquire(list(inputs.values()))
        before=(OLD/'main_c19_runtime.source.py').read_text(encoding='utf-8')
        start=before.index('def invoke(');end=before.index('def compiler_inventory(',start)
        runtime=before[:start]+(N/'cleanup_helpers.fragment.py').read_text(encoding='utf-8')+'\n\n'+before[end:]
        old_init='guards=[];cleanups=[];receipts=[];error=None;success=False;created=False;summary=None;packet_ref=None;archive_error=None'
        assert runtime.count(old_init)==1
        runtime=runtime.replace(old_init,'guards=[];cleanups=[];receipts=[];error=None;primary=None;success=False;created=False;summary=None;packet_ref=None')
        start=runtime.index('    except BaseException as exc:error=repr(exc)',runtime.index('def stage('))
        end=runtime.index('\n\ndef scope_path(',start)
        runtime=runtime[:start]+(N/'stage_tail.fragment.py').read_text(encoding='utf-8').rstrip()+runtime[end:]
        compile(runtime,'v2-runtime','exec');rp=save('main_c19_runtime.source.py',runtime.encode(),True)
        template=(OLD/'main_c19_launcher.template.py').read_text(encoding='utf-8')
        assert template.count('returned=None;error=None')==1
        template=template.replace('returned=None;error=None','returned=None;error=None;primary=None;cleanup_errors=[]')
        start=template.index('    except BaseException as exc:error=repr(exc)');end=template.index('\n\nif __name__',start)
        template=template[:start]+(N/'launcher_tail.fragment.py').read_text(encoding='utf-8').rstrip()+template[end:]
        save('main_c19_launcher.template.py',template.encode(),True)
        launcher=template.replace('RUNTIME_SHA_BIND_AT_SOURCE_SEAL',rp['sha256'])
        compile(launcher,'v2-launcher','exec');save('main_c19_launcher.source.py',launcher.encode(),True)
        for stage in ('prepare','run'):
            old=(OLD/(stage+'_main_c19.actual_owned.py')).read_bytes()
            assert old.count(pin(OLD/'main_c19_runtime.source.py')['sha256'].encode())==1
            raw=old.replace(pin(OLD/'main_c19_runtime.source.py')['sha256'].encode(),rp['sha256'].encode())
            compile(raw,stage,'exec');save(stage+'_main_c19.actual_owned.py',raw,True)
        bp=save('compiler-source-blueprint.json',(OLD/'compiler-source-blueprint.json').read_bytes(),True)
        run_id=uuid.uuid4().hex
        c.update(run_id=run_id,receipt_root=str(N/'actual-main-root'),scratch_root=str(R/'.local'/('w09-c19-main-'+run_id)),
            output_root=str(R/'execution/receipts/W09/retrieval'/('run-'+run_id)),compiler_blueprint_ref=bp,source_revision='v2')
        assert all(not Path(c[k]).exists() for k in ('receipt_root','scratch_root','output_root'))
        save('source.choice.json',c)
        contract=load(OLD/'root-calling-contract.json')
        contract['bound_source_refs']={k:pin(N/name) for k,name in contract['source_file_bindings'].items()}
        contract['source_revision']='v2'
        contract['fixed_paths']={k:c[k] for k in ('source_root','run_id','receipt_root','scratch_root','output_root')}
        for stage in ('prepare','run'):contract['future_argv'][stage][6]=str(N/(stage+'_main_c19.actual_owned.py'))
        contract['compiler_closure']['blueprint_ref']=bp
        contract['UUID_adapter']['fixed_run_id']=run_id
        contract['receipt_rules'].update(ordinary_cleanup='Outer guaranteed finally attempts every guard; observation, close, classification and save errors are separately aggregated.',
            original_exception='Exact exception object/chained cause is retained separately from cleanup and publication failures.',
            unknown_Job_closure='Missing, partial, unreadable, drifting or unpinned invocation records cannot establish closed Jobs.',
            publication_failure='No retry or replacement file; preserve partial file and emit full unsaved result where stdout remains writable.')
        contract['fix_origin_handoff_ref']=pin(Q/'HDF.json');contract['fix_origin_manifest_ref']=pin(Q/'MF.json')
        save('root-calling-contract.json',contract)
        inverse=[]
        for name in ('main_c19_runtime.source.py','main_c19_launcher.template.py','main_c19_launcher.source.py',
                     'prepare_main_c19.actual_owned.py','run_main_c19.actual_owned.py','compiler-source-blueprint.json','source.choice.json','root-calling-contract.json'):
            old=(OLD/name).read_bytes();new=(N/name).read_bytes()
            inverse.append(dict(relative=name,original_ref=pin(OLD/name),successor_ref=pin(N/name),
                whole_before_base64=base64.b64encode(old).decode(),whole_after_base64=base64.b64encode(new).decode(),
                successor_path_was_absent=True,old_namespace_never_written=True))
        save('complete-byte-inverse.json',dict(schema='researchos.main-c19-producer-v2-complete-byte-inverse.v1',files=inverse))
        save('fix-origin.json',dict(finding_id='MAIN-C19-PRODUCER-01',decision='REQUEST_CHANGES',
            handoff_ref=pin(Q/'HDF.json'),manifest_ref=pin(Q/'MF.json'),findings_ref=pin(Q/'findings.json'),
            predecessor_handoff_ref=pin(OLD/'HDF.json'),predecessor_manifest_ref=pin(OLD/'MF.json'),
            retained_original_failure952_ref=pin(OLD/'failure952.original-tool-io.json'),root_reported_next_live=953))
        for ref in inputs.values():assert pin(ref['path'])==ref
        save('source-input-pins.original.json',dict(count=len(inputs),refs=list(inputs.values()),Root_seven_and_Canon_excluded=True))
    finally:
        cleanup=guard.close();save('source-preparation.guard.cleanup.actual.json',cleanup)
    assert cleanup['closed'] is True and not cleanup['errors'] and cleanup['retained_handles_count']==0
    print(json.dumps(dict(status='V2_SOURCE_PREPARED',inputs=len(inputs),run_id=run_id,runtime_ref=rp,actual=False)))

if __name__=='__main__':main()
