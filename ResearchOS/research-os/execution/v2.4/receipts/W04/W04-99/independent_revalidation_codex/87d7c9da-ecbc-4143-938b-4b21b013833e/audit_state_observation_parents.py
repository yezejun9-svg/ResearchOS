import json,pathlib,hashlib,re,subprocess
from datetime import datetime,timezone
OUT=pathlib.Path(__file__).resolve().parent;ROOT=OUT.parents[6];BASE=ROOT/'execution/v2.4/receipts/W04/W04-99'
TARGET='64ef113e768e530d721977cf10c736d4c285fd9896ba00727871ff449c422760'
STATE=ROOT/'execution/v2.4/step_state.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def resolve(s):
 p=pathlib.Path(s)
 if not p.is_absolute():p=ROOT/('execution/v2.4/'+s if s.startswith('receipts/') else s)
 return p.resolve()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def save(name,d):
 with (OUT/name).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(OUT/name)
def refs(v,loc=''):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str):yield v['path'],v['sha256'],loc
  for k,x in v.items():
   if isinstance(x,str) and re.fullmatch('[0-9a-f]{64}',x) and ('/' in k or '\\' in k):yield k,x,loc+'/'+k
   yield from refs(x,loc+'/'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):yield from refs(x,loc+'/'+str(i))
row=next(x for x in json.loads(STATE.read_bytes())['steps'] if x['id']=='W04-99')
queue=[(resolve(x['path']),x['sha256'],{'canonical_evidence':x}) for x in row['evidence']]
visited=set();parents=[];files=[];changed=[]
while queue:
 p,h,origin=queue.pop(0)
 if (str(p),h) in visited:continue
 visited.add((str(p),h))
 if not p.is_relative_to(BASE) or p.suffix!='.json':continue
 if not p.is_file():changed.append({'path':str(p),'expected':h,'reason':'missing'});continue
 raw=p.read_bytes()
 if sha(raw)!=h:changed.append({'path':str(p),'expected':h,'actual':sha(raw)});continue
 try:d=json.loads(raw)
 except (ValueError,UnicodeError):continue
 files.append({'ref':ref(p),'bound_via':origin})
 for s,hh,loc in refs(d):
  child=resolve(s)
  if child==STATE and hh==TARGET:parents.append({'parent_ref':ref(p),'field_locator':loc,'original_path':s,'expected_sha256':hh,'bound_via':origin})
  if child.is_relative_to(BASE) and child.suffix=='.json':queue.append((child,hh,{'parent_ref':ref(p),'field_locator':loc}))
assert len(parents)==2,parents
copy=BASE/'integration_codex/step_state_before_acceptance.json';assert sha(copy.read_bytes())==TARGET
blob=subprocess.run(['git','-C',str(ROOT),'show','f68c83c2918ae25d9811e4e9f703f1a158e143d2:'+copy.relative_to(ROOT).as_posix()],capture_output=True,check=True).stdout
assert sha(blob)==TARGET
audit=save('state_observation_parent_audit.json',{'schema':'researchos.w04.exact-historical-state-parent-audit.v1','at':datetime.now(timezone.utc).isoformat(),'root_evidence':row['evidence'],'scope':'Recognized hash-bound JSON refs/maps reachable from current old canonical evidence, restricted to W04 receipt subtree; only current exact-hash immutable bytes traversed. Changed source assets listed, never silently accepted.','parents':parents,'visited_exact_json':files,'changed_or_missing_not_traversed':changed,'actual_copy_ref':ref(copy),'old_git_commit':'f68c83c2918ae25d9811e4e9f703f1a158e143d2','old_git_blob_sha256':sha(blob),'canonical_changes':0})
review=save('historical_state_second_parent_amendment.json',{'schema':'researchos.w04.exact-historical-state-parent-scope-amendment.v1','reviewer_id':'codex:/root/w05_merge_review','decision':'EXACT_PURPOSE_SCOPE_READY','prior_clarification_ref':ref(OUT/'historical_purpose_scope_clarification.json'),'audit_ref':audit,'exact_allowed_observation_parents':parents,'allowed_source_copy_ref':ref(copy),'purpose':'Both exact immutable historical audit parents recorded the same mutable canonical state observation. Verify the actual originalPath/SHA against the already existing oldRoot before-acceptance bytes and Git provenance as transparent additional corroboration. The old reviews did not bind this copy path; do not claim an original snapshot-map authorization.','guard':'Whitelist the complete parent path+parent SHA+field locator+original state path+observed SHA tuple for exactly these2 parents. Changed parent bytes, another field/path/hash or unbound copy refuse. This is not a generic STATE exemption, JSON fallback or source substitution. Mandatory receipt refs remain exact at original paths; current state and own-write transition CAS remain independently strict.','completeness':'Exactly2 matching parents found in the recognized reachable immutable W04 JSON graph. This is not permission for changed or unbound historical JSON. No other parent admitted by this amendment.','scope_change':'One additional exact parent: round2 review_detail.json f03f6c2fc182e672a64b66c4f86bb61be91b4569a982ae6b6f8bb63f003d4af5, alongside earlier audit_result.json b2ffa00c4f842ba2b1e9f45da5570f86b01970f95a719ebf552b03129baf6e27. No new copy, source path, migration or old receipt edit.','formal_acceptance_delta':0,'source_canonical_changes':0})
print(json.dumps({'review':review,'audit':audit,'parents':len(parents),'exact_jsons':len(files),'untraversed_changed':len(changed)}))
