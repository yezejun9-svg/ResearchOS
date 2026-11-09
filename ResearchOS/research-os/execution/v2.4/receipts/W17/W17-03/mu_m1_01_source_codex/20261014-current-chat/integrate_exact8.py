"""Root integrates only independently reviewed Mu M1-01 source; no live activation."""
import datetime, hashlib, json, subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');A=Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-m1-wire-20261014');O=Path(__file__).parent
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert git('rev-parse','HEAD').decode().strip()=='454492f78fc0536966c8c8343d4bdd2fd99250b7'
assert not git('diff','--cached','--name-only')
assert sha(R/'.git/config')=='1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
review=R/'execution/v2.4/receipts/W17/W17-03/mu_m1_01_independent_review_codex/20261014-current-chat/FINAL-report.json'
assert sha(review)=='9418ec17e353f1dc7667ac30ab9eef17111d3f84a6304f531e1d16892ef2b526' and read(review)['verdict']=='APPROVE_SOURCE_NATIVE_SYNTHETIC_M1_01_ONLY'
manifest=read(O/'manifest.json');names=[x['path'] for x in manifest['source8']]
assert set(git('diff','--name-only','c465d1356480d6e6a90da84656724f9fc02b31c7',manifest['source_commit']).decode().splitlines())==set(names)
protected=read(R/'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']
for m in protected:assert sha(R/m['path'])==m['sha256']
for m in manifest['source8']:
 p=R/m['path'];old=subprocess.run(['git','show','c465d1356480d6e6a90da84656724f9fc02b31c7:'+m['path']],cwd=R,capture_output=True)
 assert p.read_bytes()==old.stdout if old.returncode==0 else not p.exists()
 assert sha(A/m['path'])==m['sha256']
for m in manifest['source8']:
 p=R/m['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((A/m['path']).read_bytes())
git('add','--',*names)
assert set(git('diff','--cached','--name-only').decode().splitlines())==set(names)
for m in manifest['source8']:assert hashlib.sha256(git('show',':'+m['path'])).hexdigest()==m['sha256']
check=subprocess.run(['git','-c','core.whitespace=cr-at-eol','diff','--cached','--check'],cwd=R,capture_output=True)
assert check.returncode==0,check.stdout.decode(errors='replace')
before=git('rev-parse','HEAD').decode().strip();commit=git('commit','-m','feat(runtime): add reviewed Mu pause checkpoint wire and candidate bridge').decode()
after=git('rev-parse','HEAD').decode().strip()
assert set(git('diff','--name-only',before,after).decode().splitlines())==set(names)
for m in protected:assert sha(R/m['path'])==m['sha256']
assert sha(R/'.git/config')=='1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
result={'schema':'researchos.root-reviewed-mu-m1-source-integration/1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'before':before,'after':after,'tree':git('rev-parse','HEAD^{tree}').decode().strip(),'candidate':manifest['source_commit'],'independent_review_sha256':sha(review),'changed_paths':names,'source_hashes':manifest['source8'],'protected_source_preserved':True,'git_identity_preserved':True,'live_package_changed':False,'installed_sdk_changed':False,'Core_M1_02':'OPEN','formal_increment':0}
with (O/'integration.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'commit':after,'tree':result['tree'],'paths':len(names),'receipt_sha256':sha(O/'integration.json')}))
