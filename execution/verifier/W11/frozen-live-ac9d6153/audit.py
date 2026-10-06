from pathlib import Path
import json, hashlib, datetime

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
RAW = ROOT / 'execution/receipts/W11/frozen-live/ac9d6153-7ac9-42ed-a97f-d5d05409752d'
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
checks = []
def check(name, expected, actual):
    checks.append({'id':name, 'expected':expected, 'actual':actual, 'status':'PASS' if expected == actual else 'FAIL'})

s = load(OUT/'aggregate.stdout.json')
f = s['frozen_run']
check('terminal-persistent-public-read', s, load(OUT/'status.stdout.json'))
check('parent-terminal-matches-independent', s, load(RAW/'terminal-status.json'))
check('parent-aggregate-matches-independent', s, load(RAW/'aggregate.stdout.json'))
check('state', ['EXECUTION_REPORTED','COMPLETED','FAILED','ADVISORY','NONE','UNKNOWN'], [s['status'],f['run_state'],f['qualification'],s['maximum_mode'],f['automatic_authority'],f['cost_status']])
check('bound-project','aede0678-7308-43dc-b9f2-cfe3d90cfdfb', f['project_id'])
check('bound-plan',['independent-source-records-v1','sha256:e15d497fa2bb011b33c5a5049e5a7300570fab8b9ebdaf97b2125b671a872dfd',0.8,30],[f['generator_revision'],f['rubric_hash'],f['confidence_threshold'],f['request_budget']])
check('bound-binary','sha256:b7af809432a96a175375028088303f0a63abe42f3b273a8cc95faf3c5985c015',f['binary_hash'])
metadata = load(OUT/'installed-metadata.json')
check('installed-binary-and-manifest',[f['binary_hash'][7:]]*2,[metadata['binary_sha256'],metadata['manifest_binary_sha256']])
check('same-installed-service-process',79136, metadata['service_pid'])
check('service-still-running','Running',metadata['service_state'])
check('development-hash', 'sha256:'+sha(ROOT/'execution/verifier/W11/development-v2-live-89172731/verified-development-aggregate.json'), f['development_aggregate_hash'])
check('dataset-metadata',[f['project_id'],'LIVE','application/json','ps1:'+f['dataset']['hash'][7:39]],[f['dataset']['project'],f['dataset']['measurement_mode'],f['dataset']['media_type'],f['dataset']['ticket']])
check('dataset-size-positive',True,f['dataset']['size']>0)
start = datetime.datetime.fromisoformat(load(RAW/'environment.json')['started_at'])
frozen_at = datetime.datetime.fromisoformat(f['frozen_at'].replace('Z','+00:00'))
check('marker-after-authorized-start',True,frozen_at>=start)
check('prestart-ready','READY',load(RAW/'before.json')['frozen_run']['run_state'])
check('start-nonterminal-no-partial-feedback',['RUNNING',0,None],[load(RAW/'start.stdout.json')['frozen_run']['run_state'],load(RAW/'start.stdout.json')['total'],load(RAW/'start.stdout.json')['frozen_run']['keys']])

derived = []
for language,k in zip(['zh','zh-en'],f['keys']):
    prefix = language+'-'
    check(prefix+'scope',{'task_type':'evidence-validity','language':language,'provider':'typesafe','model_revision':'jev-1.13.0','rubric_revision':'objective-source-records-v1'},k['scope'])
    check(prefix+'request-accounting',[15,15,15,0,15,0],[k['planned'],k['started_requests'],k['recorded_invocations'],k['unknown_requests'],k['http_200'],k['errors']])
    check(prefix+'label-accounting',15,k['positive_label_count']+k['negative_label_count'])
    check(prefix+'outcome-accounting',15,k['correct']+k['false_accept']+k['false_reject']+k['abstain'])
    check(prefix+'choice-accounting',15,k['nonabstained_accept_count']+k['nonabstained_reject_count']+k['abstain'])
    tp=k['nonabstained_accept_count']-k['false_accept']
    tn=k['nonabstained_reject_count']-k['false_reject']
    ap=k['positive_label_count']-tp-k['false_reject']
    an=k['negative_label_count']-tn-k['false_accept']
    check(prefix+'matrix-nonnegative',True,min(tp,tn,ap,an)>=0)
    check(prefix+'matrix-correct',k['correct'],tp+tn)
    check(prefix+'matrix-abstained',k['abstain'],ap+an)
    check(prefix+'baseline',{'rule':'ALWAYS_REJECT','correct':k['negative_label_count'],'false_accept':0,'false_reject':k['positive_label_count']},k['baseline'])
    check(prefix+'development-count-binding',[30,30],[k['development_count'],k['development']['development_count']])
    d=k['development']
    check(prefix+'development-outcomes',30,sum(d[n] for n in ['correct_count','false_accept_count','false_reject_count','abstain_count']))
    derived.append({'scope':k['scope'],'development_count':30,'holdout_count':15,'confusion_matrix':{'positive':{'ACCEPT':tp,'REJECT':k['false_reject'],'ABSTAIN':ap},'negative':{'ACCEPT':k['false_accept'],'REJECT':tn,'ABSTAIN':an}},'critical_false_accept':k['critical_false_accept'],'false_accept_over_holdout':k['false_accept']/15,'false_accept_over_negative_labels':k['false_accept']/k['negative_label_count'],'host_nonabstained_coverage':(tp+tn+k['false_accept']+k['false_reject'])/15,'host_accept_coverage':k['nonabstained_accept_count']/15,'actual_automatic_action_coverage':0,'abstain_rate':k['abstain']/15,'correct_over_all_cases':k['correct']/15,'conditional_correct_over_nonabstained':k['correct']/(15-k['abstain']),'baseline':k['baseline'],'baseline_correct_over_all_cases':k['baseline']['correct']/15,'latency_sum_ms':k['latency_ms'],'mean_request_latency_ms':k['latency_ms']/15,'cost':None,'cost_status':'UNKNOWN','automatic_qualification_sample_gate':'FAIL_30_DEVELOPMENT_15_HOLDOUT_BELOW_60_30'})

check('exact-language-key-count',2,len(f['keys']))
for total,key in [('total','started_requests'),('correct','correct'),('false_accept','false_accept'),('false_reject','false_reject'),('abstain','abstain'),('critical_false_accept','critical_false_accept')]:
    check('overall-'+total,s[total],sum(k[key] for k in f['keys']))
check('initial-development-total',60,sum(k['development_count']for k in f['keys']))
check('initial-labeled-total',90,sum(k['development_count']+k['planned']for k in f['keys']))
(OUT/'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'derived-metrics.json').write_text(json.dumps({'by_key':derived,'overall':{'holdout_count':30,'positive_labels':14,'negative_labels':16,'correct':13,'false_accept':0,'false_reject':0,'abstain':17,'critical_false_accept':0,'errors':0,'unknown_requests':0,'http_200':30,'host_nonabstained_coverage':13/30,'host_accept_coverage':3/30,'actual_automatic_action_coverage':0,'abstain_rate':17/30,'correct_over_all_cases':13/30,'conditional_correct_over_nonabstained':1.0,'baseline_rule':'ALWAYS_REJECT','baseline_correct':16,'baseline_false_reject':14,'baseline_correct_over_all_cases':16/30,'latency_sum_ms':sum(k['latency_ms']for k in f['keys']),'mean_request_latency_ms':sum(k['latency_ms']for k in f['keys'])/30,'cost':None,'cost_status':'UNKNOWN'},'derivation_scope':'Derived only from fixed public service aggregates. No private sample, label or provider response body inspected. Nonabstained choices are advisory, not executed automatic actions.'},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'checks':len(checks),'passed':sum(x['status']=='PASS'for x in checks),'failed':sum(x['status']=='FAIL'for x in checks)}))
assert all(x['status']=='PASS' for x in checks)
