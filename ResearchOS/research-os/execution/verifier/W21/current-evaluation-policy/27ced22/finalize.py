from pathlib import Path
import json,hashlib
p=Path(__file__).parent;root=Path(r'D:/作品集/ResearchOS/research-os')
load=lambda x:json.loads(x.read_text(encoding='utf-8-sig'))
write=lambda n,v:(p/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
events=[json.loads(x) for x in (p/'tests-attempt-01.raw.jsonl').read_text(encoding='utf-8-sig').splitlines() if x.strip()]
chunks={}
for e in events:chunks.setdefault(e.get('Test',''),[]).append(e.get('Output',''))
assertions=[]
for test,parts in chunks.items():
 for line in ''.join(parts).splitlines():
  for prefix in ['W11_ASSERTION ','R03_ASSERTION ']:
   if line.startswith(prefix):
    a=json.loads(line[len(prefix):]);assertions.append({'test':test,'assertion_id':a['assertion_id'],'status':a['status']})
write('assertion-results-attempt-01.json',assertions)
write('attempt-01-summary.json',{'go_os_exit':'NOT_PERSISTED','review_runner_exit':1,'runner_failure':'Postprocessing JSONDecodeError: Go test split a long W11_ASSERTION across output events; no test failure. Fixed concatenation per test before parsing.','package_event':[e for e in events if e.get('Action') in ['pass','fail'] and not e.get('Test')],'pass_tests':[e['Test'] for e in events if e.get('Action')=='pass' and e.get('Test')],'failed_tests':[e.get('Test',e.get('Package')) for e in events if e.get('Action')=='fail'],'assertion_count':len(assertions),'failed_assertions':[a for a in assertions if a['status']!='PASS'],'raw_sha256':hashlib.sha256((p/'tests-attempt-01.raw.jsonl').read_bytes()).hexdigest(),'source_unchanged':load(p/'source-before-attempt-01.json')['files']==load(p/'source-after-attempt-01.json')['files']})
mapping=[
 ('C07-01',['C07-HARD-*','C07-NO-ADOPT-*','C07-MANUAL-*'],'PASS_CURRENT_PUBLIC_FIXTURE','Required failure/reference/hash gates and manual/legacy decision adoption reject. No formal/native reissue.'),
 ('C07-02',['C07-RECEIPT-*'],'PASS_CURRENT_PUBLIC_FIXTURE','Three maximum-score signals retained with deterministic FAIL and refusal reason; raw fixture receipt contains version/evidence.'),
 ('C07-03',['C07-NO-ADOPT-*','C07-MANUAL-NO-ADOPT-*'],'PASS_CURRENT_PUBLIC_FIXTURE','current_decision_refs unchanged and adoption request rejected; full production artifact inventory/action counter not independently enumerated.'),
 ('C08-01',['C08-STATUS-*','C08-NO-AUTO-*','*-NO-INHERIT-*'],'PASS_CURRENT_PUBLIC_FIXTURE_AND_PURE_BINDING','Four failure branches abstain; all BOUNDED_AUTO requests reject; five-dimensional qualification contract cannot inherit old receipt.'),
 ('C08-02',['C08-STATUS-*','C08-PRESERVE-*'],'PASS_CURRENT_PUBLIC_FIXTURE','Saved raw evidence and state refs retained; no empty-result promotion.'),
 ('C08-03',['C08-CONTINUE-*'],'PASS_CURRENT_PUBLIC_FIXTURE','Independent requirement create/list remain usable; loopback provider failure is fixture only, not live service availability.'),
 ('A08-01',['*-EXACT-FIVE-DIMENSION-KEY','*-FROZEN-THRESHOLDS','*-NO-INHERIT-*'],'PASS_CURRENT_PUBLIC_BINDING_ONLY','Reuse original accepted freeze/independence; no private labels or source-family regeneration.'),
 ('A08-02',['*-INSUFFICIENT-PER-KEY','*-FAILED-ADVISORY-NONE','C08-NO-AUTO-*'],'PASS_CURRENT_PUBLIC_BINDING_ONLY','Each language has development30/holdout15; aggregate30 grants no key automation.'),
 ('A08-03',['*-ORIGINAL-AGGREGATE','*-RESULT-RATES','C08-STATUS-chinese_low_confidence'],'PASS_CURRENT_PUBLIC_BINDING_ONLY','Original aggregate reused; FA/negative label counts and coverage derived below. No current live calls.'),
 ('A08-04',['*-DRAFT-TO-FAILED','*-CURRENT-RECEIPT-BINDING'],'PASS_CURRENT_PUBLIC_BINDING_ONLY','Accepted evaluation receipt remains distinct from FAILED/ADVISORY qualification; automatic authority NONE.'),
 ('A08-05',['C07-*','*-REJECT-REHASHED-*'],'PASS_CURRENT_PUBLIC_FIXTURE_AND_PURE_BINDING','Current semantic binding rejects recomputed hashes with wrong policy/author/verifier/inputs/checks; never calls live writer.'),
 ('A08-06',['JEV-PROMPT-protected-*'],'PARTIAL_HISTORICAL_ISOLATION_REUSED','Current classification-only rejection passes; actual OS/service/private export boundary reused historically, not requalified.'),
 ('R03-PROMPT-JSON',['JEV-PROMPT-json-body'],'PARTIAL_FIXTURE_STARTUP_FAILURE','First raw contains passing assertion; second attempt failed readiness before business IO/semantic assertion, no further retry.')]
write('assertion-scope-map.json',[{'formal_assertion':a,'current_assertion_patterns':b,'delta_scope_verdict':c,'limit':d,'formal_verdict_reissued':False} for a,b,c,d in mapping])
summary=load(root/'execution/verifier/W11/product-live-591d16e/zh-public-summary-content.response.json')
keys=[]
for k in summary['frozen_run']['keys']:
 keys.append({'scope':k['scope'],'false_accept_over_negative_labels':[k['false_accept'],k['negative_label_count']],'nonabstained_coverage':[k['nonabstained_accept_count']+k['nonabstained_reject_count'],k['planned']],'accept_coverage':[k['nonabstained_accept_count'],k['planned']],'abstain':[k['abstain'],k['planned']],'actual_automatic_action_coverage':0,'cost_status':'UNKNOWN'})
write('safe-derived-metrics.json',{'basis':'ALREADY_ACCEPTED_PUBLIC_AGGREGATE_NOT_FRESH_PROVIDER_RESULT','keys':keys,'automatic_authority':'NONE'})
print(json.dumps({'attempt01_assertions':len(assertions),'attempt01_pass_events':sum(e.get('Action')=='pass' and bool(e.get('Test')) for e in events),'attempt02_assertions':load(p/'command.json')['assertion_count'],'mapped_rows':len(mapping)}))
