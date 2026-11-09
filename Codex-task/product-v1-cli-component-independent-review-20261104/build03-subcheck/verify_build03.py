"""Read/hash only: never imports or runs any build03 artifact."""
from datetime import datetime,timezone
import hashlib,json,os,stat
from pathlib import Path,PurePosixPath

HERE=Path(__file__).resolve().parent
BUNDLE=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-build-03-20261104/.local/desktop-v1-build-03')
OWNED=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-owned-verification-20261104')
SCOPE=OWNED/'scopes/product-v1-build-03.json'
RESULT=OWNED/'runs/product-v1-build-03/RESULT.json'
REPORT=HERE/'report.json'
REPARSE=0x400

def digest(path):
    before=path.stat()
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda:stream.read(1024*1024),b''):h.update(part)
    after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('file changed while hashing: '+str(path))
    return h.hexdigest(),after.st_size

def no_alias(path):
    path=path.absolute()
    for item in reversed((path,*path.parents)):
        st=item.lstat()
        if stat.S_ISLNK(st.st_mode) or getattr(st,'st_file_attributes',0)&REPARSE:raise ValueError('reparse/alias refused: '+str(item))
    if os.path.normcase(os.path.realpath(path))!=os.path.normcase(str(path)):raise ValueError('resolved alias refused: '+str(path))

assert not REPORT.exists(),'Existing report: inspect; do not replay verification'
no_alias(BUNDLE)
manifest_path=BUNDLE/'development-manifest.json'
no_alias(manifest_path)
manifest_pin,_=digest(manifest_path)
manifest=json.loads(manifest_path.read_bytes())
scope=json.loads(SCOPE.read_bytes())
result=json.loads(RESULT.read_bytes())
errors=[];expected={};total_bytes=0;files_checked=[]
for row in manifest['files']:
    rel=row['path'];p=PurePosixPath(rel)
    if (not isinstance(rel,str) or not rel or p.is_absolute() or '\\' in rel or ':' in rel or
        any(part in ('','.','..') for part in rel.split('/')) or p.as_posix()!=rel or rel=='development-manifest.json'):
        raise ValueError('invalid manifest path: '+str(rel))
    folded=rel.casefold()
    if folded in expected:raise ValueError('manifest path duplicate/case alias: '+rel)
    expected[folded]=rel
    file=BUNDLE.joinpath(*p.parts);no_alias(file)
    if not file.is_file():raise ValueError('not regular file: '+rel)
    pin,size=digest(file);total_bytes+=size
    ok=pin==row['sha256'] and size==row['bytes']
    if not ok:errors.append({'kind':'BUNDLE_PIN_MISMATCH','path':rel})
    files_checked.append({'path':rel,'sha256':pin,'bytes':size,'matches':ok})
actual=[];aliases=[];todo=[BUNDLE]
while todo:
    current=todo.pop()
    with os.scandir(current) as entries:
        for item in entries:
            st=item.stat(follow_symlinks=False)
            if stat.S_ISLNK(st.st_mode) or getattr(st,'st_file_attributes',0)&REPARSE:
                aliases.append(str(item.path));continue
            path=Path(item.path)
            if stat.S_ISDIR(st.st_mode):todo.append(path)
            elif stat.S_ISREG(st.st_mode):
                rel=path.relative_to(BUNDLE).as_posix()
                if rel!='development-manifest.json':actual.append(rel)
            else:errors.append({'kind':'NONREGULAR_ENTRY','path':str(path)})
actual_fold=[name.casefold() for name in actual]
if len(actual_fold)!=len(set(actual_fold)):errors.append({'kind':'ACTUAL_CASE_ALIAS'})
missing=sorted(set(expected)-set(actual_fold));extra=sorted(set(actual_fold)-set(expected))
if missing or extra or aliases:errors.append({'kind':'INVENTORY_MISMATCH','missing':missing,'extra':extra,'aliases':aliases})

inputs=[]
for row in scope['inputs']:
    path=Path(row['path'])
    # Scope declares only public source/build resources. Refuse unexpected
    # credential/key/database paths rather than opening them for a hash.
    lowered=[part.casefold() for part in path.parts]
    if path.suffix.casefold() in ('.db','.sqlite','.sqlite3','.key','.pem') or any(part in ('.aws','.codex','.ssh') for part in lowered) or path.name.casefold() in ('session.json','credentials.json','token.json'):
        raise ValueError('credential/database input refused: '+str(path))
    no_alias(path)
    pin,size=digest(path);ok=pin==row['sha256']
    if not ok:errors.append({'kind':'SCOPE_INPUT_DRIFT','path':str(path)})
    inputs.append({'path':str(path),'sha256':pin,'bytes':size,'matches':ok})

core=BUNDLE/'apps/desktop/resources/control'
installation=json.loads((core/'runtime-verifier-installation.json').read_bytes())
mu=json.loads((core/'runtime/mu-worker.mjs.build.json').read_bytes())
client=json.loads((BUNDLE/'apps/desktop/resources/client-wire/descriptor.json').read_bytes())
rowmap={r['path']:r for r in files_checked}
def file_sha(rel):return rowmap[rel]['sha256']
bindings={
 'bundle_root':os.path.normcase(str(BUNDLE))==os.path.normcase(manifest.get('bundle_root','')),
 'verifier_path':installation.get('executable')==str(core/'runtime-verifier.exe'),
 'verifier_sha':installation.get('executable_hash')=='sha256:'+file_sha('apps/desktop/resources/control/runtime-verifier.exe'),
 'verifier_source_commit':installation.get('source_commit')==manifest.get('source',{}).get('head'),
 'core_sha':manifest.get('core',{}).get('sha256')==file_sha('apps/desktop/resources/control/researchos-control.exe'),
 'manifest_verifier_sha':manifest.get('core',{}).get('verifier_sha256')==file_sha('apps/desktop/resources/control/runtime-verifier.exe'),
 'mu_sha':mu.get('bundle_sha256')==file_sha('apps/desktop/resources/control/runtime/mu-worker.mjs'),
 'manifest_mu_sha':manifest.get('mu',{}).get('bundle_sha256')==file_sha('apps/desktop/resources/control/runtime/mu-worker.mjs'),
 'client_sha':client.get('binary_sha256')==file_sha('apps/desktop/resources/client-wire/researchos-client-wire-validator.exe'),
 'client_input':client.get('build_input_digest')==manifest.get('client_wire',{}).get('build_input_digest'),
 'electron_sha':manifest.get('tools',{}).get('electron',{}).get('sha256')==file_sha('runtime/electron/electron.exe'),
}
if not all(bindings.values()):errors.append({'kind':'METADATA_BINDING_MISMATCH','failed':[key for key,v in bindings.items() if not v]})
scope_pin,_=digest(SCOPE);result_pin,_=digest(RESULT)
stop={key:result.get(key) for key in ['status','job_assigned','resumed','timed_out','raw_limit_exceeded','terminate_job_attempts','terminate_original_root_attempts','job_total_processes','root_signaled','job_active_zero','root_exit_code','stop_proved','input_drift','automatic_retry','resource_ready','formal_increment','scope_id','scope_sha256','close_order']}
if result.get('scope_sha256')!=scope_pin:errors.append({'kind':'RESULT_SCOPE_BINDING_MISMATCH'})
report={'schema':'researchos.build03-independent-readonly-subcheck.v1','at':datetime.now(timezone.utc).isoformat(),
 'status':'READONLY_HASH_INVENTORY_MATCH' if not errors else 'READONLY_CHECK_FAILED',
 'bundle':str(BUNDLE),'development_manifest_sha256':manifest_pin,'manifest_file_count':len(manifest['files']),
 'actual_file_count_excluding_manifest':len(actual),'logical_bytes':total_bytes,'missing':missing,'extra':extra,
 'reparse_or_alias_count':len(aliases),'scope_sha256':scope_pin,'scope_input_count':len(inputs),'result_sha256':result_pin,
 'source':manifest.get('source'),'mode':manifest.get('mode'),'manifest_schema':manifest.get('schema'),
 'client_wire':manifest.get('client_wire'),'core':manifest.get('core'),
 'mu_summary':{key:manifest.get('mu',{}).get(key) for key in ['producer','producer_sha256','worker_sha256','metadata_sha256','bundle_sha256','vendored_files_verified','compiled_input_count']},
 'electron':manifest.get('electron'),'metadata_bindings':bindings,'supervisor_result_summary':stop,
 'files_checked':files_checked,'inputs_checked':inputs,'errors':errors,
 'limits':'Independent static inventory/input readback only; no artifact run, compiler/build, GUI, Native, model, credential or old DB access. Supervisor result is a recorded prior observation, not a fresh process observation.',
 'artifact_runs':0,'builds':0,'GUI':0,'Native':0,'model':0,'D_writes':0,'formal_increment':0}
with REPORT.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
report_pin,_=digest(REPORT)
print(json.dumps({'status':report['status'],'manifest_file_count':len(manifest['files']),'actual_file_count':len(actual),'scope_inputs':len(inputs),'input_mismatches':sum(not i['matches'] for i in inputs),'bundle_mismatches':sum(not i['matches'] for i in files_checked),'reparse_or_alias_count':len(aliases),'errors':errors,'report':str(REPORT),'report_sha256':report_pin,'development_manifest_sha256':manifest_pin,'scope_sha256':scope_pin,'result_sha256':result_pin,'source':manifest.get('source'),'mode':manifest.get('mode'),'supervisor_result_summary':stop},ensure_ascii=False,indent=2))
raise SystemExit(0 if not errors else 1)
