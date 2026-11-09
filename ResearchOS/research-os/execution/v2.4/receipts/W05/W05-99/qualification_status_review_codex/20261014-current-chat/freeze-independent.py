import pathlib,json,subprocess,hashlib,datetime,re
R=pathlib.Path(__file__).resolve().parent;S=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-status-repair-20261014');B='c465d1356480d6e6a90da84656724f9fc02b31c7';C='5ddc0abb8c6d95e9ca071a4eb41a7e12b8559456';T='bfade6fd49897f53e2ec629c71691405be2f2fbe'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=S).decode('utf8').strip()
assert git('rev-parse','HEAD')==C and git('rev-parse','HEAD^{tree}')==T and git('status','--porcelain=v1')==''
inputs=json.loads((R/'inputs/input-census.json').read_text(encoding='utf-8-sig'))
for e in inputs['candidate_inputs']:assert h(S/e['path'])==e['sha256']
logs=[]
for p in sorted(R.glob('*source-bind.*.jsonl')):
 rows=[json.loads(s) for s in p.read_text(encoding='utf8').splitlines()];logs+=rows
assert logs
required=['apps/desktop/main/lib/desktop-management.js','apps/desktop/main/lib/ipc.js']
for name in required:assert any(row['relative']==name for row in logs)
processes={}
for row in logs:processes.setdefault(str(row['pid']),set()).add(row['relative'])
assert len(processes)>=3
assert all(set(required)<=names for names in processes.values())
bind={'root':str(S),'records':len(logs),'test_processes':{k:sorted(v) for k,v in processes.items()},'every_test_process_loaded_changed_management_and_actual_ipc':True,'all_resolved_paths_within_source_and_hash_matched':True}
(R/'source-bind-summary.json').write_text(json.dumps(bind,ensure_ascii=False,indent=2),encoding='utf8')
core=['apps/desktop/main/main.js','apps/desktop/main/lib/ipc.js','internal/host/desktop_management_windows.go','internal/domain/runtime_qualification_confirmation_windows.go']
static=[]
for name in core:
 assert git('rev-parse',B+':'+name)==git('rev-parse',C+':'+name)
 static.append({'path':name,'sha256':h(S/name),'unchanged_git_blob':git('rev-parse',C+':'+name)})
(R/'unchanged-authority-inputs.json').write_text(json.dumps(static,indent=2),encoding='utf8')
for f,n in [('tests.raw.txt',41),('extra-tests.raw.txt',7)]:
 raw=(R/f).read_text(encoding='utf8');assert f'# tests {n}' in raw and f'# pass {n}' in raw and '# fail 0' in raw and '# skipped 0' in raw
for f in ['tests.exit.json','extra-tests.exit.json','build.exit.json']:assert json.loads((R/f).read_text())['native_exit']==0
manifest=json.loads((R/'inputs/manifest.json').read_text(encoding='utf-8-sig'))
for e in manifest['files']:
 if e['path'].startswith('web-dist/'):assert h(R/e['path'])==e['sha256']
p=subprocess.run(['git','-c','core.whitespace=cr-at-eol','diff','--check',B,C],cwd=S,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);assert p.returncode==0
(R/'diff-check.raw.txt').write_bytes(p.stdout);(R/'diff-check.exit.json').write_text(json.dumps({'native_exit':p.returncode}),encoding='utf8')
assert not list(R.glob('independent-fixture-*')) and not (R/'fixture-temp').exists()
report={'schema':'researchos.independent-source-review/1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'codex:/root/attach_review_resume','review_model':'gpt-6-astra','reasoning_effort':'high','verdict':'APPROVE_SOURCE_FIXTURE_SCOPE_ONLY','candidate_commit':C,'candidate_tree':T,'base_commit':B,'scope':'CP456 exact4 original qualification STATUS lifecycle repair','source_root':str(S),'review_root':str(R),'frozen_source_unchanged_before_after':True,'findings':[],'evidence':{'author_manifest_members_verified':20,'source_inputs_verified':33,'source_root_bind_trace_records':len(logs),'test_processes_bound':len(processes),'original_suite':{'tests':41,'pass':41,'fail':0,'skip':0,'native_exit':0,'includes_unmodified_45000ms_timeout':True},'independent_supplement':{'tests':7,'pass':7,'fail':0,'skip':0,'native_exit':0},'frontend_build':{'native_exit':0,'modules':30,'dependency_members_verified_before_after':365,'outputs':3,'byte_identical_to_author_outputs':True},'diff_check_cr_at_eol_native_exit':0},'review_conclusions':[{'topic':'Original selection and asynchronous boundaries','conclusion':'Only eight-field native contexts relax revision/epoch/writer/lease authority fields; original project/session/selectionGeneration and frozen native origin are checked before and after STATUS. Returning to same IDs with a new selection generation remains rejected.'},{'topic':'Principal and host authority','conclusion':'Source inspection confirms unchanged native management obtains bound owner and LocalQualificationStatus resolves exact principal/project/request/hash, current authority root and original OwnerHost. Renderer cannot provide request IDs through actual guarded handlers. This is source inspection, not live principal or Go execution evidence.'},{'topic':'Confirm one-shot and stale context','conclusion':'CONFIRM still requires original exact context and frozen origin, marks confirmSent before dispatch, and cannot be rearmed by consumed=false, ERROR, malformed or timed-out STATUS.'},{'topic':'Historical status display','conclusion':'ORIGINAL_REQUEST_HISTORY is separate from CURRENT_CONTEXT; authorized requires checkedContext equal to original context. Writer changes during a reply and history-to-original transitions do not transfer authorization. Renderer checks authorized rather than old state label.'},{'topic':'Coding continuation gate','conclusion':'A consumed terminal status must be fresh within 10 seconds, nonfuture, not needsRecheck, and same original selection and origin; current coding context/resource and privileged consent checks remain in effect.'}],'current_installed_gui':'NOT_REVALIDATED_OLD_PACKAGE_REMAINS_BLOCKED_PER_PARENT','live_model_qualification':'NOT_PERFORMED','native_current_process_identity':'NOT_OBSERVED_REAL_PROCESSES','formal_increment':0,'formal_case_denominator':42,'all_parents_open':22,'writes':{'source':0,'main':0,'canon':0,'real_database':0,'api':0,'gui':0,'model':0,'review_directory_only':True},'limitations':['Only fixed source, mocked process/IPC fixtures and frontend build reviewed. No claim that installed/running Desktop has this change.','Principal/Owner root enforcement was inspected in unchanged Go source; no real principal, DB, host or API call was exercised.','Native process identities in fixtures are synthetic; genuine identity, original live STATUS, coding configuration and new-model qualification remain separate Root-owned checks.','Existing failure ordinals, old helper/reviews and prior evidence were retained.'],'required_next_step':'Root may perform separately authorized integration/source-bound packaging and normal original-session live revalidation; this review grants no formal or parent acceptance.'}
with (R/'FINAL-report.json').open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
md=f'''# CP456 独立 Source 复核\n\n结论：**APPROVE_SOURCE_FIXTURE_SCOPE_ONLY**。冻结 commit `{C}`，tree `{T}`，base `{B}`；仅授权 exact4 改动，无阻断发现。\n\n独立验证：原 41 项测试与追加 7 项边界测试全部通过，无 skip；native exit 均 0。三个测试进程的 require 解析被强制绑定到冻结 Source 根，每个实际加载了变更后的 desktop-management.js 和原生 IPC handlers。33 个源码输入与 20 个作者证据成员哈希匹配，测试与构建后 Source 保持干净且未变化。365 个前端依赖文件前后哈希匹配；30 模块构建 exit 0，三份产物与作者构建逐字节相同。\n\n复核确认：历史 STATUS 保留原 request/hash/model/context，固定 project/session/selectionGeneration 与 native origin；writer/lease/revision 变化只放宽只读复核。CONFIRM 保留严格原 context 和一次性 confirmSent。ERROR、malformed、timeout 与 consumed=false 不会重新允许确认。checkedContext 防止历史结果转成当前 authorized；UI 明确标记历史状态。Coding 继续要求 consumed terminal、10 秒内且非未来的成功复核、原选择/origin，以及当前 coding context/resource 和 privileged consent 检查。\n\n原生 principal、Owner root 和 OwnerHost 约束在未变更的 Go 路径中核对；未执行真实 Go authority/DB/API 验证。当前旧安装包 GUI 仍按父任务记录为 blocked，本轮未打开或操作它。真实原请求 STATUS、新 coding/model-ref/qualification 和 native 过程证据仍未验证。正式增量 **0/42**，全部 **22 个父任务保持 open**。本报告不构成产品验收。\n\n源目录、Main、Canon、真实数据库、API、GUI 和模型调用改动均为 0。所有审查产物仅写入本独立 review 目录；临时 fixture 已清理。此前 helper/reviews 未改动。\n'''
with (R/'REPORT.md').open('x',encoding='utf8') as f:f.write(md)
files=[]
for p in sorted(R.rglob('*')):
 if p.is_file() and p.name!='manifest.json':files.append({'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':h(p)})
# The copied author manifest is an input and must be a member too.
p=R/'inputs/manifest.json';files.append({'path':'inputs/manifest.json','bytes':p.stat().st_size,'sha256':h(p)})
files.sort(key=lambda e:e['path'])
with (R/'manifest.json').open('x',encoding='utf8') as f:json.dump({'schema':'researchos.independent-evidence-manifest/1','candidate_commit':C,'candidate_tree':T,'files':files},f,ensure_ascii=False,indent=2)
print(json.dumps({'verdict':report['verdict'],'report_sha256':h(R/'FINAL-report.json'),'manifest_sha256':h(R/'manifest.json'),'members':len(files),'bound_test_processes':len(processes),'trace_records':len(logs)}))
