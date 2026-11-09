from pathlib import Path
import hashlib,json,subprocess,datetime
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-normal-model-ui-repair-v3-20261012'
CANDIDATE='2f48ad7d4cd3cececf06a2a9a059a36ba157032c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip()==CANDIDATE
(OUT/'candidate-full.diff').write_bytes(subprocess.check_output(['git','diff','292ad860f9e76cf2795d5a3010da1d114d01ff56',CANDIDATE],cwd=WT))
(OUT/'candidate-tracked-status.txt').write_bytes(subprocess.check_output(['git','status','--short','-uno'],cwd=WT))
assert not (OUT/'candidate-tracked-status.txt').read_text().strip()
files=[]
for p in sorted(OUT.rglob('*')):
    if p.is_file() and p.name not in ('receipt_manifest.json','review-seal.json'):
        files.append(dict(path=p.relative_to(OUT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
manifest=dict(schema='researchos.independent-review-manifest/1',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='REQUEST_CHANGES',candidate=CANDIDATE,model_calls=0,external_calls=0,files=files)
(OUT/'receipt_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
seal=dict(decision='REQUEST_CHANGES',files=len(files),decision_sha256=sha(OUT/'independent-review.json'),manifest_sha256=sha(OUT/'receipt_manifest.json'))
(OUT/'review-seal.json').write_text(json.dumps(seal,indent=2)+'\n',encoding='utf-8')
print(json.dumps(seal))
