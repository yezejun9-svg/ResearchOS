import collections,datetime,hashlib,json,pathlib,re,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[4]
OUT=pathlib.Path(__file__).resolve().parent
WT=ROOT/'.local/worktrees/jev-development-v2'
REV='ad3a628173f90933c3e1a5467b3e518a4c9775d6'
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
paths=['evaluation/development/jev-v2/dataset.go','evaluation/development/jev-v2/dataset.json','evaluation/development/jev-v2/manifest.json','evaluation/development/jev-v2/source_families.json','evaluation/development/jev-v2/cmd/main.go','tests/jev/live/main.go','evaluation/holdout/jev/rubric.go']
manifest={p:sha((WT/p).read_bytes()) for p in paths}
save(OUT/'before.json',dict(started_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT).decode().strip(),dirty=subprocess.check_output(['git','status','--porcelain'],cwd=WT).decode(),source_manifest=manifest,provider_calls=0,holdout_generated=False,scope='PUBLIC_DEVELOPMENT_BEFORE_LIVE'))
before=load(OUT/'before.json');assert before['source_revision']==REV and not before['dirty']
data=load(WT/paths[1]);frozen=load(WT/paths[2]);families=load(WT/paths[3]);checks=[];rows=[]
def check(id,want,got):checks.append(dict(id=id,expected=want,actual=got,status='PASS' if want==got else 'FAIL'))
check('DATASET-FROZEN-HASH','sha256:c4408fcca39320561ed03de0b56c2a9b8400dadf4eccd1b99802599e685ee979',manifest[paths[1]])
check('MANIFEST-DATASET',manifest[paths[1]],frozen['dataset_sha256']);check('FAMILY-DATASET',manifest[paths[1]],families['dataset_sha256'])
check('RUBRIC-CANONICAL-HASH',frozen['rubric_sha256'],sha(canonical(data['rubric'])))
public_source=subprocess.check_output(['git','show','2ef06ef:evaluation/holdout/jev/rubric.go'],cwd=ROOT)
check('SHARED-PUBLIC-RUBRIC-SOURCE',sha(public_source),manifest['evaluation/holdout/jev/rubric.go'])
check('NEW-RUBRIC-REVISION','objective-source-records-v1',data['rubric']['revision'])
check('FROZEN-THRESHOLD',0.8,data['rubric']['confidence_threshold'])
check('PUBLIC-SPLIT',['DEVELOPMENT_ONLY','PROJECT','NONE',0],[data['split'],data['access_class'],data['qualification_authority'],data['holdout_count']])
check('EXPECTED-COUNT',60,len(data['cases']))
known=['dev-v2-shipment-manifests','dev-v2-invoice-balances','dev-v2-warehouse-inventory','dev-v2-staff-attendance','dev-v2-repository-releases','dev-v2-dispatch-windows']
check('SOURCE-FAMILY-DECLARATION',[1,0,known],[families['source_family_count'],families['independent_empirical_source_count'],families['subfamilies']])
check('FAMILY-MAP-EXACT',sorted(c['id'] for c in data['cases']),sorted(families['cases']))
def dt(x):return datetime.datetime.fromisoformat(x.replace('Z','+00:00')).astimezone(datetime.timezone.utc)
text_pattern=re.compile(r'^(.*?) / record ([^;]+); 原始记录=\[([0-9 -]*)\]; observed_at=([^;]+); revision=(.+)$')
counter=collections.Counter();reasons=collections.Counter();pairs=collections.defaultdict(list)
for c in data['cases']:
 cid=c['id'];s=c['state'];rules=s['task_rules'];scope=c['scope'];failure=[];docs={};record_values={}
 expected_scope={'task_type':'evidence-validity','language':'zh-en' if cid.startswith('dev-zh-en-') else 'zh','provider':'typesafe','model_revision':'jev-1.13.0','rubric_revision':'objective-source-records-v1'}
 check(cid+':SCOPE',expected_scope,scope)
 ordinal=int(cid.rsplit('-',1)[1]);fam=known[(ordinal-1)//5]
 metadata=families['cases'][cid]
 check(cid+':FAMILY',{'source_family':'dev-v2-ledger-documents','subfamily':fam,'paraphrase_group':f'public-pair-{ordinal:02d}'},metadata)
 pairs[metadata['paraphrase_group']].append(c)
 if len(s['source_documents'])!=2:failure.append('missing_original_document')
 if len(s['citations'])!=2:failure.append('citation_count')
 for doc in s['source_documents']:
  if doc['id'] in docs:failure.append('duplicate_document')
  docs[doc['id']]=doc
  match=text_pattern.fullmatch(doc['text'])
  check(cid+':TEXT-PARSE:'+doc['id'],True,match is not None)
  if match:
   kind,identity,values,timestamp,revision=match.groups();values=[int(v) for v in values.split()]
   check(cid+':TEXT-FIELDS:'+doc['id'],[doc['kind'],doc['id'],doc['records'],doc['observed_at'],doc['revision']],[kind,identity,values,timestamp,revision])
   record_values[identity]=values
  if not rules['window_start_inclusive'] or not rules['window_end_inclusive']:failure.append('missing_window')
  if not dt(rules['window_start_inclusive'])<=dt(doc['observed_at'])<=dt(rules['window_end_inclusive']):failure.append('utc_outside_inclusive_window')
  if doc['revision']!=rules['required_revision']:failure.append('document_revision_conflict')
 if s['claim']['revision']!=rules['required_revision']:failure.append('claim_revision_conflict')
 for index,identity in enumerate(rules['required_source_ids']):
  if identity not in docs:failure.append('required_source_absent');continue
  cite=s['citations'][index] if index<len(s['citations']) else {}
  if cite.get('document_id')!=identity:failure.append('citation_points_to_wrong_or_absent_document')
  if not cite.get('quote') or cite.get('quote')!=docs[identity]['text']:failure.append('quote_not_exact_original')
 total=None
 if all(i in record_values for i in rules['required_source_ids']):
  groups=[record_values[i] for i in rules['required_source_ids']]
  if rules['operation']=='SUM':total=sum(map(sum,groups))
  elif rules['operation']=='BALANCE':total=sum(groups[0])-sum(groups[1])
  elif rules['operation']=='COUNT':total=sum(map(len,groups))
  else:failure.append('unsupported_operation')
  if total!=s['claim']['total']:failure.append('recomputed_number_mismatch')
 expected='REJECT' if failure else 'ACCEPT'
 check(cid+':INDEPENDENT-LABEL',[expected,expected=='REJECT'],[c['expected'],c['critical']])
 check(cid+':REQUEST-NO-LABEL-FIELDS',False,any(k in json.dumps(s) for k in ['"expected"','"critical"','"source_family"','"paraphrase_group"']))
 counter[scope['language']+':'+expected]+=1;reasons.update(set(failure))
 rows.append(dict(id=cid,scope=scope,recomputed_label=expected,recomputed_total=total,claimed_total=s['claim']['total'],failure_reasons=sorted(set(failure)),input_hash=sha(canonical(s)),source_family=metadata['source_family'],subfamily=fam))
check('LANGUAGE-LABEL-INVENTORY',{'zh:ACCEPT':15,'zh:REJECT':15,'zh-en:ACCEPT':15,'zh-en:REJECT':15},dict(counter))
check('PARAPHRASE-GROUP-COUNT',30,len(pairs))
for group,cases in pairs.items():
 check(group+':PAIR-COUNT',2,len(cases))
 check(group+':PAIRED-ORIGINAL-EVIDENCE',cases[0]['state']['source_documents'],cases[1]['state']['source_documents'])
 check(group+':PAIRED-CLAIM',cases[0]['state']['claim'],cases[1]['state']['claim'])
for p,h in manifest.items():check('SOURCE-NO-DRIFT:'+p,h,sha((WT/p).read_bytes()))
for p in paths:
 target=OUT/'source-snapshot'/(p+'.txt');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((WT/p).read_bytes())
save(OUT/'independent-checks.json',dict(checks=checks,case_recomputation=rows,failure_distribution=dict(reasons),passed=sum(x['status']=='PASS' for x in checks),failed=sum(x['status']=='FAIL' for x in checks)))
assert all(c['status']=='PASS' for c in checks)
print(json.dumps(dict(checks=len(checks),passed=len(checks),cases=len(rows),inventory=dict(counter),failure_distribution=dict(reasons),rubric_sha256=sha(canonical(data['rubric'])))))
