from pathlib import Path
import ast,hashlib,json
O=Path(__file__).parent
R=Path(r'D:/作品集/ResearchOS/research-os')
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p,b=None):
 if b is None:b=p.read_bytes()
 return dict(path=str(p),sha256=sha(b),bytes=len(b))
def save(n,v,text=False):
 p=O/n;raw=v.encode('utf-8') if text else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
 with p.open('xb') as f:f.write(raw)
 return pin(p,raw)
env=json.loads((O/'reviewed-source-envelope.json').read_bytes());raw=env['source_utf8'].encode('utf-8')
assert sha(raw)==env['source_ref']['sha256'] and len(raw)==env['source_ref']['bytes']==6820
snapshot=save('reviewed-source.py.txt',env['source_utf8'],True)
tree=ast.parse(raw);lines=raw.decode().splitlines();named={x.name:x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
def loc(needle):
 hits=[i+1 for i,l in enumerate(lines) if needle in l]
 assert hits,needle
 return hits
base=R/'execution/v2.4/receipts/W04/W04-99/integration_codex/revalidation-82783db86d8a4a49a287c371c72f156d/register.py'
b=base.read_bytes();assert sha(b)=='a7cc4305c90209271428d2c95769b515e36a949a1ae13b3d1dc7eef1756cf850' and len(b)==82251
bt=ast.parse(b);bn={x.name:x for x in bt.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
api=R/'execution/v2.4/formal_case_index.py';araw=api.read_bytes();assert sha(araw)=='e08a7f605ca12d79c672b6af0360a02b26e2231d2a602207d0ea6a37f24f7b0b'
runtime=R/'execution/v2.4/receipts/W09/W09-99/full_w09_main_native_producer_source_codex/fullw09-20261010-03/full_w09_runtime.source.py'
rr=runtime.read_bytes();assert sha(rr)=='1709bc96848fb52fe4ddde8591fe063576515aaabdc63d35630b1023a82ccc08'
findings=[
 dict(id='SS-SRC-01',priority='P1',status='BLOCKING',title='Non-SS precheck dependency closure is not held; reference pins are rebound',
 lines=loc("refs=[request_ref")+loc("refs=list(")+loc("api.recheck_inputs"),
 evidence='refs omits check.dependency_snapshot.files, owner evidence, and original_capture_ref returned by actual_audit. recheck_inputs verifies once before archive writes; unheld dependencies can change before SS replace. The comprehension recomputes pin after checked instead of retaining expected input SHA.',
 impact='SS can append an ACCEPTED row after the evidence or Source used by the PASS precheck has drifted. Holding a newly observed hash can conceal a changed expected reference.',
 minimal_fix=['Build a canonical-identity map from exact expected refs, reject conflicting aliases or different SHA for the same file.',
 'Add every dependency_snapshot.files entry except exactly canonical step_state.json, with the recorded SHA and an observed size only after matching that SHA.',
 'Add owner evidence and the actual_audit returned immutable capture refs. Preserve supplied expected digests; do not replace them with fresh pin values.',
 'Hold all these non-SS files through validation, archive, atomic replacement and committed receipt; verify approval/audit/precheck after acquire.',
 'Keep snapshot audit_ranges/inventories validation immediately before commit; validate finite original ranges without deny-write locking the entire actively growing Root audit log.',
 'If closure exceeds guard caps, report a concrete resource-boundary issue; do not silently omit dependencies.']),
 dict(id='SS-SRC-02',priority='P1',status='BLOCKING',title='Original atomic/lock functions are bound to a weaker path resolver',
 lines=loc("def path_in")+loc("env=dict("),
 evidence='The extracted functions use injected local path_in, which resolves links with strict=True and only checks repo containment. Original path_in rejects absolute/drive/traversal/symlink/junction and does not resolve SS into another target.',
 impact='An in-repo linked step_state path can cause atomic_state to replace the resolved different repo file while the receipt claims only_SS_written. A missing original lock also fails strict resolve before writer_lock can create it.',
 minimal_fix=['AST-extract original path_in with Path/PureWindowsPath, Refusal/need, sha and exclusive dependency closure; keep exact original STATE/SCOPE_DIR.',
 'Alternatively use a separately reviewed equivalent that preserves all original path/link checks; do not call the two function AST bodies exact behavioral reuse while weakening their dependencies.',
 'Resolve and verify canonical repo once; validate Root output ancestry link-free and same-volume before invoking these primitives.'])
]
positives=[
 dict(id='EXACT_BASE_AND_TWO_FUNCTION_AST',lines=loc("base_raw=BASE")+loc("tree=ast.parse"),result='PASS_SOURCE',detail='Exact base SHA is checked; actual AST FunctionDef nodes atomic_state/writer_lock are selected and compiled, retaining writer_lock decorator. This does not validate substituted globals.'),
 dict(id='SAME_SERIAL_LOCK_PATH',lines=loc("env=dict("),result='PASS_SOURCE',detail='SCOPE_DIR spells the original W04 serial-writer lock directory; no new W09 lock.'),
 dict(id='APPROVAL_OWNER_BINDING',lines=loc("EXACT_INDEPENDENT_APPROVAL")+loc("MAIN_ACTUAL_PRECHECK")+loc("OWNER_ID"),result='PASS_SOURCE',detail='Exact prospective owner refs and designated actors/statuses are compared to approval and Main precheck.'),
 dict(id='TRUE_APPROVAL_AUDIT',lines=loc("runtime.actual_audit"),result='PASS_SOURCE_WITH_CLOSURE_GAP',detail='Pinned actual_audit authenticates original Root/peer three-record delivery and approval hash; returned immutable capture refs must also be held.'),
 dict(id='CURRENT4_AND_SS_CAS',lines=loc("CURRENT4_ORDER")+loc("FULL_STATE_CAS")+loc("env['atomic_state']"),result='PASS_SOURCE',detail='Exact current4 order/refs, lock-scoped current reread and full SS expected SHA precede atomic replacement.'),
 dict(id='APPEND_ONE_OLD_ROWS_PRESERVED',lines=loc("OWNER_EXISTS")+loc("COMPLETE_INVERSE"),result='PASS_SOURCE_FOR_VALID_JSON',detail='Rejects existing W09-99; deep copy + append + pop inverse preserves old parsed rows/order/top-level metadata. This is semantic preservation, not original serialized layout.'),
 dict(id='ARCHIVE_BEFORE_REPLACE',lines=loc("step_state.before.raw.json")+loc("intent.json")+loc("env['atomic_state']"),result='PASS_SOURCE',detail='Raw original, desired and immutable intent use xb/fsync before atomic replace. Archive original is local, intent before_ref points canonical location plus old SHA; adding the explicit archive ref improves recovery clarity.'),
 dict(id='NO_AUTOROLLBACK',lines=loc("automatic_rollback=False")+loc("postcommit_formal_derivation_pending=True"),result='PASS_SOURCE',detail='No recover or rollback path is invoked. Committed receipt explicitly leaves formal derivation pending. Root postderive failure must retain SS truth and receipts.')]
observations=[
 dict(id='STRICT_JSON',status='RECOMMENDED_HARDENING',lines=loc("req=json.loads")+loc("before=json.loads"),detail='Use original strict/encoded helpers (including math dependency and allow_nan=False) or equivalent for new Root helper. json.loads can collapse duplicate keys; inverse proves preservation only after parsing. Actual canonical precheck should retain its strict validation.'),
 dict(id='POSTCOMMIT_FAILURE_RECEIPT',status='ROOT_OUTER_CONTRACT_REQUIRED',lines=loc("finally:")+loc("committed.json"),detail='This helper has no except block recording failed stage/current hash; guard-close persistence may mask an earlier exception. Root outer caller must preserve original tool exception/result and current SS classification, with no autoRollback. New failure journaling is preferable but must not overwrite the original error.'),
 dict(id='SOURCE_REVIEW_BOUNDARY',status='NOT_RUNTIME_ACCEPTANCE',detail='No request, approval or precheck execution was replayed. The report evaluates fixed Source bytes and pinned dependency implementations, not a future append or actual postderive result.')
]
controls=save('source-review-controls.json',dict(schema='researchos.ss-append-source-review-controls.v1',
 Source_ref=env['source_ref'],AST_parse=True,original_nodes={'atomic_state':[bn['atomic_state'].lineno,bn['atomic_state'].end_lineno],'writer_lock':[1193,bn['writer_lock'].end_lineno]},
 selected_original_functions=[ast.dump(bn[k],include_attributes=False) for k in ('atomic_state','writer_lock')],
 local_path_in_matches_original_AST=ast.dump(named['path_in'],include_attributes=False)==ast.dump(bn['path_in'],include_attributes=False),
 helpers_or_main_executed=False,modules_imported=False,AST_only=True,register_CLI_calls=0,Native_Go_SQL_calls=0,active_Canon_reads_writes=0,Main_source_reads=1,Main_writes=0,formal_review_replays=0))
decision=save('review-decision.json',dict(schema='researchos.ss-append-independent-source-review.v1',
 reviewer_id='codex:/root/attach_restore_independent_review',source_author='codex:/root',reviewed_source_ref=env['source_ref'],
 decision='CHANGES_REQUIRED_BEFORE_ROOT_SS_APPEND',Root_SS_append_source_ready=False,
 blocking_findings=findings,positive_checks=positives,additional_observations=observations,
 actual_authorization_granted=False,formal_acceptance=False,actual_SS_append_executed=False,
 re_review_scope='Only changed dependency closure and primitive path binding plus their exact new Source pin; do not replay successful W09 formal review or Native.'))
report='''# W09 SS 单行追加 helper 非作者 Source 审查

结论：CHANGES_REQUIRED_BEFORE_ROOT_SS_APPEND。审查对象仅为 bf391cd9531988a02b4fbd0f7b43d80f33ae719e0f7bf7e39b0f1f1040d034df / 6820 bytes；不建议 Root 执行这一版本。

两个阻断点：

1. SourceGuard 未持有 Main precheck 的全部非SS依赖、owner evidence和 actual_audit 返回的原始capture。一次 recheck 后还有归档与intent写入窗口；文件可以在替换SS前漂移。refs合并还会重新pin文件，未严格保留输入expected hash。最小修正是按物理身份去重、冲突拒绝，保留expected SHA，完整纳入非SS依赖并持有至提交回执；guard取得后重核批准/audit/precheck。只精确排除将被原子替换的SS。audit_ranges和inventory仍须正确复核，不能锁住整个活跃审计日志来阻止合法追加。
2. 原 atomic_state/writer_lock AST 虽被正确提取，却绑定了本地较弱的 path_in。它会解析link并允许指向仓库内另一文件，使原子替换可能落在该解析目标，同时回执仍宣称only_SS_written；而原path_in拒绝symlink/junction/drive/traversal。最小修正是一并复用原path_in及Refusal/need、exclusive、sha和PureWindowsPath依赖，保持原共享锁路径。

已有正确边界：固定原Source hash；提取FunctionDef保留contextmanager装饰器；指定Backup真实approval audit及exact owner/precheck ref比较；锁内current4与full SS CAS；拒绝既有W09-99；deepcopy追加一行并验证完整逆操作；原始SS/desired/intent先xb+fsync；没有自动回滚；committed明确postcommit derivation pending。以上仅为Source判断。

补充：原行内容保留是JSON语义层面，raw原文已归档。建议使用strict JSON解码并禁止NaN，避免重复键折叠。intent最好直接记录原始归档ref，当前before_ref指向会变动的canonical SS。helper异常只有finally清理；Root外层必须保留原始异常与当前SS真相，不能让清理错误覆盖首次失败，也不能在postderive失败时自动写回original。

本轮只做AST/字节与源码阅读，未导入或运行待审helper、register CLI、formal review、Native/Go/SQL；未读取或修改活动SS/Canon。无需重跑已成功的正式复核；修订后只复核新Source差异和相关metadata边界。
'''
reportref=save('SOURCE_REVIEW.md',report,True)
inputs=save('input-pins.json',dict(refs=[env['source_ref'],pin(base,b),pin(api,araw),pin(runtime,rr)],reviewed_source_snapshot_ref=snapshot))
mf=save('MF.json',dict(schema='researchos.ss-append-review-manifest.v1',
 members=[pin(x) for x in sorted(O.iterdir()) if x.is_file() and x.name not in ('MF.json','HDF.json','postseal-tool-io.json')],
 excludes=['MF.json','HDF.json','postseal-tool-io.json']))
hdf=save('HDF.json',dict(schema='researchos.ss-append-source-review-handoff.v1',
 reviewer_id='codex:/root/attach_restore_independent_review',decision='CHANGES_REQUIRED_BEFORE_ROOT_SS_APPEND',
 reviewed_source_ref=env['source_ref'],manifest_ref=mf,decision_ref=decision,report_ref=reportref,controls_ref=controls,input_pins_ref=inputs,
 blocking_findings=2,Main_Canon_writes=0,helpers_executed=False,Native_Go_SQL_formal_review_calls=0,
 source_acceptance=False,Root_SS_append_source_ready=False,execution_grant=False,STOP=True))
print(json.dumps(dict(status='SEALED_REVIEW',decision='CHANGES_REQUIRED_BEFORE_ROOT_SS_APPEND',HDF=hdf,MF=mf,decision_ref=decision,report_ref=reportref),ensure_ascii=False))

