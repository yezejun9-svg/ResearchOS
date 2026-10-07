import pathlib,json,hashlib,subprocess,sys,datetime
W=pathlib.Path.cwd();M=pathlib.Path('D:/作品集/ResearchOS/research-os');N=pathlib.Path(__file__).parent
COHORT='7da1948601f74dfca08b3d91b30b2191';D=N/('cohort-'+COHORT);D.mkdir()
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def run(name,argv):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run(argv,cwd=W,capture_output=True)
 (D/(name+'.stdout')).write_bytes(p.stdout);(D/(name+'.stderr')).write_bytes(p.stderr)
 save(D/(name+'.invocation.json'),{'actualargv':argv,'cwd':str(W),'started_at':start,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_native_exit':p.returncode})
 if p.returncode:raise SystemExit(p.returncode)
 return p.stdout
scope_path=M/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop-targeted-revision-r317/scope_registration.json';scope=json.loads(scope_path.read_bytes());assert sha(scope_path.read_bytes())=='a01d6bcb8e505b8ca20c73d51bee68e8af3f44a2a1dd31f58b5eaf4abdb1306b'
refs=[]
for key,value in scope.items():
 if isinstance(value,dict) and 'path' in value and 'sha256' in value:
  p=M/value['path'];assert sha(p.read_bytes())==value['sha256'];refs.append(value)
save(N/'scope-refs.json',refs)
assert run('head',['git','rev-parse','HEAD']).decode().strip()==scope['evidence_head_before_revision']
paths=run('source-diff-paths',['git','diff','--name-only']).decode().splitlines();assert set(paths)<=set(scope['revision_allowed_paths'])
old=[]
for path,expected in scope['all_original15_source_before'].items():
 b=run('base-'+str(len(old)),['git','show',scope['source_only_base']+':'+path]);assert sha(b)==expected['sha256'];old.append({'path':path,'sha256':sha(b),'bytes':len(b)})
save(N/'source-exact15.base.json',old)
run('gofmt',[str(M/'.local/tools/go1.27.1/go/bin/gofmt.exe'),'-w',str(W/'apps/desktop/validator/main.go'),str(W/'apps/desktop/validator/main_test.go')])
source=[{'path':p,'sha256':sha((W/p).read_bytes()),'bytes':(W/p).stat().st_size} for p in scope['all_original15_source_before']];save(D/'source-exact15.before.json',source)
(D/'source-snapshots').mkdir()
for i,row in enumerate(source):(D/'source-snapshots'/('%02d.raw'%i)).write_bytes((W/row['path']).read_bytes())
protected=json.loads((M/scope['protected_17_spans_ref']['path']).read_bytes());checked=[]
for index,row in enumerate(protected['rows']):
 e=row['expected'];base=run('protected-base-'+str(index),['git','show','2cdb0d43d5a600eef13c8f1735946a9adf52d079:'+e['path']]);span=b''.join(base.splitlines(keepends=True)[e['first_line']-1:e['last_line']]);assert sha(span)==e['sha256'];assert span in (W/e['path']).read_bytes();checked.append({**e,'preserved':True})
save(D/'protected17.json',checked)
original_roster=json.loads((M/scope['tests']['original_roster_ref']['path']).read_bytes())
extra=[{'name':x['suggested_selector'],'http_request_cap':x['expected_caps']['loopback_http_max'],'pure_child_cap':x['expected_caps']['pure_validator_children_max']} for x in scope['tests']['three_new_supplemental_controls']['cases']]
save(N/'finite-roster.frozen.json',{'original':scope['tests']['original_roster_ref'],'leaves':extra+original_roster['leaves'],'regressions':original_roster['regressions'],'go_units':['TestWireParserPreservesAdjacentIntegers','TestWireParserRejectsAmbiguousJSONAndWorkExhaustion','TestWirePrivatePacketExactKeysAndTypes'],'http_phase_maximum':390,'prior_HTTP_preserved':302,'external_SDK_MODEL_paid':0})
save(N/'tool-diagnostics.initial.json',{'apply_patch_verification_failed':{'message':'Failed to find expected lines in ipc.js: if ((!pending || replay) && snapshot && snapshot.project_id===','actual_native_exit':None,'tool_status':'Script failed; verification did not apply patch','later_corrected_input':True},'native_failures_so_far':0,'read_tools_outer0':['e8c3d6','4e24a3','0c0f9e','7cfc0e','4fb6bc','234e0e','194693','72bce7','0c6b1f','5fbceb','812ab3','706292','2b05e9'],'72bce7_output_truncated_not_native_failure':True})
argv=[sys.executable,'-B','-X','utf8',str(W/'apps/desktop/build-validator.py'),'--go',str(M/'.local/tools/go1.27.1/go/bin/go.exe'),'--node','C:/nvm4w/nodejs/node.exe','--electron',str(M/'apps/desktop/node_modules/electron/dist/electron.exe'),'--module-cache',str(M/'.local/gopath/pkg/mod'),'--web-modules',str(M/'apps/web/node_modules'),'--output',str(W/'.local/desktop-wire'/COHORT),'--receipts',str(D/'build')]
save(D/'build-launch.json',{'actualargv':argv,'cwd':str(W),'source_roster':source,'source_acceptance':False})
run('build',argv)
print(json.dumps({'cohort':COHORT,'namespace':str(N),'status':'BUILT_NOT_TESTED'},ensure_ascii=False))
