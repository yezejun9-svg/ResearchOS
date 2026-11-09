from pathlib import Path
import json,hashlib,subprocess,datetime
R=Path.cwd();RUN='7b5cedc3-b5c2-42c5-9fe6-f248b29e6f5b';D=R/'execution/receipts/W08'/RUN;O=R/'execution/verifier/W08'/('global-review-'+RUN)
load=lambda p:json.loads(p.read_text(encoding='utf8'));sha=lambda b:hashlib.sha256(b).hexdigest();hf=lambda p:sha(p.read_bytes());jcs=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();checks=[]
def ck(k,ok,details=None):
 checks.append({'id':k,'pass':bool(ok),'details':details})
 if not ok:print('FAIL',k,str(details)[:200])
r=load(D/'receipt.json');env=load(D/'environment-before.json');manifest=load(D/'artifacts.json');CODE=r['code_revision'];FROZEN='42419d0'
ck('receipt_jcs',sha(jcs({k:v for k,v in r.items() if k!='receipt_hash'}))==r['receipt_hash'].removeprefix('sha256:'));ck('manifest_binding',hf(D/'artifacts.json')==r['artifact_manifest_hash'].removeprefix('sha256:'))
for a in manifest['files']:ck('artifact:'+a['path'],hf(R/a['path'])==a['sha256'].removeprefix('sha256:'))
for p,h in env['source_sha256'].items():
 b=subprocess.check_output(['git','show',CODE+':'+p],cwd=R);f=subprocess.check_output(['git','show',FROZEN+':'+p],cwd=R);ck('source:'+p,sha(b)==h and b==f)
ck('preflight_clean',env['tracked_status_porcelain']=='' and env['tracked_source_clean']);ck('preflight_order',datetime.datetime.fromisoformat(env['sampled_at'])<datetime.datetime.fromisoformat(r['started_at']));ck('spec_manifest',hf(R/'spec/v2.0/PACKAGE_MANIFEST.json')==env['spec_manifest_sha256'])
contracts=load(R/'spec/v2.0/contracts/acceptance.json');invocations={};cases=['C05','C06']
for c in cases:
 e=load(D/(c+'.json'));spec=next(x for x in contracts['cases'] if x['id']==c)
 ck(c+':global_fields',all(k in e for k in ['run_receipt','version_manifest','command_receipt','assertion_results','acceptance_receipt']));ck(c+':all_assertions',[x['id'] for x in spec['assertions']]==[x['assertion_id'] for x in e['assertion_results']]);ck(c+':frozen_expected',all(x['expected']==y['expected'] for x,y in zip(spec['assertions'],e['assertion_results'])));ck(c+':all_command_keys',set(spec['command_keys'])=={x['command_key'] for x in e['command_receipt']})
 for section in ['lock_files','input_snapshots','policy_versions']:
  for a in e['version_manifest'][section]:ck(c+':'+section+':'+a['path'],hf(R/a['path'])==a['sha256'])
 for a in e['command_receipt']:
  i=load(R/a['reference']);invocations[a['reference']]=i;ck(c+':command:'+a['reference'],hf(R/a['reference'])==a['sha256'] and all(a[k]==i[k] for k in ['argv','cwd','environment_names','exit_code','registered_command_revision','code_revision','command_key']))
 for a in e['assertion_results']:
  ck(c+':assertion:'+a['assertion_id'],a['status']=='PASS' and len(a['actual'])>0 and len(a['raw_evidence'])>0)
  for f in a['raw_evidence']:ck(c+':rawref:'+f['path'],hf(R/f['path'])==f['sha256'])
for v in r['verification_results']:invocations[v['actual_invocation_reference']]=load(R/v['actual_invocation_reference'])
reports={}
for ref,i in invocations.items():
 for stream in ['stdout','stderr']:ck(ref+':'+stream,hf(R/i[stream]['path'])==i[stream]['sha256'])
 ck(ref+':status',i['code_revision']==CODE and i['status']=='PASS' and i['exit_code']==0)
 obj=load(R/i['stdout']['path']);ck(ref+':stdout_inventory',obj['status']=='PASS' and obj['assertion_ids']==i['assertion_ids'])
 if 'report_reference' not in obj:continue
 p=R/obj['report_reference'];report=load(p);reports[ref]=(p,report)
 ck(ref+':report_inventory',report['assertion_ids']==i['assertion_ids'] and set(report['assertion_ids'])==set(report['expected_assertion_ids']));ck(ref+':report_status',report['head']==CODE and report['status']=='PASS' and report['exit_code']==0 and not report['failures'] and not report['timed_out'])
 for section in ['raw','sqlite_snapshots']:
  for f,h in report[section].items():ck(ref+':report_hash:'+f,hf(p.parent/f)==h.removeprefix('sha256:'))
 for f,h in report['source_hashes'].items():ck(ref+':report_source:'+f,sha(subprocess.check_output(['git','show',CODE+':'+f],cwd=R))==h.removeprefix('sha256:'))
 raw=[]
 for line in (p.parent/'go-test.jsonl').read_text(encoding='utf8').splitlines():
  ob=json.loads(line);output=ob.get('Output','')
  if output.startswith('W08_ASSERTION '):raw.append(json.loads(output[len('W08_ASSERTION '):]))
 ck(ref+':raw_assertion_inventory',sorted(x['assertion_id'] for x in raw)==report['assertion_ids'])
 for a in report['assertions']:
  matches=[x for x in raw if x['assertion_id']==a['assertion_id']];ck(ref+':raw:'+a['assertion_id'],len(matches)==1 and matches[0]==a and a['status']=='PASS')
for c in cases:
 e=load(D/(c+'.json'))
 for a in e['supplemental_assertions']:
  report=reports[a['invocation_reference']][1];matches=[x for x in report['assertions'] if x['assertion_id']==a['assertion_id']];ck(c+':envelope_assertion:'+a['assertion_id'],len(matches)==1 and all(a[k]==matches[0][k] for k in ['actual','expected','status','evidence']))
# Build owns complete raw go-test output; audit C19 independently for G02 same-origin boundary.
build=next(i for i in invocations.values() if i['command_key']=='build.check');buildraw=load(R/build['stdout']['path']);go=next(c for c in buildraw['commands'] if c['name']=='go-test');events=[json.loads(x) for x in go['stdout'].splitlines() if x.strip()];ck('build:full_go_pass',go['exit_code']==0 and not any(x.get('Action')=='fail' for x in events));c19=[]
for x in events:
 if x.get('Output','').startswith('W09_ASSERTION '):
  a=json.loads(x['Output'][len('W09_ASSERTION '):]);
  if a['assertion_id'].startswith('C19'):c19.append(a)
ck('build:C19_raw_present',len(c19)>0);(O/'build-c19-raw.json').write_text(json.dumps(c19,ensure_ascii=False,indent=2),encoding='utf8')
summary={'code_revision':CODE,'candidate_revision':FROZEN,'artifact_count':len(manifest['files']),'source_count':len(env['source_sha256']),'checks':checks,'total':len(checks),'passed':sum(c['pass'] for c in checks),'failed':sum(not c['pass'] for c in checks),'invocations':[{'reference':ref,'selector':i['selectors'],'status':i['status'],'assertions':len(i['assertion_ids'])} for ref,i in invocations.items()],'report_paths':{k:str(v[0].relative_to(R)).replace('\\','/') for k,v in reports.items()}}
(O/'envelope-audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in summary.items() if k!='checks'},ensure_ascii=True))
