"""Independent readonly package/receipt verification. Never loads the bundle."""
from datetime import datetime,timezone
import hashlib,json,stat
from pathlib import Path

ROOT=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task')
OUT=ROOT/'product-v1-build-02-independent-readback-20261104'
SUP=ROOT/'product-v1-owned-verification-20261104'
BUNDLE=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-build-20261104/.local/desktop-v1-build-02')
SCOPE=SUP/'scopes/product-v1-build-02.json'
RUN=SUP/'runs/product-v1-build-02'
SCOPE_PIN='ca43c6485097450da435d53cdcc0c6eb1b024f19cdb9668ba2029a1a7633bd9d'
BUNDLE_PIN='716ed8b0f4591ff1cb8e4f5d90975345c6963ebfa5f5d8e6ea9635c4d6ab92cf'
HEAD='7006360ad46ce384993b008fe61878195b74b9bf'
REPARSE=getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def load(p):return json.loads(p.read_bytes())
def canonical(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def save(name,v):
    with (OUT/name).open('xb') as f:f.write(canonical(v))
def regular(p):
    s=p.lstat()
    if p.is_symlink() or s.st_file_attributes&REPARSE or not stat.S_ISREG(s.st_mode):raise ValueError('Nonregular/alias artifact: '+str(p))
    return s
assert not OUT.exists(),'Existing verification result: inspect, do not overwrite'
OUT.mkdir()
try:
    assert sha(SCOPE)==SCOPE_PIN
    assert sha(BUNDLE/'development-manifest.json')==BUNDLE_PIN
    scope=load(SCOPE);manifest=load(BUNDLE/'development-manifest.json');job=load(RUN/'RESULT.json')
    assert scope['scope_id']=='product-v1-build-02' and scope['purpose']=='build'
    assert manifest['schema']=='researchos.desktop-development-tree/1'
    assert manifest['mode']=='DEVELOPMENT_ONLY_BUILT_NOT_NATIVE_TESTED'
    assert Path(manifest['bundle_root'])==BUNDLE and manifest['source']['head']==HEAD
    assert manifest['source']['candidate_delta']==[]
    assert len(manifest['files'])==134
    names=set();checks=[]
    for row in manifest['files']:
        rel=Path(row['path'])
        assert not rel.is_absolute() and '..' not in rel.parts and ':' not in row['path']
        assert row['path'].casefold() not in names;names.add(row['path'].casefold())
        p=BUNDLE/rel;s=regular(p);actual=sha(p)
        assert actual==row['sha256'] and s.st_size==row['bytes'],row['path']
        checks.append({'path':row['path'],'bytes':s.st_size,'sha256':actual})
    actual_names=[]
    for p in BUNDLE.rglob('*'):
        s=p.lstat();assert not p.is_symlink() and not s.st_file_attributes&REPARSE
        if p.is_file():actual_names.append(p.relative_to(BUNDLE).as_posix())
    assert set(actual_names)=={row['path'] for row in manifest['files']}|{'development-manifest.json'}
    assert job['scope_sha256']==SCOPE_PIN and job['scope_id']==scope['scope_id']
    assert job['status']=='COMPLETED_OWNED_JOB_STOPPED' and job['stop_proved'] is True
    for key in ['job_assigned','resumed','root_signaled','job_active_zero']:assert job[key] is True
    for key in ['timed_out','raw_limit_exceeded','input_drift','automatic_retry','resource_ready']:assert job[key] is False
    assert job['errors']==[] and job['root_exit_code']==0 and int(job['creation_filetime'])>0
    assert job['terminate_job_attempts']==job['terminate_original_root_attempts']==0
    assert job['close_order']==['job','thread','process']
    raw_checks=[]
    for row in job['raw']:
        p=RUN/row['file'];assert regular(p).st_size==row['bytes'] and sha(p)==row['sha256']
        raw_checks.append({'path':str(p),'sha256':row['sha256'],'bytes':row['bytes']})
    stdout=json.loads((RUN/'stdout.raw').read_bytes())
    assert stdout['status']=='BUILT_NOT_NATIVE_TESTED' and stdout['manifest_sha256']==BUNDLE_PIN and stdout['files']==134
    assert Path(stdout['output'])==BUNDLE
    assert sha(SUP/'owned_run.py')==scope['controller_sha256']=='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
    cwd=Path(scope['cwd']);extras={'apps/desktop/build-development.py','apps/desktop/build-validator.py','apps/desktop/launch-development.mjs','go.mod','go.sum'}
    scope_checks=[];changed30=[]
    for row in scope['inputs']:
        p=Path(row['path']);actual=sha(p);assert actual==row['sha256'],str(p)
        category='external-tool-or-public-input'
        if p.is_relative_to(cwd):
            relative=p.relative_to(cwd).as_posix()
            category='build-script-or-module' if relative in extras else 'changed-source30'
            if category=='changed-source30':changed30.append({'path':relative,'sha256':actual})
        scope_checks.append({'path':str(p),'sha256':actual,'category':category})
    assert len(changed30)==30
    argv=scope['argv'];receipts=Path(argv[argv.index('--receipts')+1])
    producer=load(receipts/'result.json')
    assert producer['status']=='BUILT_NOT_NATIVE_TESTED' and producer['manifest_sha256']==BUNDLE_PIN
    assert producer['source_acceptance'] is False and producer['source_drift'] is False and producer['public_vendor_drift'] is False
    assert producer['files']==134 and Path(producer['output'])==BUNDLE
    before=load(receipts/'source.before.json');after=load(receipts/'source.after.json')
    assert before==after and before['head']==HEAD and before['tree']==manifest['source']['tree']
    assert before['digest']==manifest['source']['digest']==hashlib.sha256(canonical(before['files'])).hexdigest()
    source_rows={row['path']:row for row in before['files']}
    absent_test_only=[]
    for row in changed30:
        if row['path'] in source_rows:assert row['sha256']==source_rows[row['path']]['sha256']
        else:
            assert row['path'].startswith('tests/ui/')
            absent_test_only.append(row['path'])
    metadata_checks=[]
    pairs=[('core-verifier-go-inputs',manifest['core']['compiled_input_manifest_sha256']),
           ('mu-vendor-5083',manifest['mu']['vendor_5083_manifest_sha256']),
           ('mu-compiled-inputs',manifest['mu']['compiled_input_manifest_sha256'])]
    for name,pin in pairs:
        a=receipts/(name+'.before.json');b=receipts/(name+'.after.json')
        assert sha(a)==pin and load(a)==load(b)
        metadata_checks.append({'before':str(a),'after':str(b),'before_sha256':sha(a),'after_sha256':sha(b),'equal':True})
    external_before=load(receipts/'external-public.before.json');external_after=load(receipts/'external-public.after.json')
    assert external_before==external_after==manifest['mu']['public_main_vendor_inputs']
    install=load(BUNDLE/'apps/desktop/resources/control/runtime-verifier-installation.json')
    assert Path(install['executable'])==BUNDLE/'apps/desktop/resources/control/runtime-verifier.exe'
    assert install['executable_hash']=='sha256:'+manifest['core']['verifier_sha256'] and install['source_commit']==HEAD
    assert sha(Path(install['executable']))==manifest['core']['verifier_sha256']
    descriptor=load(BUNDLE/'apps/desktop/resources/client-wire/descriptor.json')
    assert descriptor['binary_sha256']==manifest['client_wire']['binary_sha256']
    assert descriptor['build_input_digest']==manifest['client_wire']['build_input_digest']
    for row in descriptor['exact_module_source_inventory']:
        p=BUNDLE/'apps/desktop'/row['path'];assert sha(p)==row['sha256']
    meta=load(BUNDLE/'apps/desktop/resources/control/runtime/mu-worker.mjs.build.json')
    assert meta['bundle_sha256']==manifest['mu']['bundle_sha256'] and meta['vendored_files_verified']==5083
    assert meta['source_sha256']==manifest['mu']['worker_sha256']
    save('verified-file-hashes.json',checks)
    save('scope-input-checks.json',scope_checks)
    report={'schema':'researchos.product-v1-independent-build-readback.v1','status':'BUILD_ARTIFACT_VERIFIED_NOT_NATIVE_TESTED',
        'at':datetime.now(timezone.utc).isoformat(),'reviewer':'codex:/root/runtime_readiness','manifest_path':str(BUNDLE/'development-manifest.json'),
        'manifest_sha256':BUNDLE_PIN,'bundle_inventory_files_verified':134,'extra_unlisted_files':0,'reparse_count':0,
        'source_head':HEAD,'source_tree':manifest['source']['tree'],'source_digest':manifest['source']['digest'],'source_candidate_delta':[],
        'scope_sha256':SCOPE_PIN,'scope_input_pins_verified':len(scope_checks),'changed_source_pins_verified':30,
        'source_snapshot_excluded_test_only_but_scope_pinned':absent_test_only,
        'source_before_after_equal':True,'compiled_vendor_metadata_pairs':metadata_checks,'external_public_metadata_equal':True,
        'core_sha256':manifest['core']['sha256'],'verifier_sha256':manifest['core']['verifier_sha256'],
        'client_wire_binary_sha256':manifest['client_wire']['binary_sha256'],'client_wire_descriptor_modules_verified':len(descriptor['exact_module_source_inventory']),
        'React_assets_present':True,'Electron_files':manifest['electron']['file_count'],'Mu_bundle_sha256':manifest['mu']['bundle_sha256'],
        'verifier_absolute_registration_matches_bundle':True,'producer_status':producer['status'],'producer_source_acceptance':False,
        'job_result_sha256':sha(RUN/'RESULT.json'),'job_stop_proved':True,'job_root_exit_code':0,'job_forced_termination_attempts':0,
        'job_timed_out':False,'job_active_zero':True,'job_root_signaled':True,'job_creation_filetime':job['creation_filetime'],
        'job_elapsed_seconds':job['elapsed_seconds'],'job_total_processes_cumulative':job['job_total_processes'],'job_close_order':job['close_order'],
        'job_raw_records_verified':raw_checks,'controller_sha256':scope['controller_sha256'],
        'bounds':'Readonly audit of bundle134, scope pins, source and build metadata/receipts; no rehash of all external Go/Mu source caches or reproducibility rebuild.',
        'Native_or_GUI_validation':False,'runtime_or_model_qualification':False,'business_acceptance':False,
        'artifact_execution':0,'build_replays':0,'GUI_launches':0,'model_calls':0,'old_DB_reads':0,'D_writes':0,'formal_increment':0}
    save('BUILD_ARTIFACT_VERIFIED_NOT_NATIVE_TESTED.json',report)
    print(json.dumps({'status':report['status'],'report_path':str(OUT/'BUILD_ARTIFACT_VERIFIED_NOT_NATIVE_TESTED.json'),
        'report_sha256':sha(OUT/'BUILD_ARTIFACT_VERIFIED_NOT_NATIVE_TESTED.json'),'bundle_files':134,'scope_inputs':len(scope_checks),
        'source30':30,'job_stop_proved':True,'forced_kills':0,'artifact_executions':0}))
except BaseException as e:
    save('VERIFICATION-FAILED.json',{'status':'READBACK_BLOCKED_OR_MISMATCH','type':type(e).__name__,'reason':str(e),
        'artifact_execution':0,'D_writes':0,'no_automatic_retry':True})
    raise
