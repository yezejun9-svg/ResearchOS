import pathlib,json,hashlib,sqlite3,datetime
EV=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/original-model-qualification-review-20261014');ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os');BASE=ROOT/'execution/v2.4/receipts/W05/W05-99';RUN=BASE/'normal_desktop_attach_retry07_codex/20261014-current-chat';SP=BASE/'resume_cp398_codex/20261014-current-chat/continuation-cp453/original-request-confirm-scope.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
def save(n,x):
 with (EV/n).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
ob=read(RUN/'06-original-run.observed.json');scope=read(SP);assert ref(RUN/'06-original-run.observed.json')['sha256']=='91bff869fa36398abb705dead926714ccacc5289891bfae6a472f3ab39211f81'
request=ob['original_request'];rid=ob['original_request_id'];runid=ob['original_run_id'];project=ob['project_id'];taskid=request['task_id'];assert request==scope['request'];assert 'sha256:'+sha(json.dumps(request,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())==scope['request_hash']==ob['original_request_canonical_digest']
refs=[]
for x in [scope,read(RUN/'01-bound-package-and-observation-plan.json')]:
 for name,r in x.items():
  if isinstance(r,dict) and set(['path','sha256','bytes']).issubset(r):
   p=pathlib.Path(r['path']);p=p if p.is_absolute() else ROOT/p;actual=ref(p);assert actual['sha256']==r['sha256'] and actual['bytes']==r['bytes'];refs.append({'field':name,**actual})
pre=read(RUN/'03-original-prepared-confirmation.observed.json');assert all(v==0 for v in pre['counts'].values()) and pre['private_confirmation_count_for_project']==1
before=read(RUN/'00-before-open.observed.json')['session'][0];after=read(RUN/'02-normal-session-baseline.observed.json')['session'][0];assert all(before[k]==after[k] for k in ['id','project_id','revision','writer_epoch','writer_client_id','workspace_ref','model_config_ref']) and before['lease_expires_at']<after['lease_expires_at']
click=read(RUN/'04-confirm-click.json');assert click['requestId']==rid and click['checkpoint']==453 and click['soleClick'];assert scope['at']<click['at']<request['expires_at'];assert len(ob['consume_rows'])==1
consume=json.loads(ob['consume_rows'][0]['body']);assert consume['run_ref']['id']==runid and consume['task_id']==taskid and consume['request_hash']==scope['request_hash'];assert click['at']<ob['consume_rows'][0]['created_at']<request['expires_at']
qr=ob['qualification_runs'][0];dispatch=ob['dispatches'][0];run=json.loads(ob['run'][0]['safe_body']);accept=json.loads(ob['acceptance_receipts'][0]['body']);ledger=json.loads(ob['ledger_entries'][0]['body']);effects=[json.loads(r['body']) for r in ob['resource_effects']]
assert len(ob['qualification_runs'])==len(ob['dispatches'])==1 and qr['run']==dispatch['run']==runid and qr['epoch']==dispatch['epoch']==run['lease_epoch']==1 and dispatch['state']=='OBSERVED' and run['status']=='SETTLED' and run['children_stopped'] and run['queue_empty'] and run['exit_code']==0
assert [e['state'] for e in effects]==['PREPARED','STARTED','CONFIRMED'] and len({r['effect_key'] for r in ob['resource_effects']})==1 and all(e['payload']['capability']=='MODEL' and e['run_id']==runid and e['task_id']==taskid and e['epoch']==1 for e in effects)
assert effects[-1]['receipt']['model_transport'] is True and effects[-1]['receipt']['payload']['status']==200 and effects[-1]['receipt']['actual_cost'] is None
assert accept['run_id']==runid and accept['subject_ref']['id']==taskid and accept['verdict']=='PASS' and accept['measurement_mode']=='LIVE' and accept['independence_basis']=='DETERMINISTIC_SERVICE' and accept['verifier_principal_id'] not in accept['executor_principal_ids'];assert ledger['cost_basis']=='UNKNOWN' and ledger['money'] is None
# Only fixed original request/run and sealed public Artifact records, inside a read-only snapshot. No credential/configuration tables or fields.
db=pathlib.Path(ob['database']);c=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;c.execute('PRAGMA query_only=ON');c.execute('BEGIN');query_only=c.execute('PRAGMA query_only').fetchone()[0];queries=[]
def query(sql,params):queries.append({'sql':sql,'params':list(params)});return [dict(r) for r in c.execute(sql,params).fetchall()]
current_requests=query("SELECT operation,key,request_hash,body,created_at FROM idempotency WHERE project=? AND key=? AND operation IN('host:managed-runtime-qualification','host:qualification-confirmation') ORDER BY operation",(project,rid));assert len(current_requests)==2
for r in current_requests:
 original=next(x for x in ob['request_rows'] if x['operation']==r['operation']);b=r.pop('body');b=b if isinstance(b,bytes) else b.encode();assert b.decode()==original['body'];r['body_sha256']=sha(b)
current_effects=query("SELECT effect_key,sequence,json_extract(body,'$.state') AS state,json_extract(body,'$.epoch') AS epoch,json_extract(body,'$.payload.capability') AS capability,json_extract(body,'$.request_hash') AS request_hash FROM resource_effects WHERE project=? AND run=? ORDER BY effect_key,sequence",(project,runid));assert len(current_effects)==3 and [x['state'] for x in current_effects]==['PREPARED','STARTED','CONFIRMED'] and {x['capability'] for x in current_effects}=={'MODEL'}
artifacts=[];service_report=None;model_output=None
for aid in ['52d8086dbb42af10946acd21a45ce7c2','c625152d4f56802e582640ac26419ccd']:
 rows=query("SELECT id,revision,body FROM domain_objects WHERE project=? AND kind='Artifact' AND id=?",(project,aid));assert len(rows)==1;meta=json.loads(rows[0]['body']);assert meta['access_class']=='PROJECT' and meta['measurement_mode']=='LIVE' and meta['revision']==1
 data=query("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1",(project,meta['storage_key']));assert len(data)==1;raw=bytes(data[0]['bytes']);assert 'sha256:'+sha(raw)==meta['content_hash'] and len(raw)==meta['byte_size'];content=json.loads(raw)
 if aid.startswith('52'):
  safe={k:v for k,v in content.items() if k!='messages'};assert safe['task_id']==taskid and safe['run_id']==runid and safe['epoch']==1 and safe['model_calls']==1 and safe['tool_calls']==0 and safe['actual_cost'] is None and safe['sdk_cost_is_placeholder'] is True;model_output=safe
 else:
  safe=content;service_report=safe;assert safe['run_ref']['id']==runid and safe['task_ref']['id']==taskid and safe['lease_epoch']==1 and safe['contract_hash']==accept['contract_hash'];assert safe['checks'][0]['status']=='PASS' and safe['checks'][0]['exit_code']==0
 artifacts.append({'metadata':meta,'raw_bytes':len(raw),'raw_sha256':sha(raw),'safe_content_projection':safe,'messages_excluded':aid.startswith('52')})
current_acceptance=query("SELECT id,revision,body FROM domain_objects WHERE project=? AND kind='AcceptanceReceipt' AND id=?",(project,accept['id']));assert len(current_acceptance)==1;body=current_acceptance[0].pop('body');body=body if isinstance(body,bytes) else body.encode();assert body.decode()==ob['acceptance_receipts'][0]['body'];current_acceptance[0]['body_sha256']=sha(body)
c.rollback();c.close()
snapshot={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'database_uri':db.as_uri()+'?mode=ro','PRAGMA_query_only':query_only,'transaction':'BEGIN then ROLLBACK','queries':queries,'requests':current_requests,'effects':current_effects,'artifacts':artifacts,'acceptance':current_acceptance,'scope':'Only immutable original request/run artifacts; no whole-database drift claim and no reads of newer coding configuration','mutations':0}
save('safe-original-evidence-snapshot.json',snapshot)
summary={'request_id':rid,'run_id':runid,'run_epoch':1,'task_id':taskid,'project_id':project,'session_id':ob['session_id'],'scope_timestamp':scope['at'],'click_timestamp':click['at'],'consumed_timestamp':ob['consume_rows'][0]['created_at'],'request_expires_at':request['expires_at'],'request_hash':scope['request_hash'],'plan_hash':qr['plan_hash'],'profile_hash':qr['profile_hash'],'contract_hash':qr['contract_hash'],'baseline_before_prepare':pre['counts'],'writer_renewal':{'prior':before,'after':after,'unchanged_epoch_revision':True},'dispatch':{k:dispatch[k] for k in ['run','epoch','dispatch_key','state','observation_sequence','observation_hash']},'run':run,'effect_key':ob['resource_effects'][0]['effect_key'],'effect_states':[e['state'] for e in effects],'model_transport':True,'provider_response_status':200,'model_calls':model_output['model_calls'],'tool_calls':model_output['tool_calls'],'ledger':ledger,'acceptance':accept,'service_report':service_report,'verified_references':refs,'not_observed':ob['not_observed']}
save('binding-checks.json',summary)
print(json.dumps({'request':rid,'run':runid,'epoch':1,'unique_model_effects':1,'tool_effects':0,'artifacts_verified':len(artifacts),'service_PASS':True,'snapshot_query_only':query_only,'references':len(refs),'not_observed':ob['not_observed']},ensure_ascii=True))
