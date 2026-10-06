import pathlib, json, hashlib, datetime, subprocess
P=pathlib.Path(__file__).resolve().parent
ROOT=P.parents[6]
MAIN=pathlib.Path('D:/作品集/ResearchOS/research-os')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def put(name,v):
 with (P/name).open('x',encoding='utf-8') as w:json.dump(v,w,ensure_ascii=False,indent=2);w.write('\n')
def snapshot(path,name):
 raw=path.read_bytes()
 with (P/name).open('xb') as w:w.write(raw)
 return {'original':ref(path),'snapshot':ref(P/name)}
sources={}
for path in ['internal/domain/runtime_model_verification.go','internal/domain/runtime_provider_binding_windows_test.go','internal/domain/contracts.go','internal/store/sqlite.go']:
 sources[path]=snapshot(ROOT/path,path.replace('/','__')+'.frozen')
for path in ['database/sql/driver/types.go','encoding/json/decode.go']:
 f=MAIN/'.local/tools/go1.27.1/go/src'/path
 sources[path]=snapshot(f,'go__'+path.replace('/','__')+'.frozen')
put('failed-attempt-sources.json',sources)
for label,argv in [('git-status',['git','status','--short']),('git-diff',['git','diff','--','internal/domain/runtime_model_verification.go','internal/domain/runtime_provider_binding_windows_test.go']),('git-head',['git','rev-parse','HEAD'])]:
 proc=subprocess.run(argv,cwd=ROOT,capture_output=True)
 for kind,raw in [('stdout',proc.stdout),('stderr',proc.stderr)]:
  with (P/(label+'.raw.'+kind)).open('xb') as w:w.write(raw)
 put(label+'.invocation.json',{'argv':argv,'cwd':str(ROOT),'exit':proc.returncode,'stdout':ref(P/(label+'.raw.stdout')),'stderr':ref(P/(label+'.raw.stderr'))})
extra=json.loads((P/'additional-tool-lock-inputs.before.json').read_text(encoding='utf-8'))['files']
after={p:{'sha256':sha(pathlib.Path(p)),'bytes':pathlib.Path(p).stat().st_size} for p in extra}
put('additional-tool-lock-inputs.after.json',{'files':after,'drift':[p for p in extra if extra[p]!=after[p]]})
origins=[{'chain_id':'P9-P12-SR01-author-causal-repair','ordinal':1,'case':'case-01-1-none','input':ref(P/'inputs/1.sqlite'),'invocation':ref(P/'case-01-1-none.invocation.json'),'stdout':ref(P/'case-01-1-none.stdout.raw'),'stderr':ref(P/'case-01-1-none.stderr.raw'),'result':ref(P/'case-01-1-none.result.json'),'actual':ref(P/'case-01-1-none-evidence/actual.json'),'closed_db':ref(P/'case-01-1-none-evidence/case.sqlite'),'assertion':'unexpected sealed original rejected/empty: provider original Run epoch unavailable','source_line':'internal/domain/runtime_provider_binding_windows_test.go:894','product_guard':'providerOriginalRun JSON epoch SQL parameter; no match','after_failure_source_edits':0,'after_failure_cases':0,'models':0,'workers':0,'HTTP':0,'prior_independent_red_origin':1,'held_history_refusals':5,'status':'STOPPED_FIRST_UNEXPECTED_REJECTION','interpretation':'Original unchanged PREPARED is rejected. Earlier red rejection has identical early error and is not evidence P1 semantic guard works.'}]
put('failure_origins.json',origins)
proposal={'status':'NARROW_CORRECTION_PROPOSED_NOT_AUTHORIZED','issue':'P9-P12-SR01','prior_attempt':ref(P/'execution-summary.json'),'sources':ref(P/'failed-attempt-sources.json'),'exact_path':'internal/domain/runtime_model_verification.go','exact_function':'providerOriginalRun','current_query_parameter':'effect["epoch"]','proposed_change':['Before Query, call Num(effect,"epoch"); reject error or epoch<1.','Pass resulting int64 to json_extract(body,\'$.lease_epoch\')=?; retain exact equality, Run identity checks and all failclosed guards.','No CAST on arbitrary text, no latest Run/runtime fallback, no schema or legacy exception.'],'causal_evidence':['contracts.go Decode uses json.Decoder.UseNumber; effect epoch is json.Number.','Go encoding/json Number is a named string. sql/driver DefaultParameterConverter reflect.String returns string.','New json_extract expression has no INTEGER column affinity; the old runtime_dispatches.epoch column does. A text parameter can therefore miss numeric JSON even though old column comparisons succeeded.','Actual untouched original returns zero historical Run rows. No extra DB query/probe was executed after stop; dynamic type causality is still for independent confirmation.'],'limits':'This is an implementation error hypothesis supported by static type flow, not independently proven repair. Both old held positives stay stopped. New source/test attempt requires Root registration; failure counts persist.','proposed_next_validation':'After independent cause confirmation and new authorization: rebuild/freeze current entire inputs; once original red plus unchanged PREPARED baseline, then remaining registered controls only if both behave at the correct layer. No broad model regression.','formal_increment':0}
put('epoch_parameter_correction_proposal.json',proposal)
put('stopped_handoff.json',{'status':'STOPPED_FIRST_UNEXPECTED_NOT_SOURCE_READY','failure_origins':ref(P/'failure_origins.json'),'proposal':ref(P/'epoch_parameter_correction_proposal.json'),'sources':ref(P/'failed-attempt-sources.json'),'summary':ref(P/'execution-summary.json'),'binary':ref(P/'domain.test.exe'),'red_semantic_guard_proven':False,'actual_cases':2,'not_run_cases':38,'models':0,'source_commit':'NOT_COMMITTED_PENDING_ROOT_CAUSAL_DECISION'})
files=[ref(f) for f in sorted(P.rglob('*')) if f.is_file() and f.name!='stopped_manifest.json']
put('stopped_manifest.json',{'files':files,'self_excluded':True})
print(json.dumps({n:ref(P/n) for n in ['failure_origins.json','epoch_parameter_correction_proposal.json','failed-attempt-sources.json','stopped_handoff.json','stopped_manifest.json']},ensure_ascii=True,indent=2))
