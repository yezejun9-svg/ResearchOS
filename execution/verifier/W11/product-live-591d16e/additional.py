from pathlib import Path
import json, http.client, uuid, datetime, hashlib

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
DECL=json.loads((ROOT/'execution/receipts/W11/product-live/import-jev-client591d16e.stdout.json').read_text(encoding='utf-8-sig'))
SUMMARY=json.loads((ROOT/'execution/verifier/W11/frozen-live-ac9d6153/aggregate.stdout.json').read_text())
PROJECT=DECL['project_id']; BASE='/v1/projects/'+PROJECT
creds={name:json.loads((ROOT/path).read_text(encoding='utf-8-sig')) for name,path in {'verifier':'.local/secrets/jev-independent-verifier-initial.json','owner':'.local/secrets/researchos-owner-initial.json'}.items()}
events=[]
def request(name,principal,method,path,body=None,etag=None,protected_content=False):
    headers={'Authorization':'Bearer '+creds[principal]['token'],'X-Correlation-ID':str(uuid.uuid4())}
    if body is not None:headers['Content-Type']='application/json'
    if method!='GET':headers['Idempotency-Key']='independent-w11-'+name+'-'+str(uuid.uuid4())
    if etag:headers['If-Match']=etag
    conn=http.client.HTTPConnection('127.0.0.1',8787,timeout=20)
    conn.request(method,path,json.dumps(body,separators=(',',':')).encode()if body is not None else None,headers)
    res=conn.getresponse();code=res.status;rh=dict(res.getheaders())
    if protected_content and code<400:
        conn.close();record={'name':name,'status':code,'unexpected_content_success':True,'body_read':False}
        events.append(record);(OUT/'additional-http-events.json').write_text(json.dumps(events,indent=2));raise RuntimeError('protected content unexpectedly available; body was not read')
    raw=res.read();conn.close()
    (OUT/(name+'.response.json')).write_bytes(raw)
    try:value=json.loads(raw)
    except Exception:value=None
    record={'name':name,'principal_id':creds[principal]['principal_id'],'method':method,'path':path,'request_headers':{k:v for k,v in headers.items()if k!='Authorization'},'request_body':body,'status':code,'response_headers':rh,'response_file':name+'.response.json','body_sha256':hashlib.sha256(raw).hexdigest()}
    events.append(record);(OUT/'additional-http-events.json').write_text(json.dumps(events,indent=2))
    if code==401:raise RuntimeError('credential expired or unauthenticated for '+principal)
    return code,rh,value

holdout=DECL['qualifications'][0]['qualification']['holdout_artifact_ref']['id']
code,_,state=request('owner-project-state','owner','GET',BASE+'/state')
assert code==200
code,_,events_body=request('owner-event-list','owner','GET',BASE+'/events?limit=100')
assert code==200
code,_,contexts=request('owner-context-list','owner','GET',BASE+'/context-bundles?limit=100')
assert code==200
code,_,search=request('owner-restricted-search','owner','POST',BASE+'/search',{'query':'independent-boundary-probe','snapshot_ids':[holdout],'limit':10,'expected_state_revision':state['revision']})
assert code in {403,404,422}
for lang in ['zh','zh-en']:
 receipt=json.loads((OUT/(lang+'-independent-acceptance.response.json')).read_text())
 code,_,persisted=request(lang+'-acceptance-persisted','verifier','GET',BASE+'/acceptances/'+receipt['id'])
 assert code==200 and persisted==receipt
 canonical={k:v for k,v in receipt.items()if k!='receipt_hash'}
 digest='sha256:'+hashlib.sha256(json.dumps(canonical,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 assert digest==receipt['receipt_hash']
 summary_raw=(OUT/(lang+'-public-summary-content.response.json')).read_bytes()
 assert 'sha256:'+hashlib.sha256(summary_raw).hexdigest()==receipt['artifact_refs'][0]['content_hash']
assert SUMMARY['frozen_run']['dataset']['ticket'] not in json.dumps(events_body)
assert holdout not in json.dumps(contexts)
secret_hits=[]
for file in OUT.rglob('*'):
 if file.is_file():
  data=file.read_bytes()
  if any(c['token'].encode()in data for c in creds.values()):secret_hits.append(str(file.relative_to(OUT)))
assert not secret_hits
(OUT/'additional-checks.json').write_text(json.dumps({'status':'PASS','http_calls':len(events),'owner_events_no_private_storage_ticket':True,'owner_context_list_no_holdout_ref':True,'owner_search_denied_status':next(e['status']for e in events if e['name']=='owner-restricted-search'),'receipt_hashes_independently_recomputed':2,'public_artifact_raw_hashes_match_receipts':2,'credential_leak_paths':secret_hits},indent=2))
print(json.dumps({'status':'PASS','additional_http_calls':len(events),'credential_leaks':0}))
