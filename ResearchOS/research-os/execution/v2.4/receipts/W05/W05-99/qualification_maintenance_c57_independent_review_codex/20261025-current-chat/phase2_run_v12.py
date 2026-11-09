import pathlib,json,hashlib,subprocess,os,sys,time
B=pathlib.Path(__file__).parent
jobpath=pathlib.Path(sys.argv[1]);job=json.loads(jobpath.read_text(encoding='utf-8'))
D=B/job['tag'];D.mkdir(exist_ok=False)
v=json.loads((B/'PHASE2-v12-snapshot-verification.json').read_text(encoding='utf-8'))
S=pathlib.Path(v['snapshot']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for ref in v['candidate_source_files']+v['inherited40']:
 assert sha(S/ref['path'])==ref['sha256'],ref['path']
supp=[]
for ref in job.get('supplementary_files',[]):
 assert sha(S/ref['path'])==ref['sha256'],ref['path'];supp.append(ref)
env=os.environ.copy();env.update(job['env'])
for k in ['TEMP','TMP','GOTMPDIR','GOCACHE','GOMODCACHE','GOPATH']:
 pathlib.Path(env[k]).mkdir(parents=True,exist_ok=True)
env['PATH']=str(pathlib.Path(job['argv'][0]).parent)+os.pathsep+env['PATH']
recipe={'phase':'PHASE2_INDEPENDENT_EXACT_SNAPSHOT','job_sha256':sha(jobpath),'snapshot_verification_sha256':sha(B/'PHASE2-v12-snapshot-verification.json'),'source_commit':v['commit'],'source_tree':v['tree'],'cwd':str(S),'argv':job['argv'],'env':job['env'],'tool_sha256':sha(pathlib.Path(job['argv'][0])),'supplementary_files':supp,'class':job['class']}
(D/'recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2),encoding='utf-8')
start=time.time()
with (D/'stdout.raw').open('xb') as out,(D/'stderr.raw').open('xb') as err:
 p=subprocess.run(job['argv'],cwd=S,env=env,stdout=out,stderr=err)
counts={};events=[];skips=[];fails=[];packages=[]
for line in (D/'stdout.raw').read_text(encoding='utf-8',errors='replace').splitlines():
 try:e=json.loads(line)
 except ValueError:continue
 if e.get('Action') in ['pass','fail','skip'] and 'Test' in e:
  counts[e['Action']]=counts.get(e['Action'],0)+1
  events.append({k:e[k] for k in ['Action','Package','Test','Elapsed'] if k in e})
 if e.get('Action')=='skip':skips.append(e)
 if e.get('Action')=='fail':fails.append(e)
 if e.get('Action') in ['pass','fail'] and 'Test' not in e:packages.append(e)
source_after=[ref['path'] for ref in v['candidate_source_files']+v['inherited40'] if sha(S/ref['path'])!=ref['sha256']]
result={'native_exit':p.returncode,'elapsed_seconds':time.time()-start,'stdout_sha256':sha(D/'stdout.raw'),'stderr_sha256':sha(D/'stderr.raw'),'test_event_counts':counts,'package_results':packages,'skip_events':skips,'fail_events':fails,'candidate_source_drift':source_after}
(D/'test-events.json').write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding='utf-8')
(D/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
sys.exit(p.returncode)
