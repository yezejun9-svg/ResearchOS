from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();O=R/'execution/verifier/W11/global-review-8a5ca295';load=lambda p:json.loads(p.read_text(encoding='utf8'));h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
def ck(i,x,d=None):checks.append({'id':i,'pass':bool(x),'details':d})
for p,rev in [('internal/domain/decision.go','e916704'),('internal/domain/changes.go','e916704'),('adapters/decision/jev.go','e44756d')]:
 a=subprocess.check_output(['git','show',rev+':'+p]);b=subprocess.check_output(['git','show','617e6b2:'+p]);c=subprocess.check_output(['git','show','d7cb141:'+p]);ck('independent_source_continuity:'+p,a==b==c,{'reviewed_revision':rev,'sha256':hashlib.sha256(a).hexdigest()})
C=load(R/'execution/receipts/W11/fixture/f2a531eb-b123-49d0-9dad-4cc8cc84d460/report.json');A={a['assertion_id']:a for a in C['assertions']}
for case in ['experiment_failed','citation_missing','artifact_hash_mismatch']:
 e=A['C07-HARD-'+case]['evidence'];r=e['raw_high_score'];ck('C07:hard_reject:'+case,400<=e['status']<500)
 ck('C07:maximum_signal:'+case,len(r['signals'])==3 and {s['operation']:s['value'] for s in r['signals']}=={'CHOICE':'ACCEPT','NOUL':'1','SCORE':'1'} and all(s['probability']==1 and s['host_abstained'] is False for s in r['signals']))
 ck('C07:immutable_failure:'+case,r['status']=='ABSTAIN' and r['scope']['model_revision']=='jev-1.13.0' and r['deterministic_results'][0]['status']=='FAIL' and 'DETERMINISTIC_CHECK_NOT_PASSED' in r['rationale'] and len(r['evidence_refs'])>0)
 ck('C07:no_adopt:'+case,A['C07-NO-ADOPT-'+case]['actual']==[True,[]])
for case in ['failed_check','missing_evidence']:
 ck('C07:manual_abstain:'+case,A['C07-MANUAL-ABSTAIN-'+case]['actual']=='ABSTAIN')
 for generation in ['new','legacy']:ck('C07:manual_adoption:'+case+':'+generation,A['C07-MANUAL-NO-ADOPT-'+case+'_'+generation]['actual']==[422,[]])
C=load(R/'execution/receipts/W11/fixture/f0824208-d7c2-4478-a409-0ee5a23f50f1/report.json');A={a['assertion_id']:a for a in C['assertions']}
for case in ['positive','timeout','model_revision_changed','chinese_low_confidence','contradictory_evidence']:
 want='DECIDED' if case=='positive' else 'ABSTAIN';ck('C08:fallback:'+case,A['C08-STATUS-'+case]['actual']==[want,'ADVISORY',None]);ck('C08:preserve:'+case,A['C08-PRESERVE-'+case]['actual']==['CURRENT','FIXTURE',[]]);ck('C08:closed_authority:'+case,A['C08-NO-AUTO-'+case]['actual']==503);ck('C08:continue:'+case,A['C08-CONTINUE-'+case]['actual'] is True)
for aid,want in [('QUAL-DRAFT-NO-CALL-CLAIM',['DRAFT','ADVISORY',False,None]),('QUAL-CLIENT-STATS-NO-AUTHORITY',503),('QUAL-SCOPE-NO-INHERIT',['ABSTAIN','ADVISORY',None]),('QUAL-STILL-DRAFT','DRAFT'),('JEV-IMPORTED-LIVE-NO-PROOF',['ABSTAIN',False,'FIXTURE',True]),('JEV-NO-JSON-HOST-CAPABILITY',400),('JEV-HOST-AUTHORIZATION',True)]:ck('C08:'+aid,A[aid]['actual']==want)
refs=[]
for d in ['application-4545151','application-e916704','adapter-e44756d','protected-617e6b2','protected-2c19aa6']:
 p=R/'execution/verifier/W11'/d/'review.json';refs.append({'path':str(p.relative_to(R)).replace('\\','/'),'sha256':h(p)})
for rev in ['c2536e2','6b4f935','d7cb141']:(O/(rev+'.diff')).write_bytes(subprocess.check_output(['git','show','--format=fuller',rev]))
out={'total':len(checks),'passed':sum(c['pass']for c in checks),'failed':sum(not c['pass']for c in checks),'checks':checks,'independent_review_references':refs,'source_review':'C07/C08 decision, change adoption and adapter production sources unchanged from previously independently tested revisions through final build. c2536e2 only fresh listener readiness before effects with single-shot regression;6b4f935 runs complete go test -p1 count1;d7cb141 catches TimeoutError under unchanged readiness deadline. Protected data lineage correction 2c19aa6 separately independently reviewed; formal service preparation excluded.','limits':['C07/C08 use deterministic loopback providers; no live accuracy conclusion.','Earlier failed full builds preserved in executor artifacts.','Fixture timeout result alone does not prove provider handler arrival; earlier independent FaultPersistence diagnostic separately proved entered-handler timeout and continued work.']}
(O/'semantic-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print({k:v for k,v in out.items() if k in ['total','passed','failed']});print([c for c in checks if not c['pass']])
