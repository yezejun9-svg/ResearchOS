import hashlib,json,pathlib,stat,subprocess,sys
E=pathlib.Path(__file__).parent
A=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/desktop_main7d_native_codex/20261025-current-chat/complete-tree/build-01')
W=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/desktop-main7d-native-20261025')
B=W/'.local/desktop-complete-20261025-01'
C=pathlib.Path('D:/作品集/ResearchOS/research-os')
EXPECTED='288ac604fbcc09b11d04148c970df8830c59d1352431832b06640e30fbf82a3e'
def sha(p):
    h=hashlib.sha256()
    with pathlib.Path(p).open('rb') as f:
        while b:=f.read(8*1024*1024):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_bytes())
def verify(rows):
    assert len({str(pathlib.Path(r['path'])).lower() for r in rows})==len(rows)
    for row in rows:
        p=pathlib.Path(row['path']);info=p.lstat()
        assert p.is_file() and not p.is_symlink() and not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT,str(p)
        assert info.st_size==row['bytes'] and sha(p)==row['sha256'],str(p)
    return {'files':len(rows),'bytes':sum(r['bytes'] for r in rows)}
assert sha(B/'development-manifest.json')==EXPECTED
assert (B/'development-manifest.json').read_bytes()==(A/'development-manifest.json').read_bytes()
manifest=read(B/'development-manifest.json');outcome=read(A/'result.json')
assert outcome['manifest_sha256']==EXPECTED and outcome['status']=='BUILT_NOT_NATIVE_TESTED'
assert outcome['source_drift'] is False and outcome['public_vendor_drift'] is False
freeze=read(E/'r2-fixed-inputs/source-freeze-02.json')
source=read(A/'source.before.json')
assert source==read(A/'source.after.json')==read(E/'r2-fixed-inputs/build-source.before.json')
assert manifest['source']['head']==freeze['base_commit'] and manifest['source']['tree']==freeze['base_tree']
assert manifest['source']['digest']==freeze['source_snapshot_digest'] and manifest['source']['candidate_delta']==freeze['candidate_delta']
assert manifest['source']['seven_scoped_source_sha256']=={name:row['sha256'] for name,row in freeze['seven_file_hashes'].items()}
source_stats=verify([{**r,'path':str(W/r['path'])} for r in source['files']])
names=[r['path'] for r in manifest['files']]
assert names==sorted(names) and len(names)==132
actual={p.relative_to(B).as_posix() for p in B.rglob('*') if p.is_file()}-{'development-manifest.json'}
assert actual==set(names)
bundle_stats=verify([{**r,'path':str(B/r['path'])} for r in manifest['files']])
assert manifest['electron']['file_count']==75
electron=[r for r in manifest['files'] if r['path'].startswith('runtime/electron/')]
assert len(electron)==75
for row in electron:
    p=pathlib.Path(manifest['electron']['source_dist'])/row['path'].removeprefix('runtime/electron/')
    assert sha(p)==row['sha256']
source_by={r['path']:r for r in source['files']}
migrations=[r for r in manifest['files'] if r['path'].startswith('migrations/sqlite/')]
assert len(migrations)==manifest['core']['migration_count']==25
for row in migrations:
    assert row['sha256']==source_by[row['path']]['sha256']
for relative in manifest['core']['cwd_contracts']:
    assert sha(B/relative)==source_by[relative]['sha256']
for relative, scoped in [('launch-development.mjs','apps/desktop/launch-development.mjs'),('tools/build-development.py','apps/desktop/build-development.py'),('apps/desktop/main/main.js','apps/desktop/main/main.js')]:
    assert sha(B/relative)==freeze['seven_file_hashes'][scoped]['sha256']
print('Bundle/source byte bindings verified',flush=True)
closure_stats={};refs={}
for label in ['core-verifier-go-inputs','mu-vendor-5083','mu-compiled-inputs','external-public']:
    first=read(A/(label+'.before.json'));second=read(A/(label+'.after.json'))
    assert first==second,label
    rows=first if isinstance(first,list) else list(first.values()) if label=='external-public' else first['files']
    closure_stats[label]=verify(rows)
    refs[label]=sha(A/(label+'.before.json'))
    print(label,closure_stats[label],flush=True)
assert refs['core-verifier-go-inputs']==manifest['core']['compiled_input_manifest_sha256']
assert refs['mu-vendor-5083']==manifest['mu']['vendor_5083_manifest_sha256']
assert refs['mu-compiled-inputs']==manifest['mu']['compiled_input_manifest_sha256']
assert closure_stats['mu-vendor-5083']['files']==5083
# Independently derive selected Go source fields from the retained go-list output.
def stream(raw):
    decoder=json.JSONDecoder();pos=0
    while pos<len(raw):
        while pos<len(raw) and raw[pos].isspace():pos+=1
        if pos==len(raw):break
        value,pos=decoder.raw_decode(raw,pos);yield value
expected_go=set();package_count=0
for kind in ['core','verifier']:
    for package in stream((A/f'commands/{kind}-go-list/stdout.raw').read_text(encoding='utf-8')):
        package_count+=1;directory=pathlib.Path(package['Dir'])
        for key in ['GoFiles','CompiledGoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','EmbedFiles']:
            for name in package.get(key,[]):
                p=pathlib.Path(name);expected_go.add(str((p if p.is_absolute() else directory/p).resolve()).lower())
        module=package.get('Module') or {}
        if module.get('GoMod'):expected_go.add(str(pathlib.Path(module['GoMod']).resolve()).lower())
goroot=pathlib.Path(manifest['tools']['go']['path']).parent.parent
expected_go.update(str(p.resolve()).lower() for p in (goroot/'pkg/tool/windows_amd64').glob('*.exe'))
expected_go.update(str((goroot/p).resolve()).lower() for p in ['go.env','VERSION'] if (goroot/p).is_file())
go=read(A/'core-verifier-go-inputs.before.json')
assert package_count==go['package_count']==manifest['core']['go_package_count']
assert expected_go=={str(pathlib.Path(r['path']).resolve()).lower() for r in go['files']}
vendor=read(C/'third_party/mu.MANIFEST.json')
actual_vendor=read(A/'mu-vendor-5083.before.json')
assert vendor['files']==len(vendor['entries'])==len(actual_vendor)==5083
assert {str((C/p).resolve()).lower():(r['sha256'],r['size']) for p,r in vendor['entries'].items()}=={str(pathlib.Path(r['path']).resolve()).lower():(r['sha256'],r['bytes']) for r in actual_vendor}
mu=read(A/'commands/mu-compiled-inputs/stdout.raw')
assert mu['output_sha256']==manifest['mu']['bundle_sha256'] and mu['esbuild_version']=='0.28.2'
assert len(mu['inputs'])==manifest['mu']['compiled_input_count']
actual_mu={str(pathlib.Path(r['path']).resolve()).lower() for r in read(A/'mu-compiled-inputs.before.json')['files']}
expected_mu={str(pathlib.Path(p).resolve()).lower() for p in mu['inputs']}
for package in ['esbuild','@esbuild/win32-x64']:
    expected_mu.update(str(p.resolve()).lower() for p in (C/'third_party/mu/node_modules'/package).rglob('*') if p.is_file())
assert expected_mu==actual_mu
# Verify the baseline validator's recorded digest, no-drift result and every actual input byte.
client=A/'client-wire-builder'
inputs=read(client/'inputs.before.json');after=read(client/'inputs.after.json');client_result=read(client/'result.json')
assert client_result['status']=='BUILT_NOT_TESTED' and client_result['drift']==[]
assert all(r['sha256']==r['current_sha256'] for r in after) and len(after)==len(inputs)
assert hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()==manifest['client_wire']['build_input_digest']
closure_stats['client-wire-all-inputs']=verify(inputs)
descriptor=read(B/'apps/desktop/resources/client-wire/descriptor.json')
for row in descriptor['exact_module_source_inventory']:
    assert sha(B/'apps/desktop'/row['path'])==row['sha256']
for row in descriptor['compiled_React_asset_inventory']:
    assert sha(B/'apps/web/dist'/row['path'])==row['sha256']
commands={}
for path in (A/'commands').iterdir():
    result=read(path/'result.json');recipe=read(path/'recipe.json')
    assert result['native_exit']==0,path.name
    assert sha(path/'stdout.raw')==result['stdout_sha256'] and sha(path/'stderr.raw')==result['stderr_sha256']
    commands[path.name]={'native_exit':0,'recipe_sha256':sha(path/'recipe.json'),'result_sha256':sha(path/'result.json')}
assert set(commands)=={'core-go-list','verifier-go-list','mu-source-build','mu-compiled-inputs','client-wire-source-build','core-go-build','verifier-go-build'}
for row in client_result['invocations']:
    assert row['exit']==0
assert sha(B/'development-manifest.json')==EXPECTED
summary={'status':'R2_SOURCE_BUILD_BYTES_VERIFIED_NOT_NATIVE_ACCEPTED','manifest_sha256':EXPECTED,'source':source_stats,'bundle':bundle_stats,'electron_files':75,'migrations':25,'closures':closure_stats,'closure_manifests':refs,'go_package_count':package_count,'mu_compiled_input_count':len(mu['inputs']),'commands':commands,'native_gui_or_core_starts':0}
(E/'R2-build-independent-check.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
fixed=E/'r2-build-fixed-inputs';fixed.mkdir(exist_ok=False)
for name in ['result.json','development-manifest.json','source.before.json','source.after.json']+[label+ending+'.json' for label in ['core-verifier-go-inputs','mu-vendor-5083','mu-compiled-inputs','external-public'] for ending in ['.before','.after']]:
    with (fixed/name).open('xb') as out:out.write((A/name).read_bytes())
print(json.dumps(summary),flush=True)
