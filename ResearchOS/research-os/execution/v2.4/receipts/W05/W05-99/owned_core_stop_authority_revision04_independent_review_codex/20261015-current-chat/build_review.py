import datetime,hashlib,json,pathlib
E=pathlib.Path(__file__).resolve().parent
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
def pin(p):
 p=pathlib.Path(p);raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(p,obj):pathlib.Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def build():
 final=read(E/'final-source-check.json')
 captures=[]
 for d in sorted((E/'command-captures').iterdir()):
  if (d/'result.json').exists():captures.append((d,read(d/'result.json')))
 def find_captures(needle):return [pin(d/'stdout.txt') for d,m in captures if any(needle in a for a in m['argv'])]
 cases=[{'artifact':pin(p),'result':read(p)} for p in sorted(E.glob('fixture-e2e-*/case-result.json'))]
 positive=next(x for x in cases if x['result']['mode']=='positive')
 negative=next(x for x in cases if x['result']['mode']=='bad_exit_missing')
 malformed=next(x for x in cases if x['result']['mode']=='review_malformed_effect_preflight')
 assert positive['result']['result']['native']=={'terminate_calls':1,'exit_observed':True,'exit_code':1381191507,'before_signal':False}
 assert positive['result']['result']['postflight']['rows']==35
 assert negative['result']['stop_grant_built']==False and negative['result']['zero_native_signal']
 assert malformed['result']['source_safety_failure_reproduced'] and not malformed['result']['stop_grant_built']
 summaries={
 'internal/host/owned_core_stop_identity_windows.go':'Same-SID public host state and exact schema24/sole OWNER/database identity; no credentials/private keys; reused replacement path and ACL guards.',
 'internal/host/owned_core_stop_identity_windows_test.go':'Current SID/OWNER/schema positive and revoked owner refusal; focused fresh run passed.',
 'internal/ownedcorestop/contract.go':'Only link-time compiled grant, strict canonical base64/JSON, duplicate and unknown fields refused; phase-specific actions, identities, exact seven proof classes, bounded expiry.',
 'internal/ownedcorestop/journal_windows.go':'Retained path components and pinned document bytes; private exclusive operation lock, one immutable claim, no-refund replay/UNKNOWN, inspect does not terminate or repair.',
 'internal/ownedcorestop/journal_windows_test.go':'Exclusive journal and held document tests reviewed; fresh consumed claim/BEGIN/intent/exit boundary tests passed. Synthetic journal cuts are not actual crash or full Commit cancellation.',
 'internal/ownedcorestop/proof_windows.go':'Each class decoded into a fresh receipt; pointer numeric exit/wait fields distinguish zero from absent/null; exact manifest order, subject/identity and authority hashes checked.',
 'internal/ownedcorestop/proof_windows_test.go':'Canonical grant/action tests reviewed; fresh 28 numeric field cuts passed; absent-worker-exit real preflight refused with no STOP grant.',
 'internal/ownedcorestop/stop_windows.go':'Preflight backup and baseline/proof checks; Commit rereads pinned evidence, claims once, reserves writer, compares census, checks safety/authority, durable intent, caller/grant deadline and one retained native signal; postflight real lease+census. SafetySnapshot result is affected by STOP-R4-F01.',
 'internal/ownedcorestop/stop_windows_test.go':'Frozen subject and postflight drift test logic reviewed; fresh caller cancellation boundary passed. Full Commit cancellation after its own durable intent remains unexecuted.',
 'internal/store/owned_stop_backup.go':'Online SQLite backup to exclusive outside-root file, full typed row/schema hashes, closed-file sync/hash, no generic SQL executor exposed. Fresh WAL logical-CAS test passed.',
 'internal/store/owned_stop_backup_test.go':'Nonempty committed WAL preserved in backup and later committed row changes census; fresh run passed.',
 'internal/store/owned_stop_barrier_windows.go':'BEGIN IMMEDIATE writer reservation followed by query_only readback and rollback-only release; closed safety SELECT catalog. Latest extra same-subject MODEL rows with absent/null state escape classification via SQL NULL at lines163-165 (STOP-R4-F01).',
 'internal/store/owned_stop_barrier_windows_test.go':'Existing valid/prepared/started/unknown/other-subject tests omit missing/null state. Fresh reserved/query_only writer test passed; reviewer added 2-case repro and 16-case limited state matrix via read-only overlay.',
 'ops/owned_core_stop/fixture/main_windows.go':'Separate fixture binary, only newly created own schema24 database/public host state/data-root lease/copied native process. No actual product data or model invoked.',
 'ops/owned_core_stop/main_nonwindows.go':'Non-Windows fails STOP_UNAVAILABLE with exit3; reviewed, not executed on this Windows host.',
 'ops/owned_core_stop/main_windows.go':'Exact action flags, no force or caller grant path; bounded caller context, phase dispatch, non-success states exit3.',
 'ops/owned_core_stop/main_windows_test.go':'Argument rejection and controlled crash/WAL/lease tests reviewed; full grant-aware positive executed separately by fresh copied helper+fixture.',
 'ops/supervisor/owned_core_handle_windows.go':'Trusted operator/System/Admin/TrustedInstaller owner set; fail-closed unsupported/malformed ACE; effective allow masks checked, INHERIT_ONLY skipped only on that component; isolated directory append bit; retained no-delete-share ancestors and no-write-share final handle, ID/ACL same-handle recheck, reverse closes. R3-F01 fix supported by fresh native positive/negative tests.',
 'ops/supervisor/owned_core_handle_windows_test.go':'Owner/ACE table, actual copied parent+child, unsafe final/inherited ancestor, reparse/hardlink/wrong-parent/sharing and ACL drift reviewed and freshly exercised with only test TempDir location overlay; native caller cancellation three cases passed.'}
 assert set(summaries)==set(final['source_pins'])
 finding={
 'id':'STOP-R4-F01','severity':'P2','status':'REPRODUCED_SOURCE_DEFECT','title':'额外 MODEL effect 的 state 缺失或为 null 时被安全快照漏计',
 'locations':[{'path':'internal/store/owned_stop_barrier_windows.go','line':163},{'path':'internal/store/owned_stop_barrier_windows.go','line':164},{'path':'internal/ownedcorestop/stop_windows.go','line':119},{'path':'internal/ownedcorestop/stop_windows.go','line':292}],
 'trigger':'原有效 old subject 已有一条 CONFIRMED MODEL effect；同 project/run 另有一个 effect_key 的最新记录 body={"payload":{"capability":"MODEL"}} 或 state:null，且该记录已存在于 preflight 基线。',
 'mechanism':'json_extract(...state) 返回 SQL NULL；NULL IN(...) 与 NULL != CONFIRMED 都不会成为 WHERE 的 true。因此额外行不计入 UnresolvedExternalEffects、NonModelEffects 或 ConfirmedModelEffects，原有 confirmed count 仍为1，ExactOldSubjectSafe 返回true。',
 'observed':'真实24-migration SQLite + reserved writer 两例复现；独立16项有限矩阵仅额外missing/null两项失败。真实 compiled PREFLIGHT_ONLY CLI 将包含此行的87表/36行/quick_check=ok基线标记ELIGIBLE_FOR_INDEPENDENT_REVIEW且missing为空。',
 'impact':'危险/未知effect不能被完整排除却可获得可审查的preflight eligibility。若状态在preflight前已存在，完整baseline hash一致不抵消该遗漏；Commit调用同一catalog，源码上存在相同遗漏。',
 'limits':'未为坏基线编译 STOP grant，未在坏基线执行 Commit 或 native signal；未修改或查询实际产品数据库。不能声称已观察到坏基线的真实停止。',
 'minimal_fix_paths':['internal/store/owned_stop_barrier_windows.go','internal/store/owned_stop_barrier_windows_test.go'],
 'minimal_fix':'对每个最新effect把缺失/null state作为不安全状态计数或显式拒绝，保留当前按effect_key最新sequence选择、唯一CONFIRMED MODEL计数和完整subject绑定。可用显式json_type检查/COALESCE或IS NOT语义，但必须拒绝missing/null并保留异常JSON类型拒绝。',
 'acceptance':'新增missing/null最新额外effect测试；复用有效positive与有限类型/history控制。真实坏基线preflight必须STOP_UNAVAILABLE或更早拒绝，零STOP grant/零native signal；修复者不得改原失败回执。',
 'evidence':[malformed['artifact'],*find_captures('TestReviewMalformedModelEffectMustNotBeSafe'),*find_captures('TestReviewFiniteEffectStateSemantics')]
 }
 limits=[
 'Full live Commit cancellation/expiry after its own durable intent remains unexecuted. Fresh final-native cancellation seam and consumed-journal checks are compositional evidence only.',
 'No actual foreign-user token execution, adversarial concurrent race, power-loss, or exhaustive deeper SafetySnapshot qualification.',
 'Directory GENERIC_WRITE opened successfully in multiple native fixtures. Retained ancestor rename and selected final write/delete/rename/replacement were refused. OPENED is not claimed as replacement success or universal no-write guarantee.',
 'Isolated FILE_ADD_SUBDIRECTORY is accepted only when it is the only unsafe mask bit on that directory ACE. Native selected-path retention, safe-ACL drift and inherited-child refusal support bounded equivalence; trusted operator/elevated OS actors are not adversarially contained.',
 'Historical worker/verifier receipts in CLI fixtures are explicitly synthetic; only own copied Core native signal/wait is freshly observed.',
 'Finite history control confirms latest-sequence behavior; it does not certify all historical audit semantics, malformed JSON encodings, or every safety branch.',
 'No actual Core/DB/API/keys/model/boot proofclass operation or formal acceptance; Root alone may adopt review.'
 ]
 review={
 'schema':'researchos.owned-core-stop-authority-r4-independent-review.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'verdict':'NEEDS_CHANGES','scope':'FULL19_SOURCE_AND_BOUNDED_NATIVE_FIXTURE_REVIEW','owner':'codex:/root/owned_core_stop_r4_review',
 'source_commit':final['head'],'source_tree':final['tree'],'candidate_clean':final['status']=='',
 'review_scope_sha256':'0afab55ca3bd2140bacbd91aca47fa3277ccc51af84475c4d10797c994734d9e',
 'author_final2_manifest_sha256':'9b210bb5dcf65dc34cb21743fc1e5ff8b4209e601b17bc82bf54b9590869516b',
 'full19':[{'path':p,**final['source_pins'][p],'semantic_review':summaries[p]} for p in final['source_pins']],
 'r4_delta_paths':final['delta'].splitlines(),
 'findings':[finding],
 'prior_r3_f01':{'status':'FIX_SUPPORTED_WITH_BOUNDED_NATIVE_EVIDENCE','source_paths':final['delta'].splitlines(),'evidence':['safe copied parent+child, direct Everyone/Users final and inherited ancestor negatives','native D untrusted image installation refused','trusted owner positive/foreign-owner descriptor negative; malformed/unsupported ACE refused','retained ancestor and final handles; final no-write-sharing, rename/remove/overwrite/same-name replacement refused','directory GENERIC_WRITE OPENED preserved, including isolated FILE_ADD_SUBDIRECTORY fixture','effective inherited child ACE refused after INHERIT_ONLY parent accepted','still-authorized changed ancestor/final ACL rejected by same retained handle'],'residual_limits':['No foreign-user execution','No hostile race schedule exhaustion','No universal directory no-write assertion']},
 'prior_required_fields':{'status':'SUPPORTED','numeric_cases':28,'real_missing_exit_preflight':negative},
 'prior_caller_context':{'status':'SUPPORTED_WITH_FULL_COMMIT_INTEGRATION_LIMIT','native_zero_signal_cases':['already canceled','earlier caller deadline','canceled by prewait'],'full_commit_after_own_intent_executed':False},
 'fresh_two_grant_positive':positive,
 'fresh_bad_baseline_preflight':malformed,
 'finite_effect_matrix':{'cases':16,'safe_policy_assertions_failed':2,'controls_matched':14,'failed':['additional null state','additional missing state'],'history_scope':'Only latest sequence per effect_key is catalogued; old history before valid latest is intentionally outside latest-state counts.'},
 'author_nonzero_review':pin(E/'author-nonzero-review.json'),
 'root_author_capture_verification':final['root_author_capture_verification'],
 'fixture_lineage':pin(E/'fixture-lineage.json'),'native_copy_pins':pin(E/'native-copy-pins.json'),'native_acl_snapshot':pin(E/'native-prepositive-acl.json'),
 'test_overlay':pin(E/'overlay.json'),'store_overlay':pin(E/'store-overlay.json'),'independent_extra_test':pin(E/'independent_extra_windows_test.go'),'independent_store_test':pin(E/'independent_store_review_windows_test.go'),
 'fixture_archive':pin(E/'fixture-output-archive.json'),
 'capture_notes':['Initial PowerShell read was garbled; raw output retained and Python UTF8 reread verified scope hash. First two read-only commands predate explicit relevant-env capture.', 'One PowerShell pipe parsing failure occurred outside child logger launch and is retained as shell-launch-diagnostic-001.json; this is an explicit shell capture gap, not a test pass.', 'First D test binary without extra tests was superseded and removed. Source file copies/overlays are reviewer owned; frozen production tree was never edited.', 'Independent store test source was extended by appending the finite state function after the initial two-case run; both functions are retained in final source and raw first/second execution outputs remain separate.'],
 'source_edits':False,'shared_state_edits':False,'actual_authority':False,'formal_increment':0,'parent_acceptance':False,'limits':limits}
 write(E/'review.json',review)
 text=f'''# STOP-r4 独立审查

结论：**NEEDS_CHANGES**。候选 `{final['head']}` / tree `{final['tree']}` 保持干净；全19路径及r4两路径delta与冻结输入一致。r4的owner/ACE修复获得独立支持，但全19检查发现一项新增P2问题，尚不能接受整个候选。

## STOP-R4-F01：额外 MODEL effect 的 state 缺失/null 会被漏计

位置：`internal/store/owned_stop_barrier_windows.go:163-165`，调用点 `internal/ownedcorestop/stop_windows.go:119`、`:292`。

当old subject已有一条CONFIRMED MODEL effect，另一个同project/run effect_key的最新记录为 `{{"payload":{{"capability":"MODEL"}}}}` 或 `state:null`，SQLite `json_extract` 返回NULL。`IN (...)` 和 `!= 'CONFIRMED'` 都不会计入该行，三个effect计数仍表现为0/0/1，`ExactOldSubjectSafe()`误返true。

独立真实schema24 SQLite + reserved writer复现了missing/null两例。16项有限矩阵中仅这两项失败：bool、number、array、object、empty、unknown enum、额外CONFIRMED、capability缺失/null均被拒绝；old-model最新state缺失/null因确认数0被拒绝；更早history被有效最新sequence覆盖，符合当前latest-state设计。

真实compiled PREFLIGHT_ONLY CLI也将坏基线标记 `ELIGIBLE_FOR_INDEPENDENT_REVIEW`，`missing=[]`，基线87表36行、`quick_check=ok`。该用例没有生成STOP grant，没有调用Commit，没有发native signal。完整baseline hash无法识别在preflight之前就存在的分类遗漏；Commit复用同一catalog是源码结论，不是已经执行的坏基线停止。

最小修复路径为 `internal/store/owned_stop_barrier_windows.go` 和 `internal/store/owned_stop_barrier_windows_test.go`：将最新effect的缺失/null state明确计为不安全或拒绝，并保留最新sequence与subject约束。后续须验证坏基线真实preflight拒绝、0 STOP grant、0 native signal，以及原有效正向。

## 已支持的修复和执行证据

- 原STOP-R3-F01：可信owner明确为current operator/System/Administrators/TrustedInstaller；直接/继承的Everyone/Users危险ACE、unsupported/malformed ACE被拒绝。实际copied parent+child安全路径通过，D不可信安装继续拒绝。
- 目录 `GENERIC_WRITE` 实际OPENED事实保留。持有该writer时选定ancestor rename仍被拒绝；final写入、删除、重命名、覆盖及同名替换拒绝。没有把OPENED当作替换成功或宣称目录完全不可写。
- 自加native用例允许孤立FILE_ADD_SUBDIRECTORY，验证选定路径保留；INHERIT_ONLY在parent不生效但传播到final后被拒绝；即使ACL改后仍满足可信策略，ancestor/final同句柄SDDL漂移也被拒绝。
- 原数值native proof修复：28项字段测试通过；真实missing-worker-exit preflight为STOP_UNAVAILABLE且未编译STOP grant。
- Caller ctx/earlier deadline/final prewait取消三项native边界测试通过，durable claim/intent的synthetic journal检查通过。完整Commit在自身durable intent之后被取消仍为未执行的集成边界。
- 自行构建两个不同grant CLI、独立C copied helper+child、D SQLite/data/operation：`STOPPED_LEASE_VERIFIED`，一次TerminateProcess，同一保留句柄观察exit `1381191507`，postflight87表35行且quick_check=ok；inspect/repeat commit结果及journal字节稳定。

全19逐路径语义记录、源码SHA、case及capture引用见 `review.json`。历史worker/verifier凭据在这些用例中明确为synthetic；只有自己的copied Core真实native signal/wait被执行。

## 证据边界和失败保留

作者20个nonzero已逐条读stderr/stdout：4个cross-phase ACTION_DENIED得到独立确认，其余16个历史diagnostic原样保留（包括错误测试期待、路径、编码及harness失败），不抹去中途行为。Root已有22 mixed records（另含初始相邻E和未授权C根偏差），本轮不重新计数。作者后续C data/operation与amendment措辞的歧义单列；本轮data/operation全部位于获准D TMP。

本轮所有失败、父/子命令退出均保存在diagnostic-ledger；一条PowerShell管道解析失败未进入child logger，其捕获缺口明确单列。工具模块/参数问题不是Source测试通过；新增安全断言失败归入STOP-R4-F01，不归为工具diagnostic。

仍未覆盖：foreign-user token实际执行、hostile race穷尽、power-loss、full Commit intent后取消、所有深层SafetySnapshot分支。未碰实际Core/DB/API/keys/model，未新增proof class，未改Source/shared state，formal increment为0。Root单独决定采用，不签发自身接受或实际/正式完成。
'''
 (E/'review.md').write_text(text,encoding='utf-8')
 print('Review content prepared: NEEDS_CHANGES; one reproduced P2; r4 ACL fix supported.')

def seal_after_capture():
 records=[];nonzeros=[]
 for d in sorted((E/'command-captures').iterdir()):
  assert set(p.name for p in d.iterdir())=={'command.json','stdout.txt','stderr.txt','result.json'},str(d)
  m=read(d/'result.json')
  assert hashlib.sha256((d/'stdout.txt').read_bytes()).hexdigest()==m['stdout_sha256']
  assert hashlib.sha256((d/'stderr.txt').read_bytes()).hexdigest()==m['stderr_sha256']
  rec={'ordinal':m['ordinal'],'argv':m['argv'],'cwd':m['cwd'],'native_exit':m['exit_code'],'relevant_environment':m.get('relevant_environment'), 'captures':[pin(d/n) for n in ['command.json','stdout.txt','stderr.txt','result.json']]}
  records.append(rec)
  if m['exit_code']:
   joined=' '.join(m['argv']);err=(d/'stderr.txt').read_text(encoding='utf-8',errors='replace');out=(d/'stdout.txt').read_text(encoding='utf-8',errors='replace')
   if 'STOP_GRANT_ACTION_DENIED' in err:classification='EXPECTED_CROSS_PHASE_DENIAL'
   elif 'additional MODEL effect' in out or 'STOP-R4-F01' in err or 'FINITE_CASE' in out:classification='SOURCE_FINDING_REPRODUCTION_OR_WRAPPER'
   else:classification='REVIEWER_TOOL_DIAGNOSTIC'
   nonzeros.append({'ordinal':m['ordinal'],'native_exit':m['exit_code'],'classification':classification,'argv':m['argv'],'stdout':pin(d/'stdout.txt'),'stderr':pin(d/'stderr.txt')})
 write(E/'command-index.json',{'schema':'researchos.independent-command-index.v1','completed_count':len(records),'records':records})
 write(E/'diagnostic-ledger.json',{'schema':'researchos.independent-diagnostic-ledger.v1','reviewer_nonzero_command_records':len(nonzeros),'records':nonzeros,'reviewer_extra_shell_launch_records':[pin(E/'shell-launch-diagnostic-001.json')],'reviewer_shell_capture_gap_count':1,'source_findings_unique':1,'source_failure_wrapper_records_are_not_separate_defects':True,'author_prior_records':{'nonzero':20,'expected_cross_phase':4,'diagnostic':16,'root_mixed_records':22,'recounted':False},'other_notes':['Initial garbled PowerShell stdout retained, subsequent UTF8 reread passed.','Directory GENERIC_WRITE native OPENED is factual, not a mutation exploit.','No failed attempt deleted or counter reset.']})
 review=read(E/'review.json');review['diagnostic_ledger']=pin(E/'diagnostic-ledger.json');review['command_index']=pin(E/'command-index.json');review['review_md']=pin(E/'review.md');write(E/'review.json',review)
 artifacts=[pin(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='FINAL-manifest.json']
 manifest={'schema':'researchos.independent-review-final-manifest.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':review['source_commit'],'source_tree':review['source_tree'],'verdict':'NEEDS_CHANGES','review_json':pin(E/'review.json'),'review_md':pin(E/'review.md'),'command_index':pin(E/'command-index.json'),'diagnostic_ledger':pin(E/'diagnostic-ledger.json'),'artifact_count':len(artifacts),'artifacts':artifacts,'actual_authority':False,'formal_increment':0,'self_acceptance':False}
 write(E/'FINAL-manifest.json',manifest)
 print('FINAL_MANIFEST_SHA256='+pin(E/'FINAL-manifest.json')['sha256'])
 print('REVIEW_JSON_SHA256='+pin(E/'review.json')['sha256'])
 print('COMPLETED_COMMANDS='+str(len(records))+' NONZERO_COMMAND_RECORDS='+str(len(nonzeros)))

if __name__=='__main__':build()
