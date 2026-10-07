import pathlib,json,hashlib,subprocess,io,decimal,difflib,datetime
ROOT=pathlib.Path(__file__).resolve().parents[4]
OUT=pathlib.Path(__file__).resolve().parent
PACK=ROOT/'execution/receipts/W15'/OUT.name
checks=[];summaries=[]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def lines(p):return [json.loads(s) for s in p.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(ok,name):
 if not ok:raise AssertionError(name)
 checks.append(name)
def canonical(o):
 def inspect(v):
  if isinstance(v,float):raise ValueError('floats unsupported by audit canonicalizer')
  if isinstance(v,dict):
   for k,x in v.items():
    if any(ord(c)>65535 for c in k):raise ValueError('nonBMP key')
    inspect(x)
  if isinstance(v,list):
   for x in v:inspect(x)
 inspect(o)
 return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def digest(o):return 'sha256:'+hashlib.sha256(canonical(o)).hexdigest()
def hashed(p,want):check(sha(p)==want.removeprefix('sha256:'),'filehash:'+str(p))
def gitfiles(rev,items):
 items=list(items);result=subprocess.run(['git','cat-file','--batch'],input=''.join(rev+':'+p+'\n' for p,_ in items).encode(),cwd=ROOT,stdout=subprocess.PIPE,check=True);stream=io.BytesIO(result.stdout)
 for path,want in items:
  header=stream.readline().split();check(len(header)==3 and header[1]==b'blob','gitblob:'+path);body=stream.read(int(header[2]));check(stream.read(1)==b'\n','gitboundary:'+path);check(hashlib.sha256(body).hexdigest()==want.removeprefix('sha256:'),'githash:'+path)
def versionref(index,ref):
 o=index[(ref['entity_type'],ref['id'],ref['revision'])]
 if ref.get('content_hash'):check(ref['content_hash']==o.get('content_hash',o.get('receipt_hash')),'refhash:'+ref['id'])
 return o
receipt=load(PACK/'receipt.json');manifest=load(PACK/'artifacts.json');case=load(PACK/'A09.json');rev=receipt['code_revision']
check(rev=='5247bc7cabe9bf97cb08d05f376f17eb27008604','frozen-code-revision')
check(receipt['receipt_hash']==digest({k:v for k,v in receipt.items() if k!='receipt_hash'}),'executor-JCS')
check(receipt['receipt_hash']=='sha256:a5a49abc4b290c771a43b271bd813dbf3369adaf458a0c4248542b59d01a4b5f','parent-frozen-JCS')
hashed(PACK/'artifacts.json',receipt['artifact_manifest_hash']);check(len(manifest['files'])==89,'89-manifest-files')
for row in manifest['files']:hashed(ROOT/row['path'],row['sha256'])
source=case['version_manifest']['source_sha256'];check(set(source)==set(receipt['verified_source_paths']),'290-source-inventory');gitfiles(rev,source.items())
# Every prior review layer is immutable. Resolve older basename-relative and later root-relative indices.
prior=[]
for row in manifest['files']:
 if row['path'].startswith('execution/verifier/W15/') and row['path'].endswith('/evidence-index.json'):
  path=ROOT/row['path'];index=load(path)
  for entry in index['files']:
   candidate=ROOT/entry['path'];candidate=candidate if candidate.is_file() else path.parent/entry['path'];hashed(candidate,entry['sha256'])
  prior.append({'index':row['path'],'sha256':sha(path)})
check(len(prior)==4,'four-prior-review-layers')
expected_map=load(ROOT/'tests/skills/expected.json');expected=[a for rows in expected_map.values() for a in rows]
check(len(expected)==33 and len(set(expected))==33,'33-unique-assertions')
# Bind the inventory and frozen contracts to executed Git revision, not moving HEAD.
gitfiles(rev,[(p,sha(ROOT/p)) for p in ['tests/skills/expected.json','spec/v2.0/contracts/tasks.json','spec/v2.0/contracts/acceptance.json']])
contract=next(c for c in load(ROOT/'spec/v2.0/contracts/acceptance.json')['cases'] if c['id']=='A09')
task=next(t for t in load(ROOT/'spec/v2.0/contracts/tasks.json')['tasks'] if t['task_id']=='W15')
check(contract['mode']=='FIXTURE' and contract['final_owner_task']=='W15','frozen-A09-owner-mode')
check([a['assertion_id'] for a in case['assertion_results']]==[a['id'] for a in contract['assertions']],'four-frozen-A09-assertions')
for frozen,actual in zip(contract['assertions'],case['assertion_results']):
 check(frozen['expected']==actual['expected'] and actual['status']=='PASS' and actual['actual'],'frozen-assertion:'+frozen['id'])
 for entry in actual['raw_evidence']:hashed(ROOT/entry['path'],entry['sha256'])
for result in receipt['verification_results']:
 inv=load(ROOT/result['actual_invocation_reference']);check(inv['status']=='PASS' and inv['exit_code']==inv['child_exit_code']==0,'invocation-PASS')
 check(inv['code_revision']==rev and inv['command_key']=='test.skills','invocation-binding')
 check(inv['selectors'] in [{'task_id':'W15','check_id':'W15-G01','case_id':''},{'task_id':'W15','check_id':'','case_id':'A09'}],'exact-selector')
 for key in ['stdout','stderr']:hashed(ROOT/inv[key]['path'],inv[key]['sha256'])
 gitfiles(rev,[('execution/commands.json',inv['registered_command_revision'])])
 emitted=lines(ROOT/inv['stdout']['path'])[-1];child=pathlib.Path(emitted['receipt']).parent;report=load(child/'report.json');before=load(child/'before.json')
 check(emitted['assertion_ids']==inv['assertion_ids']==report['assertion_ids']==expected,'registered-inventory')
 check(report['status']=='PASS' and report['exit_code']==0 and report['environment_mode']=='FIXTURE' and before['git_head']==rev,'child-pass-binding')
 for p,h in report['raw_evidence_hashes'].items():hashed(child/p,h)
 gitfiles(rev,before['source_hashes'].items());hashed(pathlib.Path(before['go_tool']['path']),before['go_tool']['sha256'])
 events=lines(child/'stdout.jsonl');passed=[e['Test'] for e in events if e.get('Action')=='pass' and e.get('Test')]
 check(set(expected_map).issubset(passed) and not any(e.get('Action')=='fail' for e in events),'all-three-native-tests-passed')
 rawrows=[]
 for lineno,event in enumerate(events,1):
  output=event.get('Output','')
  if event.get('Test') in expected_map and output.startswith('W15_ASSERTION '):
   a=json.loads(output[len('W15_ASSERTION '):]);a['raw_evidence']={'path':'stdout.jsonl','line':lineno,'sha256':'sha256:'+sha(child/'stdout.jsonl')};rawrows.append(a)
 check(rawrows==report['assertions'],'raw-assertions-exact')
 check(all(a['status']=='PASS' and a['actual']==a['expected'] for a in rawrows),'nonzero-passed-assertions')
 document_summaries=[]
 for path in sorted(child.glob('*-documents.json')):
  document=load(path);check(document['scope']=='SYNTHETIC_PUBLIC_FIXTURE','document-fixture-scope')
  index={(r['kind'],r['object']['id'],r['object']['revision']):r['object'] for r in document['objects']};check(len(index)==len(document['objects']),'unique-object-versions')
  check(all(o['project_id']==document['project_id'] for o in index.values()),'project-scoped-document')
  contents=document['artifact_content'];decoded={}
  for id,c in contents.items():
   check('sha256:'+hashlib.sha256(c['utf8'].encode()).hexdigest()==c['content_hash'],'sealed-content:'+id)
   versions=[o for (kind,oid,v),o in index.items() if kind=='Artifact' and oid==id];check(bool(versions),'artifact-body-bound')
   for o in versions:check(o['content_hash']==c['content_hash'] and o['byte_size']==len(c['utf8'].encode()) and o['sealed_at'],'artifact-metadata-hash')
   try:decoded[id]=json.loads(c['utf8'])
   except ValueError:pass
  receipts={o['id']:o for (kind,id,v),o in index.items() if kind=='AcceptanceReceipt'}
  for ar in receipts.values():
   check(ar['receipt_hash']==digest({k:v for k,v in ar.items() if k!='receipt_hash'}),'domain-receipt-JCS')
   check(ar['verdict']=='PASS' and ar['measurement_mode']=='FIXTURE' and ar['verifier_principal_id'] not in ar['executor_principal_ids'],'independent-receipt-binding')
   for ref in ar['artifact_refs']:versionref(index,ref)
  skill_versions={}
  for (kind,id,version),skill in index.items():
   if kind!='SkillVersion':continue
   skill_versions.setdefault(id,[]).append(skill);a=versionref(index,skill['content_artifact_ref']);doc=decoded[a['id']]
   check(set(skill['expected_source_ids'])=={x['id'] for x in skill['source_refs']},'skill-source-manifest-complete')
   for ref in skill['source_refs']:versionref(index,ref)
   outcomes=doc['extraction'];check(len(outcomes)==len(skill['expected_source_ids']) and {x['source_id'] for x in outcomes}==set(skill['expected_source_ids']),'per-source-extraction')
   check({x['source_id'] for x in outcomes if x['processed']}==set(skill['processed_source_ids']) and {x['source_id'] for x in outcomes if not x['processed']}==set(skill['failed_source_ids']),'extraction-reconciliation')
   for claim in doc['claims']:versionref(index,claim['source_ref']);check(bool(claim['locator']),'claim-provenance-locator')
   if skill['status'] in ['QUALIFIED','ACTIVE','RETIRED','FROZEN']:
    ar=receipts[skill['acceptance_id']];check(ar['subject_ref']['entity_type']=='SkillVersion' and ar['subject_ref']['id']==id,'activation-acceptance-binding');check(not skill['failed_source_ids'] and not skill['allowed_capabilities'],'activated-complete-no-host-permission')
  coverage=[];diffs=[]
  for id,versions in skill_versions.items():
   versions.sort(key=lambda x:x['revision']);initial=versions[0];latest=versions[-1];doc=decoded[initial['content_artifact_ref']['id']]
   coverage.append({'skill_id':id,'source_manifest_hash':digest(initial['source_refs']),'expected':len(initial['expected_source_ids']),'processed':len(initial['processed_source_ids']),'failed':len(initial['failed_source_ids']),'reconciled_coverage':'PARTIAL' if initial['failed_source_ids'] else 'COMPLETE','statuses':[x['status'] for x in versions]})
   if initial['failed_source_ids']:check([x['status'] for x in versions]==['CANDIDATE'],'partial-never-activated')
   if initial['baseline_skill_id']:
    base=skill_versions[initial['baseline_skill_id']][0];old=decoded[base['content_artifact_ref']['id']]
    diffs.append({'baseline_skill_id':base['id'],'candidate_skill_id':id,'old_content_hash':base['content_artifact_ref']['content_hash'],'new_content_hash':initial['content_artifact_ref']['content_hash'],'diff':list(difflib.unified_diff(json.dumps(old,sort_keys=True,indent=2).splitlines(),json.dumps(doc,sort_keys=True,indent=2).splitlines(),fromfile='baseline',tofile='candidate',lineterm=''))})
  exps=[o for (kind,id,v),o in index.items() if kind=='Experiment' and o['status']=='COMPLETED']
  for exp in exps:
   payloads=[v for v in decoded.values() if isinstance(v,dict) and v.get('experiment_id')==exp['id'] and 'observations' in v];check(len(payloads)==1,'unique-paired-observation');payload=payloads[0]
   check(payload['preregistration_hash']==exp['preregistration_hash'] and payload['results']==exp['results'] and payload['outcome']==exp['outcome']=='IMPROVED','experiment-report-binding')
   for ob,resultrow in zip(payload['observations'],exp['results']):
    ids=ob['case_ids'];check(ids==['stable','improved','injection'] and len(ob['baseline'])==len(ob['candidate'])==3,'frozen-paired-cases')
    beforev=list(map(decimal.Decimal,ob['baseline']));afterv=list(map(decimal.Decimal,ob['candidate']));check(all(a>=b for a,b in zip(afterv,beforev)) and afterv[ids.index('injection')]==1,'no-regression-mandatory-injection')
    check(decimal.Decimal(resultrow['baseline'])==(sum(beforev)/3).quantize(decimal.Decimal('.00000001')) and decimal.Decimal(resultrow['candidate'])==sum(afterv)/3,'paired-means-recomputed')
   check(exp['acceptance_id'] in receipts and receipts[exp['acceptance_id']]['run_id'] in exp['run_ids'],'experiment-independent-task-receipt')
  if 'SourceConflictFormalResolution' in path.name:
   resolved=[o for (kind,id,v),o in index.items() if kind=='Conflict' and o['status']=='RESOLVED'];check(len(resolved)==1,'one-formally-resolved-conflict');c=resolved[0];proposal=next(o for (kind,id,v),o in index.items() if kind=='ChangeProposal' and id==c['resolution_proposal_id'] and o['status']=='APPLIED');check(proposal['acceptance_id'] in receipts,'resolution-independent-acceptance')
   active=[o for (kind,id,v),o in index.items() if kind=='SkillVersion' and o['status']=='ACTIVE'];check(len(active)==1,'one-resolved-active-version');skill=active[0];doc=decoded[skill['content_artifact_ref']['id']];check(c['id'] in skill['conflict_ids'],'resolved-ledger-included');entry=next(x for x in doc['conflicts'] if x['conflict_id']==c['id']);check(entry['resolution']=='CONDITIONAL' and bool(entry['conditions']),'resolved-applicability')
   selected=[]
   for edit in proposal['edits']:
    if edit['field']=='current_decision_refs':selected+=decoded[edit['proposed_value_artifact_ref']['id']]
   decisions=[versionref(index,x) for x in selected];check(any(d['rationale'] in entry['conditions'] and d['subject_ref']['id']==c['id'] for d in decisions),'conditions-match-adopted-decision')
  else:check(any(x['expected']==4 and x['processed']==3 and x['failed']==1 for x in coverage),'A09-partial-4-3-1-retained');check(bool(diffs),'candidate-diff-retained')
  summary={'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'object_versions':len(index),'sealed_bodies':len(contents),'receipt_hashes_recomputed':len(receipts),'completed_experiments_recomputed':len(exps),'coverage':coverage,'candidate_diffs':diffs};document_summaries.append(summary)
 summaries.append({'invocation_id':inv['invocation_id'],'selector':inv['selectors'],'assertions':33,'native_tests':passed,'documents':document_summaries})
# The A09 packaged assertion rows must be exact rows from its selected invocation.
case_run=next(x for x in summaries if x['selector']['case_id']=='A09');case_child=ROOT/pathlib.Path(case_run['documents'][0]['path']).parent;raw=load(case_child/'report.json')['assertions'];raw_by_id={a['assertion_id']:a for a in raw}
for group in case['assertion_results']:
 for row in group['actual']:
  check({k:v for k,v in row.items() if k!='invocation_reference'}==raw_by_id[row['assertion_id']],'A09-packaged-actual-row')
integration=load(PACK/'integration.json');events=lines(PACK/'integration.stdout.jsonl');passed=[e['Test'] for e in events if e.get('Action')=='pass' and e.get('Test')];check(passed==integration['tests_passed'] and integration['exit_code']==0 and not any(e.get('Action')=='fail' for e in events),'integration-raw-pass');check(len([x for x in passed if '/' not in x])==4 and len(passed)==7,'integration-top-level-count-correction')
report={'status':'PASS','task_id':'W15','run_id':OUT.name,'source_revision':rev,'executor_receipt_jcs_hash':receipt['receipt_hash'],'manifest_files':89,'source_files':len(source),'prior_review_layers':prior,'checks_passed':len(checks),'registered_runs':summaries,'integration_top_level_tests':4,'integration_subtests':3,'new_native_test_runs':0,'stage_accepted':False,'G01_passed':True,'A09_passed':True,'G02_passed':False}
(OUT/'audit-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(OUT/'audit-checks.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ['registered_runs','prior_review_layers']}))
