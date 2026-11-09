import argparse,hashlib,json,os,subprocess
from pathlib import Path
from datetime import datetime,timezone
root=Path('D:/作品集/ResearchOS/research-os')
wt=root/'.local/worktrees/cli-prompt-bridge-20261104'
out=root/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104'
base='fc2b1a50662580b1a0fca92559ca26be6e959f01'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def git(cwd,*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','-c','user.name=Codex','-c','user.email=codex@local.invalid','--no-optional-locks',*args],cwd=cwd,stderr=subprocess.STDOUT).decode('utf-8')
def put(path,value):
    tmp=path.with_name(path.name+'.new');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,path)
p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--review',required=True);p.add_argument('--review-sha',required=True);args=p.parse_args()
review=out/args.review;assert sha(review)==args.review_sha
manifest=json.loads((out/args.manifest).read_bytes())
rows=manifest['files']
if isinstance(rows,dict): files=rows
else: files={r['path']:r['sha256'] for r in rows}
assert len(files)==7 and all(path.startswith('apps/cli/') for path in files)
assert not (out/'integration-journal.json').exists(),'Inspect uncertain state first'
assert git(root,'rev-parse','HEAD').strip()==base and git(wt,'rev-parse','HEAD').strip()==base
assert not git(wt,'diff','--cached','--name-only').strip()
scope=json.loads((out/'scope.json').read_bytes())
for path,digest in scope['protected_before'].items():
    if path in ['execution/v2.4/checkpoint.json','execution/v2.4/HANDOFF_RESUME_PACK.md']:continue
    assert (sha(root/path) if (root/path).is_file() else 'ABSENT_BEFORE')==digest,path
for path,digest in files.items():assert sha(wt/path)==digest,path
git(wt,'diff','--check')
put(out/'integration-journal.json',{'status':'VERIFIED_BEFORE_COMMIT','base':base,'files':files,'review_sha256':args.review_sha})
git(wt,'add','--',*files)
assert set(git(wt,'diff','--cached','--name-only').splitlines())==set(files)
commit=git(wt,'commit','-m','feat(cli): route explicit task and run prompts through shared sessions')
head=git(wt,'rev-parse','HEAD').strip()
put(out/'integration-journal.json',{'status':'CANDIDATE_COMMITTED','base':base,'candidate':head,'commit_output':commit,'files':files})
git(root,'merge','--ff-only',head)
assert git(root,'rev-parse','HEAD').strip()==head
for path,digest in files.items():assert sha(root/path)==digest,path
protected={}
for path,digest in scope['protected_before'].items():
    if path in ['execution/v2.4/checkpoint.json','execution/v2.4/HANDOFF_RESUME_PACK.md']:continue
    actual=sha(root/path) if (root/path).is_file() else 'ABSENT_BEFORE'
    assert actual==digest,path
    protected[path]=actual
result={'status':'INDEPENDENT_SOURCE_REVIEWED_AND_INTEGRATED_WITH_BASELINE_TEST_BLOCKER','at':datetime.now(timezone.utc).isoformat(),'base_head':base,'main_head':head,'main_tree':git(root,'rev-parse','HEAD^{tree}').strip(),'files':files,'review':{'path':str(review.relative_to(root)),'sha256':args.review_sha},'source_manifest':{'path':str((out/args.manifest).relative_to(root)),'sha256':sha(out/args.manifest)},'protected_preserved':protected,'registry_revision_unchanged':41,'baseline_test_blocker':'TestW14CLICommandsUseRealSessionHTTP: HOST_REJECTED:WRITER_BUSY reproduced by candidate and exact-base source overlay; no old test or writer gate modified.','formal_increment':0,'native_or_provider_started':False}
put(out/'integration.json',result)
print(json.dumps({k:result[k] for k in ['status','main_head','main_tree','formal_increment']}))
