from pathlib import Path
import hashlib
import json
import shutil

root = Path(__file__).resolve().parent
author = root.parent/'product-v1-cli-s04-author'
pins = {
 'final/source-manifest.json':'6138822e5c28a596cce3363a8850612e7a81ac119d67bd5659f0da8d349fc99a',
 'final/freeze.json':'6792d0f73fd4209ad1a13179bf8980da2b46efdebe641a02962592cbc2b21411',
 'final/summary.json':'20e80713eeb41675282ab3398f919ba57e2f5a16474c782dcd77bb5b0ca80dbf',
 'diagnostics.json':'11c58d24133dda26e798a2aa69e2204020c8ec4b051ed43cc6874617b0680f40',
 'archive-file-list.json':'b37c6b557009986785041ba7aad025a761d3f24607b9d1c721ad1530359319a0',
}
sha = lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
names = list(pins) + ['attempt-01/test.jsonl','attempt-01/test.result.json','attempt-03/test.jsonl','attempt-03/test.result.json','attempt-03/vet.log','attempt-03/vet.result.json','attempt-03/fmt.log','attempt-03/fmt.result.json','attempt-03/source-manifest.json','attempt-03.ps1','final/git-status.txt','final/git-diff-check.txt','final/main.diff']
report=[]
for name in names:
 source=author/name
 if name in pins: assert sha(source)==pins[name]
 if not source.is_file():
  report.append({'path':name,'present':False});continue
 target=root/'author-evidence'/name
 target.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(source,target)
 report.append({'path':name,'sha256':sha(source),'copy_sha256':sha(target),'bytes':source.stat().st_size})
(root/'author-evidence-pins.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'author_pins_verified':len(pins),'copied':sum(row.get('present') is not False for row in report),'no_author_source_changes':True}))
