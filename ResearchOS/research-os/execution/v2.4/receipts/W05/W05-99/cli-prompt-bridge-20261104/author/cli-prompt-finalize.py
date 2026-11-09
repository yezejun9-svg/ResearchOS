from pathlib import Path
import datetime
import hashlib
import json
import re
import shutil
import subprocess

ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/cli-prompt-bridge-20261104')
MAIN=Path('D:/作品集/ResearchOS/research-os')
OUT=MAIN/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/author'
BASE='fc2b1a50662580b1a0fca92559ca26be6e959f01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
def put(name,value):
    path=OUT/name
    if path.exists():raise RuntimeError('existing final metadata: '+str(path))
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

inputs=load(OUT/'checks-02/inputs.json')
frozen=inputs['source_sha256'];actual={name:sha(ROOT/name) for name in frozen}
if actual!=frozen:raise RuntimeError('candidate source drift since checks02')
baseline_inputs=load(OUT/'baseline-w14-01/inputs.json')
baseline=load(OUT/'baseline-w14-01/result.json')
if baseline['candidate_source_after']!=actual or baseline_inputs['candidate_source_before']!=actual:raise RuntimeError('baseline changed candidate source')
results={name:load(OUT/name/'result.json') for name in ['checks-01','checks-02','baseline-w14-01']}
stdout=(OUT/'checks-02/stdout.txt').read_text(encoding='utf-8')
base_stdout=(OUT/'baseline-w14-01/stdout.txt').read_text(encoding='utf-8')
passed=re.findall(r'^--- PASS: (Test[^\s(]+)',stdout,re.M)
failed=re.findall(r'^--- FAIL: (Test[^\s(]+)',stdout,re.M)
new_passed=[name for name in passed if name.startswith('TestCLIPrompt')]
if failed!=['TestW14CLICommandsUseRealSessionHTTP'] or 'HOST_REJECTED:WRITER_BUSY' not in stdout or 'HOST_REJECTED:WRITER_BUSY' not in base_stdout or baseline['exit_code']!=1:
    raise RuntimeError('unexpected failure set; finalization requires manual review')

lock=load(MAIN/'execution/toolchains/locked.json')
git=lock['tools']['git']
if sha(git['path'])!=git['sha256']:raise RuntimeError('Git tool mismatch')
commands={}
for name,args in [('git-status',['status','--short']),('git-diff-check',['diff','--check']),('git-head',['rev-parse','HEAD'])]:
    argv=[git['path'],'-c','gc.auto=0','-c','maintenance.auto=false']+args
    result=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=30)
    (OUT/(name+'.stdout.txt')).write_bytes(result.stdout);(OUT/(name+'.stderr.txt')).write_bytes(result.stderr)
    commands[name]={'argv':argv,'cwd':str(ROOT),'exit_code':result.returncode}
    if result.returncode!=0:raise RuntimeError('final read-only Git check failed: '+name)
if (OUT/'git-head.stdout.txt').read_text(encoding='utf-8').strip()!=BASE:raise RuntimeError('unexpected HEAD')
put('git-final-commands.json',commands)

snapshot=OUT/'frozen-source';snapshot.mkdir(exist_ok=False)
files=[]
for name,digest in actual.items():
    source=ROOT/name;copy=snapshot/name;copy.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,copy)
    text=source.read_text(encoding='utf-8')
    declarations=[{'line':index,'declaration':line} for index,line in enumerate(text.splitlines(),1) if line.startswith(('func parseExplicitCLIPrompt','func taskDispatch','func readCLIPrompt','func explicitCLIPromptRequested','func cliHostCommandWithPrompt','func runCLIVerbWithPrompt','func verbStepsWithPrompt','func TestCLIPrompt'))]
    files.append({'path':name,'sha256':digest,'bytes':source.stat().st_size,'lines':len(text.splitlines()),'declarations':declarations})
put('source-manifest.json',{'status':'FROZEN_NOT_COMMITTED','scope_id':'CLI_PROMPT_BRIDGE_20261104','base_head':BASE,'worktree':str(ROOT),'file_count':len(files),'files':files,'source_unchanged_since_checks02':True,'frozen_snapshot':str(snapshot)})

diagnostics={
 'status':'ALL_AUTHOR_DIAGNOSTICS_PRESERVED_NO_GLOBAL_LEDGER_MUTATION',
 'records':[
  {'kind':'read_diagnostic','observed':'Candidate AGENTS.md absent under sparse checkout.','resolution':'Read Main AGENTS.md instead; no candidate instruction file created.'},
  {'kind':'read_diagnostic','observed':'Receipt RESUME.md absent; actual file is RESUME.json.','resolution':'Read and obeyed RESUME.json (CP582).'},
  {'kind':'read_diagnostic','observed':'Candidate execution/toolchains/locked.json not materialized.','resolution':'Read project Main execution/toolchains/locked.json, verified absolute Go/Python SHA256, no PATH fallback.'},
  {'kind':'read_diagnostic','observed':'Optional guessed apps/cli/cli_native_init_windows.go and apps/cli/cli_configure.go paths absent.','resolution':'Existing cli_native.go and cli_v2.go locations identified; no source change to native/configuration code.'},
  {'kind':'resource_failure','failure_origin':'cli-prompt-sparse-module-closure-20261104','attempt_index':1,'evidence':'checks-01','exit_code':1,'observed':'Missing local module packages evaluation/holdout/jev, evaluation/evolution, evaluation/skills. Tests not executed.','resolution':'Parent materialized 12 tracked production Go sources and archived source-closure-repair.json; no go get/network or holdout inputs/labels read. checks-01 is unchanged.'},
  {'kind':'source_review_correction','observed':'New parser initially imposed an unsupported 2^53-1 cap on Host integer flags.','resolution':'Removed before checks02; frozen schema has no such maximum and existing CLI uses exact int64. Added 9007199254740993 and MaxInt64 exact payload/envelope tests. No acceptance threshold changed.'},
  {'kind':'directed_retry','failure_origin':'cli-prompt-sparse-module-closure-20261104','attempt_index':2,'evidence':'checks-02','exit_code':1,'observed':'Module setup now succeeds. All 12 prompt test functions and five other selected regressions pass; existing W14 takeover test fails WRITER_BUSY. Resource gap resolved, overall command remains nonzero.'},
  {'kind':'existing_regression_observation','failure_origin':'cli-prompt-existing-w14-writer-busy-20261104','attempt_index':1,'evidence':'checks-02/stdout.txt','test':'TestW14CLICommandsUseRealSessionHTTP','observed':'cli_sessions_test.go:237 desktop takeover HOST_REJECTED:WRITER_BUSY.'},
  {'kind':'baseline_diagnostic','failure_origin':'cli-prompt-existing-w14-writer-busy-20261104','attempt_index':2,'evidence':'baseline-w14-01','exit_code':1,'observed':'Exact fc2b base overlay reproduces same test/line/WRITER_BUSY.','overlay':'Five existing source files mapped to Git snapshots, two new prompt files deleted from build; GOFLAGS carries same overlay to child Go builds. Candidate source SHA256 unchanged before/after.','resolution':'Retain as existing baseline qualification blocker. No test modified, no threshold lowered, no further same-origin retry.'},
 ],
 'parent_resource_diagnostics':'Parent separately preserved sparse-checkout --no-cone unsupported Git129 and subsequent success; this author did not repeat or overwrite those records.',
 'global_failure_counter':'Parent-owned, not modified or reset by this author.',
 'all_processes_terminal':True,
}
put('diagnostics.json',diagnostics)

summary={
 'status':'SOURCE_FROZEN_NEW_PROMPT_TESTS_PASS_EXISTING_BASELINE_BLOCKER',
 'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope_id':'CLI_PROMPT_BRIDGE_20261104','base_head':BASE,
 'worktree':str(ROOT),'committed':False,'source_manifest':str(OUT/'source-manifest.json'),'source_sha256':actual,
 'changes':['task/run explicit --prompt or --prompt-file parsed before discovery, credentials or HTTP.','Validated typed text is passed directly to existing authenticated run session flow, not reconstructed as argv or sent through the credential bridge.','Legacy task and run cascade paths retain original argument delegation. Legacy writer/checker implementations are unchanged.','UTF-8/nonempty/16384 Unicode validation; prompt file reads at most 65537 bytes and rejects more than 65536.','Exact nonnegative int64 Host arguments retained; no JS safe-number cap introduced.','Help retains legacy metadata and separately marks explicit prompt mode as IMPLEMENTED/DEVELOPMENT_ONLY with NOT_EVALUATED independent acceptance.'],
 'development_results':{'overall_command_exit':results['checks-02']['exit_code'],'all_selected_tests_passed':False,'new_prompt_passed_functions':new_passed,'new_prompt_passed_function_count':len(new_passed),'other_passed_functions':[name for name in passed if name not in new_passed],'failed_functions':failed,'baseline_same_failure':True},
 'test_process_results':results,
 'baseline_overlay':{'inputs':str(OUT/'baseline-w14-01/inputs.json'),'go_flags':baseline_inputs['environment_overrides']['GOFLAGS'],'new_files_excluded':baseline_inputs['new_files_removed_from_build'],'candidate_source_unchanged':True},
 'measurement_mode':'DEVELOPMENT_FIXTURE_ONLY','formal_increment':0,'formal_assertion_ids':[],'independent_acceptance':'NOT_REQUESTED',
 'test_boundary':'Only Go test/test-binary processes and explicitly local httptest fixtures. Child credentials are fixture-only; cascade is replaced by a spy. No actual Host process, native credential bridge, provider/model, old task checker, registry or checkpoint action.',
 'model_selection':'Inherited current parent agent session for bounded compatibility implementation; no new user-side CLI/model session.',
 'limitations':['Existing W14 writer-takeover fixture qualification remains blocked on both base and candidate; the selected command is not all green.','No installed CLI/native/model delivery, formal A04 driver or independent product acceptance was exercised.','Legacy deterministic task writer still explicitly refuses; the new prompt branch reuses Host authority instead of replacing that writer.','Root must independently review and serially integrate; this author did not commit or modify Main/registry/CP.'],
 'diagnostics':str(OUT/'diagnostics.json'),'all_processes_terminal':True,
}
put('author-summary.json',summary)
for name in ['cli-prompt-author.py','cli-prompt-tests-author.py','cli-prompt-metadata.py','cli-prompt-pretest.py','cli-prompt-int64-fix.py','cli-prompt-test-controller.py','cli-prompt-test-controller-r2.py','cli-prompt-baseline-controller.py','cli-prompt-retry-prepare.py','cli-prompt-finalize.py']:
    target=OUT/name
    if target.exists():raise RuntimeError('existing author script copy: '+name)
    shutil.copyfile(Path(__file__).parent/name,target)
evidence={str(path.relative_to(OUT)).replace('\\','/'):sha(path) for path in sorted(OUT.rglob('*')) if path.is_file()}
put('diagnostics-manifest.json',{'evidence_sha256':evidence,'source_sha256':actual,'checks01_original_failure_preserved':True,'checks02_overall_exit_preserved':1,'baseline_failure_preserved':1,'no_counter_reset':True})
print(json.dumps({'status':summary['status'],'new_prompt_passed_function_count':len(new_passed),'other_passed_count':len(passed)-len(new_passed),'failed':failed,'source_sha256':actual,'metadata_sha256':{name:sha(OUT/name) for name in ['author-summary.json','source-manifest.json','diagnostics.json','diagnostics-manifest.json']}},ensure_ascii=False))
