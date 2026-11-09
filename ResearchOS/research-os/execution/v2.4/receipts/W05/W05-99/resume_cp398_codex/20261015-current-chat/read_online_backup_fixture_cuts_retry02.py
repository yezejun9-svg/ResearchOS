import hashlib
import json
from pathlib import Path
import subprocess

R=Path('D:/作品集/ResearchOS/research-os')
E=R/'execution/v2.4/receipts/W05/W05-99/online_backup_source_resource_map_codex/20261015-current-chat'
O=E/'fixture-qualification-intake03'
O.mkdir(exist_ok=False)
def put(p,v):
    with p.open('x',encoding='utf8') as f: json.dump(v,f,ensure_ascii=False,indent=2)
def ref(p):
    b=p.read_bytes()
    return {'path':p.relative_to(R).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
argv=['rg','-n','--glob','*.go',r'func .*AcquireDataRootLease|func .*newFixture|type .*Fixture|func .*SnapshotWorkspace','internal']
put(O/'01-locators.recipe.json',{'argv':argv,'cwd':str(R),'env':{}})
z=subprocess.run(argv,cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
(O/'01-locators.stdout.raw').write_bytes(z.stdout)
(O/'01-locators.stderr.raw').write_bytes(z.stderr)
put(O/'01-locators.result.json',{'native_exit':z.returncode})
assert z.returncode==0
reads={'internal/domain/backup_test.go':[(1,65)],'internal/domain/backup_cli_test.go':[(1,120)],'internal/domain/backup_workspace.go':[(1,145)],'internal/domain/runtime_model_stream_test.go':[(1,90)],'ops/backup/main.go':[(1,105),(195,280)]}
put(O/'reads.recipe.json',{'reads':reads,'previous_native_failure':'intake02 rg had nonexistent internal/runtime operand; original raw retained'})
outputs={}
refs=[]
for p,spans in reads.items():
    source=R/p
    lines=source.read_text(encoding='utf8').splitlines()
    outputs[p]='\n'.join(f'{n}: {v}' for a,b in spans for n,v in enumerate(lines,1) if a<=n<=b)
    q=O/(source.name+'.selected.txt')
    q.write_text(outputs[p],encoding='utf8')
    refs += [ref(source),ref(q)]
put(O/'intake.json',{'reads':refs,'commands':[ref(O/('01-locators'+s)) for s in ['.recipe.json','.stdout.raw','.stderr.raw','.result.json']]})
print(json.dumps({'intake':ref(O/'intake.json'),'selections':outputs,'locators':z.stdout.decode('utf8'),'prior_rg_stderr':(E/'fixture-qualification-intake02/01-locators.stderr.raw').read_text(encoding='utf8')},ensure_ascii=False))
