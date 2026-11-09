import hashlib, json, os, re, subprocess
from pathlib import Path

ROOT = Path(r'D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).resolve().parent
GIT = r'C:/Program Files/Git/cmd/git.exe'
COMMITS = ['a3816cd36322fdf554b629e780d07bb23fcaf355', 'f6e4a0ed54d697c7214a75743cd1b83dc3685ddb']
MOD = 'researchos.local/research-os/'
IO = []

def sha(b): return hashlib.sha256(b).hexdigest()
def ref(p):
    p = Path(p); b = p.read_bytes()
    return {'path': p.as_posix(), 'sha256': sha(b), 'bytes': len(b)}
def write(name, obj):
    p = OUT / name; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return ref(p)
def git(args, stdin=None):
    n = len(IO)+1
    cp = subprocess.run([GIT, '-C', str(ROOT), *args], input=stdin, capture_output=True)
    p = OUT/'git-io'; p.mkdir(exist_ok=True)
    (p/f'{n:02}.stdout.raw').write_bytes(cp.stdout)
    (p/f'{n:02}.stderr.raw').write_bytes(cp.stderr)
    rec = {'argv':[GIT,'-C',str(ROOT),*args], 'exit':cp.returncode, 'stdout':ref(p/f'{n:02}.stdout.raw'), 'stderr':ref(p/f'{n:02}.stderr.raw')}
    if stdin is not None:
        (p/f'{n:02}.stdin.raw').write_bytes(stdin); rec['stdin']=ref(p/f'{n:02}.stdin.raw')
    IO.append(rec); write('git-commands.actual.json', IO)
    if cp.returncode: raise RuntimeError('GIT_READ_FAILED_'+str(n))
    return cp.stdout

head = git(['rev-parse','HEAD']).decode().strip()
worktrees = git(['worktree','list','--porcelain']).decode()
catalog = []
all_data = {}
for commit in COMMITS:
    rawtree = git(['ls-tree','-r','-z',commit])
    tree = {}
    for line in rawtree.split(b'\0'):
        if not line: continue
        meta, path = line.split(b'\t',1)
        mode, kind, oid = meta.decode().split()
        tree[path.decode()] = {'mode':mode, 'kind':kind, 'oid':oid}
    # Only public compilation source, SQL and contracts, never receipt/business rows.
    selected = sorted(p for p in tree if (
        p.endswith('.go') and p.startswith(('apps/control/','apps/cli/','internal/','adapters/','ops/','evaluation/'))
        or p.startswith('migrations/sqlite/') and p.endswith('.sql')
        or p in ['go.mod','go.sum','AGENTS.md','VERSION','spec/v2.0/contracts/domain.schema.json','spec/v2.0/contracts/openapi.json']
        or p in ['adapters/protectedstore/frozen_development.json','internal/api/contracts/client.protocol.schema.json','internal/api/contracts/domain.schema.json','internal/domain/contracts/evaluation-v24.schema.json']))
    request = ''.join(tree[p]['oid']+'\n' for p in selected).encode()
    batch = git(['cat-file','--batch'],request)
    pos=0; data={}; entries=[]
    for p in selected:
        end=batch.index(b'\n',pos); hdr=batch[pos:end].decode().split(); size=int(hdr[2]); pos=end+1
        b=batch[pos:pos+size]; pos+=size+1
        assert hdr[0]==tree[p]['oid'] and hdr[1]=='blob'
        assert hashlib.sha1(b'blob '+str(size).encode()+b'\0'+b).hexdigest()==hdr[0]
        data[p]=b
        entries.append({'git_path':p,'git_blob':hdr[0],'sha256':sha(b),'bytes':size,'mode':tree[p]['mode']})
    assert pos==len(batch)
    # A static package-import superset keeps all OS/tag variants; actual Go list is intentionally deferred.
    pkgs={'apps/control','ops/backup','apps/cli'}; imports=set(); embeds=set(); changed=True
    while changed:
        changed=False
        for p,b in data.items():
            if not p.endswith('.go') or p.endswith('_test.go') or str(Path(p).parent).replace('\\','/') not in pkgs: continue
            s=b.decode('utf-8')
            for block in re.findall(r'(?m)^import\s*(\([^)]*\)|[^\n]+)',s):
                for imp in re.findall(r'"([^"\n]+)"',block):
                    imports.add(imp)
                    if imp.startswith(MOD) and imp[len(MOD):] not in pkgs: pkgs.add(imp[len(MOD):]); changed=True
            for line in re.findall(r'(?m)^//go:embed\s+(.+)$',s):
                for pat in line.split():
                    assert '*' not in pat and '?' not in pat
                    embeds.add((Path(p).parent/pat).as_posix())
    build_paths={p for p in data if p.endswith('.go') and not p.endswith('_test.go') and Path(p).parent.as_posix() in pkgs}|embeds|{'go.mod','go.sum'}
    missing_packages=sorted(k for k in pkgs if not any(Path(p).parent.as_posix()==k and p.endswith('.go') for p in data))
    assert not missing_packages and embeds.issubset(data)
    runtime_paths={p for p in data if p.startswith('migrations/sqlite/') or p in ['spec/v2.0/contracts/domain.schema.json','spec/v2.0/contracts/openapi.json']}
    versions=[int(Path(p).name[:4]) for p in sorted(runtime_paths) if re.match(r'^\d{4}_',Path(p).name)]
    assert versions==list(range(1,22))
    selected_evidence={'go.mod','go.sum','apps/control/main.go','apps/control/replay_command.go','ops/backup/main.go','internal/domain/store.go','internal/domain/contracts.go','internal/domain/client_session_fence.go','internal/store/sqlite.go','internal/domain/backup_migration.go','migrations/sqlite/next_v24_sessions.sql','migrations/sqlite/0021_research_pending_windows.sql'}
    evidence={}
    for p in sorted(selected_evidence & data.keys()):
        dest=OUT/'source-excerpts'/commit/p; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(data[p]); evidence[p]=ref(dest)
    candidate={'commit':commit,'tree':git(['rev-parse',commit+'^{tree}']).decode().strip(),'source_objects':entries,'numbered_versions':versions,'domain_new_installs_session_addon':b'sessionSchema' in data['internal/domain/store.go'],'static_build_packages':sorted(pkgs),'static_build_paths':sorted(build_paths),'static_build_bytes':sum(len(data[p]) for p in build_paths),'runtime_paths':sorted(runtime_paths),'embeds':sorted(embeds),'external_imports':sorted(x for x in imports if '.' in x.split('/')[0] and not x.startswith(MOD)),'selected_blob_evidence_refs':evidence,'limits':'Static import superset; no Go list/build or compiler-selected closure claim. Tests excluded from proposed build inputs; all OS/tag variants retained.'}
    catalog.append(candidate); all_data[commit]=data
write('source-object-inventory.json',catalog)

# Check small public metadata only in already existing worktrees; no mutation or broad data reads.
locations=[]
for block in worktrees.strip().split('\n\n'):
    lines=block.splitlines(); path=next(x[9:] for x in lines if x.startswith('worktree ')); h=next(x[5:] for x in lines if x.startswith('HEAD '))
    locations.append({'path':path,'head':h,'candidate_commit_match':h in COMMITS})
write('existing-worktree-observations.json',{'scope':'registered git worktrees and .local/releases directory names only; not global absence','worktrees':locations,'exact_candidate_worktrees':[x for x in locations if x['candidate_commit_match']],'release_directory_names':[p.name for p in (ROOT/'.local/releases').iterdir() if p.is_dir()]})

# Reuse sealed qualification metadata without following its old business dependencies.
B=ROOT/'execution/v2.4/receipts/W05/W05-99'
prior=[]
for folder,names in [
 ('genuine_release_resource_inventory_codex/release-resource-20261009-01',['HDF.json','MF.json','REPORT.md','inventory.json','git-tree-identities.json']),
 ('genuine_schema22_resource_independent_review_codex/schema22-20261009-01',['HDF.json','MF.json','REPORT.md','decision.json']),
 ('historical20_resource_route_readonly_codex/current_target_actual_review_01',['HDF.json','MF.json','report.md','go-dependency-resource-presence.json']),
 ('backup_regression_resource_readonly_codex/9e4a05cf0d514cfcacd6cfd74acdb609',['resource-report.json'])]:
    for name in names:
        p=B/folder/name; obj=json.loads(p.read_bytes()) if name.endswith('.json') else None
        prior.append({'ref':ref(p),'status':obj.get('status',obj.get('decision')) if isinstance(obj,dict) else None})
write('existing-qualification-refs.json',{'refs':prior,'old22_status':'Reuse existing exact-binary programme provenance decision; no rebuild/rerun; formal historical release qualification remains as in source decision.','old21_status':'Prior bounded discovery located Git source, not qualified old21 binary/build binding. This task does not promote it.','dependency_walk':'NONE; selected source-resource/qualification metadata only'})

lock=json.loads((ROOT/'execution/toolchains/locked.json').read_bytes()); toolrefs={}
for name in ['go','git','python']:
    r=ref(lock['tools'][name]['path']); assert r['sha256']==lock['tools'][name]['sha256']; toolrefs[name]=r
data=all_data[COMMITS[1]]; mod=data['go.mod'].decode(); sums=data['go.sum'].decode().splitlines(); modules=[]
for name,version in re.findall(r'^\s*([a-zA-Z0-9./_-]+)\s+(v\S+)',mod,re.M):
    cache=ROOT/'.local/gopath/pkg/mod/cache/download'/name/'@v'; expanded=ROOT/'.local/gopath/pkg/mod'/(name+'@'+version)
    metadata={}
    for suffix in ['.mod','.info','.ziphash']:
        p=cache/(version+suffix); metadata[suffix]={'present':p.is_file(),'ref':ref(p) if p.is_file() else None}
    ziphash=(cache/(version+'.ziphash')).read_text().strip() if (cache/(version+'.ziphash')).is_file() else None
    expected=next((x.split()[2] for x in sums if x.split()[:2]==[name,version]),None)
    modules.append({'module':name,'version':version,'go_sum_lines':[x for x in sums if x.startswith(name+' '+version+' ') or x.startswith(name+' '+version+'/go.mod ')],'expanded_path':expanded.as_posix(),'expanded_present':expanded.is_dir(),'expanded_go_mod_ref':ref(expanded/'go.mod') if (expanded/'go.mod').is_file() else None,'cached_metadata':metadata,'zip_present':(cache/(version+'.zip')).is_file(),'ziphash_matches_go_sum':ziphash==expected if ziphash else None})
write('tool-module-resources.json',{'lock_ref':ref(ROOT/'execution/toolchains/locked.json'),'tools_current_hash_verified':toolrefs,'go_not_executed':True,'expected_go':'go1.27.1 windows/amd64','module_count':len(modules),'modules':modules,'all_expanded_present':all(x['expanded_present'] for x in modules),'GOPATH':(ROOT/'.local/gopath').as_posix(),'GOMODCACHE':(ROOT/'.local/gopath/pkg/mod').as_posix(),'GOCACHE_existing':(ROOT/'.local/gocache').as_posix(),'future_flags':{'GOTOOLCHAIN':'local','GOPROXY':'off','GOSUMDB':'off','GOWORK':'off','GOOS':'windows','GOARCH':'amd64','CGO_ENABLED':'0','GOFLAGS':'-mod=readonly'},'limitations':'Presence and cached hash-text binding only; module content integrity, transitive graph and compiler closure remain OPEN for Root independent build. No cache/toolchain copies.'})
write('discovery-stage.json',{'head':head,'candidates':[{'commit':x['commit'],'tree':x['tree'],'numbered_sql_count':len(x['numbered_versions']),'session_addon_via_public_startup':x['domain_new_installs_session_addon'],'build_files':len(x['static_build_paths']),'build_bytes':x['static_build_bytes'],'runtime_files':len(x['runtime_paths'])} for x in catalog],'tools_verified':toolrefs,'modules':len(modules),'all_expanded_present':all(x['expanded_present'] for x in modules),'git_commands':len(IO),'go_executions':0,'native_product_executions':0,'SQL_operations':0,'active_TP':False,'runtime_grant':False})
print(json.dumps(json.loads((OUT/'discovery-stage.json').read_bytes()),ensure_ascii=False))
