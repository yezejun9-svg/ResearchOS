from pathlib import Path
import subprocess,json,hashlib
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[4];REV='0b13836';PREFIX='execution/receipts/W06/runtime-s2/control-startup-1/'
def get(rev,path):return subprocess.check_output(['git','show',rev+':'+path],cwd=ROOT)
def sha(raw):return hashlib.sha256(raw).hexdigest()
target=OUT/'author-evidence';target.mkdir(parents=True,exist_ok=True);files=[]
for path in subprocess.check_output(['git','ls-tree','-r','--name-only',REV,'--',PREFIX],cwd=ROOT).decode().splitlines():
 raw=get(REV,path);(target/Path(path).name).write_bytes(raw);files.append({'path':path,'sha256':sha(raw),'bytes':len(raw)})
receipt=json.loads((target/'receipt.json').read_bytes());events=[json.loads(x) for x in (target/'stdout.jsonl').read_bytes().splitlines()];sources=[]
for path,expected in receipt['source_sha256'].items():
 raw=get(receipt['source_commit'],path);assert sha(raw)==expected;destination=OUT/'source'/path;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw);sources.append({'path':path,'sha256':sha(raw),'matches':True})
report={'mode':'Read-only evidence inspection, no new test or native process.','evidence_revision':REV,'source_revision':receipt['source_commit'],'files':files,'source_checks':sources,'test_runs':sum(e['Action']=='run' for e in events),'test_passes':sum(e['Action']=='pass' and bool(e.get('Test')) for e in events),'skips':[e for e in events if e['Action']=='skip'],'failures':[e for e in events if e['Action']=='fail'],'highlights':[e for e in events if 'STARTUP' in e.get('Output','')],'binary_note':'Receipt declares the separately built control binary hash. Its temporary binary is not retained here or independently rehashed by this read-only review.'}
assert report['test_runs']==report['test_passes']==1 and not report['skips'] and not report['failures']
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'source_matches':len(sources),'passes':report['test_passes'],'skips':len(report['skips'])}))
