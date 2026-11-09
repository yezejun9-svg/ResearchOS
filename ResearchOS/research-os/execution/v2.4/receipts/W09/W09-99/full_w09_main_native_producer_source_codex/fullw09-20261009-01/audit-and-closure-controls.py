"""Check bounded original audit bytes and finite compiler parsing without Go."""
import copy, hashlib, json, re, sys, types
from pathlib import Path
sys.dont_write_bytecode=True
N=Path(__file__).resolve().parent
def main():
    m=types.ModuleType('audit_control_runtime');m.__file__=str(N/'full_w09_runtime.source.py')
    exec(compile(Path(m.__file__).read_bytes(),m.__file__,'exec'),m.__dict__)
    rows=[]
    def check(name,ok):
        if not ok:raise AssertionError(name)
        rows.append(dict(name=name,status='PASS'))
    def reject(name,fn,code):
        try:fn()
        except (ValueError,KeyError,TypeError) as exc:check(name,code in str(exc));return
        raise AssertionError(name+' ACCEPTED')
    # Select a real Root tool pair from a bounded tail; no synthetic provenance.
    source=Path(m.ROOT_AUDIT);size=source.stat().st_size
    with source.open('rb') as f:
        header=f.readline();f.seek(max(len(header),size-32*1024*1024))
        if f.tell()!=len(header):f.readline()
        offset=f.tell();tail=f.read(size-offset)
    records=[];cursor=offset
    for line in tail.splitlines(keepends=True):
        try:item=json.loads(line)
        except (ValueError,UnicodeDecodeError):cursor+=len(line);continue
        records.append((cursor,line,item));cursor+=len(line)
    calls={}
    pair=None
    for row in records:
        payload=row[2].get('payload',{});kind=payload.get('type');cid=payload.get('call_id')
        if kind in ('function_call','custom_tool_call') and cid:calls[cid]=row
        elif kind in ('function_call_output','custom_tool_call_output') and cid in calls:
            call=calls[cid]
            found=re.search(rb'(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])',call[1]+row[1])
            if found:pair=(call,row,found.group().decode())
    check('real_Root_tool_pair_observed',pair is not None)
    call,result,binding=pair;raw=header+call[1]+result[1]
    p=N/'real-Root-audit.control.raw.jsonl'
    with p.open('xb') as f:f.write(raw)
    audit=dict(schema='researchos.w09-native-producer.actual-audit.v1',actor_id=m.ROOT_ACTOR,Root_thread_id=m.ROOT_THREAD_ID,
        source_audit_path=m.ROOT_AUDIT,source_line_offsets=[0,call[0],result[0]],original_line_sha256=[hashlib.sha256(v).hexdigest() for v in (header,call[1],result[1])],
        source_prefix_size_observed=size,original_capture_ref=m.pin(p),binding_sha256=binding)
    ar=m.save(N,'real-Root-audit.control.binding.json',audit)
    check('actual_Root_audit_range_positive',m.actual_audit(ar,m.ROOT_ACTOR,binding)==[ar,audit['original_capture_ref']])
    for name,key,value,code in [('wrong_actor','actor_id',m.AUTHOR,'AUDIT_FIXED_ROOT_ACTOR_BINDING'),
        ('wrong_source_log','source_audit_path',str(N/'fake-root-log'),'AUDIT_FIXED_ROOT_ACTOR_BINDING'),
        ('offset_shift','source_line_offsets',[0,call[0]+1,result[0]],'ACTUAL_ROOT_AUDIT_BYTES'),
        ('short_prefix','source_prefix_size_observed',1,'AUDIT_RANGE_DIGEST'),
        ('false_digest','original_line_sha256',['0'*64,*audit['original_line_sha256'][1:]],'AUDIT_RANGE_DIGEST')]:
        bad=copy.deepcopy(audit);bad[key]=value
        original=m.read_ref;fake=dict(path=str(N/'IN_MEMORY_BAD_AUDIT'),sha256='0'*64,bytes=0)
        m.read_ref=lambda ref,bad=bad:json.dumps(bad).encode() if ref==fake else original(ref)
        try:reject('audit_'+name,lambda:m.actual_audit(fake,m.ROOT_ACTOR,binding),code)
        finally:m.read_ref=original
    # A perfectly hashed fabricated record still fails against original Root bytes.
    fabricated=json.loads(call[1]);fabricated['timestamp']='CONTROL_SYNTHETIC_TIME'
    fake_line=(json.dumps(fabricated)+'\n').encode();fake_raw=header+fake_line+result[1]
    fake_cap=dict(path=str(N/'IN_MEMORY_FORGED_CAPTURE'),sha256=hashlib.sha256(fake_raw).hexdigest(),bytes=len(fake_raw))
    bad=dict(audit,original_capture_ref=fake_cap,original_line_sha256=[hashlib.sha256(x).hexdigest() for x in (header,fake_line,result[1])])
    fake_ref=dict(path=str(N/'IN_MEMORY_FORGED_AUDIT'),sha256='0'*64,bytes=0);original=m.read_ref
    m.read_ref=lambda ref:fake_raw if ref==fake_cap else json.dumps(bad).encode() if ref==fake_ref else original(ref)
    try:reject('matching_hashes_do_not_qualify_forged_Root_bytes',lambda:m.actual_audit(fake_ref,m.ROOT_ACTOR,binding),'ACTUAL_ROOT_AUDIT_BYTES')
    finally:m.read_ref=original
    c=m.choice('W09-G01');bp=json.loads(Path(c['compiler_blueprint_ref']['path']).read_bytes())
    # Mock only physical file pins; compiler graph shape is the production function.
    original_pin,original_exact,original_dirs=m.pin,m.exact_path,m.verify_directories
    cache=Path(c['scratch_root'])/'gocache';generated=cache/'generated.go';export=cache/'compiled.a'
    refs={ref['path']:ref for ref in bp['stable_input_refs']}
    refs[str(generated)]=dict(path=str(generated),sha256='1'*64,bytes=1)
    refs[str(export)]=dict(path=str(export),sha256='2'*64,bytes=1)
    m.pin=lambda p:refs[str(p)];m.exact_path=lambda p,*a:Path(p);m.verify_directories=lambda b:None
    packages=[dict(ImportPath=path,Name='main' if path.endswith('.test') else 'retrieval',Dir=str(m.R),Export=str(export),
        CompiledGoFiles=[str(generated)]) for path in bp['required_test_packages']]
    modules=None
    for ref in bp['module_go_mod_refs']:modules=dict(GoMod=ref['path'],Replace=modules)
    packages[0]['Module']=modules
    text=lambda items:'\n'.join(json.dumps(v) for v in items)
    try:
        inv=m.compiler_inventory(text(packages),c,bp)
        check('observed_package_count_is_dynamic',inv['package_count']==6 and len(inv['private_export_refs'])==1 and len(inv['private_generated_input_refs'])==1)
        reject('missing_adapter_test_variant',lambda:m.compiler_inventory(text(packages[1:]),c,bp),'FINITE_TWO_PACKAGE_TEST_CLOSURE')
        reject('duplicate_package_rejected',lambda:m.compiler_inventory(text(packages+[packages[0]]),c,bp),'FINITE_TWO_PACKAGE_TEST_CLOSURE')
        foreign=copy.deepcopy(packages);foreign[-1]['ImportPath']='CONTROL_UNHELD_IMPORT'
        reject('foreign_package_rejected',lambda:m.compiler_inventory(text(foreign),c,bp),'FINITE_TWO_PACKAGE_TEST_CLOSURE')
        wrong=copy.deepcopy(packages);wrong[0]['Error']={'Err':'CONTROL'}
        reject('Go_list_errors_fail_closed',lambda:m.compiler_inventory(text(wrong),c,bp),'GO_LIST_PACKAGE_ERROR')
        missing=copy.deepcopy(packages);missing[0].pop('Module')
        reject('missing_module_manifest_rejected',lambda:m.compiler_inventory(text(missing),c,bp),'EXACT_MODULE_GOMOD_SET')
    finally:m.pin,m.exact_path,m.verify_directories=original_pin,original_exact,original_dirs
    m.save(N,'audit-and-closure-controls.json',dict(status='PASS_SOURCE_ONLY',controls=rows,actual_Root_audit_control_ref=ar,
        actual_Root_audit_is_example_only_not_new_execution_authority=True,compiler_samples='IN_MEMORY_ONLY_PIN_MOCKED_NOT_ACTUAL_GO_LIST',
        actual_Go_runs=0,actual_Native_runs=0,execution_grant=False,formal_case_accepted_delta=0))
    print(json.dumps(dict(status='PASS_SOURCE_ONLY',checks=len(rows),real_Root_audit_range_verified=True,actual_Go_runs=0)))
if __name__=='__main__':main()
