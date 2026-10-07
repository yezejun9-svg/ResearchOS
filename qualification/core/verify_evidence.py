from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
q=ROOT/'qualification/core'
commands=list((q/'evidence').glob('*/command.json'))
assert len(commands)>=15
for path in commands:
 record=read(path)
 assert record['cwd'] and record['argv'] and record['started_at'] and record['ended_at']
 for stream in ('stdout','stderr'):
  assert sha(path.parent/(stream+'.txt'))==record[stream+'_sha256'],str(path)
source=read(q/'source.json')
assert source['commit']=='d554c4789ed3930f8a53ac9fdf6503b3187097da'
assert (q/'evidence/source-head/stdout.txt').read_text().strip()==source['commit']
assert (q/'evidence/source-tag/stdout.txt').read_text().strip()==source['commit']
assert not (q/'evidence/final-source-status/stdout.txt').read_bytes()
for entry in read(q/'source-excerpts.json')['files']:
 local=ROOT/'.local/paperclip'/entry['path']
 if local.exists():
  assert sha(local)==entry['sha256'],entry['path']
  lines=local.read_text(encoding='utf-8').splitlines()
  for part in entry['ranges']:
   assert '\n'.join(lines[part['start_line']-1:part['end_line']])==part['text']
results=read(q/'results.json');cases=read(q/'cases.json')['cases']
assert {x['case_id'] for x in results['cases']}=={x['case_id'] for x in cases}
assert len(results['cases'])==16 and all(x['status']=='BLOCKED' for x in results['cases'])
for case in results['cases']:
 for ref in case['raw_evidence_references']:assert (ROOT/ref).is_file()
assert results['function_probe']['normal_completion']['status']=='PASS'
assert results['function_probe']['policy_clear']['status']=='FAIL'
assert read(q/'evidence/documented-start/command.json')['exit_code']==1
assert read(q/'evidence/final-health-probe/command.json')['exit_code']==1
attempts=read(q/'attempts.json')
assert len(attempts['approaches'])<=2 and all(x['repair_rounds']<=1 for x in attempts['approaches'])
assert read(ROOT/'execution/route.json')['selected_route']=='THIN_CORE'
assert read(ROOT/'execution/route.json')['product_acceptance']=='NOT_RUN'
print(json.dumps({'status':'PASS','scope':'EVIDENCE_INTEGRITY_AND_RECORDED_FALLBACK_ONLY','command_records':len(commands),'case_records':16,'product_tests':'NOT_RUN'}))
