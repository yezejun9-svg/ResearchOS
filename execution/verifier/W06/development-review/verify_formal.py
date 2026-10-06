from pathlib import Path
import json,hashlib,subprocess,datetime
root=Path(__file__).resolve().parents[4];out=Path(__file__).parent;rev='98468b525d7b88e49d23d434a1d39fcdd403b725'
ids=['49f45299-9e52-4f20-a73f-0d26deaa4bc5','149a7e80-6578-484c-a3eb-dbd14b209f37','37b2fa2e-f42b-40d3-8fae-3fc939c51f68','fd2d52e1-6643-440a-a882-03823e62280f']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();checks=[];errors=[];cache={}
def committed_hash(p):
 p=p.replace('\\','/')
 if p not in cache:cache[p]=hashlib.sha256(subprocess.check_output(['git','show',rev+':'+p],cwd=root)).hexdigest()
 return cache[p]
prepath=root/'execution/receipts/W06/524048b0-de1b-402b-9da3-ba71d7c5cfe6/environment-before.json';pre=json.loads(prepath.read_text(encoding='utf-8'))
for p,h in pre['source_sha256'].items():
 got=committed_hash(p)
 if got!=h:errors.append({'kind':'preflight-source','path':p,'expected':h,'actual':got})
for iid in ids:
 ip=root/'execution/invocations'/iid/'receipt.json';inv=json.loads(ip.read_text(encoding='utf-8'))
 for k in ['stdout','stderr']:
  if sha(root/inv[k]['path'])!=inv[k]['sha256']:errors.append({'kind':'outer-hash','invocation':iid,'path':inv[k]['path']})
 outer=json.loads((root/inv['stdout']['path']).read_text(encoding='utf-8').splitlines()[-1]);rp=Path(outer['receipt']);rep=json.loads(rp.read_text(encoding='utf-8'));before=json.loads((rp.parent/'before.json').read_text(encoding='utf-8'))
 for p,h in rep['hashes'].items():
  if sha(rp.parent/p)!=h.removeprefix('sha256:'):errors.append({'kind':'inner-hash','invocation':iid,'path':p})
 for p,h in before['versions'].items():
  got=committed_hash(p)
  if got!=h.removeprefix('sha256:'):errors.append({'kind':'before-source','invocation':iid,'path':p,'expected':h,'actual':got})
 rows=[json.loads(l.removeprefix('W06_ASSERTION ')) for l in (rp.parent/'stdout.txt').read_text(encoding='utf-8').splitlines() if l.startswith('W06_ASSERTION ')]
 got=[r['assertion_id'] for r in rows];expected=rep['expected_assertion_ids']
 ok=inv['status']==rep['status']=='PASS' and inv['exit_code']==rep['exit']==0 and len(got)==len(set(got)) and sorted(got)==sorted(expected)==sorted(inv['assertion_ids']) and all(x['status']=='PASS' for x in rows) and before['head']==rev
 if not ok:errors.append({'kind':'assertion-binding','invocation':iid})
 checks.append({'invocation_id':iid,'command_key':inv['command_key'],'selector':inv['selectors'],'invocation_receipt':str(ip.relative_to(root)).replace('\\','/'),'invocation_receipt_sha256':sha(ip),'inner_receipt':str(rp.relative_to(root)).replace('\\','/'),'inner_receipt_sha256':sha(rp),'assertions':len(got),'source_versions_verified':len(before['versions']),'exact_raw_assertions_passed':ok})
report={'revision':rev,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'preflight':str(prepath.relative_to(root)).replace('\\','/'),'preflight_sha256':sha(prepath),'preflight_sources_verified':len(pre['source_sha256']),'checks':checks,'errors':errors,'status':'PASS' if not errors else 'FAIL'}
(out/'formal-bindings.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if not errors else 1)
