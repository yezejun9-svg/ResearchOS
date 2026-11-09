import hashlib,json,os,pathlib,subprocess
E=pathlib.Path(__file__).parent
W=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/desktop-main7d-native-20261025')
A=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/desktop_main7d_native_codex/20261025-current-chat/complete-tree')
COMMIT='ecc28dd3c91a0f68dcddb41b53325aa7f0e81419';TREE='1d44a02c9483fc529b08ffe81895ec443920bdd1'
freeze=json.loads((E/'r3-fixed-inputs/SOURCE-FREEZE-03.json').read_bytes())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def git(*args):return subprocess.run(['git','--no-optional-locks','-C',str(W),*args],capture_output=True,check=True).stdout
assert git('rev-parse','HEAD').decode().strip()==COMMIT
assert git('show','-s','--format=%T','HEAD').decode().strip()==TREE
assert git('rev-parse','HEAD^').decode().strip()==freeze['base_commit']
assert not git('status','--porcelain=v1','--untracked-files=all')
diff=git('diff-tree','--no-commit-id','--name-status','-r',COMMIT).decode().splitlines()
assert len(diff)==7 and sum(x.startswith('A\t') for x in diff)==6 and sum(x.startswith('M\t') for x in diff)==1
assert sorted(x.split('\t')[1] for x in diff)==freeze['candidate_delta']
for name,row in freeze['seven_file_hashes'].items():
    content=git('show',COMMIT+':'+name)
    assert hashlib.sha256(content).hexdigest()==row['sha256'] and len(content)==row['bytes']
    assert sha(W/name)==row['sha256']
post=A/'POSTCOMMIT-VALIDATION.json'
assert sha(post)=='72f0d5cf4db4ec775f5b103cf6529748c87ce57664679da15c3d38385264ee00'
with (E/'r3-fixed-inputs/POSTCOMMIT-VALIDATION.json').open('xb') as f:f.write(post.read_bytes())
B=W/'.local/desktop-complete-20261025-02';state=E/'never-created-r3-dryrun-state'
assert not state.exists()
node=B/'apps/desktop/resources/control/runtime/node.exe'
assert sha(node)=='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
argv=[str(node),str(B/'launch-development.mjs'),'--bundle',str(B),'--state',str(state),'--dry-run']
env={k:v for k,v in os.environ.items() if k.upper() in ['SYSTEMROOT','WINDIR','COMSPEC','OS','PATH','PATHEXT']}
out=E/'r3-actual-dry-run';out.mkdir(exist_ok=False)
(out/'recipe.json').write_text(json.dumps({'argv':argv,'cwd':str(B),'env_keys':sorted(env),'candidate':COMMIT,'manifest_sha256':'e1d61b68d12c61e2dda341df3541d2b4b541b9c2331af5da26ca56dff759b620','mode':'NO_STATE_NO_SPAWN'},indent=2),encoding='utf-8')
p=subprocess.run(argv,cwd=B,env=env,capture_output=True)
(out/'stdout.raw').write_bytes(p.stdout);(out/'stderr.raw').write_bytes(p.stderr)
result={'native_exit':p.returncode,'stdout_sha256':sha(out/'stdout.raw'),'stderr_sha256':sha(out/'stderr.raw')}
(out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
assert p.returncode==0 and not state.exists()
report=json.loads(p.stdout);assert report['mode']=='DRY_RUN_NO_STATE_NO_SPAWN' and report['inventory_count']==132
assert report['manifest_sha256']=='e1d61b68d12c61e2dda341df3541d2b4b541b9c2331af5da26ca56dff759b620'
summary={'status':'EXACT_CANDIDATE_AND_ACTUAL_BUNDLE_DRYRUN_MATCH','candidate_commit':COMMIT,'candidate_tree':TREE,'parent':freeze['base_commit'],'changed_files':diff,'clean':True,'source_digest':freeze['source_snapshot_digest'],'dryrun':result,'manifest_sha256':report['manifest_sha256'],'state_created':False,'native_gui_or_core_starts':0}
(E/'R3-candidate-and-dryrun-independent-check.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary))
