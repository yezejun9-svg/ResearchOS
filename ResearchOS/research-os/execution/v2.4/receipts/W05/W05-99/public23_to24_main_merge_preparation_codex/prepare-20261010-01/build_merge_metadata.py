from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,difflib,types,collections
O=Path(__file__).parent
R=Path(r'D:/作品集/ResearchOS/research-os')
B=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99')
P=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/public23_to24_root_integration_preparation_codex/prepare-20261010-01')
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p,b=None):
 if b is None:b=p.read_bytes()
 return dict(path=str(p),sha256=sha(b),bytes=len(b))
def write(n,v,text=False):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 raw=v.encode('utf-8') if text else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
 with p.open('xb') as f:f.write(raw)
 return pin(p,raw)
mapref=pin(P/'composition-map.json')
assert mapref['sha256']=='55602273e20c126d1e6485a0ca0223b69be85c2e96f9a101a56342f0a334ea87'
composition=json.loads((P/'composition-map.json').read_bytes())
E=B/'prepared_abandonment_schema_upgrade_source_codex/e841e7fcddaa45ecb115f84df9827af2/MF.json'
epin=pin(E);early=json.loads(E.read_bytes())
targets=composition['proposed_final_files']
assert len(targets)==40
base={}
for tier in composition['tiers']:
 for row in tier['files']:
  rel=row['repo_relative_path']
  if tier['tier']=='PRA4' and row['declared_base_sha256']:
   base[rel]=dict(sha256=row['declared_base_sha256'],evidence_ref=tier['HDF_ref'],
     selector='/source_refs/candidate-root~1'+rel.replace('/','~1')+'/base_sha256')
  if tier['tier']=='Native-v1-lineage' and rel=='apps/control/main.go':
   base[rel]=dict(sha256=row['expected_base_ref']['sha256'],evidence_ref=tier['HDF_ref'],
     selector='/candidate_files/apps~1control~1main.go/previous_ref')
  if tier['tier']=='Q-schema24-revision' and rel=='internal/domain/backup_upgrade_test.go':
   base[rel]=dict(sha256=row['expected_base_ref']['sha256'],evidence_ref=tier['HDF_ref'],
     selector='/source_refs/candidate-root~1internal~1domain~1backup_upgrade_test.go/base_ref')
for rel,row in early['source_refs'].items():
 if row.get('base_ref'):
  actual_rel=rel.removeprefix('candidate-root/')
  base[actual_rel]=dict(sha256=row['base_ref']['sha256'],evidence_ref=epin,
    selector='/source_refs/'+rel.replace('/','~1')+'/base_ref')
for t in composition['handoff_targets']:
 if t['repo_relative_path']=='ops/backup/main.go':
  base[t['repo_relative_path']]=dict(sha256=t['expected_base_ref']['sha256'],
    evidence_ref=mapref,selector='/handoff_targets/1/expected_base_ref')
inputrefs={str(P/'composition-map.json'):mapref,str(E):epin}
absent=[]
for rel,info in targets.items():
 s=Path(info['source_ref']['path']);actual=pin(s)
 assert actual['sha256']==info['source_ref']['sha256'] and actual['bytes']==info['source_ref']['bytes']
 inputrefs[str(s)]=actual
 m=R/rel
 if m.is_file():inputrefs[str(m)]=pin(m)
 else:
  assert not m.exists(),'non-file destination: '+rel
  absent.append(rel)
for item in base.values():
 ref=item['evidence_ref'];p=Path(ref['path']);actual=pin(p)
 assert actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes']
 inputrefs[str(p)]=actual
G=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
raw=G.read_bytes();assert sha(raw)=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
inputrefs[str(G)]=pin(G,raw)
g=types.ModuleType('merge_recipe_guard');exec(compile(raw,str(G),'exec'),g.__dict__)
guard=g.SourceReadGuard(per_file_cap=32*1024*1024,total_cap=256*1024*1024)
guard.acquire(list(inputrefs.values()))
summaries={
'internal/domain/store.go':'仅增加 preparedAbandonmentAuthority 私有字段；现存 CheckMigrationSafety 调用保持原样。',
'internal/domain/runtime_coordinator_windows.go':'恢复路径在锁内识别已 abandonment，Recover 查询排除有 proof 的 dispatch；保留其余恢复处理。',
'internal/domain/backup_migration.go':'固定 inventory 上界23改24；连续版本及 populated DB prebackup 拒绝保持。',
'apps/control/main.go':'在原 fixture/正常启动分派前增加 maintenance 分派；保留原启动路径。',
'internal/domain/backup.go':'组合 Q workspace policy 与 handoff ordinary-public policy 四处检查及固定分支；旧加密、MAC、普通 workspace/protected-ref 检查保持。',
'internal/domain/backup_configuration_upgrade_test.go':'旧schema23 tests使用固定 release23 fixture；保留原期望版本及断言。',
'internal/domain/backup_host_configuration.go':'固定24上界加 exact24 proof-schema 检查；其余<=23路径保持。',
'internal/domain/backup_upgrade.go':'添加固定 PreparedAbandonment 计划分派；原 configuration/queue/旧版本分支保持。',
'internal/domain/backup_upgrade_test.go':'仅version14 fixture Resume调用采用历史helper；其他版本仍用原ResumeCheckpoint。',
'ops/backup/main.go':'增加命令、两个binding flags与API分派；保留旧create/export/restore/upgrade-local。'}
rows=[];at=datetime.now(timezone.utc).isoformat()
try:
 for i,(rel,info) in enumerate(targets.items(),1):
  source=Path(info['source_ref']['path']);src=guard.get_buffer(str(source))
  m=R/rel;current=inputrefs.get(str(m));common=base.get(rel)
  row=dict(repo_relative_path=rel,observed_at=at,current_ref=current,expected_composed_ref=info['source_ref'],
    final_source_layer=info['tier'],root_selected_native_revision='b1599aaf259c435db5a0a5313ab0ea65',
    source_ancestor_evidence=common,source_accepted_by_this_author=False,Main_mutation_performed=False,
    preserve_all_unmentioned_Main_bytes=True,Root_must_recheck_before_apply=True)
  if current is None:
   row.update(action='ADD_ONLY_IF_STILL_ABSENT',requires_3way_now=False,current_matches_declared_base=None,
     existing_Main_divergence=None,changed_ranges=[dict(old_start_line=0,old_line_count=0,new_start_line=1,new_line_count=len(src.splitlines()))],
     root_instruction='确认目标仍不存在后从指定最终Source取字节；若已出现同名文件则停止新增，比较新来源，禁止覆盖。')
  else:
   cur=guard.get_buffer(str(m));assert pin(m,cur)==current
   matches=common is not None and common['sha256']==current['sha256']
   row.update(action='APPLY_PINNED_INCREMENT' if matches else 'THREE_WAY_MERGE_REQUIRED',
    requires_3way_now=not matches,current_matches_declared_base=matches,
    existing_Main_divergence='NONE_RELATIVE_TO_DECLARED_SOURCE_BASE' if matches else 'PRESERVE_ALL_MAIN_SIDE_DIFFERENCES',
    root_instruction='重核current_ref及旧片段hash后只应用此增量；任何漂移先重新建立base/Main/Source三方差异。整文件覆盖不被本建议授权。',
    change_summary=summaries.get(rel,'见逐字节编辑建议。'))
   oldlines=cur.splitlines(keepends=True);newlines=src.splitlines(keepends=True)
   offsets=[0]
   for line in oldlines:offsets.append(offsets[-1]+len(line))
   ops=difflib.SequenceMatcher(a=oldlines,b=newlines,autojunk=False).get_opcodes()
   edits=[];equal=[]
   for tag,a,b,c,d in ops:
    if tag=='equal':
     equal.append(dict(old_start_byte=offsets[a],old_end_byte=offsets[b],sha256=sha(b''.join(oldlines[a:b]))))
     continue
    before=b''.join(oldlines[a:b]);after=b''.join(newlines[c:d])
    edits.append(dict(operation=tag,old_start_byte=offsets[a],old_end_byte=offsets[b],
      old_start_line=a+1,old_line_count=b-a,new_start_line=c+1,new_line_count=d-c,
      old_sha256=sha(before),old_bytes=len(before),new_sha256=sha(after),new_bytes=len(after),
      old_utf8=before.decode('utf-8'),replacement_utf8=after.decode('utf-8')))
   # Pure metadata construction check; no source, product, SQL or runtime execution.
   rebuilt=cur
   for edit in reversed(edits):
    a,b=edit['old_start_byte'],edit['old_end_byte']
    assert sha(rebuilt[a:b])==edit['old_sha256']
    rebuilt=rebuilt[:a]+edit['replacement_utf8'].encode('utf-8')+rebuilt[b:]
   assert rebuilt==src
   stem=str(i).zfill(2)+'-'+rel.replace('/','__')
   diff=''.join(difflib.unified_diff(cur.decode().splitlines(keepends=True),src.decode().splitlines(keepends=True),
     fromfile='a/'+rel,tofile='b/'+rel,n=3))
   patch=write('patch-suggestions/'+stem+'.patch',diff,True)
   editref=write('edit-suggestions/'+stem+'.json',dict(schema='researchos.main24-byte-edit-suggestion.v1',
    repo_relative_path=rel,required_current_ref=current,expected_result_ref=info['source_ref'],
    root_apply_only=True,applied=False,apply_order='descending old_start_byte',edits=edits,
    unchanged_spans=equal,in_memory_reconstruction_equals_source=True,
    note='Byte offsets and SHA guards refer to the exact current snapshot. Patch text is for review; it is not an applied merge.'))
   row.update(patch_suggestion_ref=patch,byte_edit_suggestion_ref=editref,
     changed_ranges=[{k:e[k] for k in ('operation','old_start_line','old_line_count','new_start_line','new_line_count')} for e in edits],
     unchanged_spans_preserved=len(equal),in_memory_reconstruction_equals_source=True)
  rows.append(row)
 for rel in absent:assert not (R/rel).exists(),'Main changed during read: '+rel
 report=write('file-merge-map.json',dict(schema='researchos.main24-file-merge-map.v1',
  status='METADATA_ONLY_PENDING_ROOT_REVIEW',composition_ref=mapref,
  selected_native_revision='b1599aaf259c435db5a0a5313ab0ea65',selected_by='Root explicit task instruction',
  observed_at=at,files=rows,counts=dict(collections.Counter(row['action'] for row in rows)),
  source_controls_replayed=False,Main_Canon_writes=0,Go_build_runtime_Native_SQL_calls=0))
finally:
 closed=guard.close()
close=write('source-guard.closed.json',closed)
assert closed['closed'] and not closed['errors'] and closed['retained_handles_count']==0
counts=dict(collections.Counter(row['action'] for row in rows))
readme=['# Main24 逐文件增量整合建议','',
'状态：METADATA_ONLY_PENDING_ROOT_REVIEW。Root已指定 Native v2 b1599aaf259c435db5a0a5313ab0ea65。本包不修改Main/Canon、不执行Go/build/runtime/Native/SQL，不重放Source controls。','',
'本轮40目标：'+str(counts)+'。10个已有文件均与其Source链声明的原始Main基底同字节，因此本轮没有额外Main侧分叉需要三方解冲突。30个新路径须在Root写入时再次确认不存在。这个结论只适用于observed_at快照，不能覆盖稍后编辑。','',
'每个已有文件提供三种证据：当前ref、最终组合Source ref、祖先基底的HDF/MF指针；并有可逐字节审查的edit JSON及unified patch。edit JSON记录旧范围/旧hash、新文本/hash，以及保留区间，纯内存重建与目标Source同字节。它是未执行的建议，不能作为已合并或已通过运行测试的证据。','',
'Root执行时先重核当前全文件hash，再核每个旧片段hash；按old_start_byte倒序应用增量，保留其他字节。若当前hash改变，不得强行应用或直接覆盖，应先保留新Main全文并重新计算三方差异。新文件若已出现则停止ADD，判断来源。Root实际gofmt后另行记录真实新hash。','',
'先前指南中store保护的表述需精确理解：internal/domain/store.go的CheckMigrationSafety调用在当前Main已存在，本次该文件实际只新增authority字段；版本上界调整属于backup_migration.go。','',
'## 已有文件','',
'| 路径 | 变更位置（当前行） | 增量与保留内容 |','|---|---|---|']
for row in rows:
 if row['current_ref'] is not None:
  ranges=', '.join(str(x['old_start_line'])+('+'+str(x['old_line_count']) if x['old_line_count'] else '(insert)') for x in row['changed_ranges'])
  readme.append('| '+row['repo_relative_path']+' | '+ranges+' | '+row['change_summary']+' |')
readme+=['','## 新文件','', '| 路径 | 最终来源层 | 操作 |','|---|---|---|']
for row in rows:
 if row['current_ref'] is None:readme.append('| '+row['repo_relative_path']+' | '+row['final_source_layer']+' | ADD only if absent |')
readme+=['','完整SHA、bytes、逐路径base证据、差异范围及建议文件ref见file-merge-map.json。Source的四层合成顺序和实际Main23 binding来源沿用已封存配方，不在此重跑。','',
'没有读取密钥、数据库或活动Canon。所有输入句柄已关闭；所有产物位于本包新namespace。','']
guide=write('MERGE_GUIDE.md','\n'.join(readme),True)
inputs=write('input-pins.json',dict(refs=list(inputrefs.values()),absent_Main_paths=[str(R/rel) for rel in absent],observed_at=at))
mf=write('MF.json',dict(schema='researchos.main24-merge-preparation-manifest.v1',
 members=[pin(x) for x in sorted(O.rglob('*')) if x.is_file() and x.name not in ('MF.json','HDF.json','postseal-tool-io.json')],
 excluded=['MF.json','HDF.json','postseal-tool-io.json']))
hdf=write('HDF.json',dict(schema='researchos.main24-merge-preparation-handoff.v1',
 actor_id='codex:/root/attach_restore_independent_review',status='METADATA_ONLY_PENDING_ROOT_REVIEW',
 manifest_ref=mf,merge_map_ref=report,guide_ref=guide,input_pins_ref=inputs,source_guard_ref=close,
 counts=counts,total_paths=len(rows),source_base_matches=sum(x.get('current_matches_declared_base') is True for x in rows),
 selected_native_revision='b1599aaf259c435db5a0a5313ab0ea65',existing_Main_divergences_reverted=0,
 Main_Canon_writes=0,Go_build_runtime_Native_SQL_calls=0,source_controls_replayed=False,
 author_acceptance=False,formal_acceptance=False,execution_grant=False,STOP=True))
print(json.dumps(dict(status='SEALED_METADATA_ONLY',counts=counts,HDF=hdf,MF=mf,merge_map=report,guide=guide,source_guard=close),ensure_ascii=False))

