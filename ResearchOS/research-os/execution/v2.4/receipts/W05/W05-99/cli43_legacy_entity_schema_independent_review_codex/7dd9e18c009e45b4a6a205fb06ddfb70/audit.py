from pathlib import Path
import json,hashlib,traceback
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';O=Path(__file__).parent;N=P/'cli43_legacy_entity_schema_preparation_codex/26c182c39c734501ac4f85cf6c978a86'
checks=[];refs={}
def path(x):
 p=Path(x);return p if p.is_absolute() else R/p
def ref(x):
 p=path(x);raw=p.read_bytes();r={'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)};refs[r['path']]=r;return r
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
def verify(x):
 p=path(x['path']);r=ref(p);ck('pin '+str(p),r['sha256']==x['sha256'] and r['bytes']==x['bytes']);return p
def read(x):ref(x);return json.loads(path(x).read_bytes())
def save(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
try:
 ck('given MF',ref(N/'manifest.json')['sha256']=='44c6ba1557dcaa76de874a710150233d251bb7b38d7062d99dfe95164743df40')
 mf=read(N/'manifest.json');ck('nine unique members self excluded',len(mf['members'])==len({x['path'] for x in mf['members']})==9 and mf['self_excluded'] is True)
 for x in mf['members']:verify(x)
 h=read(N/'handoff.json')
 for k,v in h.items():
  if k.endswith('_ref') and isinstance(v,dict):verify(v)
 before=read(N/'inputs.before.json');after=read(N/'inputs.after.json');ck('input before after identical',before==after)
 for x in before:verify(x)
 old=verify(h['old_helper_ref']).read_bytes();new=verify(h['helper_ref']).read_bytes();edits=read(N/'helper.exact-edits.json');inv=new
 ck('exact two edits',len(edits)==2)
 for e in edits:
  ck('unique new literal '+e['new'],inv.count(e['new'].encode())==1);inv=inv.replace(e['new'].encode(),e['old'].encode(),1)
 ck('entire helper inverse',inv==old)
 op=verify(h['old_plan_ref']).read_bytes();np=verify(h['instrumentation_plan_ref']).read_bytes();od=json.loads(op);nd=json.loads(np)
 ck('only additional_file_ref',od.keys()==nd.keys() and {k for k in od if od[k]!=nd[k]}=={'additional_file_ref'} and nd['additional_file_ref']==h['helper_ref'])
 pinv=np
 for k in ['path','sha256']:
  pinv=pinv.replace(json.dumps(nd['additional_file_ref'][k],ensure_ascii=False)[1:-1].encode(),json.dumps(od['additional_file_ref'][k],ensure_ascii=False)[1:-1].encode())
 pinv=pinv.replace(('"bytes": '+str(nd['additional_file_ref']['bytes'])).encode(),('"bytes": '+str(od['additional_file_ref']['bytes'])).encode())
 ck('plan entire byte inverse',pinv==op)
 ck('unchanged test refs',h['instrumented_source_ref']==h['unchanged_instrumented_test_ref'] and h['instrumented_source_ref']['sha256']=='6dbcdcc0fc12b2bd00a69f724cbe1f9598761fe467157273c6709344b1a1f29e')
 schema=read(verify(h['actual_fixture_contract_schema_ref']));legacy=verify(h['actual_fixture_contract_schema_ref']);export=verify(h['prior_export_same_legacy_schema_ref']);ck('Main schema and frozen export byte equal',legacy.read_bytes()==export.read_bytes())
 catalog=read(verify(h['original_source_catalog_ref']));rows=[x for x in catalog['files'] if path(x['path'])==legacy]
 ck('exact schema already in597 catalog',len(catalog['files'])==597 and len(rows)==1 and rows[0]['sha256']==h['actual_fixture_contract_schema_ref']['sha256'] and rows[0]['bytes']==195457)
 ck('Goal binding legacy routes',schema['$defs']['Goal']['properties']['binding']=={'$ref':'#/$defs/ProjectBinding'} and schema['$defs']['ProjectBinding']['properties']['route']['enum']==['PAPERCLIP','THIN_CORE'])
 ck('full Goal Task present',all(isinstance(schema['$defs'][k],dict) and schema['$defs'][k].get('type')=='object' for k in ['Goal','Task']))
 localrefs=[]
 def walk(v):
  if isinstance(v,dict):
   if '$ref' in v:localrefs.append(v['$ref'])
   for z in v.values():walk(z)
  elif isinstance(v,list):
   for z in v:walk(z)
 walk(schema)
 for target in localrefs:
  found=target.startswith('#/')
  v=schema
  if found:
   for part in target[2:].split('/'):
    part=part.replace('~1','/').replace('~0','~')
    if not isinstance(v,dict) or part not in v:found=False;break
    v=v[part]
  ck('internal schema reference resolves '+target,found)
 test=R/'apps/cli/cli_sessions_test.go';store=R/'internal/domain/store.go';contracts=R/'internal/domain/contracts.go'
 for x in [test,store,contracts]:ref(x)
 ck('fixture passes actual legacy contract directory','domain.New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")' in test.read_text(encoding='utf-8'))
 ck('service reads passed directory','c, e := LoadContracts(contractsDir)' in store.read_text(encoding='utf-8') and 'os.ReadFile(filepath.Join(dir, "domain.schema.json"))' in contracts.read_text(encoding='utf-8'))
 text=new.decode('utf-8');ck('correct fixed path and hash',edits[0]['new'] in text and h['actual_fixture_contract_schema_ref']['sha256'] in text)
 ck('strict local compiler and Goal Task retained',all(v in text for v in ['compiler.UseLoader(cli43LocalSchemaOnly{})','compiler.AssertFormat()','compiler.DefaultDraft(jsonschema.Draft2020)','[]string{"Goal","Task"}','api.ClientProtocolDocument()','b=bytes.Clone(b);']))
 closure=P/'cli43_failed_execution_independent_review_codex/b33d80b428a247539130e8585e85f3c7';reuse=[ref(closure/n) for n in ['review.json','manifest.json','cause.json']]
 reuse.append(ref(P/'cli43_transport_binding_independent_review_codex/db438ad9e85f4cdc925a222cc31c3f01/review.json'))
 for x in list(refs.values()):
  now=path(x['path']).read_bytes();ck('after unchanged '+x['path'],hashlib.sha256(now).hexdigest()==x['sha256'] and len(now)==x['bytes'])
 save('audit.json',{'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'input_refs':list(refs.values()),'helper_ref':h['helper_ref'],'plan_ref':h['instrumentation_plan_ref'],'test_ref':h['instrumented_source_ref'],'legacy_schema_ref':h['actual_fixture_contract_schema_ref'],'schema_local_ref_count':len(localrefs),'reused_refs':reuse,'target_executions':0,'new_failure_origins':[]})
 print(json.dumps({'check_count':len(checks),'failed_checks':[x for x in checks if not x['passed']],'audit_ref':ref(O/'audit.json')},ensure_ascii=False))
except BaseException as e:
 save('audit.failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'checks':checks,'input_refs':list(refs.values())});raise
