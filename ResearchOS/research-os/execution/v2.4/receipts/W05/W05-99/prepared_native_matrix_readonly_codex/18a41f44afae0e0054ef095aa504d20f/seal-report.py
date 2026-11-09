import pathlib,sys,json,hashlib,datetime
sys.dont_write_bytecode=True
q=pathlib.Path(__file__).resolve().parent
payload=json.loads((q/'seal-input.json').read_bytes())
b=pathlib.Path(payload['B'])
def ref(p):
 raw=p.read_bytes()
 return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,value):
 p=q/name
 raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
 with p.open('xb') as f:f.write(raw)
 return ref(p)
source_refs=[];manifest_checks=[];rejections=[]
roots=[pathlib.Path(payload['N']).parent,pathlib.Path(payload['M']).parent,b/'prepared_abandonment_schema_upgrade_source_codex'/'e841e7fcddaa45ecb115f84df9827af2']
for root in roots:
 mf=root/'MF.json';doc=json.loads(mf.read_bytes());drift=[]
 for relative,declared in doc['source_refs'].items():
  p=pathlib.Path(declared['path']);actual=ref(p)
  if actual['sha256']!=declared['sha256'] or actual['bytes']!=declared['bytes']:drift.append({'declared':declared,'actual':actual})
  source_refs.append({'relative':relative,'source_manifest':str(mf),**actual})
  if p.suffix=='.go' and not p.name.endswith('_test.go'):
   lines=p.read_text(encoding='utf-8').splitlines()
   for i,line in enumerate(lines,1):
    if ('return' in line or 'log.Fatal' in line) and any(s in line for s in ['errors.New(','fmt.Errorf(','Fail(','log.Fatal(']):
     rejections.append({'path':str(p),'line':i,'code':line.strip(),'preceding_context':lines[max(0,i-3):i-1]})
 manifest_checks.append({'manifest_ref':ref(mf),'source_count':len(doc['source_refs']),'drift':drift})
w=pathlib.Path(payload['W'])
for relative in ['adapters/runtime/data_root_windows.go','adapters/runtime/bridge_windows.go','internal/domain/prepared_run_abandonment_windows_test.go','internal/domain/backup_upgrade.go','internal/domain/backup_queue_upgrade.go','ops/backup/main.go']:
 source_refs.append({'relative':relative,'scope':'ACTUAL_COMPOSITION_BASELINE_READONLY',**ref(w/relative)})
a=b/'integration_codex'/'native-authority-enrolled-v2-component-root-b0647419338d47ad'
actual_refs=[ref(a/name) for name in ['native-leaf-test.invocation.json','native-leaf-test.stdout.raw','validation.closed.json']]
events=[]
for line in (a/'native-leaf-test.stdout.raw').read_text(encoding='utf-8').splitlines():
 try:event=json.loads(line)
 except json.JSONDecodeError:continue
 if event.get('Action') in ['pass','fail','skip'] and 'Test' in event:events.append({key:event[key] for key in ['Time','Action','Package','Test','Elapsed'] if key in event})
leaf=json.loads((a/'native-leaf-test.invocation.json').read_bytes())
members={name:ref(q/name) for name in ['report.md','original-tool-io.json','failure-origin.791.json','seal-input.json','seal-report.py']}
report={'schema':payload['schema'],'status':payload['status'],'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'namespace':str(q),'source_manifest_checks':manifest_checks,'source_refs':source_refs,'source_explicit_rejection_catalog':rejections,'forwarded_OS_IO_SQL_contract_errors':'In addition to explicit catalogue, each observed Windows/file/context/SQLite/auth/contracts operation can return its actual error. No native or SQL execution was performed here.','actual_refs':actual_refs,'actual_leaf_summary':{'actual_native_exit':leaf['actual_native_exit'],'result':leaf['result'],'test_actions':events,'positive_real_inherited_pipe_constructor_covered':False,'production_SQLite_token_positive_covered':False},'limitations':['No private_resource_ref target, DPAPI credential or ExecuteClaim was read','No Go/native/Git/SQL/provider was run','No production or formal acceptance verdict','No existing journal/failed counter reset or canonical/Source mutations'],'new_mechanical_failures':[791],'production_db_writes':0,'native_executions':0,'provider_requests':0,'report_ref':members['report.md'],'tool_io_ref':members['original-tool-io.json'],'failure_origin_ref':members['failure-origin.791.json']}
members['report.json']=write('report.json',report)
sealref=write('manifest.json',{'schema':'researchos.readonly-immutable-receipt-manifest.v1','status':payload['status'],'members':members,'source_checks_drift_count':sum(len(x['drift']) for x in manifest_checks),'new_mechanical_failures':[791],'Main_adopted':False,'formal_acceptance':False})
print(json.dumps({'namespace':str(q),'refs':{**members,'manifest.json':sealref},'source_manifest_checks':[{'source_count':x['source_count'],'drift_count':len(x['drift'])} for x in manifest_checks],'leaf_top_level_pass':sum(1 for e in events if e['Action']=='pass' and '/' not in e['Test']),'leaf_subtest_pass':sum(1 for e in events if e['Action']=='pass' and '/' in e['Test']),'explicit_rejection_entries':len(rejections)},ensure_ascii=False))
