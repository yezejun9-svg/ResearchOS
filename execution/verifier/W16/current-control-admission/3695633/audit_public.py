from pathlib import Path
import hashlib,json,subprocess
source=Path(r'D:/作品集/ResearchOS/research-os/.local/worktrees/control-business-proof')
out=Path(__file__).parent
receipts=source/'execution/receipts/W16/current-control-admission'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda b:hashlib.sha256(b).hexdigest()
git=lambda *a:subprocess.check_output(['git','-C',str(source),*a]).decode().strip()
manifest=load(receipts/'manifest.json')['hashes']
checks={p:'sha256:'+sha((receipts/p).read_bytes())==h for p,h in manifest.items()}
before=load(receipts/'attempt-10-first-evaluation/source-before.json')
after=load(receipts/'attempt-10-first-evaluation/source-after.json')
build=load(receipts/'attempt-10-first-evaluation/actual-build.json')
inventory=build['source_provenance']['files']
inventory_checks={p:'sha256:'+sha((source/p).read_bytes())==h for p,h in inventory.items()}
changed=git('diff-tree','--no-commit-id','--name-only','-r','36956330065ef7dc9e91005850ee19e1dea69a48').splitlines()
channel=git('diff-tree','--no-commit-id','--name-only','-r','34f9c0dd21ce44d3ba9a61ab519195fd9dfff63d').splitlines()
binding={}
for p in sorted(set(changed+channel)):
    committed=subprocess.check_output(['git','-C',str(source),'show','36956330065ef7dc9e91005850ee19e1dea69a48:'+p])
    binding[p]={'working_hash':sha((source/p).read_bytes()),'commit_hash':sha(committed),'execution_hash':before['files'].get(p)}
result={'source_commit':'36956330065ef7dc9e91005850ee19e1dea69a48','raw_head':git('rev-parse','HEAD'),'dirty_status':git('status','--short'),'manifest_checks':checks,'manifest_count':len(checks),'execution_head':before['head'],'execution_dirty':before['dirty'],'before_after_exact_files':before['files']==after['files'],'execution_inventory_count':len(before['files']),'source_inventory_checks':inventory_checks,'source_inventory_count':len(inventory),'changed_source_binding':binding,'actual_image_hash':'sha256:'+sha(Path(build['image_path']).read_bytes()),'expected_image_hash':build['binary_hash']}
assert all(checks.values()) and all(inventory_checks.values())
assert result['before_after_exact_files']
assert all(x['working_hash']==x['commit_hash']==x['execution_hash'] for x in binding.values())
assert result['actual_image_hash']==result['expected_image_hash']
(out/'public-binding-audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['execution_dirty','manifest_checks','source_inventory_checks','changed_source_binding']},ensure_ascii=False))
