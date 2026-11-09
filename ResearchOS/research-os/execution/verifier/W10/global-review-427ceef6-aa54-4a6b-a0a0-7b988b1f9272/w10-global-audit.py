from pathlib import Path
import json,hashlib,subprocess,base64,datetime
R=Path.cwd();D=R/'execution/receipts/W10/427ceef6-aa54-4a6b-a0a0-7b988b1f9272';O=R/'.local/w10-global-audit';O.mkdir(exist_ok=True)
load=lambda p:json.loads(p.read_text(encoding='utf8'));sha=lambda b:hashlib.sha256(b).hexdigest();hashfile=lambda p:sha(p.read_bytes());jcs=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
receipt=load(D/'receipt.json');env=load(D/'environment-before.json');manifest=load(D/'artifacts.json');audit=[]
def check(id,ok,details=None):
 audit.append({'id':id,'pass':bool(ok),'details':details});
 if not ok:print('FAIL',id,str(details)[:300])
check('receipt_jcs',sha(jcs({k:v for k,v in receipt.items() if k!='receipt_hash'}))==receipt['receipt_hash'].removeprefix('sha256:'),receipt['receipt_hash'])
check('manifest_bound',hashfile(D/'artifacts.json')==receipt['artifact_manifest_hash'].removeprefix('sha256:'))
for a in manifest['files']:check('artifact:'+a['path'],hashfile(R/a['path'])==a['sha256'].removeprefix('sha256:'))
CODE=receipt['code_revision'];FROZEN='7c5d7ce'
for p,h in env['source_sha256'].items():
 b=subprocess.check_output(['git','show',CODE+':'+p],cwd=R);c=subprocess.check_output(['git','show',FROZEN+':'+p],cwd=R);check('source:'+p,sha(b)==h and b==c)
check('preflight_before_execution',datetime.datetime.fromisoformat(env['sampled_at'])<datetime.datetime.fromisoformat(receipt['started_at']))
check('tracked_source_clean',env['tracked_status_porcelain']=='' and env['tracked_source_clean'])
invocations={}
for name in ['A07','C21']:
 case=load(D/(name+'.json'));spec=next(c for c in load(R/'spec/v2.0/contracts/acceptance.json')['cases'] if c['id']==name)
 check(name+':global_sections',all(k in case for k in ['run_receipt','version_manifest','command_receipt','assertion_results','acceptance_receipt']))
 check(name+':assertion_inventory',[a['id'] for a in spec['assertions']]==[a['assertion_id'] for a in case['assertion_results']])
 check(name+':expected_frozen',all(a['expected']==b['expected'] for a,b in zip(spec['assertions'],case['assertion_results'])))
 for field in ['lock_files','input_snapshots','policy_versions']:
  for entry in case['version_manifest'][field]:check(name+':'+field+':'+entry['path'],hashfile(R/entry['path'])==entry['sha256'])
 for c in case['command_receipt']:
  ref=c['reference'];inv=load(R/ref);invocations[ref]=inv;check(name+':cmd:'+ref,hashfile(R/ref)==c['sha256'] and all(inv[k]==c[k] for k in ['argv','cwd','exit_code','environment_names','code_revision','registered_command_revision','command_key']))
  for stream in ['stdout','stderr']:check(name+':stream:'+ref+':'+stream,hashfile(R/inv[stream]['path'])==inv[stream]['sha256'])
 for row in case['assertion_results']:
  check(name+':assertion:'+row['assertion_id'],row['status']=='PASS' and len(row['actual'])>0 and len(row['raw_evidence'])>0)
  for entry in row['raw_evidence']:check(name+':rawref:'+entry['path'],hashfile(R/entry['path'])==entry['sha256'])
for vr in receipt['verification_results']:invocations[vr['actual_invocation_reference']]=load(R/vr['actual_invocation_reference'])
reports={}
for ref,inv in invocations.items():
 check('inv:'+ref,inv['status']=='PASS' and inv['exit_code']==0 and inv['code_revision']==CODE)
 lines=(R/inv['stdout']['path']).read_text(encoding='utf8').splitlines();p=None
 for line in lines:
  try:o=json.loads(line)
  except ValueError:continue
  if 'receipt' in o:p=Path(o['receipt'])
 if p and p.is_file():
  report=load(p);reports[ref]=(p,report)
  check('report_ids:'+ref,report['assertion_ids']==inv['assertion_ids'])
  check('report_pass:'+ref,report['status']=='PASS' and report['exit_code']==0)
  raw=(p.parent/'stdout.txt').read_text(encoding='utf8').splitlines()
  for row in report.get('assertions',[]):
   if row.get('raw',{}).get('line'):
    line=raw[row['raw']['line']-1];prefix=line.find('{');actual=json.loads(line[prefix:]);check('raw_assertion:'+ref+':'+row['assertion_id'],all(actual[k]==row[k] for k in ['assertion_id','expected','actual','status']) and actual['status']=='PASS')
  for f,h in report.get('hashes',{}).items():check('report_hash:'+ref+':'+f,hashfile(p.parent/f)==h.removeprefix('sha256:'))
for name in ['A07','C21']:
 case=load(D/(name+'.json'))
 for row in case['supplemental_assertions']:
  report=reports[row['invocation_reference']][1];matches=[a for a in report['assertions'] if a['assertion_id']==row['assertion_id']];check('envelope_raw:'+name+':'+row['assertion_id'],len(matches)==1 and all(row[k]==matches[0][k] for k in ['actual','expected','status']))
summary={'code_revision':CODE,'frozen_candidate':FROZEN,'artifact_count':len(manifest['files']),'source_count':len(env['source_sha256']),'invocations':[{'ref':ref,'selector':i.get('selectors'),'count':len(i['assertion_ids'])} for ref,i in invocations.items()],'audit_count':len(audit),'pass':sum(a['pass'] for a in audit),'fail':sum(not a['pass'] for a in audit),'audit':audit,'report_paths':[str(p.relative_to(R)) for p,_ in reports.values()]}
(O/'audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in summary.items() if k!='audit'},ensure_ascii=True))
