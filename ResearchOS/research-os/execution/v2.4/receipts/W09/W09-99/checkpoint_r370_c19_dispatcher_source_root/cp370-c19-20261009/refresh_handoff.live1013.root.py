"""Update the resume pointer while retaining the complete historical handoff."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, subprocess, sys, types

R=Path(r'D:\作品集\ResearchOS\research-os')
N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99'
W=R/'execution/v2.4/receipts/W09/W09-99'

def pin(p):
    raw=p.read_bytes();return dict(path=str(p.resolve(strict=True)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def write(p,raw):
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return pin(p)

def save(p,v):return write(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))

resume_ref=pin(N/'RESUME.cp370-consumers-qualified.live1013.root.json')
assert resume_ref['sha256']=='38e8633ef8796e3f59663d8fa2464b33155d623112fc1fc5e26a8cb6bf3158ac' and resume_ref['bytes']==6145
resume=json.loads(Path(resume_ref['path']).read_bytes())
canonical=resume['canonical_refs']
assert [pin(Path(ref['path'])) for ref in canonical]==canonical
trial=B/'original_provider_trial_reconciliation_readonly_codex/a9e17af6e5cd42fd997f2cb9c6510f32'
gap=W/'full_w09_native_gap_source_review_codex'
extra=[]
for folder,name,sha,size in [
    (trial,'HDF.json','0b6ab9ae3e70f3e78c3f99fad5110606ef35fb403967b1a9c9e457abac97ca6c',4807),
    (trial,'MF.json','87dd9547170221e166462994e61005fecc183f5b0649a9b22e95b46d9788f28e',6668),
    (trial,'decision.json','3e2d883a3cdc8d0748dcbf4e23b23d70a16dd0ed014aee98010692046ee1215c',5685),
    (gap,'HDF.json','14badf1560e4f919f88901b9c6258508b38db49903675d596a0ffbb8f0139c08',2119),
    (gap,'MF.json','d20a939c7074e41610df60c007af50a3850f2e6460350673b5a53291971b9207',13275),
    (gap,'Source-gap-report.json','9b7bb0a54314560e285f5245d95d0ce44cb5c2510c31ef5bff3996f1602e93e5',73083)]:
    ref=pin(folder/name);assert ref['sha256']==sha and ref['bytes']==size;extra.append(ref)
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
gr=pin(gp);assert gr['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85' and gr['bytes']==11404
gm=types.ModuleType('root_handoff_guard');gm.__file__=str(gp);sys.modules[gm.__name__]=gm
exec(compile(gp.read_bytes(),str(gp),'exec'),gm.__dict__)
handoff=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';old_ref=pin(handoff)
refs=[*canonical,resume_ref,resume['identity_ref'],old_ref,*extra,gr]
guard=gm.SourceReadGuard(per_file_cap=32*1024*1024,total_cap=128*1024*1024)
try:
    guard.acquire(refs)
    old_raw=guard.get_buffer(old_ref['path'])
    documents=[json.loads(guard.get_buffer(ref['path'])) for ref in canonical]
    def protected(value):
        if isinstance(value,dict):
            raw=value.get('path')
            if isinstance(raw,str) and value.get('sha256'):
                candidate=Path(raw) if Path(raw).is_absolute() else R/raw
                if candidate.resolve()==handoff.resolve():return True
            return any(protected(child) for child in value.values())
        if isinstance(value,list):return any(protected(child) for child in value)
        return False
    is_protected=any(protected(doc) for doc in documents)
finally:closed=guard.close()
assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
guard_ref=save(N/'handoff-source-guard.live1013.closed.root.json',closed)
original_handoff=write(N/'historical.HANDOFF_RESUME_PACK.before-cp370-update.md',old_raw)
git_observations=[]
for label,args in [('head',['rev-parse','HEAD']),('branch',['branch','--show-current']),('status',['status','--porcelain=v1','-z','--untracked-files=normal'])]:
    result=subprocess.run(['git',*args],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=45)
    stdout_ref=write(N/('git-'+label+'.live1013.stdout.raw'),result.stdout)
    stderr_ref=write(N/('git-'+label+'.live1013.stderr.raw'),result.stderr)
    git_observations.append(dict(argv=['git',*args],cwd=str(R),actual_exit=result.returncode,stdout_ref=stdout_ref,stderr_ref=stderr_ref))
    assert result.returncode==0,'GIT_READ_ONLY_OBSERVATION_FAILED'
    if label=='head':head=result.stdout.decode('ascii').strip()
    if label=='branch':branch=result.stdout.decode('utf-8').strip()
    if label=='status':status_raw=result.stdout
assert head=='adc460c2138528f163f7fdab5e8d81dde157b7fb' and branch=='main'
items=[entry.decode('utf-8',errors='strict') for entry in status_raw.split(b'\0') if entry]
deletions=[entry[3:] for entry in items if entry.startswith(' D ') or entry.startswith('D  ')]
summary=save(N/'git-baseline.live1013.root.json',dict(schema='researchos.root-git-baseline.v1',
    issued_by='codex:/root',created_utc=datetime.now(timezone.utc).isoformat(),head=head,branch=branch,
    git_read_only_observations=git_observations,status_record_count=len(items),tracked_deletion_paths=deletions,
    status_scope='porcelain-v1-z with normal grouped untracked directories',reset_clean_stage_commit_push_performed=False))
text='''# ResearchOS v2.4 — R370 当前续跑入口

当前 Goal 为 ACTIVE。当前正式用例接受数为 0/42；6 个父任务记录是历史状态，22 个父任务仍须逐项核对当前有效接受。

Canon 为 checkpoint R370、ownership R174、commands R39。Root 最新原始异常序号入口为 1013；1005–1012 已逐条保存到新的 pending diagnostics，尚未登记进 Canon。未知退出码和费用保留 null，不重置历史计数。

先读取 `receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/RESUME.cp370-consumers-qualified.live1013.root.json`，其 SHA256 为 `38e8633ef8796e3f59663d8fa2464b33155d623112fc1fc5e26a8cb6bf3158ac`、6145 bytes。其后发生的新错误必须按 Root 最新台账继续追加。

W09：Main C19 Native 与两条实际 dispatcher 均已有独立组件/夹具资格；保留成功证据，不重复这两条 dispatcher。完整 G01/G02/A06 仍开放。先准备 profile/registry 兼容 Source：真实 Native tool-run 路径、受控历史 CM39 回执和真实执行/复核/观察角色，再准备三个完整 Native selector。源码准备、组件验证和正式验收分别记录。

W05：真实 schema22 程序来源已独立核对；public22 runner v2 已独立 Source 接受，但尚未登记或实际运行。正在准备当前 Main23 新构建与 Root caller/登记器。Main 23→24 尚未采用；schema21 程序和完整 20→24 链路仍开放。已合格 development13 不重复运行。

Original provider trial：只读核对已封存。本地 dispatch 前失败和 Job 关闭有记录；原账户归属、外部完整请求、服务器终止和费用仍为 UNKNOWN/null。只阻塞对应 paid/model 支路，其余授权工作继续。

只读选择卡使用 frozen `contracts/execution.plan.json` 与 `tools/task_packet.py next --state execution/v2.4/step_state.json`；上次选择 W05-99，结构有效不等于产品接受。Root 串行整合，活跃父任务 W05/W09；不启动 Qoder 或新的用户聊天。

旧成果完整保留。HEAD 为 `adc460c2138528f163f7fdab5e8d81dde157b7fb`，分支 main；本次 Git 只读快照与旧 handoff 原始完整字节保存于上述 R370 目录。最新实际 Source/证据 pins 见 `handoff-refresh.live1013.root.json`，不得按旧 R156 文本重置当前状态、计数或 Scope。
'''
new_ref=write(R/'execution/v2.4/HANDOFF_RESUME_PACK_R370.md',text.encode('utf-8'))
pointer=("<!-- R370 continuation: read HANDOFF_RESUME_PACK_R370.md and the exact pinned live1013 Root resume. "
         "The R156 content below is retained as historical evidence and must not override current Canon. -->\r\n\r\n").encode('utf-8')
updated=False
if not is_protected:
    assert handoff.read_bytes()==old_raw
    temp=handoff.with_name('HANDOFF_RESUME_PACK.cp370.pending.md')
    write(temp,pointer+old_raw)
    assert handoff.read_bytes()==old_raw
    os.replace(temp,handoff)
    assert handoff.read_bytes()[len(pointer):]==old_raw
    updated=True
outcome=save(N/'handoff-refresh.live1013.root.json',dict(schema='researchos.root-handoff-refresh.v1',issued_by='codex:/root',
    created_utc=datetime.now(timezone.utc).isoformat(),canonical_refs=canonical,resume_ref=resume_ref,
    old_handoff_ref=old_ref,historical_complete_handoff_ref=original_handoff,
    current_handoff_ref=pin(handoff),new_handoff_ref=new_ref,protected_handoff_detected=is_protected,
    pointer_prepended=updated,historical_body_preserved_exactly=True,git_baseline_ref=summary,
    source_guard_closed_ref=guard_ref,resource_and_gap_refs=extra,formal_acceptance=False,Canon_written=False,counter_reset=False))
assert [pin(Path(ref['path'])) for ref in canonical]==canonical
print(json.dumps(dict(outcome_ref=outcome,new_handoff_ref=new_ref,pointer_prepended=updated,
    protected_handoff_detected=is_protected,head=head,branch=branch,status_records=len(items),
    tracked_deletions=len(deletions),Canon_unchanged=True,original_handoff_complete_bytes_preserved=True,
    next_original=1013,formal_delta=0),ensure_ascii=False),flush=True)
