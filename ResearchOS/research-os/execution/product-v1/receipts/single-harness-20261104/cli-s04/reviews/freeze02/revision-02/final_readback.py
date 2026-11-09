from pathlib import Path
import hashlib
import json
import subprocess

root=Path(__file__).resolve().parent
stage=json.loads((root/'pin-stage.json').read_text(encoding='utf-8'))
wt=Path(stage['worktree']);repo=Path('D:/作品集/ResearchOS/research-os')
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
directory=root/'final-checks';directory.mkdir(exist_ok=False)
gofmt=repo/'.local/tools/go1.27.1/go/bin/gofmt.exe'
git=Path('C:/Program Files/Git/cmd/git.exe')
assert sha(git)=='da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f'
names=[row['path'] for row in stage['exact3']]
commands=[('fmt',[str(gofmt),'-d',*[str(root/'source-snapshot'/name) for name in names]]),
          ('diff',[str(git),'-C',str(wt),'diff','--check']),
          ('status',[str(git),'-C',str(wt),'status','--short','--untracked-files=all','-z'])]
results=[]
for label,argv in commands:
 (directory/(label+'.command.json')).write_text(json.dumps(argv,ensure_ascii=False)+'\n',encoding='utf-8')
 result=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
 (directory/(label+'.stdout')).write_bytes(result.stdout);(directory/(label+'.stderr')).write_bytes(result.stderr)
 results.append({'command':label,'exit_code':result.returncode,'stdout_empty':not result.stdout})
 if label=='status': changed=sorted(row[3:].decode('utf-8') for row in result.stdout.split(b'\0') if row)
checks=[{'path':row['path'],'expected':row['sha256'],'live_sha256':sha(wt/row['path']),'snapshot_sha256':sha(root/'source-snapshot'/row['path'])} for row in stage['exact3']]
all_match=all(row['expected']==row['live_sha256']==row['snapshot_sha256'] for row in checks)
report={'commands':results,'gofmt_sha256':sha(gofmt),'changed':changed,'exact_scope':changed==sorted(names),'checks':checks,'all_match':all_match,'no_source_writes':True}
(directory/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
raise SystemExit(0 if all(row['exit_code']==0 for row in results) and results[0]['stdout_empty'] and all_match and report['exact_scope'] else 1)
