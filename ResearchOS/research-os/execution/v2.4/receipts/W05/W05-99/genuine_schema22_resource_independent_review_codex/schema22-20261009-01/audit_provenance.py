from pathlib import Path
import json, hashlib, io, tarfile, subprocess, types, re, ntpath, struct
B=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99')
O=Path(__file__).resolve().parent
P=B/'genuine_release_resource_inventory_codex/release-resource-20261009-01'
def exact(p):
    p=Path(p); raw=p.read_bytes()
    return {'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,obj):
    p=O/name
    if p.exists(): raise RuntimeError('refusing to replace '+name)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return exact(p)
def key(p): return ntpath.normcase(ntpath.normpath(str(p)))
inv=json.loads((P/'inventory.json').read_bytes())
resource=next(x for x in inv['resources'] if x['id']=='SCHEMA22_FROZEN_PROGRAM_AND_SOURCE')
old=Path(resource['program_refs'][0]['path']).parent
frozen=old/'frozen_source'
before=json.loads((old/'source_before.json').read_bytes())
after=json.loads((old/'source_after.json').read_bytes())
gs=json.loads((old/'git_source.json').read_bytes())
build=json.loads((old/'old22-control.exe.build.invocation.json').read_bytes())
original=Path(build['cwd'])
original_dir=original.parent
rvref=inv['input_review_ref']
rv=json.loads(Path(rvref['path']).read_bytes())
gr=next(r for r in rv['basis_refs'] if r['path'].endswith('source_read_guard.py'))
graw=Path(gr['path']).read_bytes()
assert hashlib.sha256(graw).hexdigest()==gr['sha256'] and len(graw)==gr['bytes']
mod=types.ModuleType('schema22_provenance_guard')
exec(compile(graw,gr['path'],'exec'),mod.__dict__)
refs={}
roles={}
def add(r,role):
    assert set(r)=={'path','sha256','bytes'}
    k=key(r['path'])
    if k in refs: assert refs[k]['sha256']==r['sha256'] and refs[k]['bytes']==r['bytes']
    else: refs[k]=r
    roles.setdefault(k,[]).append(role)
for p in [P/'HDF.json',P/'MF.json',P/'inventory.json']: add(exact(p),'accepted-inventory')
add(rvref,'source-roster-review')
add(gr,'SourceReadGuard')
for r in resource['program_refs']: add(r,'current-program')
for r in resource['selected_sql_contract_metadata_refs']: add(r,'registered-resource')
small_names=['build.py','environment.json','git-archive.invocation.json','git-archive.stdout','git-archive.stderr','go-list.invocation.json','go-list.stdout','go-list.stderr','old22-control.exe.build.invocation.json','old22-control.exe.build.stdout','old22-control.exe.build.stderr','old22-backup.exe.build.invocation.json','old22-backup.exe.build.stdout','old22-backup.exe.build.stderr','result.json','source_before.json','source_after.json','git_source.json']
for name in small_names: add(exact(old/name),'original-build-record-copy')
for path,sha in before.items(): add({'path':path,'sha256':sha,'bytes':Path(path).stat().st_size},'original-compile-input')
for rel,sha in gs['files'].items():
    for root,role in [(original,'original-git-source'),(frozen,'relocated-git-source')]:
        p=root/rel;add({'path':p.as_posix(),'sha256':sha,'bytes':p.stat().st_size},role)
for r in resource['program_refs']:
    p=original_dir/Path(r['path']).name
    add({'path':p.as_posix(),'sha256':r['sha256'],'bytes':r['bytes']},'original-program')
for name in small_names:
    p=original_dir/name
    add({'path':p.as_posix(),'sha256':exact(old/name)['sha256'],'bytes':(old/name).stat().st_size},'original-build-record')
manifest=save('complete-input-manifest.json',{'schema':'researchos.schema22-provenance-input-manifest.v1','references':list(refs.values()),'count':len(refs),'total_bytes':sum(r['bytes'] for r in refs.values()),'roles':roles,'recorded_compile_input_count':len(before),'source_count':len(gs['files']),'original_source_root':original.as_posix(),'relocated_source_root':frozen.as_posix()})
guard=mod.SourceReadGuard()
checks=[]
def check(name,ok,detail=None):
    checks.append({'id':name,'passed':bool(ok),'detail':detail})
def raw(p): return guard.get_buffer(str(p))
def obj(p): return json.loads(raw(p))
gitcalls=[]
audit={'schema':'researchos.schema22-provenance-audit.v1','input_manifest_ref':manifest}
try:
    guard.acquire(list(refs.values()))
    b=raw(old/'source_before.json'); a=raw(old/'source_after.json')
    check('compiled-input-before-after-byte-identical',b==a,{'count':len(before)})
    check('recorded-compile-count-5922',len(before)==5922)
    result=obj(old/'result.json')
    check('result-commit-binding',result.get('commit')==gs['commit'])
    check('result-input-count-and-drift',result.get('input_count')==len(before) and result.get('source_drift') is False)
    check('result-binary-hashes',all(result.get('programs',{}).get(Path(r['path']).name)==r['sha256'] for r in resource['program_refs']))
    archive=raw(old/'git-archive.stdout')
    check('archive-sha-binding',hashlib.sha256(archive).hexdigest()==gs['archive_sha256'])
    tar_map={};blob_map={};modes={}
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:') as tf:
        for item in tf:
            if item.isdir(): continue
            check('tar-regular-file:'+item.name,item.isfile())
            if not item.isfile(): continue
            data=tf.extractfile(item).read()
            tar_map[item.name]=hashlib.sha256(data).hexdigest()
            blob_map[item.name]=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            modes[item.name]=item.mode
    check('archive-exact-git-source-map',tar_map==gs['files'],{'files':len(tar_map)})
    orig_names={p.relative_to(original).as_posix() for p in original.rglob('*') if p.is_file()}
    frozen_names={p.relative_to(frozen).as_posix() for p in frozen.rglob('*') if p.is_file()}
    check('original-source-inventory-exact',orig_names==set(gs['files']),{'actual':len(orig_names),'expected':len(gs['files'])})
    check('relocated-source-inventory-exact',frozen_names==set(gs['files']),{'actual':len(frozen_names),'expected':len(gs['files'])})
    for rel,sha in gs['files'].items():
        check('source-original-and-copy-equal:'+rel,raw(original/rel)==raw(frozen/rel))
    numbered=sorted(x for x in gs['files'] if re.fullmatch(r'migrations/sqlite/\d{4}_[^/]+\.sql',x))
    versions=[int(Path(x).name[:4]) for x in numbered]
    check('schema22-numbered-sql-exact',versions==list(range(1,23)),versions)
    check('session-addon-present','migrations/sqlite/next_v24_sessions.sql' in gs['files'])
    for rel in ['internal/api/contracts/client.protocol.schema.json','internal/api/contracts/domain.schema.json','spec/v2.0/contracts/domain.schema.json','spec/v2.0/contracts/openapi.json']:
        check('contract-bound:'+rel,rel in gs['files'] and key(original/rel) in {key(p) for p in before})
    archive_inv=obj(old/'git-archive.invocation.json')
    gitexe=Path('C:/Program Files/Git/cmd/git.EXE')
    assert gitexe.is_file()
    repo=Path(archive_inv['cwd'])
    assert (repo/'.git').exists()
    pathspecs=archive_inv['actualargv'][4:]
    args=[str(gitexe),'-C',str(repo),'ls-tree','-r','-z','--full-tree',gs['commit'],'--',*pathspecs]
    p=subprocess.run(args,capture_output=True,timeout=30)
    (O/'git-ls-tree.stdout').write_bytes(p.stdout);(O/'git-ls-tree.stderr').write_bytes(p.stderr)
    gc={'args':args,'exit_code':p.returncode,'stdout_ref':exact(O/'git-ls-tree.stdout'),'stderr_ref':exact(O/'git-ls-tree.stderr')}
    gitcalls.append(gc)
    if p.returncode: raise RuntimeError('git ls-tree failed with original exit '+str(p.returncode))
    git_map={}
    for row in p.stdout.split(b'\0'):
        if not row: continue
        meta,path=row.split(b'\t',1);mode,typ,oid=meta.decode().split()
        git_map[path.decode('utf-8')]={'mode':mode,'type':typ,'object_id':oid}
    check('archive-paths-exact-current-git-tree',set(git_map)==set(blob_map),{'git_paths':len(git_map),'archive_paths':len(blob_map)})
    check('archive-file-bytes-bind-git-blob-ids',all(git_map.get(k,{}).get('object_id')==v and git_map[k]['type']=='blob' for k,v in blob_map.items()))
    gitref=save('git-source-object-manifest.json',{'commit':gs['commit'],'source_files':git_map,'blob_id_algorithm':'sha1(blob header plus original archive bytes)','archive_ref':exact(old/'git-archive.stdout'),'archive_sha256':gs['archive_sha256']})
    audit['git_source_object_manifest_ref']=gitref
    source_input_keys={key(p) for p in before}
    go_text=raw(old/'go-list.stdout').decode()
    dec=json.JSONDecoder();i=0;packages=[]
    while i<len(go_text):
        while i<len(go_text) and go_text[i].isspace():i+=1
        if i==len(go_text):break
        package,end=dec.raw_decode(go_text,i);i=end;packages.append(package)
    required=[];missing_coverage=[];package_errors=[]
    for package in packages:
        if package.get('Incomplete') or package.get('Error') or package.get('DepsErrors'):
            package_errors.append({'ImportPath':package.get('ImportPath'),'Incomplete':package.get('Incomplete'),'Error':package.get('Error'),'DepsErrors':package.get('DepsErrors')})
        directory=package.get('Dir')
        if not directory:continue
        for field in ['GoFiles','CgoFiles','SFiles','HFiles','SysoFiles','CFiles','CXXFiles','MFiles','FFiles','EmbedFiles','SwigFiles','SwigCXXFiles']:
            for name in package.get(field,[]):
                p=Path(directory)/name;required.append({'path':str(p),'field':field,'package':package.get('ImportPath')})
                if key(p) not in source_input_keys:missing_coverage.append(required[-1])
        gomod=package.get('Module',{}).get('GoMod')
        if gomod and key(gomod) not in source_input_keys:missing_coverage.append({'path':gomod,'field':'Module.GoMod','package':package.get('ImportPath')})
    check('go-list-no-incomplete-or-package-errors',not package_errors,package_errors)
    check('declared-go-list-compile-inputs-covered',not missing_coverage,{'required_mentions':len(required),'missing':missing_coverage})
    env=obj(old/'environment.json')
    check('recorded-offline-toolchain-settings',all(env.get(k)==v for k,v in {'GOTOOLCHAIN':'local','GOENV':'off','GOPROXY':'off','GOSUMDB':'off'}.items()))
    invocations=[]
    for name in ['git-archive','go-list','old22-control.exe.build','old22-backup.exe.build']:
        record=obj(old/(name+'.invocation.json'))
        check('original-invocation-exit-zero:'+name,record.get('exit')==0,{'recorded_exit':record.get('exit'),'start':record.get('started_at'),'end':record.get('ended_at')})
        invocations.append({'name':name,'invocation_ref':exact(old/(name+'.invocation.json')),'stdout_ref':exact(old/(name+'.stdout')),'stderr_ref':exact(old/(name+'.stderr')),'original_recorded_argv':record.get('actualargv'),'original_recorded_cwd':record.get('cwd'),'original_recorded_exit':record.get('exit'),'current_reviewer_executed':False})
    for name,package in [('old22-control.exe','./apps/control'),('old22-backup.exe','./ops/backup')]:
        record=obj(old/(name+'.build.invocation.json'));argv=record['actualargv']
        check('build-package-cwd-output:'+name,argv[1:4]==['build','-buildvcs=false','-o'] and argv[-1]==package and key(record['cwd'])==key(original) and key(argv[-2])==key(original_dir/name))
        check('build-tool-in-input-vector:'+name,key(argv[0]) in source_input_keys)
        check('program-copy-original-equal:'+name,raw(old/name)==raw(original_dir/name))
    program_metadata=[]
    for r in resource['program_refs']:
        data=raw(r['path'])
        mz=data[:2]==b'MZ';peoff=int.from_bytes(data[60:64],'little') if len(data)>=64 else -1
        pesig=data[peoff:peoff+4] if 0<=peoff<len(data)-4 else b''
        check('windows-pe-signature:'+Path(r['path']).name,mz and pesig==b'PE\0\0')
        marker=b'\xff Go buildinf:'
        pos=data.find(marker)
        snippets=[]
        if pos>=0:
            segment=data[pos:pos+4096]
            snippets=[x.decode('utf-8','replace') for x in re.findall(rb'[\x20-\x7e\t]{6,}',segment)]
        program_metadata.append({'ref':r,'pe_signature':pesig.hex(),'pe_header_offset':peoff,'go_buildinfo_marker_offset':pos,'go_buildinfo_printable_segments':snippets[:12]})
    audit.update({'checks':checks,'check_count':len(checks),'failed_checks':[x for x in checks if not x['passed']],'original_build_invocations':invocations,'original_build_result':result,'recorded_environment':env,'package_count':len(packages),'declared_compile_input_mentions':len(required),'compile_input_coverage_gaps':missing_coverage,'program_metadata':program_metadata,'source_count':len(gs['files']),'compiled_input_count':len(before),'source_original_and_relocated_roots':{'original':original.as_posix(),'relocated':frozen.as_posix()},'original_env_not_fully_recorded':['GOFLAGS','GOOS','GOARCH','CGO_ENABLED','PATH'],'reviewer_execution':{'git_readonly':True,'go':False,'old_program':False,'Native_test':False,'provider':False,'dispatcher':False,'Main_or_Canon_write':False}})
finally:
    closed=guard.close()
    audit['source_guard_ref']=save('sourceguard.final.json',closed)
    audit['guard_summary']={'verification':closed['verification'],'closed':closed['closed'],'retained_handles_count':closed['retained_handles_count'],'entry_count':len(closed['entries']),'errors':closed['errors']}
    audit['git_original_io_ref']=save('git.original-io.json',{'calls':gitcalls})
    ar=save('audit.json',audit)
    print('AUDIT_RESULT',json.dumps({'ref':ar,'guard':audit['guard_summary'],'checks':len(checks),'failed_checks':[c for c in checks if not c['passed']],'program_metadata':audit.get('program_metadata')},ensure_ascii=False))
assert closed['verification']=='PASSED' and closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']

