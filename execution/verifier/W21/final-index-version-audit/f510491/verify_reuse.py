"""Compare explicit reusable code subsets and parse existing public raw logs only."""
from pathlib import Path
import fnmatch,hashlib,json,subprocess
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[4]
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
target='f510491'
files=git('ls-tree','-r','--name-only',target).decode().splitlines()
subsets={
 'C03_C04':('9cebc53',['internal/domain/changes.go','internal/domain/conflicts.go','internal/domain/change_impact.go','internal/domain/context_test.go','internal/domain/context_regression_test.go']),
 'A01':('a8de3fc',['internal/domain/import.go','internal/domain/context_test.go','spec/v2.0/PACKAGE_MANIFEST.json','go.mod','go.sum']),
 'C21_A07':('b1877d4',['internal/domain/experiments*.go','adapters/evaluation/*.go','evaluation/development/*','ops/experiment_sandbox/*.go']),
 'C22':('0e4b0c2',['internal/domain/protected*.go','internal/domain/qualification*.go','internal/domain/auth.go','internal/domain/remote_auth.go','adapters/protectedstore/*.go','ops/experiment_sandbox/*.go']),
 'A09':('9e419e7',['internal/domain/skills*.go','internal/domain/changes.go','internal/domain/conflicts.go','adapters/knowledge/*.go','tests/skills/*','evaluation/skills/*']),
 'C09':('76b1bef',['internal/domain/evolution.go','internal/domain/evolution_acceptance.go','internal/domain/evolution_execution.go','internal/domain/evolution_holdout.go','internal/domain/evolution_test.go','ops/supervisor/holdout_windows.go','evaluation/evolution/*.go','ops/experiment_sandbox/*.go']),
}
result={'scope':'EXPLICIT_REUSE_SUBSETS_NOT_COMPLETE_DEPENDENCY_CLOSURE','target':git('rev-parse',target).decode().strip(),'subsets':{},'raw':[]}
for key,(ref,patterns) in subsets.items():
 checks=[]
 for path in files:
  if not any(fnmatch.fnmatch(path,p) for p in patterns):continue
  a=git('show',ref+':'+path);b=git('show',target+':'+path)
  checks.append({'path':path,'old_git_sha256':sha(a),'target_git_sha256':sha(b),'same':a==b})
 result['subsets'][key]={'source':ref,'checks':checks,'all_equal':all(x['same'] for x in checks)}
raws=[
 ('D04','execution/receipts/W04/analyze-api/main-9cebc53/stdout.jsonl','31ac54cc100f8766973279d4d5134d4f2b245b0beaa48fc0bc1cdb394427359c'),
 ('DS2','execution/receipts/W06/runtime-s2/root-integration/consumer-tool-binding/stdout.jsonl',None),
 ('DI2','execution/receipts/W08/research-driver/cycle-binding-native-pair.jsonl','f08c420f18aba5101fab837ae82993890b5d375bea1efcea9567782ef1fa7458'),
 ('DCONTROL','execution/receipts/W16/control-business-proof/76b1bef/control-business-and-legacy.raw.jsonl',None),
]
for key,path,expected in raws:
 raw=(ROOT/path).read_bytes();events=[]
 for line in raw.decode('utf-8-sig').splitlines():
  try:events.append(json.loads(line))
  except ValueError:pass
 result['raw'].append({'id':key,'path':path,'sha256':sha(raw),'expected_sha256':expected,'declared_hash_match':sha(raw)==expected if expected else None,'pass':[x['Test'] for x in events if x.get('Action')=='pass' and 'Test' in x],'fail':[x['Test'] for x in events if x.get('Action')=='fail' and 'Test' in x],'package_actions':[x.get('Action') for x in events if 'Test' not in x and x.get('Action') in ['pass','fail']],'note':'Individual case PASS does not erase any package FAIL; no test was executed by this audit.'})
(OUT/'reuse-subset-binding.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for key,v in result['subsets'].items():print(key,len(v['checks']),v['all_equal'],[x['path'] for x in v['checks'] if not x['same']])
for v in result['raw']:print(v['id'],len(v['pass']),v['fail'],v['declared_hash_match'])
