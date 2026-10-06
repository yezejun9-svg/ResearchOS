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
        events.append(record);(OUT/'http-events.json').write_text(json.dumps(events,indent=2));raise RuntimeError('protected content unexpectedly available; body was not read')
    raw=res.read();conn.close()
    (OUT/(name+'.response.json')).write_bytes(raw)
    try:value=json.loads(raw)
    except Exception:value=None
    record={'name':name,'principal_id':creds[principal]['principal_id'],'method':method,'path':path,'request_headers':{k:v for k,v in headers.items()if k!='Authorization'},'request_body':body,'status':code,'response_headers':rh,'response_file':name+'.response.json','body_sha256':hashlib.sha256(raw).hexdigest()}
    events.append(record);(OUT/'http-events.json').write_text(json.dumps(events,indent=2))
    if code==401:raise RuntimeError('credential expired or unauthenticated for '+principal)
    return code,rh,value

outcomes=[]
holdout=DECL['qualifications'][0]['qualification']['holdout_artifact_ref']['id']
code,_,artifact=request('verifier-holdout-metadata','verifier','GET',BASE+'/artifacts/'+holdout)
assert code==200 and artifact['access_class']=='VERIFIER_ONLY' and artifact['content_hash']==SUMMARY['frozen_run']['dataset']['hash']
assert artifact['storage_key']==SUMMARY['frozen_run']['dataset']['ticket']
for principal,expected in [('owner',{403,404}),('verifier',{503})]:
    code,_,_=request(principal+'-holdout-content-denied',principal,'GET',BASE+'/artifacts/'+holdout+'/content',protected_content=True)
    assert code in expected
code,_,_=request('owner-holdout-metadata-denied','owner','GET',BASE+'/artifacts/'+holdout)
assert code in {403,404}

for decl in DECL['qualifications']:
    q=decl['qualification'];lang=q['scope']['language'];qid=q['id']
    code,headers,current=request(lang+'-qualification-before','verifier','GET',BASE+'/qualifications/'+qid)
    assert code==200 and current==q and current['status']=='DRAFT'
    key=next(k for k in SUMMARY['frozen_run']['keys']if k['scope']==q['scope'])
    assert q['total_case_count']==45 and q['holdout_case_count']==15 and q['thresholds_frozen_at']==SUMMARY['frozen_run']['frozen_at']
    etag=next(v for k,v in headers.items()if k.lower()=='etag')
    refs=[q['dataset_artifact_ref'],q['holdout_artifact_ref']]
    now=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
    checks=[{'check_id':cid,'status':'PASS','evidence_refs':refs,'command_key':'test.jev.live','actual':'Independent public service aggregate review: frozen live evaluation completed, exact dataset/rubric/model binding verified; qualification FAILED with no automatic authority.','exit_code':0,'started_at':SUMMARY['frozen_run']['frozen_at'],'finished_at':now}for cid in decl['check_ids']]
    body={'subject_ref':{'entity_type':'Qualification','id':qid,'revision':q['revision'],'content_hash':None},'run_id':None,'contract_hash':decl['contract_hash'],'input_refs':refs,'artifact_refs':[],'checks':checks,'verdict':'PASS','executor_principal_ids':['jev-registrar'],'independence_basis':'DETERMINISTIC_SERVICE','blocking_conflict_ids':[],'qualification_ids':[],'policy_revision':decl['policy_revision'],'measurement_mode':'LIVE','reason':'Accept independently verified completed negative evaluation evidence only; qualification remains FAILED/ADVISORY/NONE.'}
    code,_,receipt=request(lang+'-independent-acceptance','verifier','POST',BASE+'/acceptances',body,etag)
    assert code==201 and receipt['verdict']=='PASS' and receipt['verifier_principal_id']=='jev-independent-verifier'
    assert receipt['executor_principal_ids']==['jev-registrar'] and receipt['contract_hash']==decl['contract_hash']
    assert len(receipt['artifact_refs'])==1 and all(c['status']=='PASS'for c in receipt['checks'])
    result={'requested_maximum_mode':'ADVISORY','critical_false_accept_count':key['critical_false_accept'],'false_accept_rate':key['false_accept']/key['planned'],'false_reject_rate':key['false_reject']/key['positive_label_count'],'abstain_rate':key['abstain']/key['planned'],'test_receipt_refs':receipt['artifact_refs'],'acceptance_id':receipt['id']}
    code,_,accepted=request(lang+'-qualification-result','verifier','POST',BASE+'/qualifications/'+qid+'/result',result,etag)
    assert code==200 and accepted['status']=='FAILED' and accepted['maximum_mode']=='ADVISORY' and accepted['jev_called']is True
    assert accepted['revision']==2 and accepted['acceptance_id']==receipt['id']
    code,_,persisted=request(lang+'-qualification-persisted','verifier','GET',BASE+'/qualifications/'+qid)
    assert code==200 and persisted==accepted
    ref=receipt['artifact_refs'][0]
    code,_,public=request(lang+'-public-summary-artifact','owner','GET',BASE+'/artifacts/'+ref['id'])
    assert code==200 and public['access_class']=='PROJECT'
    code,_,summary=request(lang+'-public-summary-content','owner','GET',BASE+'/artifacts/'+ref['id']+'/content')
    assert code==200 and summary==SUMMARY and summary['frozen_run']['automatic_authority']=='NONE'
    outcomes.append({'language':lang,'qualification_id':qid,'acceptance_id':receipt['id'],'public_summary_artifact':ref,'result':accepted,'public_summary_exactly_matches_protected_service':True})
    (OUT/'outcomes.json').write_text(json.dumps(outcomes,indent=2))

code,_,listing=request('owner-artifact-list','owner','GET',BASE+'/artifacts?limit=100')
assert code==200 and holdout not in json.dumps(listing)
print(json.dumps({'status':'PASS','http_calls':len(events),'qualifications':[{k:o[k]for k in ['language','qualification_id','acceptance_id']}for o in outcomes],'automatic_authority':'NONE','private_body_read':False}))
