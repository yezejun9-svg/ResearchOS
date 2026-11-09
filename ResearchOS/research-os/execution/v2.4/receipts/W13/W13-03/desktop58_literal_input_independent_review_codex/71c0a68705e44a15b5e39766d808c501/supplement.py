from pathlib import Path
import json, hashlib, os
R=Path('D:/作品集/ResearchOS/research-os'); O=Path(__file__).parent
N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-1c4ea6999d4d4437a0202c4e81ce581b'
def p(s):
 x=Path(s); return x if x.is_absolute() else R/x
def read(x): return json.loads(p(x).read_bytes())
def ref(x):
 x=p(x); b=x.read_bytes(); return {'path':str(x),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(name,x):
 with (O/name).open('xb') as f: f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
q=read(N/'root-construction.parameters.desktop58.json'); t=read(q['scope_template_ref']['path']); a=read(t['alias_roster_ref']['path']); checks=[]
def ck(name,ok): checks.append({'check':name,'passed':bool(ok)})
ck('exact twenty roster and declarations',len(a['rows'])==len(q['negative_alias_declarations'])==20)
for original,declared in zip(a['rows'],q['negative_alias_declarations']):
 n=original['allocation_ordinal']; want=p(q['allocation']['new_export_root'])/'.local/desktop-wire-negative'/(q['allocation']['run_uuid']+'-'+str(n).zfill(2))/'resources/client-wire/researchos-client-wire-validator.exe'
 ck('frozen alias exact binding '+str(n),declared['case_name']==original['name'] and declared['mode']==original['mode'] and declared['allocation_ordinal']==n and declared['max_creates']==original['expected_image_creates'] and p(declared['path'])==want)
for name,r in zip(['checkpoint','path_ownership','step_state','commands'],q['canonical_copies']):
 ck('current canonical still same '+name,(R/('execution/v2.4/'+name+'.json')).read_bytes()==p(r['path']).read_bytes())
for k in ['new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root']:
 ck('future leaf still absent '+k,not os.path.lexists(p(q['allocation'][k])))
old=read(O/'audit.json'); ck('only original static false predicate',old['failed_checks']==[{'check':'exact nonce alias 14','passed':False}])
save('supplement.json',{'schema':'researchos.readonly-review-supplement.v1','checks':checks,'failed_checks':[x for x in checks if not x['passed']],'original_audit_ref':ref(O/'audit.json'),'request_ref':ref(N/'root-construction.parameters.desktop58.json'),'alias_roster_ref':t['alias_roster_ref'],'correction':'Original audit imposed max_creates in [0,1]. Frozen ordinal 14 unreaped-blocks requires 2; compare exact original expected_image_creates instead. Original audit/source retained. Tool exit0, no failure origin.','native_product_calls':0,'new_failure_origins':[]})
print(json.dumps({'checks':len(checks),'failed':[x for x in checks if not x['passed']],'supplement_ref':ref(O/'supplement.json')},ensure_ascii=False))
