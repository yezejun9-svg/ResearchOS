import pathlib,json,hashlib,zipfile,re,datetime
W=pathlib.Path.cwd();N=pathlib.Path(__file__).parent;B=N.parent/'revision-r317-8c81bc59bc444fe2b0c5916e282f04a1';C=N/'cohort-19e75d3970f54c2eab44fcac2f43d61d';O=W/'.local/desktop-wire/19e75d3970f54c2eab44fcac2f43d61d';D=N/'final-audit-2d44db33d4874f8bb806b44137292e08'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def ref(p):return {'path':p.relative_to(W).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def put(name,value):
 p=D/name
 with p.open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
source=read(D/'source-commit.json');whole=read(C/'source-exact15.before.json');assert all(sha(W/x['path'])==x['sha256'] for x in whole)
put('whole15.current.json',whole)
full=read(C/'full-finite-inputs.json');current=[]
for x in full:
 actual=sha(pathlib.Path(x['path']));assert actual==x['sha256'];current.append({**x,'current_sha256':actual})
put('full-inputs.current.json',current)
roster=read(N/'finite-roster.frozen.json');rows=[];reg=[];runs=[]
for p in sorted(C.glob('*/result.json')):
 x=read(p)
 if 'rows' not in x:continue
 assert not x['drift'] and not x['first_unexpected'] and x['not_run']==0
 target=reg if x['phase']=='regressions' else rows
 for item in x['rows']:
  assert item['status']=='PASS' and item['actual_native_exit']==0
  case=W/item['relative_evidence'];text=(case/'stdout.raw').read_text(encoding='utf8')
  if item['name'] not in ['w14-native','w14-review']:
   assert re.search(r'(?:#|ℹ) pass 1\b',text) and re.search(r'(?:#|ℹ) fail 0\b',text) and re.search(r'(?:#|ℹ) skipped 0\b',text)
  target.append({**item,'stdout_ref':ref(case/'stdout.raw'),'stderr_ref':ref(case/'stderr.raw'),'invocation_ref':ref(case/'invocation.json')})
 runs.append(ref(p))
assert len(rows)==162 and {x['name'] for x in rows}=={x['name'] for x in roster['leaves']};assert len(reg)==7
matrix=put('finite-matrix.json',{'source_commit':source['commit'],'cohort':C.name,'original159_actual_pass':159,'supplemental3_actual_pass':3,'regressions7_actual_pass':7,'Node_leaf_and_program_fail':0,'skip':0,'not_run':0,'rows':rows,'regressions':reg,'actual_runs':runs,'source_acceptance':False})
oldC=B/'cohort-7da1948601f74dfca08b3d91b30b2191';unit_result=next(oldC.glob('units-*/result.json'));units=read(unit_result);assert units['pass']==1 and not units['drift'];unitcase=W/units['rows'][0]['relative_evidence'];utext=(unitcase/'stdout.raw').read_text(encoding='utf8');passes=re.findall(r'^\s*--- PASS: (\S+) ',utext,re.M)
old_vector=read(oldC/'full-finite-inputs.json');bridge=[];excluded=[]
for x in old_vector:
 actual=sha(pathlib.Path(x['path']));entry={**x,'current_sha256':actual}
 if actual!=x['sha256']:
  assert pathlib.Path(x['path'])==W/'tests/ui/desktop/http-wire-boundary.test.mjs';excluded.append(entry)
 else:bridge.append(entry)
assert len(excluded)==1
oldexe=W/'.local/desktop-wire/7da1948601f74dfca08b3d91b30b2191/validator.test.exe';assert sha(oldexe)==sha(O/'validator.test.exe')
unitproof=put('Go-component-bridge.json',{'actual_once_run_ref':ref(unit_result),'actual_stdout_ref':ref(unitcase/'stdout.raw'),'top_functions':roster['go_units'],'pass_records_including_parent':len(passes),'leaf_records':len([p for p in passes if '/' in p])+2,'actual_native_exit':0,'actual_exe_before':{'path':str(oldexe),'sha256':sha(oldexe)},'new_build_exe':{'path':str(O/'validator.test.exe'),'sha256':sha(O/'validator.test.exe')},'new_cohort_units_rerun':False,'old_recorded_inputs_current_equal':bridge,'excluded_nonGo_test_input':excluded,'all_original_WORK_generated_archive_inputs_current_equal':True,'limitation':'Old unit process loaded OS/Python module inventory was not individually captured. Same executable/current compiled byte closure does not manufacture that missing actual-load observation. Root decision on any extra evidence-only execution remains separate.','current_component_OS_observation_complete':False})
historical=[]
for ns in [B,N]:
 for p in sorted(ns.glob('cohort-*/*/result.json')):
  x=read(p)
  if 'rows' in x:historical.append({'ref':ref(p),'pass':x['pass'],'executed':x['executed'],'HTTP':sum(r['http_count'] for r in x['rows']),'first_unexpected':x['first_unexpected']})
total=sum(x['HTTP'] for x in historical);now=sum(x['http_count'] for x in rows+reg);assert total==162 and now==158 and total<=390
accounting=put('revision-accounting.json',{'current_cohort_HTTP':now,'r317_author_all_HTTP':total,'r317_cap':390,'old_840_phase_HTTP_preserved':302,'all_history_HTTP':302+total,'all_history_cap':692,'history':historical,'external_MODEL_SDK_paid':0,'counts_basis':'Actual raw HTTP observations plus preserved legacy proxy5/SSE1 successful assertions. Not an independent network trace.','failed_leaf_0bbcd5_still_fail':True})
modules=[]
for p in sorted(C.rglob('modules-*.closure.json')):
 x=read(p)
 for f in x['files']:assert sha(pathlib.Path(f['path']))==f['sha256']
 modules.append({'ref':ref(p),'pid':x['pid'],'start_time':x['start_time'],'files':len(x['files']),'current_equal':True})
moduleproof=put('current-process-modules.json',{'observations':modules,'limit':'Sampled actual owned child modules; does not prove every possible later dynamically loaded module or old unit process.'})
files={}
for base in [O/'apps/desktop',O/'apps/web/dist',O/'fixtures']:
 for p in base.rglob('*'):
  if p.is_file():files[p]='development-resource/'+p.relative_to(O).as_posix()
files[O/'validator.test.exe']='development-resource/validator.test.exe'
for x in whole:files[W/x['path']]='source/'+x['path']
compiler=read(C/'build/compiler-work-archive.json')
for x in compiler['WORK']+compiler['archives']:
 p=pathlib.Path(x['path']);assert sha(p)==x['sha256'];files[p]='compiler/'+p.relative_to(O).as_posix()
archive=D/'current-source-resources-compiler.zip';entries=[]
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p,name in sorted(files.items(),key=lambda v:v[1]):
  b=p.read_bytes();z.writestr(name,b);entries.append({'original_path':str(p),'entry':name,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for x in entries:assert hashlib.sha256(z.read(x['entry'])).hexdigest()==x['sha256']
archiveproof=put('archive-entries.json',{'archive':ref(archive),'entries':entries})
failureproof=put('failure-origins.json',{'new_actual_origin':ref(B/'failure-origin-0bbcd5.json'),'apply_patch_unknown_native_diagnostic':ref(B/'tool-diagnostics.initial.json'),'old_phase_failure_index':ref(N.parent/'98552188a0014da3a6d73be7cdb3f9bd/final-audit-c0fea60e04e34fbd803b5d2feae78df8/failure-origins-index.json'),'counter_reset':False})
handoff=put('handoff.json',{'status':'EXECUTION_REPORTED_AWAITING_NONAUTHOR_REVIEW','writer':'STOPPED','source_commit':source['commit'],'base_evidence_head':source['parent'],'source_delta_paths':6,'whole_original_paths':15,'source_ref':ref(D/'source-commit.json'),'whole15_ref':ref(D/'whole15.current.json'),'protected17_ref':ref(C/'protected17.json'),'matrix_ref':matrix,'accounting_ref':accounting,'Go_component_ref':unitproof,'full_input_count':len(full),'full_inputs_ref':ref(D/'full-inputs.current.json'),'module_ref':moduleproof,'archive_ref':ref(archive),'archive_entries_ref':archiveproof,'failure_origins_ref':failureproof,'build_ref':ref(C/'build/result.json'),'source_acceptance':False,'Main_integration_authorized':False,'formal_increment':0,'limitations':['Go actual3 component once-run is linked but lacks that old unit process individual OS load observation; not claimed as new Node cohort unit execution.','PublicHost1MiB/nativeframe/actualHost completion/installedGUI/NVDA/liveprovider remain HOLD.','Closed product SQLite evidence is not applicable to this pure validator slice.'],'sealed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
manifest=put('manifest.json',{'files':[ref(p) for ns in [B,N] for p in sorted(ns.rglob('*')) if p.is_file()],'self_excluded':True,'source_writer':'STOPPED'})
print(json.dumps({'handoff':handoff,'manifest':manifest,'source_commit':source['commit'],'matrix':matrix,'archive':ref(archive),'input_count':len(full),'HTTP':total},ensure_ascii=False),flush=True)
