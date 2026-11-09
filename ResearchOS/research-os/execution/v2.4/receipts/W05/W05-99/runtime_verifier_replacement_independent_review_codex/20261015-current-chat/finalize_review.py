import pathlib, json, hashlib, datetime
E=pathlib.Path(__file__).resolve().parent
R=E.parents[7]
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
 with (E/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
summaries=[]
for label in ['01-focused','02-original-probes','05-affected-regression','06-extra-probes']:
 rows=[json.loads(x) for x in (E/(label+'.log')).read_text(encoding='utf-8').splitlines()]
 tests={a:[r['Test'] for r in rows if r.get('Test') and r.get('Action')==a] for a in ['pass','skip','fail']}
 meta=json.loads((E/(label+'.json')).read_text(encoding='utf-8'))
 assert meta['exit_code']==0 and tests['pass'] and not tests['fail']
 summaries.append({'label':label,'counts':{k:len(v) for k,v in tests.items()},'top_level_pass':sum('/' not in s for s in tests['pass']),'tests':tests,'log':pin(E/(label+'.log'))})
save('test-summary.json',summaries)
before=json.loads((E/'inputs.before.json').read_text(encoding='utf-8'))
after=json.loads((E/'inputs.after.json').read_text(encoding='utf-8'))
assert before==after
save('FINAL-report.json',{'verdict':'LIMITED_SOURCE_ACCEPTED','source_commit':'4f4023c956f84d65743f39ce77d6c8899a21ada1','source_tree':'3db13a15cc52b2b0bd75cae3452c66509a9f55c9','resolved_findings':['F1','F2'],'blocking_findings':[],'source_and_historical_evidence_guard_files':len(before),'guards_unchanged':True,'formal_increment':0,'formal_accepted':0,'formal_total':42,'parents_open':22,'product_execution':False,'independent_reviewer':'codex:/root/verifier_revision_review','model':'gpt-6-astra','reasoning_effort':'high','reviewer_failed_attempts':0,'historical_failures_preserved':True})
save('FINAL-manifest.json',{'schema':'researchos.runtime-verifier-replacement-revision-review/1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'LIMITED_SOURCE_ACCEPTED','source_commit':'4f4023c956f84d65743f39ce77d6c8899a21ada1','source_tree':'3db13a15cc52b2b0bd75cae3452c66509a9f55c9','evidence':[pin(p) for p in sorted(E.iterdir()) if p.is_file()],'formal_increment':0})
print(json.dumps({'review':pin(E/'REVIEW.md'),'manifest':pin(E/'FINAL-manifest.json'),'report':pin(E/'FINAL-report.json')},ensure_ascii=False,indent=2))
