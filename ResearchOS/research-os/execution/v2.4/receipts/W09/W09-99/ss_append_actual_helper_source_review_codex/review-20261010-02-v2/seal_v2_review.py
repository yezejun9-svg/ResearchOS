from pathlib import Path
import ast,hashlib,json,textwrap,copy
O=Path(__file__).parent
R=Path(r'D:/作品集/ResearchOS/research-os')
WRAPPER=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/append_w09_owner_v2.source.root.py')
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p,b=None):
 if b is None:b=p.read_bytes()
 return dict(path=str(p),sha256=sha(b),bytes=len(b))
def save(n,v,text=False):
 p=O/n;raw=v.encode() if text else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
 with p.open('xb') as f:f.write(raw)
 return pin(p,raw)
wrapper=WRAPPER.read_bytes()
assert sha(wrapper)=='7a0faabb9dd87fb158c7520f7f44c1f629ec24821b8662ba8a958d9039f03d0d'
v1p=WRAPPER.parent/'append_w09_owner.source.root.py';v1=v1p.read_bytes()
assert sha(v1)=='bf391cd9531988a02b4fbd0f7b43d80f33ae719e0f7bf7e39b0f1f1040d034df'
wa=ast.parse(wrapper)
def literal(n):
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='replace':
  value=ast.literal_eval(n.func.value);args=[ast.literal_eval(x) for x in n.args]
  assert type(value) is bytes and len(args)==2 and not n.keywords
  return value.replace(*args)
 return ast.literal_eval(n)
a=next(n.value for n in wa.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='replacements' for x in n.targets))
replacements=[tuple(literal(x) for x in item.elts) for item in a.elts]
fixed=v1
for old,new in replacements:
 assert fixed.count(old)==1
 fixed=fixed.replace(old,new)
inverse=fixed
for old,new in reversed(replacements):
 assert inverse.count(new)==1
 inverse=inverse.replace(new,old)
assert inverse==v1 and len(replacements)==8
ft=ast.parse(fixed);fl=fixed.decode().splitlines()
effective=save('effective-v2-source.py.txt',fixed.decode(),True)
base=R/'execution/v2.4/receipts/W04/W04-99/integration_codex/revalidation-82783db86d8a4a49a287c371c72f156d/register.py'
br=base.read_bytes();assert sha(br)=='a7cc4305c90209271428d2c95769b515e36a949a1ae13b3d1dc7eef1756cf850'
bt=ast.parse(br);names={'atomic_state','writer_lock','path_in','exclusive','need','sha'}
selected=[n for n in bt.body if (isinstance(n,ast.FunctionDef) and n.name in names) or (isinstance(n,ast.ClassDef) and n.name=='Refusal')]
assert len(selected)==7
main=next(n for n in ft.body if isinstance(n,ast.FunctionDef) and n.name=='main')
envnode=next(n.value for n in main.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='env' for t in n.targets))
keys={x.arg for x in envnode.keywords}
assert {'Path','PureWindowsPath','hashlib','contextmanager','os','uuid','STATE','SCOPE_DIR'}==keys
assert not {'path_in','need','exclusive','sha'} & keys
state=next(ast.literal_eval(x.value) for x in envnode.keywords if x.arg=='STATE')
scope=next(ast.literal_eval(x.value) for x in envnode.keywords if x.arg=='SCOPE_DIR')
assert state=='execution/v2.4/step_state.json'
assert scope=='execution/v2.4/receipts/W04/W04-99/integration_codex/revalidation-82783db86d8a4a49a287c371c72f156d/'
# Only execute the new normalization fragment on synthetic in-memory metadata.
# The wrapper, main, primitive definitions, SourceGuard and product APIs are not executed.
start=next(i for i,s in enumerate(fl) if s.strip()=='refs.extend(audit_refs)')
end=next(i for i,s in enumerate(fl) if s.strip()=='refs=list(normalized.values());out.mkdir()')
fragment=textwrap.dedent('\n'.join(fl[start:end]))+'\n'
fragment_ast=ast.parse(fragment)
allowed_calls={'extend','append','Path','items','checked','dict','str','len','need'}
for n in ast.walk(fragment_ast):
 if isinstance(n,ast.Call):
  name=n.func.id if isinstance(n.func,ast.Name) else n.func.attr
  assert name in allowed_calls,name
fragmentref=save('new-normalization-fragment.py.txt',fragment,True)
V=Path('D:/synthetic-researchos/execution/v2.4')
def ref(path,raw=b'x'):return dict(path=path,sha256=sha(raw),_body=raw)
def need(ok,code,detail):
 if not ok:raise RuntimeError(code)
def checked(r):
 p=Path(r['path']);p=p if p.is_absolute() else V.parent.parent/p
 body=r.get('_body',b'x')
 assert sha(body)==r['sha256']
 return p,body
def run(refs,audit=None,evidence=None,files=None):
 e=dict(refs=copy.deepcopy(refs),audit_refs=copy.deepcopy(audit or []),
 owner={'evidence':copy.deepcopy(evidence or [])},check={'dependency_snapshot':{'files':dict(files or {})}},
 Path=Path,V=V,checked=checked,need=need)
 exec(compile(fragment_ast,'pure-new-metadata-fragment','exec'),e)
 return e['normalized']
results=[]
def record(name,ok):
 assert ok,name
 results.append(dict(name=name,status='PASS_PURE_METADATA'))
normal=run([ref(str(V/'root-request.json'))],
 audit=[ref(str(V/'capture.raw.jsonl'))],
 evidence=[ref('receipts/owner-context.json')],
 files={str(V/'formal_profile_w09.py'):sha(b'x'),str(V/'step_state.json'):sha(b'x')})
record('all_new_nonSS_dependency_groups_included',len(normal)==4 and str(V/'capture.raw.jsonl') in normal and str(V/'formal_profile_w09.py') in normal and str(V/'receipts/owner-context.json') in normal)
record('exact_snapshot_SS_excluded',str(V/'step_state.json') not in normal)
one=run([ref(str(V/'same.json')),ref(str(V/'same.json'))])
record('matching_duplicate_collapses',len(one)==1)
conflict=None
try:run([ref(str(V/'same.json'),b'x'),ref(str(V/'same.json'),b'changed')])
except RuntimeError as exc:conflict=str(exc)
record('conflicting_expected_pins_refused',conflict=='CONFLICTING_EXPECTED_PIN')
ss=None
try:run([ref(str(V/'step_state.json'))])
except RuntimeError as exc:ss=str(exc)
record('SS_in_any_other_group_refused',ss=='EXACT_SS_EXCLUSION')
record('original_expected_SHA_preserved',all(v['sha256']==sha(b'x') for v in normal.values()))
record('guard_capacity_expansion_present',b'per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024' in fixed)
record('self_and_immutable_v1_source_refs_included',b"refs=[pin(Path(__file__).resolve()),pin(S/'append_w09_owner.source.root.py'),request_ref," in fixed)
record('after_acquire_revalidates_approval_owner_precheck_and_audit',fixed.index(b"guard.acquire(refs)")<fixed.index(b"checked(req['approval_ref']);checked(req['prospective_owner_ref']);checked(req['precheck_result_ref'])")<fixed.rindex(b"runtime.actual_audit(")<fixed.index(b"with env['writer_lock'](R):")<fixed.index(b"api.recheck_inputs(check['dependency_snapshot'])"))
record('original_private_path_primitive_binding_restored',len(selected)==7 and not {'path_in','need','exclusive','sha'} & keys)
prior=R/'execution/v2.4/receipts/W09/W09-99/ss_append_actual_helper_source_review_codex/review-20261010-01/review-decision.json'
priorraw=prior.read_bytes();assert sha(priorraw)=='7f05a688d5de8ca56c09dc0bcd911afa26f3a7a9f889fe3b084c63fc31644dfe'
control=save('new-delta-controls.json',dict(schema='researchos.ss-append-v2-delta-controls.v1',
 wrapper_ref=pin(WRAPPER,wrapper),immutable_v1_ref=pin(v1p,v1),effective_source_ref=effective,
 exact_replacements=8,inverse_restores_v1=True,wrapper_AST_parsed=True,effective_AST_parsed=True,
 original_primitive_definitions=[dict(name=n.name,start=n.lineno,end=n.end_lineno) for n in selected],
 selected_environment_keys=sorted(keys),new_synthetic_metadata_controls=results,
 wrapper_or_helper_main_executed=False,primitives_executed=False,SourceGuard_acquired=False,
 product_or_Canon_calls=0,old_v1_positive_controls_replayed=False,negative_controls_are_synthetic_not_actual_failures=True))
decision=save('review-decision.json',dict(schema='researchos.ss-append-independent-source-review.v2',
 reviewer_id='codex:/root/attach_restore_independent_review',source_author='codex:/root',
 decision='APPROVED_SOURCE_FOR_ROOT_SS_APPEND',reviewed_source_ref=pin(WRAPPER,wrapper),
 effective_source_ref=effective,prior_rejection_ref=pin(prior,priorraw),
 scope='Only v2 delta and ten new pure metadata controls; v1 successful components inherited, not replayed.',
 resolved_findings=[
 dict(id='SS-SRC-01',resolution='All snapshot files except exact SS, owner evidence and returned immutable audit refs are held; expected hashes preserved; conflicting expected pins rejected; inputs/audit reread under file guards and current4/snapshot rechecked under serial lock.'),
 dict(id='SS-SRC-02',resolution='Exact seven original definitions are AST-selected, and env no longer substitutes weak path_in/exclusive/need/sha. PureWindowsPath and hashlib supplied; original shared lock path retained.')],
 Root_SS_append_source_ready=True,blocking_findings=[],
 constraints=['Execute exactly pinned wrapper with unchanged pinned v1/base dependencies under existing Root authorization.',
 'Only one previously absent W09-99 row; actual current4/full SS CAS and actual approval/precheck/audit remain runtime gates.',
 'The helper receipt leaves postcommit formal derive pending; Root must obtain actual derive/recheck result before formal closure.',
 'On append/postderive failure preserve true observed state, original/desired/intent and actual tool errors; no autoRollback.',
 'Root caller records primary and secondary errors; prior strict-JSON and archive-ref clarity recommendations remain nonblocking observations of inherited valid-canonical-input flow.'],
 actual_append_executed=False,actual_append_pass_claimed=False,formal_acceptance=False,execution_grant_issued_by_reviewer=False))
report='''# W09 SS append v2 增量独立审查

结论：APPROVED_SOURCE_FOR_ROOT_SS_APPEND，仅绑定 wrapper SHA 7a0faabb9dd87fb158c7520f7f44c1f629ec24821b8662ba8a958d9039f03d0d（3107 bytes）。Root可在既有授权范围内以该版本执行SS单行追加；本审查没有执行追加，也不代表正式接受完成。

v1 bf391 保持原字节。八处替换均唯一命中，逆变完整还原v1；解析得到effective Source SHA 3dc45492e15dcb82e3725002719e05144224e3a86d4b5294505580a08ceeebb1（7802 bytes）。没有执行wrapper末尾exec或任何main。

两项旧阻断已修复：

- 非SS依赖闭合：纳入precheck snapshot.files全部非SS项、owner evidence、actual_audit返回的immutable capture refs，以及v2/v1自身Source。合并保留原expected SHA，冲突拒绝，SourceGuard取得后再核批准/owner/precheck和实际audit；串行writer lock内再核current4与snapshot CAS。每文件256MB、总2GB上限按实声明。
- 原始路径语义：从固定a7cc W04 Source提取Refusal、need、sha、exclusive、path_in、atomic_state、writer_lock七个定义，包含装饰器及PureWindowsPath/hashlib依赖。env不再注入较弱同名替代函数，共用原transition-writer.lock。

只执行十项新增纯metadata控制：依赖分组闭合、精确SS排除、一致重复折叠、冲突hash拒绝、其他分组SS拒绝、expected SHA保留、容量参数、自身Source refs、guard后重核顺序和原始函数绑定。控制仅执行新增normalization片段，输入为内存构造数据；不调用文件读取、SourceGuard、writer lock、atomic_state、formal API或helper main。模拟拒绝是预期控制结果，不是实际执行失败。

沿用已通过且未重跑的v1组件：exact批准/owner/precheck绑定、真实peer原始audit、全SS CAS、旧行完整结构逆操作、原始/desired/intent归档先于替换、不自动回滚。当前SS实际内容未读取。

Root后续必须保存实际调用结果并执行真实postcommit derive/recheck。若失败，已发生的SS改变应原样记录；不得自动回写original。helper committed仍明确formal_derivation_pending，不能用Source批准替代正式结果。
'''
guide=save('SOURCE_REVIEW.md',report,True)
# Confirm immutable review inputs once after this new delta analysis, without replaying old controls.
assert WRAPPER.read_bytes()==wrapper and v1p.read_bytes()==v1 and base.read_bytes()==br
inputs=save('input-pins.json',dict(refs=[pin(WRAPPER,wrapper),pin(v1p,v1),pin(base,br),pin(prior,priorraw)]))
mf=save('MF.json',dict(schema='researchos.ss-append-v2-review-manifest.v1',
 members=[pin(x) for x in sorted(O.iterdir()) if x.is_file() and x.name not in ('MF.json','HDF.json','postseal-tool-io.json')],
 excludes=['MF.json','HDF.json','postseal-tool-io.json']))
hdf=save('HDF.json',dict(schema='researchos.ss-append-v2-source-review-handoff.v1',
 reviewer_id='codex:/root/attach_restore_independent_review',decision='APPROVED_SOURCE_FOR_ROOT_SS_APPEND',
 source_ref=pin(WRAPPER,wrapper),manifest_ref=mf,decision_ref=decision,controls_ref=control,report_ref=guide,input_pins_ref=inputs,
 old_blocking_findings_resolved=2,new_pure_metadata_controls=len(results),Source_ready=True,
 helper_main_executed=False,Canon_reads_writes=0,Native_Go_SQL_formal_review_replays=0,
 actual_SS_append_executed=False,formal_acceptance=False,execution_grant_issued_by_reviewer=False,STOP=True))
print(json.dumps(dict(status='SEALED_SOURCE_APPROVAL',HDF=hdf,MF=mf,decision_ref=decision,controls_ref=control,reviewed_wrapper_ref=pin(WRAPPER,wrapper)),ensure_ascii=False))

