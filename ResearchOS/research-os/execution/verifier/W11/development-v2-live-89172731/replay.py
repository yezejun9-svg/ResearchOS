"""Independent offline verification. No network or credential-reading code."""
import base64,collections,datetime,hashlib,json,math,pathlib,statistics,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[4]
OUT=pathlib.Path(__file__).resolve().parent
RUN=ROOT/'execution/receipts/W11/development-v2-live/89172731-25df-42c1-ba8d-1608584c44a6'
DATA=ROOT/'evaluation/development/jev-v2/dataset.json'
FAMILIES=DATA.with_name('source_families.json')
GO=ROOT/'.local/tools/go1.27.1/go/bin/go.exe'
REBUILD=ROOT/'.local/worktrees/dev-v2-binary-repro-6b4f935'
def sha(raw):return 'sha256:'+hashlib.sha256(raw).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def strict(raw):
 def pairs(kvs):
  result={}
  for k,v in kvs:
   if k in result:raise ValueError('duplicate JSON key')
   result[k]=v
  return result
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def load(p):return strict(p.read_bytes())
def save(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]
def check(id,want,got):
 checks.append(dict(id=id,expected=want,actual=got,status='PASS' if want==got else 'FAIL'))
 if want!=got:raise AssertionError((id,want,got))
files=[DATA,FAMILIES]+sorted(p for p in RUN.iterdir() if p.is_file())
failures=[]
for name in ['cdd7a759-c8e5-4baf-b6ee-c159ceb297e1','d154d079-65d0-4143-ac8d-d562ddf937e2']:
 folder=RUN.parent/name
 files+=sorted(p for p in folder.iterdir() if p.is_file())
 failures.append({'run_id':name,'attributed_provider_calls':0,'raw_case_count':len(list(folder.glob('*.raw.json'))),'before_exists':(folder/'before.json').exists(),'status':'PRE_CALL_LAUNCH_FAILURE'})
source_before={str(p.relative_to(ROOT)).replace('\\','/'):sha(p.read_bytes()) for p in files}
data,before,report,launcher,families=load(DATA),load(RUN/'before.json'),load(RUN/'report.json'),load(RUN/'launcher.json'),load(FAMILIES)
check('launcher-success',0,launcher['exit_code'])
check('dataset-frozen','sha256:c4408fcca39320561ed03de0b56c2a9b8400dadf4eccd1b99802599e685ee979',sha(DATA.read_bytes()))
rubric_hash=sha(canonical(data['rubric']))
check('new-rubric-frozen','sha256:e15d497fa2bb011b33c5a5049e5a7300570fab8b9ebdaf97b2125b671a872dfd',rubric_hash)
for name,record in [('before',before),('report',report)]:
 check(name+'-dataset-hash',sha(DATA.read_bytes()),record['dataset_sha256']);check(name+'-rubric-hash',rubric_hash,record['rubric_sha256']);check(name+'-families-hash',sha(FAMILIES.read_bytes()),record['development_families_sha256'])
 check(name+'-calls-and-holdout',[60,0,'LIVE_SERVICE'],[record['provider_calls_this_run'],record['holdout_count'],record['environment_mode']])
check('source-revision-agrees',before['source_revision'],report['source_revision'])
check('threshold',0.8,data['rubric']['confidence_threshold'])
check('dataset-public',['DEVELOPMENT_ONLY','PROJECT','NONE',0],[data['split'],data['access_class'],data['qualification_authority'],data['holdout_count']])
check('family-limits',[1,0],[families['source_family_count'],families['independent_empirical_source_count']])
binary=pathlib.Path(before['argv_without_credentials'][0]);rebuilt=ROOT/'.local/dev-v2-verifier/rebuilt-6b4f935.exe'
binary_hash=sha(binary.read_bytes())
check('binary-pinned','sha256:e18a745e251281104bd45d8577711c6461a4af1f075c527bd6588a6166e695d3',binary_hash)
check('binary-before-binding',binary_hash,before['executable_sha256']);check('binary-launcher-binding',binary_hash,'sha256:'+launcher['binary_sha256'])
check('byte-identical-independent-source-rebuild',binary_hash,sha(rebuilt.read_bytes()))
info=subprocess.check_output([str(GO),'version','-m',str(binary)],cwd=ROOT).decode()
(OUT/'binary-build-info.txt').write_text(info,encoding='utf-8')
check('binary-frozen-vcs',True,'vcs.revision=6b4f9352ea984094dbe59269c39c0a51c6f81a61' in info and 'vcs.modified=true' in info)
check('rebuild-only-known-dirty-marker',['?? verifier-build-dirty-marker.txt'],(OUT/'rebuild-dirty-status.txt').read_text(encoding='utf-8-sig').splitlines())
# Capture actual imported local Go files from the same frozen rebuild checkout.
listing=subprocess.check_output([str(GO),'list','-deps','-json','./tests/jev/live'],cwd=REBUILD).decode();decoder=json.JSONDecoder();offset=0;source_manifest={}
while offset<len(listing):
 while offset<len(listing) and listing[offset].isspace():offset+=1
 if offset==len(listing):break
 obj,end=decoder.raw_decode(listing,offset);offset=end
 if obj.get('Module',{}).get('Path')=='researchos.local/research-os':
  for name in obj.get('GoFiles',[])+obj.get('CgoFiles',[]):
   p=pathlib.Path(obj['Dir'])/name;relative=p.relative_to(REBUILD).as_posix();raw=p.read_bytes();source_manifest[relative]=sha(raw)
   check('rebuild-source:'+relative,sha(subprocess.check_output(['git','show','6b4f935:'+relative],cwd=ROOT)),sha(raw))
   dest=OUT/'source-snapshot'/(relative+'.txt');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
for p in ['go.mod','go.sum']:
 source_manifest[p]=sha((REBUILD/p).read_bytes())
ids=[c['id'] for c in data['cases']]
check('unique-case-inventory',[60,60],[len(ids),len(set(ids))])
check('exact-60-original-raw',sorted(ids),sorted(p.name[:-9] for p in RUN.glob('*.raw.json')))
check('reported-case-inventory',sorted(ids),sorted(c['id'] for c in report['cases']))
check('partial-is-complete',report['cases'],load(RUN/'results.partial.json'))
old_rows={c['id']:c for c in report['cases']};rows=[]
def utc(x):return datetime.datetime.fromisoformat(x.replace('Z','+00:00')).astimezone(datetime.timezone.utc)
def objective(s):
 rules=s['task_rules'];docs={d['id']:d for d in s['source_documents']};valid=len(docs)==len(s['source_documents'])==2 and len(s['citations'])==2 and s['claim']['revision']==rules['required_revision'];groups=[]
 for i,key in enumerate(rules['required_source_ids']):
  d=docs.get(key)
  if not d:valid=False;continue
  original=d['text'];record_text=original.split('原始记录=[',1)[1].split(']',1)[0];values=[int(x) for x in record_text.split()]
  valid=valid and values==d['records'] and d['revision']==rules['required_revision'] and utc(rules['window_start_inclusive'])<=utc(d['observed_at'])<=utc(rules['window_end_inclusive'])
  cite=s['citations'][i];valid=valid and cite['document_id']==key and cite['quote']==original
  groups.append(values)
 if len(groups)==2:
  total={'SUM':lambda:sum(map(sum,groups)),'BALANCE':lambda:sum(groups[0])-sum(groups[1]),'COUNT':lambda:sum(map(len,groups))}[rules['operation']]();valid=valid and total==s['claim']['total']
 return 'ACCEPT' if valid else 'REJECT'
for case in data['cases']:
 cid=case['id'];path=RUN/(cid+'.raw.json');env=load(path);raw=base64.b64decode(env['response'],validate=True);answer=strict(raw);truth=objective(case['state'])
 check(cid+'/independent-original-label',[truth,truth=='REJECT'],[case['expected'],case['critical']])
 request={'model':case['scope']['model_revision'],'state':case['state'],'questions':data['rubric']['questions']}
 binding={'project_id':'W11-development','input_hash':sha(canonical(case['state'])),'rubric_hash':rubric_hash,'scope':case['scope']}
 check(cid+'/exact-request',request,env['request']);check(cid+'/exact-binding',binding,env['binding']);check(cid+'/request-hash',sha(canonical(request)),env['request_hash']);check(cid+'/response-hash',sha(raw),env['response_hash'])
 check(cid+'/actual-live-status',[1,'LIVE',True,200,''],[env['version'],env['measurement_mode'],env['jev_called'],env['http_status'],env['transport_error']])
 check(cid+'/response-fields',['answers','model','usage'],sorted(answer));check(cid+'/model',case['scope']['model_revision'],answer['model']);check(cid+'/question',['action'],sorted(answer['answers']))
 a=answer['answers']['action'];check(cid+'/choice-fields',['choice','confidence','probabilities','type'],sorted(a));check(cid+'/typed-choice','choice',a['type']);check(cid+'/options',['ACCEPT','REJECT'],sorted(a['probabilities']))
 values=[a['confidence'],*a['probabilities'].values()]
 check(cid+'/finite-probabilities',True,all(type(v) in [int,float] and math.isfinite(v) and 0<=v<=1 for v in values));check(cid+'/probability-sum',True,abs(sum(a['probabilities'].values())-1)<=1e-5)
 check(cid+'/selected-known',True,a['choice'] in a['probabilities']);check(cid+'/choice-argmax',True,max(a['probabilities'].values())<=a['probabilities'][a['choice']]+1e-5)
 check(cid+'/usage-fields',['input_tokens','output_tokens'],sorted(answer['usage']));check(cid+'/usage-values',True,all(type(x)==int and x>=0 for x in answer['usage'].values()))
 abstain=a['confidence']<0.8;reasons=['action:LOW_CONFIDENCE'] if abstain else []
 check(cid+'/reported-outcome',[a['choice'],abstain,reasons,env['response_hash'],env['latency_ms'],True,truth,case['critical']],[old_rows[cid][k] for k in ['selected','abstained','reasons','response_sha256','latency_ms','jev_called','expected','critical']])
 check(cid+'/latency-valid',True,type(env['latency_ms'])==int and env['latency_ms']>=0)
 rows.append(dict(id=cid,scope=case['scope'],expected=truth,critical=case['critical'],selected=a['choice'],confidence=a['confidence'],selected_option_probability=a['probabilities'][a['choice']],probabilities=a['probabilities'],abstained=abstain,reasons=reasons,correct=not abstain and a['choice']==truth,false_accept=not abstain and a['choice']=='ACCEPT' and truth=='REJECT',false_reject=not abstain and a['choice']=='REJECT' and truth=='ACCEPT',raw_choice_correct=a['choice']==truth,latency_ms=env['latency_ms'],usage=answer['usage'],raw_file_sha256=sha(path.read_bytes()),response_sha256=env['response_hash']))
def metrics(items):
 n=len(items);positive=sum(x['expected']=='ACCEPT' for x in items);negative=n-positive;correct=sum(x['correct'] for x in items);fa=sum(x['false_accept'] for x in items);fr=sum(x['false_reject'] for x in items);abstain=sum(x['abstained'] for x in items);latencies=sorted(x['latency_ms'] for x in items)
 return dict(case_count=n,positive_label_count=positive,negative_label_count=negative,correct_count=correct,false_accept_count=fa,critical_false_accept_count=sum(x['false_accept'] and x['critical'] for x in items),false_reject_count=fr,abstain_count=abstain,provider_error_count=0,missing_count=0,typed_response_count=n,false_accept_rate_over_all_cases=fa/n,false_accept_rate_over_negative_cases=fa/negative,false_reject_rate_over_positive_cases=fr/positive,abstain_rate=abstain/n,nonabstained_count=n-abstain,host_nonabstained_coverage=(n-abstain)/n,automatic_action_coverage=0,correct_rate_over_all_cases=correct/n,conditional_correct_rate_over_nonabstained=correct/(n-abstain) if n>abstain else None,raw_choice_correct_count_before_threshold=sum(x['raw_choice_correct'] for x in items),latency_ms=dict(median=statistics.median(latencies),mean=statistics.mean(latencies),p95_nearest_rank=latencies[math.ceil(n*.95)-1],maximum=max(latencies)),input_tokens=sum(x['usage']['input_tokens'] for x in items),output_tokens=sum(x['usage']['output_tokens'] for x in items),cost=None,cost_status='UNKNOWN_NOT_BILLING_EVIDENCE',development_count=n,holdout_count=0,qualification='BLOCKED_INDEPENDENT_HOLDOUT_NOT_INCLUDED',maximum_mode='ADVISORY',automatic_authority='NONE')
overall=metrics(rows);by_key=[]
def decision_counts(items):
 return dict(raw_choice_counts=dict(collections.Counter(x['selected'] for x in items)),nonabstained_accept_count=sum(not x['abstained'] and x['selected']=='ACCEPT' for x in items),nonabstained_reject_count=sum(not x['abstained'] and x['selected']=='REJECT' for x in items),abstained_positive_count=sum(x['abstained'] and x['expected']=='ACCEPT' for x in items),abstained_negative_count=sum(x['abstained'] and x['expected']=='REJECT' for x in items))
overall.update(decision_counts(rows))
for language in ['zh','zh-en']:
 group=[x for x in rows if x['scope']['language']==language];m=metrics(group);m.update(decision_counts(group));by_key.append(dict(qualification_key=group[0]['scope'],metrics=m))
for field in ['correct_count','false_accept_count','critical_false_accept_count','false_reject_count','abstain_count','input_tokens','output_tokens','false_accept_rate_over_all_cases','false_accept_rate_over_negative_cases','false_reject_rate_over_positive_cases','abstain_rate']:
 check('aggregate:'+field,overall[field],report[field])
check('actual-successful-responses',60,report['successful_typed_response_count'])
for f in failures:check('failed-launch-no-before-or-raw:'+f['run_id'],[False,0],[f['before_exists'],f['raw_case_count']])
correction=load(RUN.parent/'cdd7a759-c8e5-4baf-b6ee-c159ceb297e1/correction.json')
check('first-failure-limit-preserved','NOT_RECOVERABLE',correction['raw_stderr_for_first_run'])
check('first-failure-cause-corrected','DIGEST_PREFIX_MISSING',correction['corrected_cause'])
check('all-input-bytes-preserved',source_before,{str(p.relative_to(ROOT)).replace('\\','/'):sha(p.read_bytes()) for p in files})
save(OUT/'checks.json',checks);save(OUT/'rows.json',rows);save(OUT/'input-hashes.json',source_before);save(OUT/'source-manifest.json',source_manifest)
save(OUT/'metrics.json',dict(overall=overall,by_qualification_key=by_key,confidence_is_selected_probability_mismatch_count=sum(abs(x['confidence']-x['selected_option_probability'])>1e-5 for x in rows),new_provider_calls=0,formal_holdout_count=0,prior_failed_launches=failures,first_failure_limit=correction,deterministic_baseline=dict(basis='Independent Python recomputation of the exact closed-world source-record rules',case_count=60,correct_count=60,false_accept_count=0,false_reject_count=0,abstain_count=0,not_general_research_accuracy=True),brier_ece=dict(status='NOT_REQUIRED_BY_FROZEN_A08_CONTRACT',note='Neither Typesafe confidence nor selected probability is assumed to be a calibrated real-world success probability.')))
print(json.dumps(dict(checks=len(checks),overall=overall,by_qualification_key=by_key),ensure_ascii=False))
