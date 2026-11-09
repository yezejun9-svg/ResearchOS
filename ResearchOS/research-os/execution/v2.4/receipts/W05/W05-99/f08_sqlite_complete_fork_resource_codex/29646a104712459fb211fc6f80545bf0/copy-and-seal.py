from pathlib import Path
import os,stat,json,hashlib,base64,ast,difflib,datetime
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
AUTHOR=ROOT/'execution/v2.4/receipts/W05/W05-99/f08_sqlite_innocuous_driver_preparation_codex/da3c883ec6684c4487dbe36ff45affe4'
PEER=ROOT/'execution/v2.4/receipts/W05/W05-99/f08_sqlite_innocuous_driver_independent_source_review_codex/734ee12d8b8d404798c2ec6e6e1f56bc'
MODULE=ROOT/'.local/gopath/pkg/mod/modernc.org/sqlite@v1.60.1'
CACHE=ROOT/'.local/gopath/pkg/mod/cache/download/modernc.org/sqlite/@v'
FORK=OUT/'module/modernc_sqlite_v1_60_1_researchos_innocuous'
PREFIX='modernc.org/sqlite@v1.60.1'
INPUTS={}
def digest(b):return hashlib.sha256(b).hexdigest()
def plain(p,kind=None):
    p=Path(p);a=p.absolute();assert p.resolve(strict=True)==a,('alias',str(p))
    for q in [a]+list(a.parents):
        s=q.lstat();assert not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&1024,('reparse',str(q))
    s=p.lstat()
    if kind=='file':assert stat.S_ISREG(s.st_mode),('not regular',str(p))
    if kind=='dir':assert stat.S_ISDIR(s.st_mode),('not directory',str(p))
    return s
def identity(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def raw(p):
    p=Path(p);a=plain(p,'file');b=p.read_bytes();z=plain(p,'file');assert identity(a)==identity(z) and len(b)==a.st_size,('read drift',str(p));return b
def ref(p,b=None):
    p=Path(p);b=raw(p) if b is None else b
    return {'path':p.as_posix(),'sha256':digest(b),'bytes':len(b)}
def read_input(p):
    b=raw(p);r=ref(p,b);INPUTS[r['path']]=r;return b
def doc(p):return json.loads(read_input(p).decode('utf-8'))
def verify(r):
    p=Path(r['path']);p=p if p.is_absolute() else ROOT/p;b=read_input(p)
    assert digest(b)==r['sha256'] and len(b)==r['bytes'],('input mismatch',str(p));return b
def write(rel,b):
    p=OUT/rel;assert p.absolute().is_relative_to(OUT)
    p.parent.mkdir(parents=True,exist_ok=True);plain(p.parent,'dir')
    if isinstance(b,str):b=b.encode('utf-8')
    with p.open('xb') as f:f.write(b)
    return ref(p)
def js(rel,x):return write(rel,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def inventory(base):
    plain(base,'dir');files=[];dirs=[];todo=[base]
    while todo:
        d=todo.pop();plain(d,'dir')
        for item in sorted(d.iterdir(),key=lambda p:p.name):
            s=plain(item)
            if stat.S_ISDIR(s.st_mode):dirs.append(item.relative_to(base).as_posix());todo.append(item)
            else:
                assert stat.S_ISREG(s.st_mode),('nonregular',str(item))
                name=item.relative_to(base).as_posix();assert '\n' not in name and '\r' not in name
                files.append({'relative_path':name,'bytes':s.st_size,'identity':identity(s),'link_count':s.st_nlink})
    return sorted(files,key=lambda r:r['relative_path']),sorted(dirs)
def hash1(rows,prefix):
    h=hashlib.sha256()
    for r in sorted(rows,key=lambda r:(prefix+'/'+r['relative_path']).encode('utf-8')):
        name=prefix+'/'+r['relative_path'];h.update((r['sha256']+'  '+name+'\n').encode('utf-8'))
    return 'h1:'+base64.b64encode(h.digest()).decode('ascii')
assert OUT.name=='29646a104712459fb211fc6f80545bf0'
plain(OUT,'dir');assert not FORK.exists()
author_handoff=doc(AUTHOR/'handoff.json');assert digest(raw(AUTHOR/'handoff.json'))=='cf24eb27c506f0e4fb524ab39cf29459433452326bf1e625df86f275fd503f57'
peer_handoff=doc(PEER/'handoff.json');assert digest(raw(PEER/'handoff.json'))=='282a97352c1dd11e37c8712f755288e4ce971f83616f5f87df1f97365b1b082f'
for package in (AUTHOR,PEER):
    mf=doc(package/'manifest.json')
    for r in mf['files']:verify(r)
candidate=verify(author_handoff['candidate_ref']);assert len(candidate)==45071 and digest(candidate)=='0eea393caed04ad05ff9a8ca2a1e81d6dc3ad519728ebfcd62fec66b1101e2cb'
patch=verify(author_handoff['patch_ref']);assert len(patch)==847
original_pins=doc(AUTHOR/'inputs.before.json')
for pair in original_pins:
    p=Path(pair['original']['path'])
    if p.is_relative_to(MODULE):verify(pair['original'])
original_go=raw(MODULE/'sqlite.go');assert digest(original_go)=='095b77ed583de9b845814210debf6ca0a4e3b23d0134006db9e577e81db709d9'
write('origin/original-sqlite.go',original_go)
write('origin/modernc-sqlite-innocuous.patch',patch)
write('origin/reviewed-driver-handoff.json',raw(AUTHOR/'handoff.json'))
write('origin/independent-review-handoff.json',raw(PEER/'handoff.json'))
for name in ['REVIEW.md','source-review.json','oracle-review.json']:
    write('origin/independent-'+name,read_input(PEER/name))
for name in ['v1.60.1.info','v1.60.1.mod','v1.60.1.ziphash']:
    write('origin/cache-'+name,read_input(CACHE/name))
cache_inventory=[p.name for p in sorted(CACHE.iterdir()) if p.is_file()]
root_mod=read_input(ROOT/'go.mod');root_sum=read_input(ROOT/'go.sum')
write('origin/consumer-original.go.mod',root_mod);write('origin/consumer-original.go.sum',root_sum)
algorithm=ROOT/'.local/tools/go1.27.1/go/src/cmd/vendor/golang.org/x/mod/sumdb/dirhash/hash.go'
write('origin/dirhash-hash.go',read_input(algorithm))
initial,dirs=inventory(MODULE);assert len(initial)==1899 and sum(r['bytes'] for r in initial)==150427576
js('inventory.original.json',{'root':MODULE.as_posix(),'files':initial,'directories':dirs,'symlink_reparse_count':0,'scope':'all files including hidden/testdata/GOOS variants; not a selected Go build subset'})
before=[]
for entry in initial:
    p=MODULE/entry['relative_path'];b=raw(p);before.append({'relative_path':entry['relative_path'],**ref(p,b)})
js('module.before.json',{'module':'modernc.org/sqlite','version':'v1.60.1','files':before,'file_count':len(before),'bytes':sum(r['bytes'] for r in before)})
FORK.mkdir(parents=True,exist_ok=False)
for d in dirs:(FORK/d).mkdir(parents=True,exist_ok=True)
copied=[]
for r in before:
    p=Path(r['path']);b=raw(p);assert digest(b)==r['sha256'] and len(b)==r['bytes']
    output=candidate if r['relative_path']=='sqlite.go' else b
    target=FORK/r['relative_path'];plain(target.parent,'dir')
    with target.open('xb') as f:f.write(output)
    actual=ref(target);assert actual['sha256']==digest(output) and actual['bytes']==len(output)
    copied.append({'relative_path':r['relative_path'],**actual})
after_inventory,after_dirs=inventory(MODULE);assert after_inventory==initial and after_dirs==dirs
after=[]
for r in before:
    now=ref(Path(r['path']));assert now['sha256']==r['sha256'] and now['bytes']==r['bytes'];after.append({'relative_path':r['relative_path'],**now})
js('module.after.json',{'files':after,'file_count':len(after),'source_drift_count':0,'inventory_drift_count':0,'source_cache_written':False})
fork_inventory,fork_dirs=inventory(FORK)
assert [r['relative_path'] for r in fork_inventory]==[r['relative_path'] for r in initial] and fork_dirs==dirs
by={r['relative_path']:r for r in before}
changed=[r['relative_path'] for r in copied if (r['sha256'],r['bytes'])!=(by[r['relative_path']]['sha256'],by[r['relative_path']]['bytes'])]
assert changed==['sqlite.go']
fork_lock=js('fork.file-lock.json',{'schema':'researchos.full-local-module-file-lock.v1','module_path':'modernc.org/sqlite','upstream_version':'v1.60.1','root':FORK.as_posix(),'files':copied,'directories':fork_dirs,'file_count':len(copied),'bytes':sum(r['bytes'] for r in copied),'changed_files':changed,'go_sum_authenticates_local_replace':False,'default_innocuous':False})
up_h1=hash1(before,PREFIX);fork_h1=hash1(copied,PREFIX)
mod_hash='h1:'+base64.b64encode(hashlib.sha256((digest(raw(MODULE/'go.mod'))+'  go.mod\n').encode()).digest()).decode()
expected_module=[line.split()[2] for line in root_sum.decode().splitlines() if line.split()[:2]==['modernc.org/sqlite','v1.60.1']]
expected_mod=[line.split()[2] for line in root_sum.decode().splitlines() if line.split()[:2]==['modernc.org/sqlite','v1.60.1/go.mod']]
assert len(expected_module)==len(expected_mod)==1
ziphash=raw(CACHE/'v1.60.1.ziphash').decode().strip()
origin=js('module-origin-verification.json',{'schema':'researchos.local-module-origin-check.v1','module_directory_ref':ref(OUT/'module.before.json'),'cache_info':json.loads(raw(CACHE/'v1.60.1.info')),'cache_info_authority':'local metadata only; no live upstream/git/signature verification','cache_inventory':cache_inventory,'zip_present':'v1.60.1.zip' in cache_inventory,'algorithm_ref':ref(algorithm),'algorithm':'pure Python byte-level transcription of frozen dirhash.Hash1; Go tool not invoked','directory_h1':up_h1,'cached_ziphash':ziphash,'consumer_go_sum_h1':expected_module[0],'directory_matches_cached_ziphash':up_h1==ziphash,'directory_matches_consumer_go_sum':up_h1==expected_module[0],'go_mod_h1':mod_hash,'consumer_go_mod_h1':expected_mod[0],'go_mod_matches_consumer':mod_hash==expected_mod[0],'cache_mod_matches_directory':raw(CACHE/'v1.60.1.mod')==raw(MODULE/'go.mod'),'fork_directory_h1_informational':fork_h1,'fork_h1_not_upstream_h1':fork_h1!=up_h1,'upstream_zip_reconstruction_or_download':False,'upstream_authentication':'OPEN: absent module zip and no independent upstream verification; any hash mismatch also remains OPEN'})
original_tests=doc(AUTHOR/'future-tests.proposed.json');tests=json.loads(json.dumps(original_tests))
wrong='Function flags mask must exactly equal UTF8 | optional DETERMINISTIC | optional INNOCUOUS, no other bits'
assert tests['methods'].count(wrong)==1
tests['methods'][tests['methods'].index(wrong)]='PRAGMA function_list: enc must equal utf8; flags must equal optional DETERMINISTIC | optional INNOCUOUS exactly, without UTF8 or unknown bits. Also assert builtin=0, exact name/type/narg.'
tests['internal_eTextRep_note']='UTF8=1 belongs only to internal create-function eTextRep, not function_list.flags.'
tests['function_list_oracle']=[{'deterministic':d,'innocuous':i,'internal_eTextRep':1+(2048 if d else 0)+(2097152 if i else 0),'enc':'utf8','flags':(2048 if d else 0)+(2097152 if i else 0),'builtin':0,'state':'NOT_RUN'} for d,i in [(False,False),(True,False),(False,True),(True,True)]]
assert tests['cases']==original_tests['cases'] and tests['count']==18 and tests['state']=='ALL_NOT_RUN'
tests_ref=js('future-tests.corrected.proposed.json',tests)
write('future-tests.oracle-only.patch',''.join(difflib.unified_diff(json.dumps(original_tests,ensure_ascii=False,indent=2).splitlines(True),json.dumps(tests,ensure_ascii=False,indent=2).splitlines(True),fromfile='original/future-tests.proposed.json',tofile='corrected/future-tests.proposed.json')))
licenses=[r for r in copied if any(x in r['relative_path'].lower() for x in ('license','notice','copying'))]
js('license-and-module-preservation.json',{'license_notice_files':licenses,'all_module_files_preserved_except_exact_sqlite_go':True,'go_mod_ref':ref(FORK/'go.mod'),'go_sum_ref':ref(FORK/'go.sum'),'original_go_mod_ref':ref(MODULE/'go.mod'),'original_go_sum_ref':ref(MODULE/'go.sum'),'transitive_dependency_sources_bundled':False,'module_directives_unchanged':True})
contract=js('consumer-and-driver-validation.contract.proposed.json',{'schema':'researchos.sqlite-local-fork-consumer-contract.v1','authorized':False,'actual_grant':None,'proposed_destination':'third_party/modernc_sqlite_v1_60_1_researchos_innocuous','version_qualified_replace':'replace modernc.org/sqlite v1.60.1 => ./third_party/modernc_sqlite_v1_60_1_researchos_innocuous','consumer_go_mod_before_ref':ref(ROOT/'go.mod'),'consumer_go_sum_before_ref':ref(ROOT/'go.sum'),'preserve_existing_upstream_go_sum':True,'local_replace_authentication':fork_lock,'no_implicit_all_versions_replace':True,'frozen_driver_candidate_ref':author_handoff['candidate_ref'],'required_source_adoption_gate':['Non-author complete fork/origin/lock/oracle review','Root exact dependency source/resource lease and explicit target tuple','Resolve or explicitly retain upstream-origin OPEN conditions before adoption'],'future_compile_gate':['Actual selected module/version/Dir/Replace evidence from separately authorized Go list','Pinned Go1.27.1 with GOTOOLCHAIN=local GOENV=off and isolated project caches','Freeze complete Go -deps -test -compiled graph, GOOS variants, embed files, go.mod/sum, importcfg, WORK/archive/generated testmain, compiler/link/executable/runtime inputs','Consumer full compile including exported FunctionImpl keyed/unkeyed literal compatibility; no layout/ABI equivalence claim','New driver test source needs exact future owner path/lease; do not overwrite existing func_test.go'],'future_driver_validation_ref':tests_ref,'case_count':18,'all_cases':'NOT_RUN','I17_blockers':['Three F08 callbacks remain incomplete/OPEN','Must not substitute all-error partial callback for positive F08 schema OFF authorization'],'future_SQL_requirements':['trusted_schema=OFF readback on each physical test connection','Foreign key and recursive trigger settings/actual schema paths independently captured','Scalar/aggregate/window routes and encoding/flags exact 2x2','Strict actual unsafe-use/semantic rejection reasons; no setup/compile false positive','Original DB handles closed before evidence snapshot; no private/user DB'],'limits':'No consumer compile/driver validation/adoption authorized by this receipt; Root must separately freeze finite execution caps/controller/OS closure','old22_23_and_SQL24_upgrade_backup_rollback':'OPEN separate qualification, no inherited acceptance'})
for r in list(INPUTS.values()):
    now=ref(Path(r['path']));assert now==r,('input drift',r['path'])
inputref=js('inputs.before-after.json',{'files':sorted(INPUTS.values(),key=lambda r:r['path']),'drift_count':0,'author_peer_originals_unchanged':True})
audit=js('copy-audit.json',{'schema':'researchos.complete-fork-copy-audit.v1','module_before_ref':ref(OUT/'module.before.json'),'module_after_ref':ref(OUT/'module.after.json'),'fork_lock_ref':fork_lock,'original_file_count':len(before),'copied_file_count':len(copied),'original_bytes':sum(r['bytes'] for r in before),'fork_bytes':sum(r['bytes'] for r in copied),'changed_files':changed,'changed_file_ref':ref(FORK/'sqlite.go'),'candidate_exact_equal':raw(FORK/'sqlite.go')==candidate,'original_go_mod_sum_unchanged':raw(FORK/'go.mod')==raw(MODULE/'go.mod') and raw(FORK/'go.sum')==raw(MODULE/'go.sum'),'symlink_reparse_or_escape':0,'all_source_reads_identity_checked_before_after':True,'destination_exclusive_regular_files':True,'directory_inventory_unchanged':True,'source_cache_writes':0,'Main_source_canonical_index_writes':0,'Go_gofmt_SQL_Node_SDK_HTTP_model_calls':0,'actual_tests':0,'new_failures':[],'TOCTOU_boundary':'lstat/resolve before and after normal file IO; no OS handle-level anti-race proof is claimed','implicit_rowid_or_DB_checks':'not applicable; no SQL'})
handoff=js('handoff.json',{'schema':'researchos.sqlite-complete-fork-resource-handoff.v1','actor':'codex:/root/sources_parent_impl','status':'RESOURCE_BUNDLE_PREPARED_NOT_ADOPTED','writer':'STOPPED','source_module':MODULE.as_posix(),'fork_root':FORK.as_posix(),'exact_driver_candidate_ref':ref(FORK/'sqlite.go'),'fork_lock_ref':fork_lock,'origin_verification_ref':origin,'copy_audit_ref':audit,'input_closure_ref':inputref,'corrected_18_test_proposal_ref':tests_ref,'consumer_contract_ref':contract,'author_handoff_ref':ref(AUTHOR/'handoff.json'),'peer_handoff_ref':ref(PEER/'handoff.json'),'file_count':len(copied),'source_bytes':sum(r['bytes'] for r in before),'fork_bytes':sum(r['bytes'] for r in copied),'changed_files':changed,'default_Innocuous':False,'module_go_mod_go_sum_and_licenses':'original bytes retained','directory_h1_matches_root_go_sum':up_h1==expected_module[0],'go_mod_h1_matches_root_go_sum':mod_hash==expected_mod[0],'module_zip_available':False,'source_acceptance':False,'SQL24_adoption_allowed':False,'formal_increment':0,'execution_authorized':False,'tests':'18 NOT_RUN','open':['Upstream module zip absent; local origin metadata is not online/authenticated upstream proof','Any recorded h1 mismatch requires explicit review, never ignored','Full transitive dependency/compiled/runtime consumer closure not built','Actual driver18, old22/23 compatibility and SQL24/F08 gates not executed','F08 pure callback implementation remains independently OPEN'],'new_failure_origins':[],'failure_counter_written':False,'preserved_prior_scope_deviation':'bd3 scope-deviation.empty-add-file.json unchanged; no native1 invented or recounted','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
ast.parse(Path(__file__).read_text(encoding='utf-8'))
files=[ref(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p!=OUT/'manifest.json']
mf=js('manifest.json',{'schema':'researchos.receipt-manifest.v1','files':files,'self_excluded':True})
print(json.dumps({'handoff_ref':handoff,'manifest_ref':mf,'listed_files':len(files),'file_count':len(copied),'changed_files':changed,'directory_h1':up_h1,'matches_root_go_sum':up_h1==expected_module[0],'go_mod_matches_root_go_sum':mod_hash==expected_mod[0],'status':'STOPPED','target_calls':0},ensure_ascii=False))
