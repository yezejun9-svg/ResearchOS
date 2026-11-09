import pathlib,json,hashlib,subprocess,shutil
B=pathlib.Path(__file__).parent
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
A=R/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp549/C57-independent-phase2-v12-amendment.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(A)=='1f051071c6ce5f3cc6d4e4eb55ac0f6cb0ee85ec79a229ef10d8b9492917ba64'
a=json.loads(A.read_text(encoding='utf-8'))
old=json.loads((B/'PHASE2-exact-snapshot-verification.json').read_text(encoding='utf-8'));S=pathlib.Path(old['snapshot'])
for ref in old['candidate_source_files']+old['inherited40']:assert sha(S/ref['path'])==ref['sha256'],ref['path']
supp=json.loads((B/'PHASE2-jobs/128-independent-concurrent-borrow.json').read_text(encoding='utf-8'))['supplementary_files']
for ref in supp:assert sha(S/ref['path'])==ref['sha256']
I=B/'PHASE2-v12-fixed-inputs';I.mkdir(exist_ok=False)
shutil.copyfile(A,I/A.name);refs=[]
for key,ref in a.items():
 if not key.endswith('_ref') or not isinstance(ref,dict):continue
 p=pathlib.Path(ref['path']);p=p if p.is_absolute() else R/p
 assert sha(p)==ref['sha256'],str(p)
 dest=I/(key+'-'+p.name);shutil.copyfile(p,dest)
 refs.append({'path':str(p),'sha256':sha(p),'copy':str(dest)})
manifestPath=R/a['source57_manifest_ref']['path'];manifest=json.loads(manifestPath.read_text(encoding='utf-8'))
git=shutil.which('git');assert git
def g(*args):return subprocess.check_output([git,'-C',str(R),*args])
commit=a['candidate_commit'];assert g('rev-parse',commit+'^{tree}').decode().strip()==a['candidate_tree']
assert g('rev-parse',commit+'^').decode().strip()==old['commit']
delta=g('diff','--name-only',old['commit'],commit).decode().splitlines()
assert sorted(delta)==sorted(a['source_snapshot_upgrade']['allowed_delta'])
blobs={}
for ref in manifest['files']:
 data=g('show',commit+':'+ref['path']);assert hashlib.sha256(data).hexdigest()==ref['sha256'],ref['path']
 if ref['path'] in delta:blobs[ref['path']]=data
 else:assert sha(S/ref['path'])==ref['sha256'],ref['path']
assert len(manifest['files'])==57
for ref in old['inherited40']:
 assert hashlib.sha256(g('show',commit+':'+ref['path'])).hexdigest()==ref['sha256']
preserve=B/'PHASE2-old08d63-preserved-delta2';preserve.mkdir(exist_ok=False);oldrefs=[]
for path in delta:
 dest=preserve/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/path,dest)
 oldrefs.append({'path':path,'sha256':sha(dest),'preserved':str(dest)})
for path,data in blobs.items():(S/path).write_bytes(data)
for ref in manifest['files']+old['inherited40']:assert sha(S/ref['path'])==ref['sha256']
for ref in supp:assert sha(S/ref['path'])==ref['sha256']
v={'schema':'researchos.c57.independent-phase2-snapshot.v2','amendment_sha256':sha(A),'commit':commit,'tree':a['candidate_tree'],'parent':old['commit'],'baseline':a['candidate_baseline'],'snapshot':str(S),'directory_label_is_not_source_version':True,'source57_verified':True,'inherited40_verified':True,'delta2_verified':True,'old_source_reconstructable_from_unchanged55_and_preserved2':True,'old2':oldrefs,'candidate_source_files':manifest['files'],'inherited40':old['inherited40'],'supplementary_files':supp,'fixed_inputs':refs}
V=B/'PHASE2-v12-snapshot-verification.json';V.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
runner=(B/'phase2_run.py').read_text(encoding='utf-8').replace("B/'PHASE2-exact-snapshot-verification.json'","B/'PHASE2-v12-snapshot-verification.json'")
(B/'phase2_run_v12.py').write_text(runner,encoding='utf-8')
for tag,oldjob in [('133-v12-boot-c','097-phase2-boot-c-owned-cache'),('134-v12-boot-d','108-phase2-boot-d-all-temp'),('135-v12-host-wiring','095-phase2-core-c-owned-cache')]:
 j=json.loads((B/'PHASE2-jobs'/f'{oldjob}.json').read_text(encoding='utf-8'));j['tag']=tag;j['supplementary_files']=supp
 if tag=='133-v12-boot-c':
  for key in ['TEMP','TMP','TMPDIR','GOTMPDIR']:j['env'][key]='C:/Users/yqyyds/.codex/researchos-fixture-cache/qualification-maintenance-c57-independent-review-20261025/native-c'
 if tag=='135-v12-host-wiring':
  j['argv']=j['argv'][:5]+['./internal/host','./apps/control','-run','^(TestQualification.*|TestControlReplayRefusesOrdinaryToken|TestControlReplaySecondWriterRefused)$']
 (B/'PHASE2-jobs'/f'{tag}.json').write_text(json.dumps(j,indent=2),encoding='utf-8')
print(json.dumps({'commit':commit,'tree':v['tree'],'snapshot_verification_sha256':sha(V),'delta':delta,'source57':57,'pins40':40,'supplements':len(supp)},indent=2))
