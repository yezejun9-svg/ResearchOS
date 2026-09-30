import hashlib, json, pathlib, subprocess
ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/research-cycle-driver')
OUT=pathlib.Path(__file__).parent
SOURCE='b1877d4a32f15868d19ed9d32f39fc2b6b563db9'
def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args])
files=git('diff-tree','--no-commit-id','--name-only','-r',SOURCE).decode().splitlines()
source=[]
for name in files:
    current=(ROOT/name).read_bytes()
    frozen=git('show',SOURCE+':'+name)
    source.append({'path':name,'sha256':hashlib.sha256(current).hexdigest(),'equals_frozen_source':current==frozen})
raw=[]
names=['bound-close-first','bound-close-second','cycle-binding-first','cycle-binding-native-pair','offline-native-experiment-first','offline-native-experiment-second','lifecycle-first','lifecycle-second','lifecycle-migration-third','drift-historical-ref-final','native-source-binding']
for name in names:
    path=ROOT/'execution/receipts/W08/research-driver'/f'{name}.jsonl'
    data=path.read_bytes()
    events=[json.loads(line) for line in data.decode('utf-8-sig').splitlines() if line.strip()]
    raw.append({'path':str(path.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(data).hexdigest(),'test_results':[{'test':e['Test'],'action':e['Action']} for e in events if e.get('Action') in ('pass','fail','skip') and 'Test' in e],'package_results':[e['Action'] for e in events if e.get('Action') in ('pass','fail','skip') and 'Test' not in e],'failure_lines':[e['Output'].strip() for e in events if e.get('OutputType')=='error']})
report={'source_commit':SOURCE,'evidence_head':git('rev-parse','HEAD').decode().strip(),'worktree_status':git('status','--porcelain').decode(),'source_files':source,'all_16_source_files_match_freeze':len(source)==16 and all(x['equals_frozen_source'] for x in source),'raw_audit':raw,'scope':'Read-only source/raw verification; no business test replay; separate monitor-cycle probe is in-memory SQLite only.'}
(OUT/'source-and-raw-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'source_matches':report['all_16_source_files_match_freeze'],'clean':report['worktree_status']=='','raw_files':len(raw),'package_results':{x['path'].split('/')[-1]:x['package_results'] for x in raw}},ensure_ascii=False))
