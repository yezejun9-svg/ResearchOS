import datetime,hashlib,json,re,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent;W=R.parents[6];M=Path('D:/作品集/ResearchOS/research-os');NS=R.parent
BASE='0bbcef5347ed9bd3a1174c7d3df9dfd8a270e837'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(W).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def save(n,v):(R/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def counts(p):
 raw=p.read_text('utf8',errors='replace');rows=[]
 for line in raw.splitlines():
  try:rows.append(json.loads(line))
  except ValueError:pass
 if any(x.get("Action") in ["pass","fail","skip"] for x in rows if isinstance(x,dict)):return {s:sum(x.get('Action')==s.lower() and 'Test' in x for x in rows) for s in ['PASS','FAIL','SKIP']}
 return {s:len(re.findall(r'^\s*--- '+s+r':',raw,re.M)) for s in ['PASS','FAIL','SKIP']}
sources=json.loads((R/'source_manifest.json').read_text())
for x in sources:assert sha(W/x['path'])==x['after_sha256']
final=[]
for name in ['closure-86d60d4092df4d1896858f6001034b37','closure-a190ef919abf4652ba731eb314d24156']:
 d=NS/name;result=json.loads((d/'result.json').read_text());before=json.loads((d/'source_before.json').read_text());after=json.loads((d/'source_after.json').read_text());assert before==after and result['exit']==0 and not result['source_drift']
 current=[]
 for key,digest in before.items():
  kind,path=key.split(':',1);p=(W/path if kind=='repo' else M/path if kind=='main' else Path(path))
  if sha(p)!=digest:current.append(key)
 assert not current,current
 c=counts(d/'test.stdout');assert c['PASS']>0 and c['FAIL']==c['SKIP']==0,c
 final.append({'directory':d.relative_to(W).as_posix(),'result':result,'counts':c,'source_current_drift':current,'invocation_ref':ref(d/'test.invocation.json'),'stdout_ref':ref(d/'test.stdout'),'stderr_ref':ref(d/'test.stderr'),'source_before_ref':ref(d/'source_before.json'),'source_after_ref':ref(d/'source_after.json'),'go_list_invocation_ref':ref(d/'go-list.invocation.json'),'go_list_ref':ref(d/'go-list.stdout'),'environment_ref':ref(d/'environment.json')})
newpaths=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=W).decode().splitlines()
newdirs=sorted({str(Path(x).parent) for x in newpaths if x.endswith('/invocation.json') or x.endswith('/test.invocation.json')})
runs=[]
for relative in newdirs:
 d=W/relative
 if not d.is_relative_to(NS):raise AssertionError(relative)
 inv=next((p for p in [d/'invocation.json',d/'test.invocation.json'] if p.exists()),None)
 if not inv:continue
 record=json.loads(inv.read_text());raw=next((p for p in [d/'stdout.raw',d/'test.stdout'] if p.exists()),None)
 runs.append({'directory':d.relative_to(W).as_posix(),'exit':record['exit'],'invocation_ref':ref(inv),'stdout_ref':ref(raw) if raw else None,'counts':counts(raw) if raw else None})
save('all_new_runs.json',runs)
save('failure_origins.json',{'prior_failure_origins_ref':ref(NS/'candidate-b8938f84655849b9847611dbf3440442/failure_origins.json'),'old_raw_unchanged':True,'shared_failure_counters_modified':False,'new_actual_failures':[{'directory':x['directory'],'actual_exit':x['exit'],'invocation_ref':x['invocation_ref'],'stdout_ref':x['stdout_ref'],'resolution':('Retained original independent semantic red reproduced before repair.' if 'e319d1' in x['directory'] else 'New test initially omitted fmt import; compiler failure preserved, import corrected within allowed test.' if 'c38aa' in x['directory'] else 'Second-level tool JSON decoded secret confirmed by fixed SDK; added bounded incremental token quarantine.')} for x in runs if x['exit']!=0],'intermediate_closures':['closure-4c5f578b122345e49b1db36450034418','closure-b7f80074cdf24df59273a25770c7bc74'],'receipt_assembly_failure':{'script':'finalize.py','actual_exit':1,'reason':'First counter treated unrelated standalone structured test logs as go test -json output, yielding zero assertion counts; fail-closed assembly refused. Finalize_v2 distinguishes Action rows from ordinary logs; no source/raw changes.'},'intermediate_note':'Both actual exit0/39053/zero drift. Later necessary tool-JSON source change makes them historical, not final current proof.'})
fixtures=[]
for x in final:
 d=W/x['directory']/'actual-fixtures'
 if d.exists():fixtures.extend(ref(p) for p in sorted(d.rglob('*')) if p.is_file())
patch=subprocess.check_output(['git','diff','--',*[x['path'] for x in sources]],cwd=W);(R/'source.patch').write_bytes(patch)
modified=subprocess.check_output(['git','diff','--name-only'],cwd=W).decode().splitlines();assert set(modified)=={x['path'] for x in sources},modified
save('handoff.json',{'schema':'researchos.w05.model-stream-quarantine-repair.v1','status':'CANDIDATE_FOR_INDEPENDENT_REVIEW','executor_id':'codex:/root/sources_parent_impl','verifier_id':'codex:/root/w05_merge_review','base_candidate':BASE,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_manifest_ref':ref(R/'source_manifest.json'),'exact_changed_source':modified,'original_authorities_ref':ref(R/'original_refs.json'),'final_runs':final,'actual_fixture_artifacts':fixtures,'failure_origins_ref':ref(R/'failure_origins.json'),'all_new_runs_ref':ref(R/'all_new_runs.json'),'behavior':['Fixed SDK first choice and first non-empty reasoning_content/reasoning/reasoning_text append to one thinking lane. Unused aliases do not create false concatenation.','Valid consecutive reasoning.text/text and reasoning.summary/summary merge irrespective provider detail id/index. Invalid details do not break merges; other valid types do.','Function arguments use SDK index/id aliases and bounded incremental second-level JSON string/escape/UTF16 detection. Incomplete escape units are withheld and rejected at EOF; harmless divergence progresses before EOF, with no whole-argument extra buffer.','Original 2 MiB raw/4096 lane ceilings and immutable original accepted bytes remain. Custom input is included in semantic raw suffix tracking.','Four actual loopback SDK/SQLite/compiled CLI semantic negative controls preserve three already durable visible deltas, original effect UNKNOWN and zero END; synthetic credential fragments absent from canonical evidence and archived worker stdout.'],'fixed_sdk_positive_refs':[ref(NS/'test-4f11cc74084a4d338e441d8bbc618e0b/stdout.raw'),ref(NS/'test-fb2f418aa396497c94fedecb64454c10/stdout.raw')],'prior_candidate_ref':ref(NS/'candidate-b8938f84655849b9847611dbf3440442/handoff.json'),'protected':'JS2, SDK, public schemas, SQL migrations, ordinary ACK/budgets/queue/oldraw and Root metadata unchanged. L04 review is separate MAIN namespace, absent from this candidate.','open_gates':['Original CANCEL ACK-to-final immutable-idempotency trigger remains OPEN.','No real provider/paid API/model qualification or W05/A04/formal acceptance.','Prior legacy29/W17/Linux/resource failure origins remain unchanged.'],'formal_acceptance_delta':0,'external_provider_calls':0,'real_credential_reads':0})
files=[W/x for x in subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=W).decode().splitlines() if x.startswith(NS.relative_to(W).as_posix()+'/')]
save('manifest.json',{'schema':'researchos.immutable-artifact-manifest.v1','self_excluded':True,'files':[ref(p) for p in sorted(files) if p.is_file() and p!=R/'manifest.json']})
print(json.dumps({'handoff':ref(R/'handoff.json'),'manifest':ref(R/'manifest.json'),'final_counts':[x['counts'] for x in final],'receipt_files':len(files)},ensure_ascii=False))
