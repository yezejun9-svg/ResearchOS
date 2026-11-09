from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent;T=R.parent.parent
A=T/'product-v1-cli-same-host-caps-prepare-revision-03-20261104'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 assert not p.exists(),str(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert sha(A/'MANIFEST.json')=='09d300b1859b966febfc61d50bb744b9fc357670130d64c07eb59c28ba04e9be'
assert sha(A/'same-host-caps.mjs')=='834ce474f5f62bab79d7908395efec6dbdd57856b2448dd74d71205bdf8a109f'
m=json.loads((A/'MANIFEST.json').read_text())
for row in m['files']:
 p=Path(row['path']);assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
r=json.loads((R/'result.json').read_text());assert r['exit_code']==0 and sha(R/'stdout.raw')==r['stdout_sha256']
prior=R.parent/'revision02/report.json';assert sha(prior)=='96ce69711cf8b2a00612d6c5e04f9ad3d73649ffff2324c8214d469497cd9410'
bind=json.loads((A/'SOURCE_BINDINGS.json').read_text())
write(R/'report.json',{
 'schema':'researchos.independent-source-review.v1','decision':'APPROVED_SOURCE_FIXTURE_ONLY','formal_increment':0,'product_increment':0,'pending_blockers':[],
 'source_sha256':{'same-host-caps.mjs':sha(A/'same-host-caps.mjs')},'manifest_ref':str(A/'MANIFEST.json'),'manifest_sha256':sha(A/'MANIFEST.json'),'freeze_sha256':sha(A/'MANIFEST.json'),'freeze_basis':'Pinned MANIFEST construction_frozen true/source_modification_permitted false','manifest_files_verified':17,'no_drift':True,
 'scope_template_sha256':sha(A/'scope.template.json'),'runtime_authorized':False,
 'findings':[
  {'ref':'same-host-caps.mjs:30','result':'withDerivedSystemDrive runs after the unchanged pinned R04 makeEnvironment, so drive-relative SystemRoot is refused by the composition. Only the explicit Root scope SystemRoot supplies the drive; ambient input is not inherited.'},
  {'ref':'same-host-caps.mjs run','result':'Actual Electron launch cwd is the already-created owned run_root. Fixed Electron binary and app entry remain in sealed build06. Product Core cwd is untouched.'},
  {'ref':'wrapper.diff','result':'Bundle root/manifest/control pins bind build06 71396f9. CLI remains its original 881e26 component with source c4029c0, honestly marked separately; fixed argv only harness caps remains one invocation.'},
  {'ref':'independent pure.mjs','result':'parsePublicCaps and streams/public-output persistence block are byte-identical to approved revision02. Metadata-only hash/count and closed public projection remain; old P2 evidence and failed snapshots are retained.'}
 ],
 'independent_checks':{'case_groups':3,'exit_code':0,'ref':str(R/'result.json'),'command_ref':str(R/'command.json'),'raw_tool_chunk':'7d27b0','stdout_ref':str(R/'stdout.raw'),'stdout_sha256':sha(R/'stdout.raw'),'stderr_ref':str(R/'stderr.raw'),'stderr_sha256':sha(R/'stderr.raw'),'method':'VM-extracted actual R04 environment plus actual drive helper and actual launch fragment with fake launch only; pins/17files and unchanged public parse/output blocks checked. No SDK import or wrapper entry.'},
 'reused_review':{'ref':str(prior),'sha256':sha(prior),'old7cases_rerun':False,'reason':'Exact public parse and persistence bytes unchanged; new checks limited to environment/cwd/build binding.'},
 'build_binding':bind,
 'qualification_limits':[
  'No Electron, CLI, Native, SDK, model, DB/auth/cache or old run state was accessed or launched by this review.',
  'Public caps summary is not full rev2 response or login qualification; only actual caps run can observe the values. CLI/Host runtime compatibility remains unproven until that run.',
  'READY listener race remains fail-closed. App/CLI close and Root original Job accounting are required; no network/pipe PID interception is claimed.',
  'This slice moves Electron cwd only and forwards a derived drive. It is not Core filesystem isolation or a proof of general Windows Shell behavior.',
  'Source qualification does not authorize a consumed-scope retry or real model task. Root must separately register one fresh exact-source caps-only Job scope.'
 ],
 'diagnostic_events':[],
 'carryforward_only':[{'origin_key':'same-host-cli-caps-secret-output-persistence','ref':str(prior),'status':'RESOLVED_SOURCE_FIXTURE_ONLY_IN_REVISION02','count_again':False},{'origin_key':'sealed-bundle-native-shell-cache-missing-systemdrive','status':'Root prior runtime context; old evidence/bundle untouched','count_again':False}],
 'counter_reset':False,'pending_operations':[],'uncertain_outcomes':[]
})
files=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(R.iterdir()) if p.is_file() and p.name not in ['EVIDENCE-MANIFEST.json','archive-file-list.json']]
write(R/'EVIDENCE-MANIFEST.json',{'schema':'researchos.independent-review-evidence.v1','files':files})
write(R/'archive-file-list.json',[v['path'] for v in files]+[str(R/'EVIDENCE-MANIFEST.json')])
D=T/'product-v1-dialog-diagnostic-independent-review-20261104/actual04'
run=T/'product-v1-tree-diagnostic-run-04/receipts';outer=T/'product-v1-owned-verification-20261104/runs/product-v1-tree-diagnostic-04'
paths=[run/'owned-tree-snapshot.json',run/'result.json',run/'owned-core.json',run/'native-folder-automation.json',outer/'RESULT.json',T/'product-v1-build06-post-diagnostic04-root-readback.json']
values=[json.loads(p.read_text(encoding='utf-8-sig')) for p in paths]
snapshot,result,owned,helper,job,bundle=values
tree=[x for x in snapshot['win32_children_when_zero']['controls'] if x['class_name']=='SysTreeView32' and x['visible'] is True and x['enabled'] is True]
core=owned['owned_core_identity'];hr=json.loads(helper['stdout'])
assert snapshot['tree_count']==snapshot['captured_count']==0 and len(tree)==1 and tree[0]['hwnd']=='61803664' and tree[0]['process_id']==snapshot['dialog_owner_pid']==core['pid']==58044
assert helper['exit']==2 and hr['clicked_ok'] is False and hr['ok_attempted'] is False and hr['cleanup']['status']=='OWNED_IDCANCEL_CLICKED'
assert result['actual_dom_submit_attempts']==0 and result['model_outcome']=='NOT_RUN_DIAGNOSTIC_ONLY' and result['close']['app_close_resolved'] is True
assert job['status']=='COMPLETED_OWNED_JOB_STOPPED' and job['stop_proved'] and job['job_active_zero'] and job['root_exit_code']==0 and job['terminate_job_attempts']==job['terminate_original_root_attempts']==0
assert sha(paths[-1])=='8e3c39724171f8eb211bf79aedd90dc8f6c2f5db453ca47a939e05e6d1fef687' and bundle['listed_files_checked']==134 and bundle['listed_changed']==bundle['unlisted']==[]
write(D/'report.json',{
 'schema':'researchos.independent-receipt-readback.v1','decision':'OBSERVATION_CONFIRMED_NOT_PRODUCT_ACCEPTANCE','formal_increment':0,'product_increment':0,
 'inputs':[{'path':str(p),'sha256':sha(p)} for p in paths],
 'confirmed':{'UIA_tree_count':0,'UIA_captured_count':0,'unique_visible_enabled_Win32_tree':tree[0],'owned_core_pid':core['pid'],'dialog_hwnd':snapshot['dialog_hwnd'],'owned_IDCANCEL':True,'OK_attempted':False,'OK_clicked':False,'DOM_submit_attempts':0,'model_outcome':'NOT_RUN_DIAGNOSTIC_ONLY','app_close_resolved':True,'outer_status':job['status'],'outer_exit_code':0,'stop_proved':True,'job_active_zero':True,'forced_termination_attempts':0},
 'bundle_observation':{'basis':'Read existing Root d70254 observation only, not a second hash execution','ref':str(paths[-1]),'sha256':sha(paths[-1]),'listed_files':134,'listed_changed':[],'unlisted':[]},
 'limits':['Unique visible SysTreeView32 metadata is not a proved UIA Tree provider, selected target path, workspace authorization or task readiness.','No runtime tests or new resources were started by this readback. Existing helper exit2 is expected diagnostic termination, not a new product failure.','Actual transport POST count is NOT_INSTRUMENTED. No login, model, full task or general filesystem enforcement qualification is inferred.','Any next native-tree/UIA or product dialog change requires its own reviewed source and fresh run scope. No path guessing or remote pointer message was attempted.'],
 'diagnostic_events':[],'pending_operations':[],'counter_reset':False
})
print(json.dumps({'cli_report_sha256':sha(R/'report.json'),'cli_archive_list_sha256':sha(R/'archive-file-list.json'),'cli_evidence_sha256':sha(R/'EVIDENCE-MANIFEST.json'),'actual04_report':str(D/'report.json'),'actual04_report_sha256':sha(D/'report.json')}))
