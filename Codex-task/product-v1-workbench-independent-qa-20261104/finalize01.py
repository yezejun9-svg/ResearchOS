from pathlib import Path
import hashlib,json,datetime,re
Q=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
stage=json.loads((Q/'stage01-manifest.json').read_text(encoding='utf-8'))
checks=json.loads((Q/'checks01/results.json').read_text(encoding='utf-8'))
correction=json.loads((Q/'checks02-qa-fixture-correction/result.json').read_text(encoding='utf-8'))
assert correction['exit_code']==0
assert checks['stage_inputs_unchanged']
assert {n:sha(Q/'stage01'/n) for n in stage['files']}=={n:v['sha256'] for n,v in stage['files'].items()}
def summary(path):
    text=path.read_text(encoding='utf-8')
    return {k:int(v) for k,v in re.findall(r'(?:#|\u2139) (tests|pass|fail|cancelled|skipped|todo) (\d+)',text)}
def raw(path):return {'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size}
results={}
for row in checks['commands']:
    folder=Q/'checks01';name=row['phase'];stdout=folder/(name+'.stdout.raw');stderr=folder/(name+'.stderr.raw')
    assert sha(stdout)==row['stdout_sha256'] and sha(stderr)==row['stderr_sha256']
    results[name]={'exit_code':row['exit_code'],'summary':summary(stdout),'stdout':raw(stdout),'stderr':raw(stderr),'command':raw(folder/(name+'.command.json'))}
results['qa-fixture-correction']={'exit_code':correction['exit_code'],'summary':summary(Q/'checks02-qa-fixture-correction/stdout.raw'),
 'stdout':raw(Q/'checks02-qa-fixture-correction/stdout.raw'),'stderr':raw(Q/'checks02-qa-fixture-correction/stderr.raw'),'result':raw(Q/'checks02-qa-fixture-correction/result.json')}
assert results['independent-ui']['summary']=={'tests':14,'pass':11,'fail':3,'cancelled':0,'skipped':0,'todo':0}
assert results['independent-bridge']['summary']['pass']==15
assert results['qa-fixture-correction']['summary']['pass']==3
assert sum(results[n]['summary']['pass'] for n in ['author-ui-replay','author-bridge-replay','legacy-activity-replay'])==40
source=(Q/'stage01/apps/web/src/workbench.jsx').read_text(encoding='utf-8')
block=source[source.index('function NativeHarnessWorkbench('):source.index('function NativeMuWorkbench(')]
send=re.search(r'async function send\(event\) \{[\s\S]*?\n  \}',block).group(0)
events=[
 {'origin_key':'PRODUCT_V1_UI_DRAFT_CLEAR_AFTER_LATE_ACK','classification':'PRODUCT_SOURCE_DEFECT','severity':'P2','attempt_index':1,
  'source':'apps/web/src/workbench.jsx','lines':[453,457,458,469],'source_sha256':stage['source_sha256_exact10']['apps/web/src/workbench.jsx'],
  'exact_extracted_function_sha256':hashlib.sha256(send.encode()).hexdigest(),
  'counterexamples':['submit unresolved -> type new unsent text -> resolve true -> actual draft empty',
                    'submit unresolved -> edit draft and return to original text -> resolve true -> actual draft empty'],
  'expected':'Do not clear any newer edit generation, even when text returns to the originally submitted value; stale/unmounted component must not mutate current draft.',
  'raw_refs':[results['independent-ui']['stdout']],
  'failed_assertions':2,'count_propagation':'Two input variants, one source origin; do not count as two product defects.','status':'OPEN_NEEDS_FIX'},
 {'origin_key':'QA_HARNESS_ACTIVITY_TASKREF_ARGUMENT_MISUSE','classification':'QA_FIXTURE_ERROR','attempt_index':1,
  'cause':'Independent Q02/Q23 test passed Task instead of required TaskRef to harnessActivityRows.',
  'failed_assertions':1,'raw_refs':[results['independent-ui']['stdout']],
  'correction_result':results['qa-fixture-correction'],'status':'CORRECTED_WITH_SOURCE_UNCHANGED',
  'before_test_copy':raw(Q/'checks02-qa-fixture-correction/independent-ui.before-correction.mjs')},
 {'origin_key':'QA_METADATA_OUTPUT_TRUNCATED_JSON_PARSE','classification':'QA_CONTROLLER_DIAGNOSTIC','attempt_index':1,
  'cause':'Initial read printed full276-entry manifest; tool truncation warning made JSON.parse fail. Known read-only action; no write/test ran.',
  'resolution':'Read only manifest metadata/exact freeze fields and separately verify all276 file pins during stage01.',
  'status':'RESOLVED_NO_SOURCE_EFFECT'}]
covered={q:[] for q in [f'Q{i:02d}' for i in range(1,25)]}
for q in ['Q01','Q02','Q03','Q04','Q05','Q06','Q07','Q09','Q10','Q13','Q17','Q18','Q19','Q23']:
    covered[q].append('checks01 independent-ui (Q02 separately corrected, Q19 helper only)')
for q in ['Q01','Q02','Q03','Q04','Q07','Q08','Q09','Q10','Q11','Q13','Q14','Q15']:
    covered[q].append('checks01 independent-bridge mock HTTP/IPC/fresh C journal')
for q in ['Q12','Q16','Q17','Q18','Q19','Q21','Q22','Q24']:
    covered[q].append('Frozen-source/static boundary review; author tests replay where relevant; no real UI qualification.')
covered['Q20']=['Confirmed product source defect via actual extracted frozen send function and controlled Promise.']
report={
 'schema':'researchos.productv1.workbench-independent-review/1','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'reviewer':'codex:/root/workbench_builder','author':'codex:/root/resource_controller_review','revision':'FREEZE01',
 'decision':'NEEDS_FIX','formal_increment':0,'product_acceptance_increment':0,
 'source_base':stage['base_head'],'source_sha256':stage['source_sha256_exact10'],
 'freeze_sha256':stage['freeze_sha256'],'author_manifest_sha256':stage['author_evidence_manifest_sha256'],
 'stage_manifest':raw(Q/'stage01-manifest.json'),'verified_author_evidence_file_count':276,
 'pending_blockers':[{'origin_key':events[0]['origin_key'],'severity':'P2','summary':'Late successful submit clears unsent draft edits; fix with draft-edit revision/lifecycle protection and re-freeze.'}],
 'evidence':results,'diagnostic_events':events,'counterexample_coverage':covered,
 'build':{'independent_build':'NOT_RUN_NOT_NEEDED_TO_REPRODUCE_SOURCE_BLOCKER','author_build':'Vite successful source build is author evidence only; entire276-file evidence manifest verified, no claim of independently rerun build.',
  'real_Electron':'NOT_RUN_ROOT_SEPARATE_SCOPE','model_harness_native':'NOT_RUN_FORBIDDEN_IN_THIS_QA'},
 'static_findings':['Root contractrev2/schema digest matches wire constant. Exact int64 values use decimal strings/BigInt.',
  'Main IPC only exposes typed fixed harness actions; bearer stays in Main request options in tested success/error/journal paths.',
  'Pending journal faults/corruption/restart/NOT_FOUND remain failclosed and do not automatically POST.',
  'Renderer has no V2 session for Harness Tasks; file/diff/write/resume/attachment actions visibly disabled.',
  'Verification and native platform policy displayed separately; can_submit remains Host policy and is not independently equated with verification.',
  'screens.jsx249 keys NativeWorkbench by projectId, excluding the unconfirmed cross-project retained-draft risk.',
  'Old Mu function is retained under the Harness selector; static comparison and40 replayed component checks are not a real Mu execution/UI qualification.'],
 'limitations':['This is source and pure fixture QA; no real HTTP listener/socket, CLI/native/model child, old DB or credential access.',
  'Q19 keyboard helper is tested but real IME/focus/window/narrow-screen behavior is NOT_RUN.',
  'Q21 legacy Mu UI/native execution path has static/component evidence only, not full real flow proof.',
  'Readonly enforcement, actual Codex events/cancel/Windows package/acceptance remain separate Root scopes.',
  'Freeze01 must not be approved or its failed evidence rewritten green. Re-freeze02 needs fresh pins and targeted independent recheck.']}
out=Q/'review01';out.mkdir(exist_ok=False)
for n,v in [('review.json',report),('diagnostics.json',{'diagnostic_events':events,'counter_reset':False,'global_counter_not_modified':True})]:
    with (out/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
text='''# Freeze01 独立UI源码审查：NEEDS_FIX

唯一产品阻断为workbench.jsx453–459：actual send函数在等待提交/GET成功期间允许输入，迟到成功无条件清空当前草稿。两种输入（新文本、编辑后回原文）均实证失败，属于一个P2来源。需draft edit revision/lifecycle保护，而不是仅文本相等。旧freeze10pins保持。

独立UI14项：11通过、2项同源草稿失败、1项QA参数错误；独立mock HTTP/IPC/journal15项通过。QA参数错误纠正后activity窄测3项通过，首轮原始失败与原test完整copy保留。作者UI12+bridge21+旧activity7项重放全通过。

原始输出和精确命令见checks01、checks02-qa-fixture-correction。未运行真实server/Electron/Native/CLI/model、旧DB或认证内容。build不重跑，因为已存在可复现源阻断；作者Vite只作已pin的作者开发证据。真实IME/窄屏、Windows执行/权限/取消均未取得资格。

review.json含exact10 source_sha256、freeze/manifest pins、唯一origin分类与raw hash。decision=NEEDS_FIX，formal_increment=0。修复后必须freeze02再独立重验，不把旧失败改绿。
'''
(out/'REVIEW.md').write_text(text,encoding='utf-8')
files=[]
for f in Q.rglob('*'):
    if f.is_file() and 'runtime' not in f.relative_to(Q).parts and f.name!='EVIDENCE.json':
        files.append({'path':f.relative_to(Q).as_posix(),'sha256':sha(f),'bytes':f.stat().st_size})
with (out/'EVIDENCE.json').open('x',encoding='utf-8') as f:json.dump({'files':files,'file_count':len(files),'source_freeze_sha256':stage['freeze_sha256']},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'decision':'NEEDS_FIX','report':str(out/'review.json'),'review_sha256':sha(out/'review.json'),
 'manifest_sha256':sha(out/'EVIDENCE.json'),'diagnostics_sha256':sha(out/'diagnostics.json'),
 'source_files':10,'product_defect_origins':1,'QA_fixture_error_origins':1,'product_acceptance_increment':0},ensure_ascii=True))
