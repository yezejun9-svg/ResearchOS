from pathlib import Path
import json,hashlib,subprocess,base64,datetime,collections
R=Path.cwd();O=R/'.local/w10-global-audit';load=lambda p:json.loads(p.read_text(encoding='utf8'));sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def check(k,ok,actual=None):
 checks.append({'id':k,'pass':bool(ok),'actual':actual})
 if not ok:print('FAIL',k,actual)
for rid in ['18381650-6312-49c0-9a07-faa87c6c6d6b','3c780b46-f776-4648-a69a-3f19c87e068b','c05b1992-5aff-441e-bd0b-cef29b40611a']:
 d=R/'execution/receipts/W10'/rid;x=load(d/'native-execution.json');e=load(d/'native-experiment.json');a=load(d/'native-acceptance.json')
 check(rid+':registered_before_reserved',datetime.datetime.fromisoformat(e['registered_at'])<datetime.datetime.fromisoformat(x['reserved_at']))
 check(rid+':bindings',x['experiment_id']==e['id'] and x['preregistration_hash']==e['preregistration_hash'] and x['run_id'] in e['run_ids'] and x['candidate_ref']['content_hash']==x['manifest']['candidate_hash'] and x['baseline_refs'][0]['content_hash']==x['manifest']['baseline_hash'])
 values=[]
 for i,raw in enumerate(x['raw_exports']):
  rc=x['sandbox_receipts'][i];rs=x['reports'][i];rows=json.loads(raw)
  check(rid+':raw_hash:'+str(i),'sha256:'+sha(raw.encode())==x['raw_hashes'][i])
  check(rid+':native_stdout:'+str(i),base64.b64decode(rc['stdout']).decode().strip()==raw.strip())
  check(rid+':isolation:'+str(i),rc['pid']>0 and not rc['capabilities'] and rc['exit_code']==0 and rc['children_stopped'] and not rc['timed_out'])
  check(rid+':expected_ids:'+str(i),[r['case_id'] for r in rows]==x['manifest']['expected_case_ids'])
  values.append(sum(r['verdict']=='PASS' and r['hard_checks_passed'] is True for r in rows)/len(x['manifest']['expected_case_ids']))
  check(rid+':counts:'+str(i),rs['counts']['pass_count']==sum(r['verdict']=='PASS' for r in rows) and rs['counts']['expected_count']==2)
 check(rid+':manual_means',values==[0.5,1.0] and e['results'][0]['baseline']=='0.5' and e['results'][0]['candidate']=='1' and e['outcome']=='IMPROVED',values)
 check(rid+':independent_acceptance',a['verdict']=='PASS' and a['id']==e['acceptance_id'])
for rid in ['23e20a25-6267-44dd-b100-c43568c290b1','7779d54c-4467-43a9-9320-b58504dd7ce8']:
 d=R/'execution/receipts/W10'/rid;raw=load(d/'raw-results.json');report=load(d/'protocol-report.json');unique={}
 for row in raw:unique.setdefault(row['case_id'],row)
 counts=collections.Counter(row['verdict'] for row in unique.values());counts['MISSING']=12-len(unique)
 want={'expected_count':12,'observed_count':11,'pass_count':5,'fail_count':4,'error_count':1,'abstain_count':1,'missing_count':1,'duplicate_count':1}
 check(rid+':manual_protocol_counts',counts=={'PASS':5,'FAIL':4,'ERROR':1,'ABSTAIN':1,'MISSING':1} and report['counts']==want and report['integrity_status']=='INVALID',dict(counts))
 check(rid+':all_12_labels',[x['verdict'] for x in report['results']]==['PASS','PASS','FAIL','FAIL','FAIL','FAIL','PASS','PASS','ABSTAIN','ERROR','PASS','MISSING'])
for rid in ['23e20a25-6267-44dd-b100-c43568c290b1','7779d54c-4467-43a9-9320-b58504dd7ce8','3c780b46-f776-4648-a69a-3f19c87e068b']:
 d=R/'execution/receipts/W10'/rid
 for mode in ['baseline','candidate']:
  rc=load(d/('sandbox-'+mode+'.json'));raw=base64.b64decode(rc['stdout']);v=json.loads(raw);check(rid+':sandbox_'+mode,raw==(d/(mode+'.stdout.txt')).read_bytes() and v['sum']==(10 if mode=='baseline' else 11) and all(v[k] is True for k in ['read_denied','write_denied','input_write_denied','network_denied','external_denied']) and 'forbidden' in v['external_error'],{'pid':rc['pid'],'sum':v['sum'],'external_error':v['external_error']})
 rc=load(d/'sandbox-timeout.json');check(rid+':timeout',rc['timed_out'] and rc['children_stopped'] and rc['exit_code']==124)
expected={'positive':('1','3','PASS','IMPROVED'),'negative':('3','1','FAIL','REGRESSED'),'null':('1',None,'INCONCLUSIVE','INCONCLUSIVE'),'inconclusive':(None,None,'INCONCLUSIVE','INCONCLUSIVE'),'stable':('1','1','FAIL','NO_IMPROVEMENT')}
d=R/'execution/receipts/W10/18381650-6312-49c0-9a07-faa87c6c6d6b';report=load(d/'report.json');rows={a['assertion_id']:a for a in report['assertions']}
for scenario,want in expected.items():
 a=rows['A07-RECOMPUTE-'+scenario]['actual'][0];actual=(a['baseline'],a['candidate'],a['status'],rows['A07-OUTCOME-'+scenario]['actual']);check('manual_fixture_'+scenario,actual==want,actual)
# In 7c5 only later W12 registration files differ; exact 5cf execution bytes must all match.
prior=load(O/'audit.json');diffs=[]
for a in prior['audit']:
 if not a['pass'] and a['id'].startswith('source:'):
  p=a['id'].split(':',1)[1];env=load(R/'execution/receipts/W10/427ceef6-aa54-4a6b-a0a0-7b988b1f9272/environment-before.json');b=subprocess.check_output(['git','show','5cf08bb:'+p],cwd=R);check('executed_source:'+p,sha(b)==env['source_sha256'][p]);diffs.append({'path':p,'executed_hash':sha(b),'candidate_hash':sha(subprocess.check_output(['git','show','7c5d7ce:'+p],cwd=R))})
result={'checks':checks,'total':len(checks),'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'later_registration_differences':diffs,'basis':'Independent manual arithmetic, raw-export parsing, native stdout bytes, preregistration order, and git blobs; no product recompute function used.'};(O/'recompute.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print('checks',len(checks),'passed',result['passed'],'failed',result['failed'])
