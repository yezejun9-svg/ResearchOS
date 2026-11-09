from pathlib import Path
import json,hashlib,base64,copy,traceback
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';N=P/'cli43_transport_binding_preparation_codex/2c271a22fbb34123a65d799e854b9d24';O=Path(__file__).parent
checks=[];refs={}
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def pin(p):
 p=path(p);b=p.read_bytes();x={'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};refs[x['path']]=x;return x
def verify(x):
 p=path(x['path']);y=pin(p);ck('pin '+str(p),all(x[k]==y[k] for k in ['sha256','bytes']));return p
def read(p):pin(p);return json.loads(path(p).read_bytes())
def save(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def inverse(raw,changes):
 for x in reversed(changes):
  old=x['old'].encode();new=x['new'].encode();ck('unique inverse '+old[:60].decode(),raw.count(new)==1);raw=raw.replace(new,old,1)
 return raw
try:
 hdf=read(N/'handoff.json');mf=read(N/'manifest.json');ck('handoff supplied',pin(N/'handoff.json')['sha256']=='32e24ea665279ab628710f09eb9323e882cc475b034cf78d9bd7114de939ff9c');ck('MF supplied',pin(N/'manifest.json')['sha256']=='d333d71a2be818e34d3d322dfd517f5dd195d0b06a4c9f0759d3c56411836632')
 for x in mf['members']:verify(x)
 for k,v in hdf.items():
  if k.endswith('_ref') and isinstance(v,dict):verify(v)
 before=read(N/'inputs.before.json');after=read(N/'inputs.after.json');ck('author before after exact',before==after)
 for x in before:verify(x)
 helper=verify(hdf['helper_ref']).read_bytes();test=verify(hdf['instrumented_source_ref']).read_bytes();oldh=verify(hdf['old_helper_ref']).read_bytes();oldt=verify(hdf['old_test_ref']).read_bytes();hc=read(N/'helper.exact-edits.json');tc=read(N/'test.exact-edits.json');plan=read(N/'instrumentation-plan.proposed.json');oldplan=read(verify(hdf['old_plan_ref']))
 ck('8helper 6test exactedits',len(hc)==8 and len(tc)==6)
 ck('helper inverse entire bytes',inverse(helper,hc)==oldh);ck('test inverse entire bytes',inverse(test,tc)==oldt)
 original=R/plan['original_path'];ck('whole plan inverse actual Main bytes',inverse(test,plan['changes'])==original.read_bytes());ck('Main original hash',pin(original)['sha256']==plan['original_sha256']=='f02d74fa43caed9963a12ec902bde3882de84018696e93e259e5c38c3f04f210')
 restore=copy.deepcopy(plan);restore['changes']=restore['changes'][:-6];restore['exact_scoped_inline_edits']=restore['exact_scoped_inline_edits'][:-6];restore['additional_file_ref']=oldplan['additional_file_ref'];restore['instrumented_sha256']=oldplan['instrumented_sha256'];ck('plan full byte inverse',(json.dumps(restore,ensure_ascii=False,indent=2)+'\n').encode()==path(hdf['old_plan_ref']['path']).read_bytes())
 hs=helper.decode();ts=test.decode();olds=oldh.decode()
 st='  canonicalRequest,e:=canonical.JSON(raw)';en='   if method=="session.attach"&&result["write_owner_acquired"]!=false{t.Fatal("readonly attach acquired writer")}';ck('entire original POST validation block',olds[olds.index(st):olds.index(en)+len(en)]==hs[hs.index(st):hs.index(en)+len(en)])
 ck('original immediate byteClone',b'func cli43Bytes(b []byte) map[string]any{b=bytes.Clone(b);' in helper)
 required=['fact.RequestIndex!=i||fact.ResponseIndex!=i||fact.Status!=http.StatusOK','uri.RawQuery!=""||uri.ForceQuery','len(raw)!=0||len(responses[i])==0||completedSends!=1','fact.Method!=http.MethodPost||uri.Path!="/v2/command"||len(raw)==0','binding["route"]!="THIN_CORE"','entities.Validate(kind,reply)','reply["id"]!=parts[4]||reply["project_id"]!=cfg.ProjectID','reply["id"]!=sendGoal','reply["goal_id"]!=sendGoal','completedSends!=1||len(goals)!=1||len(tasks)!=1','matches!=1','compiler.UseLoader(cli43LocalSchemaOnly{})','compiler.AssertFormat();compiler.DefaultDraft(jsonschema.Draft2020)']
 for x in required:ck('strict source guard '+x,x in hs)
 ck('request index under mutex','mu.Lock()\n\t\t\t\t\trequestIndex := len(requests)' in ts)
 ck('transport response appended together','transport = append(transport, cli43TransportFact{RequestIndex: requestIndex, ResponseIndex: len(responses), Method: r.Method, RequestURI: r.URL.RequestURI(), Status: resp.StatusCode})\n\t\t\t\t\tresponses = append' in ts)
 schema=read(verify(hdf['schema_ref']));srefs=[];patterns=[];wo=[]
 def walk(x):
  if isinstance(x,dict):
   if '$ref' in x:srefs.append(x['$ref'])
   if 'pattern' in x:patterns.append(x['pattern'])
   if x.get('writeOnly') is True:wo.append(x)
   for v in x.values():walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 walk(schema)
 for s in srefs:
  cur=schema;ok=s.startswith('#/')
  for seg in s[2:].split('/'):
   seg=seg.replace('~1','/').replace('~0','~')
   if not isinstance(cur,dict) or seg not in cur:ok=False;break
   cur=cur[seg]
  ck('local schema ref '+s,ok)
 ck('schema no writeOnly and 6 simple patterns',not wo and len(patterns)==6)
 for name in ['internal/domain/contracts.go','internal/domain/contracts_persistence_v24.go','go.mod']:pin(R/name)
 runner=P/'cli43_test2json_preparation_codex/72d89fe5130e4e83a7dc44257289c1db/runner.v7.proposed.py';rt=runner.read_text(encoding='utf-8');pin(runner);ck('runner identity consumer keys retained',"ident['before_sid']==ident['after_sid']==ident['db_sid'] and ident['epoch']==1" in rt and all(k in hs for k in ['"before_sid"','"after_sid"','"db_sid"','"epoch"']))
 # Only read and compare existing r329 fixture JSON. No Go/schema execution.
 f=R/'.local/cli43-export-246c20b781664b0e80fae7fd29b9b2b4/.cli43-build/case-evidence/case-01/TestCLIProtocolInteractiveAuthority_real-existing-self-send';summary=read(f/'http-summary.json');rq=read(f/'requests.exact.json');rp=read(f/'responses.base64.json');proxy=sorted([x for x in summary['records'].values() if x['layer']=='proxy'],key=lambda x:x['sequence']);sendgoal=None;goal=None;task=None;actualpairs=[]
 for i,(q,b,rec) in enumerate(zip(rq,rp,proxy)):
  qb=b'' if q['raw_base64'] is None else base64.b64decode(q['raw_base64'],validate=True);rb=base64.b64decode(b,validate=True);reply=json.loads(rb)
  actualpairs.append({'i':i,'method':rec['request_method'],'URI':rec['request_uri'],'request_bytes':len(qb),'response_bytes':len(rb),'status':rec['status']})
  ck('actual status200 '+str(i),rec['status']==200)
  if qb:
   env=json.loads(qb);ck('actual POST route '+str(i),rec['request_method']=='POST' and rec['request_uri']=='/v2/command')
   if env['method']=='session.send':sendgoal=reply['result']['snapshot']['goal_id']
  else:
   ck('actual exact GET route and THIN_CORE '+str(i),rec['request_method']=='GET' and rec['request_uri'].split('/')[-1]==reply['id'] and reply['binding']['route']=='THIN_CORE')
   if '/goals/' in rec['request_uri']:goal=reply
   elif '/tasks/' in rec['request_uri']:task=reply
 ck('actual send Goal Task full linkage',sendgoal==goal['id']==task['goal_id'] and goal['task_ids'].count(task['id'])==1 and goal['project_id']==task['project_id'])
 ck('9proxy 12upstream 3setup',len(rq)==len(rp)==len(proxy)==9 and summary['upstream']['dispatched']==12 and summary['proxy']['admitted']==9)
 origins=[]
 for x in hdf['original_diagnostic_failures_preserved']:origins.append({'ref':pin(R/x),'original_payload':read(R/x)})
 save('audit.json',{'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'input_refs':list(refs.values()),'schema_internal_ref_count':len(srefs),'patterns_exact':patterns,'actual_r329_pairs':actualpairs,'original_diagnostic_origins':origins,'target_executions':0,'schema_validation_executed':False,'counter_written':False})
 print(json.dumps({'audit_ref':pin(O/'audit.json'),'checks':len(checks),'failed_checks':[x for x in checks if not x['passed']],'output':str(O)},ensure_ascii=False))
except BaseException as e:
 save('audit.failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'checks':checks,'input_refs':list(refs.values())});raise
