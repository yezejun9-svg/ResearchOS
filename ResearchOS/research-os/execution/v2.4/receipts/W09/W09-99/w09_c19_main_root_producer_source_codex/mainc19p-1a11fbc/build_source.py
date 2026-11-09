"""Build future Main-root producer Source inputs; never execute a producer."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import types
import uuid

R=Path('D:/作品集/ResearchOS/research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
B=R/'execution/v2.4/receipts/W05/W05-99'
N=Path(__file__).resolve().parent
S=W/'w09_c19_caller_v7_source_codex/w09c19r3-1a11f30'
M=W/'main_c19_source_registry_v2_source_codex/Mainv2-1a11fbc'
A=W/'integration_codex/w09c19v7-producer-1a11f30'
AR=W/'w09c19_v7_actual_independent_review_codex/review-37dedbd890c44a93975558f2851d8675'
GP=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
HP=B/'integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py'

def pin(p):
    p=Path(p).resolve(strict=True);raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,v,raw=False):
    data=v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
    with (N/name).open('xb') as f:f.write(data)
    return pin(N/name)
def load(p):return json.loads(Path(p).read_bytes())

def main():
    inputs={}
    def add(ref):
        assert pin(ref['path'])==ref
        key=ref['path'].casefold();assert key not in inputs or inputs[key]==ref;inputs[key]=ref
    def pair(home):
        h=load(home/'HDF.json');add(pin(home/'HDF.json'));add(pin(home/'MF.json'));assert h['manifest_ref']==pin(home/'MF.json')
        for ref in load(home/'MF.json')['members']:add(ref)
        return h
    hs=pair(S);hm=pair(M);ha=pair(AR)
    assert pin(S/'HDF.json')['sha256']=='1ad85d20080d9ad8c0fb5cd4220a04646f3d1a6d2f04296713dbe1b24520e0f3'
    assert pin(M/'HDF.json')['sha256']=='bfcb5010778c27ed4065bc6cda5d963e8f568f2207a413e7b5029b541f0613e7'
    change=load(M/'change-set.json');source=load(S/'source.integration.choice.json')
    for ref in source['sources'].values():add(ref)
    for p in (GP,HP,A/'actual-compiler-input-inventory.json',A/'compiler-input-list.stdout.raw',R/'execution/toolchains/locked.json',R/'execution/project_identity.json',R/'spec/v2.0/PACKAGE_MANIFEST.json'):add(pin(p))
    assert pin(HP)['sha256']=='6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad'
    lock=load(R/'execution/toolchains/locked.json')
    for key in ('python','go','git'):
        add(pin(lock['tools'][key]['path']));assert pin(lock['tools'][key]['path'])['sha256']==lock['tools'][key]['sha256']
    previous=load(A/'actual-compiler-input-inventory.json');assert previous['package_count']==351
    oldroot=Path(hs['fixed_paths']['candidate'])
    bytarget={row['relative']:row['after_target_ref'] for row in change['targets']}
    source21=[]
    for row in change['source21']:
        if row['path'] in bytarget:target=bytarget[row['path']]
        else:target=row['current_ref'];add(target)
        source21.append(target)
    future={}
    generated=[]
    def expect(ref):
        p=Path(ref['path'])
        if p.is_relative_to(oldroot):
            rel=p.relative_to(oldroot).as_posix();target=bytarget.get(rel,{**ref,'path':str(R/rel)})
            if rel not in bytarget:add(target)
            future[target['path']]=target
        elif p.is_relative_to(R/'.local/gocache'):
            generated.append(ref)
        else:add(ref);future[ref['path']]=ref
    for ref in previous['build_inputs']+previous['product_inventory']+previous['compiler_tool_refs']:expect(ref)
    text=(A/'compiler-input-list.stdout.raw').read_text(encoding='utf-8')
    decoder=json.JSONDecoder();pos=0;packages=[];gomods={}
    while pos<len(text):
        while pos<len(text) and text[pos].isspace():pos+=1
        if pos==len(text):break
        pkg,pos=decoder.raw_decode(text,pos);packages.append(pkg)
        m=pkg.get('Module')
        while m:
            if m.get('GoMod'):
                p=Path(m['GoMod']);p=R/p.relative_to(oldroot) if p.is_relative_to(oldroot) else p
                ref=pin(p);add(ref);gomods[ref['path']]=ref;future[ref['path']]=ref
            m=m.get('Replace')
    assert len(packages)==351 and [p.get('ImportPath') for p in packages]==previous['packages']
    driver=ast.parse(Path(source['sources']['ops/ci/retrieval.py']['path']).read_bytes())
    attrs=[n for n in ast.walk(driver) if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='uuid']
    assert len(attrs)==1 and attrs[0].attr=='uuid4'
    assert any(isinstance(n,ast.Call) and n.func is attrs[0] and not n.args and not n.keywords for n in ast.walk(driver))
    gm=types.ModuleType('main_c19_source_guard');gm.__file__=str(GP);exec(compile(GP.read_bytes(),str(GP),'exec'),gm.__dict__)
    guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
    try:
        guard.acquire(list(inputs.values()))
        run_id=uuid.uuid4().hex
        actual=N/'actual-main-root';scratch=R/'.local'/('w09-c19-main-'+run_id);output=R/'execution/receipts/W09/retrieval'/('run-'+run_id)
        assert not actual.exists() and not scratch.exists() and not output.exists()
        blueprint=save('compiler-source-blueprint.json',dict(schema='researchos.w09-main-c19-compiler-blueprint.v1',
            metadata_only_not_previous_Native_acceptance=True,metadata_origin_refs=[pin(A/'actual-compiler-input-inventory.json'),pin(A/'compiler-input-list.stdout.raw')],
            package_count=351,package_roster=previous['packages'],stable_input_refs=sorted(future.values(),key=lambda r:r['path']),
            module_go_mod_refs=list(gomods.values()),historical_generated_cache_entries=len(generated),
            generated_cache_policy='Only actual fresh private GOCACHE generated inputs; old cache files are never runtime inputs.',
            expected_source21=source21))
        choice=dict(schema='researchos.w09-main-c19-producer-source-choice.v1',actor_id='codex:/root/command_queue_impl',
            source_root=str(R),run_id=run_id,receipt_root=str(actual),scratch_root=str(scratch),output_root=str(output),
            selected_tests=['TestW09C19ChainInvalidation','TestW09C19ExplicitOriginAndUnknown'],expected_native_ids=['C19-01','C19-02','C19-03','C19-04','C19-05'],
            source21=source21,main_seven_after_refs=[row['after_target_ref'] for row in change['targets']],
            sealed_six_source_refs=source['sources'],compiler_blueprint_ref=blueprint,
            producer_r3_handoff_ref=pin(S/'HDF.json'),producer_r3_manifest_ref=pin(S/'MF.json'),
            adoption_source_handoff_ref=pin(M/'HDF.json'),adoption_source_manifest_ref=pin(M/'MF.json'),
            adoption_source_contract_ref=pin(M/'root-calling-contract.json'),adoption_source_change_set_ref=pin(M/'change-set.json'),
            future_adoption_outcome_path=str(M/'actual-adoption/outcome.json'),
            guard_ref=pin(GP),owned_job_ref=pin(HP),toolchain_ref=pin(R/'execution/toolchains/locked.json'),
            tool_refs={k:pin(lock['tools'][k]['path']) for k in ('python','go','git')},
            identity_ref=pin(R/'execution/project_identity.json'),spec_manifest_ref=pin(R/'spec/v2.0/PACKAGE_MANIFEST.json'),
            expected_git_head='adc460c2138528f163f7fdab5e8d81dde157b7fb',
            list_timeout_seconds=240,producer_timeout_seconds=420,inner_Go_timeout_seconds=180,
            list_argv_suffix=['list','-test','-deps','-compiled','-export','-json','./internal/domain'],
            source_only=True,execution_grant=False,actual_Main_producer=False,formal_case_accepted_delta=0)
        save('source.choice.json',choice)
        save('source-input-pins.original.json',dict(count=len(inputs),refs=list(inputs.values()),
            future_Main_paths_not_assumed_present=True,all_missing_Main_members_represented_by_sealed_sources=True))
        for ref in inputs.values():assert pin(ref['path'])==ref
    finally:
        cleanup=guard.close();save('source-preparation.guard.cleanup.actual.json',cleanup)
    assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
    print(json.dumps(dict(status='SOURCE_INPUTS_PREPARED',inputs=len(inputs),run_id=run_id,stable_compiler_refs=len(future),module_GoMod_refs=len(gomods),actual=False)))

if __name__=='__main__':main()
