import pathlib,json,hashlib,zipfile,subprocess,datetime,re
ROOT=pathlib.Path.cwd()
NS=ROOT/'execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/98552188a0014da3a6d73be7cdb3f9bd'
D=NS/'final-audit-5d4b54f18d6e443d87a0b1efcacbce6a'
C=NS/'cohort-e959253f81ad4b5ab7e76c8b9ec30494'
OUT=ROOT/'.local/desktop-wire/e959253f81ad4b5ab7e76c8b9ec30494'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def put(name,value):
 p=D/name
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2)
 return p
source=read(D/'source-commit.json');assert source['commit']==subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
assert len(source['paths'])==15 and all(sha(ROOT/x['path'])==x['sha256'] for x in source['paths'])
inputs=read(C/'build/inputs.before.json');current=[]
for x in inputs:
 p=pathlib.Path(x['path']);actual=sha(p);assert actual==x['sha256'],str(p);current.append({**x,'current_sha256':actual})
put('inputs.current.json',current)
roster=read(C/'leaf-inventory.before.json');expected=set(roster['leaves']);rows=[];reg=[];runs=[]
for path in sorted(C.glob('*/result.json')):
 x=read(path)
 if 'rows' not in x:continue
 assert not x['drift'] and x['not_run']==0 and x['first_unexpected'] is None
 target=reg if path.parent.name.startswith('regressions-') else rows
 for item in x['rows']:
  assert item['status']=='PASS' and item['exit']==0
  case=ROOT/item['relative_evidence'];text=(case/'stdout').read_text(encoding='utf-8')
  node_case=item['name'] not in ['w14-native','w14-review']
  if node_case:
   assert re.search(r'# pass 1\b',text) and re.search(r'# fail 0\b',text) and re.search(r'# skipped 0\b',text),item['name']
  target.append({**item,'unit':'node:test leaf' if node_case else 'legacy assertion program','stdout_ref':ref(case/'stdout'),'stderr_ref':ref(case/'stderr'),'invocation_ref':ref(case/'invocation.json'),'raw_evidence_refs':[ref(p) for p in sorted((case/'evidence').rglob('*')) if p.is_file()] if (case/'evidence').exists() else []})
 runs.append(ref(path))
assert len(rows)==159 and len(set(x['name'] for x in rows))==159 and {x['name'] for x in rows}==expected
assert len(reg)==7 and len({x['name'] for x in reg})==7
put('finite-matrix.json',{'source_commit':source['commit'],'cohort':C.name,'leaves':rows,'regressions':reg,'finite159_pass':159,'finite159_fail':0,'finite159_skip':0,'finite159_not_run':0,'regression_units_pass':7,'regression_unit_breakdown':{'node_test_leaves':5,'legacy_assertion_programs':2},'no_invented_legacy_assertion_count':True,'source_acceptance':False,'runs':runs})
historical=[]
for p in sorted(NS.glob('cohort-*/*/result.json')):
 x=read(p)
 if 'rows' in x:historical.append({'result_ref':ref(p),'executed':x['executed'],'pass':x['pass'],'http':sum(r['http_count'] for r in x['rows']),'direct_validator_children':sum(r['child_count'] for r in x['rows']),'first_unexpected':x['first_unexpected']})
total=sum(x['http'] for x in historical);assert total<=386
put('all-cohorts-accounting.json',{'history':historical,'recorded_http_total_including_history':total,'current_http':sum(x['http_count'] for x in rows+reg),'http_max':386,'external':0,'model':0,'SDK':0,'paid':0,'notes':['Direct validator child counts exclude Node test processes, Electron processes and synthetic pipe-holder descendants; original per-process records remain authoritative.','Six legacy v1 HTTP requests derive from successful original server assertions: proxy5 and SSE1. Other recorded requests are raw loopback HTTP observations.','Legacy bootstrap and first-use logical doubles are synthetic; no actual native credential or workspace bootstrap was executed.']})
modules=[]
for p in sorted(C.rglob('modules-*.closure.json')):
 x=read(p)
 for f in x['files']:assert sha(pathlib.Path(f['path']))==f['sha256'],f['path']
 modules.append({'closure_ref':ref(p),'owned_pid':x['pid'],'OS_creation_time':x['start_time'],'count':len(x['files']),'current_hashes_match':True})
put('process-modules.current.json',modules)
files={}
for base in [OUT/'apps/desktop',OUT/'apps/web/dist',OUT/'fixtures']:
 for p in base.rglob('*'):
  if p.is_file():files[p]='development-resource/'+p.relative_to(OUT).as_posix()
files[OUT/'validator.test.exe']='development-resource/validator.test.exe'
for x in source['paths']:files[ROOT/x['path']]='source/'+x['path']
compiler=read(C/'build/compiler-work-archive.json')
for x in compiler['WORK']+compiler['archives']:
 p=pathlib.Path(x['path']);assert sha(p)==x['sha256'];files[p]='compiler/'+p.relative_to(OUT).as_posix()
archive=D/'current-source-resource-compiler.zip';entries=[]
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p,name in sorted(files.items(),key=lambda item:item[1]):
  b=p.read_bytes();z.writestr(name,b);entries.append({'original_path':str(p),'entry':name,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for x in entries:assert hashlib.sha256(z.read(x['entry'])).hexdigest()==x['sha256']
put('archive-entries.json',{'archive_ref':ref(archive),'entries':entries})
failures=[ref(p) for p in sorted(NS.glob('failure-origin-*.json'))]+[ref(p) for p in sorted(NS.glob('qualification-deviation-*.json'))]
put('failure-origins-index.json',{'origins':failures,'policy':'Original bytes, actual native/outer/nested exits and qualification deviations retained. No failure counter is reset. This index does not re-register Root counters.'})
build=read(C/'build/result.json')
descriptor=pathlib.Path(build['descriptor']);binary=descriptor.parent/'researchos-client-wire-validator.exe'
assert sha(binary)==build['binary_sha256']
handoff={'status':'EXECUTION_REPORTED_AWAITING_NONAUTHOR_REVIEW','source_acceptance':False,'formal_acceptance':False,'executor_id':'codex:/root/sources_parent_impl','writer':'STOPPED','source_commit':source['commit'],'base':source['base'],'source_paths':15,'source_scope_audit_ref':ref(D/'source-scope-audit.json'),'source_commit_ref':ref(D/'source-commit.json'),'matrix_ref':ref(D/'finite-matrix.json'),'accounting_ref':ref(D/'all-cohorts-accounting.json'),'failure_origins_ref':ref(D/'failure-origins-index.json'),'current_inputs_ref':ref(D/'inputs.current.json'),'input_count':len(inputs),'input_drift':0,'process_closure_ref':ref(D/'process-modules.current.json'),'build_ref':ref(C/'build/result.json'),'build_input_digest':build['build_input_digest'],'binary_sha256':build['binary_sha256'],'descriptor_exact_ref':{'absolute_path':str(descriptor),'sha256':sha(descriptor)},'archive_ref':ref(archive),'archive_entries_ref':ref(D/'archive-entries.json'),'final_cohort':C.name,'current_results':{'finite_leaves_pass':159,'finite_leaves_fail':0,'finite_leaves_skip':0,'finite_leaves_not_run':0,'regression_programs_and_leaves_pass':7,'regression_fail':0,'regression_skip':0,'regression_not_run':0,'offscreen_real_renderers':2,'http':sum(x['http_count'] for x in rows+reg),'external':0,'model':0,'SDK':0,'paid':0},'not_run_or_hold':['Two Go unit functions are compiled by test-c only; actual finite validation uses compiled production Go child and Node/Electron roster. Not reported as Go-test PASS.','Actual Host requests greater than its existing1MiB limit remain unqualified. Helper/Desktop capacity does not expand public API.','Actual Host acquire/renew/cancel/resume completion, native frame boundaries, browser Continuity, installed deployment/packaging, visible GUI/NVDA and live provider qualification remain HOLD.','No product SQLite DB or private DB is accessed by this pure validator slice; closed-DB evidence is not applicable.'], 'scope_registration_ref':ref(NS/'scope_registration.json'),'implementation_conditions_ref':ref(NS/'implementation_conditions_ref.json'),'sealed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
put('handoff.json',handoff)
manifest=[ref(p) for p in sorted(NS.rglob('*')) if p.is_file() and p.name!='manifest.json']
put('manifest.json',{'root':NS.relative_to(ROOT).as_posix(),'files':manifest,'self_excluded':True,'source_writer':'STOPPED'})
print(json.dumps({'handoff':ref(D/'handoff.json'),'manifest':ref(D/'manifest.json'),'source_commit':source['commit'],'archive':ref(archive),'files':len(manifest),'http_total':total},ensure_ascii=False),flush=True)
