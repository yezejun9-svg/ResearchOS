from pathlib import Path
import json,hashlib,subprocess,datetime
R=Path.cwd();RUN='8a5ca295-69c0-4ebd-9ae3-8a8e266bc942';D=R/'execution/receipts/W11'/RUN;O=R/'execution/verifier/W11/global-review-8a5ca295'
load=lambda p:json.loads(p.read_text(encoding='utf8'));sha=lambda b:hashlib.sha256(b).hexdigest();hf=lambda p:sha(p.read_bytes());jcs=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();checks=[]
def ck(k,ok,details=None):
 checks.append({'id':k,'pass':bool(ok),'details':details})
 if not ok:print('FAIL',k,ascii(details)[:180])
r=load(D/'receipt.json');manifest=load(D/'artifacts.json');CODE=r['code_revision']
ck('receipt_jcs',sha(jcs({k:v for k,v in r.items() if k!='receipt_hash'}))==r['receipt_hash'].removeprefix('sha256:'))
ck('manifest_binding',hf(D/'artifacts.json')==r['artifact_manifest_hash'].removeprefix('sha256:'))
for a in manifest['files']:ck('artifact:'+a['path'],hf(R/a['path'])==a['sha256'].removeprefix('sha256:'))
# Independently verify every preserved preflight against the actual git objects,
# preserving the earlier failures and distinct successful build version.
for p in D.glob('*environment-before.json'):
 env=load(p)
 ck(p.name+':clean',env['tracked_status_porcelain']=='' and env['tracked_source_clean'])
 for f,h in env['source_sha256'].items():
  b=subprocess.check_output(['git','show',env['git_head']+':'+f],cwd=R);ck(p.name+':source:'+f,sha(b)==h)
 ck(p.name+':spec',hf(R/'spec/v2.0/PACKAGE_MANIFEST.json')==env['spec_manifest_sha256'])
contracts=load(R/'spec/v2.0/contracts/acceptance.json');reports={};invs={}
for v in r['verification_results']:
 ref=v['actual_invocation_reference'];i=load(R/ref);invs[ref]=i
 ck(ref+':success',i['status']=='PASS' and i['exit_code']==0 and i['assertion_ids']==v['assertion_ids'])
 for stream in ['stdout','stderr']:ck(ref+':'+stream,hf(R/i[stream]['path'])==i[stream]['sha256'])
 ck(ref+':registration',sha(subprocess.check_output(['git','show',i['code_revision']+':execution/commands.json'],cwd=R))==i['registered_command_revision'])
 for a in v['artifact_versions']:ck(ref+':adapter:'+a['path'],sha(subprocess.check_output(['git','show',i['code_revision']+':'+a['path']],cwd=R))==a['sha256'])
 for line in (R/i['stdout']['path']).read_text(encoding='utf8').splitlines():
  try:ob=json.loads(line)
  except ValueError:continue
  if 'receipt' not in ob:continue
  p=Path(ob['receipt']);q=load(p);reports[ref]=(p,q);before=load(p.parent/'before.json')
  ck(ref+':report',q['status']=='PASS' and q['exit_code']==0 and not q['missing'] and not q['malformed'] and not q['source_drift'] and q['assertion_ids']==i['assertion_ids'] and set(q['assertion_ids'])==set(q['expected_assertion_ids']))
  ck(ref+':frozen',before['code_revision']==i['code_revision']==CODE and before['automatic_authority']=='NONE')
  for f,h in q['raw_evidence_hashes'].items():ck(ref+':rawhash:'+f,hf(p.parent/f)==h.removeprefix('sha256:'))
  lines=(p.parent/'stdout.txt').read_text(encoding='utf8').splitlines()
  for a in q['assertions']:
   raw=json.loads(lines[a['raw_evidence']['line']-1].split('W11_ASSERTION ',1)[1]);ck(ref+':assert:'+a['assertion_id'],all(raw[k]==a[k] for k in ['assertion_id','expected','actual','status','evidence']) and raw['status']=='PASS')
for c in ['C07','C08']:
 e=load(D/(c+'.json'));spec=next(x for x in contracts['cases'] if x['id']==c)
 ck(c+':fields',all(k in e for k in ['run_receipt','version_manifest','command_receipt','assertion_results','acceptance_receipt']))
 ck(c+':all_assertions',[x['id']for x in spec['assertions']]==[x['assertion_id']for x in e['assertion_results']])
 ck(c+':expected',all(x['expected']==y['expected'] for x,y in zip(spec['assertions'],e['assertion_results'])))
 ck(c+':commands',set(spec['command_keys'])=={x['command_key']for x in e['command_receipt']})
 for section in ['lock_files','input_snapshots','policy_versions']:
  for a in e['version_manifest'][section]:ck(c+':'+section+':'+a['path'],hf(R/a['path'])==a['sha256'])
 for a in e['command_receipt']:
  i=invs[a['reference']];ck(c+':inv:'+a['reference'],hf(R/a['reference'])==a['sha256'] and all(a[k]==i[k] for k in ['argv','cwd','environment_names','exit_code','registered_command_revision','code_revision','command_key']))
 supp=e['supplemental_assertions']
 for a in supp:
  q=reports[a['invocation_reference']][1];matches=[x for x in q['assertions'] if x['assertion_id']==a['assertion_id']];ck(c+':supp:'+a['invocation_reference']+':'+a['assertion_id'],len(matches)==1 and all(a[k]==matches[0][k] for k in ['actual','expected','status','evidence','raw_evidence']))
 for a in e['assertion_results']:
  ck(c+':status:'+a['assertion_id'],a['status']=='PASS' and len(a['actual'])>0)
  for b in a['actual']:ck(c+':binding:'+a['assertion_id']+':'+b['assertion_id'],any(b==s for s in supp))
  for f in a['raw_evidence']:ck(c+':raw:'+f['path'],hf(R/f['path'])==f['sha256'])
# The complete build is independently version-bound, not falsely attributed to617.
bref=next(k for k,i in invs.items() if i['command_key']=='build.check');bi=invs[bref];build=load(R/bi['stdout']['path']);be=load(D/'build-b22d6a9a-7561-4d3f-bc45-2f4f5f65b551-environment-before.json')
ck('build:revision',bi['code_revision']==be['git_head']=='d7cb141305a16b13bfdafad1b514275833c4a3a0')
ck('build:all_steps',all(a['exit_code']==0 for a in build['commands']))
go=next(a for a in build['commands'] if a['name']=='go-test');ck('build:complete_uncached',go['argv'][1:]==['test','-p','1','-json','-count=1','./...'])
ck('build:preflight',datetime.datetime.fromisoformat(be['sampled_at'])<datetime.datetime.fromisoformat(bi['started_at']))
out={'task_id':'W11','run_id':RUN,'total':len(checks),'passed':sum(c['pass'] for c in checks),'failed':sum(not c['pass'] for c in checks),'artifact_count':len(manifest['files']),'fixture_code_revision':CODE,'build_revision':bi['code_revision'],'checks':checks,'invocations':[{'reference':k,'code_revision':i['code_revision'],'command':i['command_key'],'assertions':len(i['assertion_ids'])}for k,i in invs.items()]}
(O/'envelope-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k not in ['checks','invocations']}))
