import pathlib,hashlib,json,shutil,subprocess,sys,os
O=pathlib.Path(r'C:/Users/yqyyds/.codex/researchos-build-worktrees/normal-qualification-observer-v3-review-20261012');D=pathlib.Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/normal_qualification_actual_observer_v3_codex/20261012-current-chat');C=pathlib.Path(r'C:/Users/yqyyds/.codex/researchos-resource-cache/researchos-storage-continuation-cp441-20261012/observer-v3')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(D/'manifest.json')=='06ee2e6504439bde03b1ebc238db5847221bbd0025df8b74ace94750bc3c5c7c';m=json.loads((D/'manifest.json').read_text());refs=[]
for member in m['members']:
 for root in [D,C]:
  p=root/member['path'];assert p.is_file() and sha(p)==member['sha256'],str(p);refs.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
 p=D/member['path'];q=O/'frozen-source'/member['path'];q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
primary=pathlib.Path(r'C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012/internal/canonical/jcs.go');assert sha(primary)==m['primary_jcs_source']['sha256'];refs.append({'path':str(primary),'sha256':sha(primary)})
refs.append({'path':str(D/'manifest.json'),'sha256':sha(D/'manifest.json')});(O/'binding-before.json').write_text(json.dumps({'refs':refs,'source_manifest_sha256':sha(D/'manifest.json'),'original_database_opened':False},indent=2)+'\n')
fixture=O/'author-replay';fixture.mkdir()
for n in ['observe.py','controlled_validation.py']:(fixture/n).write_bytes((D/n).read_bytes())
shutil.copytree(D/'go-jcs-oracle',fixture/'go-jcs-oracle')
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['TEMP']=str(O/'temp');env['TMP']=env['TEMP'];(O/'temp').mkdir()
args=[sys.executable,'-X','utf8',str(fixture/'controlled_validation.py')];p=subprocess.run(args,cwd=O,env=env,capture_output=True,timeout=45)
(O/'author-replay.stdout.raw').write_bytes(p.stdout);(O/'author-replay.stderr.raw').write_bytes(p.stderr);(O/'author-replay.invocation.json').write_text(json.dumps({'argv':args,'cwd':str(O),'exit':p.returncode,'env':{k:env[k] for k in ['PYTHONDONTWRITEBYTECODE','TEMP','TMP']}},indent=2)+'\n');assert p.returncode==0,p.stderr
print(json.dumps({'source_members_verified_both_roots':len(m['members']),'author_replay_exit':p.returncode,'fixtures_created_on_C':9}))
