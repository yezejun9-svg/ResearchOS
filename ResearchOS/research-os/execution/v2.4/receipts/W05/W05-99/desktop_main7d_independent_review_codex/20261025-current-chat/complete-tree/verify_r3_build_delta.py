import hashlib,json,pathlib,stat
E=pathlib.Path(__file__).parent
A=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/desktop_main7d_native_codex/20261025-current-chat/complete-tree/build-02')
W=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/desktop-main7d-native-20261025')
EXPECTED='e1d61b68d12c61e2dda341df3541d2b4b541b9c2331af5da26ca56dff759b620'
def read(p):return json.loads(pathlib.Path(p).read_bytes())
def sha(p):
    h=hashlib.sha256()
    with pathlib.Path(p).open('rb') as f:
        while b:=f.read(8*1024*1024):h.update(b)
    return h.hexdigest()
def check(row,path=None):
    p=pathlib.Path(path or row['path']);st=p.lstat()
    assert p.is_file() and not p.is_symlink() and not st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
    assert st.st_size==row['bytes'] and sha(p)==row['sha256'],str(p)
result=read(A/'result.json');B=pathlib.Path(result['output'])
assert B.is_relative_to(W/'.local') and B.name=='desktop-complete-20261025-02'
assert result['manifest_sha256']==sha(B/'development-manifest.json')==EXPECTED
assert result['status']=='BUILT_NOT_NATIVE_TESTED' and result['source_drift'] is False and result['public_vendor_drift'] is False
manifest=read(B/'development-manifest.json');freeze=read(E/'r3-fixed-inputs/SOURCE-FREEZE-03.json')
source=read(A/'source.before.json');assert source==read(A/'source.after.json')
assert source['digest']==freeze['source_snapshot_digest']==manifest['source']['digest']
assert hashlib.sha256((json.dumps(source['files'],sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()).hexdigest()==source['digest']
assert source['head']==freeze['base_commit']==manifest['source']['head'] and source['tree']==freeze['base_tree']==manifest['source']['tree']
old=read(E/'r2-build-fixed-inputs/source.before.json')
oldrows={r['path']:r for r in old['files']};newrows={r['path']:r for r in source['files']}
assert oldrows.keys()==newrows.keys() and len(newrows)==591
changed=[p for p,r in newrows.items() if r!=oldrows[p]]
assert sorted(changed)==['apps/desktop/launch-development.mjs','tests/ui/desktop/development-launcher.test.mjs']
for p,r in freeze['seven_file_hashes'].items():check(r,W/p)
assert manifest['source']['seven_scoped_source_sha256']=={p:r['sha256'] for p,r in freeze['seven_file_hashes'].items()}
assert source['candidate_delta']==manifest['source']['candidate_delta']==freeze['candidate_delta']
names=[r['path'] for r in manifest['files']]
assert len(names)==132 and names==sorted(set(names))
assert set(names)=={p.relative_to(B).as_posix() for p in B.rglob('*') if p.is_file()}-{'development-manifest.json'}
for r in manifest['files']:check(r,B/r['path'])
assert sha(B/'launch-development.mjs')==freeze['seven_file_hashes']['apps/desktop/launch-development.mjs']['sha256']
assert sha(B/'tools/build-development.py')==freeze['seven_file_hashes']['apps/desktop/build-development.py']['sha256']
oldmanifest=read(E/'r2-build-fixed-inputs/development-manifest.json')
oldout={r['path']:r for r in oldmanifest['files']};newout={r['path']:r for r in manifest['files']}
assert oldout.keys()==newout.keys()
output_changed=[p for p,r in newout.items() if r!=oldout[p]]
assert set(output_changed)=={'launch-development.mjs','apps/desktop/resources/control/runtime-verifier-installation.json','apps/desktop/resources/client-wire/descriptor.json','apps/desktop/resources/client-wire/researchos-client-wire-validator.exe'},output_changed
assert manifest['core']['migration_count']==25 and manifest['electron']['file_count']==75
reused={}
for label in ['core-verifier-go-inputs','mu-vendor-5083','mu-compiled-inputs','external-public']:
    before=read(A/(label+'.before.json'));after=read(A/(label+'.after.json'))
    assert before==after==read(E/'r2-build-fixed-inputs'/(label+'.before.json')),label
    reused[label]={'new_before_sha256':sha(A/(label+'.before.json')),'new_after_sha256':sha(A/(label+'.after.json')),'identical_to_r2_independently_verified_input_manifest':True}
# All output bytes were read again. Unchanged source/input byte evidence is reused
# only after exact new before/after manifests match the independently checked r2 set.
client=A/'client-wire-builder';inputs=read(client/'inputs.before.json');after=read(client/'inputs.after.json')
oldclient=A.parent/'build-01/client-wire-builder';oldinputs=read(oldclient/'inputs.before.json')
assert len(inputs)==len(oldinputs)==6451
by={r['path']:r for r in inputs};oldby={r['path']:r for r in oldinputs}
changed_inputs=[p for p in by.keys()&oldby.keys() if by[p]!=oldby[p]]
assert changed_inputs==[str(W/'tests/ui/desktop/development-launcher.test.mjs')],changed_inputs
new_paths=by.keys()-oldby.keys();old_paths=oldby.keys()-by.keys()
assert len(new_paths)==len(old_paths)==1
new_fixture=next(iter(new_paths));old_fixture=next(iter(old_paths))
assert pathlib.Path(new_fixture).is_relative_to(W/'.local') and pathlib.Path(new_fixture).as_posix().endswith('/fixtures/negative-child.go')
assert (by[new_fixture]['sha256'],by[new_fixture]['bytes'])==(oldby[old_fixture]['sha256'],oldby[old_fixture]['bytes'])
for p in changed_inputs+list(new_paths):check(by[p])
assert len(after)==len(inputs) and all(r['sha256']==r['current_sha256'] for r in after)
assert [{k:v for k,v in r.items() if k!='current_sha256'} for r in after]==inputs
bound=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert bound==manifest['client_wire']['build_input_digest']
desc=read(B/'apps/desktop/resources/client-wire/descriptor.json')
assert desc['build_input_digest']==bound and desc['binary_sha256']==sha(B/'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe')
for r in desc['exact_module_source_inventory']:assert sha(B/'apps/desktop'/r['path'])==r['sha256']
for r in desc['compiled_React_asset_inventory']:assert sha(B/'apps/web/dist'/r['path'])==r['sha256']
commands={}
for p in (A/'commands').iterdir():
    value=read(p/'result.json');assert value['native_exit']==0
    assert value['stdout_sha256']==sha(p/'stdout.raw') and value['stderr_sha256']==sha(p/'stderr.raw')
    commands[p.name]={'native_exit':0,'result_sha256':sha(p/'result.json'),'recipe_sha256':sha(p/'recipe.json')}
assert len(commands)==7
clientresult=read(client/'result.json');assert clientresult['drift']==[] and all(r['exit']==0 for r in clientresult['invocations'])
assert (A/'development-manifest.json').read_bytes()==(B/'development-manifest.json').read_bytes()
fixed=E/'r3-build-fixed-inputs';fixed.mkdir(exist_ok=False)
for name in ['result.json','development-manifest.json','source.before.json','source.after.json']+[label+ending+'.json' for label in reused for ending in ['.before','.after']]:
    with (fixed/name).open('xb') as f:f.write((A/name).read_bytes())
summary={'status':'R3_SOURCE_BUILD_DELTA_VERIFIED_NOT_NATIVE_ACCEPTED','manifest_sha256':EXPECTED,'bundle':str(B),'source_digest':source['digest'],'source_changes_since_r2':changed,'actual_bundle_files_verified':len(names),'actual_bundle_bytes_verified':sum(r['bytes'] for r in manifest['files']),'output_changes_since_r2':output_changed,'unchanged_closures_reused':reused,'changed_client_inputs_verified':changed_inputs,'relocated_identical_fixture_input':new_fixture,'commands':commands,'native_gui_or_core_starts':0}
(E/'R3-build-delta-independent-check.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary))
