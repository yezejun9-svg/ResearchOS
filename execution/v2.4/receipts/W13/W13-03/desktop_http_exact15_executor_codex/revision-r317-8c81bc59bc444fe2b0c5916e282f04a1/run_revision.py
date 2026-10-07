import pathlib,json,hashlib,subprocess,sys,os,datetime,uuid,re
W=pathlib.Path.cwd();M=pathlib.Path('D:/作品集/ResearchOS/research-os');N=pathlib.Path(__file__).parent;C='7da1948601f74dfca08b3d91b30b2191';D=N/('cohort-'+C);O=W/'.local/desktop-wire'/C
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def load(p):return json.loads(p.read_bytes())
build=load(D/'build/result.json');assert build['status']=='BUILT_NOT_TESTED' and not build['drift']
roster=load(N/'finite-roster.frozen.json');source=load(D/'source-exact15.before.json');assert all(sha(W/x['path'])==x['sha256'] for x in source)
vectorpath=D/'full-finite-inputs.json'
if not vectorpath.exists():
 paths={pathlib.Path(x['path']) for x in load(D/'build/inputs.before.json')}
 compiler=load(D/'build/compiler-work-archive.json');paths.update(pathlib.Path(x['path']) for k in ['WORK','archives'] for x in compiler[k])
 paths.update([O/'validator.test.exe',pathlib.Path(build['descriptor']),pathlib.Path(__file__),N/'finite-roster.frozen.json'])
 for folder in [O/'apps/desktop',O/'apps/web/dist']:
  paths.update(p for p in folder.rglob('*') if p.is_file())
 save(vectorpath,[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths)])
frozen=load(vectorpath);assert all(sha(pathlib.Path(x['path']))==x['sha256'] for x in frozen)
phase=sys.argv[1];R=D/(phase+'-'+uuid.uuid4().hex);R.mkdir();rows=[]
env={k:v for k,v in os.environ.items() if k.upper() in ['SYSTEMROOT','WINDIR','COMSPEC','PATH','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE']}
env.update(RESEARCHOS_DESKTOP_WIRE_ROOT=str(O/'apps/desktop'),RESEARCHOS_DESKTOP_ELECTRON=str(M/'apps/desktop/node_modules/electron/dist/electron.exe'))
node='C:/nvm4w/nodejs/node.exe'
if phase=='units':leaves=[{'name':'pure-Go-exact3','argv':[str(O/'validator.test.exe'),'-test.run','^('+'|'.join(roster['go_units'])+')$','-test.v','-test.count=1','-test.failfast','-test.timeout=120s'],'http_request_cap':0,'pure_child_cap':0}]
elif phase=='supplement':leaves=roster['leaves'][:3]
elif phase=='original':leaves=roster['leaves'][3:]
elif phase=='regressions':leaves=roster['regressions']
else:raise ValueError('unknown phase')
save(R/'invocation.json',{'argv':sys.argv,'phase':phase,'selected':[x['name'] for x in leaves],'roster_sha256':sha(N/'finite-roster.frozen.json'),'full_vector_sha256':sha(vectorpath),'environment':{k:v for k,v in env.items() if k.startswith('RESEARCHOS_')},'new_source_cohort':C,'acceptance':False})
for index,leaf in enumerate(leaves):
 case=R/(str(index).zfill(3)+'-'+re.sub('[^a-zA-Z0-9._-]','_',leaf['name']));case.mkdir();env['RESEARCHOS_DESKTOP_CASE_RECEIPT']=str(case/'evidence')
 if phase=='units':argv=leaf['argv']
 elif phase=='regressions':argv=[node,*leaf['argv'][1:]]
 else:argv=[node,'--test','--test-reporter=tap','--test-name-pattern','^'+re.escape(leaf['name'])+'$','tests/ui/desktop/http-wire-boundary.test.mjs']
 started=datetime.datetime.now(datetime.timezone.utc).isoformat();timeout=False
 try:p=subprocess.run(argv,cwd=W,env=env,capture_output=True,timeout=150);code=p.returncode;out=p.stdout;err=p.stderr
 except subprocess.TimeoutExpired as e:code=None;timeout=True;out=e.stdout or b'';err=e.stderr or b''
 (case/'stdout.raw').write_bytes(out);(case/'stderr.raw').write_bytes(err)
 observations=[load(p) for p in (case/'evidence').rglob('observations.json')] if (case/'evidence').exists() else []
 http=sum(len(x.get('http',[])) for x in observations);children=sum(len(x.get('children',[])) for x in observations)
 if phase=='regressions':http+={'proxy never replays a write on 401; explicit retry preserves upload, safe GET renews, redirects fail':5,'SSE response is streamed with original event bytes':1}.get(leaf['name'],0)
 cap=leaf.get('http_request_cap',leaf.get('http_cap',0));ccap=leaf.get('pure_child_cap',64)
 text=out.decode('utf8',errors='replace');proof=True
 if phase=='units':proof=all('--- PASS: '+name+' (' in text for name in roster['go_units']) and '\nPASS\n' in text.replace('\r\n','\n') and '--- FAIL:' not in text and '--- SKIP:' not in text
 elif phase!='regressions':proof=bool(re.search(r'^# pass 1$',text,re.M)) and bool(re.search(r'^# fail 0$',text,re.M)) and bool(re.search(r'^# skipped 0$',text,re.M))
 row={'name':leaf['name'],'actualargv':argv,'cwd':str(W),'started_at':started,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_native_exit':code,'timed_out':timeout,'http_count':http,'child_count':children,'http_cap':cap,'child_cap':ccap,'actual_pass_predicate':proof,'status':'PASS' if code==0 and not timeout and proof and http<=cap and children<=ccap else 'FIRST_UNEXPECTED','raw_stdout_sha256':sha(case/'stdout.raw'),'raw_stderr_sha256':sha(case/'stderr.raw'),'relative_evidence':str(case.relative_to(W)),'external_MODEL_SDK_paid':0}
 save(case/'invocation.json',row);rows.append(row);print(json.dumps({k:row[k] for k in ['name','actual_native_exit','status','http_count','child_count']}),flush=True)
 if row['status']!='PASS':break
current=[{**x,'current_sha256':sha(pathlib.Path(x['path']))} for x in frozen];drift=[x for x in current if x['sha256']!=x['current_sha256']]
save(R/'inputs.after.json',current)
summary={'cohort':C,'phase':phase,'selected':len(leaves),'executed':len(rows),'rows':rows,'pass':sum(x['status']=='PASS' for x in rows),'not_run':len(leaves)-len(rows),'drift':drift,'full_input_count':len(frozen),'first_unexpected':next((x for x in rows if x['status']!='PASS'),None),'source_acceptance':False,'HTTP_phase_total':sum(x['http_count'] for x in rows)}
save(R/'result.json',summary);print(json.dumps({'result':str(R/'result.json'),'pass':summary['pass'],'not_run':summary['not_run'],'drift':len(drift),'native_wrapper_exit':0}),flush=True)
