import pathlib,json,hashlib,shutil,subprocess
E=pathlib.Path(__file__).parent;R=pathlib.Path('D:/作品集/ResearchOS/research-os');W=R/'.local/worktrees/desktop-main7d-native-20261025';A=R/'execution/v2.4/receipts/W05/W05-99/desktop_main7d_native_codex/20261025-current-chat/complete-tree';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
P=A/'SOURCE-FREEZE-02.json';assert sha(P)=='6d885a649bb020d702487d5331f394cc43b3fd1c22d00a11822289ba7d644d3b';f=json.loads(P.read_text(encoding='utf-8'))
scope=json.loads((E/'Desktop-complete-tree-source-scope.json').read_text(encoding='utf-8'));assert set(f['candidate_delta'])==set(scope['source_write_allowlist'])
patch=pathlib.Path(f['patch']['path']);assert sha(patch)==f['patch']['sha256'];assert patch.stat().st_size==73782
F=E/'r2-fixed-inputs';F.mkdir(exist_ok=False);shutil.copyfile(P,F/P.name);shutil.copyfile(patch,F/patch.name)
S=E/'source-r2';S.mkdir(exist_ok=False)
for name,ref in f['seven_file_hashes'].items():
 assert sha(W/name)==ref['sha256'];assert (W/name).stat().st_size==ref['bytes'];dest=S/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(W/name,dest)
git=shutil.which('git');base=f['base_commit']
basefiles=['apps/desktop/build-validator.py','apps/desktop/main/lib/desktop-management.js','apps/desktop/main/lib/native.js','go.mod','go.sum']
refs=[]
for name in basefiles:
 raw=subprocess.check_output([git,'-C',str(R),'show',base+':'+name]);p=S/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 assert (W/name).read_bytes()==raw,name;refs.append({'path':name,'sha256':sha(p),'origin':base})
for name,ref in f['seven_file_hashes'].items():assert sha(W/name)==ref['sha256'];assert sha(S/name)==ref['sha256']
manifest={'freeze_sha256':sha(P),'patch_sha256':sha(patch),'base_commit':base,'base_tree':f['base_tree'],'candidate_commit':None,'snapshot':str(S),'seven':f['seven_file_hashes'],'unchanged_dependencies':refs,'snapshot_count_limit':'Own snapshot contains seven candidate files plus five unchanged direct test/review dependencies; full source591 digest pending independent recomputation/source closure review.'}
p=E/'R2-independent-snapshot-manifest.json';p.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'snapshot':str(S),'manifest_sha256':sha(p),'candidate_files':7,'base_dependencies':len(refs)},indent=2))
