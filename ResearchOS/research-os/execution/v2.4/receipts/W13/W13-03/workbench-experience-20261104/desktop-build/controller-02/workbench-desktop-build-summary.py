from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,shutil

main=Path(r'D:\作品集\ResearchOS\research-os')
root=main/'.local/worktrees/workbench-experience-20261104'
receipt=main/'execution/v2.4/receipts/W13/W13-03/workbench-experience-20261104/desktop-build'
control=receipt/'controller-02'
build=receipt/'build-02'
bundle=root/'.local/development-ui-20261104-r2'
head='3cd8e4ceba16ba6c4890fe2fd5a35324682b44f5'
def ref(p):
    p=Path(p)
    return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def read(p):return json.loads(Path(p).read_bytes())
final=read(control/'final.json')
result=read(build/'result.json')
manifest=read(bundle/'development-manifest.json')
if final['status']!='DEVELOPMENT_BUILT_AND_DRYRUN_VALIDATED_NO_NATIVE_START' or manifest['source']['head']!=head:
    raise RuntimeError('final source-bound build is not complete')
dryrun=read(control/'launcher-dryrun/result.json')
build_exit=read(control/'complete-development-build/result.json')
if dryrun['native_exit'] or build_exit['native_exit']: raise RuntimeError('native operation did not pass')
for name in ['workbench-desktop-build-controller.py','workbench-desktop-build-controller-r2.py','workbench-desktop-build-retry-prepare.py','workbench-desktop-build-summary.py']:
    target=control/name
    if target.exists(): raise RuntimeError('controller provenance collision')
    shutil.copyfile(Path(r'C:\Users\yqyyds\Documents\Codex\2026-11-04\task')/name,target)
summary={
 'schema':'researchos.desktop-development-build-summary.v1','at':datetime.now(timezone.utc).isoformat(),
 'status':'BUILT_NOT_NATIVE_TESTED','dry_run_validated':True,'controller_status':final['status'],'executor':'codex:/root/workbench_builder','mode':'DEVELOPMENT_ONLY_NOT_INSTALLER_NOT_NATIVE_ACCEPTANCE',
 'source_head':head,'source_tree':manifest['source']['tree'],'source_digest':manifest['source']['digest'],
 'output':str(bundle),'manifest_path':str(bundle/'development-manifest.json'),'result_path':str(build/'result.json'),'dry_run_report_path':str(control/'launcher-dryrun/stdout.raw'),'actual_build_exit':build_exit['native_exit'],'actual_dryrun_exit':dryrun['native_exit'],
 'outer_exec_session':86389,'outer_exec_exit':0,'files':result['files'],'file_count':result['files'],'bytes':sum(row['bytes'] for row in manifest['files']),'total_bytes':sum(row['bytes'] for row in manifest['files']),
 'electron_files':result['electron_files'],'client_wire_build_input_digest':result['client_wire_build_input_digest'],
 'mu_bundle_sha256':result['mu_bundle_sha256'],
 'source_seven_unchanged':final['source_seven_unchanged'],'source_tracked_clean':final['source_tracked_clean'],
 'bundle_manifest_ref':ref(bundle/'development-manifest.json'),'build_result_ref':ref(build/'result.json'),
 'build_invocation_ref':ref(control/'complete-development-build/invocation.json'),
 'build_exit_ref':ref(control/'complete-development-build/result.json'),
 'build_stdout_ref':ref(control/'complete-development-build/stdout.raw'),'build_stderr_ref':ref(control/'complete-development-build/stderr.raw'),
 'dryrun_invocation_ref':ref(control/'launcher-dryrun/invocation.json'),'dryrun_exit_ref':ref(control/'launcher-dryrun/result.json'),
 'dryrun_stdout_ref':ref(control/'launcher-dryrun/stdout.raw'),'dryrun_stderr_ref':ref(control/'launcher-dryrun/stderr.raw'),
 'source_before_ref':ref(build/'source.before.json'),'source_after_ref':ref(build/'source.after.json'),
 'frozen_ui_manifest':ref(control/'frozen-ui.before.json'),'frozen_seven_before_ref':ref(control/'frozen-ui.before.json'),'frozen_seven_after_ref':ref(control/'frozen-ui.after.json'),
 'attempt_1_ref':ref(receipt/'summary.build-01.json'),'attempt_index':2,
 'failure_origin':'desktop-build/sparse-module-closure','prior_failure_retained':True,'counters_reset':False,
 'dryrun_state_created':False,'provider_calls':0,'product_core_starts':0,'product_gui_starts':0,'installation_actions':0,'formal_increment':0,
 'limits':['Build and dry-run validate the complete development directory only.','No installation, real-provider inference, native product lifecycle or formal acceptance asserted.','The development manifest and verifier installation bind this absolute output path; do not move or copy the directory for use.','First failed attempt and every original scratch/receipt remain preserved.','Root independent build review is still required.']}
with (receipt/'summary.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(summary,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'summary':str(receipt/'summary.json'),'summary_sha256':ref(receipt/'summary.json')['sha256'],'output':str(bundle),'manifest_sha256':summary['bundle_manifest_ref']['sha256'],'files':summary['files'],'bytes':summary['bytes'],'build_exit':summary['actual_build_exit'],'dryrun_exit':summary['actual_dryrun_exit']},ensure_ascii=True))
