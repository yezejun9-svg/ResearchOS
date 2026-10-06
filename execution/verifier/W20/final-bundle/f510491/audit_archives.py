import hashlib, json, struct, subprocess, zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).resolve().parent
SOURCE='f51049149b6ba0d53c83f5bb5cf0274ea1039c24'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def check(ok,label):
    if not ok:raise AssertionError(label)
tree={}
for entry in git('ls-tree','-r','-z',SOURCE).split(b'\0'):
    if entry:
        meta,name=entry.split(b'\t',1);tree[name.decode()]=meta.decode().split()[2]
source_dirs=('spec/v2.0','migrations/sqlite','adapters','internal','apps/control','apps/web/src','ops','tests','bootstrap','evaluation/development','evaluation/evolution','evaluation/skills','execution/command_dispatcher','release','docs/installation')
root_files={'go.mod','go.sum','apps/web/package.json','apps/web/package-lock.json','apps/web/index.html','execution/commands.json'}
suffixes={'.go','.py','.js','.jsx','.css','.json','.html','.md','.ps1','.sql'}
excluded_parts={'.local','node_modules','dist','__pycache__','.git','receipts','verifier'}
excluded={'tests/ui/browser_smoke.py','tests/intent/browser_intake.py','tests/evolution/control_private_recompute/main.go'}
expected_sources={p for p in tree if p in root_files or (any(p.startswith(d+'/') for d in source_dirs) and PurePosixPath(p).suffix.lower() in suffixes and not any(x in excluded_parts or x.startswith('.') for x in PurePosixPath(p).parts) and p not in excluded)}
aliases={f'scripts/{n}.ps1':f'ops/release/{n}.ps1' for n in ('start','stop','verify')}
expected_sources.update(aliases)
report={'source_commit':SOURCE,'scope':'INDEPENDENT_PACKAGE_CURRENT_USER_FIXTURE_ONLY','archives':[]}
inventories=[];manifests=[];source_matches=[];forbidden=[];sensitive=[]
for label in ('a','b'):
    path=ROOT/'.local'/f'researchos-final-f510491-{label}.zip'
    record={'label':label,'path':str(path),'sha256':sha(path.read_bytes()),'size':path.stat().st_size}
    with zipfile.ZipFile(path) as z:
        names=z.namelist();check(len(names)==len(set(names)),'duplicate ZIP entries');check(names==sorted(names),'ZIP order');check(z.testzip() is None,'ZIP CRC')
        for name in names:
            p=PurePosixPath(name);check(not p.is_absolute() and '..' not in p.parts and '\\' not in name and ':' not in name,'unsafe ZIP path')
        raw={n:z.read(n) for n in names};m=json.loads(raw['release-manifest.json']);manifests.append(raw['release-manifest.json'])
        listed={f['path']:f for f in m['files']};check(len(listed)==len(m['files']),'duplicate manifest entries');check(set(names)==set(listed)|{'release-manifest.json'},'manifest inventory')
        for n,f in listed.items():check(sha(raw[n])==f['sha256'] and len(raw[n])==f['size'],'file hash '+n)
        inventory={n:{'sha256':sha(b),'size':len(b)} for n,b in raw.items()};inventories.append(inventory)
        check(m['source_commit']==SOURCE,'frozen source ref');check(set(excluded).isdisjoint(names),'construction helper bundled')
        for n in excluded:check(n in m['commands']['source_checkout_gap'],'exclusion disclosure')
        sources={n for n in listed if not n.startswith(('bin/','web/dist/','licenses/'))};check(sources==expected_sources,'complete frozen source allowlist')
        for n in sorted(sources):
            blob=raw[n];oid=hashlib.sha1(f'blob {len(blob)}\0'.encode()+blob).hexdigest();check(oid==tree[aliases.get(n,n)],'source differs from exact Git blob '+n)
        check(sha(canonical({n:sha(raw[n]) for n in sorted(sources)}))==m['source_tree_sha256'],'source tree digest')
        check(m['build_id']==m['source_tree_sha256'][:20],'build ID')
        bins={n for n in names if n.startswith('bin/')};check(bins=={f'bin/{n}.exe' for n in ('control','runtime','backup','release_host')},'four exact executables')
        for n in bins:
            b=raw[n];check(b[:2]==b'MZ','PE DOS header');offset=struct.unpack_from('<I',b,0x3c)[0];check(b[offset:offset+4]==b'PE\0\0' and struct.unpack_from('<H',b,offset+4)[0]==0x8664,'PE AMD64')
        migration_names=sorted(n for n in names if n.startswith('migrations/sqlite/') and n.endswith('.sql'))
        check([int(PurePosixPath(n).name[:4]) for n in migration_names]==list(range(1,21)),'twenty frozen migrations')
        check(m['migrations']==[{'name':PurePosixPath(n).name,'sha256':sha(raw[n])} for n in migration_names],'migration manifest')
        check(m['database']['fresh_fixture_schema']==20 and m['database']['final_release_schema']==20,'schema20')
        check(m['database']['schema13_to_final_qualification']=='BOUNDED_FIXTURE_MECHANISM_ONLY; ACTUAL_ACTIVATION_BLOCKED','activation gap')
        check(m['acceptance']=={'A15_clean_windows':'NOT_RUN','W20':'NOT_ACCEPTED','normal_live_runtime':'CLOSED'},'scope guard')
        markers=[x.encode() for x in ('C:\\Users\\','C:/Users/','D:\\作品集\\','D:/作品集/')]
        for n,b in raw.items():
            if any(x in b or x.decode().encode('utf-16le') in b for x in markers):forbidden.append(n)
            if PurePosixPath(n).suffix.lower() in {'.key','.pem','.sqlite','.db','.pid','.pfx'} or PurePosixPath(n).name.startswith('.env'):sensitive.append(n)
        check(not forbidden,'developer path marker in archive');check(not sensitive,'credential/database file in archive')
        npm=m['sbom']['npm'];lock=json.loads(raw['apps/web/package-lock.json'])['packages'];lock={n.removeprefix('node_modules/'):v for n,v in lock.items() if n}
        check(len(npm)==len(lock)==43,'43 npm inventory entries');check({x['name'] for x in npm}==set(lock),'npm inventory exact lock set')
        for module in npm:
            entry=lock[module['name']];check(module['version']==entry['version'],'npm locked version')
            check(module['integrity']==entry.get('integrity','UNKNOWN'),'npm locked integrity')
            if module['installation_status']=='INSTALLED':check(module['installed_version']==module['version'],'npm installed version')
            for text in module['license_texts']:check(sha(raw[text['file']])==text['sha256'],'npm license bytes')
        for module in m['sbom']['go']:
            if 'license_file' in module:check(sha(raw[module['license_file']])==module['license_sha256'],'Go license bytes')
        check(len(m['sbom']['license_gaps'])==2,'two explicit license gaps')
        record.update(manifest_sha256=sha(raw['release-manifest.json']),file_count=len(names),source_files_verified=len(sources),four_bins={n:inventory[n] for n in sorted(bins)},npm_inventory_count=len(npm),npm_installation_counts=dict(Counter(x['installation_status'] for x in npm)),go_module_count=len(m['sbom']['go']),license_gaps=m['sbom']['license_gaps'],migration_count=len(migration_names))
        if label=='a':
            (OUT/'archive-files.json').write_bytes(canonical(inventory))
            (OUT/'manifest-copy.json').write_bytes(raw['release-manifest.json'])
    report['archives'].append(record)
check(report['archives'][0]['sha256']==report['archives'][1]['sha256'],'archive reproducibility')
check(inventories[0]==inventories[1] and manifests[0]==manifests[1],'every-file and manifest reproducibility')
report.update(status='PASS_ARCHIVE_AUDIT',all_file_hashes_equal=True,manifest_bytes_equal=True,exact_frozen_git_source_verified=True,developer_path_scan_hits=forbidden,sensitive_runtime_file_hits=sensitive,clean_windows='NOT_RUN',SCM='NOT_RUN',normal_live='CLOSED')
(OUT/'archive-audit.json').write_bytes(canonical(report))
print(json.dumps(report,ensure_ascii=False,sort_keys=True))
