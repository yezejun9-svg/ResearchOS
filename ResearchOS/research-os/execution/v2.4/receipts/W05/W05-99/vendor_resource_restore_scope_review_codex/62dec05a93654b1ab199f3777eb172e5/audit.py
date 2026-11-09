import concurrent.futures, hashlib, json, os, stat, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).resolve().parent
def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def write(name, value):
    with (OUT/name).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')
def ref(p):
    p = Path(p)
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p.read_bytes())}
def command(name, argv):
    start=now(); p=subprocess.run(argv,cwd=ROOT,capture_output=True)
    for suffix,raw in [('stdout',p.stdout),('stderr',p.stderr)]:
        with (OUT/(name+'.'+suffix)).open('xb') as f: f.write(raw)
    write(name+'.invocation.json', {'actualargv':argv,'cwd':str(ROOT),'started_at':start,'ended_at':now(),'exit':p.returncode,
        'stdout_ref':ref(OUT/(name+'.stdout')),'stderr_ref':ref(OUT/(name+'.stderr'))})
    if p.returncode: raise RuntimeError(name+' exit '+str(p.returncode))
    return p.stdout

start=now()
head=command('git-head-before',['git','rev-parse','HEAD']).decode().strip()
status_args=['git','status','--porcelain=v1','--untracked-files=no','--','third_party','adapters/runtime/mu/build.mjs']
status_before=command('git-status-before',status_args)
manifest_path=ROOT/'third_party/mu.MANIFEST.json'
manifest=json.loads(manifest_path.read_bytes())
entries=manifest['entries']
assert manifest['files']==5083 and len(entries)==5083
tree_raw=command('git-tree',['git','ls-tree','-r','-z',head,'--','third_party/mu'])
tree={}
for record in tree_raw.split(b'\0'):
    if not record: continue
    meta,path=record.split(b'\t',1); mode,kind,oid=meta.decode().split()
    tree[path.decode('utf-8')]={'mode':mode,'kind':kind,'blob_oid':oid}
metadata_paths=['AGENTS.md','execution/project_identity.json','adapters/runtime/mu/build.mjs',
    'third_party/mu.MANIFEST.json','third_party/VENDORED_FROM.md','execution/v2.4/component_lock.json',
    'execution/v2.4/patch_inventory.json','third_party/mu/package-lock.json','third_party/mu/package.json',
    'third_party/mu/packages/coding-agent/package.json','third_party/mu/packages/ai/package.json']
metadata_before=[ref(ROOT/p) for p in metadata_paths]
manifest_git=command('git-manifest',['git','cat-file','blob',head+':third_party/mu.MANIFEST.json'])
assert manifest_git==manifest_path.read_bytes(), 'working manifest differs from immutable HEAD'

def inspect(item):
    path,expected=item
    assert path.startswith('third_party/mu/') and '..' not in path.split('/')
    p=ROOT/path
    assert p.resolve().is_relative_to((ROOT/'third_party/mu').resolve())
    row={'path':path,'expected_sha256':expected['sha256'],'expected_size':expected['size'],'git':tree.get(path)}
    try: info=p.lstat()
    except FileNotFoundError:
        row['status']='MISSING'; return row
    if not stat.S_ISREG(info.st_mode): row['status']='NOT_REGULAR'; return row
    raw=p.read_bytes()
    row.update(actual_size=len(raw),actual_sha256=sha(raw),actual_git_blob_oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest())
    row['manifest_match']=row['actual_size']==expected['size'] and row['actual_sha256']==expected['sha256']
    row['git_match']=bool(row['git'] and row['git']['blob_oid']==row['actual_git_blob_oid'])
    row['status']='MATCH' if row['manifest_match'] and row['git_match'] else 'MODIFIED_OR_GIT_MISMATCH'
    return row
def inventory():
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        return list(pool.map(inspect,sorted(entries.items())))
before=inventory(); write('inventory.before.json',before)
issues=[r for r in before if r['status']!='MATCH']
restores=[]
for i,row in enumerate(issues):
    assert row['git'] and row['git']['kind']=='blob'
    raw=command('git-original-asset-'+str(i+1),['git','cat-file','blob',row['git']['blob_oid']])
    original_match=sha(raw)==row['expected_sha256'] and len(raw)==row['expected_size']
    media='image/png' if raw.startswith(b'\x89PNG\r\n\x1a\n') else 'image/gif' if raw[:6] in (b'GIF87a',b'GIF89a') else 'UNKNOWN'
    restores.append({**row,'expected_absence':row['status']=='MISSING','original_commit':head,
      'original_source':'git cat-file blob '+row['git']['blob_oid'],'original_sha256':sha(raw),'original_size':len(raw),
      'original_matches_manifest':original_match,'media_type':media,'original_bytes_ref':ref(OUT/('git-original-asset-'+str(i+1)+'.stdout')),
      'eligible_for_narrow_restore':row['status']=='MISSING' and original_match and media in ('image/png','image/gif')})
junction=ROOT/'third_party/mu/node_modules/@earendil-works/pi-coding-agent'
mirror=junction/'docs/images/exy.png'
junction_info={'path':str(junction),'exists':junction.exists(),'is_junction':junction.is_junction(),
 'resolved':str(junction.resolve()),'expected_target':str(ROOT/'third_party/mu/packages/coding-agent'),
 'target_matches':junction.resolve()==(ROOT/'third_party/mu/packages/coding-agent').resolve(),
 'mirror_path':str(mirror),'mirror_exists':mirror.exists(),'mirror_resolved':str(mirror.resolve()),
 'mirror_is_same_logical_target':mirror.resolve()==(ROOT/'third_party/mu/packages/coding-agent/docs/images/exy.png').resolve(),
 'mirror_requires_separate_write':False}
write('mirror_observation.json',junction_info)
after=inventory(); write('inventory.after.json',after)
metadata_after=[ref(ROOT/p) for p in metadata_paths]
head_after=command('git-head-after',['git','rev-parse','HEAD']).decode().strip()
status_after=command('git-status-after',status_args)
drift=[a['path'] for a,b in zip(before,after) if a!=b]
assert not drift and metadata_before==metadata_after and head==head_after and status_before==status_after
write('public_read_closure.json',{'before':metadata_before,'after':metadata_after,'drift':[],
 'vendor_before_ref':ref(OUT/'inventory.before.json'),'vendor_after_ref':ref(OUT/'inventory.after.json')})
counts={s:sum(r['status']==s for r in before) for s in sorted(set(r['status'] for r in before))}
write('audit.json',{'schema':'researchos.vendor-resource-readonly-audit.v1','reviewer_id':'codex:/root/sources_parent_impl',
 'started_at':start,'ended_at':now(),'head':head,'manifest_ref':ref(manifest_path),'manifest_count':len(entries),
 'git_tracked_count_under_vendor':len(tree),'manifest_not_in_git':sorted(set(entries)-set(tree)),
 'git_not_in_manifest':sorted(set(tree)-set(entries)),'counts':counts,'issues':restores,
 'closure_ref':ref(OUT/'public_read_closure.json'),'mirror_ref':ref(OUT/'mirror_observation.json'),
 'actual_resource_writes':0,'build_executed':False,'unknown_deletion_origin':'NOT_ATTRIBUTED',
 'git_status_before_ref':ref(OUT/'git-status-before.stdout'),'git_status_after_ref':ref(OUT/'git-status-after.stdout')})
eligible=all(r['eligible_for_narrow_restore'] for r in restores) and junction_info['target_matches'] and junction_info['mirror_is_same_logical_target']
write('scope_proposal.json',{'schema':'researchos.vendor-resource-restore-scope-proposal.v1',
 'status':'PROPOSED_EXACT_BINARY_RESOURCE_RESTORE_REQUIRES_ROOT_REGISTRATION' if eligible else 'BLOCKED_NEEDS_SEPARATE_REVIEW',
 'audit_ref':ref(OUT/'audit.json'),'repository':str(ROOT),'source_commit':head,
 'exact_resource_paths':[r['path'] for r in restores],'resources':restores,
 'why_all_required':'build.mjs validates every one of 5083 manifest entries before dependency import or bundling; each missing file blocks a fresh build.',
 'mirror_policy':'Existing node_modules package junction resolves to this MAIN package. Restore only the original package path; do not write or replace the junction or mirrored pathname.',
 'mandatory_execution_guards':[
  'Root must independently register exact resource paths before execution; this proposal is not authorization or acceptance.',
  'Use only the recorded immutable Git blob and verify size and SHA256 against both HEAD and unchanged manifest before write.',
  'Restore only absent MAIN paths using exclusive create; refuse existing files, symlinks or reparse targets. Revalidate resolved parent stays within exact MAIN vendor root.',
  'No overwrite, whole-tree checkout/restore, network fetch, package install, code changes, SDK version changes, lock or manifest changes.',
  'Record before absence and after exact SHA256 plus all5083 checks and public-input before/after closure in a new Root-owned receipt.',
  'Unknown-origin deletions in other worktrees and historical stdout/W20 ZIP artifacts are excluded and must remain untouched.',
  'Any nonlisted mismatch or failed precondition stops only affected branch; preserve failure evidence without widening restore.',
  'A subsequent actual build needs its own authorized source vector and builder output; asset restoration itself does not qualify a bundle or provider.'
 ],'excluded_source_changes':['adapters/runtime/mu/build.mjs','third_party/mu.MANIFEST.json','execution/v2.4/component_lock.json','third_party/mu/package-lock.json','all SDK code'],
 'sdk_source_or_manifest_change':False,'actual_build_or_provider_qualification':False})
write('handoff.json',{'status':'READONLY_RESTORE_SCOPE_PROPOSED','audit_ref':ref(OUT/'audit.json'),
 'proposal_ref':ref(OUT/'scope_proposal.json'),'counts':counts,'resource_count':len(restores),
 'source_drift':0,'resource_writes':0,'build_runs':0,'paid_calls':0,'private_data_reads':0,
 'current_pinned_bundle':'Not rebuilt or changed; no bundle acceptance inferred.',
 'remaining_gate':'Root narrow registration and absent-only exact-blob restoration; then fresh actual builder qualification.',
 'failure_origins':[]})
write('manifest.json',{'files':[ref(p) for p in sorted(OUT.iterdir()) if p.is_file()]})
print(json.dumps({'counts':counts,'head':head,'audit':ref(OUT/'audit.json'),'proposal':ref(OUT/'scope_proposal.json'),
 'handoff':ref(OUT/'handoff.json'),'manifest':ref(OUT/'manifest.json'),'paths':[r['path'] for r in restores]},ensure_ascii=False))
