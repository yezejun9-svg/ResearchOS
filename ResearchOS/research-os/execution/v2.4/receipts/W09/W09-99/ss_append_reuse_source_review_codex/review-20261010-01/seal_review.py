from pathlib import Path
import ast,hashlib,json
O=Path(__file__).parent
S=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W04/W04-99/integration_codex/revalidation-82783db86d8a4a49a287c371c72f156d/register.py')
R=Path(r'D:/作品集/ResearchOS/research-os')
def digest(b):return hashlib.sha256(b).hexdigest()
def pin(p,b=None):
 if b is None:b=p.read_bytes()
 return dict(path=str(p),sha256=digest(b),bytes=len(b))
def save(n,v,text=False):
 p=O/n
 raw=v.encode() if text else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
 with p.open('xb') as f:f.write(raw)
 return pin(p,raw)
raw=S.read_bytes()
assert digest(raw)=='a7cc4305c90209271428d2c95769b515e36a949a1ae13b3d1dc7eef1756cf850' and len(raw)==82251
text=raw.decode('utf-8');tree=ast.parse(text);lines=text.splitlines(keepends=True)
nodes={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
names=['Refusal','need','sha','exclusive','path_in','atomic_state','writer_lock']
imports=['import hashlib','import os','from pathlib import Path, PureWindowsPath','from contextlib import contextmanager','import uuid']
constants={}
for node in tree.body:
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('BASE','SCOPE_DIR','STATE'):
  constants[node.targets[0].id]=ast.get_source_segment(text,node)
snippets=[];selected=[]
for name in names:
 node=nodes[name];first=min([node.lineno]+[x.lineno for x in getattr(node,'decorator_list',[])])
 fragment=''.join(lines[first-1:node.end_lineno])
 snippets.append(fragment)
 selected.append(dict(name=name,start_line=first,definition_line=node.lineno,end_line=node.end_lineno,
   sha256=digest(fragment.encode()),bytes=len(fragment.encode()),
   loaded_names=sorted({x.id for x in ast.walk(node) if isinstance(x,ast.Name) and isinstance(x.ctx,ast.Load)})))
minimal='\n'.join(imports)+'\n\n'+'\n'.join(constants[x] for x in ('BASE','SCOPE_DIR','STATE'))+'\n\n'+'\n\n'.join(snippets)
ast.parse(minimal) # source syntax only; never exec/import the extracted helper.
snippetref=save('minimal-reuse-source.py.txt',minimal,True)
lock_rel='execution/v2.4/receipts/W04/W04-99/integration_codex/revalidation-82783db86d8a4a49a287c371c72f156d/transition-writer.lock'
deps=save('dependency-contract.json',dict(schema='researchos.ss-append-reuse-dependencies.v1',
 source_ref=pin(S,raw),selected_nodes=selected,minimal_imports=imports,local_runtime_import='msvcrt inside writer_lock on Windows only',
 constants=constants,exact_lock_relative_path=lock_rel,exact_lock_absolute_path=str(R/lock_rel),
 target_relative_path='execution/v2.4/step_state.json',
 runtime_preconditions=['Windows os.name == nt','Root locked Python with pathlib.Path.is_junction support',
  'repo is the actual resolved canonical ResearchOS repository Path',
  'Root-authorized, unique, link-free output directory on same volume as step_state.json',
  'all cooperating SS writers use this identical physical lock; no alternate W09 lock',
  'caller closes SS file read handles that deny delete before os.replace'],
 excluded_W04_specific_entrypoints=['full_state_cas','apply','recover','main','parser','cli_ref','Audit','RESOLVER'],
 excluded_reason='full_state_cas/apply/recover encode W04-99 row replacement and W04 authorization; CLI also uses W04 scopes.',
 extracted_functions_executed=False,register_module_imported=False,writer_lock_acquired=False,atomic_state_called=False))
sequence=[
 dict(order=1,phase='PREPARE_READONLY',requirements=['Pin this exact helper source and selected dependency code.',
 'Verify actual Root scope, unique output directory, real new W09 row and actual review/derive input references outside these low-level primitives.',
 'Require expected SHA of the entire current SS supplied by the reviewed plan, not only W09 row or a row count.',
 'Use caller current actual timestamps and refs; no future acceptance or placeholder references.']),
 dict(order=2,phase='ACQUIRE_COMMON_LOCK',requirements=['Enter the exact extracted writer_lock(repo).',
 'Do not create a different lock in W09 output. Do not delete/recreate the existing lock file.',
 'Busy LK_NBLCK exception is a failed attempt, not permission to retry silently.',
 'Keep this lock through current read, archive, CAS, readback, derive/recheck and outcome persistence.']),
 dict(order=3,phase='READ_AND_VERIFY_BASE',requirements=['Read current full SS raw bytes under the lock; compare SHA to reviewed expected_full_state_sha256.',
 'Strictly parse JSON rejecting duplicate keys/nonfinite numbers. Require steps list and unique existing step ids.',
 'Require no existing W09-99 row for this one-row append contract. Existing W09-99 requires a separate reviewed contract, never upsert or remove.',
 'Validate new row exact shape/evidence externally and enforce id=W09-99.',
 'Any unrelated SS change is a failed full-file CAS and needs a new plan.']),
 dict(order=4,phase='CONSTRUCT_APPEND_ONLY',requirements=['Deep-copy original document and set desired.steps = original.steps + [new_row].',
 'Require desired.steps[:-1] == original.steps, desired.steps[-1] == new_row, len(desired.steps) == len(original.steps)+1.',
 'Require every non-steps top-level key/value unchanged, same top-level key set, same old row order and entire old nested row objects.',
 'Serialize desired once. These are semantic preservation checks; raw original bytes are separately archived exactly.',
 'Do not infer old row byte layout survives JSON reserialization. If exact formatting preservation is required, use an independently reviewed serializer.']),
 dict(order=5,phase='ARCHIVE_BEFORE_MUTATION',requirements=['Use exclusive(path,raw), never overwrite, to write full SS original bytes, desired bytes, and exact new-row bytes.',
 'Each archive is flush+fsync before returning; pin SHA/bytes and verify readback.',
 'Write an immutable pending intent binding target, actor, scope/authorization refs, expected before SHA, desired after SHA, archive refs, new-row SHA and no-auto-rollback policy.',
 'All archives and pending intent must exist before atomic_state; their failure means do not invoke it.']),
 dict(order=6,phase='FULL_BYTES_CAS_REPLACE',requirements=['While still holding common lock, call atomic_state(repo, expected_full_state_sha256, desired_raw, out).',
 'It first creates/fsyncs a unique out/atomic-payload-UUID.tmp; then re-reads current SS and checks expected full SHA.',
 'On match it calls os.replace(temp, SS) and checks complete SS readback hash against desired.',
 'This is check-then-replace plus cooperating lock, not a kernel hash-conditional replace.',
 'Source provides no directory fsync or power-loss guarantee; do not claim crash-durable transaction.']),
 dict(order=7,phase='VERIFY_ACTUAL_STATE',requirements=['Read actual full SS again under lock and require exact desired bytes/hash.',
 'Strictly parse actual and repeat all-old-rows/prefix/top-level equality, one new W09 row and exact new row checks.',
 'Save actual after-image or readback receipt with observed hash and timestamps. Do not claim acceptance merely because replace returned.']),
 dict(order=8,phase='POST_DERIVE_AND_RECHECK',requirements=['Run only separately authorized current Main formal derive/check against actual new SS and real current evidence; this review does not execute them.',
 'Persist full returned result, inspect W09/C19/A06 according to current contract and keep all old owner rows/results.',
 'Recheck dependency snapshot and exact current desired SS after derive.',
 'Only after successful postconditions write a completion/commit receipt; construction does not self-sign independent acceptance.']),
 dict(order=9,phase='PERSIST_OUTCOME_AND_RELEASE',requirements=['Persist the actual success or failure while retaining original, desired, pending intent and tool observations.',
 'If failure persistence itself fails, preserve original error and report secondary error separately through actual tool result.',
 'Exit common lock in finally; source seeks0 and unlocks1 byte; do not delete lock file.'])
]
seq=save('append-cas-sequence.json',dict(schema='researchos.ss-one-row-append-contract.v1',
 status='SOURCE_REUSE_RECOMMENDATION_PENDING_ROOT_REVIEW',sequence=sequence,
 expected_full_state_sha256=None,new_W09_row_ref=None,actual_prederive_ref=None,actual_postderive_ref=None,
 execution_grant=False,old_rows_may_be_replaced=False,automatic_rollback=False))
failure=save('failure-contract.json',dict(schema='researchos.ss-append-failure-contract.v1',
 phases=[
 dict(where='before os.replace',canonical_effect='No write by this attempt; other writers or outsiders may still have changed SS.',action='Record failure/current hash; keep original/desired/intent/temp; do not rerun automatically.'),
 dict(where='os.replace raises or process terminates around replace',canonical_effect='Determine from actual readback, never infer unchanged solely from exception.',action='Record observed current hash if readable; UNKNOWN if not. No automatic rollback.'),
 dict(where='READBACK_HASH / row checks / derive / dependency recheck fails after replacement',canonical_effect='SS may already equal desired, or may have foreign bytes; applied state is distinct from accepted state.',action='Keep actual SS, archive/intent/results and failure. Do not call W04 recover or write original over SS.'),
 dict(where='completion receipt fails after actual derive succeeds',canonical_effect='SS and derive observation remain real but durable closure is incomplete.',action='Keep actual results; report incomplete closure and secondary persistence error, no manufactured completed marker.')
 ],
 observed_state_classes=['MATCHES_ORIGINAL','MATCHES_DESIRED','FOREIGN_HASH','UNREADABLE_UNKNOWN'],
 recovery_rule='Only a separately authorized explicit Root recovery with current own-write full-hash CAS can change state later. Never autoRollback.',
 source_evidence_lines=[{'start':1261,'end':1269,'claim':'original W04 main has no silent postcommit rollback'},
 {'start':996,'end':1027,'claim':'W04 recover is a separate explicit phase and is not reusable W09 append authorization'}]))
md='''# SS 单行追加：现有函数复用审查

状态：SOURCE_REUSE_RECOMMENDATION_PENDING_ROOT_REVIEW。未调用原 register 模块、CLI、writer_lock 或 atomic_state；未读取或修改当前 SS、Main、Canon、密钥，未执行 Go/Native 或重跑测试。

只需复用 Refusal、need、sha、exclusive、path_in、atomic_state、writer_lock 七个定义，加 hashlib/os/uuid、Path/PureWindowsPath、contextmanager 和 BASE/SCOPE_DIR/STATE 三个常量。精确源码片段和行号见 dependency-contract.json 与 minimal-reuse-source.py.txt。writer_lock 的 @contextmanager 装饰器在1193行，不能只抄1194起而遗漏装饰器。片段只做AST语法解析，未执行。

## 锁路径与 Windows 语义

必须使用原路径：
execution/v2.4/receipts/W04/W04-99/integration_codex/revalidation-82783db86d8a4a49a287c371c72f156d/transition-writer.lock

原函数仅在文件不存在时用 xb 创建 b"0"；已有时沿用。它以 r+b 打开，检查首字节为 b"0"，seek(0)，用 msvcrt.LK_NBLCK 锁偏移0的一字节。busy直接抛异常，函数没有自动等待/重试。yield期间保留句柄，finally再seek(0)并LK_UNLCK，随后关闭句柄。它只检查首字节，不要求总长度恰好1；不要把实现描述成全文件格式校验。

这个锁串行化遵守同一锁文件的writer。它不锁SS文件本身，不能阻止不遵守协议的写入，也没有调用方身份认证。另建W09锁会失去与原writer的串行关系。不要删除/recreate锁文件。

## 原子替换边界

atomic_state 987–993本身不获取锁：创建并fsync临时payload→读取SS计算full SHA比较expected→os.replace→读取完整SS验证desired SHA。Root必须在同一writer_lock作用域内调用。out必须在SS同一volume、属于Root本次独占可写且link-free目录，repo须预先resolve到真实canonical根。路径检查复用path_in的穿越/drive/symlink/junction拒绝；这不代替Root身份和scope检查。

这是全文件哈希检查加cooperating writer lock，不是内核提供的hash条件替换。exclusive fsync了临时内容，但atomic_state没有目录fsync，因此不能宣称掉电持久化事务。保留归档和pending intent以供明确恢复。若有deny-delete的SS读句柄，调用方须先关闭，否则replace可能失败。

## 归档、追加与CAS

append-cas-sequence.json给出九阶段顺序。先取得共同锁，再读取并校验最新full SS raw SHA，严格JSON解析并确认W09-99尚不存在。构造desired.steps=old.steps+[new_row]；全部旧行嵌套内容、顺序与其他顶层字段保持，长度只增加1。不能调用硬编码W04-99替换的full_state_cas/apply/recover，也不能upsert已有W09行。

将原始SS bytes、desired bytes、new row bytes及绑定这些文件的pending intent用exclusive归档并核验后，才调用atomic_state。原始bytes归档保持逐字节；JSON重新序列化只能保证旧行语义相同，不能宣称旧文本格式不变。替换后重复完整bytes、行前缀和顶层字段检查，再执行另行授权的当前正式derive与依赖recheck。真实postderive结果、最终SS hash及接受判断必须来自未来实际调用，此处均留空。

## 替换后失败

postderive失败不会使已发生的SS写入消失。保持实际SS、原始/desired归档、pending intent、真实错误与结果，不自动调用recover或写回original。失败回执区分MATCHES_ORIGINAL、MATCHES_DESIRED、FOREIGN_HASH、UNREADABLE_UNKNOWN；不要因replace抛错而推定未改动。只有后续另行授权的显式Root恢复能在当前own-write full-hash CAS成立时进行。原W04 main1261–1269也明确禁止静默postcommit rollback。

这份审查只确认最小函数复用与新增append合同所需边界，不授予W09追加执行或独立接受。
'''
guide=save('REUSE_REVIEW.md',md,True)
check=save('ast-review.json',dict(source_sha256=pin(S,raw)['sha256'],source_bytes=len(raw),selected_definition_count=len(names),
 atomic_state_lines=[nodes['atomic_state'].lineno,nodes['atomic_state'].end_lineno],
 writer_lock_lines_including_decorator=[1193,nodes['writer_lock'].end_lineno],
 AST_only=True,source_module_imported=False,extracted_functions_executed=False,tests_replayed=False,
 lock_or_canonical_file_opened=False,source_unchanged=(S.read_bytes()==raw)))
assert json.loads((O/'ast-review.json').read_bytes())['source_unchanged']
mf=save('MF.json',dict(schema='researchos.ss-reuse-review-manifest.v1',
 members=[pin(x) for x in sorted(O.iterdir()) if x.is_file() and x.name not in ('MF.json','HDF.json','postseal-tool-io.json')],
 excludes=['MF.json','HDF.json','postseal-tool-io.json']))
hdf=save('HDF.json',dict(schema='researchos.ss-reuse-source-review-handoff.v1',
 actor_id='codex:/root/attach_restore_independent_review',status='SOURCE_REUSE_RECOMMENDATION_PENDING_ROOT_REVIEW',
 source_ref=pin(S,raw),manifest_ref=mf,guide_ref=guide,dependency_contract_ref=deps,
 minimal_source_ref=snippetref,append_sequence_ref=seq,failure_contract_ref=failure,AST_review_ref=check,
 Main_Canon_writes=0,register_CLI_calls=0,Go_Native_build_runtime_calls=0,tests_replayed=False,
 actual_SS_read=False,execution_grant=False,formal_acceptance=False,STOP=True))
print(json.dumps(dict(status='SEALED_SOURCE_REVIEW',HDF=hdf,MF=mf,guide=guide,dependencies=deps),ensure_ascii=False))

