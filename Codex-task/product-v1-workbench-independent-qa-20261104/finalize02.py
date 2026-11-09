from pathlib import Path
import json,hashlib,datetime,re
Q=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
stage=json.loads((Q/'stage02-manifest.json').read_text(encoding='utf-8'))
prior=json.loads((Q/'review01/review.json').read_text(encoding='utf-8'))
assert stage['inputs_unchanged'] and all(r['exit_code']==0 for r in stage['commands'])
assert {n:sha(Q/'stage02'/n) for n in stage['source_sha256']}==stage['source_sha256']
def raw(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def stats(p):return {k:int(v) for k,v in re.findall(r'(?:#|\u2139) (tests|pass|fail|cancelled|skipped|todo) (\d+)',p.read_text(encoding='utf-8'))}
evidence={}
for r in stage['commands']:
 name=r['phase'];directory=Q/'checks03-freeze02';stdout=directory/(name+'.stdout.raw');stderr=directory/(name+'.stderr.raw')
 assert sha(stdout)==r['stdout_sha256'] and sha(stderr)==r['stderr_sha256']
 evidence[name]={'exit_code':r['exit_code'],'summary':stats(stdout),'stdout':raw(stdout),'stderr':raw(stderr),'command':raw(directory/(name+'.command.json'))}
assert evidence['independent-draft-recheck']['summary']['pass']==9
assert evidence['author-changed-ui-replay']['summary']['pass']==18
out=Q/'review02';out.mkdir(exist_ok=False)
report={'schema':'researchos.productv1.workbench-independent-review/1','revision':'FREEZE02','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'decision':'APPROVED_SOURCE_FIXTURE_ONLY','formal_increment':0,'product_acceptance_increment':0,'pending_blockers':[],
 'reviewer':'codex:/root/workbench_builder','author':'codex:/root/resource_controller_review','source_base':'29f92310a0bdefefbb7c020c792a3565f7b71504',
 'source_sha256':stage['source_sha256'],'freeze_sha256':stage['freeze_sha256'],'manifest_sha256':stage['manifest_sha256'],
 'stage_manifest':raw(Q/'stage02-manifest.json'),'verified_author_evidence_files':110,
 'evidence':evidence,'unchanged_eight_source_evidence':{'previous_review':raw(Q/'review01/review.json'),
  'independent_http_ipc_journal_tests':prior['evidence']['independent-bridge'],
  'previous_independent_ui':prior['evidence']['independent-ui'],
  'qa_fixture_correction':prior['evidence']['qa-fixture-correction'],
  'author_bridge_21_replay':prior['evidence']['author-bridge-replay'],'legacy_activity7_replay':prior['evidence']['legacy-activity-replay'],
  'note':'These exact eight bytes are unchanged. Their checks were not falsely reported as rerun under freeze02.'},
 'source_review':{'changed_paths':stage['changed_since_freeze01'],'actual_send_and_edit_functions_extracted':True,
  'actual_textarea_onChange_extracted':True,'actual_scope_invalidation_executed':True,'actual_effect_cleanup_executed':True,
  'counterexamples':['new unsent text during submit','edit back to submitted text','unchanged draft cleared on success','failure retains newer draft',
    'workspace ABA','project ABA','unmount/Harness switch cleanup','new controller replacement','Welcome function-updater ABA'],
  'conclusion':'Draft edit revision and captured controller identity prevent late clearing. Scope changes and cleanup invalidate old versions. Only the originally untouched draft clears after acceptance.'},
 'diagnostic_events':[
  {'origin_key':'PRODUCT_V1_UI_DRAFT_CLEAR_AFTER_LATE_ACK','classification':'PRODUCT_SOURCE_DEFECT','status':'RESOLVED_BY_FREEZE02_AND_INDEPENDENT_RECHECK',
   'severity':'P2','count_as_new_failure':False,'aliases':['WB-Q20-LATE_ACK-DRAFT'],'first_attempt':raw(Q/'checks01/independent-ui.stdout.raw'),
   'old_decision':'NEEDS_FIX','old_review':raw(Q/'review01/review.json'),'resolution_raw_refs':[evidence['independent-draft-recheck']['stdout']],
   'new_source_sha256':stage['source_sha256']['apps/web/src/workbench.jsx']},
  {'origin_key':'QA_HARNESS_ACTIVITY_TASKREF_ARGUMENT_MISUSE','classification':'QA_FIXTURE_ERROR','status':'CORRECTED_PREVIOUSLY_FIRST_FAILURE_RETAINED','count_as_new_failure':False,
   'first_raw':raw(Q/'checks01/independent-ui.stdout.raw'),'before_test':raw(Q/'checks02-qa-fixture-correction/independent-ui.before-correction.mjs'),
   'correction':raw(Q/'checks02-qa-fixture-correction/result.json')},
  {'origin_key':'AUTHOR_R2_CLEANUP_VM_VISIBLE','classification':'AUTHOR_TEST_FIXTURE_DIAGNOSTIC','status':'AUTHOR_REPORTED_RETAINED','count_as_independent_failure':False,
   'reference':'Author freeze02 manifest110 includes attempt01 source/raw; independent9-test VM provided all actual cleanup dependencies and passed.'}],
 'build':{'independent':'NOT_RERUN_FOR_TARGETED_LOGIC_FIX','author_vite':'Successful author source build pins verified in new110-file evidence manifest; no independent build or real UI claim.'},
 'limitations':['Approval covers reviewed source and pure/mocked fixtures only; all formal journeys remain NOT_RUN.',
  'No real Electron window, HTTP server/socket, Native/CLI/model run, Windows permission enforcement, cancellation qualification or oldDB access.',
  'Real IME/narrow-screen/focus/reduced-motion and actual legacy Mu use still require separately registered Root evidence.',
  'Same can_submit Host policy/verification separation remains; no READY qualification inferred.',
  'No source was modified by QA; Main original tracked changes were not touched.']}
with (out/'review.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
(out/'REVIEW.md').write_text('''# Freeze02 独立复验：APPROVED_SOURCE_FIXTURE_ONLY

实际send/editDraft/textarea onChange/作用域失效和effect cleanup由冻结源码提取，9项定向反例全部通过：新文本、编辑回原文、未编辑成功清空、失败保留、workspace/project ABA、卸载/Harness切换、新controller以及Welcome更新。新作者UI文件18项重放通过。

仅workbench.jsx和UI测试改变，其余8文件字节与freeze01一致；原独立HTTP/IPC/journal15项、旧作者bridge21和activity7证据沿用时明确未重跑。旧freeze01 NEEDS_FIX、两个同源产品失败和QA参数错误的原始源码/raw/hash全部保留，不改绿旧证据。

decision仅源码与纯fixture层批准，pending_blockers为空，formal/product增量0。真实GUI、模型、Windows权限/取消/打包及正式旅程未运行/未接受。review.json提供exact10源pins、新freeze/manifest、raw refs和唯一origin分类。
''',encoding='utf-8')
minimal=[]
fixed=['matrix.json','PREPARATION.md','stage01-manifest.json','stage02-manifest.json','guard.cjs','independent-ui.mjs','independent-bridge.cjs','activity-proof.mjs','draft-recheck02.mjs',
 'stage-ui-qa.py','run-independent.py','activity-check.py','finalize01.py','stage02-and-run.py','finalize02.py']
for n in fixed:minimal.append(Q/n)
for folder in ['checks01','checks02-qa-fixture-correction','checks03-freeze02','review01','review02']:
 for p in (Q/folder).iterdir():
  if p.is_file() and p.name not in ['ARCHIVE_FILES.json']:minimal.append(p)
entries=[{'path':p.relative_to(Q).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(set(minimal))]
with (out/'ARCHIVE_FILES.json').open('x',encoding='utf-8') as f:json.dump({'root':str(Q),'semantics':'Minimal independent QA evidence; excludes stage source copies/cache/runtime fixtures/build dist. Reconstruct stage from pinned author freeze plus baseline dependency manifest if rerunning.',
 'files':entries,'file_count':len(entries),'total_bytes':sum(x['bytes'] for x in entries)},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'decision':report['decision'],'review_path':str(out/'review.json'),'review_sha256':sha(out/'review.json'),'archive_path':str(out/'ARCHIVE_FILES.json'),
 'archive_sha256':sha(out/'ARCHIVE_FILES.json'),'files':len(entries),'bytes':sum(x['bytes'] for x in entries),'independent_tests':9,'author_changed_tests_replay':18,'formal_increment':0},ensure_ascii=True))
