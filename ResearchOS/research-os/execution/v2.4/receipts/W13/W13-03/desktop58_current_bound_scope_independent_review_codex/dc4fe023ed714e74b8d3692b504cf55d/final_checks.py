from pathlib import Path
import json,hashlib
O=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os');N=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r336-'+O.name)
C=[];refs={}
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=path(p);b=p.read_bytes();refs[str(p)]={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def obj(p):return json.loads(read(p))
def ck(n,x,d=None):C.append({'check':n,'passed':bool(x),'detail':d})
def pin(r):
 z=read(r['path']);ck('pin '+r['path'],len(z)==r['bytes'] and hashlib.sha256(z).hexdigest()==r['sha256']);return z
s=obj(N/'scope_registration.json');b=obj(N/'binding.pre-review.json');auth=obj(s['current_source_authority_ref']['path']);src=obj(auth['source_commit_closure_ref']['path']);manifest=obj(src['manifest_ref']['path'])
allrefs=[]
def collect(v):
 if isinstance(v,dict):
  if set(v)=={'path','sha256','bytes'}:allrefs.append(v)
  else:
   for x in v.values():collect(x)
 elif isinstance(v,list):
  for x in v:collect(x)
collect(manifest);collect(src)
facts=[]
for r in allrefs:
 p=path(r['path']);name=p.name.lower()
 if ('status' in name or 'index' in name) and name.endswith(('.stdout.raw','.stdout.bin','.stdout')):
  raw=pin(r);facts.append({'ref':r,'bytes':len(raw),'rows':raw.count(b'\0') if b'\0' in raw else len(raw.splitlines()),'raw_utf8':raw.decode('utf-8','strict')})
status=[x for x in facts if x['ref']['sha256']==s['main_git']['status_sha256']]
ck('sealed source status raw matches scope894',bool(status) and all(x['bytes']==894 for x in status))
if status:
 z=status[0]['raw_utf8'];rows=[x for x in (z.split('\0') if '\0' in z else z.splitlines()) if x]
 ck('frozen13rows11D',len(rows)==13 and sum(x[:2]==' D' for x in rows)==11,rows)
indices=[x for x in facts if path(x['ref']['path']).name=='index-after.stdout.raw']
ck('source closure sealed empty-index raw exists',len(indices)==1 and indices[0]['bytes']==0 and indices[0]['ref']['sha256']==hashlib.sha256(b'').hexdigest(),[x['ref'] for x in indices])
can=obj(b['canonical_before_ref']['path'])['entries']
for x in can:ck('final live four equal copied '+x['canonical_path'],read(x['canonical_path'])==pin(x['ref']))
for k in ('output_root','outer_output_root','export_root','new_authorization_root','new_grant_preflight_root'):ck('stillabsent '+k,not path(s[k]).exists())
head=read(R/'.git/HEAD').decode().strip();head=read(R/'.git'/head[5:]).decode().strip() if head.startswith('ref: ') else head;ck('direct Main E2',head==s['source_commit'])
data={'schema':'researchos.desktop58-bound-final-guards.v1','checks':C,'failed':[x for x in C if not x['passed']],'frozen_git_raw_facts':facts,'input_refs':list(refs.values()),'no_new_git_invocation':True,'status_index_reused_source_closure_not_fresh_native_measurement':True}
with (O/'final-checks.json').open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'checks':len(C),'failed':data['failed'],'rawfacts':[{'path':x['ref']['path'],'bytes':x['bytes']} for x in facts]},ensure_ascii=False))
