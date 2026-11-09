from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent
W=R.parent.parent
S=W/'product-v1-real-electron-tree-diagnostic-revision-05'
B=W/'product-v1-real-electron-tree-diagnostic-revision-04'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
pins={
 'FROZEN.json':'e5580f5c81158edce3ae1e581379b85acfce0dc8df98cfe12d31ce1c2a85e819',
 'MANIFEST.json':'df695dedc5926ccbf1b3b2a7df1345c973839ed20ff0dddafa938657ec90f55b',
 'choose-owned-folder.ps1':'8d2811eb8e8c3fd93cbbf460b5562c899df88cb1458dc522fbadad5def284875',
 'real-electron-flow.mjs':'def290342be6417bff524cac2e0a3c0779429851e3c87160381600c268ca3eb6'}
for n,h in pins.items():assert sha(S/n)==h,n
manifest=read(S/'MANIFEST.json')
checked=[]
for f in manifest['files']:
 p=S/f['path'];assert sha(p)==f['sha256'] and p.stat().st_size==f['bytes'],f['path']
 checked.append({'path':f['path'],'sha256':sha(p),'bytes':p.stat().st_size})
prior=R.parent/'revision04/report.json'
assert sha(prior)=='6cba3256565446f240013d42bd84556d98cf8932c2018bd438ac40b29bbfd147'
assert read(prior)['decision']=='APPROVED_SOURCE_FIXTURE_ONLY'
assert sha(B/'choose-owned-folder.ps1')=='88e4b33142d8e8274ec0edcc99314f4f867a749217f869298ae8e7fdc52d9d47'
assert (B/'real-electron-flow.mjs').read_bytes()==(S/'real-electron-flow.mjs').read_bytes()
old=(B/'choose-owned-folder.ps1').read_bytes();new=(S/'choose-owned-folder.ps1').read_bytes()
old_start=old.index(b'      foreach ($provider in @(\n')
new_start=new.index(b'      $providers=[Collections.Generic.List[object]]::new()\n')
suffix=b'        Assert-DirectNativeTree\n'
old_end=old.index(suffix,old_start);new_end=new.index(suffix,new_start)
assert old[:old_start]==new[:new_start] and old[old_end:]==new[new_end:]
assert new[:new_start]+old[old_start:old_end]+new[new_end:]==old
assert b'Windows.Automation.LegacyIAccessiblePattern]::Pattern' not in new[new_start:new_end]
assert b"status='UNSUPPORTED_TYPE'" in new
assert b'$okAttempted=$true' not in new and b'Get-OwnedDialogButton 1' not in new
actual=W/'product-v1-tree-diagnostic-run-05/receipts/owned-tree-snapshot.json'
assert sha(actual)=='ea56d9a93d9c378ac9c517346353f678b2c57758d18edf52c08161dadc20a140'
result=read(R/'result.json');pure=read(R/'stdout.raw')
assert result['exit_code']==0 and pure['status']=='PASS' and pure['passed']==3
assert sha(R/'stderr.raw')=='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
assert sha(R/'stdout.raw')==result['stdout_sha256']
source_checks={'schema':'researchos.optional-legacy-independent-source-checks/1','pins_verified':pins,'manifest_files_verified':checked,'baseline_report_sha256':sha(prior),'actual05_snapshot_sha256':sha(actual),'source_delta':{'only_provider_construction_changed':True,'reverse_optional_branch_restores_entire_revision04_helper_bytes':True,'baseline_line_endings_preserved':True,'actual_line_endings':'LF','runner_byte_identical':True,'prior_owner_projection_and_both_call_sites_unchanged':True,'prior_budget_zero_noOK_normal_owned_Cancel_fresh_HWND_PID_creation_image_nonce_guards_unchanged':True},'no_drift':True,'old_suites_rerun':False}
write(R/'source-checks.json',source_checks)
diagnostics=read(S/'DIAGNOSTICS.json')
report={
 'schema':'researchos.independent-source-review.v1',
 'decision':'APPROVED_SOURCE_FIXTURE_ONLY','formal_increment':0,'product_increment':0,'pending_blockers':[],
 'source_sha256':{n:pins[n] for n in ('real-electron-flow.mjs','choose-owned-folder.ps1')},
 'freeze_ref':str(S/'FROZEN.json'),'freeze_sha256':pins['FROZEN.json'],
 'manifest_ref':str(S/'MANIFEST.json'),'manifest_sha256':pins['MANIFEST.json'],'manifest_files_verified':len(checked),'no_drift':True,
 'review_scope':'Narrow optional Legacy managed-type fix and unchanged same-Current owner guard; source and synthetic fixtures only.',
 'reused_review':{'ref':str(prior),'sha256':sha(prior),'reason':'Revision04 P2 resolution and unchanged guard/noOK/zero-budget source findings; no old date/path/env/SDK/Go suites rerun or recounted.'},
 'source_delta_proof':source_checks['source_delta'],
 'independent_checks':{'case_groups':3,'exit_code':0,'helper_AST_syntax_exit':0,'selection_fragment_syntax_exit':0,'cases':pure['cases'],'method':'Extracted actual AST function definitions and corrected line-start-bounded actual Selection fragment; all elements and getters synthetic. Installed pwsh7 -NoLogo -NoProfile -File; no ExecutionPolicy/IEX.','ref':str(R/'result.json'),'command_ref':str(R/'command.json'),'stdout_ref':str(R/'stdout.raw'),'stdout_sha256':sha(R/'stdout.raw'),'stderr_ref':str(R/'stderr.raw'),'stderr_sha256':sha(R/'stderr.raw'),'powershell_sha256':'362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139','raw_tool_chunk':'57b8a4','passive_assembly_loads':2,'dynamic_csharp_compile':0,'com_objects':0,'helper_entrypoint':0,'real_uia_element_calls':0,'gui':0,'model':0},
 'static_second_eye':{'result':'NO_BLOCKER','lines':{'same_Current_owner_before_values':'398-400','optional_type_and_provider_loop':'401-420','Selection_continuation':'429-445','same_Current_metadata_owner_guard':'66-74','owned_Cancel_noOK':'461-487'},'execution':0,'writes':0},
 'diagnostic_events':[
  {'origin_key':'direct-managed-legacy-type-eager-array-aborts-available-patterns','classification':'PRESERVED_ACTUAL05_OPTIONAL_MANAGED_TYPE_FAILURE','status':'SOURCE_FIXTURE_ONLY_REAL_PATH_NOT_RUN','ref':str(actual),'sha256':sha(actual),'observed_error':read(actual)['direct_native_tree']['error'],'new_count':0,'failure_history_retained':True},
  {'origin_key':'direct-native-provider-metadata-before-owner-check','classification':'PRESERVED_PRIOR_P2_RESOLUTION','ref':str(prior),'sha256':sha(prior),'new_count':0,'failure_history_retained':True},
  *[dict(e,preserved_from=str(S/'DIAGNOSTICS.json'),preserved_source_sha256=sha(S/'DIAGNOSTICS.json'),new_count=0,failure_history_retained=True) for e in diagnostics['new_events']],
  {'origin_key':'independent-review-evidence-assertion-scope','classification':'LOCAL_REPORT_PREPARATION_ERROR','attempts':2,'known_not_executed':'No report was written before either error; pure fake checks had already passed.','ref':str(R/'preparation-attempt.raw'),'resolution':'Used observed baseline LF and scoped absent-eager-Legacy assertion to changed diagnostic provider block; historical dormant navigation function remains byte-identical to approved baseline. Exact reverse byte comparison required. Source/fixtures unchanged; no real diagnostic.','helper_entrypoint':0,'gui':0,'model':0}
 ],
 'qualification_limits':['Approval is source/fixture only; no actual provider path, folder permission, authorization, product acceptance or V1 journey completion is established.','Root must register fresh exact-source scope06 and original exact outer Job accounting before any actual zero-model diagnostic.','Value and selected absolute candidates remain nonauthorizing; unknown provider/cancel/close remains blocked.'],
 'counter_reset':False,'pending_operations':[],'uncertain_outcomes':[]}
write(R/'report.json',report)
files=['optional-regression.ps1','run.py','finish_review.py','command.json','stdout.raw','stderr.raw','result.json','preparation-attempt.raw','source-checks.json','report.json']
write(R/'EVIDENCE-MANIFEST.json',{'root':str(R),'files':[{'path':n,'sha256':sha(R/n),'bytes':(R/n).stat().st_size} for n in files]})
write(R/'archive-file-list.json',{'root':str(R),'files':files+['EVIDENCE-MANIFEST.json','archive-file-list.json']})
print(json.dumps({'decision':report['decision'],'report':str(R/'report.json'),'report_sha256':sha(R/'report.json'),'archive_file_list':str(R/'archive-file-list.json'),'archive_file_list_sha256':sha(R/'archive-file-list.json'),'manifest_files_verified':len(checked),'passed':pure['passed']}))
